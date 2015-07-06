from __future__ import print_function
import os,sys
from string import Template

import logging

from nulecule_base import Nulecule_Base
from utils import Utils
from constants import GLOBAL_CONF, DEFAULT_PROVIDER, MAIN_FILE
from plugin import Plugin, ProviderFailedException
from install import Install

logger = logging.getLogger(__name__)


class Run(object):
    debug = False
    dryrun = False
    nulecule_base = None
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

    def __init__(self, answers, APP, dryrun = False, debug = False, stop = False, **kwargs):

        self.debug = debug
        self.dryrun = dryrun
        self.stop = stop
        self.kwargs = kwargs
        
        if "answers_output" in kwargs:
            self.answers_output = kwargs["answers_output"]

        if os.environ and "IMAGE" in os.environ:
            self.app_path = APP
            APP = os.environ["IMAGE"]
            del os.environ["IMAGE"]
        elif "image" in kwargs:
            logger.warning("Setting image to %s", kwargs["image"])

            self.app_path = APP
            APP = kwargs["image"]
            del kwargs["image"]

        self.kwargs = kwargs

        if APP and os.path.exists(APP):
            self.app_path = APP
        else:
            if not self.app_path:
                self.app_path = os.getcwd()
            install = Install(answers, APP, dryrun = dryrun, target_path = self.app_path)
            install.install()

        self.nulecule_base = Nulecule_Base(target_path=self.app_path, dryrun = dryrun)
        if "ask" in kwargs:
            self.nulecule_base.ask = kwargs["ask"]

        workdir = None
        if "workdir" in kwargs:
            workdir = kwargs["workdir"]

        self.utils = Utils(self.app_path, workdir)
        if not "workdir" in kwargs:
            kwargs["workdir"] = self.utils.workdir


        self.answers_file = answers
        self.plugin = Plugin()
        self.plugin.load_plugins()

    def _dispatchGraph(self):
        if not "graph" in self.nulecule_base.mainfile_data:
            raise Exception("Graph not specified in %s" % MAIN_FILE)

        for graph_item in self.nulecule_base.mainfile_data["graph"]:
            component = graph_item.get("name")
            if not component:
                raise ValueError("Component name missing in graph")

            if self.utils.isExternal(graph_item):
                self.kwargs["image"] = self.utils.getSourceImage(graph_item)
                component_run = Run(self.answers_file, self.utils.getExternalAppDir(component), self.dryrun, self.debug, self.stop, **self.kwargs)
                ret = component_run.run()
                if self.answers_output:
                    self.nulecule_base.loadAnswers(ret)
            else:
                self._processComponent(component, graph_item)

    def _applyTemplate(self, data, component):
        template = Template(data)
        config = self.nulecule_base.getValues(component)
        logger.debug("Config: %s ", config)

        output = None
        while not output:
            try:
                logger.debug(config)
                output = template.substitute(config)
            except KeyError as ex:
                name = ex.args[0]
                logger.debug("Artifact contains unknown parameter %s, asking for it", name)
                config[name] = self.utils.askFor(name, {"description": "Missing parameter '%s', provide the value or fix your %s" % (name, MAIN_FILE)})
                if not len(config[name]):
                    raise Exception("Artifact contains unknown parameter %s" % name)
                self.nulecule_base.loadAnswers({component: {name: config[name]}})

        return output

    def _processArtifacts(self, component, provider, provider_name = None):
        if not provider_name:
            provider_name = str(provider)

        artifacts = self.nulecule_base.getArtifacts(component)
        artifact_provider_list = []
        if not provider_name in artifacts:
            raise Exception("Data for provider \"%s\" are not part of this app" % provider_name)

        dst_dir = os.path.join(self.utils.workdir, component)
        data = None

        for artifact in artifacts[provider_name]:
            if "inherit" in artifact:
                logger.debug("Inheriting from %s", artifact["inherit"])
                for item in artifact["inherit"]:
                    inherited_artifacts, _ = self._processArtifacts(component, provider, item)
                    artifact_provider_list += inherited_artifacts
                continue
            artifact_path = self.utils.sanitizePath(artifact)
            data = provider.loadArtifact(os.path.join(self.app_path, artifact_path))

            logger.debug("Templating artifact %s/%s", self.app_path, artifact_path)
            data = self._applyTemplate(data, component)

            artifact_dst = os.path.join(dst_dir, artifact_path)

            provider.saveArtifact(artifact_dst, data)

            artifact_provider_list.append(artifact_path)

        return artifact_provider_list, dst_dir

    def _processComponent(self, component, graph_item):
        logger.debug("Processing component '%s' and graph item '%s'", component, graph_item)

        provider_class = self.plugin.getProvider(self.nulecule_base.provider)
        dst_dir = os.path.join(self.utils.workdir, component) 
        provider = provider_class(self.nulecule_base.getValues(component), dst_dir, self.dryrun)
        if provider:
            logger.info("Using provider %s for component %s", self.nulecule_base.provider, component)
        else:
            raise Exception("Something is broken - couldn't get the provider")

        provider.artifacts, dst_dir = self._processArtifacts(component, provider)

        try:
            provider.init()
            if self.stop:
                provider.undeploy()
            else:
                provider.deploy()
        except ProviderFailedException as ex:
            logger.error(ex)
            sys.exit(1)

    def run(self):
        self.nulecule_base.loadMainfile(os.path.join(self.nulecule_base.target_path, MAIN_FILE))
        self.nulecule_base.checkSpecVersion()
        self.nulecule_base.loadAnswers(self.answers_file)

        self.nulecule_base.checkAllArtifacts()
        config = self.nulecule_base.get()
        if "provider" in config:
            self.provider = config["provider"]

        self._dispatchGraph()

#Think about this a bit more probably - it's (re)written for all components...
        if self.answers_output:
            self.nulecule_base.writeAnswers(self.answers_output)
            return self.nulecule_base.answers_data

        return None




