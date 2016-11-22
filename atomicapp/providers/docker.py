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
import re
import logging
from atomicapp.constants import (DEFAULT_CONTAINER_NAME,
                                 DEFAULT_NAMESPACE,
                                 LOGGER_DEFAULT)
from atomicapp.plugin import Provider, ProviderFailedException
from atomicapp.providers.lib.shipy.dpyexec import Shipy
from atomicapp.utils import Utils

logger = logging.getLogger(LOGGER_DEFAULT)


class DockerProvider(Provider):
    key = "docker"

    def init(self):
        self.namespace = DEFAULT_NAMESPACE
        self.default_name = DEFAULT_CONTAINER_NAME

        self.shipy_exec = Shipy()

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

            version = self.shipy(cmd_check)

            compatibility = {
                '1.21': ('1.6.0', '1.7.0', '1.7.1', '1.7.2'),
                '1.22': ('1.8.0', '1.8.1'),
                '1.23': ('1.8.0', '1.8.1')
            }

            if version.dpy not in compatibility[version.sapi]:
                raise Exception('docker-py version {}, using API version {} '
                                'is not compatible with docker server using '
                                'API version {}.\n'
                                'Please install docker-py version one of '
                                'the following {}'.format(
                                    version.dpy,
                                    version.capi,
                                    version.sapi,
                                    compatibility[version.sapi]))

    def shipy(self, cmd):
        return self.shipy_exec.shipy(cmd[1:], external_logger=logger)

    def _get_containers(self):
        docker_cmd = 'docker ps -a'
        if self.dryrun:
            logger.info("DRY-RUN: %s", docker_cmd)
            return []
        else:
            containers = []

            output = self.shipy(docker_cmd.split())
            for container in output:
                containers.append(container['Names'][0].split('/')[1])

            return containers

    def run(self):
        logger.info("Deploying to provider: Docker")
        for container in self._get_containers():
            if re.match("%s_+%s+_+[a-zA-Z0-9]{12}" % (self.namespace, self.image), container):
                raise ProviderFailedException(
                    "Container with name %s-%s already deployed in Docker" % (self.namespace, self.image))

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
                logger.warning("WARNING: Using --name provided within artifact file.")
            else:
                run_args.insert(run_args.index('run') + 1,
                                "--name=%s_%s_%s" % (self.namespace, self.image, Utils.getUniqueUUID()))

            cmd = run_args
            if self.dryrun:
                logger.info("DRY-RUN: %s", " ".join(cmd))
            else:
                self.shipy(cmd)

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
                    self.shipy(cmd)
