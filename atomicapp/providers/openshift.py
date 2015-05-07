from atomicapp.plugin import Provider

from collections import OrderedDict

import os, subprocess
import anymarkup
import logging

logger = logging.getLogger(__name__)

class OpenshiftProvider(Provider):
    key = "openshift"

    config = None
    path = None
    artifacts = None
    dryrun = None

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
            logger.debug("Do something about %s" % artifact_path)

        logger.info("Files %s merged into imaginary template file and pushed to Openshift..." % ", ".join(self.artifacts))
