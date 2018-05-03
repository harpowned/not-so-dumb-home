#!/usr/bin/env python
import sys
import time
import socket
import logging
import threading
import traceback
import os
from logging.handlers import RotatingFileHandler
import datetime
import ConfigParser
import getopt
import paho.mqtt.client as mqtt
import json

eERSION="1.7.0-dev"

Config = ConfigParser.ConfigParser()
def_config_paths = [
	"/etc/smarthome/deviceInterface.cfg",
	"/usr/local/etc/smarthome/deviceInterface.cfg",
	"./deviceInterface.cfg",
]

globalLogger = logging.getLogger("smarthome")
logger = logging.getLogger("smarthome.deviceInterface")

secondDisplayOutdoor = False
secondDisplayTimeout = 15 # minutes
secondDisplayTimeSet = datetime.datetime(2000,1,1,0,0)

testRun = False
mqtt_topic = ""

consecutiveCommErrors = 0
maxConsecutiveCommErrors = 5
commWatchdogOn = True
 
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

def print_powermeter():
	powermeter.getVoltage()
	powermeter.getCurrent()
	powermeter.getPower()
	powermeter.getApPower()
	powermeter.getRePower()
	powermeter.getPowerFactor()
	powermeter.getPhaseAngle()
	powermeter.getFrequency()
	powermeter.getAccImportActiveEnergy()
	powermeter.getAccExportActiveEnergy()
	powermeter.getAccImportReactiveEnergy()
	powermeter.getAccExportReactiveEnergy()
	powermeter.getAccTotalActiveEnergy()
	powermeter.getAccTotalReactiveEnergy()
	powermeter.getMaxPower()

def print_thermostat():
	thermostat.getCurrentMode()
	thermostat.getCurrentTemp()
	thermostat.getCurrentSetpoint()
	thermostat.isHeating()

def isOutTempTimeoutExpired():
	global secondDisplayTimeSet
	global secondDisplayTimeout
	# if secondDisplayTimeSet + secondDisplayTimeout is older than now, return true
	if (secondDisplayTimeSet + datetime.timedelta(minutes=secondDisplayTimeout) < datetime.datetime.now()):
		logger.info("Timeout is expired (set on %s, now is %s)" % (secondDisplayTimeSet,datetime.datetime.now()))
		return True
	logger.debug("Timeout is not expired")
	return False

def refreshOutTempTimeout():
	global secondDisplayTimeSet
	logger.debug("Refreshing timeout")
	secondDisplayTimeSet = datetime.datetime.now()

powermeter_datatypes_get = [
	"volt",
	"current",
	"power",
	"appower",
	"repower",
	"pfactor",
	"phase",
	"freq",
	"acciae",
	"acceae",
	"accire",
	"accere",
	"totact",
	"totrea",
	"maxpower",
	
]
powermeter_datafunctions_get = [
	"getVoltage",
	"getCurrent",
	"getPower",
	"getApPower",
	"getRePower",
	"getPowerFactor",
	"getPhaseAngle",
	"getFrequency",
	"getAccImportActiveEnergy",
	"getAccExportActiveEnergy",
	"getAccImportReactiveEnergy",
	"getAccExportReactiveEnergy",
	"getAccTotalActiveEnergy",
	"getAccTotalReactiveEnergy",
	"getMaxPower",
]
thermostat_datatypes_get = [
	"curtemp",
	"setpoint",
	"isheating",
	"solar",
	"mode",
]
thermostat_datafunctions_get = [
	"getCurrentTemp",
	"getCurrentSetpoint",
	"isHeatingInt",
	"isSolarInt",
	"getCurrentMode",
]
thermostat_datatypes_set = [
	"setpoint",
	"outtemp",
]
thermostat_datafunctions_set = [
	"setSetpoint",
	"setOutTemp",
]


