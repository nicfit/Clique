# -*- coding: utf-8 -*-
import logging
import logging.config

LOG_FORMAT = "[%(asctime)s] %(name)-25s [%(levelname)-8s]: %(message)s"

logging.VERBOSE = logging.DEBUG + 1
logging.addLevelName(logging.VERBOSE, "VERBOSE")
LEVELS = [logging.DEBUG, logging.VERBOSE, logging.INFO,
          logging.WARNING, logging.ERROR, logging.CRITICAL]
LEVEL_NAMES = [logging.getLevelName(l).lower() for l in LEVELS]


class Logger(logging.getLoggerClass()):
    '''Base class for all package loggers'''

    def __init__(self, name):
        super().__init__(name)

        # Using propogation of child to parent, by default
        self.propagate = True
        self.setLevel(logging.NOTSET)

    def verbose(self, msg, *args, **kwargs):
        '''Log \a msg at 'verbose' level, debug < verbose < info'''
        self.log(logging.VERBOSE, msg, *args, **kwargs)


def getLogger(name):
    OrigLoggerClass = logging.getLoggerClass()
    try:
        logging.setLoggerClass(Logger)
        return logging.getLogger(name)
    finally:
        logging.setLoggerClass(OrigLoggerClass)


log = getLogger("clique")
log.addHandler(logging.NullHandler())


def simpleConfig(level=logging.NOTSET):
    '''Configures the ``clique`` logger with a
    simple stdout logging handler set to ``level``.'''
    log = getLogger("clique")

    log.setLevel(level)

    formatter = logging.Formatter(LOG_FORMAT)
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    log.handlers.clear()
    log.addHandler(console)


DEFAULT_LOGGING_CONFIG = """
###
#logging configuration
#https://docs.python.org/3/library/logging.config.html#configuration-file-format
###

[loggers]
keys = root, clique

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_authchain]
level = NOTSET
qualname = clique
; When adding more specific handlers than what exists on the root you'll
; likely want to set propagate to false.
handlers =
propagate = 1

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = {default_format}

""".format(default_format=LOG_FORMAT)
