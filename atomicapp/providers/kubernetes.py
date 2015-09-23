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
from subprocess import Popen, PIPE

from atomicapp.constants import HOST_DIR
from atomicapp.plugin import Provider, ProviderFailedException
from atomicapp.utils import printErrorStatus, Utils
from atomicapp.display import Display

display = Display()


class KubernetesProvider(Provider):

    """Operations for Kubernetes provider is implemented in this class.
    This class implements deploy, stop and undeploy of an atomicapp on
    Kubernetes provider.
    """
    key = "kubernetes"
    config_file = None
    kubectl = None

    def init(self):
        self.namespace = "default"

        self.k8s_manifests = []

        display.debug("Given config: %s" % self.config)
        if self.config.get("namespace"):
            self.namespace = self.config.get("namespace")

        display.info("Using namespace %s" % self.namespace)
        if self.container:
            self.kubectl = self._find_kubectl(Utils.getRoot())
            kube_conf_path = "/etc/kubernetes"
            if not os.path.exists(kube_conf_path):
                if self.dryrun:
                    display.info("DRY-RUN: link %s from %s%s" % (kube_conf_path, HOST_DIR, kube_conf_path))
                else:
                    os.symlink(os.path.join(Utils.getRoot(), kube_conf_path.lstrip("/")), kube_conf_path)
        else:
            self.kubectl = self._find_kubectl()

        if not self.dryrun:
            if not os.access(self.kubectl, os.X_OK):
                raise ProviderFailedException("Command: " + self.kubectl + " not found")

            # Check if Kubernetes config file is accessible
            self.checkConfigFile()

    def _find_kubectl(self, prefix=""):
        """Determine the path to the kubectl program on the host.
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
            display.info("caller gave provider_cli: " + self.config.get("provider_cli"))
            test_paths.insert(0, self.config.get("provider_cli"))

        for path in test_paths:
            test_path = prefix + path
            display.info("trying kubectl at " + test_path)
            kubectl = test_path
            if os.access(kubectl, os.X_OK):
                display.info("found kubectl at " + test_path)
                return kubectl

        raise ProviderFailedException("No kubectl found in %s" % ":".join(test_paths))

    def generateConfigFile(self):
        """Generates configuration file for Kubernetes by calling
        kubectl config view and saving the output
        """

        cmd = [self.kubectl, "config", "view"]

        content = self._call(cmd)
        config_dir = os.path.dirname(self.config_file)
        if config_dir and not os.path.isdir(config_dir):
            os.makedirs(config_dir)

        with open(self.config_file, "w") as fp:
            fp.write(content)

    def _call(self, cmd):
        """Calls given command

        :arg cmd: Command to be called in a form of list
        :raises: Exception
        """

        if self.dryrun:
            display.info("DRY-RUN: %s" % " ".join(cmd))
        else:
            try:
                p = Popen(cmd, stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
                display.debug("stdout = %s" % stdout)
                display.debug("stderr = %s" % stderr)
                if stderr and stderr.strip() != "":
                    raise Exception(str(stderr))

                return stdout
            except Exception:
                printErrorStatus("cmd failed: " + " ".join(cmd))
                raise

    def process_k8s_artifacts(self):
        """Processes Kubernetes manifests files and checks if manifest under
        process is valid.
        """
        for artifact in self.artifacts:
            data = None
            with open(os.path.join(self.path, artifact), "r") as fp:
                display.debug(os.path.join(self.path, artifact))
                try:
                    data = anymarkup.parse(fp)
                except Exception:
                    msg = "Error processing %s artifcats, Error:" % os.path.join(
                        self.path, artifact)
                    printErrorStatus(msg)
                    raise
            if "kind" in data:
                self.k8s_manifests.append((data["kind"].lower(), artifact))
            else:
                apath = os.path.join(self.path, artifact)
                raise ProviderFailedException("Malformed kube file: %s" % apath)

    def _resource_identity(self, path):
        """Finds the Kubernetes resource name / identity from resource manifest
        and raises if manifest is not supported.

        :arg path: Absolute path to Kubernetes resource manifest

        :return: str -- Resource name / identity

        :raises: ProviderFailedException
        """
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

    def _scale_replicas(self, path, replicas=0):
        """Scales replicationController to specified replicas size

        :arg path: Path to replicationController manifest
        :arg replicas: Replica size to scale to.
        """
        rname = self._resource_identity(path)
        cmd = [self.kubectl, "--kubeconfig=%s" % self.config_file, "scale", "rc", rname,
               "--replicas=%s" % str(replicas),
               "--namespace=%s" % self.namespace]

        self._call(cmd)

    def deploy(self):
        """Deploys the app by given resource manifests.
        """
        display.info("Deploying to Kubernetes")
        self.process_k8s_artifacts()

        for kind, artifact in self.k8s_manifests:
            if not artifact:
                continue

            k8s_file = os.path.join(self.path, artifact)

            cmd = [self.kubectl, "--kubeconfig=%s" % self.config_file, "create", "-f", k8s_file, "--namespace=%s" % self.namespace]
            self._call(cmd)

    def undeploy(self):
        """Undeploys the app by given resource manifests.
        Undeploy operation first scale down the replicas to 0 and then deletes
        the resource from cluster.
        """
        display.info("Undeploying from Kubernetes")
        self.process_k8s_artifacts()

        for kind, artifact in self.k8s_manifests:
            if not artifact:
                continue

            path = os.path.join(self.path, artifact)

            if kind in ["ReplicationController", "rc", "replicationcontroller"]:
                self._scale_replicas(path, replicas=0)

            cmd = [self.kubectl, "--kubeconfig=%s" % self.config_file, "delete", "-f", path, "--namespace=%s" % self.namespace]
            self._call(cmd)
