import os
import sys
import time
import logging

from atomicapp.constants import LOG_FILE

path = LOG_FILE

# Do we want to write to /var/log/atomicapp.log ?
'''
if not (os.path.exists(path)):
    raise RuntimeError("%s does not exist" % path)
elif not (os.access(path, os.W_OK)):
    raise RuntimeError("%s is not writeable" % path)

# Setup log handling
handler = logging.FileHandler(path)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
'''


class Display:

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
        self.verbose_level = logging.getLogger("atomicapp").isEnabledFor(logging.DEBUG)
        self.logger = logging.getLogger("atomicapp")
        # self.logger.addHandler(handler)
        self.logger.propagate = False

    def display(self, msg, color='white', stderr=False):
        msg = self._colorize(self._make_unicode(msg), color)

        if stderr:
            print(msg)
            sys.stderr.flush()
        elif self.verbose:
            print(msg)
            sys.stdout.flush()

    def debug(self, msg, *args):
        self.logger.debug(msg)
        if self.verbose_level:
            self.display("[DEBUG] %6d %0.2f: %s" % (os.getpid(), time.time(), msg), 'purple')

    def verbose(self, msg, *args):
        self.logger.info(msg)
        if self.verbose_level:
            self.display("[VERBOSE]: %s" % msg, 'purple')

    def info(self, msg, *args):
        self.logger.info(msg)
        self.display(" %s" % msg, 'green')

    def warning(self, msg, *args):
        self.logger.warning(msg)
        self.display("[WARNING]: %s" % msg, 'yellow', stderr=True)

    def error(self, msg, *args):
        self.logger.error(msg)
        self.display("[ERROR]: %s" % msg, 'red', stderr=True)

    # Colors!
    def _colorize(self, text, color):
        return "\033[" + self.codeCodes[color] + "m" + text + "\033[0m"

    # Convert all those pesky log messages
    def _make_unicode(self, input):
        if type(input) != unicode:
            input = input.decode('utf-8')
            return input
        else:
            return input


def set_logging(level=logging.DEBUG):
    logger = logging.getLogger("atomicapp")
    logger.setLevel(level)
