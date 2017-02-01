#!/usr/bin/env python
import logging

logger = logging.getLogger("smarthome.nullThermo")


def getCurrentMode():
	logger.error("getCurrentMode Not implemented")

def getCurrentTemp():
	temperature = 20
	logger.info("Current temperature: %s C" % temperature)
	return temperature

def getCurrentSetpoint():
	temperature = 20
	logger.info("Current setpoint: %s C" % temperature)
	return temperature

def isHeating():
	isHeating = True
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
	logger.info("Setpoint set to %s" % newtemp)

def setOutTemp(newtemp):
	## Value limits: 0 - 49 degrees
	if newtemp < 0:
		newtemp = 0
	elif newtemp > 49:
		newtemp = 49
	logger.info("Outdoor temp display set to %s" % newtemp)

def disableSecDisplay():
	logger.info("Outdoor temp display disabled")
