from atomicapp.plugin import Provider
import os, subprocess

import logging

logger = logging.getLogger(__name__)

class DockerProvider(Provider):
    key = "docker"

    def init(self):
        
        cmd_check = ["docker", "version"]
        docker_version = subprocess.check_output(cmd_check).split("\n")

        client = ""
        server = ""
        for line in docker_version:
            if line.startswith("Client API version"):
                client = line.split(":")[1]
            if line.startswith("Server API version"):
                server = line.split(":")[1]

        if client > server:
            raise Exception("Docker version in app image (%s) is higher than the one on host (%s). Pleas update your host." % (client, server))

    def deploy(self):
        for artifact in self.artifacts:
            artifact_path = os.path.join(self.path, artifact)
            label_run = None
            with open(artifact_path, "r") as fp:
                label_run = fp.read().strip()

            cmd = label_run.split(" ")

            if self.dryrun:
                logger.info("Pretending to run:\n\t %s" % " ".join(cmd))
            else:
                subprocess.call(cmd)
