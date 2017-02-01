#!/usr/bin/env python
import logging

logger = logging.getLogger("smarthome.nullPowerMeter")

sdm220_address = 1 ## Modbus address of device


def getVoltage():
	voltage = 220
	logger.info("Voltage: %s V" % voltage)
	return voltage

def getCurrent():
	current = 1
	logger.info("Current: %s A" % current)
	return current

def getPower():
	power = 220
	logger.info("Power: %s W" % power)
	return power

def getApPower():
	aap = 1
	logger.info("Active Apparent Power: %s VA" % aap)
	return aap

def getRePower():
	rap = 1
	logger.info("Reactive Apparent Power: %s VAr" % rap)
	return rap

def getPowerFactor():
	pfactor = 1
	logger.info("Power Factor: %s" % pfactor)
	return pfactor

def getPhaseAngle():
	phaseangle = 0
	logger.info("Phase angle: %s deg" % phaseangle)
	return phaseangle

def getFrequency():
	freq = 60
	logger.info("Frequency: %s Hz" % freq)
	return freq

def getAccImportActiveEnergy():
	iae = 1000
	logger.info("Import Active Energy: %s kwh" % iae)
	return iae

def getAccExportActiveEnergy():
	eae = 1000
	logger.info("Export Active Energy: %s kwh" % eae)
	return eae

def getAccImportReactiveEnergy():
	ire = 1000
	logger.info("Import Reactive Energy: %s kvarh" % ire)
	return ire

def getAccExportReactiveEnergy():
	ere = 1000
	logger.info("Export Reactive Energy: %s kvarh" % ere)
	return ere

def getAccTotalActiveEnergy():
	tae = 1000
	logger.info("Total Active Energy: %s kwh" % tae)
	return tae

def getAccTotalReactiveEnergy():
	tre = 1000
	logger.info("Total Reactive Energy: %s kvarh" % tre)
	return tre

