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
import logging.handlers
from atomicapp.constants import LOG_NAME, LOG_LEVELS, LOG_CUSTOM_NAME


class Display:

    '''

    In order to effectively use logging within Python, we manipulate the level
    codes by adding our own custom ones. By doing so, we are able to have different
    log legs effectively span all Python files.

    Upon initialization, Atomic App checks to see if --logging-ouput= is set during
    initalization and set's the appropriate log level based on either the default
    or custom level value.

    Default python level codes

    NOTSET    0
    DEBUG    10
    INFO     20
    WARNING  30
    ERROR    40
    CRITICAL 50

    Custom log levels in constants.py

    LOG_LEVELS = {
        "default": 90,
        "cockpit": 91,
        "stdout": 92,
        "none": 93
    }

    '''

    # Console colour codes
    codeCodes = {
        'black': '0;30', 'bright gray': '0;37',
        'blue': '0;34', 'white': '1;37',
        'green': '0;32', 'bright blue': '1;34',
        'cyan': '0;36', 'bright green': '1;32',
        'red': '0;31', 'bright cyan': '1;36',
        'purple': '0;35', 'bright red': '1;31',
        'yellow': '0;33', 'bright purple': '1;35',
        'dark gray': '1;30', 'bright yellow': '1;33',
        'normal': '0'
    }

    def __init__(self):
        """
        Upon initialization of the Display class we grab the log level from
        logger as well as the standard verbose level (ex. if -v was passed or not)
        """
        self.logger = logging.getLogger(LOG_NAME)
        self.verbose_level = self.logger.getEffectiveLevel()
        self.log_level = logging.getLogger(LOG_CUSTOM_NAME).getEffectiveLevel()

    def debug(self, msg, only=None):
        self._display(msg, LOG_LEVELS["debug"], 'cyan', only)

    def verbose(self, msg, only=None):
        self._display(msg, LOG_LEVELS["debug"], 'cyan', only)

    def info(self, msg, only=None):
        self._display(msg, LOG_LEVELS["info"], 'white', only)

    def warning(self, msg, only=None):
        self._display(msg, LOG_LEVELS["warning"], 'yellow', only)

    def error(self, msg, only=None):
        self._display(msg, LOG_LEVELS["error"], 'red', only)

    def _display(self, msg, code, color, only):
        """
        Display checks to see what log_level is being matched to and passes it
        along to the correct logging provider. If an unknown error occurs
        retrieving the log level, we error out.
        """
        if self.log_level == LOG_LEVELS['stdout']:
            self._stdout(msg, code)
        elif self.log_level == LOG_LEVELS['cockpit']:
            self._cockpit(msg, code, only)
        elif self.log_level == LOG_LEVELS['none']:
            return
        else:
            self._stdout_via_logger(msg, code, color)

    def _stdout(self, msg, code):
        """
        Colorless logging output using the standard [DEBUG], [WARNING], etc tags.
        """
        if self.verbose_level is not LOG_LEVELS['debug'] and code is LOG_LEVELS['debug']:
            return

        if code == LOG_LEVELS['debug']:
            msg = "[DEBUG] %s" % msg
        elif code == LOG_LEVELS['warning']:
            msg = "[WARNING] %s" % msg
        elif code == LOG_LEVELS['error']:
            msg = "[ERROR] %s" % msg
        else:
            msg = "[INFO] %s" % msg

        self._sysflush()
        print(self._make_unicode(msg))

    def _stdout_via_logger(self, msg, code, color):
        """
        Colorful logging with the logger library.
        """
        if self.verbose_level is not LOG_LEVELS['debug'] and code is LOG_LEVELS['debug']:
            return

        if code == LOG_LEVELS['debug']:
            self.logger.info(msg)
            msg = "[DEBUG] %s" % msg
        elif code == LOG_LEVELS['warning']:
            self.logger.warning(msg)
            msg = "[WARNING] %s" % msg
        elif code == LOG_LEVELS['error']:
            self.logger.error(msg)
            msg = "[ERROR] %s" % msg
        else:
            self.logger.info(msg)
            msg = "[INFO] %s" % msg

        self._sysflush()
        print(self._colorize(self._make_unicode(msg), color))

    def _cockpit(self, msg, code, only):
        """
        Due to cockpit logging requirements, we will ONLY output logging that is designed as
        display.info("foo bar", "cockpit")
        """
        if only is not "cockpit":
            return

        if self.verbose_level is not LOG_LEVELS['debug'] and code is LOG_LEVELS['debug']:
            return

        if code == LOG_LEVELS['debug']:
            msg = "atomicapp.status.debug.message=%s" % msg
        elif code == LOG_LEVELS['warning']:
            msg = "atomicapp.status.warning.message=%s" % msg
        elif code == LOG_LEVELS['error']:
            msg = "atomicapp.status.error.message=%s" % msg
        else:
            msg = "atomicapp.status.info.message=%s" % msg

        self._sysflush()
        print(self._make_unicode(msg))

    def _sysflush(self):
        """
        Before each output, we check to see that we correctly flush out stderr
        or stdout
        """
        if self.verbose_level is LOG_LEVELS['error'] or self.verbose_level is LOG_LEVELS['warning']:
            sys.stderr.flush()
        else:
            sys.stdout.flush()

    def _colorize(self, text, color):
        """
        Colorize based upon the color codes indicated.
        """
        return "\033[" + self.codeCodes[color] + "m" + text + "\033[0m"

    def _make_unicode(self, input):
        """
        Convert all input to utf-8 for multi language support
        """
        if type(input) != unicode:
            input = input.decode('utf-8')
            return input
        else:
            return input


def set_logging(verbose=None, quiet=None, logging_output=None):
    """
    This function loops through all the available log levels and sets them
    appropriatedly based upon the logging input provided.
    """
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.WARNING
    else:
        level = logging.INFO

    # Let's check to see if any of our choices match the LOG_LEVELS constant! --logging-output
    if logging_output in LOG_LEVELS:
        custom_level = LOG_LEVELS[logging_output]
    else:
        custom_level = LOG_LEVELS['default']

    logging.getLogger(LOG_NAME).setLevel(level)
    logging.getLogger(LOG_CUSTOM_NAME).setLevel(custom_level)
