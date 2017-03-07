# -*- coding: utf-8 -*-
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
import logging

from atomicapp.constants import (GLOBAL_CONF,
                                 LOGGER_COCKPIT,
                                 NAME_KEY,
                                 DEFAULTNAME_KEY,
                                 PROVIDERS)
from atomicapp.utils import Utils
from atomicapp.plugin import Plugin
from atomicapp.nulecule.exceptions import NuleculeException

cockpit_logger = logging.getLogger(LOGGER_COCKPIT)


class NuleculeBase(object):

    """
    This is the base class for Nulecule and NuleculeComponent in
    atomicapp.nulecule.base.
    """

    def __init__(self, basepath, params, namespace):
        self.plugin = Plugin()
        self.basepath = basepath
        self.params = params or []
        self.namespace = namespace

    def load(self):
        pass

    def load_config(self, config, ask=False, skip_asking=False):
        """
        Load config data. Sets the loaded config data to self.config.

        Args:
            config (dict): Initial config data
            ask (bool): When True, ask for values for a param from user even
                        if the param has a default value
            skip_asking (bool): When True, skip asking for values for params
                                with missing values and set the value as
                                None

        Returns:
            None
        """
        self.config = config
        for param in self.params:
            value = config.get(param[NAME_KEY], scope=self.namespace, ignore_sources=['defaults'])
            if value is None:
                if ask or (not skip_asking and
                           param.get(DEFAULTNAME_KEY) is None):
                    cockpit_logger.info(
                        "%s is missing in answers.conf." % param[NAME_KEY])
                    value = config.get(param[NAME_KEY], scope=self.namespace) \
                        or Utils.askFor(param[NAME_KEY], param, self.namespace)
                else:
                    value = param.get(DEFAULTNAME_KEY)
                config.set(param[NAME_KEY], value, source='runtime',
                           scope=self.namespace)

    def get_provider(self, provider_key=None, dry=False):
        """
        Get provider key and provider instance.

        Args:
            provider_key (str or None): Name of provider
            dry (bool): Do not make change to the host system while True

        Returns:
            tuple: (provider key, provider instance)
        """
        # If provider_key isn't provided via CLI, let's grab it the configuration
        if provider_key is None:
            provider_key = self.config.get('provider', scope=GLOBAL_CONF)
        provider_class = self.plugin.getProvider(provider_key)
        if provider_class is None:
            raise NuleculeException("Invalid Provider - '{}', provided in "
                                    "answers.conf (choose from {})"
                                    .format(provider_key, ', '
                                                          .join(PROVIDERS)))
        return provider_key, provider_class(
            self.config.context(), self.basepath, dry)

    def run(self, provider_key=None, dry=False):
        raise NotImplementedError

    def stop(self, provider):
        raise NotImplementedError

    def fetch(self):
        raise NotImplementedError

    def uninstall(self):
        raise NotImplementedError
