#!/usr/bin/python
import logging
import socket
import sys
import mail_sender
import time

SERVER_IP="192.168.10.10"
SERVER_PORT=1545

CMD_SETTEMP="ts_settemp"
CMD_GETTEMP="ts_getsetpoint"

#logger = logging.getlogger("programmer")

def start():
	print "TCP sender initialized"

def send_command(command):
	# Create a TCP/IP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Connect the socket to the port where the server is listening
	server_address = (SERVER_IP, SERVER_PORT)
	print 'connecting to %s port %s' % server_address
	sock.connect(server_address)

	try:
		# Send data
		print "Debug: Now sending command %s" % command
		sock.sendall(command)

		data = sock.recv(16)
		print "Debug: Data returned is %s" % data
		return data

	finally:
		print >>sys.stderr, 'closing socket'
		sock.close()
	## TODO: Send setpoint command
	## Check that the setpoint has been changed
	## Retry 3 times if not
	## Send an email report?

def setTemp(temp):
	retries = 0
	success = False
	max_retries = 3
	while retries <= max_retries and not success:
		if retries > 0:
			time.sleep(10)
		print "Setting thermostat setpoint to %s" % temp
		send_command("%s %s" % (CMD_SETTEMP,temp))
		thermo_temp = send_command("%s" % CMD_GETTEMP)
		print "Temperature set to %s" % thermo_temp
		retries += 1
		if float(thermo_temp) == float(temp):
			print "Temperature set OK"
			success = True
	mail_sender.sendMail("Set temperature to %s (%s tries)" % (temp, retries))
