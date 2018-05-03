#!/usr/bin/env python
import modbusdriver_pymodbus as modbusdriver
import logging
import ConfigParser
import threading
import time
import datetime

logger = logging.getLogger("smarthome.rdf302")

class Driver:

	def __init__(self, deviceName, config):
		logger.debug("initializing RDF 302 device: %s" % deviceName)
		self.deviceName = deviceName
		address = config.get(deviceName,"modbus-address")
		logger.debug("Setting RDF302 modbus address %s" % address)
		self.address = int(address)

		# Disable secondary display by default
		self.disableSecDisplay()

		# Start thread to erase secondary display when no information is available
		self.outTempActive = False
		self.outTempTimeout = 15 # minutes
		self.outTempTimeSet = datetime.datetime(2000,1,1,0,0) # Set a time in the past as initial value
		t = threading.Thread(target=self.outTempExpiration)
		t.setDaemon(True)
		t.start()
		
	def outTempExpiration(self):
		while True:
			# if secondDisplayTimeSet + secondDisplayTimeout is older than now, return true
			if (self.outTempActive) and (self.outTempTimeSet + datetime.timedelta(minutes=self.outTempTimeout) < datetime.datetime.now()):
				logger.info("Timeout is expired (set on %s, now is %s)" % (self.outTempTimeSet,datetime.datetime.now()))
				self.disableSecDisplay()
			time.sleep(30)

	def getName(self):
		return self.deviceName

	def getType(self):
		return "Thermostat"

	def getGettableVars(self):
		return ["curtemp","setpoint","isheating"]

	def getValue(self,key):
		if key == "curtemp":
			# Current Temp - addr 31003 - cmd 0x04 
			temperature = self.rdf302_read_temp(1002)
			logger.info("Current temperature: %s C" % temperature)
			return temperature
		elif key == "setpoint":
			# Current set point - addr 31004 - cmd 0x04
			temperature = self.rdf302_read_temp(1003)
			logger.info("Current setpoint: %s C" % temperature)
			return temperature
		elif key == "isheating":
			# Heating output - addr 31005 - cmd 0x04
			isHeating = self.rdf302_read_bool(1004)
			logger.info("Is heating: %s" % isHeating)
			if isHeating:
				return 1
			else:
				return 0

	def getSettableVars(self):
		return ["setpoint","outtemp"]

	def setValue(self,key,value):
		if key == "setpoint":
			## Value limits: 0 - 49 degrees
			if value< 5:
				logger.warn("Temperature below 5 degrees requested. Setting setpoint to minimum")
				value = 5
			elif value > 40:
				logger.warn("Temperature over 40 degrees requested. Setting setpoint to maximum")
				value = 40
			# Set confort setpoint - addr 40103
			self.rdf302_write_temp(102,value)
		elif key == "outtemp":
			self.outTempActive = True
			self.outTempTimeSet= datetime.datetime.now()
			# Set secondary display to outdoor temp - addr 40007 - value 2
			self.rdf302_write_int(006,2)
			## Value limits: 0 - 49 degrees
			if value < 0:
				value = 0
			elif value > 49:
				value = 49
			# Set displayed outdoor temp - addr 40104
			self.rdf302_write_temp(103,value)
	
	def rdf302_read_temp(self,data_address):
		result = round(int(modbusdriver.modbus_read_input(self.address,data_address))/float(50),2)
		return result

	def rdf302_write_int(self,data_address,value):
		logger.debug("Writing int to rdf302. Data_address: %s Value: %s" % (data_address,value))
		modbusdriver.modbus_write_holding(self.address,data_address,value)

	def rdf302_write_temp(self,data_address,value):
		value = int(value * 50)
		modbusdriver.modbus_write_holding(self.address,data_address,value)

	def rdf302_read_bool(self,data_address):
		value = modbusdriver.modbus_read_input(self.address,data_address)
		if value == 100:
			return True
		elif value == 0:
			return False		



	def disableSecDisplay(self):
		# Set secondary display nothing - addr 40007 - value 0
		self.rdf302_write_int(006,0)
