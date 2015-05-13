#!/usr/bin/env python

from __future__ import print_function
import os,sys
from string import Template

import logging

from params import Params
from utils import Utils
from constants import GLOBAL_CONF, DEFAULT_PROVIDER, MAIN_FILE, PARAMS_FILE
from plugin import Plugin
from install import Install

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
    plugins = []
    update = False
    app_path = None
    target_path = None
    app_id = None
    app = None
    answers_output = None
    kwargs = None

    def __init__(self, answers, APP, dryrun = False, debug = False, **kwargs):

        self.debug = debug
        self.dryrun = dryrun
        self.kwargs = kwargs
        if "answers_output" in kwargs:
            self.answers_output = kwargs["answers_output"]

        if os.environ and "IMAGE" in os.environ:
            self.app_path = APP
            APP = os.environ["IMAGE"]

        if APP and os.path.exists(APP):
            self.app_path = APP
        else:
            self.app_path = os.getcwd()
            install = Install(answers, APP, dryrun = dryrun, target_path = self.app_path)
            install.install()

        self.params = Params(target_path=self.app_path)
        if "ask" in kwargs:
            self.params.ask = kwargs["ask"]

        self.utils = Utils(self.params)

        self.answers_file = answers
        self.plugin = Plugin()
        self.plugin.load_plugins()

    def _dispatchGraph(self):
        if not "graph" in self.params.mainfile_data:
            raise Exception("Graph not specified in %s" % MAIN_FILE)

        for component, graph_item in self.params.mainfile_data["graph"].iteritems():
            if self.utils.isExternal(graph_item):
                component_run = Run(self.answers_file, self.utils.getExternalAppDir(component), self.dryrun, self.debug, **self.kwargs)
                ret = component_run.run()
                if self.answers_output:
                    self.params.loadAnswers(ret)
            else:
                self._processComponent(component, graph_item)

    def _applyTemplate(self, data, component):
        template = Template(data)
        config = self.params.getValues(component)
        logger.debug("Config: %s " % config)

        output = None
        while not output:
            try:
                logger.debug(config)
                output = template.substitute(config)
            except KeyError as ex:
                name = ex.args[0]
                logger.debug("Artifact contains unknown parameter %s, asking for it" % name)
                config[name] = self.params._askFor(name, {"description": "Missing parameter '%s', provide the value or fix your %s" % (name, MAIN_FILE)})
                if not len(config[name]):
                    raise Exception("Artifact contains unknown parameter %s" % name)
                self.params.loadAnswers({component: {name: config[name]}})

        return output

    def _processComponent(self, component, graph_item):
        logger.debug("Processing component %s" % component)
        
        data = None
        artifacts = self.utils.getArtifacts(component)
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

        provider_class = self.plugin.getProvider(self.params.provider)
        provider = provider_class(self.params.getValues(component), artifact_provider_list, dst_dir, self.dryrun)
        if provider:
            logger.info("Using provider %s for component %s" % (self.params.provider, component))
        else:
            raise Exception("Something is broken - couldn't get the provider")
        provider.init()
        provider.deploy()

    def run(self):
        self.params.loadMainfile(os.path.join(self.params.target_path, MAIN_FILE))
        self.params.loadAnswers(self.answers_file)

        self.utils.checkArtifacts()
        config = self.params.get()
        if "provider" in config:
            self.provider = config["provider"]

        self._dispatchGraph()

#Think about this a bit more probably - it's (re)written for all components...
        if self.answers_output:
            self.params.writeAnswers(self.answers_output)
            return self.params.answers_data

        return None

    


