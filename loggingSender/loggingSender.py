#!/usr/bin/python
import time
import datetime
import threading
import logging
from logging.handlers import RotatingFileHandler
import traceback
import os
import ConfigParser
import sys
import getopt
import paho.mqtt.client as mqtt
import json
from random import randint
import zabbixSender as loggingServer

VERSION="1.6"

Config = ConfigParser.ConfigParser()
def_config_paths = [
	"/etc/smarthome/loggingSender.cfg",
	"/usr/local/etc/smarthome/loggingSender.cfg",
	"./loggingSender.cfg",
]

logpath=""


globalLogger = logging.getLogger("smarthome")
logger = logging.getLogger("smarthome.loggingSender")

waitingForQuery = False

global sched

def die():
        print(traceback.format_exc())
        logger.error(traceback.format_exc())
	try:
		mail_sender.sendMail(traceback.format_exc())
	except:
        	os._exit(1)
        os._exit(1)

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

def sendDataToLoggingServer(device,values):
	logger.debug("sendDataToLoggingServer")
	deviceHostname = Config.get(device,"loggingServerHostname")
	for value in values:
		loggingServer.pushData(deviceHostname,value,values[value])

launchedQueries = set()

def on_message(mqttClient, userdata, msg):
	global launchedQueries
	logger.debug("MQTT message received: "+msg.topic+" - "+str(msg.payload))
	try:
		jsonMsg = json.loads(msg.payload)
		if "command" not in jsonMsg:
			logger.debug("Command not in json")
			return
		command = jsonMsg["command"]
		if command != "readings":
			logger.debug("Command is not readings")
			return
		if "query_id" not in jsonMsg:
			logger.debug("Query ID not in json")
			return
		query_id = jsonMsg["query_id"]
		if query_id in launchedQueries:
			launchedQueries.discard(query_id)
			if "device" not in jsonMsg:
				logger.debug("Device not in json")
				return
			device = jsonMsg["device"]
			if "values" not in jsonMsg:
				logger.debug("Values not in json")
				return
			values = jsonMsg["values"]
			sendDataToLoggingServer(device,values)
	except:
        	logger.debug(traceback.format_exc())
		pass

def logging_scheduler():
	global launchedQueries
	devices_str = Config.get("loggingSender","devices")
	devices = [x.strip() for x in devices_str.split(',')]
	delay = int(Config.get("loggingSender","interval"))
	while True:
		logger.debug("Logging loop running")
		launchedQueries.clear()
		for device in devices:
			logger.debug("Now processing device: %s" % device)
			variables_str = Config.get(device,"variables")
			variables = [x.strip() for x in variables_str.split(',')]
			query_id = randint(1,1000000000)
			query = {}
			query["device"] = device
			query["command"] = "get"
			query["keys"] = variables
			query["query_id"] = query_id
			mqttClient.publish(mqtt_topic,json.dumps(query))
			launchedQueries.add(query_id)
			logger.debug(launchedQueries)
			
		time.sleep(delay)



def print_usage():
	print 'Usage: loggingScheduler.py [-c <configfile>, -v]'
	print '	-c <configfile> : Read config file from nonstandard location'
	print '	-v : Enable verbose output'
	print ' If no config file is specified using -c, config file is loaded from the first existing location in the following:'
	for config_path in reversed(def_config_paths):
		print "    %s "%config_path
	
	sys.exit(2)

def on_connect(mqttClient, userdata, flags, rc):
	logger.info("Connected to MQTT server")
	mqttClient.subscribe(mqtt_topic)

def main(args):
	global mqttClient
	global mqtt_topic
	global logger

	config_file = ""
	debug = False

	## Parse command line arguments
	try:
		opts,args = getopt.getopt(sys.argv[1:],"c:v",["--config=","--verbose"])
	except getopt.GetoptError:
		print_usage()
	for opt, arg in opts:
		if opt == '-h':
			print_usage()
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

	logpath = Config.get("loggingSender","logfile")
	if not logpath:
		print "Error: missing logpath. Check config file"
		sys.exit(2)
	
	init_log(logpath)
	if debug:
		globalLogger.setLevel(logging.DEBUG)
	logger.info("Starting SmartHome Logging Sender %s" % VERSION)

	zabbix_host = Config.get("logging-zabbix","host")
	zabbix_port = Config.get("logging-zabbix","port")
	loggingServer.setConfig(zabbix_host,zabbix_port)
	
	# Read MQTT config and connect to server
	mqtt_host = Config.get("server-mqtt","host")
	mqtt_port = Config.get("server-mqtt","port")
	mqtt_topic = Config.get("server-mqtt","topic")
	mqtt_ssl = Config.get("server-mqtt","ssl")
	mqtt_cacert = Config.get("server-mqtt","cacert")
	mqtt_clientcert = Config.get("server-mqtt","clientcert")
	mqtt_clientkey = Config.get("server-mqtt","clientkey")

	instanceName = Config.get("loggingSender","instanceName")
	
	mqttClient = mqtt.Client(client_id=instanceName, clean_session=False, userdata=None, protocol="MQTTv311", transport="tcp")
	mqttClient.on_connect = on_connect
	mqttClient.on_message = on_message
	if mqtt_ssl == "yes":
		import ssl
		if mqtt_clientcert:	
			mqttClient.tls_set(mqtt_cacert, certfile=mqtt_clientcert, keyfile=mqtt_clientkey, cert_reqs=ssl.CERT_REQUIRED,tls_version=ssl.PROTOCOL_TLSv1, ciphers=None)
		else:
			mqttClient.tls_set(mqtt_cacert, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED,tls_version=ssl.PROTOCOL_TLSv1, ciphers=None)
	logger.debug("Now connecting to MQTT server")
	mqttClient.connect(mqtt_host,port=mqtt_port,keepalive=60)

	t = threading.Thread(target=logging_scheduler)
	t.daemon = True
	t.start()

	mqttClient.loop_forever()

if __name__ == "__main__":
	main(sys.argv[1:])
