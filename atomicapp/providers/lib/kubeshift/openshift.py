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

import datetime
import time
import os
import tarfile
import logging
import re

from urlparse import urljoin
from urllib import urlencode
from atomicapp.utils import Utils
from atomicapp.constants import LOGGER_DEFAULT
from atomicapp.providers.lib.kubeshift.kubebase import KubeBase
from atomicapp.providers.lib.kubeshift.exceptions import KubeOpenshiftError

logger = logging.getLogger(LOGGER_DEFAULT)


class KubeOpenshiftClient(object):

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
            raise KubeOpenshiftError("OpenShift API URL does not include HTTP or HTTPS")

        # Gather what end-points we will be using
        self.k8s_api = urljoin(url, "api/v1/")
        self.oc_api = urljoin(url, "oapi/v1/")

        # Test the connection before proceeding
        self.api.test_connection(self.k8s_api)
        self.api.test_connection(self.oc_api)

        # Gather the resource names which will be used for the 'kind' API calls
        self.oc_api_resources = self.api.get_resources(self.oc_api)

        # Gather what API groups are available
        # TODO: refactor this (create function in kubebase.py)
        self.k8s_api_resources = {}
        self.k8s_api_resources['v1'] = self.api.get_resources(self.k8s_api)
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

        # Must process through each object if kind is a 'template'
        if kind is "template":
            self._process_template(obj, namespace, "create")
        else:
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

        # Must process through each object if kind is a 'template'
        if kind is "template":
            self._process_template(obj, namespace, "create")
        else:
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
        url = urljoin(self.oc_api, "projects")
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
            raise KubeOpenshiftError("Error processing object. There is no apiVersion")

        if 'kind' not in obj.keys():
            raise KubeOpenshiftError("Error processing object. There is no kind")

        api_version = obj['apiVersion']

        kind = obj['kind']

        resource = KubeBase.kind_to_resource_name(kind)

        if resource in self.k8s_api_resources[api_version]:
            if api_version == 'v1':
                url = self.k8s_api
            else:
                url = urljoin(self.k8s_apis, "%s/" % api_version)
        elif resource in self.oc_api_resources:
            url = self.oc_api
        else:
            raise KubeOpenshiftError("No kind by that name: %s" % kind)

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
            raise KubeOpenshiftError("Cannot undeploy. There is no"
                                     " name in object metadata "
                                     "object=%s" % obj)
        return name

    # OPENSHIFT-SPECIFIC FUNCTIONS

    def extract(self, image, src, dest, namespace, update=True):
        """
        Extract contents of a container image from 'src' in container
        to 'dest' in host.

        Args:
            image (str): Name of container image
            src (str): Source path in container
            dest (str): Destination path in host
            update (bool): Update existing destination, if True
        """
        if os.path.exists(dest) and not update:
            return
        cleaned_image_name = Utils.sanitizeName(image)
        pod_name = '{}-{}'.format(cleaned_image_name, Utils.getUniqueUUID())
        container_name = cleaned_image_name

        # Pull (if needed) image and bring up a container from it
        # with 'sleep 3600' entrypoint, just to extract content from it
        artifact = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'name': pod_name
            },
            'spec': {
                'containers': [
                    {
                        'image': image,
                        'command': [
                            'sleep',
                            '3600'
                        ],
                        'imagePullPolicy': 'IfNotPresent',
                        'name': container_name
                    }
                ],
                'restartPolicy': 'Always'
            }
        }

        self.create(artifact, namespace)
        try:
            self._wait_till_pod_runs(namespace, pod_name, timeout=300)

            # Archive content from the container and dump it to tmpfile
            tmpfile = '/tmp/atomicapp-{pod}.tar.gz'.format(pod=pod_name)

            self._execute(
                namespace, pod_name, container_name,
                'tar -cz --directory {} ./'.format('/' + src),
                outfile=tmpfile
            )
        finally:
            # Delete created pod
            self.delete(artifact, namespace)

        # Extract archive data
        tar = tarfile.open(tmpfile, 'r:gz')
        tar.extractall(dest)

    def _execute(self, namespace, pod, container, command,
                 outfile=None):
        """
        Execute a command in a container in an Openshift pod.

        Args:
            namespace (str): Namespace
            pod (str): Pod name
            container (str): Container name inside pod
            command (str): Command to execute
            outfile (str): Path to output file where results should be dumped

        Returns:
            Command output (str) or None in case results dumped to output file
        """
        args = {
            'token': self.api.token,
            'namespace': namespace,
            'pod': pod,
            'container': container,
            'command': ''.join(['command={}&'.format(word) for word in command.split()])
        }
        url = urljoin(
            self.k8s_api,
            'namespaces/{namespace}/pods/{pod}/exec?'
            'access_token={token}&container={container}&'
            '{command}stdout=1&stdin=0&tty=0'.format(**args))

        return self.api.websocket_request(url, outfile)

    def _process_template(self, obj, namespace, method):
        _, url = self._generate_kurl(obj, namespace)
        data = self.api.request("post", url, data=obj)

        if method is "create":
            for o in data[0]['objects']:
                name = self._get_metadata_name(o)
                _, object_url = self._generate_kurl(o, namespace)
                self.api.request("post", object_url, data=o)
                logger.debug("Created template object: %s" % name)
        elif method is "delete":
            for o in data[0]['objects']:
                name = self._get_metadata_name(o)
                _, object_url = self._generate_kurl(o, namespace, name)
                self.api.request("delete", object_url)
                logger.debug("Deleted template object: %s" % name)
        else:
            raise KubeOpenshiftError("No method by that name to process template")

        logger.debug("Processed object template successfully")

    def _get_pod_status(self, namespace, pod):
        """
        Get pod status.

        Args:
            namespace (str): Openshift namespace
            pod (str): Pod name

        Returns:
            Status of pod (str)

        Raises:
            ProviderFailedException when unable to fetch Pod status.
        """
        args = {
            'namespace': namespace,
            'pod': pod,
            'access_token': self.api.token
        }
        url = urljoin(
            self.k8s_api,
            'namespaces/{namespace}/pods/{pod}?'
            'access_token={access_token}'.format(**args))
        data = self.api.request("get", url)

        return data['status']['phase'].lower()

    def _wait_till_pod_runs(self, namespace, pod, timeout=300):
        """
        Wait till pod runs, with a timeout.

        Args:
            namespace (str): Openshift namespace
            pod (str): Pod name
            timeout (int): Timeout in seconds.

        Raises:
            ProviderFailedException on timeout or when the pod goes to
            failed state.
        """
        now = datetime.datetime.now()
        timeout_delta = datetime.timedelta(seconds=timeout)
        while datetime.datetime.now() - now < timeout_delta:
            status = self.oc.get_pod_status(namespace, pod)
            if status == 'running':
                break
            elif status == 'failed':
                raise KubeOpenshiftError(
                    'Unable to run pod for extracting content: '
                    '{namespace}/{pod}'.format(namespace=namespace,
                                               pod=pod))
            time.sleep(1)
        if status != 'running':
            raise KubeOpenshiftError(
                'Timed out to extract content from pod: '
                '{namespace}/{pod}'.format(namespace=namespace,
                                           pod=pod))
