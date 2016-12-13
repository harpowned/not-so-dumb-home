#!/usr/bin/env python
import modbusdriver_pymodbus as modbusdriver
import logging

logger = logging.getLogger("smarthome.sdm220")

sdm220_address = 1 ## Modbus address of device

def sdm220_request(data_address):
	return modbusdriver.modbus_read_float(sdm220_address,data_address)

def getVoltage():
	# 30001 - Voltage - Spannung - Volts
	voltage = sdm220_request(0)
	logger.info("Voltage: %s V" % voltage)
	return voltage

def getCurrent():
	# 30007 - Current - Ampere - Amps
	current = sdm220_request(6)
	logger.info("Current: %s A" % current)
	return current

def getPower():
	# 30013 - Active Power - Wirkleistung - Watts
	power = sdm220_request(12)
	logger.info("Power: %s W" % power)
	return power

def getApPower():
	# 30019 - Apparent power - Scheinleistung - VoltAmps
	aap = sdm220_request(18)
	logger.info("Active Apparent Power: %s VA" % aap)
	return aap

def getRePower():
	# 30025 - Reactive power - Blindleistung - VAr
	rap = sdm220_request(24)
	logger.info("Reactive Apparent Power: %s VAr" % rap)
	return rap

def getPowerFactor():
	# 30031 - Power factor - Leistungsfaktor
	pfactor = sdm220_request(30)
	logger.info("Power Factor: %s" % pfactor)
	return pfactor

def getPhaseAngle():
	# 30037 - Phase angle - Phasenverschiebungswinkel - Grad
	phaseangle = sdm220_request(36)
	logger.info("Phase angle: %s deg" % phaseangle)
	return phaseangle

def getFrequency():
	# 30071 - Frequency - Frequenz - Hz
	freq = sdm220_request(70)
	logger.info("Frequency: %s Hz" % freq)
	return freq

def getAccImportActiveEnergy():
	# 30073 - Import active energy - Import kumulierte Wirkleistung - kwh
	iae = sdm220_request(72)
	logger.info("Import Active Energy: %s kwh" % iae)
	return iae

def getAccExportActiveEnergy():
	# 30075 - Export active energy - Export kumulierte Wirkleistung - kwh
	eae = sdm220_request(74)
	logger.info("Export Active Energy: %s kwh" % eae)
	return eae

def getAccImportReactiveEnergy():
	# 30077 - Import reactive energy - Import kumulierte Blindleistung - kvarh
	ire = sdm220_request(76)
	logger.info("Import Reactive Energy: %s kvarh" % ire)
	return ire

def getAccExportReactiveEnergy():
	# 30079 - Export reactive energy - Export kumulierte Blindleistung - kvarh
	ere = sdm220_request(78)
	logger.info("Export Reactive Energy: %s kvarh" % ere)
	return ere

def getAccTotalActiveEnergy():
	# 30343 - Total active energy - Gesamute kumulierte Wirkleistung - kwh
	tae = sdm220_request(342)
	logger.info("Total Active Energy: %s kwh" % tae)
	return tae

def getAccTotalReactiveEnergy():
	# 30345 - Total reactive energy - Gesamte kumulierte Blindleistung - kvarh
	tre = sdm220_request(344)
	logger.info("Total Reactive Energy: %s kvarh" % tre)
	return tre

