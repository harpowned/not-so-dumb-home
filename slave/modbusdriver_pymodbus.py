#!/usr/bin/env python
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import threading
import logging
import serial
import time
import struct

logger = logging.getLogger("smarthome.modbusdriver")

mutex = threading.Lock()

global serialclient


serialclient = ModbusClient(method='rtu', port='/dev/rs485', timeout=0.125, baudrate=9600, parity=serial.PARITY_EVEN)
serialclient.connect()

def modbus_read_float(device,address):
	global serialclient
	global mutex
	logger.debug("Acquiring mutex for query to %s" % address)
	mutex.acquire()
	logger.debug("Acquired mutex for query to %s" % address)
	logger.debug("Performing modbus call for query to %s" % address)
	resp = serialclient.read_input_registers(address,2, unit=device)
	result = round(struct.unpack('>f',struct.pack('>HH',*resp.registers))[0],1)
	logger.debug("Modbus call done for query to %s, result is %s" % (address,result))
	mutex.release()
	logger.debug("Released mutex for query to %s" % address)
	return result

def modbus_read_input(device,address):
	global serialclient
	global mutex
	logger.debug("Acquiring mutex for query to %s" % address)
	mutex.acquire()
	logger.debug("Acquired mutex for query to %s" % address)
	logger.debug("Performing modbus call for query to %s" % address)
	result = serialclient.read_input_registers(address,1, unit=device).registers[0]
	logger.debug("Modbus call done for query to %s, result is %s" % (address,result))
	mutex.release()
	logger.debug("Released mutex for query to %s" % address)
	return result

def modbus_write_holding(device,address,value):
	global serialclient
	global mutex
	logger.debug("Acquiring mutex for query to %s" % address)
	mutex.acquire()
	logger.debug("Acquired mutex for query to %s" % address)
	logger.debug("Performing modbus call for query to %s" % address)
	result = serialclient.write_register(address,value,unit=device)
	logger.debug("Modbus call done for query to %s, result is %s" % (address,result))
	mutex.release()
	logger.debug("Released mutex for query to %s" % address)
	return result
