from yapsy.IPlugin import IPlugin

import os, subprocess

class DockerProvider(IPlugin):
    config = None
    path = None
    artifacts = None
    dryrun = None
    logger = None
    def init(self, config, artifacts, path, dryrun, logger):
        self.confif = config
        self.artifacts = artifacts
        self.path = path
        self.dryrun = dryrun
        self.logger = logger.getChild("docker")
        
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
                self.logger.info("Pretending to run:\n\t %s" % " ".join(cmd))
            else:
                subprocess.call(cmd)
