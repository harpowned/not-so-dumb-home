# Not-so-dumb-home
Because I wouldn't go as far as to call it smart..

# Description and features
 Not-so-dumb-home is the core of a small home automation project, with the following features:
 - Automatic control of a thermostat
	- Monitoring of ambient temperature (readings are stored into a Zabbix server)
	- Periodic change of temperature (every monday at 5, set temperature to 21 degrees)
	- Exceptions (On the 15th of January, from 7 to 13, ignore normal programming and set 18 degrees instead)
 - Reading of a power meter
	- Periodic reading of the power meter and storing data into a Zabbix server
- Integration with Home Assistant

# Why yet another programmer?
I have underfloor heating in my new home. Yay!
Underfloor heating has many advantadges, but quick heating is not one of them. It takes a long time to bring the temprature up or down. By the time you're feeling a bit chilly, you're already very late. It will take somewhere between 90 minutes and 2 hours to reach the confort temperature. By the time you're a bit too warm, you're late, too. The solution of course, is to have a programmer set configurations for you, so that these changes are done automatically.

So, my requirements:
 - The actual decision to turn the heater on and off should be done by a real thermostat. We don't want a software failure to cause infinite heating, which can get really expensive really fast.
 - We want to have a nice way to know what's been happening. What's the temperature been, how much time has the heater been on?
 - I prefer wired communications to wireless ones for this purpose. This device is going to spend its whole life (at least a decade, I hope!) hanging on the same wall, and I'm going to have to run power to it anyway, so to me, there's no real benefit to wireless communications. Using wireless however, causes security and maintenance headaches. Besides, you need to feed power to it, so you will be running wires to it anyway.
 - Remote control would be nice to have
 - Also, I would like my system to be self-contained, so anything using a remote service is a no-go. Especially if the server is provided "for free" with the purchase of the hardware, as the provider could cease to operate or otherwise break compatiblity and render my existing hardware obsolete. I also discard this option because of privacy concerns.

When I looked at existing solutions, I found the following:
 - Dumb programmers, large devices to be put on the wall, with lots of buttons and no remote functionality
 - Integrated proprietary solutions (for example, honeywell thermostats), which require their own control unit and are not interoperable
 - Cloud-based services, with their fancy wi-fi devices and their proprietary stack (like Nest)
 - Some devices meant for hotels or large office buildings with industrial central control units

# My hardware
Thermostat: Siemens RDF302
  - It's a wall-mounted thermostat with RS485 communications
  - Uses Modbus RTU, and the manual has the full documentation on how to remotely operate it
  - It's very simple to use, looks nice and seems well-built (hope it will last!)
  - It also shows the exterior temperature, if you can feed it from somewhere else

Power Meter: Eastron SDM220/SDM230
  - It's a din-rail mounted power meter with RS485 communications
  - Uses Modbus RTU, and the manual has the full documentation on how to remotely operate it
  - It was fairly easy to put it into the mains power box

# Software architecture
The different components mostly communicate via an MQTT broker.

NSDH has the following parts:
DeviceInterface:
  - The deviceInterface's job is to manage the communication with the final devices.
  - It's meant to run on a small, embedded device (probably with a read-only filesystem) and must be connected to the sensors you want to control.
  - It's the device that is connected to the sensor or sensors, maybe via some non-ethernet network (like RS485)
  - It listens for commands from clients
  - It periodically sends data to the MQTT topics, so other programs (like Home Assistant) can update their state
  - There could be more than one instance (on different locations, or connected to different devices)

LoggingSender:
  - The LoggingSender's job is to send data to a server, for logging and archival
  - I'm using Zabbix for this, which provides some nice charts, and allows setting alerts if things go out of hand
  - It subscribes to the MQTT topics where the DeviceInterfaces post their status

WeatherNotifier:
  - This is a simple program which queries an internet service for weather data, an posts it on an MQTT channel
  - It's meant to provide support to a thermostat which has an outdoor temperature display