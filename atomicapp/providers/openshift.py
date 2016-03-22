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
import os
import anymarkup
import ssl
import tarfile
import time
from urlparse import urljoin
from urllib import urlencode
import websocket

from atomicapp.utils import Utils
from atomicapp.plugin import Provider, ProviderFailedException
from atomicapp.constants import (ACCESS_TOKEN_KEY,
                                 ANSWERS_FILE,
                                 DEFAULT_NAMESPACE,
                                 LOGGER_DEFAULT,
                                 NAMESPACE_KEY,
                                 PROVIDER_API_KEY,
                                 PROVIDER_TLS_VERIFY_KEY,
                                 PROVIDER_CA_KEY)
from requests.exceptions import SSLError
import logging
logger = logging.getLogger(LOGGER_DEFAULT)

# If running in an openshift POD via `oc new-app`, the ca file is here
OPENSHIFT_POD_CA_FILE = "/run/secrets/kubernetes.io/serviceaccount/ca.crt"


class OpenshiftClient(object):

    def __init__(self, providerapi, access_token,
                 provider_tls_verify, provider_ca):
        self.providerapi = providerapi
        self.access_token = access_token
        self.provider_tls_verify = provider_tls_verify
        self.provider_ca = provider_ca

        # construct full urls for api endpoints
        self.kubernetes_api = urljoin(self.providerapi, "api/v1/")
        self.openshift_api = urljoin(self.providerapi, "oapi/v1/")

        logger.debug("kubernetes_api = %s", self.kubernetes_api)
        logger.debug("openshift_api = %s", self.openshift_api)

    def test_connection(self):
        """
        Test connection to OpenShift server

        Raises:
            ProviderFailedException - Invalid SSL/TLS certificate
        """
        logger.debug("Testing connection to OpenShift server")

        if self.provider_ca and not os.path.exists(self.provider_ca):
            raise ProviderFailedException("Unable to find CA path %s"
                                          % self.provider_ca)

        try:
            (status_code, return_data) = \
                Utils.make_rest_request("get",
                                        self.openshift_api,
                                        verify=self._requests_tls_verify())
        except SSLError as e:
            if self.provider_tls_verify:
                msg = "SSL/TLS ERROR: invalid certificate. " \
                      "Add certificate of correct Certificate Authority providing" \
                      " `%s` or you can disable SSL/TLS verification by `%s=False`" \
                      % (PROVIDER_CA_KEY, PROVIDER_TLS_VERIFY_KEY)
                raise ProviderFailedException(msg)
            else:
                # this shouldn't happen
                raise ProviderFailedException(e.message)

    def get_oapi_resources(self):
        """
        Get Openshift API resources
        """
        # get list of supported resources for each api
        (status_code, return_data) = \
            Utils.make_rest_request("get",
                                    self.openshift_api,
                                    verify=self._requests_tls_verify())
        if status_code == 200:
            oapi_resources = return_data["resources"]
        else:
            raise ProviderFailedException("Cannot get OpenShift resource list")

        # convert resources list of dicts to list of names
        oapi_resources = [res['name'] for res in oapi_resources]

        logger.debug("Openshift resources %s", oapi_resources)

        return oapi_resources

    def get_kapi_resources(self):
        """
        Get kubernetes API resources
        """
        # get list of supported resources for each api
        (status_code, return_data) = \
            Utils.make_rest_request("get",
                                    self.kubernetes_api,
                                    verify=self._requests_tls_verify())
        if status_code == 200:
            kapi_resources = return_data["resources"]
        else:
            raise ProviderFailedException("Cannot get Kubernetes resource list")

        # convert resources list of dicts to list of names
        kapi_resources = [res['name'] for res in kapi_resources]

        logger.debug("Kubernetes resources %s", kapi_resources)

        return kapi_resources

    def deploy(self, url, artifact):
        (status_code, return_data) = \
            Utils.make_rest_request("post",
                                    url,
                                    verify=self._requests_tls_verify(),
                                    data=artifact)
        if status_code == 201:
            logger.info("Object %s successfully deployed.",
                        artifact['metadata']['name'])
        else:
            msg = "%s %s" % (status_code, return_data)
            logger.error(msg)
            # TODO: remove running components (issue: #428)
            raise ProviderFailedException(msg)

    def delete(self, url):
        """
        Delete object on given url

        Args:
            url (str): full url for artifact

        Raises:
            ProviderFailedException: error when calling remote api
        """
        (status_code, return_data) = \
            Utils.make_rest_request("delete",
                                    url,
                                    verify=self._requests_tls_verify())
        if status_code == 200:
            logger.info("Successfully deleted.")
        else:
            msg = "%s %s" % (status_code, return_data)
            logger.error(msg)
            raise ProviderFailedException(msg)

    def scale(self, url, replicas):
        """
        Scale ReplicationControllers or DeploymentConfig

        Args:
          url (str): full url for artifact
          replicas (int): number of replicas scale to
        """
        patch = [{"op": "replace",
                  "path": "/spec/replicas",
                  "value": replicas}]

        (status_code, return_data) = \
            Utils.make_rest_request("patch",
                                    url,
                                    data=patch,
                                    verify=self._requests_tls_verify())
        if status_code == 200:
            logger.info("Successfully scaled to %s replicas", replicas)
        else:
            msg = "%s %s" % (status_code, return_data)
            logger.error(msg)
            raise ProviderFailedException(msg)

    def process_template(self, url, template):
        (status_code, return_data) = \
            Utils.make_rest_request("post",
                                    url,
                                    verify=self._requests_tls_verify(),
                                    data=template)
        if status_code == 201:
            logger.info("template processed %s", template['metadata']['name'])
            logger.debug("processed template %s", return_data)
            return return_data['objects']
        else:
            msg = "%s %s" % (status_code, return_data)
            logger.error(msg)
            raise ProviderFailedException(msg)

    def _requests_tls_verify(self):
        """
        Return verify parameter for function Utils.make_rest_request
        in format that is used by requests library.
        see: http://docs.python-requests.org/en/latest/user/advanced/#ssl-cert-verification
        """
        if self.provider_ca and self.provider_tls_verify:
            return self.provider_ca
        else:
            return self.provider_tls_verify

    def execute(self, namespace, pod, container, command,
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
            'token': self.access_token,
            'namespace': namespace,
            'pod': pod,
            'container': container,
            'command': ''.join(['command={}&'.format(word) for word in command.split()])
        }
        url = urljoin(
            self.kubernetes_api,
            'namespaces/{namespace}/pods/{pod}/exec?'
            'access_token={token}&container={container}&'
            '{command}stdout=1&stdin=0&tty=0'.format(**args))

        # The above endpoint needs the request to be upgraded to SPDY,
        # which python-requests does not yet support. However, the same
        # endpoint works over websockets, so we are using websocket client.

        # Convert url from http(s) protocol to wss protocol
        url = 'wss://' + url.split('://', 1)[-1]
        logger.debug('url: {}'.format(url))

        results = []

        ws = websocket.WebSocketApp(
            url,
            on_message=lambda ws, message: self._handle_exec_reply(ws, message, results, outfile))

        ws.run_forever(sslopt={
            'ca_certs': self.provider_ca,
            'cert_reqs': ssl.CERT_REQUIRED if self.provider_tls_verify else ssl.CERT_NONE})

        if not outfile:
            return ''.join(results)

    def _handle_exec_reply(self, ws, message, results, outfile=None):
        """
        Handle reply message for exec call
        """
        # FIXME: For some reason, we do not know why,  we need to ignore the
        # 1st char of the message, to generate a meaningful result
        cleaned_msg = message[1:]
        if outfile:
            with open(outfile, 'ab') as f:
                f.write(cleaned_msg)
        else:
            results.append(cleaned_msg)

    def get_pod_status(self, namespace, pod):
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
            'access_token': self.access_token
        }
        url = urljoin(
            self.kubernetes_api,
            'namespaces/{namespace}/pods/{pod}?'
            'access_token={access_token}'.format(**args))
        (status_code, return_data) = \
            Utils.make_rest_request("get", url, verify=self._requests_tls_verify())

        if status_code != 200:
            raise ProviderFailedException(
                'Could not fetch status for pod: {namespace}/{pod}'.format(
                    namespace=namespace, pod=pod))
        return return_data['status']['phase'].lower()


