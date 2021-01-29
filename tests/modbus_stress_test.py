#!/usr/bin/env python3
import time
import os, sys

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append("%s/libs/drivers/modbus" % parentdir)

import modbusdriver_pymodbus as modbus

sdm220_address = 1
rdf302_address = 2

modbus_driver = modbus.ModbusDriver()


def read_sdm220_data():
    voltage = modbus_driver.modbus_read_float(sdm220_address, 0)
    print(" * Voltage: %s" % voltage)
    current = modbus_driver.modbus_read_float(sdm220_address, 6)
    print(" * Current is %s" % current)
    power = modbus_driver.modbus_read_float(sdm220_address, 12)
    print(" * Power is %s" % power)
    aap = modbus_driver.modbus_read_float(sdm220_address, 18)
    print(" * Apparent active power is %s" % aap)
    rep = modbus_driver.modbus_read_float(sdm220_address, 24)
    print(" * Reactive apparent power is %s" % rep)
    pfactor = modbus_driver.modbus_read_float(sdm220_address, 30)
    print(" * power factor is %s" % pfactor)
    phase = modbus_driver.modbus_read_float(sdm220_address, 36)
    print(" * Phase is %s" % phase)


def rdf302_read_temp(data_address):
    result = round(int(modbus_driver.modbus_read_input(rdf302_address, data_address)) / float(50), 2)
    return result


def read_rdf302_data():
    curtemp = rdf302_read_temp(1002)
    print(" * Current temperature is %s" % curtemp)
    setpoint = rdf302_read_temp(1003)
    print(" * Setpoint is %s" % setpoint)
    is_heating = modbus_driver.modbus_read_input(rdf302_address, 1004)
    print(" * Is heating is %s" % is_heating)


def rdf302_set_setpoint(new_temp):
    print(" * Setting setpoint to %s" % new_temp)
    value = int(new_temp * 50)
    modbus_driver.modbus_write_holding(rdf302_address, 102, value)

def rdf302_extended_test():
    time.sleep(1)
    rdf302_set_setpoint(15)
    read_rdf302_data()
    time.sleep(1)
    rdf302_set_setpoint(27)
    read_rdf302_data()

while True:
    read_sdm220_data()
    read_rdf302_data()
    #rdf302_extended_test()
