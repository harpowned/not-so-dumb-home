# openheat
Automatic scheduler and remote control for home heating

# Description and features
Openheat is the core of a small home automation project, with the following features:
 - Automatic control of a thermostat
	- Monitoring of ambient temperature (readings are stored into a Zabbix server)
	- Periodic change of temperature (every monday at 5, set temperature to 21 degrees)
	- Exceptions (On the 15th of January, from 7 to 13, ignore normal programming and set 18 degrees instead)
 - Reading of a power meter
	- Periodic reading of the power meter and storing data into a Zabbix server

# Why yet another programmer?
I have underfloor heating in my new home. Yay!
Underfloor heating has many advantadges, but quick heating is not one of them. It takes a long time to bring the temprature up or down. By the time you're feeling a bit chilly, you're already very late. It will take somewhere between 90 minutes and 2 hours to reach the confort temperature. By the time you're a bit too warm, you're late, too. The solution of course, is to have a programmer set configurations for you, so that these changes are done automatically.

So, my requirements:
 - The actual decision to turn the heater on and off should be done by a real thermostat. We don't want a software failure to cause infinite heating, which can get really expensive really fast.
 - We want to have a nice way to know what's been happening. What's the temperature been, how much time has the heater been on?
 - I prefer wired communications to wireless ones for this purpose. This device is going to spend its whole life (at least a decade, I hope!) hanging on the same wall, so there's no real benefit to wireless communications. Using wireless however, causes security and maintenance headaches. Besides, you need to feed power to it, so you will be running wires to it anyway.
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

Power Meter: Eastron SDM220
  - It's a din-rail mounted power meter with RS485 communications
  - Uses Modbus RTU, and the manual has the full documentation on how to remotely operate it
  - It was fairly easy to put it into the mains power box

# Status
Openheat is (currently) a small project I've been using at home for some time. I'm confident it does what it's expected in my scenario, but it's currently not deployable for anyone without some programming expertise.

# Software architecture
Openheat has 2 parts, the heatingScheduler and the deviceInterface.
The deviceInterface is meant to run on a small, embedded device (probably with a read-only filesystem) and must be connected to the RS485 bus (and to a network connecting to the heatingScheduler).
  - The deviceInterface's job is to manage the communication with the modbus devices.
  - It periodically takes a sample of the data from the devices, and sends data to the datastore (Zabbix)
  - It listens for commands from clients

The heatingScheduler is meant to run on the "main server", where you'll be doing the programming, probably together with other programs and/or frontends for this.
  - The heatingScheduler is the one who implements the logic of when to change the temperature
  - It reads the rules from a database (currently mysql)
  - It sends commands to the client to change the setpoint according to the programming

Master and deviceInterface can be run on the same device, if that's what fits your setup. I have the deviceInterface on a separate device, and the heatingScheduler, mysql and zabbix servers all on the same machine.

# Next steps
 - Lots of configuration parameters are hard-coded. This is okay for my own unchanging installation, but config files must be used in order for this to be useful for anyone else.
 - Communications between components are now an ugly command over a tcp port. Make them communicate over mqtt, with ssl and authentication, and choose a nicer (json?) communication method. Maybe something "standard"?
 - Right now, configuring means using phpmyadmin to add orders to the device. Since the tables describe exactly what I want to do, it's not really hard, but a better interface would be nice
 - Instant, remote changes are done right now using ssh and sending commands to the deviceInterface. I certanly need to add a frontend to that

# Other thoughts
 - For power consumption and heater control, this software mostly covers my needs, but it would be nice to have it integrated into something more scalable, which I can easily extend to further add sensors and actuators.
