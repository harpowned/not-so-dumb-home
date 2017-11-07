#!/usr/bin/python
import mysql.connector
import time
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import threading
import logging
from logging.handlers import RotatingFileHandler
import traceback
import os
import mail_sender
import ConfigParser
import sys
import getopt
import paho.mqtt.client as mqtt
import json

VERSION="1.6"

Config = ConfigParser.ConfigParser()
def_config_paths = [
	"/etc/smarthome/heatingScheduler.cfg",
	"/usr/local/etc/smarthome/heatingScheduler.cfg",
	"./heatingScheduler.cfg",
]
supported_dbs = [
	"mysql",
]
supported_email = [
	"smtp",
	"none",
]

logpath=""


globalLogger = logging.getLogger("smarthome")
logger = logging.getLogger("smarthome.heatingScheduler")

DB_user=''
DB_password=''
DB_host=''
DB_database=''

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

def setTemp(temp):
	msg = {}
	msg["device"] = "thermostat"
	msg["command"] = "set"
	msg["key"] = "setpoint"
	msg["value"] = temp
	mqttClient.publish(mqtt_topic,json.dumps(msg))
	mail_sender.sendMail("Set temperature to %s" % (temp))
	

def get_temp_at(date):
	logger.debug("Looking for temp at %s" % date)
	if time_in_exception(date):
		logger.debug("Time is in exception")
		cnx = mysql.connector.connect(user=DB_user, password=DB_password, host=DB_host, database=DB_database)
		cursor = cnx.cursor()
		query = "SELECT date_start,date_end,temp FROM `heating_except` WHERE (%s BETWEEN date_start AND date_end)"
		cursor.execute(query, [date])
		result = False
		for (date_start,date_end,temp) in cursor:
			set_temp = temp
			result = True
		cursor.close()
		cnx.close()
		if result:
			return set_temp
		else:
			logger.error("Error! Time in exception, but no exceptions returned")
			raise exception('print "Error! Time in exception, but no exceptions returned"')
	else:
		query_1 = "SELECT temp FROM `heating_regular` WHERE dow = %s AND time <= %s ORDER BY dow DESC, time DESC LIMIT 1"
		query_2 = "SELECT temp FROM `heating_regular` WHERE dow < %s ORDER BY dow DESC, time DESC LIMIT 1"
		query_3 = "SELECT temp FROM `heating_regular` WHERE dow > %s ORDER BY dow DESC, time DESC LIMIT 1"
		query_4 = "SELECT temp FROM `heating_regular` WHERE dow = %s AND time > %s ORDER BY dow DESC, time DESC LIMIT 1"
		q_dow = date.isoweekday()
		q_time = date.time()

		result = False
		cnx = mysql.connector.connect(user=DB_user, password=DB_password, host=DB_host, database=DB_database)
		cursor = cnx.cursor()
		cursor.execute(query_1, [q_dow,q_time])
		for (temp) in cursor:
			logger.debug("Last temp was set same day, and is %s" % temp)
			set_temp = temp[0]
			result = True
		if result:
			cursor.close()
			cnx.close()
			return set_temp
		cursor.execute(query_2, [q_dow])
		for (temp) in cursor:
			logger.debug("Last temp was set same week, and is %s" % temp)
			set_temp = temp[0]
			result = True
		if result:
			cursor.close()
			cnx.close()
			return set_temp
		cursor.execute(query_3, [q_dow])
		for (temp) in cursor:
			logger.debug("Last temp was set last week, and is %s" % temp)
			set_temp = temp[0]
			result = True
		if result:
			cursor.close()
			cnx.close()
			return set_temp
		cursor.execute(query_4, [q_dow,q_time])
		for (temp) in cursor:
			logger.debug("Last temp was set last week, on the same day, and is %s" % temp)
			set_temp = temp[0]
			result = True
		if result:
			cursor.close()
			cnx.close()
			return set_temp
		logger.error("Error! Time in regular, but no regular events returned")
		raise exception('print "Error! Time in regular, but no regular events returned"')

def time_in_exception(date):
	in_exception = False
	cnx = mysql.connector.connect(user=DB_user, password=DB_password, host=DB_host, database=DB_database)
	cursor = cnx.cursor()
	query = "SELECT date_start,date_end,temp FROM `heating_except` WHERE (%s BETWEEN date_start AND date_end)"
	cursor.execute(query, [date])
	for (date_start,date_end,temp) in cursor:
		in_exception = True
	cursor.close()
	cnx.close()
	logger.debug("Are we in exception at %s? %s" % (date,in_exception))
	return in_exception

