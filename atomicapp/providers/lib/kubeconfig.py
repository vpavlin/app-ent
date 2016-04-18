import anymarkup
import os
from base64 import b64decode

from atomicapp.plugin import ProviderFailedException
from atomicapp.constants import (PROVIDER_AUTH_KEY,
                                 LOGGER_DEFAULT,
                                 NAMESPACE_KEY,
                                 PROVIDER_API_KEY,
                                 PROVIDER_TLS_VERIFY_KEY,
                                 PROVIDER_CA_KEY)
import logging
from atomicapp.utils import Utils
logger = logging.getLogger(LOGGER_DEFAULT)


class KubeConfig(object):

    @staticmethod
    def parse_kubeconf(filename):
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
            return KubeConfig.parse_kubeconf_data(kubecfg)
        except ProviderFailedException:
            raise ProviderFailedException('Invalid %s' % filename)

    @staticmethod
    def parse_kubeconf_data(kubecfg):
        """
        Parse kubeconf data.

        Args:
            kubecfg (dict): Kubernetes config data

        Returns:
            dict of parsed values from config
        """
        url = None
        auth = None
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
        auth = user["user"].get("token")
        namespace = context["context"].get("namespace")
        tls_verify = not cluster["cluster"].get("insecure-skip-tls-verify")

        if tls_verify:
            ca_data = cluster["cluster"].get("certificate-authority-data")
            if ca_data:
                ca = Utils.getTmpFile(b64decode(ca_data))
            else:
                if "certificate-authority" in cluster["cluster"]:
                    # if we are in container translate path to path on host
                    ca = os.path.join(Utils.getRoot(),
                                      cluster["cluster"].get("certificate-authority").lstrip('/'))

        if not auth:
            # If token not specified, check for certificate auth.

            # client-certificate-data and client-key-data options overrides
            # client-certificate and client-key
            # https://github.com/kubernetes/kubernetes/blob/v1.2.2/pkg/client/unversioned/clientcmd/api/types.go#L78
            # `{client-certificate,client-key}-data` keys in Kubernetes config
            # file are inline base64 encoded certificates, requests library
            # requires certs in files, this is why we are putting them to tmp
            # files.

            cert_data = user["user"].get("client-certificate-data")
            key_data = user["user"].get("client-key-data")

            if cert_data:
                cert = Utils.getTmpFile(b64decode(cert_data))
            else:
                if "client-certificate" in user["user"]:
                    cert = os.path.join(Utils.getRoot(),
                                        user["user"].get("client-certificate").lstrip('/'))

            if key_data:
                key = Utils.getTmpFile(b64decode(key_data))
            else:
                if "client-key" in user["user"]:
                    key = os.path.join(Utils.getRoot(),
                                       user["user"].get("client-key").lstrip('/'))

            auth = "{}:{}".format(cert, key)

        return {PROVIDER_API_KEY: url,
                PROVIDER_AUTH_KEY: auth,
                NAMESPACE_KEY: namespace,
                PROVIDER_TLS_VERIFY_KEY: tls_verify,
                PROVIDER_CA_KEY: ca}
