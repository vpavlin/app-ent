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

import anymarkup
import os
import subprocess
from atomicapp.plugin import Provider
from atomicapp.utils import printErrorStatus

import logging

logger = logging.getLogger(__name__)


class DockerComposeProvider(Provider):
    key = "docker-compose"

    def init(self):
        pass

    def deploy(self):
        for artifact in self.artifacts:
            artifact_path = os.path.join(self.path, artifact)

            if self._is_artifact_empty(artifact_path):
                continue

            cmd = "docker-compose -f {} up -d".format(artifact_path)

            if self.dryrun:
                logger.info("DRY-RUN: %s" % cmd)
            else:
                subprocess.check_call(cmd.split(" "))

    def undeploy(self):
        for artifact in self.artifacts:
            artifact_path = os.path.join(self.path, artifact)

            if self._is_artifact_empty(artifact_path):
                continue

            cmd = "docker-compose -f {} stop".format(artifact_path)

            if self.dryrun:
                logger.info("DRY-RUN: %s" % cmd)
            else:
                subprocess.check_call(cmd.split(" "))

    def _is_artifact_empty(self, artifact_path):
        with open(artifact_path, 'r') as fp:
            try:
                data = anymarkup.parse(fp)
                if not data:
                    logger.info(
                        'Skipping empty compose YAML file: %s' % artifact_path)
                    return True
            except Exception:
                msg = "Error processing %s artifacts, Error: %s" % (
                    artifact_path)
                printErrorStatus(msg)
                raise
