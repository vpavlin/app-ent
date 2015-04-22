from yapsy.IPlugin import IPlugin

from collections import OrderedDict

import os, subprocess
import anymarkup
import logging

class OpenshiftProvider(IPlugin):
    config = None
    path = None
    artifacts = None
    dryrun = None
    logger = None
    def init(self, config, artifacts, path, dryrun, logger):
        self.config = config
        self.artifacts = artifacts
        self.path = path
        self.dryrun = dryrun
        self.logger = logger.getChild("openshift")

    def _callK8s(self, path):
        cmd = ["kubectl", "create", "-f", path, "--api-version=v1beta1"]
        print("Calling: %s" % " ".join(cmd))

        if self.dryrun:
            return True
        else:
            if subprocess.call(cmd) == 0:
                return True
        
        return False

    def deploy(self):
        for artifact in self.artifacts:
            artifact_path = os.path.join(self.path, artifact)
            self.logger.debug("Do something about %s" % artifact_path)

        self.logger.info("Files %s merged into imaginary template file and pushed to Openshift..." % ", ".join(self.artifacts))