def on_message(mqttClient, userdata, msg):
	logger.debug("MQTT message received: "+msg.topic+" - "+str(msg.payload))
	global secondDisplayOutdoor
	global consecutiveCommErrors
	global commWatchdogOn
	try:
		jsonMsg = json.loads(msg.payload)
		response = {}
		device = jsonMsg["device"]
		logger.debug("Device is %s",device)
		command = jsonMsg["command"]
		logger.debug("Command is %s",command)
		## Process powermeter GET commands

		if device == "powermeter" and command == "get":
			powermeter_data = []
			keys = jsonMsg["keys"]
			for key in keys:
				if key in powermeter_datatypes_get:
					powermeter_data.append(key)
			for datatype,function in zip(powermeter_datatypes_get,powermeter_datafunctions_get):
				if datatype in powermeter_data:
					if "values" not in response:
						response["values"] = {}
					methodToCall = getattr(powermeter, function)
					response["values"][datatype] = str(methodToCall())
			if response:
				if "query_id" in jsonMsg:
					response["query_id"] = jsonMsg["query_id"]
				response["device"] = "powermeter"
				response["command"] = "readings"
				consecutiveCommErrors = 0
				mqttClient.publish(mqtt_topic,json.dumps(response),qos=1)
		## Process thermostat GET commands
		elif device == "thermostat" and command == "get":
			thermostat_data = []
			keys = jsonMsg["keys"]
			for key in keys:
				if key in thermostat_datatypes_get:
					thermostat_data.append(key)
			for datatype,function in zip(thermostat_datatypes_get,thermostat_datafunctions_get):
				if datatype in thermostat_data:
					if "values" not in response:
						response["values"] = {}
					methodToCall = getattr(thermostat, function)
					response["values"][datatype] = str(methodToCall())
			if response:
				response["device"] = "thermostat"
				response["command"] = "readings"
				if "query_id" in jsonMsg:
					response["query_id"] = jsonMsg["query_id"]
				consecutiveCommErrors = 0
				mqttClient.publish(mqtt_topic,json.dumps(response),qos=1)
		## Process thermostat SET commands
		elif device == "thermostat" and command == "set":
			thermostat_data = []
			key = jsonMsg["key"]
			value = jsonMsg["value"]
			# Asking for a nonexisting index will raise an exception, so we don't need to treat the case here
			logger.info("Thermostat SET command, Key: %s, value: %s" % (key,value))
			keyIndex = thermostat_datatypes_set.index(key)
			methodToCall = getattr(thermostat,thermostat_datafunctions_set[keyIndex])
			methodToCall(value)
	except ValueError:
		logger.warning("Received invalid json (invalid value)")
	except KeyError:
		logger.warning("Received invalid json (invalid key)")
	except TypeError:
		logger.warning("Received invalid json (invalid type)")
	except RuntimeError:
		logger.warning("No response to a query")
		consecutiveCommErrors = consecutiveCommErrors + 1
		if commWatchdogOn and consecutiveCommErrors > maxConsecutiveCommErrors:
			logger.error("%s consecutive communication errors. Quitting.." % consecutiveCommErrors)
			die()
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
	global thermostat
	global powermeter
	global testRun
	global mqtt_topic

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

	
	thermoType = Config.get("deviceInterface","thermostat")
	if thermoType == "none":
		import nullThermo as thermostat
	elif thermoType == "rdf302":
		import rdf302driver as thermostat
		thermostat.setModbusAddr(Config.get("thermostat-rdf302","modbus-address"))
	elif thermoType == "arduinoSolarThermo":
		import arduinoSolarThermoDriver as thermostat
		thermostat.setSerialAddr(Config.get("thermostat-arduinoSolarThermo","serial-address"))
		thermostat.openSerial()
		logger.info("Sleeping to allow thermostat to boot..")
		time.sleep(5)
		solarSchedulerOn = Config.get("thermostat-arduinoSolarThermo","solarScheduler")
		if solarSchedulerOn == "yes":
			solarTimeOn = int(Config.get("thermostat-arduinoSolarThermo","solarTimeOn"))
			solarTimeOff = int(Config.get("thermostat-arduinoSolarThermo","solarTimeOff"))
			thermostat.startSolarScheduler(solarTimeOn,solarTimeOff)
	else:
		logger.error("Unsupported thermostat type. Check config file")
		sys.exit(2)

	pmType = Config.get("deviceInterface","powermeter")
	if pmType == "none":
		import nullPowerMeter as powermeter
	elif pmType == "sdm220":
		import sdm220driver as powermeter
		powermeter.setModbusAddr(Config.get("powermeter-sdm220","modbus-address"))
		powermeter.setMaxPower(Config.get("powermeter-sdm220","maxpower"))
	else:
		logger.error("Unsupported power meter type. Check config file")
		sys.exit(2)

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

	# As a default, we want to start with the secondary display disabled.
	# It will be enabled the first time an outdoor temp reading is received
	thermostat.disableSecDisplay()

	if testRun:
		runTest()
	

	mqttClient.loop_forever()


if __name__ == "__main__":
        main(sys.argv[1:])
