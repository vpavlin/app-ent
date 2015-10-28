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

from atomicapp.plugin import Provider, ProviderFailedException
from atomicapp.utils import Utils, find_binary, printErrorStatus

from collections import OrderedDict
import os
import anymarkup
import subprocess
from subprocess import Popen, PIPE
from distutils.spawn import find_executable

import logging

logger = logging.getLogger(__name__)


class OpenShiftProvider(Provider):
    key = "openshift"
    cli_str = "oc"
    cli = None
    config_file = None
    template_data = None

    def init(self):
        self.cli = find_executable(self.cli_str)
        if self.container and not self.cli:
            host_path = []
            for path in os.environ.get("PATH").split(":"):
                host_path.append(os.path.join(Utils.getRoot(), path.lstrip("/")))
            self.cli = find_binary(self.cli_str, path=":".join(host_path))
            if not self.cli:
                # if run as non-root we need a symlink in the container
                os.symlink(os.path.join(Utils.getRoot(), "usr/bin/oc"), "/usr/bin/oc")
                self.cli = "/usr/bin/oc"

        if not self.dryrun:
            if not self.cli or not os.access(self.cli, os.X_OK):
                raise ProviderFailedException("Command %s not found" % self.cli)
            else:
                logger.debug("Using %s to run OpenShift commands.", self.cli)

            # Check if OpenShift config file is accessible
            self.checkConfigFile()

    def _callCli(self, path):
        cmd = [self.cli, "--config=%s" % self.config_file, "create", "-f", path]

        if self.dryrun:
            logger.info("Calling: %s", " ".join(cmd))
        else:
            try:
                p = Popen(cmd, stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
                logger.debug("stdout = %s", stdout)
                logger.debug("stderr = %s", stderr)
                if stderr and stderr.strip() != "":
                    raise Exception(str(stderr))

                return stdout
            except Exception:
                printErrorStatus("cmd failed: " + " ".join(cmd))
                raise

    def _processTemplate(self, path):
        cmd = [self.cli, "--config=%s" % self.config_file, "process", "-f", path]

        name = "config-%s" % os.path.basename(path)
        output_path = os.path.join(self.path, name)
        if self.cli and not self.dryrun:
            output = subprocess.check_output(cmd)
            logger.debug("Writing processed template to %s", output_path)
            with open(output_path, "w") as fp:
                fp.write(output)
        return name

    def loadArtifact(self, path):
        data = super(self.__class__, self).loadArtifact(path)
        self.template_data = anymarkup.parse(data, force_types=None)
        if "kind" in self.template_data and \
                self.template_data["kind"].lower() == "template":
            if "parameters" in self.template_data:
                return anymarkup.serialize(
                    self.template_data["parameters"], format="json")

        return data

    def saveArtifact(self, path, data):
        if self.template_data:
            if "kind" in self.template_data and \
                    self.template_data["kind"].lower() == "template":
                if "parameters" in self.template_data:
                    passed_data = anymarkup.parse(data, force_types=None)
                    self.template_data["parameters"] = passed_data
                    data = anymarkup.serialize(
                        self.template_data,
                        format=os.path.splitext(path)[1].strip("."))  # FIXME

        super(self.__class__, self).saveArtifact(path, data)

    def deploy(self):
        kube_order = OrderedDict(
            [("service", None), ("rc", None), ("pod", None)])  # FIXME
        for artifact in self.artifacts:
            data = None
            artifact_path = os.path.join(self.path, artifact)
            with open(artifact_path, "r") as fp:
                data = anymarkup.parse(fp, force_types=None)
            if "kind" in data:
                if data["kind"].lower() == "template":
                    logger.info("Processing template")
                    artifact = self._processTemplate(artifact_path)
                kube_order[data["kind"].lower()] = artifact
            else:
                raise ProviderFailedException("Malformed artifact file")

        for artifact in kube_order:
            if not kube_order[artifact]:
                continue

            k8s_file = os.path.join(self.path, kube_order[artifact])
            self._callCli(k8s_file)
