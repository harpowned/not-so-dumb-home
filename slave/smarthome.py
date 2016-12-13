#!/usr/bin/env python
import sdm220driver as powermeter
import rdf302driver as thermostat
import zabbixSender as zabbix
import sys
import time
import socket
import logging
import threading
import traceback
import os
from logging.handlers import RotatingFileHandler
import datetime

VERSION="1.5"

logpath="/var/log/smarthome/smarthome.log"


logger = logging.getLogger("smarthome")

secondDisplayOutdoor = False
secondDisplayTimeout = 15 # minutes
secondDisplayTimeSet = datetime.datetime(2000,1,1,0,0)

 
#----------------------------------------------------------------------

def die():
	#print(traceback.format_exc())
	logger.error(traceback.format_exc())
	logger.error("Error detected, application is Dying!")
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
	console_formatter = logging.Formatter('%(asctime)s %(name)-12s: %(levelname)-8s %(message)s')
	# tell the handler to use this format
	console.setFormatter(console_formatter)
	# add the handler to the root logger
	logging.getLogger('').addHandler(console)

def is_number(s):
	try:
		float(s)
		return True
	except ValueError:
		return False


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


class commandServer(threading.Thread):
	def __init__(self, (socket,address)):
		threading.Thread.__init__(self)
		self.socket = socket
		self.address= address

	def run(self):
		global secondDisplayOutdoor
		try:
			logger.debug('%s connected.',self.address)
			data = self.socket.recv(1024)
			if data.startswith("pm_getvolt"):
				self.socket.send(str(powermeter.getVoltage()))
			elif data.startswith("pm_getcurrent"):
				self.socket.send(str(powermeter.getCurrent()))
			elif data.startswith("pm_getpower"):
				self.socket.send(str(powermeter.getPower()))
			elif data.startswith("pm_getappower"):
				self.socket.send(str(powermeter.getApPower()))
			elif data.startswith("pm_getrepower"):
				self.socket.send(str(powermeter.getRePower()))
			elif data.startswith("pm_getpfactor"):
				self.socket.send(str(powermeter.getPowerFactor()))
			elif data.startswith("pm_getphase"):
				self.socket.send(str(powermeter.getPhaseAngle()))
			elif data.startswith("pm_getfreq"):
				self.socket.send(str(powermeter.getFrequency()))
			elif data.startswith("pm_getacciae"):
				self.socket.send(str(powermeter.getAccImportActiveEnergy()))
			elif data.startswith("pm_getacceae"):
				self.socket.send(str(powermeter.getAccExportActiveEnergy()))
			elif data.startswith("pm_getaccire"):
				self.socket.send(str(powermeter.getAccImportReactiveEnergy()))
			elif data.startswith("pm_getaccere"):
				self.socket.send(str(powermeter.getAccExportReactiveEnergy()))
			elif data.startswith("pm_gettotact"):
				self.socket.send(str(powermeter.getAccTotalActiveEnergy()))
			elif data.startswith("pm_gettotrea"):
				self.socket.send(str(powermeter.getAccTotalReactiveEnergy()))
			elif data.startswith("ts_getcurtemp"):
				self.socket.send(str(thermostat.getCurrentTemp()))
			elif data.startswith("ts_getsetpoint"):
				self.socket.send(str(thermostat.getCurrentSetpoint()))
			elif data.startswith("ts_isheating"):
				self.socket.send(str(thermostat.isHeatingInt()))
			elif data.startswith("ts_setouttemp"):
				newtemp = data[14:]
				if is_number(newtemp):
					thermostat.setOutTemp(float(newtemp))
					secondDisplayOutdoor = True
					refreshOutTempTimeout()
			elif data.startswith("ts_disseconddisplay"):
				thermostat.disableSecDisplay()
			elif data.startswith("ts_settemp"):
				newtemp = data[11:]
				if is_number(newtemp):
					thermostat.setSetpoint(float(newtemp))
			elif data.startswith("kill"):
				self.socket.send("killing")
				sys.exit(0)
				self.socket.close()
			logger.debug('%s disconnected.',self.address)
		except:
			die()
		
	
def command_server():
	while True:
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.bind(("",1545))
			s.listen(4)
			while True:
				commandServer(s.accept()).start()
		except Exception:
			die()

def zabbix_scheduledPush():
	global secondDisplayOutdoor
	while True:
		try:
			## Check if the outdoor thermometer data showing stale data. Disable display if it is.
			if (secondDisplayOutdoor and isOutTempTimeoutExpired()):
				secondDisplayOutdoor = False
				thermostat.disableSecDisplay()
			zabbix.pushData("powermeter","power",powermeter.getPower())
			zabbix.pushData("powermeter","volt",powermeter.getVoltage())
			zabbix.pushData("powermeter","current",powermeter.getCurrent())
			zabbix.pushData("powermeter","appower",powermeter.getApPower())
			zabbix.pushData("powermeter","repower",powermeter.getRePower())
			zabbix.pushData("powermeter","pfactor",powermeter.getPowerFactor())
#			zabbix.pushData("powermeter","phase",powermeter.getPhaseAngle())
#			zabbix.pushData("powermeter","freq",powermeter.getFrequency())
			zabbix.pushData("powermeter","acciae",powermeter.getAccImportActiveEnergy())
			zabbix.pushData("powermeter","accire",powermeter.getAccImportReactiveEnergy())
			zabbix.pushData("powermeter","acceae",powermeter.getAccExportActiveEnergy())
			zabbix.pushData("powermeter","accere",powermeter.getAccExportReactiveEnergy())
			total_act = powermeter.getAccTotalActiveEnergy()
			zabbix.pushData("powermeter","totact",total_act)
			total_rea = powermeter.getAccTotalReactiveEnergy()
			zabbix.pushData("powermeter","totrea",total_rea)
			zabbix.pushData("thermostat","curtemp",thermostat.getCurrentTemp())
			zabbix.pushData("thermostat","setpoint",thermostat.getCurrentSetpoint())
			zabbix.pushData("thermostat","isheating",thermostat.isHeatingInt())
		except:
			die()
		time.sleep(60)

def main(args):
	init_log(logpath)
	logger.info("Starting SmartHome %s" % VERSION)

	if "-t" in args:
		logger.info("Test mode run")
		print_powermeter()
		print_thermostat()
		sys.exit()

	# As a default, we want to start with the secondary display disabled.
	# It will be enabled the first time an outdoor temp reading is received
	thermostat.disableSecDisplay()

	# Start the command server
	t = threading.Thread(target=command_server)
	t.daemon = True
	t.start()


	zabbix_scheduledPush()

if __name__ == "__main__":
        main(sys.argv[1:])