def schedule_updater():
	current_jobs = ""
	last_updated = False
	while True:
		try:
			logger.debug("Now updating schedule")
			logger.debug("Connecting to DB. Host: %s, user: %s, db: %s" % (DB_host,DB_user,DB_database))
			cnx = mysql.connector.connect(user=DB_user, password=DB_password, host=DB_host, database=DB_database)
			cursor = cnx.cursor()
			query = "SELECT * FROM heating_regular WHERE enabled=1"
			cursor.execute(query, ())
			alljobs = ""
			for result in cursor:
				alljobs+=str(result)
			query = "SELECT * FROM heating_except"
			cursor.execute(query, ())
			for result in cursor:
				alljobs+=str(result)
	#		print alljobs
			cursor.close()
			cnx.close()
			scheduled_update = False
			if not last_updated or last_updated < (datetime.datetime.now() - datetime.timedelta(hours=6)):
				scheduled_update = True
			if (alljobs != current_jobs) or (scheduled_update):
				logger.info("Jobs have changed (%s) or scheduled update (%s), updating scheduler.." % (alljobs != current_jobs,scheduled_update))
				update_schedule()
				current_jobs = alljobs
				last_updated = datetime.datetime.now()
			time.sleep(60)
		except:
			die()

def update_schedule():
	global sched
	## Empty schedule
	sched.remove_all_jobs()

	## Connect to database
	cnx = mysql.connector.connect(user=DB_user, password=DB_password, host=DB_host, database=DB_database)
	cursor = cnx.cursor()

	## Initialize to current date. Get date just once to prevent inconsistencies
	current_time = datetime.datetime.now()
	current_dow = current_time.isoweekday()
	if current_dow == 7:
		next_dow = 1
	else:
		next_dow = current_dow+1

	logger.debug("Now doing exceptional scheduling")
	## Get exceptional scheduling from DB.
	## Program startup for events which begin between now and +1 day
	query = "SELECT date_start,date_end,temp FROM `heating_except` WHERE (date_start BETWEEN NOW() AND DATE_ADD(NOW(),INTERVAL 1 day))"
	cursor.execute(query, ())
	for (date_start,date_end,temp) in cursor:
		logger.debug("Exceptional event start programmed : at %s, set temp to %s" % (date_start,temp))
		sched.add_job(setTemp,'date', run_date=date_start, args=[temp])

	## Program finish for events which finish between now and +1 day
	query = "SELECT date_start,date_end,temp FROM `heating_except` WHERE (date_end BETWEEN NOW() AND DATE_ADD(NOW(),INTERVAL 1 day))"
	cursor.execute(query, ())
	for (date_start,date_end,temp) in cursor:
		## We add a minute, because we want the temperature outside of the exception. The date_end is included in the exception, hence it is not valid.
		previous_temp = get_temp_at(date_end + datetime.timedelta(minutes=1))
		logger.debug("Exceptional event finish programmed: at %s, set temp to %s" % (date_end,previous_temp))
		sched.add_job(setTemp,'date', run_date=date_end, args=[previous_temp])
		


	logger.debug("Now doing regular scheduling")
	## Get regular scheduling from DB
	query = "SELECT dow,temp,time FROM heating_regular WHERE enabled=1 AND (dow = %s OR dow = %s)"
	cursor.execute(query, (current_dow,next_dow))

	for (job_dow,job_temp,job_time) in cursor:
#		print "On day %s at %s, temp will be at %s" % (job_dow,job_time,job_temp)
		today = current_time.replace(hour=0, minute=0, second=0,microsecond=0)
		if job_dow == current_dow:
#			print "Job is for today"
			job_day = today
		else:
			job_day = today + datetime.timedelta(days=1)
		job_time = job_day + job_time
#		print "Job time is %s" % job_time

		## If a job is past, don't schedule it
		## If a regular job overlaps an exceptional one, the exceptional wins (don't schedule the regular)
		if not (job_time < current_time) and (not time_in_exception(job_time)):
			logger.debug("Regular job programmed. At %s, set the temp to %s" % (job_time,job_temp))
			sched.add_job(setTemp,'date', run_date=job_time, args=[job_temp])
	cursor.close()
	cnx.close()

