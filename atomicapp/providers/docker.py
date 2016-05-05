"""
 Copyright 2014-2016 Red Hat, Inc.

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

import os
import subprocess
import re
import logging
from atomicapp.constants import (DEFAULT_CONTAINER_NAME,
                                 DEFAULT_NAMESPACE,
                                 LOGGER_DEFAULT)
from atomicapp.plugin import Provider, ProviderFailedException
from atomicapp.utils import Utils

logger = logging.getLogger(LOGGER_DEFAULT)


class DockerProvider(Provider):
    key = "docker"

    def init(self):
        self.namespace = DEFAULT_NAMESPACE
        self.default_name = DEFAULT_CONTAINER_NAME

        logger.debug("Given config: %s", self.config)
        if self.config.get("namespace"):
            self.namespace = self.config.get("namespace")
        logger.debug("Namespace: %s", self.namespace)

        if "image" in self.config:
            self.image = Utils.sanitizeName(self.config.get("image"))
        else:
            self.image = Utils.getUniqueUUID()
            logger.warning("The artifact name has not been provided within Nulecule, using a UUID instead")
            logger.debug("No image name found for artifact, using UUID %s in container name" % self.image)

        if self.dryrun:
            logger.info("DRY-RUN: Did not check Docker version compatibility")
        else:
            cmd_check = ["docker", "version"]
            try:
                docker_version = subprocess.check_output(cmd_check).split("\n")
            except Exception as ex:
                raise ProviderFailedException(ex)

            client = ""
            server = ""
            for line in docker_version:
                if line.startswith("Client API version"):
                    client = line.split(":")[1]
                if line.startswith("Server API version"):
                    server = line.split(":")[1]

            if client > server:
                msg = ("Docker version in app image (%s) is higher than the one "
                       "on host (%s). Please update your host." % (client, server))
                raise ProviderFailedException(msg)

    def _get_containers(self):
        docker_cmd = 'docker ps -a --format="{{ .Names }}"'
        if self.dryrun:
            logger.info("DRY-RUN: %s", docker_cmd)
            return []
        else:
            return dict((line, 1) for line in subprocess.check_output(docker_cmd, shell=True).splitlines())

    def run(self):
        logger.info("Deploying to provider: Docker")
        for container in self._get_containers():
            if re.match("%s_+%s+_+[a-zA-Z0-9]{12}" % (self.namespace, self.image), container):
                raise ProviderFailedException("Container with name %s-%s already deployed in Docker" % (self.namespace, self.image))

        for artifact in self.artifacts:
            artifact_path = os.path.join(self.path, artifact)
            label_run = None
            with open(artifact_path, "r") as fp:
                label_run = fp.read().strip()
                # if docker-run provided as multiline command
                label_run = ' '.join(label_run.split('\\\n'))
            run_args = label_run.split()

            # If --name is provided, do not re-name due to potential linking of containers. Warn user instead.
            # Else use namespace provided within answers.conf
            if '--name' in run_args:
                logger.info("WARNING: Using --name provided within artifact file.")
            else:
                run_args.insert(run_args.index('run') + 1, "--name=%s_%s_%s" % (self.namespace, self.image, Utils.getUniqueUUID()))

            cmd = run_args
            if self.dryrun:
                logger.info("DRY-RUN: %s", " ".join(cmd))
            else:
                subprocess.check_call(cmd)

    def stop(self):
        logger.info("Undeploying to provider: Docker")
        artifact_names = list()

        # Gather the list of containers within /artifacts/docker
        for artifact in self.artifacts:
            artifact_path = os.path.join(self.path, artifact)
            label_run = None
            with open(artifact_path, "r") as fp:
                label_run = fp.read().strip()

            # If user specified a name of the container via --name=NAME then
            # then remove the equals sign since it breaks our later processing
            label_run = label_run.replace('--name=', '--name ')

            # Convert to list for processing
            run_args = label_run.split()

            # If any artifacts are labelled by name, add it to a container dict list
            if '--name' in run_args:
                artifact_names.append(run_args[run_args.index('--name') + 1])
                logger.debug("artifact cnames: %s", artifact_names)

        # Regex checks for matching container name and kills it. ex. atomic_mariadb-atomicapp-app_9dfb369ed2a0
        for container in self._get_containers():
            if artifact_names:
                m = [i for i, x in enumerate(artifact_names) if x == container]
            else:
                m = re.match("%s_+%s+_+[a-zA-Z0-9]{12}" % (self.namespace, self.image), container)
            if m:
                logger.info("Stopping container: %s", container)
                cmd = ["docker", "stop", container]
                if self.dryrun:
                    logger.info("DRY-RUN: STOPPING CONTAINER %s", " ".join(cmd))
                else:
                    try:
                        subprocess.check_call(cmd)
                    except Exception as e:
                        if not self.ignore_errors:
                            raise e
