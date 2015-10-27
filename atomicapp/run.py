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

from __future__ import print_function
import os
from string import Template

import logging
import anymarkup

from nulecule_base import Nulecule_Base
from utils import Utils, printStatus, printErrorStatus
from constants import GLOBAL_CONF, DEFAULT_PROVIDER, MAIN_FILE, \
        ANSWERS_FILE_SAMPLE_FORMAT, PARAMS_KEY, RESOURCE_KEY, \
        INHERIT_KEY
from plugin import Plugin, ProviderFailedException
from install import Install

from jsonpointer import resolve_pointer, set_pointer, JsonPointerException

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

    def __init__(
            self, answers, APP, dryrun=False, debug=False, stop=False,
            answers_format=ANSWERS_FILE_SAMPLE_FORMAT, **kwargs):

        self.debug = debug
        self.dryrun = dryrun
        self.stop = stop
        self.kwargs = kwargs
        self.cli_provider = None

        if "answers_output" in kwargs:
            self.answers_output = kwargs["answers_output"]

        if "cli_provider" in kwargs:
            self.cli_provider = kwargs["cli_provider"]

        if os.environ and "IMAGE" in os.environ:
            self.app_path = APP
            APP = os.environ["IMAGE"]
            del os.environ["IMAGE"]
        elif "image" in kwargs:
            logger.warning("Setting image to %s" % kwargs["image"])

            self.app_path = APP
            APP = kwargs["image"]
            del kwargs["image"]

        self.kwargs = kwargs

        if APP and os.path.exists(APP):
            self.app_path = APP
        else:
            if not self.app_path:
                self.app_path = os.getcwd()
            install = Install(
                answers, APP, dryrun=dryrun, target_path=self.app_path,
                answers_format=answers_format)
            install.install()
            printStatus("Install Successful.")

        self.nulecule_base = Nulecule_Base(
            target_path=self.app_path,
            dryrun=dryrun,
            file_format=answers_format,
            cli_provider=self.cli_provider)
        if "ask" in kwargs:
            self.nulecule_base.ask = kwargs["ask"]

        workdir = None
        if "workdir" in kwargs:
            workdir = kwargs["workdir"]

        self.utils = Utils(self.app_path, workdir)
        if "workdir" not in kwargs:
            kwargs["workdir"] = self.utils.workdir

        self.answers_file = answers
        self.plugin = Plugin()
        self.plugin.load_plugins()

    def _dispatchGraph(self):
        if "graph" not in self.nulecule_base.mainfile_data:
            printErrorStatus("Graph not specified in %s." % MAIN_FILE)
            raise Exception("Graph not specified in %s" % MAIN_FILE)

        for graph_item in self.nulecule_base.mainfile_data["graph"]:
            component = graph_item.get("name")
            if not component:
                printErrorStatus("Component name missing in graph.")
                raise ValueError("Component name missing in graph")

            if self.utils.isExternal(graph_item):
                self.kwargs["image"] = self.utils.getSourceImage(graph_item)
                component_run = Run(self.answers_file, self.utils.getExternalAppDir(
                    component), self.dryrun, self.debug, self.stop, **self.kwargs)
                ret = component_run.run()
                if self.answers_output:
                    self.nulecule_base.loadAnswers(ret)
            else:
                self._processComponent(component, graph_item)

    def _applyPointers(self, data, component, params_map,  config):
        '''
        Tries to parse the artifact and returns None if that fails (which
        probably means $ substitution is used). If it succeedes, it checks
        if all params have pointer (no mixing, please!). Last step is to
        replace all values in artifact according to given pointers.
        '''

        obj = anymarkup.parse(data)
        if type(obj) != dict:
            return None
        params = self.nulecule_base.getParams(component)

        for param in params:
            name = param.get("name")
            pointers = params_map.get(name)
            if not pointers:
                logger.warning("COuldn't find %s", name)
                continue

            for pointer in pointers:
                try:
                    resolve_pointer(obj, pointer)
                    set_pointer(obj, pointer, config.get(name))
                except JsonPointerException:
                    logger.error("Couldn't replace param %s (%s) in %s artifact.", name, pointer, component)
                    logger.debug("Artifact content: %s", obj)
                    raise

        return anymarkup.serialize(obj, format="json")

    def _applyTemplate(self, data, component, config):
        template = Template(data)

        logger.debug("Config: %s ", config)

        output = None
        while not output:
            try:
                logger.debug(config)
                output = template.substitute(config)
            except KeyError as ex:
                name = ex.args[0]
                logger.debug(
                    "Artifact contains unknown parameter %s, asking for it", name)
                try:
                    config[name] = self.utils.askFor(
                        name,
                        {"description":
                         "Missing parameter '%s', provide the value or fix your %s" % (
                             name, MAIN_FILE)})
                except EOFError:
                    raise Exception("Artifact contains unknown parameter %s" % name)
                if not len(config[name]):
                    printErrorStatus("Artifact contains unknown parameter %s." % name)
                    raise Exception("Artifact contains unknown parameter %s" % name)
                self.nulecule_base.loadAnswers({component: {name: config[name]}})

        return output

    def _processArtifact(self, data, component, params_map):
        if self.stop:
            config = self.nulecule_base.getValues(component, skip_asking=True)
        else:
            config = self.nulecule_base.getValues(component)

        if params_map:
            return self._applyPointers(data, component, params_map, config)
        else:
            return self._applyTemplate(data, component, config)

    def _processArtifacts(self, component, provider, provider_name=None):
        if not provider_name:
            provider_name = str(provider)

        artifacts = self.nulecule_base.getArtifacts(component)
        artifact_provider_list = []
        if provider_name not in artifacts:
            msg = "Data for provider \"%s\" are not part of this app" % provider_name
            raise Exception(msg)

        dst_dir = os.path.join(self.utils.workdir, component)
        data = None

        for artifact in artifacts[provider_name]:
            if INHERIT_KEY in artifact:
                logger.debug("Inheriting from %s", artifact[INHERIT_KEY])
                for item in artifact[INHERIT_KEY]:
                    inherited_artifacts, _ = self._processArtifacts(
                        component, provider, item)
                    artifact_provider_list += inherited_artifacts
                continue

            params_map = self.nulecule_base.getParamsMap(artifact)
            resource = self.nulecule_base.getResource(artifact)
            artifact_path = self.utils.sanitizePath(resource)
            data = provider.loadArtifact(os.path.join(self.app_path, artifact_path))

            logger.debug("Templating artifact %s/%s", self.app_path, artifact_path)
            data = self._processArtifact(data, component, params_map)

            artifact_dst = os.path.join(dst_dir, artifact_path)

            provider.saveArtifact(artifact_dst, data)

            artifact_provider_list.append(artifact_path)

        return artifact_provider_list, dst_dir

    def _processComponent(self, component, graph_item):
        logger.debug(
            "Processing component '%s' and graph item '%s'", component, graph_item)
        provider_class = self.plugin.getProvider(self.nulecule_base.provider)
        dst_dir = os.path.join(self.utils.workdir, component)
        if self.stop:
            component_values = self.nulecule_base.getValues(component, skip_asking=True)
        else:
            component_values = self.nulecule_base.getValues(component)
        provider = provider_class(component_values, dst_dir, self.dryrun)
        if provider:
            printStatus("Deploying component %s ..." % component)
            logger.info("Using provider %s for component %s",
                        self.nulecule_base.provider, component)
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
            printErrorStatus(ex)
            logger.error(ex)
            raise

    def run(self):
        self.nulecule_base.loadMainfile(
            os.path.join(self.nulecule_base.target_path, MAIN_FILE))
        self.nulecule_base.checkSpecVersion()
        self.nulecule_base.loadAnswers(self.answers_file)

        self.nulecule_base.checkAllArtifacts()

        self._dispatchGraph()

# Think about this a bit more probably - it's (re)written for all components...
        if self.answers_output:
            self.nulecule_base.writeAnswers(self.answers_output)
            return self.nulecule_base.answers_data

        return None
