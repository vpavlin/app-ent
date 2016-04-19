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

import anymarkup
import logging
import os

from atomicapp.constants import (ACCESS_TOKEN_KEY,
                                 ANSWERS_FILE,
                                 DEFAULT_NAMESPACE,
                                 LOGGER_DEFAULT,
                                 NAMESPACE_KEY,
                                 PROVIDER_API_KEY,
                                 PROVIDER_CA_KEY,
                                 LOGGER_COCKPIT)
from atomicapp.plugin import Provider, ProviderFailedException

from pykube.config import KubeConfig
from pykube.http import HTTPClient, HTTPError
from pykube.objects import Pod, ReplicationController, Service, Namespace

cockpit_logger = logging.getLogger(LOGGER_COCKPIT)
logger = logging.getLogger(LOGGER_DEFAULT)


class KubernetesAPI(object):

    def __init__(self, config):
        self.api = HTTPClient(config)

    def namespaces(self):
        return Namespace.objects(self.api).all().response["items"]

    def create(self, kind, artifact):
        if kind in ["pod", "po"]:
            k8s = Pod(self.api, artifact)
        elif kind in ["rc", "replicationcontroller"]:
            k8s = ReplicationController(self.api, artifact)
        elif kind == "service":
            k8s = Service(self.api, artifact)
        else:
            raise ProviderFailedException(
                "No Kubernetes API of that kind: %s" % kind)
        k8s.create()

    def delete(self, kind, artifact):
        kind = artifact['kind']
        if kind in ["pod", "po"]:
            k8s = Pod(self.api, artifact)
        elif kind in ["rc", "replicationcontroller"]:
            k8s = ReplicationController(self.api, artifact)
            k8s.scale(replicas=0)
        elif kind == "service":
            k8s = Service(self.api, artifact)
        else:
            raise ProviderFailedException(
                "No Kubernetes API of that kind: %s" % kind)
        k8s.delete()


class KubernetesProvider(Provider):

    """Operations for Kubernetes provider is implemented in this class.
    This class implements deploy, stop and undeploy of an atomicapp on
    Kubernetes provider.
    """
    key = "kubernetes"
    namespace = DEFAULT_NAMESPACE
    k8s_artifacts = {}
    config_file = None

    # Kubernetes cmd line settings
    providerapi = "https://127.0.0.1:8080"
    access_token = None
    provider_ca = None

    def init(self):
        self.k8s_artifacts = {}

        logger.debug("Given config: %s", self.config)
        if self.config.get("namespace"):
            self.namespace = self.config.get("namespace")

        logger.info("Using namespace %s", self.namespace)

        self._process_artifacts()

        if self.config_file:
            self.api = KubernetesAPI(KubeConfig.from_file(self.config_file))
        else:
            self.api = KubernetesAPI(self._from_env())

        self._check_namespaces()

    def _from_env(self):
        result = {PROVIDER_API_KEY: self.providerapi,
                  ACCESS_TOKEN_KEY: self.access_token,
                  PROVIDER_CA_KEY: self.provider_ca}

        for k in [PROVIDER_API_KEY, ACCESS_TOKEN_KEY, NAMESPACE_KEY]:
            if result[k] is None:
                msg = "Kubernetes API access: You need to set %s in %s" % (k, ANSWERS_FILE)
                logger.error(msg)
                raise ProviderFailedException(msg)

        config = {
            "clusters": [
                {
                    "name": "self",
                    "cluster": {
                        "server": self.providerapi,
                        "certificate-authority": self.provider_ca,
                    },
                },
            ],
            "users": [
                {
                    "name": "self",
                    "user": {
                        "token": self.access_token,
                    },
                },
            ],
            "contexts": [
                {
                    "name": "self",
                    "context": {
                        "cluster": "self",
                        "user": "self",
                    },
                }
            ],
            "current-context": "self",
        }
        return config

    def _check_namespaces(self):
        namespace_list = self.api.namespaces()
        logger.debug("There are currently %s namespaces in the cluster." % str(len(namespace_list)))

        namespaces = []
        for ns in namespace_list:
            namespaces.append(ns["metadata"]["name"])

        if self.namespace not in namespaces:
            logger.error("%s namespace does not exist. Please create the namespace and try again.")

    def _process_artifacts(self):
        """
        Parse each Kubernetes file and convert said format into an Object for
        deployment.
        """
        for artifact in self.artifacts:
            logger.debug("Processing artifact: %s", artifact)
            data = None
            with open(os.path.join(self.path, artifact), "r") as fp:
                data = anymarkup.parse(fp, force_types=None)

            self._process_artifact_data(artifact, data)

    def _process_artifact_data(self, artifact, data):
        """
        Process the data for an artifact

        Args:
            artifact (str): Artifact name
            data (dict): Artifact data
        """

        # Check that the artifact is using the correct API
        self._identify_api(artifact, data)

        # Check if kind exists
        if "kind" not in data.keys():
            raise ProviderFailedException(
                "Error processing %s artifact. There is no kind" % artifact)

        # Change to lower case so it's easier to parse
        kind = data["kind"].lower()

        if kind not in self.k8s_artifacts.keys():
            self.k8s_artifacts[kind] = []

        # Change to the namespace specified on init()
        data['metadata']['namespace'] = self.namespace
        data['metadata']['labels']['namespace'] = self.namespace

        self.k8s_artifacts[kind].append(data)

    def _identify_api(self, artifact, data):
        """
        Make sure that the artifact is using the correct API

        Args:
            artifact (str): Artifact name
            data (dict): Artifact data
        """
        if data["apiVersion"] == "v1":
            pass
        elif data["apiVersion"] in ["v1beta3", "v1beta2", "v1beta1"]:
            msg = ("%s is not a supported API version, update Kubernetes "
                   "artifacts to v1 API version. Error in processing "
                   "%s manifest." % (data["apiVersion"], artifact))
            raise ProviderFailedException(msg)
        else:
            raise ProviderFailedException("Malformed kubernetes artifact: %s" % artifact)

    def run(self):
        """
        Deploys the app by given resource artifacts.
        """
        logger.info("Deploying to Kubernetes")

        for kind, objects in self.k8s_artifacts.iteritems():
            for artifact in objects:
                if self.dryrun:
                    logger.info("DRY-RUN: Deploying k8s KIND: %s, ARTIFACT: %s"
                                % (kind, artifact))
                else:
                    try:
                        self.api.create(kind, artifact)
                    except HTTPError as e:
                        msg = "Failed to deploy Kubernetes artifact kind: %s. " \
                            "Error: %s" % (kind, e)
                        raise ProviderFailedException(msg)

    def stop(self):
        """Undeploys the app by given resource manifests.
        Undeploy operation first scale down the replicas to 0 and then deletes
        the resource from cluster.
        """
        logger.info("Deploying to Kubernetes")

        for kind, objects in self.k8s_artifacts.iteritems():
            for artifact in objects:
                if self.dryrun:
                    logger.info("DRY-RUN: Deploying k8s KIND: %s, ARTIFACT: %s"
                                % (kind, artifact))
                else:
                    try:
                        self.api.delete(kind, artifact)
                    except HTTPError as e:
                        msg = "Failed to stop Kubernetes artifact kind: %s. " \
                            "Error: %s" % (kind, e)
                        raise ProviderFailedException(msg)
