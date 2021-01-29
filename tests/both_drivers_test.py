#!/usr/bin/env python3
import time
from libs.drivers import thermostat_rdf302 as tslib
from libs.drivers import powermeter_sdm220 as pmlib

tsconfig = {}
tsconfig["name"] = "test thermostat"
tsconfig["modbus-address"] = 2
tsconfig["outdoor_temp_topic"] = ""
ts = tslib.Driver("test_thermostat", tsconfig)

pmconfig = {}
pmconfig["name"] = "test powermeter"
pmconfig["modbus-address"] = 1
pmconfig["maxpower"] = 1000
pm = pmlib.Driver("test_powermeter", pmconfig)

def ts_get_values():
    curtemp = ts.get_value("curtemp")
    print("Current temp is %s" % curtemp)
    setpoint = ts.get_value("setpoint")
    print("Setpoint is %s" % setpoint)
    isheating = ts.get_value("isheating")
    print("Is heating is %s" % isheating)
    is_on = ts.get_value("is_on")
    print("Is on is %s" % is_on)

def pm_get_values():
    voltage = pm.get_value("volt")
    print("Voltage is %s" % voltage)
    current = pm.get_value("current")
    print("Current is %s" % current)
    power = pm.get_value("power")
    print("Power is %s" % power)

while True:
    ts_get_values()
    pm_get_values()