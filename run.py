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

ATOMIC_FILE="Atomicfile"
PARAMS_FILE="params.conf"
ANSWERS_FILE="answers.conf"
K8S_DIR="graph"
APP_ENT_PATH="application-entity"


class AppEnt():
    debug = False
    dryrun = False
    atomicfile_data = None
    params_data = None
    answers_data = None
    tmpdir = None
    def __init__(self, answers, app, dryrun = False, debug = False):
        self.debug = debug
        self.dryrun = dryrun

        self.tmpdir = tempfile.mkdtemp(prefix="appent-")
        if self.debug:
            print(self.tmpdir)

        if not os.path.exists(app):
            self._pullApp(app)
            self._populateMainApp()

        if not self._loadAtomicfile(os.path.join(os.getcwd(), ATOMIC_FILE)):
            print("Failed to load %s" % ATOMIC_FILE)
            return

        if self.debug:
            print(self.atomicfile_data)

        if not self._loadParams(os.path.join(os.getcwd(), PARAMS_FILE)):
            print("Failed to load %s" % PARAMS_FILE)
            return
        
        if self.debug:
            print(self.params_data)

        if not self._loadAnswers(answers):
            print("No %s file found, using defaults" % ANSWERS_FILE)


        self._dispatchGraph()


        

    def _loadAtomicfile(self, path = None):
        if not os.path.exists(path):
            return None
        
        with open(path, "r") as fp:
            self.atomicfile_data = json.load(fp)

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

    def _getComponentDir(self, component):
        return os.path.join(os.getcwd(), K8S_DIR, component)

    def _dispatchGraph(self):
        if not "graph" in self.atomicfile_data:
            raise Exception("Graph not specified in %s" % ATOMIC_FILE)
        if not os.path.isdir(os.path.join(os.getcwd(), K8S_DIR)):
            raise Exception("Couldn't find %s directory" % K8S_DIR)

        for component in self.atomicfile_data["graph"]:
            component_path = self._getComponentDir(component)
            if not os.path.isdir(component_path):
                self._pullApp(component)

            component_params = os.path.join(component_path, PARAMS_FILE)
            if os.path.isfile(component_params):
                self._loadParams(component_params)
            self._processComponent(component)

    def _applyTemplate(self, data, component):
        template = Template(data)

        d = {}
        if "general" in self.params_data:
            d = self.params_data["general"]
        if component in self.params_data:
            d.update(self.params_data[component])
        else:
            print("No defaults for %s" % component)
        if self.answers_data and component in self.answers_data:
            d.update(self.answers_data[component])

        return template.substitute(d)

    def _callK8s(self, path):
        cmd = ["kubectl", "create", "-f", path, "--api-version=v1beta1"]
        print("Calling: %s" % " ".join(cmd))

        if self.dryrun:
            return True
        else:
            if subprocess.call(cmd) == 0:
                return True
        
        return False

    def _processComponent(self, component):
        kube_order = ["service", "rc", "pod"] #FIXME
        kube_artifacts = {"service":{}, "rc":{}, "pod":{}}
        path = os.path.join(self._getComponentDir(component))
        for entity in os.listdir(path):
            print(entity)
            data = None
            with open(os.path.join(path, entity), "r") as fp:
                data = json.load(fp)
            if "kind" in data:
                kube_artifacts[data["kind"].lower()] = data
            else:
                print("Malformed kube file")

        for artifact in kube_order:
            filename = "%s-%s.json" % (component, artifact)
            data = self._applyTemplate(json.dumps(kube_artifacts[artifact]), component)
        
            k8s_file = os.path.join(self.tmpdir, filename)
            with open(k8s_file, "w") as fp:
                fp.write(data)

            self._callK8s(k8s_file)

    def _pullApp(self, app):
        pull = ["docker", "pull", app]
        subprocess.call(pull)
        data_list = ["/Atomicfile",
                "/params.conf",
                "/graph/%s/pod.json" % app,
                "/graph/%s/replication_controller.json" % app,
                "/graph/%s/service.json" % app,
                "/graph/%s/params.conf" % app
                ]
    
        name = os.path.basename(app).split(":")[0]
        create = ["docker", "create", "--name", name, app, "nop"]
        subprocess.call(create)
        cp = ["docker", "cp", "%s:/%s" % (name, APP_ENT_PATH), self.tmpdir]
        subprocess.call(cp)

        rm = ["docker", "rm", name]
        subprocess.call(rm)


#        client.remove_container(container, force=True)

    def _populateMainApp(self):
        print("Copying")
        distutils.dir_util.copy_tree(os.path.join(self.tmpdir, APP_ENT_PATH), os.getcwd())





if __name__ == "__main__":
    parser = ArgumentParser(description='Run an application defined by Atomicfile', formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--debug", dest="debug", default=False, action="store_true", help="Debug output mode")
    parser.add_argument("--dry-run", dest="dryrun", default=False, action="store_true", help="Don't actually call provider but download the metadata files, including the README and answerfile.txt. The commands that will run will be sent to stdout but not run.")
    parser.add_argument("-a", "--answers", dest="answers", default=os.path.join(os.getcwd(), ANSWERS_FILE), help="Path to %s" % ANSWERS_FILE)
    parser.add_argument("APP", help="Application to run. This is a container image that has the metadata describing the whole application.")

    args = parser.parse_args()

    ae = AppEnt(args.answers, args.app, args.dryrun, args.debug)

    sys.exit(0)
