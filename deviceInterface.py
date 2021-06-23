#!/usr/bin/env python3
import argparse
import configparser
import importlib
import logging
import sys

from libs import mqtt_connection as mqtt
from libs import not_so_dumb_home_utils as utils
from libs.drivers.modbus import modbusdriver_pymodbus as modbus_driver_lib

APP_NAME = "deviceInterface"
VERSION = "2.1.0"

def_config_paths = [
    "/etc/smarthome/deviceInterface.cfg",
    "/usr/local/etc/smarthome/deviceInterface.cfg",
    "./deviceInterface.cfg",
]

devices = []
logger = ""
mqtt_conn = ""


# ----------------------------------------------------------------------

def register_mqtt_device(device):
    mqtt_adapter = mqtt_conn.new_adapter(device)


def on_connect():
    logger.debug("Parent on connect")
    for device in devices:
        logger.info("Registering device: %s" % device.get_id())
        register_mqtt_device(device)


def main(args):
    global devices
    global logger
    global mqtt_conn

    # Parse command line arguments
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-v", "--verbose", action="store_true",
                            help="increase output verbosity")
    arg_parser.add_argument("-c", "--config")
    args = arg_parser.parse_args()

    config_file = utils.get_config_file(args.config, def_config_paths)

    print("Reading config file from: %s" % config_file)
    config = configparser.ConfigParser()
    config.read(config_file)

    instance_name = config["deviceInterface"]["instanceName"]

    utils.init_log(APP_NAME + "." + instance_name, config["deviceInterface"]["logfile"], args.verbose)

    logger = logging.getLogger("not_so_dumb_home.device_interface")

    logger.info("Starting SmartHome DeviceInterface %s" % VERSION)

    modbus_port = config["modbus"]["port"]
    modbus_driver = None
    if modbus_port != "disabled":
        modbus_driver = modbus_driver_lib.ModbusDriver(modbus_port)

    enabled_devices = config["deviceInterface"]["enabled_devices"].replace(" ", "").split(',')
    device_drivers = dict()
    for device_id in enabled_devices:
        device_type = config[device_id]["type"]
        device_model = config[device_id]["model"]
        device_driver = device_type + "_" + device_model

        # Load the driver for this device
        if device_driver not in sys.modules:
            device_drivers[device_driver] = importlib.import_module("libs.drivers." + device_driver)

        # Instantiate the device object
        if device_drivers[device_driver].is_modbus():
             device = device_drivers[device_driver].Driver(device_id, config[device_id], modbus_driver)
        else:
            device = device_drivers[device_driver].Driver(device_id, config[device_id])
        # Add the object to the running drivers
        devices.append(device)

    mqtt_conn = mqtt.MqttConnection(config["server-mqtt"], instance_name, on_connect, None)
    mqtt_conn.loop_forever()


if __name__ == "__main__":
    main(sys.argv[1:])
