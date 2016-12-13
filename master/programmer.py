#!/usr/bin/python
import mysql.connector
import time
from apscheduler.schedulers.blocking import BlockingScheduler
import datetime
import thermo_control
import threading
import logging
from logging.handlers import RotatingFileHandler
import traceback
import os
import mail_sender

VERSION="1.0"

logpath="/var/log/smarthome/programmer.log"


global logger
logger = logging.getLogger("programmer")

DB_user='smarthome'
DB_password='aaaaaaaa'
DB_host='127.0.0.1'
DB_database='smarthome'

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
        global logger
        logger.setLevel(logging.DEBUG)

        # add a rotating handler
        file_handler = RotatingFileHandler(path, maxBytes=10*1024*1024,backupCount=5)
        file_formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        # set a format which is simpler for console use
        console_formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        # tell the handler to use this format
        console.setFormatter(console_formatter)
        # add the handler to the root logger
        logging.getLogger('').addHandler(console)

def setTemp(temp):
	thermo_control.setTemp(temp)

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
			cnx.close()
			return set_temp
		cursor.execute(query_2, [q_dow])
		for (temp) in cursor:
			logger.debug("Last temp was set same week, and is %s" % temp)
			set_temp = temp[0]
			result = True
		if result:
			cnx.close()
			return set_temp
		cursor.execute(query_3, [q_dow])
		for (temp) in cursor:
			logger.debug("Last temp was set last week, and is %s" % temp)
			set_temp = temp[0]
			result = True
		if result:
			cnx.close()
			return set_temp
		cursor.execute(query_4, [q_dow,q_time])
		for (temp) in cursor:
			logger.debug("Last temp was set last week, on the same day, and is %s" % temp)
			set_temp = temp[0]
			result = True
		if result:
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
	cnx.close()
	logger.debug("Are we in exception at %s? %s" % (date,in_exception))
	return in_exception

def schedule_updater():
	current_jobs = ""
	last_updated = False
	while True:
		try:
#			logger.debug("Now updating schedule")
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
	cnx.close()


## Main function
init_log(logpath)
logger.info("Starting SmartHome Programmer %s" % VERSION)
sched = BlockingScheduler()

t = threading.Thread(target=schedule_updater)
t.daemon = True
t.start()

#update_schedule()
sched.start()
