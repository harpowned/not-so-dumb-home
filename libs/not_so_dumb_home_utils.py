import logging
import os
import sys
import traceback
from logging.handlers import RotatingFileHandler


def die():
    # print(traceback.format_exc())
    logging.error(traceback.format_exc())
    logging.error("Error detected, application is Dying!")
    sys.exit(2)


class LogPathNotFoundException(object):
    pass


def init_log(app_name, path, verbose):
    if not path:
        print("Error: missing logpath. Check config file")
        raise LogPathNotFoundException

    global_logger = logging.getLogger()
    global_logger.setLevel(logging.DEBUG)

    # add a rotating handler
    file_handler = RotatingFileHandler(path, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    file_handler.setFormatter(file_formatter)
    global_logger.addHandler(file_handler)

    console = logging.StreamHandler()
    # set a format which is simpler for console use
    console_formatter = logging.Formatter('%(asctime)s %(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(console_formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    if verbose:
        global_logger.setLevel(logging.DEBUG)


class ConfigFileNotFoundException(object):
    pass


def get_config_file(config_file_param, def_config_paths):
    config_file = config_file_param
    # If we weren't given an explicit config file, try to find one on the defaults paths
    if not config_file:
        for config_candidate in def_config_paths:
            if os.path.exists(config_candidate):
                config_file = config_candidate
    # If we still don't have a config file, die
    if not config_file:
        print("Could not find a configuration file")
        sys.exit(2)
    if not os.path.exists(config_file):
        # Note: Logging has not been initialized at this stage, so just print to screen
        print("Error: Config file not found")
        raise ConfigFileNotFoundException

    return config_file
