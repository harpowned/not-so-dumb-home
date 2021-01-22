#!/usr/bin/env python
import sys
import logging
import traceback
import os
from logging.handlers import RotatingFileHandler
import ConfigParser
import getopt
import paho.mqtt.client as mqtt
import json
import ast
import importlib

VERSION="1.7.0"

Config = ConfigParser.ConfigParser()
def_config_paths = [
	"/etc/smarthome/deviceInterface.cfg",
	"/usr/local/etc/smarthome/deviceInterface.cfg",
	"./deviceInterface.cfg",
]

globalLogger = logging.getLogger("smarthome")
logger = logging.getLogger("smarthome.deviceInterface")

testRun = False
mqtt_topic = ""

consecutiveCommErrors = 0
maxConsecutiveCommErrors = 5
commWatchdogOn = True

instanceName = ""

devices = [] 

#----------------------------------------------------------------------

def die():
	#print(traceback.format_exc())
	logger.error(traceback.format_exc())
	logger.error("Error detected, application is Dying!")
	sys.exit(2)

def init_log(path):
	global globalLogger
	globalLogger.setLevel(logging.INFO) 

	# add a rotating handler
	file_handler = RotatingFileHandler(path, maxBytes=10*1024*1024,backupCount=5)
	file_formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
	file_handler.setFormatter(file_formatter)
	globalLogger.addHandler(file_handler)
 
	console = logging.StreamHandler()
	# set a format which is simpler for console use
	console_formatter = logging.Formatter('%(asctime)s %(name)-12s: %(levelname)-8s %(message)s')
	# tell the handler to use this format
	console.setFormatter(console_formatter)
	# add the handler to the root logger
	logging.getLogger('').addHandler(console)

def on_message(mqttClient, userdata, msg):
	logger.debug("MQTT message received: "+msg.topic+" - "+str(msg.payload))
	global consecutiveCommErrors
	global devices
	global instanceName
	try:
		jsonMsg = json.loads(msg.payload)
		if "command" not in jsonMsg:
			logger.warn("Received message without a valid command field")
			return
		response = {}
		command = jsonMsg["command"]
		if command == "listDevices":
			logger.info("Requested device list")
			response["command"] = "deviceList"
			response["instanceName"] = instanceName
			response["devices"] = []
			for device in devices:
				deviceInfo = {}
				deviceInfo["name"] = device.getName()
				deviceInfo["type"] = device.getType()
				response["devices"].append(deviceInfo)
			mqttClient.publish(mqtt_topic,json.dumps(response),qos=1)
			return
		if "device" not in jsonMsg:
			logger.warn("Received message without a valid device field")
			return
		deviceName = jsonMsg["device"]
		## Iterate on all active devices
		for device in devices:
			## If the message is addressed to this device, or to all devices of this type, process it
			logger.debug("msg destination is %s. device name is %s, device type is %s",deviceName,device.getName(),device.getType())
			if (device.getName() == deviceName) or (device.getType() == deviceName):
				if command == "get":
					## create the response and fill the common fields
					response = {}
					response["device"] = deviceName
					response["command"] = "readings"
					## Fill the query ID if the query has one
					if "query_id" in jsonMsg:
						response["query_id"] = jsonMsg["query_id"]
					## Get the requested values from the device
					gettable_vars = device.getGettableVars()
					keys = jsonMsg["keys"]
					for key in keys:
						if key in gettable_vars:
							if "values" not in response:
								response["values"] = {}
							response["values"][key] = str(device.getValue(key))
					## If any values were returned, respond
					if response["values"]:
						consecutiveCommErrors = 0
						mqttClient.publish(mqtt_topic,json.dumps(response),qos=1)
				if command == "set":
					settable_vars = device.getSettableVars()
					key = jsonMsg["key"]
					value = jsonMsg["value"]
					logger.debug("Set command received for device %s, key %s, value %s",deviceName,key,value)
					if key in settable_vars:
						device.setValue(key,value)
#	except ValueError:
#		logger.warning("Received invalid json (invalid value)")
#	except KeyError:
#		logger.warning("Received invalid json (invalid key)")
#	except TypeError:
#		logger.warning("Received invalid json (invalid type)")
#	except RuntimeError:
#		logger.warning("No response to a query")
#		consecutiveCommErrors = consecutiveCommErrors + 1
#		if commWatchdogOn and consecutiveCommErrors > maxConsecutiveCommErrors:
#			logger.error("%s consecutive communication errors. Quitting.." % consecutiveCommErrors)
#			die()
	except:
		die()
	

