#!/usr/bin/env python
import modbusdriver_pymodbus as modbusdriver
import logging
import ConfigParser

logger = logging.getLogger("smarthome.sdm220")

class Driver:
	def __init__(self, deviceName, config):
		logger.debug("initializing SDM 220 device: %s" % deviceName)
		self.deviceName = deviceName
		address = config.get(deviceName,"modbus-address")
		logger.debug("Setting SDM220 modbus address %s" % address)
		self.address = int(address)
		self.maxpower = config.get(deviceName,"maxpower")

	def getName(self):
		return self.deviceName

	def getType(self):
		return "Powermeter"

	def getGettableVars(self):
		return ["volt","current","power","appower","repower","pfactor","phase","freq","acciae","acceae","accire","accere","totact","totrea","maxpower"]

	def getValue(self,key):
		if key == "maxpower":
			return self.maxpower
		elif key == "volt":
			# 30001 - Voltage - Spannung - Volts
			voltage = self.sdm220_request(0)
			logger.info("Voltage: %s V" % voltage)
			return voltage
		elif key == "current":
			# 30007 - Current - Ampere - Amps
			current = self.sdm220_request(6)
			logger.info("Current: %s A" % current)
			return current
		elif key == "power":
			# 30013 - Active Power - Wirkleistung - Watts
			power = self.sdm220_request(12)
			logger.info("Power: %s W" % power)
			return power
		elif key == "appower":
			# 30019 - Apparent power - Scheinleistung - VoltAmps
			aap = self.sdm220_request(18)
			logger.info("Active Apparent Power: %s VA" % aap)
			return aap
		elif key == "repower":
			# 30025 - Reactive power - Blindleistung - VAr
			rap = self.sdm220_request(24)
			logger.info("Reactive Apparent Power: %s VAr" % rap)
			return rap
		elif key == "pfactor":
			# 30031 - Power factor - Leistungsfaktor
			pfactor = self.sdm220_request(30)
			logger.info("Power Factor: %s" % pfactor)
			return pfactor
		elif key == "phase":
			# 30037 - Phase angle - Phasenverschiebungswinkel - Grad
			phaseangle = self.sdm220_request(36)
			logger.info("Phase angle: %s deg" % phaseangle)
			return phaseangle
		elif key == "freq":
			# 30071 - Frequency - Frequenz - Hz
			freq = self.sdm220_request(70)
			logger.info("Frequency: %s Hz" % freq)
			return freq
		elif key == "acciae":
			# 30073 - Import active energy - Import kumulierte Wirkleistung - kwh
			iae = self.sdm220_request(72)
			logger.info("Import Active Energy: %s kwh" % iae)
			return iae
		elif key == "acceae":
			# 30075 - Export active energy - Export kumulierte Wirkleistung - kwh
			eae = self.sdm220_request(74)
			logger.info("Export Active Energy: %s kwh" % eae)
			return eae
		elif key == "accire":
			# 30077 - Import reactive energy - Import kumulierte Blindleistung - kvarh
			ire = self.sdm220_request(76)
			logger.info("Import Reactive Energy: %s kvarh" % ire)
			return ire
		elif key == "accere":
			# 30079 - Export reactive energy - Export kumulierte Blindleistung - kvarh
			ere = self.sdm220_request(78)
			logger.info("Export Reactive Energy: %s kvarh" % ere)
			return ere
		elif key == "totact":
			# 30343 - Total active energy - Gesamute kumulierte Wirkleistung - kwh
			tae = self.sdm220_request(342)
			logger.info("Total Active Energy: %s kwh" % tae)
			return tae
		elif key == "totrea":
			# 30345 - Total reactive energy - Gesamte kumulierte Blindleistung - kvarh
			tre = self.sdm220_request(344)
			logger.info("Total Reactive Energy: %s kvarh" % tre)
			return tre
		


	def sdm220_request(self,data_address):
		return modbusdriver.modbus_read_float(self.address,data_address)