class OpenShiftProvider(Provider):
    key = "openshift"
    cli_str = "oc"
    cli = None
    config_file = None
    template_data = None
    providerapi = "https://127.0.0.1:8443"
    openshift_api = None
    kubernetes_api = None
    access_token = None
    namespace = DEFAULT_NAMESPACE

    # verify tls/ssl connection
    provider_tls_verify = True
    # path to file or dir with CA certificates
    provider_ca = None

    # Parsed artifacts. Key is kind of artifacts. Value is list of artifacts.
    openshift_artifacts = {}

    def init(self):
        self.openshift_artifacts = {}

        self._set_config_values()

        self.oc = OpenshiftClient(self.providerapi,
                                  self.access_token,
                                  self.provider_tls_verify,
                                  self.provider_ca)
        self.openshift_api = self.oc.openshift_api
        self.kubernetes_api = self.oc.kubernetes_api

        # test connection to openshift server
        self.oc.test_connection()

        self.oapi_resources = self.oc.get_oapi_resources()
        self.kapi_resources = self.oc.get_kapi_resources()

        self._process_artifacts()

    def _get_namespace(self, artifact):
        """
        Return namespace for artifact. If namespace is specified inside
        artifact use that, if not return default namespace (as specfied in
        answers.conf)

        Args:
            artifact (dict): OpenShift/Kubernetes object

        Returns:
            namespace (str)
        """
        if "metadata" in artifact and "namespace" in artifact["metadata"]:
            return artifact["metadata"]["namespace"]
        return self.namespace

    def run(self):
        logger.debug("Deploying to OpenShift")
        # TODO: remove running components if one component fails issue:#428
        for kind, objects in self.openshift_artifacts.iteritems():
            for artifact in objects:
                namespace = self._get_namespace(artifact)
                url = self._get_url(namespace, kind)

                if self.dryrun:
                    logger.info("DRY-RUN: %s", url)
                    continue
                self.oc.deploy(url, artifact)

    def stop(self):
        """
        Undeploy application.

        Cascade the deletion of the resources managed other resource
        (e.g. ReplicationControllers created by a DeploymentConfig and
        Pods created by a ReplicationController).
        When using command line client this is done automatically
        by `oc` command.
        When using API calls we have to cascade deletion manually.
        """
        logger.debug("Starting undeploy")
        delete_artifacts = []
        for kind, objects in self.openshift_artifacts.iteritems():
            # Add deployment configs to beginning of the list so they are deleted first.
            # Do deployment config first because if you do replication controller
            # before deployment config then the deployment config will re-spawn
            # the replication controller before the deployment config is deleted.
            if kind == "deploymentconfig":
                delete_artifacts = objects + delete_artifacts
            else:
                delete_artifacts = delete_artifacts + objects

        for artifact in delete_artifacts:
            kind = artifact["kind"].lower()
            namespace = self._get_namespace(artifact)

            # Get name from metadata so we know which object to delete.
            if "metadata" in artifact and \
                    "name" in artifact["metadata"]:
                name = artifact["metadata"]["name"]
            else:
                raise ProviderFailedException("Cannot undeploy. There is no"
                                              " name in artifacts metadata "
                                              "artifact=%s" % artifact)

            logger.info("Undeploying artifact name=%s kind=%s" % (name, kind))

            # If this is a deployment config we need to delete all
            # replication controllers that were created by this.
            # Find the replication controller that was created by this deployment
            # config by querying for all replication controllers and filtering based
            # on automatically created label openshift.io/deployment-config.name
            if kind.lower() == "deploymentconfig":
                params = {"labelSelector":
                          "openshift.io/deployment-config.name=%s" % name}
                url = self._get_url(namespace,
                                    "replicationcontroller",
                                    params=params)
                (status_code, return_data) = \
                    Utils.make_rest_request("get", url, verify=self.oc._requests_tls_verify())
                if status_code != 200:
                    raise ProviderFailedException("Cannot get Replication"
                                                  "Controllers for Deployment"
                                                  "Config %s (status code %s)" %
                                                  (name, status_code))
                # kind of returned data is ReplicationControllerList
                # https://docs.openshift.com/enterprise/3.1/rest_api/kubernetes_v1.html#v1-replicationcontrollerlist
                # we need modify items to get valid ReplicationController
                items = return_data["items"]
                for item in items:
                    item["kind"] = "ReplicationController"
                    item["apiVersion"] = return_data["apiVersion"]
                # add items to list of artifact to be deleted
                delete_artifacts.extend(items)

            url = self._get_url(namespace, kind, name)

            # Scale down replication controller to 0 replicas before deleting.
            # This should take care of all pods created by this replication
            # controller and we can safely delete it.
            if kind.lower() == "replicationcontroller":
                if self.dryrun:
                    logger.info("DRY-RUN: SCALE %s down to 0", url)
                else:
                    self.oc.scale(url, 0)

            if self.dryrun:
                logger.info("DRY-RUN: DELETE %s", url)
            else:
                self.oc.delete(url)

    def _process_artifacts(self):
        """
        Parse OpenShift manifests files and checks if manifest under
        process is valid. Reads self.artifacts and saves parsed artifacts
        to self.openshift_artifacts
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
        # kind has to be specified in artifact
        if "kind" not in data.keys():
            raise ProviderFailedException(
                "Error processing %s artifact. There is no kind" % artifact)

        kind = data["kind"].lower()
        resource = self._kind_to_resource(kind)

        # check if resource is supported by apis
        if resource not in self.oapi_resources \
                and resource not in self.kapi_resources:
            raise ProviderFailedException(
                "Unsupported kind %s in artifact %s" % (kind, artifact))

        # process templates
        if kind == "template":
            processed_objects = self._process_template(data)
            # add all processed object to artifacts dict
            for obj in processed_objects:
                obj_kind = obj["kind"].lower()
                if obj_kind not in self.openshift_artifacts.keys():
                    self.openshift_artifacts[obj_kind] = []
                self.openshift_artifacts[obj_kind].append(obj)
            return

        # add parsed artifact to dict
        if kind not in self.openshift_artifacts.keys():
            self.openshift_artifacts[kind] = []
        self.openshift_artifacts[kind].append(data)

    def _process_template(self, template):
        """
        Call OpenShift api and process template.
        Templates allow parameterization of resources prior to being sent to
        the server for creation or update. Templates have "parameters",
        which may either be generated on creation or set by the user.

        Args:
            template (dict): template to process

        Returns:
            List of objects from processed template.
        """
        logger.debug("processing template: %s", template)
        url = self._get_url(self._get_namespace(template), "processedtemplates")
        return self.oc.process_template(url, template)

    def _kind_to_resource(self, kind):
        """
        Converts kind to resource name. It is same logics
        as in k8s.io/kubernetes/pkg/api/meta/restmapper.go (func KindToResource)
        Example:
            Pod -> pods
            Policy - > policies
            BuildConfig - > buildconfigs

        Args:
            kind (str): Kind of the object

        Returns:
            Resource name (str) (kind in plural form)
        """
        singular = kind.lower()
        if singular.endswith("status"):
            plural = singular + "es"
        else:
            if singular[-1] == "s":
                plural = singular
            elif singular[-1] == "y":
                plural = singular.rstrip("y") + "ies"
            else:
                plural = singular + "s"
        return plural

    def _get_url(self, namespace, kind, name=None, params=None):
        """
        Some kinds/resources are managed by OpensShift and some by Kubernetes.
        Here we compose right url (Kubernets or OpenShift) for given kind.
        If resource is managed by Kubernetes or OpenShift is determined by
        self.kapi_resources/self.oapi_resources lists
        Example:
            For namespace=project1, kind=DeploymentConfig, name=dc1 result
            would be http://example.com:8443/oapi/v1/namespaces/project1/deploymentconfigs/dc1

        Args:
            namespace (str): Kubernetes namespace or Openshift project name
            kind (str): kind of the object
            name (str): object name if modifying or deleting specific object (optional)
            params (dict): query parameters {"key":"value"}  url?key=value

        Returns:
            Full url (str) for given kind, namespace and name
        """
        url = None

        resource = self._kind_to_resource(kind)

        if resource in self.oapi_resources:
            url = self.openshift_api
        elif resource in self.kapi_resources:
            url = self.kubernetes_api

        url = urljoin(url, "namespaces/%s/%s/" % (namespace, resource))

        if name:
            url = urljoin(url, name)

        if params:
            params["access_token"] = self.access_token
        else:
            params = {"access_token": self.access_token}

        url = urljoin(url, "?%s" % urlencode(params))
        logger.debug("url: %s", url)
        return url

    def _parse_kubeconf(self, filename):
        """"
        Parse kubectl config file

        Args:
            filename (string): path to configuration file (e.g. ./kube/config)

        Returns:
            dict of parsed values from config

        Example of expected file format:
            apiVersion: v1
            clusters:
            - cluster:
                server: https://10.1.2.2:8443
                certificate-authority: path-to-ca.cert
                insecure-skip-tls-verify: false
              name: 10-1-2-2:8443
            contexts:
            - context:
                cluster: 10-1-2-2:8443
                namespace: test
                user: test-admin/10-1-2-2:8443
              name: test/10-1-2-2:8443/test-admin
            current-context: test/10-1-2-2:8443/test-admin
            kind: Config
            preferences: {}
            users:
            - name: test-admin/10-1-2-2:8443
            user:
                token: abcdefghijklmnopqrstuvwxyz0123456789ABCDEF
        """
        logger.debug("Parsing %s", filename)

        with open(filename, 'r') as fp:
            kubecfg = anymarkup.parse(fp.read())

        try:
            return self._parse_kubeconf_data(kubecfg)
        except ProviderFailedException:
            raise ProviderFailedException('Invalid %s' % filename)

    def _parse_kubeconf_data(self, kubecfg):
        """
        Parse kubeconf data.

        Args:
            kubecfg (dict): Kubernetes config data

        Returns:
            dict of parsed values from config
        """
        url = None
        token = None
        namespace = None
        tls_verify = True
        ca = None

        current_context = kubecfg["current-context"]

        logger.debug("current context: %s", current_context)

        context = None
        for co in kubecfg["contexts"]:
            if co["name"] == current_context:
                context = co

        if not context:
            raise ProviderFailedException()

        cluster = None
        for cl in kubecfg["clusters"]:
            if cl["name"] == context["context"]["cluster"]:
                cluster = cl

        user = None
        for usr in kubecfg["users"]:
            if usr["name"] == context["context"]["user"]:
                user = usr

        if not cluster or not user:
            raise ProviderFailedException()

        logger.debug("context: %s", context)
        logger.debug("cluster: %s", cluster)
        logger.debug("user: %s", user)

        url = cluster["cluster"]["server"]
        token = user["user"]["token"]
        if "namespace" in context["context"]:
            namespace = context["context"]["namespace"]
        if "insecure-skip-tls-verify" in cluster["cluster"]:
            tls_verify = not cluster["cluster"]["insecure-skip-tls-verify"]
        elif "certificate-authority" in cluster["cluster"]:
            ca = cluster["cluster"]["certificate-authority"]

        return {PROVIDER_API_KEY: url,
                ACCESS_TOKEN_KEY: token,
                NAMESPACE_KEY: namespace,
                PROVIDER_TLS_VERIFY_KEY: tls_verify,
                PROVIDER_CA_KEY: ca}

    def _set_config_values(self):
        """
        Reads providerapi, namespace and accesstoken from answers.conf and
        corresponding values from providerconfig (if set).
        Use one that is set, if both are set and have conflicting values raise
        exception.

        Raises:
            ProviderFailedException: values in providerconfig and answers.conf
                are in conflict

        """

        # First things first, if we are running inside of an openshift pod via
        # `oc new-app` then get the config from the environment (files/env vars)
        # NOTE: pick up provider_tls_verify from answers if exists
        if Utils.running_on_openshift():
            self.providerapi = Utils.get_openshift_api_endpoint_from_env()
            self.namespace = os.environ['POD_NAMESPACE']
            self.access_token = os.environ['TOKEN_ENV_VAR']
            self.provider_ca = OPENSHIFT_POD_CA_FILE
            self.provider_tls_verify = \
                self.config.get(PROVIDER_TLS_VERIFY_KEY, True)
            return  # No need to process other information

        # initialize result to default values
        result = {PROVIDER_API_KEY: self.providerapi,
                  ACCESS_TOKEN_KEY: self.access_token,
                  NAMESPACE_KEY: self.namespace,
                  PROVIDER_TLS_VERIFY_KEY: self.provider_tls_verify,
                  PROVIDER_CA_KEY: self.provider_ca}

        # create keys in dicts and initialize values to None
        answers = {}
        providerconfig = {}
        for k in result.keys():
            answers[k] = None
            providerconfig[k] = None

        # get values from answers.conf
        for k in result.keys():
            answers[k] = self.config.get(k)

        # get values from providerconfig
        if self.config_file:
            providerconfig = self._parse_kubeconf(self.config_file)

        # decide between values from answers.conf and providerconfig
        # if only one is set use that, report if they are in conflict
        for k in result.keys():
            if answers[k] is not None and providerconfig[k] is None:
                result[k] = answers[k]
            if answers[k] is None and providerconfig[k] is not None:
                result[k] = providerconfig[k]
            if answers[k] is not None and providerconfig[k] is not None:
                if answers[k] == providerconfig[k]:
                    result[k] = answers[k]
                else:
                    msg = "There are conflicting values in %s (%s) and %s (%s)"\
                        % (self.config_file, providerconfig[k], ANSWERS_FILE,
                           answers[k])
                    logger.error(msg)
                    raise ProviderFailedException(msg)

        logger.debug("config values: %s" % result)

        # this items are required, they have to be not None
        for k in [PROVIDER_API_KEY, ACCESS_TOKEN_KEY, NAMESPACE_KEY]:
            if result[k] is None:
                msg = "You need to set %s in %s" % (k, ANSWERS_FILE)
                logger.error(msg)
                raise ProviderFailedException(msg)

        # set config values
        self.providerapi = result[PROVIDER_API_KEY]
        self.access_token = result[ACCESS_TOKEN_KEY]
        self.namespace = result[NAMESPACE_KEY]
        self.provider_tls_verify = result[PROVIDER_TLS_VERIFY_KEY]
        if result[PROVIDER_CA_KEY]:
            # if we are in container translate path to path on host
            self.provider_ca = os.path.join(Utils.getRoot(),
                                            result[PROVIDER_CA_KEY].lstrip('/'))
        else:
            self.provider_ca = None

    def extract(self, image, src, dest, update=True):
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

        self.oc.deploy(self._get_url(self.namespace, 'Pod'), artifact)
        try:
            self._wait_till_pod_runs(self.namespace, pod_name, timeout=300)

            # Archive content from the container and dump it to tmpfile
            tmpfile = '/tmp/atomicapp-{pod}.tar.gz'.format(pod=pod_name)
            self.oc.execute(
                self.namespace, pod_name, container_name,
                'tar -cz --directory {} ./'.format('/' + src),
                outfile=tmpfile
            )
        finally:
            # Delete created pod
            self.oc.delete(self._get_url(self.namespace, 'Pod', pod_name))

        # Extract archive data
        tar = tarfile.open(tmpfile, 'r:gz')
        tar.extractall(dest)

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
                raise ProviderFailedException(
                    'Unable to run pod for extracting content: '
                    '{namespace}/{pod}'.format(namespace=namespace,
                                               pod=pod))
            time.sleep(1)
        if status != 'running':
            raise ProviderFailedException(
                'Timed out to extract content from pod: '
                '{namespace}/{pod}'.format(namespace=namespace,
                                           pod=pod))
