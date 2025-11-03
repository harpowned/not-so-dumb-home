import datetime
import logging
import threading
import time

def is_modbus():
    return True

class Driver:
    sampling_period = 15
    off_temperature = 18

    # A note on turning the thermostat on/off:
    #   When the thermostat is put into protection mode via modbus, it's not possible to turn it on again (comfort) via
    #   HMI.
    #   So let's disable the command, unless we find a solution.
    #
    #   However, because of the way the Home Assistant integration works, we still need to be able to turn the
    #   thermostat on/off via a command.
    #   The trick we'll do is that any temperature at or below 18ºC is considered OFF.
    #   So, sending the command to turn the thermostat OFF will not put it into protection mode, but will set the
    #   temperature a configurable temperature temp_low, which must be below 18, effectively turning it off.
    #
    #   When the command to turn on is received, the Modbus thermostat has no way to remember at which temperature
    #   the setpoint was before it was turned off, so we'll have to use a configurable temp_high value.
    #
    #   Both temp_high and temp_low are configurable (and should be adjustable from the interface), and it's this
    #   module's responsibility to persist that configuration across reboots.

    def __init__(self, device_id, config, modbus_driver):
        self.logger = logging.getLogger("not_so_dumb_home.dummy_thermostat_%s" % device_id)
        self.logger.debug("initializing RDF 302 device: %s" % device_id)
        self.device_id = device_id
        self.modbus_driver = modbus_driver

        self.device_name = config["name"]
        self.outdoor_temp_topic = config["outdoor_temp_topic"]

        self.use_ghost_thermostat = config["use_ghost_thermostat"]
        self.temp_high = 0
        self.temp_low = 0
        if self.use_ghost_thermostat:
            self.persistence_file = config["persistence_file"]
            self.load_persistence_file()

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

    def using_ghost_thermostat(self):
        return self.use_ghost_thermostat

    def load_persistence_file(self):
        self.logger.info("Loading persistance file")
        with open(self.persistence_file) as pf:
            line1 = pf.readline()
            line2 = pf.readline()
            temp_high = float(line1)
            self.logger.info("Loaded high temp: %s" % temp_high)
            temp_low = float(line2)
            self.logger.info("Loaded low temp: %s" % temp_low)
            self.temp_high = temp_high
            self.temp_low = temp_low

    def save_persistence_file(self):
        with open(self.persistence_file, 'w') as pf:
            pf.write("%s\n" % self.temp_high)
            pf.write("%s\n" % self.temp_low)

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
        return ["curtemp", "setpoint", "isheating", "is_on", "temp_low", "temp_high"]

    def get_value(self, key):
        if key == "curtemp":
            # Current Temp - addr 31003 - cmd 0x04
            self.logger.debug("Reading current temperature")
            temperature = self.rdf302_read_temp(1002)
            self.logger.info("Current temperature: %s C" % temperature)
            return temperature
        elif key == "setpoint":
            # Current set point - addr 31004 - cmd 0x04
            self.logger.debug("Reading setpoint")
            temperature = self.rdf302_read_temp(1003)
            self.logger.info("Current setpoint: %s C" % temperature)
            return temperature
        elif key == "temp_high":
            return self.temp_high
        elif key == "temp_low":
            return self.temp_low
        elif key == "isheating":
            # Heating output - addr 31005 - cmd 0x04
            self.logger.debug("Reading is heating")
            is_heating = self.rdf302_read_bool(1004)
            self.logger.info("Is heating: %s" % is_heating)
            if is_heating:
                return 1
            else:
                return 0
        elif key == "is_on":
            # We consider ON if the setpoint is above the OFF temperature. Don't use protection mode.
            # is_on = self.rdf302_read_int(1000)
            self.logger.debug("Reading current temperature to determine ON state")
            setpoint = float(self.rdf302_read_temp(1003))
            is_on = setpoint >= self.off_temperature
            self.logger.info("Is on: %s" % is_on)
            return is_on

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
        elif key == "temp_high" and self.use_ghost_thermostat:
            temp_high = float(value)
            self.temp_high = temp_high
            self.save_persistence_file()
        elif key == "temp_low" and self.use_ghost_thermostat:
            temp_low = float(value)
            self.temp_low = temp_low
            self.save_persistence_file()
        elif key == "is_on":
            if value:
                # self.rdf302_write_int(100, 1)
                self.set_value("setpoint", self.temp_high)
            else:
                # self.rdf302_write_int(100, 4)
                self.set_value("setpoint", self.temp_low)

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
