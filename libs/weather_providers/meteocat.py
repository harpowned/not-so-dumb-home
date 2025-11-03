import json
import logging
import traceback
import requests


class WeatherProvider:
    logger = logging.getLogger("smarthome.meteoCatLogger")

    apikey = 0
    station = ""

    current_temp = 0

    def __init__(self, config):
        self.logger = logging.getLogger("not_so_dumb_home.weather_provider_meteocat")
        apikey = config["apikey"]
        self.logger.debug("Setting Meteocat api key to %s" % apikey)
        self.apikey = apikey
        station = config["station"]
        self.logger.debug("Setting Meteocat station code to %s" % apikey)
        self.station = station

    def set_position(self, lat, lon):
        self.logger.debug("Meteocat weather provider does not use position, ignoring..")

    def update_data(self):
        try:
            url = "https://api.meteo.cat/xema/v1/variables/mesurades/32/ultimes?codiEstacio=%s" % self.station
            self.logger.debug("Calling URL: %s" % url)
            response = requests.get(url, headers={"Content-Type": "application/json", "X-Api-Key": self.apikey})
            if response.status_code != 200:
                self.logger.error("Meteocat API returned status code %s" % response.status_code)
                return False
            self.logger.debug("OpenWeatherMap http get: %s" % response.text)
            data = json.loads(response.text)
            self.current_temp = data["lectures"][0]["valor"]
            return True
        except:
            traceback.print_exc()
            return False

    def get_current_temp(self):
        return self.current_temp

    def get_current_hum(self):
        return -1

    def get_current_press(self):
        return -1

    def get_current_wind_speed(self):
        return -1

    def get_weather_icon(self):
        return "not supported"

    def get_weather_text(self):
        return "not supported"
