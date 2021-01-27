#!/usr/bin/env python
import minimalmodbus
import threading
import logging
import serial
import time

logger = logging.getLogger("smarthome.modbusdriver")

mutex = threading.Lock()

instruments = {}


def instrument_init(addr):
	global instruments
	logger.debug("Checking for initialization for device %s" % addr)
	if addr not in instruments:
		logger.debug("Device is not initialized")
		instrument = minimalmodbus.Instrument('/dev/rs485', addr) # port name, slave address (in decimal)
		instrument.serial.baudrate=9600
		instrument.serial.parity = serial.PARITY_EVEN
		instrument.debug = True
		instruments[addr] = instrument
		
		

def modbus_read_float(device,address):
	global instruments
	global mutex
	instrument_init(device)
	instrument = instruments[device]
	logger.debug("Acquiring mutex for query to %s" % address)
	mutex.acquire()
	logger.debug("Acquired mutex for query to %s" % address)
	time.sleep(0.5)
	logger.debug("Performing modbus call for query to %s" % address)
	try:
		result = round(instrument.read_float(address, functioncode=4),1)
	except:
		logger.debug("Exception on serial read from device %s, retrying.." % device)
		instruments = {}
		instrument_init(device)
		instrument = instruments[device]
		try:
			result = round(instrument.read_float(address, functioncode=4),1)
		except:
			logger.debug("Exception on serial read from device %s on retry. Dying.." % device)
			sys.exit(0)
	logger.debug("Modbus call done for query to %s, result is %s" % (address,result))
	mutex.release()
	logger.debug("Released mutex for query to %s" % address)
	return result

def modbus_read_input(device,address):
	instrument_init(device)
	instrument = instruments[device]
	global mutex
	logger.debug("Acquiring mutex for query to %s" % address)
	mutex.acquire()
	logger.debug("Acquired mutex for query to %s" % address)
	time.sleep(0.5)
	logger.debug("Performing modbus call for query to %s" % address)
	result = instrument.read_register(address, functioncode=4)
	logger.debug("Modbus call done for query to %s, result is %s" % (address,result))
	mutex.release()
	logger.debug("Released mutex for query to %s" % address)
	return result
