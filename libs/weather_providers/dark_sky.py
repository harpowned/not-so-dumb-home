#!/usr/bin/env python
import logging
import urllib.request
import traceback
import json


class WeatherProvider:
    logger = logging.getLogger("smarthome.darkSkyLogger")

    apikey = 0
    latitude = 0
    longitude = 0

    current_temp = 0
    current_hum = 0
    current_press = 0
    current_wind_speed = 0
    weather_icon = ""
    weather_text = ""

    def __init__(self, config):
        self.logger = logging.getLogger("not_so_dumb_home.weather_provider_darksky")
        apikey = config["apikey"]
        self.logger.debug("Setting Dark Sky api key to %s" % apikey)
        self.apikey = apikey

    def set_position(self, lat, lon):
        self.logger.debug("Setting position (lat,lon) to %s, %s" % (lat, lon))
        self.latitude = lat
        self.longitude = lon

    def update_data(self):
        try:
            url = "https://api.darksky.net/forecast/%s/%s,%s?units=si" % (self.apikey, self.latitude, self.longitude)
            response = urllib.request.urlopen(url).read()
            self.logger.debug("DarkSky http get: %s" % response)
            data = json.loads(response)
            self.current_temp = data["currently"]["temperature"]
            self.current_hum = data["currently"]["humidity"]
            self.current_press = data["currently"]["pressure"]
            self.current_wind_speed = data["currently"]["windSpeed"]
            self.weather_icon = data["currently"]["icon"]
            self.weather_text = data["hourly"]["summary"]
            return True
        except:
            traceback.print_exc()
            return False

    def get_current_temp(self):
        return self.current_temp

    def get_current_hum(self):
        return self.current_hum

    def get_current_press(self):
        return self.current_press

    def get_current_wind_speed(self):
        return self.current_wind_speed

    def get_weather_icon(self):
        return self.weather_icon

    def get_weather_text(self):
        return self.weather_text
