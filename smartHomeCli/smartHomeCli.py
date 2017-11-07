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
import cmd
from random import randint

VERSION="1.7"

QUERY_TIMEOUT=2

Config = ConfigParser.ConfigParser()
def_config_paths = [
	"/etc/smarthome/smartHomeCli.cfg",
	"/usr/local/etc/smarthome/smartHomeCli.cfg",
	"./smartHomeCli.cfg",
]

globalLogger = logging.getLogger("smarthome")
logger = logging.getLogger("smarthome.smartHomeCli")

mqtt_topic = ""

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
	global pending_query_id
	global queryAnswer
	global queryAnswerEvent
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
		if query_id == pending_query_id:
			logger.debug("Got answer to pending query")
			queryAnswer = jsonMsg
			queryAnswerEvent.set()
	except:
        	logger.debug(traceback.format_exc())
		pass
	

def print_usage():
	print 'Usage: smartHomeCli.py [-c <configfile>, -v, -t]'
	print '	-c <configfile> : Read config file from nonstandard location'
	print '	-v : Enable verbose output'
	print ' If no config file is specified using -c, config file is loaded from the first existing location in the following:'
	for config_path in reversed(def_config_paths):
		print "    %s "%config_path
	
	sys.exit(2)

def isanumber(a):
	try:
		float(a)
		return True
	except:
		logger.error(traceback.format_exc())
		return False

def get_thermostat_status():
	global pending_query_id
	global queryAnswerEvent
	global queryAnswer
	pending_query_id = randint(1,1000000000)
	query = '{"device":"thermostat","keys":["curtemp","setpoint","isheating"],"command":"get","query_id":%s}' % pending_query_id
	mqttClient.publish(mqtt_topic,query)
	queryAnswerEvent.clear()
	queryAnswer = ""
	queryAnswerEvent.wait(QUERY_TIMEOUT)
	if not queryAnswer:
		return False
	else:
		return queryAnswer["values"]

def get_powermeter_power():
	global pending_query_id
	global queryAnswerEvent
	global queryAnswer
	pending_query_id = randint(1,1000000000)
	query = '{"device":"powermeter","keys":["power"],"command":"get","query_id":%s}' % pending_query_id
	mqttClient.publish(mqtt_topic,query)
	queryAnswerEvent.clear()
	queryAnswer = ""
	queryAnswerEvent.wait(QUERY_TIMEOUT)
	if not queryAnswer:
		return False
	else:
		return queryAnswer["values"]["power"]

def print_thermostat_status():
	answer = get_thermostat_status()
	if answer:
		print "Current temperature: %s" % answer["curtemp"]
		print "Set point: %s" % answer["setpoint"]
		print "Is heating: %s" % answer["isheating"]
	else:
		print "No answer from thermostat"
		
	
def set_thermostat_setpoint(temp):
	msg = {}
	msg["device"] = "thermostat"
	msg["command"] = "set"
	msg["key"] = "setpoint"
	msg["value"] = temp
	mqttClient.publish(mqtt_topic,json.dumps(msg))
	answer = get_thermostat_status()
	if answer:
		if float(answer["setpoint"]) == temp:
			print "Thermostat set correctly"
		else:
			print "Error setting setpoint"
	else:
		print "No answer from thermostat"

def wait_for_key():
	global stop_reading
	raw_input()
	stop_reading = True

def print_powermeter():
	global stop_reading
	stop_reading = False

	
	t = threading.Thread(target=wait_for_key)
	t.start()

	print "Press enter to go back"
	print "  "
	while True:
		power = get_powermeter_power()
		if power:
			sys.stdout.write("\r%s W       " % power)
			sys.stdout.flush()
			time.sleep(0.2)
		else:
			sys.stdout.write("\rNo answer..       " % power)
			sys.stdout.flush()
			time.sleep(0.2)
		if stop_reading:
			break
	

def on_connect(mqttClient, userdata, flags, rc):
	logger.info("Connected to MQTT server")
	mqttClient.subscribe(mqtt_topic, qos=1)
	
class MainMenu(cmd.Cmd):
	def do_pm(self, arg):
		"Show power meter readings"
		print_powermeter()
	def do_thget(self,arg):
		"Show thermostat status"
		print_thermostat_status()
	def do_thset(self,arg):
		"Set thermostat setpoint"
		if not isanumber(arg):
			print "Error: Input must be a number"
		set_thermostat_setpoint(float(arg))
	def do_q(self,arg):
		return True
	def do_EOF(self, line):
		return True

def run_cli():
	MainMenu().cmdloop()
	


def main(args):
	global mqtt_topic
	global queryAnswerEvent
	global mqttClient
	global pending_query_id

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

	logpath = Config.get("smartHomeCli","logfile")
	if not logpath:
		print "Error: missing logpath. Check config file"
		sys.exit(2)

	init_log(logpath)
	if debug:
		globalLogger.setLevel(logging.DEBUG)
	logger.info("Starting SmartHome Command Line Interface %s" % VERSION)

	# Read MQTT config and connect to server
	mqtt_host = Config.get("server-mqtt","host")
	mqtt_port = Config.get("server-mqtt","port")
	mqtt_topic = Config.get("server-mqtt","topic")
	mqtt_ssl = Config.get("server-mqtt","ssl")

	instanceName = Config.get("smartHomeCli","instanceName")
	
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

	queryAnswerEvent = threading.Event()
	pending_query_id = 0

	logger.debug("Now connecting to MQTT server")
	mqttClient.connect(mqtt_host,port=mqtt_port,keepalive=60)

	mqttClient.loop_start()

	# TODO: Run the CLI only on_connect of mqtt. Implement a timeout in case the server is unreachable. Show connection status on the CLI.
	run_cli()

	logger.info("GUI Exited, shutting down..")
	mqttClient.loop_stop()


if __name__ == "__main__":
        main(sys.argv[1:])
