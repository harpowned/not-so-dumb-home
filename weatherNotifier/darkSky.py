#!/usr/bin/env python
import logging
import urllib2
import traceback
import json

logger = logging.getLogger("smarthome.darkSkyLogger")

apikey = 0
latitude = 0
longitude = 0

currentTemp = 0
currentHum = 0
currentPress = 0
currentWindSpeed = 0
weatherIcon = ""
weatherText = ""

def setDarkSkyApiKey(arg):
	global apikey
	logger.debug("Setting Dark Sky api key to %s" % arg)
	apikey = arg
	

def setPosition(argLat, argLon):
	global latitude
	global longitude
	logger.debug("Setting position (lat,lon) to %s, %s" % (argLat, argLon))
	latitude = argLat
	longitude = argLon
	
def updateData():
	global apikey
	global latitude
	global longitude
	global currentTemp
	global currentHum
	global currentPress
	global currentWindSpeed
	global weatherIcon
	global weatherText
	try:
		url = "https://api.darksky.net/forecast/%s/%s,%s?units=si" % (apikey, latitude, longitude)
		response = urllib2.urlopen(url).read()
		logger.debug("DarkSky http get: %s" % response)
		data = json.loads(response)
		currentTemp = data["currently"]["temperature"]
		currentHum = data["currently"]["humidity"]
		currentPress = data["currently"]["pressure"]
		currentWindSpeed = data["currently"]["windSpeed"]
		weatherIcon = data["currently"]["icon"]
		weatherText = data["hourly"]["summary"]
		return True
	except:
		traceback.print_exc()
		return False

def getCurrentTemp():
	global currentTemp
	return currentTemp

def getCurrentHum():
	global currentHum
	return currentHum

def getCurrentPress():
	global currentPress
	return currentPress

def getCurrentWindSpeed():
	global currentWindSpeed
	return currentWindSpeed

def getWeatherIcon():
	global weatherIcon
	return weatherIcon

def getWeatherText():
	global weatherText
	return weatherText
