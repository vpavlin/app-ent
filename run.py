#!/usr/bin/python

from __future__ import print_function
import os,sys
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from string import Template
import tempfile
import subprocess
#import anymarkup
import distutils.dir_util
import ConfigParser, json

from yapsy.PluginManager import PluginManager

import logging
from pprint import pprint

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

ATOMIC_FILE="Atomicfile"
PARAMS_FILE="params.conf"
ANSWERS_FILE="answers.conf"
GRAPH_DIR="graph"
APP_ENT_PATH="application-entity"
GLOBAL_CONF="general"
DEFAULT_PROVIDER="kubernetes"

class AtomicappLevel:
    Main, Module = range(2)

def isTrue(val):
    logger.debug("Value: %s" % val)
    return True if str(val).lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'sure'] else False


class Atomicapp():
    debug = False
    dryrun = False
    atomicfile_data = None
    params_data = None
    answers_data = {GLOBAL_CONF: {}}
    tmpdir = None
    answers_file = None
    provider = DEFAULT_PROVIDER
    installed = False
    plugins = None
    recursive = True
    update = False
    app_path = None
    target_path = None
    app_id = None
    app = None

    def __init__(self, answers, app, recursive = True, update = False, target_path = None, dryrun = False, debug = False):

        run_path = os.path.dirname(os.path.realpath(__file__))
        self.debug = debug
        self.dryrun = dryrun
        self.recursive = isTrue(recursive)
        self.update = isTrue(update)
        self.target_path = target_path
        logger.info("Path for %s is %s" % (app, target_path))

        if os.path.exists(app):
            self.app_path = app
            if not os.path.basename(app) == ATOMIC_FILE:
                app = os.path.join(app, ATOMIC_FILE)
            atomic_data = self._loadAtomicfile(app)
            app = os.environ["IMAGE"] if "IMAGE" in os.environ else atomic_data["id"]
            self.app_id = atomic_data["id"]
            print("Setting path to %s" % self.app_path)

        if not self.target_path:
            if self.app_path:
                self.target_path = self.app_path
            else: 
                self.target_path = os.getcwd()


        self.tmpdir = tempfile.mkdtemp(prefix="appent-%s" % self._getComponentName(app))
        logger.debug("Temporary dir: %s" % self.tmpdir)

        self.app = app
        self.answers_file = answers

        self.plugins = PluginManager()
        self.plugins.setPluginPlaces([os.path.join(run_path, "providers")])
        self.plugins.collectPlugins()

    def _sanitizeName(self, app):
        return app.replace("/", "-")

    def _mergeConfig(self):

        config = self.params_data
        if self.answers_data:
            if config:
                config.update(self.answers_data)
            else:
                config = self.answers_data

        return config

    #LOAD FUNCTIONS

    def _loadAtomicfile(self, path = None):
        print(os.path.isfile(path))
        if not os.path.exists(path):
            print("Path: %s" % path)
            logger.error("Atomicfile not found: %s" % path)
            sys.exit(1)

        
        with open(path, "r") as fp:
            self.atomicfile_data = json.load(fp)
            self.app_id = self.atomicfile_data["id"]

        pprint(self.atomicfile_data)
        return self.atomicfile_data

    def _loadParams(self, path = None):
        if not os.path.exists(path):
            return None

        config = ConfigParser.ConfigParser()

        data = {}
        with open(path, "r") as fp:
            config.readfp(fp)

            for section in config.sections():
                data[section] = dict(config.items(section))

        if self.params_data:
                self.params_data.update(data)
        else:
            self.params_data = data

        return self.params_data

    def _loadAnswers(self, path = None):
        if not os.path.exists(path):
            return None

        config = ConfigParser.ConfigParser()

        data = {}
        with open(path, "r") as fp:
            config.readfp(fp)

            for section in config.sections():
                data[section] = dict(config.items(section))
        
        self.answers_data = data

        return self.answers_data

    #GET_FUNCTIONS

    def _getComponentDir(self, component):
        return os.path.join(self.target_path, GRAPH_DIR, self._getComponentName(component))

    def _getProviderDir(self, component):
        #FIXME add provider resolution by answers file
        return os.path.join(self.target_path, GRAPH_DIR, component, self.provider)

    def _getComponentConf(self, component):
        return os.path.join(self._getComponentDir(component), self.provider, PARAMS_FILE)

    def _getTmpAppDir(self):
        return os.path.join(self.tmpdir, APP_ENT_PATH)

    def _getGraphDir(self):
        return os.path.join(self.target_path, GRAPH_DIR)

    def _getComponentName(self, graph_item):
        if type(graph_item) is str or type(graph_item) is unicode:
            return os.path.basename(graph_item).split(":")[0]
        elif type(graph_item) is dict:
            return graph_item["name"].split(":")[0]
        else:
            return None
    
    def _getComponentImageName(self, graph_item):
        if type(graph_item) is str or type(graph_item) is unicode:
            return graph_item
        elif type(graph_item) is dict:
            print(graph_item)
            repo = ""
            if "repository" in graph_item:
                repo = graph_item["repository"]

            print(repo)
            return os.path.join(repo, graph_item["name"])
        else:
            return None

    def _dispatchGraph(self):
        if not "graph" in self.atomicfile_data:
            raise Exception("Graph not specified in %s" % ATOMIC_FILE)
        if not os.path.isdir(self._getGraphDir()):
            raise Exception("Couldn't find %s directory" % GRAPH_DIR)

        for graph_item in self.atomicfile_data["graph"]:
            component = self._getComponentName(graph_item)
            component_path = self._getComponentDir(component)

        
            component_params = self._getComponentConf(component)
            if os.path.isfile(component_params):
                self._loadParams(component_params)
            self._processComponent(component)

    def _applyTemplate(self, data, component):
        template = Template(data)

        config = self._mergeConfig()
        component_config = config[component] if component in config else None

        return template.substitute(component_config)

    def _getProvider(self):
        for provider in self.plugins.getAllPlugins():
            module_path = provider.details.get("Core", "Module")
            if os.path.basename(module_path) == self.provider:
                return provider.plugin_object

    def _processComponent(self, component):
        path = self._getProviderDir(component)
        data = None
        for artifact in os.listdir(path):
            if artifact == PARAMS_FILE:
                continue
            with open(os.path.join(path, artifact), "r") as fp:
                data = fp.read()

            data = self._applyTemplate(data, component)
        
            dst_dir = os.path.join(self.tmpdir, component)
            artifact_dst = os.path.join(dst_dir, artifact)
            
            if not os.path.isdir(dst_dir):
                os.makedirs(dst_dir)
            with open(artifact_dst, "w") as fp:
                fp.write(data)

        provider = self._getProvider()
        provider.init(self._mergeConfig(), os.path.join(self.tmpdir, component), self.debug, self.dryrun)
        provider.deploy()


    def _getImageURI(self, image):
        config = self._mergeConfig()
        
        if config and GLOBAL_CONF in config and "registry" in config[GLOBAL_CONF]:
            print("Adding registry %s for %s" % (config[GLOBAL_CONF]["registry"], image))
            image = os.path.join(config[GLOBAL_CONF]["registry"], image)
        
        return image

    def _pullApp(self, image):
        image = self._getImageURI(image)

        pull = ["docker", "pull", image]
        if subprocess.call(pull) != 0:
            print("Couldn't pull %s" % image)
            sys.exit(1)
            

    def _copyFromContainer(self, image):
        image = self._getImageURI(image)
        name = self._getComponentName(image)
        
        create = ["docker", "create", "--name", name, image, "nop"]
        subprocess.call(create)
        cp = ["docker", "cp", "%s:/%s" % (name, APP_ENT_PATH), self.tmpdir]
        if not subprocess.call(cp):
            logger.debug("Application entity data copied to %s" % self.tmpdir)


        rm = ["docker", "rm", name]
        subprocess.call(rm)

    def _populateMainApp(self, src = None, dst = None):
        print("Copying app %s" % self._getComponentName(self.app))
        if not src:
            src = os.path.join(self.tmpdir, APP_ENT_PATH)
            
        if not dst:
            dst = self.target_path
        distutils.dir_util.copy_tree(src, dst, update=(not self.update))
    
    def _populateModule(self):

        data_list = [
                "graph/%s/" % self.app_id,
                "Atomicfile",
                "params.conf"
                ]
        
        logger.info("Populating module %s" % self._getComponentName(self.app))
        for item in data_list:
            path = os.path.join(self.tmpdir, APP_ENT_PATH, item)
            if os.path.isdir(path):
                logger.debug("%s/%s/%s" % (self.target_path, GRAPH_DIR, self.app_id))
                distutils.dir_util.copy_tree(path, self._getComponentDir(self.app_id))
            else:
                logger.debug("copy item %s > %s > %s > %s" % (self.target_path, GRAPH_DIR, self.app_id, item))
                distutils.file_util.copy_file(path, os.path.join(self._getComponentDir(self.app_id), item))

    def run(self, level = AtomicappLevel.Main):
        if not self.installed:
            self.install(level)

        if not self._loadAtomicfile(os.path.join(self.target_path, ATOMIC_FILE)):
            print("Failed to load %s" % ATOMIC_FILE)
            return

        if self.debug:
            print(self.atomicfile_data)

        if not self._loadParams(os.path.join(self.target_path, PARAMS_FILE)):
            print("Failed to load %s" % PARAMS_FILE)
            return

        config = self._mergeConfig()
        if "provider" in config[GLOBAL_CONF]:
            self.provider = config[GLOBAL_CONF]["provider"]

        if self.debug:
            print(self.params_data)

        self._dispatchGraph()

    def install(self, level = AtomicappLevel.Main):

        if not self._loadAnswers(self.answers_file):
            print("No %s file found, using defaults" % ANSWERS_FILE)

        if self.app_path and not self.target_path == self.app_path:
            logger.info("Copying content of directory %s to %s" % (self.app_path, self.target_path))
            self._populateMainApp(src=self.app_path)

        atomicfile_path = os.path.join(self.target_path, ATOMIC_FILE)
        
        if level == AtomicappLevel.Module:
            atomicfile_path = os.path.join(self._getComponentDir(self.app), ATOMIC_FILE)
        
        logger.debug("Test: %s -> %s" % (self.app, ( not self.app_path and not os.path.exists(self._getComponentDir(self.app)))))
        if not self.app_path and (self.update or not os.path.exists(self._getComponentDir(self.app))):
            self._pullApp(self.app)
            self._copyFromContainer(self.app)
            atomicfile_path = os.path.join(self._getTmpAppDir(), ATOMIC_FILE)
            logger.debug("Atomicfile path for pulled image: %s" % atomicfile_path)
            self._loadAtomicfile(atomicfile_path)
            logger.debug("App ID: %s" % self.app_id)
       
            if level == AtomicappLevel.Main:
                self._populateMainApp()
            elif level == AtomicappLevel.Module:
                self._populateModule()
        else:
            logger.info("Component data exist in %s, skipping population..." % self._getComponentDir(self.app))
       
        if not self.atomicfile_data:
            self._loadAtomicfile(atomicfile_path)

        if self.recursive:
            self._installDependencies()

        self.installed = True
        return self.app_id

    def _installDependencies(self):
        for graph_item in self.atomicfile_data["graph"]:
            component = self._getComponentName(graph_item)
            component_path = self._getComponentDir(component)
            logger.debug("Component path: %s" % component_path)
            logger.debug("%s == %s -> %s" % (component, self.app_id, component == self.app_id))
            if not component == self.app_id and not os.path.isdir(component_path) and (not self.app_path or self.update):

                image_name = self._getComponentImageName(graph_item)
                print("Pulling %s" % image_name)
                component_atomicapp = Atomicapp(self.answers_file, image_name, self.recursive, self.update, self.target_path, self.dryrun, self.debug)
                component = component_atomicapp.install(AtomicappLevel.Module)
                component_path = self._getComponentDir(component)
                logger.info("Component installed into %s" % component_path)


if __name__ == "__main__":
    parser = ArgumentParser(description='Run an application defined by Atomicfile', formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--debug", dest="debug", default=False, action="store_true", help="Debug output mode")
    parser.add_argument("--dry-run", dest="dryrun", default=False, action="store_true", help="Don't actually call provider but download the metadata files, including the README and answerfile.txt. The commands that will run will be sent to stdout but not run.")
    parser.add_argument("-a", "--answers", dest="answers", default=os.path.join(os.getcwd(), ANSWERS_FILE), help="Path to %s" % ANSWERS_FILE)
    parser.add_argument("APP", help="Application to run. This is a container image that has the metadata describing the whole application.")

    args = parser.parse_args()

    ae = Atomicapp(args.answers, args.app, True, False, None, args.dryrun, args.debug)
    ae.run()

    sys.exit(0)
