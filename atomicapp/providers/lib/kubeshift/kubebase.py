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

import requests
import websocket
import tempfile
import base64
import ssl
from requests.exceptions import SSLError
from atomicapp.providers.lib.kubeshift.exceptions import (KubeBaseError,
                                                          KubeConnectionError)
from atomicapp.constants import LOGGER_DEFAULT
import logging
logger = logging.getLogger(LOGGER_DEFAULT)


class KubeBase(object):

    '''
    The role of Kube Base is to parse the Kube Config file and create an
    understandable API as well as initiation of connection to
    Kubernetes-based APIs (OpenShift/Kubernetes).

    '''
    cluster = None
    user = None
    token = None
    client_certification = None
    client_key = None
    certificate_authority_data = None  # Not yet implemented
    certificate_authority = None
    certificate_ca = None  # Not yet implemented
    insecure_skip_tls_verify = False

    def __init__(self, config):
        '''
        Args:
            config (object): An object of the .kube/config configuration
        '''
        self.kubeconfig = config

        # Gather the "current-context" from .kube/config which lists what the
        # associated cluster, user, token, etc. is being used.
        if "current-context" not in config:
            raise KubeBaseError("'current-context' needs to be set within .kube/config")
        else:
            self.current_context = config["current-context"]

        # Gather the context and cluster details of .kube/config based upon the current_context
        kubeconfig_context = self._contexts()[self.current_context]
        kubeconfig_cluster = kubeconfig_context['cluster']
        self.cluster = self._clusters()[kubeconfig_cluster]

        # Gather cluster information (certificate authority)
        if "certificate-authority" in self.cluster:
            self.certificate_authority = self.cluster["certificate-authority"]

        if "insecure-skip-tls-verify" in self.cluster:
            self.insecure_skip_tls_verify = self.cluster["insecure-skip-tls-verify"]

        # If a 'user' is present, gather the information in order to retrieve the token(s),
        # certificate(s) as well as client-key. A user is OPTIONAL in the .kube/config data
        # and hence the if statement.
        if "user" in kubeconfig_context:

            kubeconfig_user = kubeconfig_context['user']
            self.user = self._users()[kubeconfig_user]

            if "token" in self.user:
                self.token = self.user['token']

            if "client-certificate" in self.user:
                self.client_certification = self.user['client-certificate']

            if "client-key" in self.user:
                self.client_key = self.user['client-key']

        # Initialize the connection using all the .kube/config credentials
        self.api = self._connection()

    def request(self, method, url, data=None):
        '''
        Completes the request to the API and fails if the status_code is != 200/201

        Args:
            method (str): put/get/post/patch
            url (str): url of the api call
            data (object): object of the data that is being passed (will be converted to json)
        '''
        status_code = None
        return_data = None

        try:
            res = self._request_method(method, url, data)
            status_code = res.status_code
            return_data = res.json()
        except requests.exceptions.ConnectTimeout:
            msg = "Timeout when connecting to  %s" % url
            raise KubeConnectionError(msg)
        except requests.exceptions.ReadTimeout:
            msg = "Timeout when reading from %s" % url
            raise KubeConnectionError(msg)
        except requests.exceptions.ConnectionError:
            msg = "Refused connection to %s" % url
            raise KubeConnectionError(msg)
        except SSLError:
            raise KubeConnectionError("SSL/TLS ERROR: invalid certificate")
        except ValueError:
            return_data = None

        # 200 = OK
        # 201 = PENDING
        # EVERYTHING ELSE == FAIL
        if status_code is not 200 and status_code is not 201:
            raise KubeConnectionError("Unable to complete request: Status: %s, Error: %s"
                                      % (status_code, return_data))
        return return_data

    def websocket_request(self, url, outfile=None):
        '''
        Due to the requests library not supporting SPDY, websocket(s) are required
        to communicate to the API.

        Args:
            url (str): URL of the API
            outfile (str): path of the outfile/data.
        '''
        url = 'wss://' + url.split('://', 1)[-1]
        logger.debug('Converted http to wss url: %s', url)
        results = []

        ws = websocket.WebSocketApp(
            url,
            on_message=lambda ws, message: self._handle_exec_reply(ws, message, results, outfile))

        ws.run_forever(sslopt={
            'ca_certs': self.cert_ca if self.cert_ca is not None else ssl.CERT_NONE,
            'cert_reqs': ssl.CERT_REQUIRED if self.insecure_skip_tls_verify else ssl.CERT_NONE})

        # If an outfile was not provided, return the results in its entirety
        if not outfile:
            return ''.join(results)

    def get_groups(self, url):
        '''
        Get the groups of APIs available.
        '''
        data = self.request("get", url)
        groups = data["groups"] or []
        groups = [(group['name'], [i['version'] for i in group['versions']]) for group in groups]
        return groups

    def get_resources(self, url):
        '''
        Get the resources available to the API. This is a list of all available
        API calls that can be made to the API.
        '''
        data = self.request("get", url)
        resources = data["resources"] or []
        resources = [res['name'] for res in resources]
        return resources

    def test_connection(self, url):
        self.api.request("get", url)
        logger.debug("Connection successfully tested on URL %s" % url)

    @staticmethod
    def cert_file(data, key):
        '''
        Some certificate .kube/config components are required to be a filename.

        Returns either the filename or a tmp location of said data in a file.
        All certificates used with Kubernetes are base64 encoded and thus need to be decoded

        Keys which have "-data" associated with the name are base64 encoded. All others are not.
        '''

        # If it starts with /, we assume it's a filename so we just return that.
        if data.startswith('/'):
            return data

        # If it's data, we assume it's a certificate and we decode and write to a tmp file
        # If the base64 param has been passed as true, we decode the data.
        else:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                # If '-data' is included in the keyname, it's a base64 encoded string and
                # is required to be decoded
                if "-data" in key:
                    f.write(base64.b64decode(data))
                else:
                    f.write(data)
                return f.name

    @staticmethod
    def kind_to_resource_name(kind):
        """
        Converts kind to resource name. It is same logics
        as in k8s.io/k8s/pkg/api/meta/restmapper.go (func KindToResource)
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
        if singular.endswith(("s", "x", "z", "ch", "sh")):
            plural = singular + "es"
        else:
            if singular[-1] == "s":
                plural = singular
            elif singular[-1] == "y":
                plural = singular.rstrip("y") + "ies"
            else:
                plural = singular + "s"
        return plural

    def _contexts(self):
        '''
        Parses the contexts and formats it in a name = object way.
        ex.
            'foobar': { name: 'foobar', context: 'foo' }
        '''
        contexts = {}
        if "contexts" not in self.kubeconfig:
            raise KubeBaseError("No contexts within the .kube/config file")
        for f in self.kubeconfig["contexts"]:
            contexts[f["name"]] = f["context"]
        return contexts

    def _clusters(self):
        '''
        Parses the clusters and formats it in a name = object way.
        ex.
            'foobar': { name: 'foobar', cluster: 'foo' }
        '''
        clusters = {}
        if "clusters" not in self.kubeconfig:
            raise KubeBaseError("No clusters within the .kube/config file")
        for f in self.kubeconfig["clusters"]:
            clusters[f["name"]] = f["cluster"]
        return clusters

    def _users(self):
        '''
        Parses the users and formats it in a name = object way.
        ex.
            'foobar': { name: 'foobar', user: 'foo' }
        '''
        users = {}
        if "users" not in self.kubeconfig:
            raise KubeBaseError("No users within the .kube/config file")
        for f in self.kubeconfig["users"]:
            users[f["name"]] = f["user"]
        return users

    def _connection(self):
        '''
        Initializes the required requests session certs / token / authentication
        in order to communicate with the API
        '''
        connection = requests.Session()

        # CA Certificate for TLS verification
        if self.certificate_authority:
            connection.verify = self.cert_file(
                self.certificate_authority,
                "certificate-authority")

        # Check to see if verification has been disabled, if it has
        # disable tls-verification
        if self.insecure_skip_tls_verify:
            connection.verify = False
            # Disable the 'InsecureRequestWarning' notifications.
            # As per: https://github.com/kennethreitz/requests/issues/2214
            # Instead make a large one-time noticable warning instead
            requests.packages.urllib3.disable_warnings()
            logger.warning("CAUTION: TLS verification has been DISABLED")
        else:
            logger.debug("Verification will be required for all API calls")

        # If we're using a token, use it, otherwise it's assumed the user uses
        # client-certificate and client-key
        if self.token:
            connection.headers["Authorization"] = "Bearer %s" % self.token

        # Lastly, if we have client-certificate and client-key in the .kube/config
        # we add them to the connection as a cert
        if self.client_certification and self.client_key:
            connection.cert = (
                self.cert_file(self.client_certification, "client-certificate"),
                self.cert_file(self.client_key, "client-key")
            )

        return connection

    def _handle_ws_reply(self, ws, message, results, outfile=None):
        """
        Handle websocket reply messages for each exec call
        """
        # FIXME: For some reason, we do not know why,  we need to ignore the
        # 1st char of the message, to generate a meaningful result
        cleaned_msg = message[1:]
        if outfile:
            with open(outfile, 'ab') as f:
                f.write(cleaned_msg)
        else:
            results.append(cleaned_msg)

    def _request_method(self, method, url, data):
        '''
        Converts the method to the most appropriate request and calls it.

        Args:
            method (str): put/get/post/patch
            url (str): url of the api call
            data (object): object of the data that is being passed (will be converted to json)
        '''
        if method.lower() == "get":
            res = self.api.get(url, json=data)
        elif method.lower() == "post":
            res = self.api.post(url, json=data)
        elif method.lower() == "put":
            res = self.api.put(url, json=data)
        elif method.lower() == "delete":
            res = self.api.delete(url, json=data)
        elif method.lower() == "patch":
            headers = {"Content-Type": "application/json-patch+json"}
            res = self.api.patch(url, json=data, headers=headers)
        return res
