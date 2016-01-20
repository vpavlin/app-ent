# -*- coding: utf-8 -*-
from atomicapp.constants import (GLOBAL_CONF,
                                 NAME_KEY,
                                 DEFAULTNAME_KEY,
                                 PROVIDER_KEY)
from atomicapp.utils import Utils
from atomicapp.plugin import Plugin


class NuleculeBase(object):

    """
    This is the base class for Nulecule and NuleculeComponent in
    atomicapp.nulecule.base.
    """

    def __init__(self, basepath, params, namespace):
        self.plugin = Plugin()
        self.plugin.load_plugins()
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
        for param in self.params:
            value = config.get(self.namespace, {}).get(param[NAME_KEY]) or \
                config.get(GLOBAL_CONF, {}).get(param[NAME_KEY])
            if value is None and (ask or (
                    not skip_asking and param.get(DEFAULTNAME_KEY) is None)):
                value = Utils.askFor(param[NAME_KEY], param)
            elif value is None:
                value = param.get(DEFAULTNAME_KEY)
            if config.get(self.namespace) is None:
                config[self.namespace] = {}
            config[self.namespace][param[NAME_KEY]] = value
        self.config = config

    def merge_config(self, to_config, from_config):
        """
        Merge values from from_config to to_config. If value for a key
        in a group in to_config is missing, then only set it's value from
        corresponding key in the same group in from_config.

        Args:
            to_config (dict): Dictionary to merge config into
            from_config (dict): Dictionary to merge config from

        Returns:
            None
        """
        for group, group_vars in from_config.items():
            to_config[group] = to_config.get(group) or {}
            for key, value in (group_vars or {}).items():
                if to_config[group].get(key) is None:
                    to_config[group][key] = value

    def get_context(self):
        """
        Get context data from config data for rendering an artifact.
        """
        context = {}
        context.update(self.config.get(GLOBAL_CONF) or {})
        context.update(self.config.get(self.namespace) or {})
        return context

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
            provider_key = self.config.get(GLOBAL_CONF)[PROVIDER_KEY]
        provider_class = self.plugin.getProvider(provider_key)
        return provider_key, provider_class(
            self.get_context(), self.basepath, dry)

    def run(self, provider_key=None, dry=False):
        raise NotImplementedError

    def stop(self, provider):
        raise NotImplementedError

    def fetch(self):
        raise NotImplementedError
    def uninstall(self):
        raise NotImplementedError
