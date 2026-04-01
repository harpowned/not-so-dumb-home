import sdnotify
import logging

class Watchdog:
    def __init__(self):
        self.logger = logging.getLogger("not_so_dumb_home.watchdog")
        self.n = sdnotify.SystemdNotifier()
        self.n.notify("READY=1")
        self.logger.info("Watchdog started")
    def kick(self):
        self.logger.info("Kicking watchdog process")
        self.n.notify("WATCHDOG=1")