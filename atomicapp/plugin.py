# Based on https://github.com/DBuildService/dock/blob/master/dock/plugin.py

from __future__ import print_function
import os

import imp

import logging

logger = logging.getLogger(__name__)

class Provider(object):
    key = None

    config = None
    path = None
    dryrun = None
    container = False
    __artifacts = None

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
        if os.path.exists("/host"):
            self.container = True

    def init(self):
        raise NotImplementedError()

    def deploy(self):
        raise NotImplementedError()

    def undeploy(self):
        logger.warning("Call to undeploy for provider %s failed - this action is not implemented", self.key)
    
    def loadArtifact(self, path):
        with open(path, "r") as fp:
            data = fp.read()

        return data

    def saveArtifact(self, path, data):
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "w") as fp:
            logger.debug("Writing artifact to %s", path)
            fp.write(data)

    def __str__(self):
        return "%s" % self.key

    def __repr__(self):
        return "Plugin(key='%s')" % self.key

class ProviderFailedException(Exception):
    """Error during provider execution"""


class Plugin(object):
    plugins = []
    def __init__(self, ):
        pass

    def load_plugins(self):
        run_path = os.path.dirname(os.path.realpath(__file__))
        providers_dir = os.path.join(run_path, "providers")
        logger.debug("Loading providers from %s", providers_dir)

        plugin_classes = {}
        plugin_class = globals()["Provider"]

        for f in os.listdir(providers_dir):
            if f.endswith(".py"):
                module_name = os.path.basename(f).rsplit('.', 1)[0]
                try:
                    f_module = imp.load_source(module_name, os.path.join(providers_dir, f))
                except (IOError, OSError, ImportError) as ex:
                    logger.warning("can't load module '%s': %s", f, repr(ex))
                    continue

                for name in dir(f_module):
                    binding = getattr(f_module, name, None)
                    try:
                        # if you try to compare binding and PostBuildPlugin, python won't match them if you call
                        # this script directly b/c:
                        # ! <class 'plugins.plugin_rpmqa.PostBuildRPMqaPlugin'> <= <class '__main__.PostBuildPlugin'>
                        # but
                        # <class 'plugins.plugin_rpmqa.PostBuildRPMqaPlugin'> <= <class 'dock.plugin.PostBuildPlugin'>
                        is_sub = issubclass(binding, plugin_class)
                    except TypeError:
                        is_sub = False
                    if binding and is_sub and plugin_class.__name__ != binding.__name__:
                        plugin_classes[binding.key] = binding

        self.plugins = plugin_classes

    def getProvider(self, provider_key):
        for key, provider in self.plugins.iteritems():
            if key == provider_key:
                logger.debug("Found provider %s", provider)
                return provider
