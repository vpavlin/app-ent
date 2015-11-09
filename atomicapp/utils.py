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

from __future__ import print_function
import copy
import distutils.dir_util
import os
import sys
import tempfile
import re
import collections
import anymarkup
import uuid
from distutils.spawn import find_executable

import logging
from subprocess import Popen, PIPE
from constants import (ANSWERS_FILE,
                       APP_ENT_PATH,
                       CACHE_DIR,
                       DEFAULT_ANSWERS,
                       EXTERNAL_APP_DIR,
                       HOST_DIR,
                       WORKDIR)

__all__ = ('Utils')

logger = logging.getLogger(__name__)

# Following Methods(printStatus, printErrorStatus)
#  are required for Cockpit or thirdparty management tool integration
#  DONOT change the atomicapp.status.* prefix in the logger method.


def printStatus(message):
    logger.info("atomicapp.status.info.message=" + str(message))


def printErrorStatus(message):
    logger.info("atomicapp.status.error.message=" + str(message))


def find_binary(executable, path=None):
    """Tries to find 'executable' in the directories listed in 'path'.

    A string listing directories separated by 'os.pathsep'; defaults to
    os.environ['PATH'].  Returns the complete filename or None if not found.
    """
    if path is None:
        path = os.environ['PATH']

    paths = path.split(os.pathsep)
    base, ext = os.path.splitext(executable)

    if (sys.platform == 'win32' or os.name == 'os2') and (ext != '.exe'):
        executable = executable + '.exe'

    if not os.path.isfile(executable):
        for p in paths:
            f = os.path.join(p, executable)
            if os.path.isfile(f) or os.path.islink(f):
                return f
        return None
    else:
        return executable


