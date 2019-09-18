# -*- coding: utf-8 -*-
"""
   kingdomlib.log
   ~~~~~~~~~~~~~~
"""

from enum import Enum
from termcolor import colored


class LogLevel(Enum):
    DEBUG = 'DEBUG'
    WARN = 'WARN'
    INFO = 'INFO'
    ERROR = 'ERROR'


class Console(object):
    @staticmethod
    def log(message=None, level=None):
        message = message or ''

        if level == LogLevel.DEBUG:
            print(colored(f'[{LogLevel.DEBUG.name}]', 'magenta'), str(message))
        elif level == LogLevel.WARN:
            print(colored(f'[{LogLevel.WARN.name}]', 'yellow'), str(message))
        elif level == LogLevel.INFO:
            print(colored(f'[{LogLevel.INFO.name}]', 'blue'), str(message))
        elif level == LogLevel.ERROR:
            print(colored(f'[{LogLevel.ERROR.name}] ' + str(message), 'red'))
        else:
            print(colored('[{}]'.format(type), 'cyan'), str(message))

    @staticmethod
    def debug(message=None):
        Console.log(message, LogLevel.DEBUG)

    @staticmethod
    def warn(message=None):
        Console.log(message, LogLevel.WARN)

    @staticmethod
    def info(message=None):
        Console.log(message, LogLevel.INFO)

    @staticmethod
    def error(message=None):
        Console.log(message, LogLevel.ERROR)

    @staticmethod
    def echo(message=None):
        Console.log(message)


console = Console
