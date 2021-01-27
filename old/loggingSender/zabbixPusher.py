#!/usr/bin/env python
import protobix
import logging

logger = logging.getLogger("smarthome.modbusdriver")

def pushData(hostname,item,value):
	''' create DataContainer, providing data_type, zabbix server and port '''
	zbx_container = protobix.DataContainer("items", "192.168.20.4", 10051)
	''' set debug '''
	zbx_container.set_debug(True)
	zbx_container.set_verbosity(True)

	logger.debug("Inserting data into Zabbix. Host: %s, item: %s, value: %s" % (hostname,item,value))
	''' Add items one after the other '''
	zbx_container.add_item( hostname, item, value)

	''' Send data to zabbix '''
	ret = zbx_container.send(zbx_container)
	''' If returns False, then we got a problem '''
	if not ret:
		logger.error("Something went wrong when sending data to Zabbix")
	
	logger.debug ("Data inserted to Zabbix")

#''' or use bulk insert '''
#data = {
#    "myhost1": {
#        "my.zabbix.item1": 0,
#        "my.zabbix.item2": "item string"
#    },
#    "myhost2": {
#        "my.zabbix.item1": 0,
#        "my.zabbix.item2": "item string"
#    }
#}
#zbx_container.add(data)

