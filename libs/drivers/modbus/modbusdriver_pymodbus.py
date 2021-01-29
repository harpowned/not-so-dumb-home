import logging
import struct
import threading
import time
import serial
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.exceptions import ModbusIOException


class ModbusDriver:
    def __init__(self):
        self.logger = logging.getLogger("not_so_dumb_home.modbusdriver_pymodbus")
        self.serialclient = ModbusClient(method='rtu', port='/dev/rs485', timeout=0.125, baudrate=9600,
                                         parity=serial.PARITY_EVEN)
        self.serialclient.connect()
        self.mutex = threading.Lock()

    def modbus_read_float(self, device, address):
        self.logger.debug("Acquiring mutex for query to %s" % address)
        self.mutex.acquire()
        time.sleep(0.05)
        result = None
        self.logger.debug("Acquired mutex for query to %s" % address)
        try:
            resp = self.serialclient.read_input_registers(address, 2, unit=device)
            if type(resp) != ModbusIOException:
                result = round(struct.unpack('>f', struct.pack('>HH', *resp.registers))[0], 1)
                self.logger.debug("Modbus call done for query to %s, result is %s" % (address, result))
            else:
                self.logger.error("Modbus IO Exception caught")
        except:
            self.logger.error("Exception caught")
        finally:
            self.mutex.release()
            self.logger.debug("Released mutex for query to %s" % address)
        return result

    def modbus_read_input(self, device, address):
        self.logger.debug("Acquiring mutex for query to %s" % address)
        self.mutex.acquire()
        result = None
        time.sleep(0.05)
        self.logger.debug("Acquired mutex for query to %s" % address)
        try:
            response = self.serialclient.read_input_registers(address, 1, unit=device)
            if type(response) != ModbusIOException:
                result = response.registers[0]
        except:
            self.logger.error("Exception caught")
        finally:
            self.mutex.release()
            self.logger.debug("Released mutex for query to %s" % address)
        return result

    def modbus_write_holding(self, device, address, value):
        self.logger.debug("Acquiring mutex for query to %s" % address)
        self.mutex.acquire()
        result = None
        time.sleep(0.05)
        self.logger.debug("Acquired mutex for query to %s" % address)
        try:
            result = self.serialclient.write_register(address, value, unit=device)
        except:
            self.logger.error("Exception caught")
        finally:
            self.mutex.release()
            self.logger.debug("Released mutex for query to %s" % address)
        self.logger.debug("Modbus call done for query to %s, result is %s" % (address, result))

        return result
