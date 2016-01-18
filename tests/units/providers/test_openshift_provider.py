# -*- coding: utf-8 -*-
"""
Unittests for atomicapp/providers/openshift.py

We test most functionalities of OpenshiftProvider by
mocking out OpenshiftClient which interacts with
the external world openshift and kubernetes API.
"""

import unittest
import mock
from atomicapp.providers.openshift import OpenShiftProvider
from atomicapp.plugin import ProviderFailedException


class OpenshiftProviderTestMixin(object):

    def setUp(self):
        # Patch OpenshiftClient to test OpenShiftProvider
        self.patcher = mock.patch('atomicapp.providers.openshift.OpenshiftClient')
        self.mock_OpenshiftClient = self.patcher.start()
        self.mock_oc = self.mock_OpenshiftClient()

    def get_oc_provider(self, dryrun=False, artifacts=[]):
        """
        Get OpenShiftProvider instance
        """
        op = OpenShiftProvider({}, '.', dryrun)
        op.artifacts = artifacts
        op.access_token = 'test'
        op.init()
        return op

    def tearDown(self):
        self.patcher.stop()


class TestOpenshiftProviderDeploy(OpenshiftProviderTestMixin, unittest.TestCase):
    """
    Test OpenShiftProvider.run
    """

    def test_run(self):
        """
        Test calling OpenshiftClient.run from OpenShiftProvider.run
        """
        op = self.get_oc_provider()
        op.oapi_resources = ['foo']
        op.openshift_artifacts = {
            'pods': [
                {
                    'metadata': {
                        'namespace': 'foo'
                    }
                }
            ]
        }

        op.run()

        self.mock_oc.deploy.assert_called_once_with(
            'namespaces/foo/pods/?access_token=test',
            op.openshift_artifacts['pods'][0])

    def test_run_dryrun(self):
        """
        Test running OpenShiftProvider.run as dryrun
        """
        op = self.get_oc_provider(dryrun=True)
        op.oapi_resources = ['foo']
        op.openshift_artifacts = {
            'pods': [
                {
                    'metadata': {
                        'namespace': 'foo'
                    }
                }
            ]
        }

        op.run()

        self.assertFalse(self.mock_oc.run.call_count)

class TestOpenshiftProviderUnrun(OpenshiftProviderTestMixin, unittest.TestCase):
    """
    Test OpenShiftProvider.stop
    """

    def test_stop(self):
        """
        Test calling OpenshiftClient.delete from OpenShiftProvider.stop
        """
        op = self.get_oc_provider()
        op.oapi_resources = ['foo']
        op.openshift_artifacts = {
            'pods': [
                {
                    'kind': 'Pod',
                    'metadata': {
                        'name': 'bar',
                        'namespace': 'foo'
                    }
                }
            ]
        }

        op.stop()

        self.mock_oc.delete.assert_called_once_with(
            'namespaces/foo/pods/%s?access_token=test' %
            op.openshift_artifacts['pods'][0]['metadata']['name'])

    def test_stop_dryrun(self):
        """
        Test running OpenShiftProvider.stop as dryrun
        """
        op = self.get_oc_provider(dryrun=True)
        op.oapi_resources = ['foo']
        op.openshift_artifacts = {
            'pods': [
                {
                    'kind': 'Pod',
                    'metadata': {
                        'name': 'bar',
                        'namespace': 'foo'
                    }
                }
            ]
        }

        op.stop()

        self.assertFalse(self.mock_oc.delete.call_count)

class TestOpenshiftProviderProcessArtifactData(OpenshiftProviderTestMixin, unittest.TestCase):
    """
    Test processing Openshift artifact data
    """

    def test_process_artifact_data_non_template_kind(self):
        """
        Test processing non template artifact data
        """
        artifact_data = {
            'kind': 'Pod',
            'pods': [
                {
                    'metadata': {
                        'namespace': 'foo'
                    }
                }
            ]
        }
        self.mock_oc.get_oapi_resources.return_value = ['pods']

        op = self.get_oc_provider()

        op._process_artifact_data('foo', artifact_data)

        self.assertEqual(op.openshift_artifacts,
                         {'pod': [artifact_data]})

    def test_process_artifact_data_template_kind(self):
        """
        Test processing non template artifact data
        """
        artifact_data = {
            'kind': 'Template',
            'objects': [
                {
                    'kind': 'Pod',
                    'metadata': {
                        'namespace': 'foo'
                    }
                },
                {
                    'kind': 'Service',
                    'metadata': {
                        'namespace': 'foo'
                    }
                }
            ]
        }
        self.mock_oc.get_oapi_resources.return_value = ['templates']
        op = self.get_oc_provider()
        self.mock_oc.process_template.return_value = artifact_data['objects']

        op._process_artifact_data('foo', artifact_data)

        self.assertEqual(
            op.openshift_artifacts, {
                'pod': [
                    {'kind': 'Pod', 'metadata': {'namespace': 'foo'}}
                ],
                'service': [
                    {'kind': 'Service', 'metadata': {'namespace': 'foo'}}
                ]
            }
        )

    def test_process_artifact_data_error_resource_not_in_resources(self):
        """
        Test processing artifact data with kind not in resources
        """
        artifact_data = {
            'kind': 'foobar'
        }

        op = self.get_oc_provider()

        self.assertRaises(
            ProviderFailedException,
            op._process_artifact_data, 'foo', artifact_data)

    def test_process_artifact_data_error_kind_key_missing(self):
        """
        Test processing artifact data with missing key 'kind'
        """
        artifact_data = {}
        op = self.get_oc_provider()

        self.assertRaises(
            ProviderFailedException,
            op._process_artifact_data, 'foo', artifact_data)


class TestOpenshiftProviderParseKubeconfData(OpenshiftProviderTestMixin, unittest.TestCase):

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

        op = self.get_oc_provider()
        self.assertEqual(op._parse_kubeconf_data(kubecfg_data),
                         {'providerapi': 'server1',
                          'accesstoken': 'token1',
                          'namespace': 'namespace1',
                          'providertlsverify': False,
                          'providercafile': None})

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

        op = self.get_oc_provider()
        self.assertEqual(op._parse_kubeconf_data(kubecfg_data),
                         {'providerapi': 'server1',
                          'accesstoken': 'token1',
                          'namespace': 'namespace1',
                          'providertlsverify': True,
                          'providercafile': '/foo/bar'})

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

        op = self.get_oc_provider()
        self.assertRaises(ProviderFailedException,
                          op._parse_kubeconf_data, kubecfg_data)

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

        op = self.get_oc_provider()
        self.assertRaises(ProviderFailedException,
                          op._parse_kubeconf_data, kubecfg_data)
