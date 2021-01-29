#!/usr/bin/python3
import argparse
import configparser
import json
import logging
import sys
import datetime

from libs import mqtt_connection as mqtt
from libs import not_so_dumb_home_utils as utils
#from libs.logging_providers import dummy_logging_provider as logging_server_lib
from libs.logging_providers import zabbix_sender as logging_server_lib

APP_NAME = "loggingSender"
VERSION = "2.0"

def_config_paths = [
    "/etc/smarthome/loggingSender.cfg",
    "/usr/local/etc/smarthome/loggingSender.cfg",
    "./loggingSender.cfg",
]

devices = []
logging_server = ""
logger = ""
mqtt_conn = ""
topic_prefix = ""


class DeviceLogger:

    def __init__(self, device_id, config):
        self.deviceName = device_id
        self.nameInServer = config["nameInServer"]
        self.interval = float(config["interval"])
        self.variables = config["variables"].replace(" ", "").split(',')
        component_name = config["component_name"]
        device_topic = "%s/%s/%s/state" % (topic_prefix, component_name, device_id)
        logger.info("Subscribing to topic: \"%s\"" % device_topic)

        self.time_last_message = datetime.datetime(2000, 1, 1, 0, 0)  # Set a time in the past as initial value

        mqtt_conn.subscribe(device_topic, self.on_message)

    def on_message(self, client, userdata, message):
        if self.time_last_message + datetime.timedelta(seconds=self.interval) > datetime.datetime.now():
            logger.debug("Ignoring message received within interval")
        else:
            status_data = json.loads(message.payload)
            for variable in self.variables:
                logging_server.push_data(self.nameInServer, variable, status_data[variable])
            self.time_last_message = datetime.datetime.now()


def main(args):
    global devices
    global logger
    global mqtt_conn
    global topic_prefix
    global logging_server

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

    instance_name = config["loggingSender"]["instanceName"]
    topic_prefix = config["server-mqtt"]["topic_prefix"]

    utils.init_log(APP_NAME + "." + instance_name, config["loggingSender"]["logfile"], args.verbose)

    logger = logging.getLogger("not_so_dumb_home.loggingSender")

    logger.info("Starting SmartHome LoggingSender %s" % VERSION)

    enabled_devices = config["loggingSender"]["enabled_devices"].replace(" ", "").split(',')

    mqtt_conn = mqtt.MqttConnection(config["server-mqtt"], instance_name, None, None)

    logging_server = logging_server_lib.LoggingProvider(config["zabbix-server"])

    for device_id in enabled_devices:
        # Instantiate the device object
        device = DeviceLogger(device_id, config[device_id])
        # Add the object to the running drivers
        devices.append(device)

    mqtt_conn.loop_forever()


if __name__ == "__main__":
    main(sys.argv[1:])
