import datetime
import logging
import threading
import time


class Driver:
    sampling_period = 15

    def __init__(self, device_id, config, modbus_driver):
        self.logger = logging.getLogger("not_so_dumb_home.dummy_thermostat_%s" % device_id)
        self.logger.debug("initializing RDF 302 device: %s" % device_id)
        self.device_id = device_id
        self.modbus_driver = modbus_driver

        self.device_name = config["name"]
        self.outdoor_temp_topic = config["outdoor_temp_topic"]

        address = config["modbus-address"]
        self.logger.debug("Setting RDF302 modbus address %s" % address)
        self.address = int(address)

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
            if (self.outTempActive) and (
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
            # Current Temp - addr 31003 - cmd 0x04
            temperature = self.rdf302_read_temp(1002)
            self.logger.info("Current temperature: %s C" % temperature)
            return temperature
        elif key == "setpoint":
            # Current set point - addr 31004 - cmd 0x04
            temperature = self.rdf302_read_temp(1003)
            self.logger.info("Current setpoint: %s C" % temperature)
            return temperature
        elif key == "isheating":
            # Heating output - addr 31005 - cmd 0x04
            is_heating = self.rdf302_read_bool(1004)
            self.logger.info("Is heating: %s" % is_heating)
            if is_heating:
                return 1
            else:
                return 0
        elif key == "is_on":
            is_on = self.rdf302_read_int(1000)
            self.logger.info("Is on: %s" % is_on)
            return is_on == 1

    def get_settable_vars(self):
        return ["setpoint", "outtemp", "is_on"]

    def set_value(self, key, value):
        if key == "setpoint":
            ## Value limits: 0 - 49 degrees
            if value < 5:
                self.logger.warning("Temperature below 5 degrees requested. Setting setpoint to minimum")
                value = 5
            elif value > 40:
                self.logger.warning("Temperature over 40 degrees requested. Setting setpoint to maximum")
                value = 40
            # Set confort setpoint - addr 40103
            self.rdf302_write_temp(102, value)
        elif key == "outtemp":
            self.outTempActive = True
            self.outTempTimeSet = datetime.datetime.now()
            # Set secondary display to outdoor temp - addr 40007 - value 2
            self.rdf302_write_int(6, 2)
            ## Value limits: 0 - 49 degrees
            if value < 0:
                value = 0
            elif value > 49:
                value = 49
            # Set displayed outdoor temp - addr 40104
            self.rdf302_write_temp(103, value)
        # When the thermostat is put into protection mode via modbus,
        # it's not possible to turn it on again (comfort) via HMI.
        # So let's disable the command, unless we find a solution.
        elif key == "is_on" and False:
            if value:
                self.rdf302_write_int(100, 1)
            else:
                self.rdf302_write_int(100, 4)

    def rdf302_read_temp(self, data_address):
        result = round(int(self.modbus_driver.modbus_read_input(self.address, data_address)) / float(50), 2)
        return result

    def rdf302_write_int(self, data_address, value):
        self.logger.debug("Writing int to rdf302. Data_address: %s Value: %s" % (data_address, value))
        self.modbus_driver.modbus_write_holding(self.address, data_address, value)

    def rdf302_write_temp(self, data_address, value):
        value = int(value * 50)
        self.modbus_driver.modbus_write_holding(self.address, data_address, value)

    def rdf302_read_bool(self, data_address):
        value = self.modbus_driver.modbus_read_input(self.address, data_address)
        if value == 100:
            return True
        elif value == 0:
            return False

    def rdf302_read_int(self, data_address):
        value = self.modbus_driver.modbus_read_input(self.address, data_address)
        return value

    def disable_sec_display(self):
        # Set secondary display nothing - addr 40007 - value 0
        self.rdf302_write_int(6, 0)
