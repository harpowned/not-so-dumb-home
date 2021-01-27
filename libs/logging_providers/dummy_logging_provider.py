import logging


class LoggingProvider:

    def __init__(self, config):
        self.logger = logging.getLogger("not_so_dumb_home.logging_provider_dummy")

    def push_data(self, hostname, item, value):
        self.logger.debug("Inserting data into null logging server. Host: %s, item: %s, value: %s" % (hostname, item, value))