def print_usage():
	print 'Usage: programmer.py [-c <configfile>, -v]'
	print '	-c <configfile> : Read config file from nonstandard location'
	print '	-v : Enable verbose output'
	print ' If no config file is specified using -c, config file is loaded from the first existing location in the following:'
	for config_path in reversed(def_config_paths):
		print "    %s "%config_path
	
	sys.exit(2)

def on_message(mqttClient, userdata, msg):
	logger.debug("MQTT message received: "+msg.topic+" - "+str(msg.payload))
	try:
		jsonMsg = json.loads(msg.payload)
		command = jsonMsg["command"]
		logger.debug("Command is %s",command)
		if command == "getHeatingSchedulingRegular":
			response = {}
			response["command"] = "heatingSchedulingRegular"
			response["schedule"] = []
			sql = "SELECT id,name,dow,temp,time,enabled from heating_regular"
			cnx = mysql.connector.connect(user=DB_user, password=DB_password, host=DB_host, database=DB_database)
			cursor = cnx.cursor()
			cursor.execute(sql, ())
			for (entryId,name,dow,temp,time,enabled) in cursor:
				entry = {}
				entry["id"] = entryId
				entry["name"] = name
				entry["dow"] = dow
				entry["temp"] = temp
				entry["time"] = str(time)
				entry["enabled"] = enabled
				response["schedule"].append(entry)
			cursor.close()
			cnx.close()
			mqttClient.publish(mqtt_topic,json.dumps(response))
		elif command == "updateHeatingSchedulingRegular":
			if "entry" not in jsonMsg:
				return
			entry = jsonMsg["entry"]
			if "id" not in entry:
				return
			entryId = entry["id"]
			if "name" not in entry:
				return
			name = entry["name"]
			if "dow" not in entry:
				return
			dow = entry["dow"]
			if "temp" not in entry:
				return
			temp = entry["temp"]
			if "time" not in entry:
				return
			time = entry["time"]
			if "enabled" not in entry:
				return
			enabled = entry["enabled"]
			cnx = mysql.connector.connect(user=DB_user, password=DB_password, host=DB_host, database=DB_database)
			cursor = cnx.cursor()
			logger.debug("Executing SQL query")
			logger.debug("UPDATE `heating_regular` SET `name` = %s, `dow` = %s, `temp` = %s, `time` = %s, `enabled` = %s WHERE `heating_regular`.`id` = %s;" %(name,dow,temp,time,enabled,entryId))
			cursor.execute("UPDATE `heating_regular` SET `name` = %s, `dow` = %s, `temp` = %s, `time` = %s, `enabled` = %s WHERE `heating_regular`.`id` = %s;", [name,dow,temp,time,enabled,entryId])
			cnx.commit()
			cursor.close()
			cnx.close()
		elif command == "insertHeatingSchedulingRegular":
			if "entry" not in jsonMsg:
				return
			entry = jsonMsg["entry"]
			if "name" not in entry:
				return
			name = entry["name"]
			if "dow" not in entry:
				return
			dow = entry["dow"]
			if "temp" not in entry:
				return
			temp = entry["temp"]
			if "time" not in entry:
				return
			time = entry["time"]
			if "enabled" not in entry:
				return
			enabled = entry["enabled"]
			cnx = mysql.connector.connect(user=DB_user, password=DB_password, host=DB_host, database=DB_database)
			cursor = cnx.cursor()
			logger.debug("Executing SQL query")
			cursor.execute("INSERT INTO `heating_regular` (`name`,`dow`,`temp`,`time`,`enabled`) VALUES (%s,%s,%s,%s,%s);", [name,dow,temp,time,enabled])
			cnx.commit()
			cursor.close()
			cnx.close()
			
		elif command == "getHeatingSchedulingExcept":
			response = {}
			response["command"] = "heatingSchedulingExcept"
			response["schedule"] = []
			sql = "SELECT id,name,temp,date_start,date_end from heating_except"
			cnx = mysql.connector.connect(user=DB_user, password=DB_password, host=DB_host, database=DB_database)
			cursor = cnx.cursor()
			cursor.execute(sql, ())
			for (entryId,name,temp,date_start,date_end) in cursor:
				entry = {}
				entry["id"] = entryId
				entry["name"] = name
				entry["temp"] = temp
				entry["date_start"] = str(date_start)
				entry["date_end"] = str(date_end)
				response["schedule"].append(entry)
			cursor.close()
			cnx.close()
			mqttClient.publish(mqtt_topic,json.dumps(response))
		elif command == "updateHeatingSchedulingExcept":
			if "entry" not in jsonMsg:
				return
			entry = jsonMsg["entry"]
			if "id" not in entry:
				return
			entryId = entry["id"]
			if "name" not in entry:
				return
			name = entry["name"]
			if "dow" not in entry:
				return
			temp = entry["temp"]
			if "date_start" not in entry:
				return
			date_start = entry["date_start"]
			if "date_end" not in entry:
				return
			date_end = entry["date_end"]
			cnx = mysql.connector.connect(user=DB_user, password=DB_password, host=DB_host, database=DB_database)
			cursor = cnx.cursor()
			logger.debug("Executing SQL query")
			cursor.execute("UPDATE `heating_except` SET `name` = %s, `temp` = %s, `date_start` = %s, `date_end` = %s WHERE `heating_except`.`id` = %s;", [name,temp,time,date_start,date_end])
			cnx.commit()
			cursor.close()
			cnx.close()
		elif command == "insertHeatingSchedulingExcept":
			if "entry" not in jsonMsg:
				return
			entry = jsonMsg["entry"]
			if "name" not in entry:
				return
			name = entry["name"]
			if "dow" not in entry:
				return
			temp = entry["temp"]
			if "date_start" not in entry:
				return
			date_start = entry["date_start"]
			if "date_end" not in entry:
				return
			date_end = entry["date_end"]
			cnx = mysql.connector.connect(user=DB_user, password=DB_password, host=DB_host, database=DB_database)
			cursor = cnx.cursor()
			logger.debug("Executing SQL query")
			cursor.execute("INSERT INTO `heating_except` (`name`,`temp`,`date_start`,`date_end`) VALUES (%s,%s,%s,%s);", [name,temp,date_start,date_end])
			cnx.commit()
			cursor.close()
			cnx.close()
	except:
		logger.debug(traceback.format_exc())
		pass
		
	

