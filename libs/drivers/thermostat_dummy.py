#!/usr/bin/env python3
import datetime
import logging
import threading
import time


def is_modbus():
    return False


class Driver:
    temperature = 22.5
    setpoint = 24.0
    is_on = True
    sampling_period = 30  # seconds

    def __init__(self, device_id, config):
        self.logger = logging.getLogger("not_so_dumb_home.dummy_thermostat_%s" % device_id)
        self.logger.debug("initializing dummy thermostat device: %s" % device_id)
        self.device_id = device_id

        self.device_name = config["name"]
        self.outdoor_temp_topic = config["outdoor_temp_topic"]

        # Disable secondary display by default
        self.disable_sec_display()

        # Start thread to erase secondary display when no information is available
        self.outTempActive = False
        self.outTempTimeout = 15  # minutes
        self.outTempTimeSet = datetime.datetime(2000, 1, 1, 0, 0)  # Set a time in the past as initial value
        t = threading.Thread(target=self.out_temp_expiration)
        t.setDaemon(True)
        t.start()

    def out_temp_expiration(self):
        while True:
            # if secondDisplayTimeSet + secondDisplayTimeout is older than now, return true
            if self.outTempActive and (
                    self.outTempTimeSet + datetime.timedelta(minutes=self.outTempTimeout) < datetime.datetime.now()):
                self.logger.info(
                    "Timeout is expired (set on %s, now is %s)" % (self.outTempTimeSet, datetime.datetime.now()))
                self.disableSecDisplay()
            time.sleep(30)

    def get_sampling_period(self):
        return self.sampling_period

    def get_id(self):
        return self.device_id

    def get_name(self):
        return self.device_name

    def get_type(self):
        return "thermostat"

    def get_outdoor_temp_topic(self):
        return self.outdoor_temp_topic

    def get_gettable_vars(self):
        return ["curtemp", "setpoint", "isheating", "is_on"]

    def get_value(self, key):
        if key == "curtemp":
            # Current Temp
            self.logger.info("Current temperature: %s C" % self.temperature)
            return self.temperature
        elif key == "setpoint":
            # Current set point
            self.logger.info("Current setpoint: %s C" % self.setpoint)
            return self.setpoint
        elif key == "isheating":
            # Heating output - addr 31005 - cmd 0x04
            is_heating = self.is_on and (self.setpoint >= self.temperature)
            self.logger.info("Is heating: %s" % is_heating)
            if is_heating:
                return 1
            else:
                return 0
        elif key == "is_on":
            return self.is_on

    def get_settable_vars(self):
        return ["setpoint", "outtemp", "is_on"]

    def set_value(self, key, value):
        if key == "setpoint":
            # Value limits: 0 - 49 degrees
            if value < 5:
                self.logger.warning("Temperature below 5 degrees requested. Setting setpoint to minimum")
                value = 5
            elif value > 40:
                self.logger.warning("Temperature over 40 degrees requested. Setting setpoint to maximum")
                value = 40
            # Set confort setpoint
            self.logger.info("Setting setpoint to %s" % value)
            self.setpoint = value
        elif key == "outtemp":
            self.outTempActive = True
            self.outTempTimeSet = datetime.datetime.now()
            # Set secondary display to outdoor temp - addr 40007 - value 2
            self.logger.info("Activating outdoor temperature display")
            # Value limits: 0 - 49 degrees
            if value < 0:
                value = 0
            elif value > 49:
                value = 49
            # Set displayed outdoor temp - addr 40104
            self.logger.info("Setting displayed outdoor temperature to %s" % value)
        elif key == "is_on":
            self.logger.debug("is_on value is \"%s\"" % value)
            if value:
                self.logger.info("Thermostat turning ON")
                self.is_on = True
            else:
                self.logger.info("Thermostat turning OFF")
                self.is_on = False

    def disable_sec_display(self):
        # Set secondary display to nothing
        self.logger.info("Disabling outdoor temperature display")
