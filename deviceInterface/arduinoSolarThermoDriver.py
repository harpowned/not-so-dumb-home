#!/usr/bin/env python
import serial
import json
import logging
import threading
import time
import datetime

logger = logging.getLogger("smarthome.arduinoSolarThermo")

# Default serial port, in case none is provided in the config file
serial_port = "/dev/arduino"
ser = ""
lock = threading.Lock()
serialAnswerRequested = False
serialAnswer = ""

solarTimeOn = 10
solarTimeOff = 16

timeout = 5 ## seconds

def setSerialAddr(address):
	global ser
	global serial_port
	if ser:
		logger.error("Serial already open, cannot change address")
	else: 
		logger.debug("Setting serial port to %s" % address)
		serial_port = address

def serial_read():
	global ser
	global serialAnswer
	global serialAnswerRequested
	while True:
		data = ser.readline()
		print "Read from serial: %s" % data
		if serialAnswerRequested:
			serialAnswer = data

## Opening the serial will reset the Arduino board. It's important that this is only done once.
def openSerial():
	global serial_port
	global ser
	if not ser:
		ser = serial.Serial(serial_port, 9600)
		thread = threading.Thread(target=serial_read)
		thread.daemon = True
		thread.start()

def serialSendCommand(cmd):
	global ser
	ser.write(cmd+"\n")

def solar_scheduler():
	global solarTimeOn
	global solarTimeOff
	while True:
		hour = datetime.datetime.now().time().hour
		if (hour >= solarTimeOn) and (hour < solarTimeOff):
			logger.info("Sending command Solar ON")
			serialSendCommand("slr 1")
		else:
			logger.info("Sending command Solar OFF")
			serialSendCommand("slr 0")
		time.sleep(60)

def startSolarScheduler(timeOn,timeOff):
	global solarTimeOn
	global solarTimeOff
	solarTimeOn = timeOn
	solarTimeOff = timeOff
	logger.info("Starting solar scheduler. On at %s, Off at %s" % (timeOn,timeOff))
	thread = threading.Thread(target=solar_scheduler)
	thread.daemon = True
	thread.start()
	

def getStatusData(key):
	global lock
	global serialAnswer
	global serialAnswerRequested
	logger.debug("Processing request for key %s" % key)
	response = 0
	openSerial()
	with lock:
		serialAnswerRequested = True
		start = time.time()
		serialSendCommand("stt")
		while serialAnswerRequested:
			if serialAnswer:
				message = serialAnswer
				serialAnswer = ""
				try:
					json_object = json.loads(message)
					logger.debug("Received Valid json")
					response = json_object[key]
					serialAnswerRequested = False
					
				except ValueError, e:
					logger.debug("Non json received")
					pass
			## If timeout
			elapsed = time.time() - start
			logger.debug("Elapsed: %s" % elapsed)
			if elapsed > timeout:
				serialAnswerRequested = False
				raise RuntimeError()
			time.sleep(0.2)
	logger.debug("Response is %s" % response)
	return response

def getCurrentTemp():
	return getStatusData("temp")

def getCurrentSetpoint():
	return getStatusData("setpoint")

def isHeating():
	isheating = getStatusData("heating")
	if isheating == "true":
		return True
	else:
		return False

def isHeatingInt():
	if isHeating():
		return 1
	else:
		return 0

def setSetpoint(newtemp):
	logger.info("Setting setpoint not implemented")

def setOutTemp(newtemp):
	logger.info("Secondary display not available")

def disableSecDisplay():
	logger.info("Secondary display not available")

def getCurrentMode():
	isheating = getStatusData("mode")

def isSolarOn():
	return getStatusData("solar")

def isSolarInt():
	if isSolarOn():
		return 1
	else:
		return 0
