# -*- coding: utf-8 -*-
from atomicapp.constants import (GLOBAL_CONF, DEFAULT_PROVIDER,
                                 DEFAULT_ANSWERS)
from atomicapp.utils import Utils
from atomicapp.plugin import Plugin
import os
import urllib2

plugin = Plugin()
plugin.load_plugins()


class NuleculeBase(object):
    """
    This is the base class for Nulecule and NuleculeComponent in
    atomicapp.nulecule.base.
    """

    def __init__(self, basepath, params, namespace):
        self.basepath = basepath
        self.params = params or []
        self.namespace = namespace

    def load(self):
        pass

    def load_config(self, config=None, ask=False, skip_asking=False):
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
        config = config or DEFAULT_ANSWERS
        for param in self.params:
            value = config.get(self.namespace, {}).get(param['name']) or \
                config.get(GLOBAL_CONF, {}).get(param['name'])
            if value is None and (ask or (
                    not skip_asking and param.get('default') is None)):
                value = Utils.askFor(param['name'], param)
            elif value is None:
                value = param.get('default')
            if config.get(self.namespace) is None:
                config[self.namespace] = {}
            config[self.namespace][param['name']] = value
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
            if group == GLOBAL_CONF:
                if self.namespace == GLOBAL_CONF:
                    key = GLOBAL_CONF
                else:
                    key = self.namespace
                to_config[key] = to_config.get(key) or {}
                to_config[key].update(group_vars or {})
            else:
                for key, value in group_vars.items():
                    to_config[group][key] = value

    def get_context(self):
        """
        Get context data from config data for rendering an artifact.
        """
        context = {}
        context.update(self.config.get('general') or {})
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
        if provider_key is None:
            if self.running_on_openshift:
                provider_key = "openshift"
            else:
                provider_key = self.config.get('general', {}).get(
                    'provider', DEFAULT_PROVIDER)
        provider_class = plugin.getProvider(provider_key)
        return provider_key, provider_class(
            self.get_context(), self.basepath, dry)

    @property
    def running_on_openshift(self):
        """
        The KUBERNETES_SERVICE_HOST env var should only exist
        on an openshift or kubernetes environment.
        Here we check if the "kubernetes" host has an openshift
        API endpoint. If so, we're running from an openshift pod.
        """
        _kube_host = os.getenv("KUBERNETES_SERVICE_HOST")
        if _kube_host:
            url = "https://%s/oapi" % _kube_host
            cafile = "/run/secrets/kubernetes.io/serviceaccount/ca.crt"
            try:
                connection = urllib2.urlopen(url, cafile=cafile)
                return connection.getcode() is 200
            except Exception:
                return False
        return False

    def run(self, provider_key=None, dry=False):
        raise NotImplementedError

    def stop(self, provider):
        raise NotImplementedError

    def install(self):
        raise NotImplementedError

    def uninstall(self):
        raise NotImplementedError
