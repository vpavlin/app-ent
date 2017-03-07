import unittest
import pytest
import tempfile
import os
from atomicapp.plugin import ProviderFailedException
from atomicapp.providers.lib.kubeshift.kubeconfig import KubeConfig


class TestKubeConfParsing(unittest.TestCase):

    def test_from_file(self):
        """
        Test parsing a hello world JSON example and returning back the
        respective anymarkup content
        """
        _, tmpfilename = tempfile.mkstemp()
        f = open(tmpfilename, 'w')
        f.write("{ 'hello': 'world'}")
        f.close()
        KubeConfig.from_file(tmpfilename)

    def test_from_params(self):
        KubeConfig.from_params("foo", "bar", "foo", "bar")

    def test_parse_kubeconf_from_file_failure(self):
        _, tmpfilename = tempfile.mkstemp()
        f = open(tmpfilename, 'w')
        f.write("{ 'hello': 'world'}")
        f.close()
        with pytest.raises(KeyError):
            KubeConfig.parse_kubeconf(tmpfilename)

    def test_parse_kubeconf_from_file(self):
        example_kubeconfig = os.path.dirname(__file__) + '/external/example_kubeconfig'
        KubeConfig.parse_kubeconf(example_kubeconfig)

    def test_parse_kubeconf_data_insecure(self):
        """
        Test parsing kubeconf data with current context containing
        cluster, user, namespace info and skipping tls verification
        """
        kubecfg_data = {
            'current-context': 'context2',
            'contexts': [
                {
                    'name': 'context1',
                },
                {
                    'name': 'context2',
                    'context': {
                        'cluster': 'cluster1',
                        'user': 'user1',
                        'namespace': 'namespace1'
                    }
                }
            ],
            'clusters': [
                {
                    'name': 'cluster1',
                    'cluster': {
                        'insecure-skip-tls-verify': 'true',
                        'server': 'server1'
                    }
                }
            ],
            'users': [
                {
                    'name': 'user1',
                    'user': {
                        'token': 'token1'
                    }
                }
            ]
        }

        self.assertEqual(KubeConfig.parse_kubeconf_data(kubecfg_data),
                         {'provider-api': 'server1',
                          'provider-auth': 'token1',
                          'namespace': 'namespace1',
                          'provider-tlsverify': False,
                          'provider-cafile': None})

    def test_parse_kubeconf_data_cafile(self):
        """
        Test parsing kubeconf data with current context containing
        cluster, user, namespace info and certificate-authority
        """
        kubecfg_data = {
            'current-context': 'context2',
            'contexts': [
                {
                    'name': 'context1',
                },
                {
                    'name': 'context2',
                    'context': {
                        'cluster': 'cluster1',
                        'user': 'user1',
                        'namespace': 'namespace1'
                    }
                }
            ],
            'clusters': [
                {
                    'name': 'cluster1',
                    'cluster': {
                        'certificate-authority': '/foo/bar',
                        'server': 'server1'
                    }
                }
            ],
            'users': [
                {
                    'name': 'user1',
                    'user': {
                        'token': 'token1'
                    }
                }
            ]
        }

        self.assertEqual(KubeConfig.parse_kubeconf_data(kubecfg_data),
                         {'provider-api': 'server1',
                          'provider-auth': 'token1',
                          'namespace': 'namespace1',
                          'provider-tlsverify': True,
                          'provider-cafile': '/foo/bar'})

    def test_parse_kubeconf_data_no_context(self):
        """
        Test parsing kubeconf data with missing context data for
        current context.
        """
        kubecfg_data = {
            'current-context': 'context2',
            'contexts': [
                {
                    'name': 'context1',
                }
            ],
            'clusters': [
                {
                    'name': 'cluster1',
                    'cluster': {
                        'server': 'server1'
                    }
                }
            ],
            'users': [
                {
                    'name': 'user1',
                    'user': {
                        'token': 'token1'
                    }
                }
            ]
        }

        self.assertRaises(ProviderFailedException,
                          KubeConfig.parse_kubeconf_data, kubecfg_data)

    def test_parse_kubeconf_data_no_user(self):
        """
        Test parsing kubeconf data with missing user data in current
        context.
        """
        kubecfg_data = {
            'current-context': 'context2',
            'contexts': [
                {
                    'name': 'context1',
                },
                {
                    'name': 'context2',
                    'context': {
                        'cluster': 'cluster1',
                        'user': 'user1',
                        'namespace': 'namespace1'
                    }
                }
            ],
            'clusters': [
                {
                    'name': 'cluster1',
                    'cluster': {
                        'server': 'server1'
                    }
                }
            ],
            'users': [
            ]
        }

        self.assertRaises(ProviderFailedException,
                          KubeConfig.parse_kubeconf_data, kubecfg_data)
