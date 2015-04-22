#!/usr/bin/env python

from __future__ import print_function
import os,sys
from string import Template

from yapsy.PluginManager import PluginManager

import logging

from params import Params
from utils import Utils
from constants import GLOBAL_CONF, DEFAULT_PROVIDER, MAIN_FILE, PARAMS_FILE

logger = logging.getLogger(__name__)

def isTrue(val):
    logger.debug("Value: %s" % val)
    return True if str(val).lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'sure'] else False

class Run():
    debug = False
    dryrun = False
    params = None
    answers_data = {GLOBAL_CONF: {}}
    tmpdir = None
    answers_file = None
    provider = DEFAULT_PROVIDER
    installed = False
    plugins = None
    update = False
    app_path = None
    target_path = None
    app_id = None
    app = None

    def __init__(self, answers, APP, dryrun = False, debug = False, **kwargs):

        self.debug = debug
        self.dryrun = dryrun

        if os.path.exists(APP):
            self.app_path = APP
        else:
            logger.error("App path %s does not exist." % APP)


        self.params = Params(target_path=self.app_path)
        self.utils = Utils(self.params)

        self.answers_file = answers

        run_path = os.path.dirname(os.path.realpath(__file__))
        self.plugins = PluginManager()
        self.plugins.setPluginPlaces([os.path.join(run_path, "providers")])
        self.plugins.collectPlugins()

    def _dispatchGraph(self):
        if not "graph" in self.params.mainfile_data:
            raise Exception("Graph not specified in %s" % MAIN_FILE)
        if not os.path.isdir(self.utils.getGraphDir()):
            raise Exception("Couldn't find %s directory" % GRAPH_DIR)

        for component, graph_item in self.params.mainfile_data["graph"].iteritems():
            if self.utils.isExternal(graph_item):
                component_run = Run(self.answers_file, self.utils.getExternalAppDir(component), self.dryrun, self.debug)
                component_run.run()
            else:
                self._processComponent(component, graph_item)

    def _applyTemplate(self, data, component):
        template = Template(data)
        config = self.params.get(component)
        return template.substitute(config)

    def _getProvider(self):
        for provider in self.plugins.getAllPlugins():
            module_path = provider.details.get("Core", "Module")
            if os.path.basename(module_path) == self.params.provider:
                return provider.plugin_object

    def _processComponent(self, component, graph_item):
        logger.debug("Processing component %s" % component)
        
        data = None
        artifacts = self.utils.getArtifacts(component)
        logger.debug(artifacts)
        artifact_provider_list = []
        if not self.params.provider in artifacts:
            raise Exception("Data for provider \"%s\" are not part of this app" % self.params.provider)
        
        dst_dir = os.path.join(self.utils.tmpdir, component)
        for artifact in artifacts[self.params.provider]:
            artifact_path = self.utils.sanitizePath(artifact)
            with open(os.path.join(self.app_path, artifact_path), "r") as fp:
                data = fp.read()

            logger.debug("Templating artifact %s/%s" % (self.app_path, artifact_path))
            data = self._applyTemplate(data, component)
        
            artifact_dst = os.path.join(dst_dir, artifact_path)
            
            if not os.path.isdir(os.path.dirname(artifact_dst)):
                os.makedirs(os.path.dirname(artifact_dst))
            with open(artifact_dst, "w") as fp:
                logger.debug("Writing artifact to %s" % artifact_dst)
                fp.write(data)

            artifact_provider_list.append(artifact_path)

        provider = self._getProvider()
        logger.info("Using provider %s for component %s" % (self.params.provider, component))
        provider.init(self.params.get(component), artifact_provider_list, dst_dir, self.dryrun, logger)
        provider.deploy()

    def run(self):
        self.params.loadMainfile(os.path.join(self.params.target_path, MAIN_FILE))
        self.params.loadAnswers(self.answers_file)

        self.utils.checkArtifacts()
        config = self.params.get()
        if "provider" in config[GLOBAL_CONF]:
            self.provider = config[GLOBAL_CONF]["provider"]

        self._dispatchGraph()

    