def on_connect(mqttClient, userdata, flags, rc):
	logger.info("Connected to MQTT server")
	mqttClient.subscribe(mqtt_topic)

def main(args):
	global DB_host
	global DB_user
	global DB_password
	global DB_database
	global sched
	global mqttClient
	global mqtt_topic

	config_file = ""

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
			logger.setLevel(logging.DEBUG)

	if not config_file:
		for config_candidate in def_config_paths:
			if os.path.exists(config_candidate):
				config_file = config_candidate
	
	if not os.path.exists(config_file):
		print "Error: Config file not found"
		sys.exit(2)


	print "Reading config file from: %s" % config_file
	Config.read(config_file)

	logpath = Config.get("heatingScheduler","logfile")
	if not logpath:
		print "Error: missing logpath. Check config file"
		sys.exit(2)
	
	db_type = Config.get("heatingScheduler","database")
	if db_type not in supported_dbs:
		print "Error: unsupported database type. Check config file"
		sys.exit(2)
	
	## Only mysql is supported right now
	DB_user=Config.get("database-mysql","user")
	DB_password=Config.get("database-mysql","pass")
	DB_host=Config.get("database-mysql","host")
	DB_database=Config.get("database-mysql","database")
	
	
	init_log(logpath)
	logger.info("Starting SmartHome Heating Programmer %s" % VERSION)
	sched = BackgroundScheduler()
	
	# Read MQTT config and connect to server
	mqtt_host = Config.get("server-mqtt","host")
	mqtt_port = Config.get("server-mqtt","port")
	mqtt_topic = Config.get("server-mqtt","topic")
	mqtt_ssl = Config.get("server-mqtt","ssl")
	mqtt_cacert = Config.get("server-mqtt","cacert")
	mqtt_clientcert = Config.get("server-mqtt","clientcert")
	mqtt_clientkey = Config.get("server-mqtt","clientkey")

	instanceName = Config.get("heatingScheduler","instanceName")
	
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

	t = threading.Thread(target=schedule_updater)
	t.daemon = True
	t.start()

	#update_schedule()
	sched.start()

	mqttClient.loop_forever()

if __name__ == "__main__":
        main(sys.argv[1:])
