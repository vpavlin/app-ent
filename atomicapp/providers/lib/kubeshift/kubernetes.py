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

import logging
import re

from urlparse import urljoin
from urllib import urlencode
from atomicapp.constants import LOGGER_DEFAULT
from atomicapp.providers.lib.kubeshift.kubebase import KubeBase
from atomicapp.providers.lib.kubeshift.exceptions import (KubeKubernetesError)

logger = logging.getLogger(LOGGER_DEFAULT)


class KubeKubernetesClient(object):

    def __init__(self, config):
        '''

        Args:
            config (obj): Object of the configuration data

        '''

        # The configuration data passed in will be .kube/config data, so process is accordingly.
        self.api = KubeBase(config)

        # Check the API url
        url = self.api.cluster['server']
        if not re.match('(?:http|https)://', url):
            raise KubeKubernetesError("Kubernetes API URL does not include HTTP or HTTPS")

        # Gather what end-points we will be using
        self.k8s_api = urljoin(url, "api/v1/")

        # Test the connection before proceeding
        self.api.test_connection(self.k8s_api)

        # Gather the resource names which will be used for the 'kind' API calls
        self.k8s_api_resources = {}
        self.k8s_api_resources['v1'] = self.api.get_resources(self.k8s_api)

        # Gather what API groups are available
        self.k8s_apis = urljoin(url, "apis/")

        # Gather the group names from which resource names will be derived
        self.k8s_api_groups = self.api.get_groups(self.k8s_apis)

        for (name, versions) in self.k8s_api_groups:
            for version in versions:
                api = "%s/%s" % (name, version)
                url = urljoin(self.k8s_apis, api)
                self.k8s_api_resources[api] = self.api.get_resources(url)

    def create(self, obj, namespace):
        '''
        Create an object from the Kubernetes cluster
        '''
        name = self._get_metadata_name(obj)
        kind, url = self._generate_kurl(obj, namespace)

        self.api.request("post", url, data=obj)

        logger.info("%s '%s' successfully created", kind.capitalize(), name)

    def delete(self, obj, namespace):
        '''
        Delete an object from the Kubernetes cluster

        Args:
            obj (object): Object of the artifact being modified
            namesapce (str): Namespace of the kubernetes cluster to be used
            replicates (int): Default 0, size of the amount of replicas to scale

        *Note*
        Replication controllers must scale to 0 in order to delete pods.
        Kubernetes 1.3 will implement server-side cascading deletion, but
        until then, it's mandatory to scale to 0
        https://github.com/kubernetes/kubernetes/blob/master/docs/proposals/garbage-collection.md

        '''
        name = self._get_metadata_name(obj)
        kind, url = self._generate_kurl(obj, namespace, name)

        if kind in ['rcs', 'replicationcontrollers']:
            self.scale(obj, namespace)
        self.api.request("delete", url)

        logger.info("%s '%s' successfully deleted", kind.capitalize(), name)

    def scale(self, obj, namespace, replicas=0):
        '''
        By default we scale back down to 0. This function takes an object and scales said
        object down to a specified value on the Kubernetes cluster

        Args:
            obj (object): Object of the artifact being modified
            namesapce (str): Namespace of the kubernetes cluster to be used
            replicates (int): Default 0, size of the amount of replicas to scale
        '''
        patch = [{"op": "replace",
                  "path": "/spec/replicas",
                  "value": replicas}]
        name = self._get_metadata_name(obj)
        _, url = self._generate_kurl(obj, namespace, name)
        self.api.request("patch", url, data=patch)
        logger.info("'%s' successfully scaled to %s", name, replicas)

    def namespaces(self):
        '''
        Gathers a list of namespaces on the Kubernetes cluster
        '''
        url = urljoin(self.k8s_api, "namespaces")
        ns = self.api.request("get", url)
        return ns['items']

    def _generate_kurl(self, obj, namespace, name=None, params=None):
        '''
        Generate the required URL by extracting the 'kind' from the
        object as well as the namespace.

        Args:
            obj (obj): Object of the data being passed
            namespace (str): k8s namespace
            name (str): Name of the object being passed
            params (arr): Extra params passed such as timeout=300

        Returns:
            kind (str): The kind used
            url (str): The URL to be used / artifact URL
        '''
        if 'apiVersion' not in obj.keys():
            raise KubeKubernetesError("Error processing object. There is no apiVersion")

        if 'kind' not in obj.keys():
            raise KubeKubernetesError("Error processing object. There is no kind")

        api_version = obj['apiVersion']

        kind = obj['kind']

        resource = KubeBase.kind_to_resource_name(kind)

        if resource in self.k8s_api_resources[api_version]:
            if api_version == 'v1':
                url = self.k8s_api
            else:
                url = urljoin(self.k8s_apis, "%s/" % api_version)
        else:
            raise KubeKubernetesError("No kind by that name: %s" % kind)

        url = urljoin(url, "namespaces/%s/%s/" % (namespace, resource))

        if name:
            url = urljoin(url, name)

        if params:
            url = urljoin(url, "?%s" % urlencode(params))

        return (resource, url)

    @staticmethod
    def _get_metadata_name(obj):
        '''
        This looks at the object and grabs the metadata name of said object

        Args:
            obj (object): Object file of the artifact

        Returns:
            name (str): Returns the metadata name of the object
        '''
        if "metadata" in obj and \
                "name" in obj["metadata"]:
            name = obj["metadata"]["name"]
        else:
            raise KubeKubernetesError("Cannot undeploy. There is no"
                                      " name in object metadata "
                                      "object=%s" % obj)
        return name
