import os
import unittest

import mock
import pytest

from atomicapp.nulecule.base import Nulecule
from atomicapp.nulecule.exceptions import NuleculeException


class TestNuleculeRun(unittest.TestCase):

    """Test Nulecule run"""

    @staticmethod
    def test_run():
        provider = 'docker'
        dryrun = False
        mock_component_1 = mock.Mock()
        mock_component_2 = mock.Mock()

        n = Nulecule('some-id', '0.0.2', [{}], 'some/path', {})
        n.components = [mock_component_1, mock_component_2]
        n.run(provider)

        mock_component_1.run.assert_called_once_with(provider, dryrun)
        mock_component_2.run.assert_called_once_with(provider, dryrun)


class TestNuleculeStop(unittest.TestCase):

    """Test Nulecule stop"""

    @staticmethod
    def test_stop():
        provider = 'docker'
        dryrun = False
        mock_component_1 = mock.Mock()
        mock_component_2 = mock.Mock()

        n = Nulecule('some-id', '0.0.2', {}, [], 'some/path')
        n.components = [mock_component_1, mock_component_2]
        n.stop(provider)

        mock_component_1.stop.assert_called_once_with(provider, dryrun)
        mock_component_2.stop.assert_called_once_with(provider, dryrun)


class TestNuleculeLoadConfig(unittest.TestCase):

    """Test Nulecule load_config"""

    def test_load_config_without_specified_provider(self):
        """
        Test Nulecule load_config without specifying a provider.
        """
        config = {'general': {}, 'group1': {'a': 'b'}}
        mock_component_1 = mock.Mock()
        mock_component_1.config = {
            'group1': {'a': 'c', 'k': 'v'},
            'group2': {'1': '2'}
        }

        n = Nulecule(id='some-id', specversion='0.0.2', metadata={}, basepath='some/path')
        n.components = [mock_component_1]
        n.load_config(config)

        self.assertEqual(n.config, {
            'general': {'provider': 'kubernetes'},
            'group1': {'a': 'b', 'k': 'v'},
            'group2': {'1': '2'}
        })

    def test_load_config_with_defaultprovider(self):
        """
        Test Nulecule load_config with default provider specified
        in global params in Nulecule spec.
        """
        config = {'general': {}, 'group1': {'a': 'b'}}
        mock_component_1 = mock.Mock()
        mock_component_1.config = {
            'group1': {'a': 'c', 'k': 'v'},
            'group2': {'1': '2'}
        }

        n = Nulecule(id='some-id', specversion='0.0.2', metadata={},
                     basepath='some/path',
                     params=[{'name': 'provider', 'default': 'some-provider'}])
        n.components = [mock_component_1]
        n.load_config(config)

        self.assertEqual(n.config, {
            'general': {'provider': 'some-provider'},
            'group1': {'a': 'b', 'k': 'v'},
            'group2': {'1': '2'}
        })

    def test_load_config_with_defaultprovider_overridden_by_provider_in_answers(self):
        """
        Test Nulecule load_config with default provider specified
        in global params in Nulecule spec, but overridden in answers config.
        """
        config = {'general': {'provider': 'new-provider'},
                  'group1': {'a': 'b'}}
        mock_component_1 = mock.Mock()
        mock_component_1.config = {
            'group1': {'a': 'c', 'k': 'v'},
            'group2': {'1': '2'}
        }

        n = Nulecule(id='some-id', specversion='0.0.2', metadata={},
                     basepath='some/path',
                     params=[{'name': 'provider', 'default': 'some-provider'}])
        n.components = [mock_component_1]
        n.load_config(config)

        self.assertEqual(n.config, {
            'general': {'provider': 'new-provider'},
            'group1': {'a': 'b', 'k': 'v'},
            'group2': {'1': '2'}
        })


class TestNuleculeLoadComponents(unittest.TestCase):

    """Test loading Nulecules for a Nulecule"""

    @staticmethod
    @mock.patch('atomicapp.nulecule.base.Nulecule')
    def test_load_components(MockNulecule):
        graph = [
            {
                'name': 'app1',
                'source': 'docker://somecontainer',
                'params': []
            },
            {
                'name': 'app2',
                'artifacts': [
                    {'a': 'b'}
                ]
            }
        ]

        n = Nulecule('some-id', '0.0.2', graph, 'some/path', {})
        n.load_components()

        MockNulecule.assert_any_call(
            graph[0]['name'], n.basepath, 'somecontainer',
            graph[0]['params'], None, {})
        MockNulecule.assert_any_call(
            graph[1]['name'], n.basepath, None,
            graph[1].get('params'), graph[1].get('artifacts'), {})


class TestNuleculeRender(unittest.TestCase):

    """Test Nulecule render"""

    @staticmethod
    def test_render():
        mock_component_1 = mock.Mock()
        mock_component_2 = mock.Mock()
        provider_key = 'foo'

        n = Nulecule('some-id', '0.0.2', {}, [], 'some/path', progenitor=True)
        n.components = [mock_component_1, mock_component_2]
        n.render(provider_key)

        mock_component_1.render.assert_called_once_with(
            provider_key=provider_key)
        mock_component_2.render.assert_called_once_with(
            provider_key=provider_key)


class TestLoadNuleculeParsing(unittest.TestCase):

    @staticmethod
    def test_missing_nulecule():
        n = Nulecule('some-id', '0.0.2', {}, [], 'some/path')
        with pytest.raises(NuleculeException):
            n.load_from_path(src='foo/bar')

    @staticmethod
    def test_invalid_nulecule_format():
        n = Nulecule('some-id', '0.0.2', {}, [], 'some/path')
        with pytest.raises(NuleculeException):
            n.load_from_path(src=os.path.dirname(__file__) + '/invalid_nulecule/')
