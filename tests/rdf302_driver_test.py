#!/usr/bin/env python3
import time
from libs.drivers import thermostat_rdf302 as tslib

config = {}
config["name"] = "test thermostat"
config["modbus-address"] = 2
config["outdoor_temp_topic"] = ""

ts = tslib.Driver("test_thermostat", config)

def get_values():
    curtemp = ts.get_value("curtemp")
    print("Current temp is %s" % curtemp)
    setpoint = ts.get_value("setpoint")
    print("Setpoint is %s" % setpoint)
    isheating = ts.get_value("isheating")
    print("Is heating is %s" % isheating)
    is_on = ts.get_value("is_on")
    print("Is on is %s" % is_on)

while True:
    #get_values()
    is_on = ts.get_value("is_on")
    print("Is on is %s" % is_on)
    time.sleep(10)
    print("Turning ON")
    ts.set_value("is_on", True)
    is_on = ts.get_value("is_on")
    print("Is on is %s" % is_on)
    time.sleep(10)
    print("Turning OFF")
    ts.set_value("is_on", False)
    is_on = ts.get_value("is_on")
    print("Is on is %s" % is_on)