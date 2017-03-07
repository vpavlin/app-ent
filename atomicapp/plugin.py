"""
 Copyright 2014-2016 Red Hat, Inc.

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

# Based on https://github.com/DBuildService/dock/blob/master/dock/plugin.py

from __future__ import print_function
import os

import logging
import importlib
from utils import Utils
from constants import (HOST_DIR,
                       LOGGER_DEFAULT,
                       PROVIDER_CONFIG_KEY)

logger = logging.getLogger(LOGGER_DEFAULT)


class Provider(object):
    key = None

    config = None
    path = None
    dryrun = None
    container = False
    config_file = None

    # By default, no artifacts are loaded
    __artifacts = []

    @property
    def artifacts(self):
        return self.__artifacts

    @artifacts.setter
    def artifacts(self, artifacts):
        self.__artifacts = artifacts

    def __init__(self, config, path, dryrun):
        self.config = config
        self.path = path
        self.dryrun = dryrun
        if Utils.getRoot() == HOST_DIR:
            self.container = True

        self.config_file = None
        self.getConfigFile()

    def init(self):
        raise NotImplementedError()

    def deploy(self):
        raise NotImplementedError()

    def getConfigFile(self):
        """
        Looks up provider configuration file (aka ~/.kube/config) in config passed
        to provider.
        """
        if PROVIDER_CONFIG_KEY in self.config:
            self.config_file = self.config[PROVIDER_CONFIG_KEY]
            if os.path.isabs(self.config_file):
                self.config_file = Utils.get_real_abspath(self.config_file)
        else:
            logger.debug("Configuration option '%s' not provided" % PROVIDER_CONFIG_KEY)

    def checkConfigFile(self):
        if not self.config_file:
            raise ProviderFailedException(
                "No provider config file specified!")
        elif not os.access(self.config_file, os.R_OK):
            raise ProviderFailedException(
                "Cannot access configuration file %s. Try adding "
                "'%s = /path/to/your/config_file' in the "
                "[general] section of the answers.conf file."
                % (self.config_file, PROVIDER_CONFIG_KEY))

    def undeploy(self):
        logger.warning(
            "Call to undeploy for provider %s failed - this action is not implemented",
            self.key)

    def loadArtifact(self, path):
        with open(path, "r") as fp:
            data = fp.read()

        return data

    def saveArtifact(self, path, data):
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "w") as fp:
            logger.debug("Writing artifact to %s" % path)
            fp.write(data)

    def __str__(self):
        return "%s" % self.key

    def __repr__(self):
        return "Plugin(key='%s')" % self.key


class ProviderFailedException(Exception):
    """Error during provider execution"""
    pass


class Plugin(object):
    plugins = []

    def __init__(self, ):
        pass

    def getProvider(self, provider_key):
        try:
            module = importlib.import_module("atomicapp.providers.%s" % provider_key)
            provider_class = "%sProvider" % provider_key.capitalize()
            provider = getattr(module, provider_class)
        except ImportError:
            provider = None
        return provider
