#!/usr/bin/env python
import logging
import subprocess

logger = logging.getLogger("smarthome.modbusdriver")

def pushData(hostname,item,value):

	logger.debug("Inserting data into Zabbix. Host: %s, item: %s, value: %s" % (hostname,item,value))

	subprocess.call("/usr/bin/zabbix_sender -v -z 192.168.10.11 -s %s -k %s -o %s" % (hostname,item,value),shell=True)