class Utils(object):

    __tmpdir = None
    __workdir = None
    target_path = None

    @property
    def workdir(self):
        if not self.__workdir:
            self.__workdir = os.path.join(self.target_path, WORKDIR)
            logger.debug("Using working directory %s", self.__workdir)
            if not os.path.isdir(self.__workdir):
                os.mkdir(self.__workdir)

        return self.__workdir

    @property
    def tmpdir(self):
        if not self.__tmpdir:
            self.__tmpdir = tempfile.mkdtemp(prefix="nulecule-")
            logger.info("Using temporary directory %s", self.__tmpdir)

        return self.__tmpdir

    def __init__(self, target_path, workdir=None):
        self.target_path = target_path
        if workdir:
            self.__workdir = workdir

    @staticmethod
    def isTrue(val):
        true_values = ('true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'sure')
        return str(val).lower() in true_values

    @staticmethod
    def sanitizeName(app):
        return app.replace("/", "-")

    @staticmethod
    def getNewAppCacheDir(image):
        """
        Get a new unique dir under CACHE_DIR based on the image name

        Args:
            image (str): The name of the image the app is in

        Returns:
            path (str): The path to the unique directory
        """
        path = os.path.join(
            Utils.getRoot(),
            CACHE_DIR.lstrip('/'),  # Rip leading '/' off
            "%s-%s" % (Utils.sanitizeName(image), Utils.getUniqueUUID()))
        return path

    def getExternalAppDir(self, component):
        return os.path.join(
            self.target_path, EXTERNAL_APP_DIR, self.getComponentName(component))

    def getTmpAppDir(self):
        return os.path.join(self.tmpdir, APP_ENT_PATH)

    @staticmethod
    def getComponentName(graph_item):
        # logger.debug("Getting name for %s", graph_item)
        if type(graph_item) is str or type(graph_item) is unicode:
            return os.path.basename(graph_item).split(":")[0]
        elif type(graph_item) is dict:
            return graph_item["name"].split(":")[0]
        else:
            raise ValueError

    @staticmethod
    def getComponentImageName(graph_item):
        if type(graph_item) is str or type(graph_item) is unicode:
            return graph_item
        elif type(graph_item) is dict:
            repo = ""
            if "repository" in graph_item:
                repo = graph_item["repository"]

            return os.path.join(repo, graph_item["name"])
        else:
            return None

    @staticmethod
    def isExternal(graph_item):
        logger.debug(graph_item)
        if "artifacts" in graph_item:
            return False

        if "source" not in graph_item:
            return False

        return True

    @staticmethod
    def getSourceImage(graph_item):
        if "source" not in graph_item:
            return None

        if graph_item["source"].startswith("docker://"):
            return graph_item["source"][len("docker://"):]

        return None

    @staticmethod
    def sanitizePath(path):
        if path.startswith("file://"):
            return path[7:]

    @staticmethod
    def run_cmd(cmd, args_str=None):
        """
        Runs a command with its arguments.

        Args:
            args_str (str): arguments to the command.

        Returns:
            string response output.
            Might throw an Exception if stderr exists.
        """
        try:
            p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate(args_str)
            logger.debug("stdout = %s", stdout)
            logger.debug("stderr = %s", stderr)
            """
            stderr can be None.
            We need to raise an exception for the stderr value
            if the response is from Kubernetes or Openshift.
            """
            if stderr and stderr.strip() != "":
                raise Exception(str(stderr))

            return stdout
        except Exception:
            printErrorStatus("cmd failed: " + " ".join(cmd))
            raise

    @staticmethod
    def askFor(what, info):
        repeat = True
        desc = info["description"]
        constraints = None
        if "constraints" in info:
            constraints = info["constraints"]
        while repeat:
            repeat = False
            if "default" in info:
                value = raw_input(
                    "%s (%s, default: %s): " % (what, desc, info["default"]))
                if len(value) == 0:
                    value = info["default"]
            else:
                try:
                    value = raw_input("%s (%s): " % (what, desc))
                except EOFError:
                    raise

            if constraints:
                for constraint in constraints:
                    logger.info("Checking pattern: %s", constraint["allowed_pattern"])
                    if not re.match("^%s$" % constraint["allowed_pattern"], value):
                        logger.error(constraint["description"])
                        repeat = True

        return value

    @staticmethod
    def update(old_dict, new_dict):
        for key, val in new_dict.iteritems():
            if isinstance(val, collections.Mapping):
                tmp = Utils.update(old_dict.get(key, {}), val)
                old_dict[key] = tmp
            elif isinstance(val, list) and key in old_dict:
                res = (old_dict[key] + val)
                if isinstance(val[0], collections.Mapping):
                    old_dict[key] = [dict(y) for y in set(tuple(x.items()) for x in res)]
                else:
                    old_dict[key] = list(set(res))
            else:
                old_dict[key] = new_dict[key]
        return old_dict

    @staticmethod
    def getAppId(path):
        # obsolete
        if not os.path.isfile(path):
            return None

        data = anymarkup.parse_file(path)
        return data.get("id")

    @staticmethod
    def getDockerCli(dryrun=False):
        cli = find_executable("docker")
        if not cli:
            if dryrun:
                logger.error("Could not find docker client")
            else:
                raise Exception("Could not find docker client")

        return cli

    @staticmethod
    def inContainer():
        """
        Determine if we are running inside a container or not.

        Returns:
            (bool): True == we are in a container
        """
        if os.path.isdir(HOST_DIR):
            return True
        else:
            return False

    @staticmethod
    def getRoot():
        if Utils.inContainer():
            return HOST_DIR
        else:
            return "/"

    # generates a unique 12 character UUID
    @staticmethod
    def getUniqueUUID():
        data = str(uuid.uuid4().get_hex().lower()[0:12])
        return data

    @staticmethod
    def loadAnswers(data=None):
        answers_data = {}
        write_sample_answers = False
        if not data:
            logger.info("No answers data given")

        if type(data) == dict:
            logger.debug("Data given %s", data)
        elif os.path.exists(data):
            logger.debug("Path to answers file given, loading %s", data)
            if os.path.isdir(data):
                if os.path.isfile(os.path.join(data, ANSWERS_FILE)):
                    data = os.path.join(data, ANSWERS_FILE)
                else:
                    write_sample_answers = True

            if os.path.isfile(data):
                data = anymarkup.parse_file(data)
        else:
            write_sample_answers = True

        if write_sample_answers:
            data = copy.deepcopy(DEFAULT_ANSWERS)

        if answers_data:
            answers_data = Utils.update(answers_data, data)
        else:
            answers_data = data

        return answers_data

    @staticmethod
    def copy_dir(src, dest, update=False, dryrun=False):
        if not dryrun:
            distutils.dir_util.copy_tree(src, dest, update)
