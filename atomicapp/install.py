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
import distutils.dir_util
import json
import subprocess

import logging

from nulecule_base import Nulecule_Base
from utils import Utils, printStatus
from constants import APP_ENT_PATH, MAIN_FILE, ANSWERS_FILE_SAMPLE_FORMAT

logger = logging.getLogger(__name__)


class Install(object):
    dryrun = False
    params = None
    answers_file = None
    docker_cli = "docker"
    answers_file_values = {}

    def __init__(
            self, answers, APP, nodeps=False, update=False, target_path=None,
            dryrun=False, answers_format=ANSWERS_FILE_SAMPLE_FORMAT, **kwargs):
        self.dryrun = dryrun
        self.kwargs = kwargs

        app = APP  # FIXME

        self.nulecule_base = Nulecule_Base(
            nodeps, update, target_path, dryrun, answers_format)

        if os.path.exists(app):
            logger.info("App path is %s, will be populated to %s", app, target_path)
            app = self._loadApp(app)
        else:
            logger.info("App name is %s, will be populated to %s", app, target_path)

        printStatus("Loading app %s ." % app)
        if not target_path:
            if self.nulecule_base.app_path:
                self.nulecule_base.target_path = self.nulecule_base.app_path
            else:
                self.nulecule_base.target_path = os.getcwd()

        self.utils = Utils(self.nulecule_base.target_path)

        self.nulecule_base.app = app

        self.answers_file = answers
        self.docker_cli = Utils.getDockerCli(self.dryrun)

    def _loadApp(self, app_path):
        self.nulecule_base.app_path = app_path

        if not os.path.basename(app_path) == MAIN_FILE:
            app_path = os.path.join(app_path, MAIN_FILE)

        mainfile_data = self.nulecule_base.loadMainfile(app_path)
        app = os.environ["IMAGE"] if "IMAGE" in os.environ else mainfile_data["id"]
        logger.debug("Setting path to %s", self.nulecule_base.app_path)

        return app

    def _copyFromContainer(self, image):
        image = self.nulecule_base.getImageURI(image)

        name = "%s-%s" % (self.utils.getComponentName(image),
                          ''.join(Utils.getUniqueUUID()))
        logger.debug("Creating a container with name %s", name)

        # Workaround docker bug BZ1252168 by using run instead of create
        create = [self.docker_cli, "run", "--name", name, "--entrypoint", "/bin/true", image]
        logger.debug(" ".join(create))
        subprocess.call(create)
        cp = [self.docker_cli, "cp", "%s:/%s" % (name, APP_ENT_PATH), self.utils.tmpdir]
        logger.debug(cp)
        if not subprocess.call(cp):
            logger.debug("Application entity data copied to %s", self.utils.tmpdir)

        printStatus("Copied app successfully.")
        rm = [self.docker_cli, "rm", name]
        subprocess.call(rm)

    def _populateApp(self, src=None, dst=None):
        logger.info("Copying app %s", self.utils.getComponentName(self.nulecule_base.app))
        if not src:
            src = os.path.join(self.utils.tmpdir, APP_ENT_PATH)

        if not dst:
            dst = self.nulecule_base.target_path
        distutils.dir_util.copy_tree(src, dst, update=(not self.nulecule_base.update))

    def _fromImage(self):
        return not self.nulecule_base.app_path or \
            self.nulecule_base.target_path == self.nulecule_base.app_path

    def install(self):
        answerContent = self.nulecule_base.loadAnswers(self.answers_file)
        logger.debug(json.dumps(answerContent))

        mainfile_dir = self.nulecule_base.app_path
        if not self.dryrun:
            if self._fromImage():
                self.nulecule_base.pullApp()
                self._copyFromContainer(self.nulecule_base.app)
                mainfile_dir = self.utils.getTmpAppDir()

            current_app_id = None
            if os.path.isfile(self.nulecule_base.getMainfilePath()):
                current_app_id = Utils.getAppId(self.nulecule_base.getMainfilePath())
                printStatus("Loading app_id %s ." % current_app_id)

            if current_app_id:
                tmp_mainfile_path = os.path.join(mainfile_dir, MAIN_FILE)
                self.nulecule_base.loadMainfile(tmp_mainfile_path)
                logger.debug("%s path for pulled image: %s", MAIN_FILE, tmp_mainfile_path)
                if current_app_id != self.nulecule_base.app_id:
                    msg = ("You are trying to overwrite existing app %s with "
                           "app %s - clear or change current directory."
                           % (current_app_id, self.nulecule_base.app_id))
                    raise Exception(msg)
        elif self._fromImage():
            logger.warning("Using DRY-RUN together with install from image "
                           "may result in unexpected behaviour")

        if self.nulecule_base.update or \
            (not self.dryrun and
             not os.path.exists(self.nulecule_base.getMainfilePath())):
            if self._fromImage():
                self._populateApp()
            else:
                logger.info("Copying content of directory %s to %s",
                            self.nulecule_base.app_path, self.nulecule_base.target_path)
                self._populateApp(src=self.nulecule_base.app_path)

        mainfile_path = os.path.join(self.nulecule_base.target_path, MAIN_FILE)
        if not self.nulecule_base.mainfile_data:
            self.nulecule_base.loadMainfile(mainfile_path)

        logger.debug("App ID: %s", self.nulecule_base.app_id)

        self.nulecule_base.checkSpecVersion()
        printStatus("Checking all artifacts")
        self.nulecule_base.checkAllArtifacts()

        printStatus("Loading Nulecule file.")
        if not self.nulecule_base.nodeps:
            logger.info("Installing dependencies for %s", self.nulecule_base.app_id)
            self.answers_file_values = self._installDependencies()
            printStatus("All dependencies installed successfully.")

        logger.debug(self.answers_file_values)
        answerContent = self.nulecule_base.loadAnswers(self.answers_file_values)
        logger.debug(self.nulecule_base.answers_data)
        if self.nulecule_base.write_sample_answers:
            self.nulecule_base.writeAnswersSample()

        logger.debug(json.dumps(answerContent))
        printStatus("Install Successful.")
        return None

    def _installDependencies(self):
        values = {}
        for graph_item in self.nulecule_base.mainfile_data["graph"]:
            component = graph_item.get("name")
            if not component:
                raise ValueError("Component name missing in graph")

            if not self.utils.isExternal(graph_item):
                values[component] = self.nulecule_base.getValues(
                    component, skip_asking=True)
                logger.debug("Component %s is part of the app", component)
                logger.debug("Values: %s", values)
                continue

            logger.info("Component %s is external dependency", component)

            image_name = self.utils.getSourceImage(graph_item)
            component_path = self.utils.getExternalAppDir(component)
            mainfile_component_path = os.path.join(component_path, MAIN_FILE)
            logger.debug("Component path: %s", component_path)
            if not os.path.isfile(mainfile_component_path) or self.nulecule_base.update:
                printStatus("Pulling %s ..." % image_name)
                component_app = Install(
                    self.nulecule_base.answers_data,
                    image_name, self.nulecule_base.nodeps,
                    self.nulecule_base.update, component_path, self.dryrun)
                component_app.install()
                values = Utils.update(values, component_app.answers_file_values)
                printStatus("Component %s installed successfully." % component)
                logger.debug("Component installed into %s", component_path)
            else:
                printStatus("Component %s already installed." % component)
                logger.info("Component %s already exists at %s - remove the directory "
                            "or use --update option" % (component, component_path))

        return values
