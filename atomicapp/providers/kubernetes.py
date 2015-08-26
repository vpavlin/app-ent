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
from atomicapp.utils import printErrorStatus
from collections import OrderedDict
import os
import anymarkup
import subprocess
from subprocess import Popen, PIPE
import logging

logger = logging.getLogger(__name__)


class KubernetesProvider(Provider):
    key = "kubernetes"

    def init(self):
        self.namespace = "default"

        self.kube_order = OrderedDict(
            [("service", None), ("rc", None), ("pod", None)])  # FIXME

        logger.debug("Given config: %s", self.config)
        if self.config.get("namespace"):
            self.namespace = self.config.get("namespace")

        logger.info("Using namespace %s", self.namespace)
        if self.container:
            self.kubectl = self._findKubectl("/host")
            if not os.path.exists("/etc/kubernetes"):
                if self.dryrun:
                    logger.info("DRY-RUN: link /etc/kubernetes from /host/etc/kubernetes")
                else:
                    os.symlink("/host/etc/kubernetes", "/etc/kubernetes")
        else:
            self.kubectl = self._findKubectl()

        if not self.dryrun:
            if not os.access(self.kubectl, os.X_OK):
                raise ProviderFailedException("Command: " + self.kubectl + " not found")

    def _findKubectl(self, prefix=""):
        """
        Determine the path to the kubectl program on the host.
        1) Check the config for a provider_cli in the general section
           remember to add /host prefix
        2) Search /usr/bin:/usr/local/bin

        Use the first valid value found
        """

        if self.dryrun:
            # Testing env does not have kubectl in it
            return "/usr/bin/kubectl"

        test_paths = ['/usr/bin/kubectl', '/usr/local/bin/kubectl']
        if self.config.get("provider_cli"):
            logger.info("caller gave provider_cli: " + self.config.get("provider_cli"))
            test_paths.insert(0, self.config.get("provider_cli"))

        for path in test_paths:
            test_path = prefix + path
            logger.info("trying kubectl at " + test_path)
            kubectl = test_path
            if os.access(kubectl, os.X_OK):
                logger.info("found kubectl at " + test_path)
                return kubectl

        raise ProviderFailedException("No kubectl found in %s" % ":".join(test_paths))

    def _callK8s(self, path):
        cmd = [self.kubectl, "create", "-f", path, "--namespace=%s" % self.namespace]

        if self.dryrun:
            logger.info("DRY-RUN: %s", " ".join(cmd))
        else:
            try:
                p = Popen(cmd, stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
                logger.debug("stdout = %s", stdout)
                logger.debug("stderr = %s", stderr)
                if stderr and stderr.strip() != "":
                    raise Exception(str(stderr))
            except Exception:
                printErrorStatus("cmd failed: " + " ".join(cmd))
                raise

    def prepareOrder(self):
        for artifact in self.artifacts:
            data = None
            with open(os.path.join(self.path, artifact), "r") as fp:
                logger.debug(os.path.join(self.path, artifact))
                data = anymarkup.parse(fp)
            if "kind" in data:
                self.kube_order[data["kind"].lower()] = artifact
            else:
                raise ProviderFailedException("Malformed kube file")

    def _resourceIdentity(self, path):
        data = anymarkup.parse_file(path)
        if data["apiVersion"] == "v1":
            return data["metadata"]["name"]
        elif data["apiVersion"] in ["v1beta3", "v1beta2", "v1beta1"]:
            msg = ("%s is not supported API version, update Kubernetes "
                   "artifacts to v1 API version. Error in processing "
                   "%s manifest." % (data["apiVersion"], path))
            raise ProviderFailedException(msg)
        else:
            raise ProviderFailedException("Malformed kube file: %s" % path)

    def _resetReplicas(self, path):
        rname = self._resourceIdentity(path)
        cmd = [self.kubectl, "resize", "rc", rname, "--replicas=0", "--namespace=%s" %
               self.namespace]

        if self.dryrun:
            logger.info("DRY-RUN: %s", " ".join(cmd))
        else:
            subprocess.check_call(cmd)

    def deploy(self):
        logger.info("Deploying to Kubernetes")
        self.prepareOrder()

        for artifact in self.kube_order:
            if not self.kube_order[artifact]:
                continue

            k8s_file = os.path.join(self.path, self.kube_order[artifact])
            self._callK8s(k8s_file)

    def undeploy(self):
        logger.info("Undeploying from Kubernetes")
        self.prepareOrder()

        for kind, artifact in self.kube_order.iteritems():
            if not self.kube_order[kind]:
                continue

            path = os.path.join(self.path, artifact)

            if kind in ["ReplicationController", "rc", "replicationcontroller"]:
                self._resetReplicas(path)

            cmd = [self.kubectl, "delete", "-f", path, "--namespace=%s" % self.namespace]
            if self.dryrun:
                logger.info("DRY-RUN: %s", " ".join(cmd))
            else:
                subprocess.check_call(cmd)
