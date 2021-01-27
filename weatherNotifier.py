#!/usr/bin/python3
import time
import threading
import logging
import sys
import json
import configparser
import argparse
from libs import not_so_dumb_home_utils as utils
from libs import mqtt_connection as mqtt

APP_NAME = "weatherNotifier"
VERSION = "2.0"

def_config_paths = [
    "/etc/smarthome/weatherNotifier.cfg",
    "/usr/local/etc/smarthome/weatherNotifier.cfg",
    "./weatherNotifier.cfg",
]

notification_interval = 0
weather_provider = ""
logger = ""
mqtt_conn = ""
mqtt_topic_full_report = ""
mqtt_topic_temperature = ""


def weatherinfo_scheduler():
    global notification_interval
    global weather_provider
    global mqtt_conn
    global mqtt_topic_full_report
    global mqtt_topic_temperature

    while True:
        logger.debug("Weather reporting loop running")
        if weather_provider.update_data():
            # Send a full json weather report
            logger.debug("Updated weather info OK")
            if mqtt_topic_full_report:
                weatherinfo = {}
                weatherinfo["device"] = "weatherstation"
                weatherinfo["command"] = "report"
                weatherinfo["currentTemp"] = weather_provider.get_current_temp()
                weatherinfo["currentHum"] = weather_provider.get_current_hum()
                weatherinfo["currentPress"] = weather_provider.get_current_press()
                weatherinfo["currentWindSpeed"] = weather_provider.get_current_wind_speed()
                weatherinfo["weatherIcon"] = weather_provider.get_weather_icon()
                weatherinfo["weatherText"] = weather_provider.get_weather_text()
                jsonstr = json.dumps(weatherinfo)
                logger.info("Posting to mqtt: %s" % jsonstr)
                mqtt_conn.publish(mqtt_topic_full_report, jsonstr)

            # Send a report with only the temperature
            if mqtt_topic_temperature:
                temp = weather_provider.get_current_temp()
                logger.info("Posting to mqtt: %s" % temp)
                mqtt_conn.publish(mqtt_topic_temperature, temp)
        else:
            logger.warning("Could not update weather info")

        time.sleep(notification_interval)


def main(args):
    global logger
    global weather_provider
    global notification_interval
    global mqtt_conn
    global mqtt_topic_full_report
    global mqtt_topic_temperature

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

    instance_name = config["weatherNotifier"]["instanceName"]

    utils.init_log(APP_NAME + "." + instance_name, config["weatherNotifier"]["logfile"], args.verbose)

    logger = logging.getLogger("not_so_dumb_home.device_interface")

    logger.info("Starting SmartHome weatherNotifier %s" % VERSION)

    weather_type = config["weatherNotifier"]["weatherService"]
    if weather_type == "darksky":
        from libs.weather_providers import dark_sky as weather_provider_lib
        weather_provider = weather_provider_lib.WeatherProvider(config["darksky"])

    weather_conf = config["weatherNotifier"]
    weather_provider.set_position(weather_conf["latitude"], weather_conf["longitude"])

    mqtt_topic_full_report = config["server-mqtt"]["json_topic"]
    mqtt_topic_temperature = config["server-mqtt"]["temperature_topic"]

    notification_interval = float(weather_conf["interval"])

    mqtt_conn = mqtt.MqttConnection(config["server-mqtt"], instance_name, None, None)

    t = threading.Thread(target=weatherinfo_scheduler)
    t.daemon = True
    t.start()

    mqtt_conn.loop_forever()


if __name__ == "__main__":
    main(sys.argv[1:])
