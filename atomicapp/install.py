from __future__ import print_function
import os
import distutils.dir_util
import random, string

import subprocess

import logging

from nulecule_base import Nulecule_Base
from utils import Utils
from constants import APP_ENT_PATH, MAIN_FILE
import context
logger = logging.getLogger(__name__)

class Install(object):
    dryrun = False
    params = None
    answers_file = None
    docker_cli = "docker"

    def __init__(self, answers, APP, nodeps = False, update = False, target_path = None, dryrun = False, **kwargs):
        self.dryrun = dryrun
        self.kwargs = kwargs

        app = APP #FIXME
        context.globalCtx.setApp(app)

        self.nulecule_base = Nulecule_Base(nodeps, update, target_path, dryrun)

        if os.path.exists(app):
            logger.info("App path is %s, will be populated to %s", app, target_path)
            app = self._loadApp(app)
        else:
            logger.info("App name is %s, will be populated to %s", app, target_path)

        context.globalCtx.addStatus("Loading app %s ." % app)
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

        name = "%s-%s" % (self.utils.getComponentName(image), ''.join(random.sample(string.letters, 6)))
        logger.debug("Creating a container with name %s", name)

        create = [self.docker_cli, "create", "--name", name, image, "nop"]
        subprocess.call(create)
        cp = [self.docker_cli, "cp", "%s:/%s" % (name, APP_ENT_PATH), self.utils.tmpdir]
        logger.debug(cp)
        if not subprocess.call(cp):
            logger.debug("Application entity data copied to %s", self.utils.tmpdir)

        context.globalCtx.addStatus("Copied app successfully.")
        rm = [self.docker_cli, "rm", name]
        subprocess.call(rm)

    def _populateApp(self, src = None, dst = None):
        logger.info("Copying app %s", self.utils.getComponentName(self.nulecule_base.app))
        if not src:
            src = os.path.join(self.utils.tmpdir, APP_ENT_PATH)

        if not dst:
            dst = self.nulecule_base.target_path
        distutils.dir_util.copy_tree(src, dst, update=(not self.nulecule_base.update))

    def _fromImage(self):
        return not self.nulecule_base.app_path or self.nulecule_base.target_path == self.nulecule_base.app_path

    def install(self):
        answerContent = self.nulecule_base.loadAnswers(self.answers_file)
        context.globalCtx.addStatus("Loading answers.conf", answerContent)

        mainfile_dir = self.nulecule_base.app_path
        if not self.dryrun:
            if self._fromImage():
                self.nulecule_base.pullApp()
                self._copyFromContainer(self.nulecule_base.app)
                mainfile_dir = self.utils.getTmpAppDir()

            current_app_id = None
            if os.path.isfile(self.nulecule_base.getMainfilePath()):
                current_app_id = Utils.getAppId(self.nulecule_base.getMainfilePath())
                context.globalCtx.setAppId(current_app_id)

            if current_app_id:
                tmp_mainfile_path = os.path.join(mainfile_dir, MAIN_FILE)
                self.nulecule_base.loadMainfile(tmp_mainfile_path)
                logger.debug("%s path for pulled image: %s", MAIN_FILE, tmp_mainfile_path)
                if current_app_id != self.nulecule_base.app_id:
                    raise Exception("You are trying to overwrite existing app %s with app %s - clear or change current directory." 
                                                % (current_app_id, self.nulecule_base.app_id))
        elif self._fromImage():
            logger.warning("Using DRY-RUN together with install from image may result in unexpected behaviour")

        if self.nulecule_base.update or (not self.dryrun and not os.path.exists(self.nulecule_base.getMainfilePath())):
            if self._fromImage():
                self._populateApp()
            else:
                logger.info("Copying content of directory %s to %s", self.nulecule_base.app_path, self.nulecule_base.target_path)
                self._populateApp(src=self.nulecule_base.app_path)

        mainfile_path = os.path.join(self.nulecule_base.target_path, MAIN_FILE)
        if not self.nulecule_base.mainfile_data:
            self.nulecule_base.loadMainfile(mainfile_path)

        logger.debug("App ID: %s", self.nulecule_base.app_id)

        self.nulecule_base.checkSpecVersion()
        context.globalCtx.addStatus("Checking all artifacts")
        self.nulecule_base.checkAllArtifacts()

        context.globalCtx.addStatus("Loading Nulecule file.")
        values = {}
        if not self.nulecule_base.nodeps:
            logger.info("Installing dependencies for %s", self.nulecule_base.app_id)
            values = self._installDependencies()
            context.globalCtx.addStatus("All dependencies installed successfully.")

        logger.debug(values)
        answerContent = self.nulecule_base.loadAnswers(values)
        logger.debug(self.nulecule_base.answers_data)
        if self.nulecule_base.write_sample_answers:
            self.nulecule_base.writeAnswersSample()

        context.globalCtx.addStatus("Updated answers.conf .", answerContent)
        return values

    def _installDependencies(self):
        values = {}
        for graph_item in self.nulecule_base.mainfile_data["graph"]:
            component = graph_item.get("name")
            if not component:
                raise ValueError("Component name missing in graph")

            if not self.utils.isExternal(graph_item):
                values[component] = self.nulecule_base.getValues(component, skip_asking = True)
                logger.debug("Component %s is part of the app", component)
                logger.debug("Values: %s", values)
                continue

            logger.info("Component %s is external dependency", component)

            image_name = self.utils.getSourceImage(graph_item)
            component_path = self.utils.getExternalAppDir(component)
            mainfile_component_path = os.path.join(component_path, MAIN_FILE)
            logger.debug("Component path: %s", component_path)
            if not os.path.isfile(mainfile_component_path) or self.nulecule_base.update:
                logger.info("Pulling %s", image_name)
                context.globalCtx.addStatus("Pulling %s ..." % image_name)
                component_app = Install(self.nulecule_base.answers_data, image_name, self.nulecule_base.nodeps, 
                                        self.nulecule_base.update, component_path, self.dryrun)
                values = Utils.update(values, component_app.install())
                context.globalCtx.addStatus("Component %s installed successfully."%component)
                logger.info("Component installed into %s", component_path)
            else:
                context.globalCtx.addStatus("Component %s already installed."%component)
                logger.info("Component %s already exists at %s - remove the directory or use --update option", component, component_path)

        return values
