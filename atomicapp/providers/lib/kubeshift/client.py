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

from atomicapp.providers.lib.kubeshift.kubernetes import KubeKubernetesClient
from atomicapp.providers.lib.kubeshift.openshift import KubeOpenshiftClient
from atomicapp.providers.lib.kubeshift.exceptions import KubeClientError
from atomicapp.constants import LOGGER_DEFAULT
import logging
logger = logging.getLogger(LOGGER_DEFAULT)


class Client(object):

    def __init__(self, config, provider):
        '''

        Args:
            config (obj): Object of the configuration data
            provider (str): String value of the provider that is being used

        '''
        self.config = config
        self.provider = provider

        # Choose the type of provider that is being used. Error out if it is not available
        if provider is "kubernetes":
            self.connection = KubeKubernetesClient(config)
            logger.debug("Using Kubernetes Provider KubeClient library")
        elif provider is "openshift":
            self.connection = KubeOpenshiftClient(config)
            logger.debug("Using OpenShift Provider KubeClient library")
        else:
            raise KubeClientError("No provider by that name.")

    # Create an object using its respective API
    def create(self, obj, namespace="default"):
        self.connection.create(obj, namespace)

    # Delete an object using its respective API
    def delete(self, obj, namespace="default"):
        self.connection.delete(obj, namespace)

    # Current support: kubernetes only
    def namespaces(self):
        return self.connection.namespaces()