def print_usage():
	print 'Usage: deviceInterface.py [-c <configfile>, -v, -t]'
	print '	-c <configfile> : Read config file from nonstandard location'
	print '	-v : Enable verbose output'
	print ' -t : Test run, print a report for all devices and exit'
	print ' If no config file is specified using -c, config file is loaded from the first existing location in the following:'
	for config_path in reversed(def_config_paths):
		print "    %s "%config_path
	
	sys.exit(2)



def on_connect(mqttClient, userdata, flags, rc):
	logger.info("Connected to MQTT server")
	mqttClient.subscribe(mqtt_topic, qos=1)
	


def main(args):
	global devices
	global testRun
	global mqtt_topic
	global instanceName

	config_file = ""
	debug = False

	## Parse command line arguments
	try:
		opts,args = getopt.getopt(sys.argv[1:],"c:vt",["--config=","--verbose","--test"])
	except getopt.GetoptError:
		print_usage()
	for opt, arg in opts:
		if opt == '-h':
			print_usage()
		elif opt in ("-t","--test"):
			testRun = True
		elif opt in ("-c","--config"):
			config_file = arg
		elif opt in ("-v","--verbose"):
			debug = True
	if not config_file:
		for config_candidate in def_config_paths:
			if os.path.exists(config_candidate):
				config_file = config_candidate

	if not os.path.exists(config_file):
		print "Error: Config file not found"
		sys.exit(2)


	print "Reading config file from: %s" % config_file
	Config.read(config_file)

	logpath = Config.get("deviceInterface","logfile")
	if not logpath:
		print "Error: missing logpath. Check config file"
		sys.exit(2)

	init_log(logpath)
	if debug:
		globalLogger.setLevel(logging.DEBUG)
	logger.info("Starting SmartHome DeviceInterface %s" % VERSION)

	if "-t" in args:
		logger.info("Test mode run")

	enabledDevices = ast.literal_eval(Config.get("deviceInterface","enabled_devices"))
	deviceDrivers = dict()
	for deviceName in enabledDevices:
		deviceType = Config.get(deviceName,"type")
		deviceModel = Config.get(deviceName,"model")
		deviceDriver = deviceType+"_"+deviceModel
		
		## Load the driver for this device
		if deviceDriver not in sys.modules:
			deviceDrivers[deviceDriver] = importlib.import_module(deviceDriver)
		driver = importlib.import_module(deviceDriver)
		## Instantiate the device object
		device = deviceDrivers[deviceDriver].Driver(deviceName,Config)
		## Add the object to the running devices
		devices.append(device)
		
	# Read MQTT config and connect to server
	mqtt_host = Config.get("server-mqtt","host")
	mqtt_port = Config.get("server-mqtt","port")
	mqtt_topic = Config.get("server-mqtt","topic")
	mqtt_ssl = Config.get("server-mqtt","ssl")

	instanceName = Config.get("deviceInterface","instanceName")
	
	mqttClient = mqtt.Client(client_id=instanceName, clean_session=False, userdata=None, protocol="MQTTv311", transport="tcp")
	mqttClient.on_connect = on_connect
	mqttClient.on_message = on_message
	if mqtt_ssl == "yes":
		import ssl
		mqtt_cacert = Config.get("server-mqtt","cacert")
		mqtt_clientcert = Config.get("server-mqtt","clientcert")
		mqtt_clientkey = Config.get("server-mqtt","clientkey")
		if mqtt_clientcert:	
			mqttClient.tls_set(mqtt_cacert, certfile=mqtt_clientcert, keyfile=mqtt_clientkey, cert_reqs=ssl.CERT_REQUIRED,tls_version=ssl.PROTOCOL_TLSv1, ciphers=None)
		else:
			mqttClient.tls_set(mqtt_cacert, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED,tls_version=ssl.PROTOCOL_TLSv1, ciphers=None)
	logger.debug("Now connecting to MQTT server")
	mqttClient.connect(mqtt_host,port=mqtt_port,keepalive=60)

	if testRun:
		runTest()
	

	mqttClient.loop_forever()


if __name__ == "__main__":
        main(sys.argv[1:])
