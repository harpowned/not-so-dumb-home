#!/usr/bin/env python
import modbusdriver_pymodbus as modbusdriver
import logging

logger = logging.getLogger("smarthome.rdf302")

rdf302_address = 1

def setModbusAddr(address):
	global rdf302_address
	logger.debug("Setting RDF302 modbus address to %s" % address)
	rdf302_address = int(address)

def rdf302_read_temp(data_address):
	result = round(int(modbusdriver.modbus_read_input(rdf302_address,data_address))/float(50),2)
	return result

def rdf302_write_int(data_address,value):
	logger.debug("Writing int to rdf302. Data_address: %s Value: %s" % (data_address,value))
	logger.debug("RDF302 modbus address to %s" % rdf302_address)
	modbusdriver.modbus_write_holding(rdf302_address,data_address,value)

def rdf302_write_temp(data_address,value):
	value = int(value * 50)
	modbusdriver.modbus_write_holding(rdf302_address,data_address,value)


def rdf302_read_bool(data_address):
	value = modbusdriver.modbus_read_input(rdf302_address,data_address)
	if value == 100:
		return True
	elif value == 0:
		return False
		

def getCurrentMode():
	logger.error("getCurrentMode Not implemented")

def getCurrentTemp():
	# Current Temp - addr 31003 - cmd 0x04 
	temperature = rdf302_read_temp(1002)
	logger.info("Current temperature: %s C" % temperature)
	return temperature

def getCurrentSetpoint():
	# Current set point - addr 31004 - cmd 0x04
	temperature = rdf302_read_temp(1003)
	logger.info("Current setpoint: %s C" % temperature)
	return temperature

def isHeating():
	# Heating output - addr 31005 - cmd 0x04
	isHeating = rdf302_read_bool(1004)
	logger.info("Is heating: %s" % isHeating)
	return isHeating

def isHeatingInt():
	if isHeating():
		return 1
	else:
		return 0

def setSetpoint(newtemp):
	## Value limits: 0 - 49 degrees
	if newtemp< 5:
		newtemp = 5
	elif newtemp > 40:
		newtemp = 40
	# Set confort setpoint - addr 40103
	rdf302_write_temp(102,newtemp)

def setOutTemp(newtemp):
	# Set secondary display to outdoor temp - addr 40007 - value 2
	rdf302_write_int(006,2)
	## Value limits: 0 - 49 degrees
	if newtemp < 0:
		newtemp = 0
	elif newtemp > 49:
		newtemp = 49
	# Set displayed outdoor temp - addr 40104
	rdf302_write_temp(103,newtemp)

def disableSecDisplay():
	# Set secondary display nothing - addr 40007 - value 0
	rdf302_write_int(006,0)
