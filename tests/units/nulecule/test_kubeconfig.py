import unittest
from atomicapp.plugin import ProviderFailedException
from atomicapp.providers.lib.kubeconfig import KubeConfig
import base64


class TestKubeConfParsing(unittest.TestCase):

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

    def test_parse_kubeconf_data_cafile_data(self):
        """
        Test parsing kubeconf data with current context containing
        cluster, user, namespace info and certificate-authority-data
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
                        'certificate-authority-data': base64.b64encode("foobar"),
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

        result = KubeConfig.parse_kubeconf_data(kubecfg_data)

        self.assertDictContainsSubset({'provider-api': 'server1',
                                       'provider-auth': 'token1',
                                       'namespace': 'namespace1',
                                       'provider-tlsverify': True},
                                      result)

        # verify content of ca file
        ca_content = open(result['provider-cafile']).read()
        self.assertEqual(ca_content, "foobar")

    def test_parse_kubeconf_data_client_cert(self):
        """
        Test parsing kubeconf data with current context containing
        cluster, user, namespace info and client-certificate and key
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

                        'client-certificate': '/foo/ca',
                        'client-key': '/foo/key'
                    }
                }
            ]
        }

        self.assertEqual(KubeConfig.parse_kubeconf_data(kubecfg_data),
                         {'provider-api': 'server1',
                          'provider-auth': '/foo/ca:/foo/key',
                          'namespace': 'namespace1',
                          'provider-tlsverify': True,
                          'provider-cafile': '/foo/bar'})

    def test_parse_kubeconf_data_client_cert_data(self):
        """
        Test parsing kubeconf data with current context containing
        cluster, user, namespace info and client-certificate-data and key
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
                        'certificate-authority-data': base64.b64encode("foobar"),
                        'server': 'server1'
                    }
                }
            ],
            'users': [
                {
                    'name': 'user1',
                    'user': {
                        'client-certificate-data': base64.b64encode("cert"),
                        'client-key-data': base64.b64encode("key")
                    }
                }
            ]
        }

        result = KubeConfig.parse_kubeconf_data(kubecfg_data)

        self.assertDictContainsSubset({'provider-api': 'server1',
                                       'namespace': 'namespace1',
                                       'provider-tlsverify': True},
                                      result)

        # verify content of ca file
        ca_content = open(result['provider-cafile']).read()
        self.assertEqual(ca_content, "foobar")

        # verify content client ca and key
        client_ca_file, client_key_file = result['provider-auth'].split(":")
        client_ca_content = open(client_ca_file).read()
        client_key_content = open(client_key_file).read()
        self.assertEqual(client_ca_content, "cert")
        self.assertEqual(client_key_content, "key")

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
