#!/usr/bin/env python
import logging
import threading
import serial
from array import *
import numpy

def is_modbus():
    return False

class Driver:
    sampling_period = 60  # seconds
    min_reading = 50 # 5 cm
    max_reading = 1500 # 150 cm
    max_queue = 30

    def __init__(self, device_id, config):
        self.logger = logging.getLogger("not_so_dumb_home.gasoilmeter%s" % device_id)
        self.logger.debug("initializing Dummy Gasoilmeter device: %s" % device_id)
        self.device_id = device_id
        self.device_name = config["name"]
        self.serial_port = config["serial_port"]
        self.capacity = int(config["capacity"])
        self.distance_full = int(config["distance_full"])
        self.distance_empty = int(config["distance_empty"])

        self.readings_queue = array('i')

        serial_thread = threading.Thread(target=self._serial_thread)
        serial_thread.start()

    def _serial_thread(self):
        ser = serial.Serial(self.serial_port, 9600)

        while True:
            line = ser.readline()
            self.logger.debug("Line received from serial: %s" % line)
            int_line = int(line)
            if self.min_reading < int_line < self.max_reading:
                self.readings_queue.append(int_line)
            else:
                self.logger.warning("Received out of range reading from sensor: %s" % int_line)
            while len(self.readings_queue)>self.max_queue:
                self.readings_queue.pop(0)

    def _get_distance(self):
        return numpy.median(self.readings_queue)

    def _get_liters(self):
        reading = self._get_distance()
        range = self.distance_empty - self.distance_full
        distance_per_liter = self.capacity / range
        corrected_reading = reading - self.distance_full
        # If we are reading fuller than full, return full and issue a warning
        if corrected_reading < self.distance_full:
            self.logger.warning("Sensor is reporting fuller than full")
            corrected_reading = self.distance_full
        # If we are reading emptier than empty, return empty and issue a warning
        if corrected_reading > self.distance_empty:
            corrected_reading = self.distance_empty
            self.logger.warning("Sensor is reporting emptier than empty")
        liters = self.capacity-(corrected_reading * distance_per_liter)
        return liters


    def _get_percentage(self):
        liters = self._get_liters()
        percentage = 100 * liters / self.capacity
        return percentage


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
            liters = self._get_liters()
            # Round to 2 decimals
            liters_str = "{:.2f}".format(liters)
            self.logger.info("Liters: %s L" % liters_str)
            return liters_str
        elif key == "percentage":
            percentage = self._get_percentage()
            # Round to 2 decimals
            percentage_str = "{:.2f}".format(percentage)
            self.logger.info("Percent: %s" % percentage_str)
            return percentage_str

    def get_settable_vars(self):
        return []
