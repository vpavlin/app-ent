from __future__ import print_function
import distutils.dir_util
import os
import sys
import tempfile
import re
import collections
import anymarkup
import uuid
import requests
from distutils.spawn import find_executable

import logging

from subprocess import Popen, PIPE
from constants import (APP_ENT_PATH,
                       CACHE_DIR,
                       EXTERNAL_APP_DIR,
                       HOST_DIR,
                       LOGGER_COCKPIT,
                       LOGGER_DEFAULT,
                       WORKDIR)

__all__ = ('Utils')

cockpit_logger = logging.getLogger(LOGGER_COCKPIT)
logger = logging.getLogger(LOGGER_DEFAULT)


class AtomicAppUtilsException(Exception):
    pass


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
    def running_on_openshift():
        """
        If we can detect the openshift api endpoint from the
        environment and connect to it then we are running in
        openshift.
        """

        # Detect possible openshift api url, if none then not in openshift env
        url = Utils.get_openshift_api_endpoint_from_env()
        if not url:
            return False

        # Validate it as an openshift endpoint (could just be
        # kubernetes). Don't worry about ssl verification for now
        # as the openshift provider will do that.
        try:
            response = requests.get(url, verify=False)
            if response.status_code == 200:
                logger.debug("Detected environment: openshift pod")
                return True
        except:
            return False
        return False

    @staticmethod
    def get_openshift_api_endpoint_from_env():
        """
        The KUBERNETES_SERVICE_HOST env var should only exist
        on an openshift or kubernetes environment. Here we check that
        variable and return the url of the openshift api endpoint that
        will exist if we are in openshift.
        """
        service_host = os.getenv("KUBERNETES_SERVICE_HOST")
        service_port = os.getenv("KUBERNETES_SERVICE_PORT")
        if service_host:
            return "https://%s:%s/oapi" % (service_host, service_port)
        else:
            return False

    @staticmethod
    def isTrue(val):
        true_values = ('true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'sure')
        return str(val).lower() in true_values

    @staticmethod
    def sanitizeName(app):
        return app.replace("/", "-").replace(":", "-")

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

    # Create a temporary file with data in order to use kubectl, openshift, etc.
    # Returns the tmp dir and name of the file
    @staticmethod
    def getTmpFile(data, suffix=''):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        f.write(data)
        f.close()
        return f.name

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
    def run_cmd(cmd, checkexitcode=True, stdin=None):
        """
        Runs a command with its arguments and returns the results. If
        the command gives a bad exit code then a CalledProcessError
        exceptions is raised, just like if check_call() were called.

        Args:
            checkexitcode: Raise exception on bad exit code
            stdin: input string to pass to stdin of the command

        Returns:
            ec:     The exit code from the command
            stdout: stdout from the command
            stderr: stderr from the command
        """
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate(stdin)
        ec = p.returncode
        logger.debug("\n<<< stdout >>>\n%s<<< end >>>\n", stdout)
        logger.debug("\n<<< stderr >>>\n%s<<< end >>>\n", stderr)

        # If the exit code is an error then raise exception unless
        # we were asked not to.
        if checkexitcode:
            if ec != 0:
                cockpit_logger.error("cmd failed: %s" % str(cmd))
                raise AtomicAppUtilsException(
                    "cmd: %s failed: \n%s" % (str(cmd), stderr))

        return ec, stdout, stderr

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
    def loadAnswers(answers_file):
        if not os.path.isfile(answers_file):
            raise AtomicAppUtilsException(
                "Provided answers file does not exist: %s" % answers_file)

        logger.debug("Loading answers from file: %s", answers_file)
        return anymarkup.parse_file(answers_file)

    @staticmethod
    def copy_dir(src, dest, update=False, dryrun=False):
        if not dryrun:
            distutils.dir_util.copy_tree(src, dest, update)

    @staticmethod
    def rm_dir(directory):
        logger.debug('Recursively removing directory: %s' % directory)
        distutils.dir_util.remove_tree(directory)

    @staticmethod
    def make_rest_request(method, url, verify=True, data=None):
        """
        Make HTTP request to url

        Args:
            method (str): http method (post/get/delete)
            url (str): url
            verify (bool/string): wheter to verify ssl certificate or path
                                  to CA_BUNDLE or direcotry with certifactes
                                  of trusted CAs
            data (dict/list): object to be serialised to json and send as http
                              data (when method=post/put/delete)

        Returns:
            tuple (status_code, return_data): status_code - http status code
                                              return_data - deserialised json object

        Raises:
            ProviderFailedException: connect or read timeout when communicating
                                     with api
        """

        status_code = None
        return_data = None

        try:
            if method.lower() == "get":
                res = requests.get(url, verify=verify)
            elif method.lower() == "post":
                res = requests.post(url, json=data, verify=verify)
            elif method.lower() == "put":
                res = requests.put(url, json=data, verify=verify)
            elif method.lower() == "delete":
                res = requests.delete(url, json=data, verify=verify)
            elif method.lower() == "patch":
                headers = {"Content-Type": "application/json-patch+json"}
                res = requests.patch(url, json=data, verify=verify, headers=headers)

            status_code = res.status_code
            return_data = res.json()
        except requests.exceptions.ConnectTimeout:
            msg = "Timeout when connecting to  %s" % url
            logger.error(msg)
            raise AtomicAppUtilsException(msg)
        except requests.exceptions.ReadTimeout:
            msg = "Timeout when reading from %s" % url
            logger.error(msg)
            raise AtomicAppUtilsException(msg)
        except ValueError:
            # invalid json
            return_data = None

        return (status_code, return_data)
