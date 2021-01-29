#!/usr/bin/env python
import logging
import threading
import time

import modbus_tk.defines as cst
import serial
from modbus_tk import modbus_rtu

logger = logging.getLogger("smarthome.modbusdriver")

mutex = threading.Lock()

instruments = {}
serialclient = ""


def serial_init():
    global serialclient
    global logger
    serialclient = modbus_rtu.RtuMaster(
        serial.Serial(port="/dev/ttyUSB0", baudrate=9600, bytesize=8, parity='E', stopbits=1, xonxoff=0))
    serialclient.set_timeout(5.0)
    serialclient.set_verbose(True)
    logger.info("connected")


def modbus_read_float(device, address):
    global serialclient
    global mutex
    logger.debug("Acquiring mutex for query to %s" % address)
    mutex.acquire()
    logger.debug("Acquired mutex for query to %s" % address)
    time.sleep(0.5)
    logger.debug("Performing modbus call for query to %s" % address)
    serialclient.execute(2, cst.READ_HOLDING_REGISTERS, 100, 4)
    #	result = round(instrument.read_float(address, functioncode=4),1)
    logger.debug("Modbus call done for query to %s, result is %s" % (address, result))
    mutex.release()
    logger.debug("Released mutex for query to %s" % address)
    return result


def modbus_read_input(device, address):
    global serialclient
    global mutex
    logger.debug("Acquiring mutex for query to %s" % address)
    mutex.acquire()
    logger.debug("Acquired mutex for query to %s" % address)
    time.sleep(0.5)
    logger.debug("Performing modbus call for query to %s" % address)
    #	result = instrument.read_register(address, functioncode=4)
    logger.debug("Modbus call done for query to %s, result is %s" % (address, result))
    mutex.release()
    logger.debug("Released mutex for query to %s" % address)
    return result
