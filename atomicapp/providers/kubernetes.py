from atomicapp.plugin import Provider, ProviderFailedException

from collections import OrderedDict
import os, anymarkup, subprocess

import logging

logger = logging.getLogger(__name__)

class KubernetesProvider(Provider):
    key = "kubernetes"

    kube_order = OrderedDict([("service", None), ("rc", None), ("pod", None)]) #FIXME
    kubectl = "kubectl"

    def init(self):
        if self.container:
            self.kubectl = "/host/usr/bin/kubectl"
            if not os.path.exists("/etc/kubernetes"):
                if self.dryrun:
                    logger.info("DRY-RUN: link /etc/kubernetes from /host/etc/kubernetes")
                else:
                    os.symlink("/host/etc/kubernetes", "/etc/kubernetes")

        if not self.dryrun:
            if not os.access(self.kubectl, os.X_OK):
                raise ProviderFailedException("Command kubectl not found")

    def _callK8s(self, path):
        cmd = [self.kubectl, "create", "-f", path]

        if self.dryrun:
            logger.info("DRY-RUN: %s", " ".join(cmd))
        else:
            subprocess.check_call(cmd)

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

        for artifact in self.kube_order:
            if not self.kube_order[artifact]:
                continue

            k8s_file = os.path.join(self.path, self.kube_order[artifact])
            self._callK8s(k8s_file)

    def _resetReplicas(self, path):
        data = anymarkup.parse_file(path)
        name = data["metadata"]["name"]
        cmd = [self.kubectl, "resize", "rc", name, "--replicas=4" ]
        if not self.dryrun:
            subprocess.check_call(cmd)
        else:
            logger.info("Calling: %s", " ".join(cmd))

    def undeploy(self):
        self.prepareOrder()

        for kind, artifact in self.kube_order.iteritems():
            if not self.kube_order[kind]:
                continue

            path = os.path.join(self.path, artifact)

            if kind in ["ReplicationController", "rc", "replicationcontroller"]:
                self._resetReplicas(path)

            cmd = [self.kubectl, "delete", "-f", path]
            if not self.dryrun:
                subprocess.check_call(cmd)
            else:
                logger.info("DRY-RUN: Calling: %s", " ".join(cmd))
