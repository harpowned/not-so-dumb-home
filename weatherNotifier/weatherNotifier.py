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

VERSION="1.6.3"

Config = ConfigParser.ConfigParser()
def_config_paths = [
	"/etc/smarthome/weatherNotifier.cfg",
	"/usr/local/etc/smarthome/weatherNotifier.cfg",
	"./weatherNotifier.cfg",
]

logpath=""


globalLogger = logging.getLogger("smarthome")
logger = logging.getLogger("smarthome.weatherNotifier")

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

def weatherinfo_scheduler():
	global notification_interval
	global weatherService
	while True:
		logger.debug("Weather reporting loop running")
		if weatherService.updateData():
			# Send a generic weather report
			logger.debug("Updated weather info OK")
			weatherinfo = {}
			weatherinfo["device"] = "weatherstation"
			weatherinfo["currentTemp"] = weatherService.getCurrentTemp()
			weatherinfo["currentHum"] = weatherService.getCurrentHum()
			weatherinfo["currentPress"] = weatherService.getCurrentPress()
			weatherinfo["currentWindSpeed"] = weatherService.getCurrentWindSpeed()
			weatherinfo["weatherIcon"] = weatherService.getWeatherIcon()
			weatherinfo["weatherText"] = weatherService.getWeatherText()
			jsonstr = json.dumps(weatherinfo)
			logger.info("Posting to mqtt: %s" % jsonstr)
			mqttClient.publish(mqtt_topic,jsonstr, qos=0)
			# Send a command to update the thermostat outdoor temp display
			# This is a dirty hack. The thermostat should subscribe to the generic report
			thermostatCommand = {}
			thermostatCommand["device"] = "thermostat"
			thermostatCommand["command"] = "set"
			thermostatCommand["key"] = "outtemp"
			thermostatCommand["value"] = weatherService.getCurrentTemp()
			jsonstr = json.dumps(thermostatCommand)
			logger.info("Posting to mqtt: %s" % thermostatCommand)
			mqttClient.publish(mqtt_topic,jsonstr, qos=0)
		else:
			logger.warning("Could not update weather info")
			
		time.sleep(notification_interval)



def print_usage():
	print 'Usage: weatherNotifier.py [-c <configfile>, -v]'
	print '	-c <configfile> : Read config file from nonstandard location'
	print '	-v : Enable verbose output'
	print ' If no config file is specified using -c, config file is loaded from the first existing location in the following:'
	for config_path in reversed(def_config_paths):
		print "    %s "%config_path
	
	sys.exit(2)

def on_connect(mqttClient, userdata, flags, rc):
	logger.info("Connected to MQTT server")

def main(args):
	global mqttClient
	global mqtt_topic
	global logger
	global notification_interval
	global weatherService

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

	logpath = Config.get("weatherNotifier","logfile")
	if not logpath:
		print "Error: missing logpath. Check config file"
		sys.exit(2)
	
	init_log(logpath)
	if debug:
		globalLogger.setLevel(logging.DEBUG)
	logger.info("Starting SmartHome Weather Notigfier %s" % VERSION)

	weatherType = Config.get("weatherNotifier","weatherService")
	if weatherType == "darksky":
		import darkSky as weatherService
		weatherService.setDarkSkyApiKey(Config.get("darksky","apikey"))
	weatherService.setPosition(Config.get("weatherNotifier","latitude"),Config.get("weatherNotifier","longitude"))
	
	notification_interval = float(Config.get("weatherNotifier","interval"))

	# Read MQTT config and connect to server
	mqtt_host = Config.get("server-mqtt","host")
	mqtt_port = Config.get("server-mqtt","port")
	mqtt_topic = Config.get("server-mqtt","topic")
	mqtt_ssl = Config.get("server-mqtt","ssl")

	instanceName = Config.get("weatherNotifier","instanceName")
	
	mqttClient = mqtt.Client(client_id=instanceName, clean_session=False, userdata=None, protocol="MQTTv311", transport="tcp")
	mqttClient.on_connect = on_connect
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

	t = threading.Thread(target=weatherinfo_scheduler)
	t.daemon = True
	t.start()

	mqttClient.loop_forever()

if __name__ == "__main__":
	main(sys.argv[1:])
