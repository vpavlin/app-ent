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

import anymarkup
import os
import logging
import copy
import subprocess

from constants import MAIN_FILE, GLOBAL_CONF, DEFAULT_PROVIDER, PARAMS_KEY, \
    ANSWERS_FILE, DEFAULT_ANSWERS, ANSWERS_FILE_SAMPLE, \
    __NULECULESPECVERSION__, ANSWERS_FILE_SAMPLE_FORMAT, \
    RESOURCE_KEY, INHERIT_KEY

from utils import Utils, printStatus, printErrorStatus

logger = logging.getLogger(__name__)


class Nulecule_Base(object):
    answers_data = None
    params_data = None
    mainfile_data = None
    __target_path = None
    nodeps = False
    app_id = None
    app_path = None
    __provider = DEFAULT_PROVIDER
    __app = None
    ask = False
    write_sample_answers = False
    docker_cli = None
    answer_file_format = ANSWERS_FILE_SAMPLE_FORMAT

    @property
    def app(self):
        if not self.__app and self.mainfile_data:
            self.__app = self.app_id
        return self.__app

    @app.setter
    def app(self, val):
        self.__app = val

    @property
    def provider(self):
        config = self.get()
        if self.cli_provider:
            return self.cli_provider
        elif "provider" in config:
            return config["provider"]
        return self.__provider

    @property
    def target_path(self):
        return self.__target_path

    @target_path.setter
    def target_path(self, path):
        if not path:
            path = os.getcwd()
        if not os.path.isdir(path):
            os.makedirs(path)

        self.__target_path = path

    def __init__(
            self, nodeps=False, update=False, target_path=None,
            dryrun=False, file_format=ANSWERS_FILE_SAMPLE_FORMAT,
            cli_provider=None):
        self.target_path = target_path
        self.nodeps = Utils.isTrue(nodeps)
        self.update = Utils.isTrue(update)
        self.override = Utils.isTrue(False)
        self.dryrun = dryrun
        self.docker_cli = Utils.getDockerCli(dryrun)
        self.answer_file_format = file_format
        self.cli_provider = cli_provider

    def loadParams(self, data=None):
        if type(data) == dict:
            logger.debug("Data given: %s", data)
        elif os.path.exists(data):
            logger.debug("Path given, loading %s", data)
            data = anymarkup.parse_file(data)
        else:
            raise Exception("Given params are broken: %s" % data)

        if "specversion" in data:
            logger.debug("Params part of %s", MAIN_FILE)
            tmp = {}
            tmp[GLOBAL_CONF] = self.fromListToDict(data[PARAMS_KEY])
            data = tmp
        else:
            logger.debug("Params in separate file")

        if self.params_data:
            self.params_data = Utils.update(self.params_data, data)
        else:
            self.params_data = data

        return self.params_data

    def loadMainfile(self, path=None):
        if not os.path.exists(path):
            raise Exception("%s not found: %s" % (MAIN_FILE, path))

        self.mainfile_data = anymarkup.parse_file(path)
        if "id" in self.mainfile_data:
            self.app_id = self.mainfile_data["id"]
            logger.debug("Setting app id to %s", self.mainfile_data["id"])
        else:
            raise Exception("Missing ID in %s" % self.mainfile_data)

        if PARAMS_KEY in self.mainfile_data:
            logger.debug("Loading params")
            self.loadParams(self.mainfile_data)

        return self.mainfile_data

    def loadAnswers(self, data=None):
        if not data:
            logger.info("No answers data given")

        if type(data) == dict:
            logger.debug("Data given %s", data)
        elif os.path.exists(data):
            logger.debug("Path to answers file given, loading %s", data)
            if os.path.isdir(data):
                if os.path.isfile(os.path.join(data, ANSWERS_FILE)):
                    data = os.path.join(data, ANSWERS_FILE)
                else:
                    self.write_sample_answers = True

            if os.path.isfile(data):
                data = anymarkup.parse_file(data)
        else:
            self.write_sample_answers = True

        if self.write_sample_answers:
            data = copy.deepcopy(DEFAULT_ANSWERS)

        if self.answers_data:
            self.answers_data = Utils.update(self.answers_data, data)
        else:
            self.answers_data = data

        return self.answers_data

    def get(self, component=None, global_base=True):
        params = None
        if component:
            params = self._mergeParamsComponent(component, global_base=global_base)
        else:
            params = self._mergeParamsComponent()  # self._mergeParams()

        return params

    def getValues(self, component=GLOBAL_CONF, skip_asking=False):
        params = self.get(component, not skip_asking)

        values = self._getComponentValues(params, skip_asking)
        for n, p in values.iteritems():
            self._updateAnswers(component, n, p)
        return values

    def _mergeParamsComponent(self, component=GLOBAL_CONF, global_base=True):
        component_config = self._mergeParamsComponent(
        ) if not component == GLOBAL_CONF and global_base else {}
        if component == GLOBAL_CONF:
            if self.mainfile_data and PARAMS_KEY in self.mainfile_data:
                config = self.fromListToDict(self.mainfile_data[PARAMS_KEY])
                component_config = Utils.update(
                    component_config, config)
        else:
            graph_item = self.getComponent(component)
            if graph_item and PARAMS_KEY in graph_item:
                config = self.fromListToDict(graph_item[PARAMS_KEY])
                component_config = Utils.update(component_config, config)

        if component in self.answers_data:
            tmp_clean_answers = self._cleanNullValues(self.answers_data[component])
            component_config = Utils.update(component_config, tmp_clean_answers)
        return component_config

    def _getValue(self, param, name, skip_asking=False):
        value = None

        if type(param) == dict:
            if "default" in param:
                value = param["default"]
            if not skip_asking and (self.ask or not value) and \
                    "description" in param:  # FIXME
                printErrorStatus("%s is missing in answers.conf ." % (name))
                logger.debug("Ask for %s: %s", name, param["description"])
                value = Utils.askFor(name, param)
            elif not skip_asking and not value:
                logger.debug("Skipping %s", name)
                value = param
        else:
            value = param

        return value

    def _getComponentValues(self, data, skip_asking=False):
        result = {}
        for name, p in data.iteritems():
            value = self._getValue(p, name, skip_asking)
            result[name] = value
        return result

    def _cleanNullValues(self, data):
        result = {}
        for name, value in data.iteritems():
            if value:
                result[name] = value

        return result

    def _updateAnswers(self, component, param, value):
        if component not in self.answers_data:
            self.answers_data[component] = {}

        if component != GLOBAL_CONF and param in self.answers_data[GLOBAL_CONF] \
                and value == self.answers_data[GLOBAL_CONF][param]:
            logger.debug(
                "Param %s already in %s with value %s", param, GLOBAL_CONF, value)
            return

        if param not in self.answers_data[component]:
            self.answers_data[component][param] = None

        self.answers_data[component][param] = value

    def writeAnswers(self, path):
        logger.debug("writing %s to %s with format %s",
                     self.answers_data, path, self.answer_file_format)
        anymarkup.serialize_file(self.answers_data, path, format=self.answer_file_format)

    def writeAnswersSample(self):
        path = os.path.join(self.target_path, ANSWERS_FILE_SAMPLE)
        logger.info("Writing answers file template to %s", path)
        self.writeAnswers(path)

    def getComponent(self, component):
        return self.getItem(self.mainfile_data["graph"], component)

    def getItem(self, items, key):
        for item in items:
            name = item.get("name")
            if name is key:
                return item

    def getParams(self, component):
        return self.getComponent(component).get(PARAMS_KEY)

    def getArtifacts(self, component):
        graph_item = self.getComponent(component)
        if "artifacts" in graph_item:
            return graph_item["artifacts"]

        return None

    def getResource(self, artifact):
        return artifact[RESOURCE_KEY] if isinstance(artifact, dict) else artifact

    def getParamsMap(self, artifact):
        if isinstance(artifact, dict):
            return artifact.get(PARAMS_KEY)

        return None

    def checkArtifacts(self, component, check_provider=None):
        checked_providers = []
        artifacts = self.getArtifacts(component)
        if not artifacts:
            logger.debug("No artifacts for %s", component)
            return []

        for provider, artifact_list in artifacts.iteritems():
            if (check_provider and not provider == check_provider) \
                    or provider in checked_providers:
                continue

            logger.debug("Provider: %s, artifacts object: %s", provider, artifact_list)
            for artifact in artifact_list:
                if INHERIT_KEY in artifact:
                    self._checkInherit(component, artifact[INHERIT_KEY], checked_providers)
                    continue

                resource = self.getResource(artifact)
                path = os.path.join(self.target_path, Utils.sanitizePath(resource))
                if os.path.isfile(path):
                    printStatus("Artifact %s: OK." % (resource))
                else:
                    printErrorStatus("Missing artifact %s." % (resource))
                    raise Exception("Missing artifact %s (%s)" % (resource, path))
            checked_providers.append(provider)

        return checked_providers

    def checkAllArtifacts(self):
        for graph_item in self.mainfile_data["graph"]:
            component = graph_item.get("name")
            if not component:
                raise ValueError("Component name missing in graph")

            checked_providers = self.checkArtifacts(component)
            printStatus("All artifacts OK. ")
            logger.info("Artifacts for %s present for these providers: %s",
                        component, ", ".join(checked_providers))

    def _checkInherit(self, component, inherit_list, checked_providers):
        for inherit_provider in inherit_list:
            if inherit_provider not in checked_providers:
                logger.debug("Checking %s because of 'inherit'", inherit_provider)
                checked_providers += self.checkArtifacts(component, inherit_provider)

    def checkSpecVersion(self):
        if not self.mainfile_data:
            raise ValueError("Could not access %s data" % MAIN_FILE)

        if "specversion" not in self.mainfile_data:
            msg = "Data corrupted: couldn't find specversion in %s" % MAIN_FILE
            raise ValueError(msg)

        if self.mainfile_data["specversion"] == __NULECULESPECVERSION__:
            logger.debug("Version check successful: specversion == %s",
                         __NULECULESPECVERSION__)
        else:
            logger.error("Your version in %s file (%s) does not match "
                         "supported version (%s)" % (MAIN_FILE,
                                                     self.mainfile_data["specversion"],
                                                     __NULECULESPECVERSION__))
            raise Exception("Spec version check failed")

    def getImageURI(self, image):
        config = self.get()
        logger.debug(config)

        if "registry" in config:
            logger.info("Adding registry %s for %s", config["registry"], image)
            image = os.path.join(config["registry"], image)

        return image

    def pullApp(self, image=None, update=None):
        if not image:
            image = self.app
        if not update:
            update = self.update

        image = self.getImageURI(image)
        if not update:
            check_cmd = ["docker", "images", "-q", image]
            image_id = subprocess.check_output(check_cmd)
            logger.debug("Output of docker images cmd: %s", image_id)
            if len(image_id) != 0:
                logger.debug(
                    "Image %s already present with id %s. Use --update to re-pull.",
                    image, image_id.strip())
                return

        pull = ["docker", "pull", image]
        printStatus("Pulling image %s ..." % image)
        if subprocess.call(pull) != 0:
            printErrorStatus("Couldn't pull %s." % image)
            raise Exception("Couldn't pull %s" % image)

    def fromListToDict(self, llist):
        result = {}
        for item in llist:
            if "name" in item:
                result[item.get("name")] = item
            else:
                logger.warning("Attribute 'name' missing in %s", item)

        return result

    def getMainfilePath(self):
        return os.path.join(self.target_path, MAIN_FILE)
