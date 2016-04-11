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
import uuid
import logging

from atomicapp.constants import (APP_ENT_PATH,
                                 LOGGER_COCKPIT,
                                 LOGGER_DEFAULT,
                                 MAIN_FILE)
from atomicapp.utils import Utils
from atomicapp.nulecule.exceptions import NuleculeException, DockerException

cockpit_logger = logging.getLogger(LOGGER_COCKPIT)
logger = logging.getLogger(LOGGER_DEFAULT)


class DockerHandler(object):

    """Interface to interact with Docker."""

    def __init__(self, dryrun=False, docker_cli='/usr/bin/docker'):
        self.dryrun = dryrun
        self.docker_cli = docker_cli

        # Check to make sure the docker client in the container and
        # the server on the host can communicate.
        if not dryrun:
            try:
                subprocess.check_output([docker_cli, 'version'],
                                        stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                if "client and server don't have same version" in e.output \
                        or "client is newer than server" in e.output:
                    raise DockerException("\nThe docker version in this "
                                          "Atomic App differs greatly from "
                                          "the host version.\nPlease use a "
                                          "different Atomic App version for "
                                          "this host.\n")
                elif "Is your docker daemon up and running" in e.output or \
                     "Are you trying to connect to a TLS-enabled daemon " \
                     "without TLS" in e.output:
                    raise DockerException("Could not connect to the "
                                          "docker daemon.")
                else:
                    raise DockerException(e.output)

    def pull(self, image, update=False):
        """
        Pulls a Docker image if not already present in the host.

        Args:
            image (str): Container image name
            update (bool): Always pull image if True even if image already
                    exists on host

        Returns:
            None
        """
        if not self.is_image_present(image) or update:
            logger.info('Pulling Docker image: %s' % image)
            cockpit_logger.info('Pulling Docker image: %s' % image)
            pull_cmd = [self.docker_cli, 'pull', image]
            logger.debug(' '.join(pull_cmd))
        else:
            logger.info('Skipping pulling Docker image: %s' % image)
            return

        if self.dryrun:
            logger.info("DRY-RUN: %s", pull_cmd)
        elif subprocess.call(pull_cmd) != 0:
            raise DockerException("Could not pull Docker image %s" % image)

        cockpit_logger.info('Skipping pulling Docker image: %s' % image)

    def extract(self, image, source, dest, update=False):
        """
        Extracts content from a directory in a Docker image to specified
        destination.

        Args:
            image (str): Docker image name
            source (str): Source directory in Docker image to copy from
            dest (str): Path to destination directory on host
            update (bool): Update destination directory if it exists when
                           True

        Returns:
            None
        """
        logger.info(
            'Extracting nulecule data from image: %s to %s' % (image, dest))
        if self.dryrun:
            return

        # Create dummy container
        run_cmd = [
            self.docker_cli, 'create', '--entrypoint', '/bin/true', image]
        logger.debug('Creating docker container: %s' % ' '.join(run_cmd))
        container_id = subprocess.check_output(run_cmd).strip()

        # Copy files out of dummy container to tmpdir
        tmpdir = '/tmp/nulecule-{}'.format(uuid.uuid1())
        cp_cmd = [self.docker_cli, 'cp',
                  '%s:/%s' % (container_id, source),
                  tmpdir]
        logger.debug(
            'Copying data from Docker container: %s' % ' '.join(cp_cmd))
        subprocess.call(cp_cmd)

        # There has been some inconsistent behavior where docker cp
        # will either copy out the entire dir /APP_ENT_PATH/*files* or
        # it will copy out just /*files* without APP_ENT_PATH. Detect
        # that here and adjust accordingly.
        src = os.path.join(tmpdir, APP_ENT_PATH)
        if not os.path.exists(src):
            src = tmpdir

        # If the application already exists locally then need to
        # make sure the local app id is the same as the one requested
        # on the command line.
        mainfile = os.path.join(dest, MAIN_FILE)
        tmpmainfile = os.path.join(src, MAIN_FILE)
        if os.path.exists(mainfile):
            existing_id = Utils.getAppId(mainfile)
            new_id = Utils.getAppId(tmpmainfile)
            cockpit_logger.info("Loading app_id %s ." % new_id)
            if existing_id != new_id:
                raise NuleculeException(
                    "Existing app (%s) and requested app (%s) differ" %
                    (existing_id, new_id))
            # If app exists and no update requested then move on
            if update:
                logger.info("App exists locally. Performing update...")
            else:
                logger.info("App exists locally and no update requested")
                return

        # Copy files
        logger.debug('Copying nulecule data from %s to %s' % (src, dest))
        Utils.copy_dir(src, dest, update)
        logger.debug('Removing tmp dir: %s' % tmpdir)
        Utils.rm_dir(tmpdir)

        # Clean up dummy container
        rm_cmd = [self.docker_cli, 'rm', '-f', container_id[:12]]
        logger.debug('Removing Docker container: %s' % ' '.join(rm_cmd))
        subprocess.call(rm_cmd)

    def is_image_present(self, image):
        """
        Check if a Docker image is present in the host.

        Args:
            image (str): Docker image name.

        Returns:
            bool: True if docker image is present on host, else False
        """
        # If dryrun then just return True
        if self.dryrun:
            return True

        output = subprocess.check_output([self.docker_cli, 'images'])
        image_lines = output.strip().splitlines()[1:]
        for line in image_lines:
            words = line.split()
            image_name = words[0]
            registry = repo = None
            if '/' in image_name:
                registry, repo = image_name.split('/', 1)
            if image_name == image or repo == image:
                return True
        return False
