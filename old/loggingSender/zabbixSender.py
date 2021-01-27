#!/usr/bin/env python
import logging
import subprocess

logger = logging.getLogger("smarthome.zabbixSender")

configInit = False

def setConfig(server_host_par, server_port_par):
	global configInit
	global server_host
	global server_port
	server_host = server_host_par
	server_port = server_port_par
	configInit = True

def pushData(hostname,item,value):
	if not configInit:
		logger.error("Zabbix config not initialized")
		return

	logger.debug("Inserting data into Zabbix. Host: %s, item: %s, value: %s" % (hostname,item,value))

	logger.debug("/usr/bin/zabbix_sender -v -z %s -p %s -s %s -k %s -o %s" % (server_host,server_port,hostname,item,value))
	subprocess.call("/usr/bin/zabbix_sender -v -z %s -p %s -s %s -k %s -o %s" % (server_host,server_port,hostname,item,value),shell=True)
