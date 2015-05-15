from atomicapp.plugin import Provider

from collections import OrderedDict
import os, anymarkup, subprocess

import logging

logger = logging.getLogger(__name__)

class KubernetesProvider(Provider):
    key = "kubernetes"

    kube_order = OrderedDict([("service", None), ("rc", None), ("pod", None)]) #FIXME
    kubectl = "kubectl"
    def init(self):
        if not self.dryrun and self.container:
            self.kubectl = "/host/usr/bin/kubectl"
            if not os.path.exists("/etc/kubernetes"):
                os.symlink("/host/etc/kubernetes", "/etc/kubernetes")

    def _callK8s(self, path):
        cmd = [self.kubectl, "create", "-f", path]
        logger.info("Calling: %s" % " ".join(cmd))

        if not self.dryrun:
            subprocess.check_call(cmd) == 0

    def prepareOrder(self):
        for artifact in self.artifacts:
            data = None
            with open(os.path.join(self.path, artifact), "r") as fp:
                logger.debug(os.path.join(self.path, artifact))
                data = anymarkup.parse(fp)
            if "kind" in data:
                self.kube_order[data["kind"].lower()] = artifact
            else:
                logger.info("Malformed kube file %s" % artifact)

    def deploy(self):
        self.prepareOrder()

        for artifact in self.kube_order:
            if not self.kube_order[artifact]:
                continue

            k8s_file = os.path.join(self.path, self.kube_order[artifact])
            self._callK8s(k8s_file)

    def _resetReplicas(self, path):
        data = anymarkup.parse_file(path)
        name = data["metadata"]["name"]
        cmd = [self.kubectl, "resize", "rc", name, "--replicas=4" ]
        logger.info("Calling: %s" % " ".join(cmd))
            if not self.dryrun:
                subprocess.check_call(cmd)

    def undeploy(self):
        self.prepareOrder()

        for kind, artifact in self.kube_order.iteritems():
            if not self.kube_order[kind]:
                continue

            path = os.path.join(self.path, artifact)

            if kind in ["ReplicationController", "rc", "replicationcontroller"]:
                self._resetReplicas(path)

            cmd = [self.kubectl, "delete", "-f", path]
            logger.info("Calling: %s" % " ".join(cmd))
            if not self.dryrun:
                subprocess.check_call(cmd)
