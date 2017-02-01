#!/usr/bin/env python
import logging

logger = logging.getLogger("smarthome.nullLoggingServer")

def pushData(hostname,item,value):

	logger.debug("Inserting data into null logging server. Host: %s, item: %s, value: %s" % (hostname,item,value))
