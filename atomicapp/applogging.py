"""
 Copyright 2015 Red Hat, Inc.

 This file is part of Atomic App.

 Atomic App is free software: you can redistribute it and/or modify
 it under the terms of the GNU Lesser General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Atomic App is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Lesser General Public License for more details.

 You should have received a copy of the GNU Lesser General Public License
 along with Atomic App. If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import logging

from atomicapp.constants import (LOGGER_COCKPIT,
                                 LOGGER_DEFAULT)


class colorizeOutputFormatter(logging.Formatter):
    """
    A class to colorize the log msgs based on log level
    """

    def format(self, record):
        # Call the parent class to do formatting.
        msg = super(colorizeOutputFormatter, self).format(record)

        # Now post process and colorize if needed
        if record.levelno == logging.DEBUG:
            msg = self._colorize(msg, 'cyan')
        elif record.levelno == logging.WARNING:
            msg = self._colorize(msg, 'yellow')
        elif record.levelno == logging.INFO:
            msg = self._colorize(msg, 'white')
        elif record.levelno == logging.ERROR:
            msg = self._colorize(msg, 'red')
        else:
            raise Exception("Invalid logging level {}".format(record.levelno))
        return self._make_unicode(msg)

    def _colorize(self, text, color):
        """
        Colorize based upon the color codes indicated.
        """
        # Console color codes
        colorCodes = {
            'white': '0', 'bright white': '1;37',
            'blue': '0;34', 'bright blue': '1;34',
            'green': '0;32', 'bright green': '1;32',
            'cyan': '0;36', 'bright cyan': '1;36',
            'red': '0;31', 'bright red': '1;31',
            'purple': '0;35', 'bright purple': '1;35',
            'yellow': '0;33', 'bright yellow': '1;33',
        }
        return "\033[" + colorCodes[color] + "m" + text + "\033[0m"

    def _make_unicode(self, input):
        """
        Convert all input to utf-8 for multi language support
        """
        if type(input) != unicode:
            input = input.decode('utf-8')
        return input


class AtomicappLoggingAdapter(logging.LoggerAdapter):
    """
    A class to pass contextual information to logs.
    """
    def process(self, msg, kwargs):
        return('{} : {}'.format(self.extra['atomicapp_extra'], msg), kwargs)


class Logging:
    @staticmethod
    def setup_logging(verbose=None, quiet=None, logtype=None):
        """
        This function sets up logging based on the logtype requested.
        The 'none' level outputs no logs at all
        The 'cockpit' level outputs just logs for the cockpit logger
        The 'nocolor' level prints out normal log msgs (no cockpit) without color
        The 'color' level prints out normal log msgs (no cockpit) with color
        """

        # If no logtype was set then let's have a sane default
        # If connected to a tty, then default to color, else, no color
        if not logtype:
            if sys.stdout.isatty():
                logtype = 'color'
            else:
                logtype = 'nocolor'

        # Determine what logging level we should use
        if verbose:
            logging_level = logging.DEBUG
        elif quiet:
            logging_level = logging.WARNING
        else:
            logging_level = logging.INFO

        # Get the loggers and clear out the handlers (allows this function
        # to be ran more than once)
        logger_raw = logging.getLogger(LOGGER_DEFAULT)
        logger_raw.handlers = []
        cockpit_logger = logging.getLogger(LOGGER_COCKPIT)
        cockpit_logger.handlers = []

        if logtype == 'none':
            # blank out both loggers
            logger_raw.addHandler(logging.NullHandler())
            cockpit_logger.addHandler(logging.NullHandler())
            return

        if logtype == 'cockpit':
            # blank out normal log messages
            logger_raw.addHandler(logging.NullHandler())

            # configure cockpit logger
            handler = logging.StreamHandler(stream=sys.stdout)
            formatter = logging.Formatter('atomicapp.status.%(levelname)s.message=%(message)s')
            handler.setFormatter(formatter)
            cockpit_logger.addHandler(handler)
            cockpit_logger.setLevel(logging_level)
            return

        if logtype == 'nocolor':
            # blank out cockpit log messages
            cockpit_logger.addHandler(logging.NullHandler())

            # configure logger for basic no color printing to stdout
            handler = logging.StreamHandler(stream=sys.stdout)
            formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
            handler.setFormatter(formatter)
            logger_raw.addHandler(handler)
            logger_raw.setLevel(logging_level)
            return

        if logtype == 'color':
            # blank out cockpit log messages
            cockpit_logger.addHandler(logging.NullHandler())

            # configure logger for color printing to stdout
            handler = logging.StreamHandler(stream=sys.stdout)
            formatter = colorizeOutputFormatter('%(asctime)s - [%(levelname)s] - %(message)s')
            handler.setFormatter(formatter)
            logger_raw.addHandler(handler)
            logger_raw.setLevel(logging_level)
            return

        # If we made it here then there is an error
        raise Exception("Invalid logging output type: {}".format(logtype))

    @staticmethod
    def global_logger(filename):
        """
        This function returns a logging instance which will output logging event information
        along with what the LoggerAdapter tells it to output
        :param filename: path of the file calling this function
        :return the function returns the logger instance which is being used by all the files
        """

        # creating a logging instance
        logger_raw = logging.getLogger(LOGGER_DEFAULT)
        # the logging adapter handles the filename received from the file importing this
        logger = AtomicappLoggingAdapter(logger_raw, {'atomicapp_extra': '/'.join(filename.split('/')[-2:])})
        return logger
