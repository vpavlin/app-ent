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

from atomicapp.constants import (PROVIDER_AUTH_KEY,
                                 ANSWERS_FILE,
                                 DEFAULT_NAMESPACE,
                                 LOGGER_DEFAULT,
                                 PROVIDER_API_KEY,
                                 PROVIDER_CA_KEY,
                                 PROVIDER_TLS_VERIFY_KEY,
                                 LOGGER_COCKPIT,
                                 OC_DEFAULT_API)
from atomicapp.plugin import Provider, ProviderFailedException

from atomicapp.providers.lib.kubeshift.kubeconfig import KubeConfig
from atomicapp.providers.lib.kubeshift.client import Client
from atomicapp.utils import Utils
cockpit_logger = logging.getLogger(LOGGER_COCKPIT)
logger = logging.getLogger(LOGGER_DEFAULT)


class OpenshiftProvider(Provider):

    """Operations for OpenShift provider is implemented in this class.
    This class implements deploy, stop and undeploy of an atomicapp on
    OpenShift provider.
    """

    # Class variables
    key = "openshift"
    namespace = DEFAULT_NAMESPACE
    oc_artifacts = {}

    # From the provider configuration
    config_file = None

    # Essential provider parameters
    provider_api = None
    provider_auth = None
    provider_tls_verify = None
    provider_ca = None

    def init(self):
        self.oc_artifacts = {}

        logger.debug("Given config: %s", self.config)
        if self.config.get("namespace"):
            self.namespace = self.config.get("namespace")

        logger.info("Using namespace %s", self.namespace)

        self._process_artifacts()

        if self.dryrun:
            return

        '''
        Config_file:
            If a config_file has been provided, use the configuration
            from the file and load the associated generated file.
            If a config_file exists (--provider-config) use that.

        Params:
            If any provider specific parameters have been provided,
            load the configuration through the answers.conf file

        .kube/config:
            If no config file or params are provided by user then try to find and
            use a config file at the default location.

        no config at all:
            If no .kube/config file can be found then try to connect to the default
            unauthenticated http://localhost:8080/api end-point.
        '''

        default_config_loc = os.path.join(
            Utils.getRoot(), Utils.getUserHome().strip('/'), '.kube/config')

        if self.config_file:
            logger.debug("Provider configuration provided")
            self.api = Client(KubeConfig.from_file(self.config_file), "openshift")
        elif self._check_required_params():
            logger.debug("Generating .kube/config from given parameters")
            self.api = Client(self._from_required_params(), "openshift")
        elif os.path.isfile(default_config_loc):
            logger.debug(".kube/config exists, using default configuration file")
            self.api = Client(KubeConfig.from_file(default_config_loc), "openshift")
        else:
            self.config["provider-api"] = OC_DEFAULT_API
            self.api = Client(self._from_required_params(), "openshift")

        self._check_namespaces()

    def _build_param_dict(self):
        # Initialize the values
        paramdict = {PROVIDER_API_KEY: self.provider_api,
                     PROVIDER_AUTH_KEY: self.provider_auth,
                     PROVIDER_TLS_VERIFY_KEY: self.provider_tls_verify,
                     PROVIDER_CA_KEY: self.provider_ca}

        # Get values from the loaded answers.conf / passed CLI params
        for k in paramdict.keys():
            paramdict[k] = self.config.get(k)

        return paramdict

    def _check_required_params(self, exception=False):
        '''
        This checks to see if required parameters associated to the Kubernetes
        provider are passed.
        PROVIDER_API_KEY and PROVIDER_AUTH_KEY are *required*. Token may be blank.
        '''

        paramdict = self._build_param_dict()
        logger.debug("List of parameters passed: %s" % paramdict)

        # Check that the required parameters are passed. If not, error out.
        for k in [PROVIDER_API_KEY, PROVIDER_AUTH_KEY]:
            if paramdict[k] is None:
                if exception:
                    msg = "You need to set %s in %s or pass it as a CLI param" % (k, ANSWERS_FILE)
                    raise ProviderFailedException(msg)
                else:
                    return False

        return True

    def _from_required_params(self):
        '''
        Create a default configuration from passed environment parameters.
        '''

        self._check_required_params(exception=True)
        paramdict = self._build_param_dict()

        logger.debug("Building from required params")
        # Generate the configuration from the paramters
        config = KubeConfig().from_params(api=paramdict[PROVIDER_API_KEY],
                                          auth=paramdict[PROVIDER_AUTH_KEY],
                                          ca=paramdict[PROVIDER_CA_KEY],
                                          verify=paramdict[PROVIDER_TLS_VERIFY_KEY])
        logger.debug("Passed configuration for .kube/config %s" % config)
        return config

    def _check_namespaces(self):
        '''
        This function checks to see whether or not the namespaces created in the cluster match the
        namespace that is associated and/or provided in the deployed application
        '''

        # Get the namespaces and output the currently used ones
        namespace_list = self.api.namespaces()
        logger.debug("There are currently %s namespaces in the cluster." % str(len(namespace_list)))

        # Create a namespace list
        namespaces = []
        for ns in namespace_list:
            namespaces.append(ns["metadata"]["name"])

        # Output the namespaces and check to see if the one provided exists
        logger.debug("Namespaces: %s" % namespaces)
        if self.namespace not in namespaces:
            msg = "%s namespace does not exist. Please create the namespace and try again." % self.namespace
            raise ProviderFailedException(msg)

    def _process_artifacts(self):
        """
        Parse each Kubernetes file and convert said format into an Object for
        deployment.
        """
        for artifact in self.artifacts:
            logger.debug("Processing artifact: %s", artifact)
            data = None

            # Open and parse the artifact data
            with open(os.path.join(self.path, artifact), "r") as fp:
                data = anymarkup.parse(fp, force_types=None)

            # Process said artifacts
            self._process_artifact_data(artifact, data)

    def _process_artifact_data(self, artifact, data):
        """
        Process the data for an artifact

        Args:
            artifact (str): Artifact name
            data (dict): Artifact data
        """

        # Check if kind exists
        if "kind" not in data.keys():
            raise ProviderFailedException(
                "Error processing %s artifact. There is no kind" % artifact)

        # Change to lower case so it's easier to parse
        kind = data["kind"].lower()

        if kind not in self.oc_artifacts.keys():
            self.oc_artifacts[kind] = []

        # Fail if there is no metadata
        if 'metadata' not in data:
            raise ProviderFailedException(
                "Error processing %s artifact. There is no metadata object" % artifact)

        # Change to the namespace specified on init()
        data['metadata']['namespace'] = self.namespace

        if 'labels' not in data['metadata']:
            data['metadata']['labels'] = {'namespace': self.namespace}
        else:
            data['metadata']['labels']['namespace'] = self.namespace

        self.oc_artifacts[kind].append(data)

    def run(self):
        """
        Deploys the app by given resource artifacts.
        """
        logger.info("Deploying to OpenShift")

        for kind, objects in self.oc_artifacts.iteritems():
            for artifact in objects:
                if self.dryrun:
                    logger.info("DRY-RUN: Deploying k8s KIND: %s, ARTIFACT: %s"
                                % (kind, artifact))
                else:
                    self.api.create(artifact, self.namespace)

    def stop(self):
        """Undeploys the app by given resource manifests.
        Undeploy operation first scale down the replicas to 0 and then deletes
        the resource from cluster.
        """
        logger.info("Undeploying from OpenShift")

        for kind, objects in self.oc_artifacts.iteritems():
            for artifact in objects:
                if self.dryrun:
                    logger.info("DRY-RUN: Deploying k8s KIND: %s, ARTIFACT: %s"
                                % (kind, artifact))
                else:
                    self.api.delete(artifact, self.namespace)
