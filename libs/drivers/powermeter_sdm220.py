import logging

class Driver:
    sampling_period = 5  # seconds

    def __init__(self, device_id, config, modbus_driver):
        self.logger = logging.getLogger("not_so_dumb_home.powermeter_%s" % device_id)
        self.logger.debug("initializing SDM 220 device: %s" % device_id)
        self.device_id = device_id
        self.device_name = config["name"]
        address = config["modbus-address"]
        self.logger.debug("Setting SDM220 modbus addresdata_addresss %s" % address)
        self.address = int(address)
        self.maxpower = config["maxpower"]
        self.modbus_driver = modbus_driver

    def get_sampling_period(self):
        return self.sampling_period

    def get_id(self):
        return self.device_id

    def get_name(self):
        return self.device_name

    def get_type(self):
        return "powermeter"

    def get_gettable_vars(self):
        return ["volt", "current", "power", "appower", "repower", "pfactor", "phase", "freq", "acciae", "acceae",
                "accire", "accere", "totact", "totrea", "maxpower"]

    def get_value(self, key):
        if key == "maxpower":
            return self.maxpower
        elif key == "volt":
            # 30001 - Voltage - Spannung - Volts
            voltage = self.sdm220_request(0)
            self.logger.info("Voltage: %s V" % voltage)
            return voltage
        elif key == "current":
            # 30007 - Current - Ampere - Amps
            current = self.sdm220_request(6)
            self.logger.info("Current: %s A" % current)
            return current
        elif key == "power":
            # 30013 - Active Power - Wirkleistung - Watts
            power = self.sdm220_request(12)
            self.logger.info("Power: %s W" % power)
            return power
        elif key == "appower":
            # 30019 - Apparent power - Scheinleistung - VoltAmps
            aap = self.sdm220_request(18)
            self.logger.info("Active Apparent Power: %s VA" % aap)
            return aap
        elif key == "repower":
            # 30025 - Reactive power - Blindleistung - VAr
            rap = self.sdm220_request(24)
            self.logger.info("Reactive Apparent Power: %s VAr" % rap)
            return rap
        elif key == "pfactor":
            # 30031 - Power factor - Leistungsfaktor
            pfactor = self.sdm220_request(30)
            self.logger.info("Power Factor: %s" % pfactor)
            return pfactor
        elif key == "phase":
            # 30037 - Phase angle - Phasenverschiebungswinkel - Grad
            phaseangle = self.sdm220_request(36)
            self.logger.info("Phase angle: %s deg" % phaseangle)
            return phaseangle
        elif key == "freq":
            # 30071 - Frequency - Frequenz - Hz
            freq = self.sdm220_request(70)
            self.logger.info("Frequency: %s Hz" % freq)
            return freq
        elif key == "acciae":
            # 30073 - Import active energy - Import kumulierte Wirkleistung - kwh
            iae = self.sdm220_request(72)
            self.logger.info("Import Active Energy: %s kwh" % iae)
            return iae
        elif key == "acceae":
            # 30075 - Export active energy - Export kumulierte Wirkleistung - kwh
            eae = self.sdm220_request(74)
            self.logger.info("Export Active Energy: %s kwh" % eae)
            return eae
        elif key == "accire":
            # 30077 - Import reactive energy - Import kumulierte Blindleistung - kvarh
            ire = self.sdm220_request(76)
            self.logger.info("Import Reactive Energy: %s kvarh" % ire)
            return ire
        elif key == "accere":
            # 30079 - Export reactive energy - Export kumulierte Blindleistung - kvarh
            ere = self.sdm220_request(78)
            self.logger.info("Export Reactive Energy: %s kvarh" % ere)
            return ere
        elif key == "totact":
            # 30343 - Total active energy - Gesamute kumulierte Wirkleistung - kwh
            tae = self.sdm220_request(342)
            self.logger.info("Total Active Energy: %s kwh" % tae)
            return tae
        elif key == "totrea":
            # 30345 - Total reactive energy - Gesamte kumulierte Blindleistung - kvarh
            tre = self.sdm220_request(344)
            self.logger.info("Total Reactive Energy: %s kvarh" % tre)
            return tre

    def get_settable_vars(self):
        return []

    def sdm220_request(self, data_address):
        return self.modbus_driver.modbus_read_float(self.address, data_address)
