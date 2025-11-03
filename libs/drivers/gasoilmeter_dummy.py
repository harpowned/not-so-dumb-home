#!/usr/bin/env python
import logging

def is_modbus():
    return False

class Driver:
    sampling_period = 5  # seconds

    def __init__(self, device_id, config):
        self.logger = logging.getLogger("not_so_dumb_home.gasoilmeter%s" % device_id)
        self.logger.debug("initializing Dummy Gasoilmeter device: %s" % device_id)
        self.device_id = device_id
        self.device_name = config["name"]
        self.capacity = config["capacity"]

    def get_sampling_period(self):
        return self.sampling_period

    def get_id(self):
        return self.device_id

    def get_name(self):
        return self.device_name

    def get_type(self):
        return "gasoilmeter"

    def get_gettable_vars(self):
        return ["level", "percentage", "capacity"]

    def get_value(self, key):
        if key == "capacity":
            return self.capacity
        elif key == "level":
            liters = 400.5
            self.logger.info("Liters: %s L" % liters)
            return liters
        elif key == "percentage":
            percent = 40.2
            self.logger.info("Percent: %s" % percent)
            return percent

    def get_settable_vars(self):
        return []
