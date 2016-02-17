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
import logging
import os
from string import Template

from atomicapp.plugin import Provider, ProviderFailedException
from atomicapp.utils import Utils
from atomicapp.display import Display

logger = logging.getLogger(__name__)


class KubernetesProvider(Provider):

    """Operations for Kubernetes provider is implemented in this class.
    This class implements deploy, stop and undeploy of an atomicapp on
    Kubernetes provider.
    """
    key = "kubernetes"
    config_file = None
    kubectl = None

    def init(self):
        self.display = Display()
        self.namespace = "default"

        self.k8s_manifests = []

        logger.debug("Given config: %s", self.config)
        if self.config.get("namespace"):
            self.namespace = self.config.get("namespace")

        logger.info("Using namespace %s", self.namespace)
        if self.container:
            self.kubectl = self._find_kubectl(Utils.getRoot())
            kube_conf_path = "/etc/kubernetes"
            host_kube_conf_path = os.path.join(Utils.getRoot(), kube_conf_path.lstrip("/"))
            if not os.path.exists(kube_conf_path) and os.path.exists(host_kube_conf_path):
                if self.dryrun:
                    logger.info("DRY-RUN: link %s from %s" % (kube_conf_path, host_kube_conf_path))
                else:
                    os.symlink(host_kube_conf_path, kube_conf_path)
        else:
            self.kubectl = self._find_kubectl()

        if not self.dryrun:
            if not os.access(self.kubectl, os.X_OK):
                raise ProviderFailedException("Command: " + self.kubectl + " not found")

            # Check if Kubernetes config file is accessible, but only
            # if one was provided by the user; config file is optional.
            if self.config_file:
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

    def _call(self, cmd):
        """Calls given command

        :arg cmd: Command to be called in a form of list
        :raises: Exception
        """

        if self.dryrun:
            logger.info("DRY-RUN: %s", " ".join(cmd))
        else:
            try:
                ec, stdout, stderr = Utils.run_cmd(cmd, checkexitcode=True)
            except Exception as e:
                self.display.error("cmd failed: %s" % e, "cockpit")  # cockpit logging
                raise
            return stdout

    def process_k8s_artifacts(self):
        """Processes Kubernetes manifests files and checks if manifest under
        process is valid.
        """
        for artifact in self.artifacts:
            data = None
            with open(os.path.join(self.path, artifact), "r") as fp:
                logger.debug(os.path.join(self.path, artifact))
                try:
                    data = anymarkup.parse(fp)
                except Exception:
                    msg = "Error processing %s artifcats, Error:" % os.path.join(
                        self.path, artifact)
                    self.display.error(msg, "cockpit")
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
        cmd = [self.kubectl, "scale", "rc", rname,
               "--replicas=%s" % str(replicas),
               "--namespace=%s" % self.namespace]
        if self.config_file:
            cmd.append("--kubeconfig=%s" % self.config_file)

        self._call(cmd)

    def run(self):
        """Deploys the app by given resource manifests.
        """
        logger.info("Deploying to Kubernetes")
        self.process_k8s_artifacts()

        for kind, artifact in self.k8s_manifests:
            if not artifact:
                continue

            k8s_file = os.path.join(self.path, artifact)

            cmd = [self.kubectl, "create", "-f", k8s_file, "--namespace=%s" % self.namespace]
            if self.config_file:
                cmd.append("--kubeconfig=%s" % self.config_file)
            self._call(cmd)

    def stop(self):
        """Undeploys the app by given resource manifests.
        Undeploy operation first scale down the replicas to 0 and then deletes
        the resource from cluster.
        """
        logger.info("Undeploying from Kubernetes")
        self.process_k8s_artifacts()

        for kind, artifact in self.k8s_manifests:
            if not artifact:
                continue

            path = os.path.join(self.path, artifact)

            if kind in ["ReplicationController", "rc", "replicationcontroller"]:
                self._scale_replicas(path, replicas=0)

            cmd = [self.kubectl, "delete", "-f", path, "--namespace=%s" % self.namespace]
            if self.config_file:
                cmd.append("--kubeconfig=%s" % self.config_file)
            self._call(cmd)

    def persistent_storage(self, graph, action):
        """
        Actions are either: run, stop or uninstall as per the Requirements class
        Curently run is the only function implemented for k8s persistent storage
        """

        logger.debug("Persistent storage enabled! Running action: %s" % action)

        if action not in ['run']:
            logger.warning(
                "%s action is not available for provider %s. Doing nothing." %
                (action, self.key))
            return

        self._check_persistent_volumes()

        # Get the path of the persistent storage yaml file includes in /external
        # Plug the information from the graph into the persistent storage file
        base_path = os.path.dirname(os.path.realpath(__file__))
        template_path = os.path.join(base_path,
                                     'external/kubernetes/persistent_storage.yaml')
        with open(template_path, 'r') as f:
            content = f.read()
        template = Template(content)
        rendered_template = template.safe_substitute(graph)

        tmp_file = Utils.getTmpFile(rendered_template, '.yaml')

        # Pass the .yaml file and execute
        if action is "run":
            cmd = [self.kubectl, "create", "-f", tmp_file, "--namespace=%s" % self.namespace]
            if self.config_file:
                cmd.append("--kubeconfig=%s" % self.config_file)
            self._call(cmd)
            os.unlink(tmp_file)

    def _check_persistent_volumes(self):
            cmd = [self.kubectl, "get", "pv"]
            if self.config_file:
                cmd.append("--kubeconfig=%s" % self.config_file)
            lines = self._call(cmd)

            # If there are no persistent volumes to claim, warn the user
            if not self.dryrun and len(lines.split("\n")) == 2:
                logger.warning("No persistent volumes detected in Kubernetes. Volume claim will not "
                               "initialize unless persistent volumes exist.")
