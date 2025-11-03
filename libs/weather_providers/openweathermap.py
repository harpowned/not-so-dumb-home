import json
import logging
import traceback
import urllib.request


class WeatherProvider:
    logger = logging.getLogger("smarthome.openWeatherMapLogger")

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
        self.logger = logging.getLogger("not_so_dumb_home.weather_provider_openweathermap")
        apikey = config["apikey"]
        self.logger.debug("Setting OpenWeatherMap api key to %s" % apikey)
        self.apikey = apikey

    def set_position(self, lat, lon):
        self.logger.debug("Setting position (lat,lon) to %s, %s" % (lat, lon))
        self.latitude = lat
        self.longitude = lon

    def update_data(self):
        try:
            url = "https://api.openweathermap.org/data/2.5/weather?lat=%s&lon=%s&appid=%s&units=metric&lang=ca" % (self.latitude, self.longitude, self.apikey)
            self.logger.debug("Calling URL: %s" % url)
            response = urllib.request.urlopen(url).read()
            self.logger.debug("OpenWeatherMap http get: %s" % response)
            data = json.loads(response)
            self.current_temp = data["main"]["temp"]
            self.current_hum = data["main"]["humidity"]
            self.current_press = data["main"]["pressure"]
            self.current_wind_speed = data["wind"]["speed"]
            self.weather_icon = data["weather"][0]["main"]
            self.weather_text = data["weather"][0]["description"]
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
