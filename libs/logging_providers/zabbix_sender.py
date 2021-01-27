import logging
import subprocess

logger = logging.getLogger("smarthome.zabbixSender")


class LoggingProvider:

    def __init__(self, config):
        self.logger = logging.getLogger("not_so_dumb_home.logging_provider_dummy")
        self.host = config["host"]
        self.port = config["port"]

    def push_data(self, hostname, item, value):
        self.logger.debug("Inserting data into Zabbix. Host: %s, item: %s, value: %s" % (hostname, item, value))

        self.logger.debug(
            "/usr/bin/zabbix_sender -v -z %s -p %s -s %s -k %s -o %s" % (self.host, self.port, hostname, item, value))
        subprocess.call(
            "/usr/bin/zabbix_sender -v -z %s -p %s -s %s -k %s -o %s" % (self.host, self.port, hostname, item, value),
            shell=True)
