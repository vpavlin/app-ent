import mock
import unittest
import pytest
import os
from atomicapp.nulecule.base import Nulecule
from atomicapp.nulecule.exceptions import NuleculeException
from atomicapp.nulecule.config import Config


class TestNuleculeRun(unittest.TestCase):

    """Test Nulecule run"""

    def test_run(self):
        provider = 'docker'
        dryrun = False
        mock_component_1 = mock.Mock()
        mock_component_2 = mock.Mock()
        config = Config(answers={})

        n = Nulecule('some-id', '0.0.2', [{}], 'some/path', {}, config=config)
        n.components = [mock_component_1, mock_component_2]
        n.run(provider)

        mock_component_1.run.assert_called_once_with(provider, dryrun)
        mock_component_2.run.assert_called_once_with(provider, dryrun)


class TestNuleculeStop(unittest.TestCase):

    """Test Nulecule stop"""

    def test_stop(self):
        provider = 'docker'
        dryrun = False
        mock_component_1 = mock.Mock()
        mock_component_2 = mock.Mock()

        config = Config(answers={})

        n = Nulecule('some-id', '0.0.2', {}, [], 'some/path', config=config)
        n.components = [mock_component_1, mock_component_2]
        n.stop(provider)

        mock_component_1.stop.assert_called_once_with(provider, dryrun)
        mock_component_2.stop.assert_called_once_with(provider, dryrun)


class TestNuleculeLoadConfig(unittest.TestCase):

    """Test Nulecule load_config"""

    def test_load_config_with_default_provider(self):
        """
        Test Nulecule load_config with a default provider.
        """
        config = Config(answers={})

        params = [
            {
                "name": "key1",
                "default": "val1",
            },
            {
                "name": "key3",
                "default": "val3"
            },
            {
                "name": "provider",
                "default": "docker"
            }
        ]

        graph = [
            {
                "name": "component1",
                "params": [
                    {
                        "name": "key1",
                    },
                    {
                        "name": "key2",
                        "default": "val2"
                    }
                ],
                "artifacts": []
            }
        ]

        n = Nulecule(id='some-id', specversion='0.0.2', metadata={},
                     graph=graph, params=params, basepath='some/path',
                     config=config)
        n.load_components()
        n.load_config(config)

        self.assertEqual(n.config.runtime_answers(), {
            'general': {
                'namespace': 'default',
                'provider': 'docker',
                'key1': 'val1',
                'key3': 'val3'
            },
            'component1': {
                'key2': 'val2'
            }
        })

        self.assertEqual(
            n.components[0].config.context(scope=n.components[0].namespace),
            {'key3': 'val3',
             'key2': 'val2',
             'key1': 'val1',
             'provider': 'docker',
             'namespace': 'default'}
        )

    def test_load_config_without_default_provider(self):
        """
        Test Nulecule load_config without specifying a default provider.
        """
        config = Config()

        params = [
            {
                "name": "key1",
                "default": "val1",
            },
            {
                "name": "key3",
                "default": "val3"
            }
        ]

        graph = [
            {
                "name": "component1",
                "params": [
                    {
                        "name": "key1",
                    },
                    {
                        "name": "key2",
                        "default": "val2"
                    }
                ],
                "artifacts": []
            }
        ]

        n = Nulecule(id='some-id', specversion='0.0.2', metadata={},
                     graph=graph, params=params, basepath='some/path',
                     config=config)
        n.load_components()
        n.load_config()

        self.assertEqual(n.config.runtime_answers(), {
            'general': {
                'namespace': 'default',
                'provider': 'kubernetes',
                'key1': 'val1',
                'key3': 'val3'
            },
            'component1': {
                'key2': 'val2'
            }
        })

        self.assertEqual(
            n.components[0].config.context(n.components[0].namespace),
            {'key3': 'val3',
             'key2': 'val2',
             'key1': 'val1',
             'namespace': 'default',
             'provider': 'kubernetes'}
        )

    def test_load_config_with_default_provider_overridden_by_answers(self):
        """
        Test Nulecule load_config with default provider overridden by provider
        in answers.
        """
        config = Config(answers={
            'general': {
                'provider': 'openshift'
            }
        })

        params = [
            {
                "name": "key1",
                "default": "val1",
            },
            {
                "name": "key3",
                "default": "val3"
            },
            {
                "name": "provider",
                "default": "docker"
            }
        ]

        graph = [
            {
                "name": "component1",
                "params": [
                    {
                        "name": "key1",
                    },
                    {
                        "name": "key2",
                        "default": "val2"
                    }
                ],
                "artifacts": []
            }
        ]

        n = Nulecule(id='some-id', specversion='0.0.2', metadata={},
                     graph=graph, params=params, basepath='some/path',
                     config=config)
        n.load_components()
        n.load_config(config)

        self.assertEqual(n.config.runtime_answers(), {
            'general': {
                'namespace': 'default',
                'provider': 'openshift',
                'key1': 'val1',
                'key3': 'val3'
            },
            'component1': {
                'key2': 'val2'
            }
        })

        self.assertEqual(
            n.components[0].config.context(n.components[0].namespace),
            {'key3': 'val3',
             'key2': 'val2',
             'key1': 'val1',
             'namespace': 'default',
             'provider': 'openshift'}
        )


class TestNuleculeLoadComponents(unittest.TestCase):

    """Test loading NuleculeComponents for a Nulecule"""

    @mock.patch('atomicapp.nulecule.base.NuleculeComponent')
    def test_load_components(self, MockNuleculeComponent):
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

        config = Config(answers={})

        n = Nulecule('some-id', '0.0.2', graph, 'some/path', config=config)
        n.load_components()

        MockNuleculeComponent.assert_any_call(
            graph[0]['name'], n.basepath, 'somecontainer',
            graph[0]['params'], None, config)
        MockNuleculeComponent.assert_any_call(
            graph[1]['name'], n.basepath, None,
            graph[1].get('params'), graph[1].get('artifacts'), config)


class TestNuleculeRender(unittest.TestCase):

    """Test Nulecule render"""

    def test_render(self):
        mock_component_1 = mock.Mock()
        mock_component_2 = mock.Mock()
        provider_key = 'foo'
        dryrun = True

        n = Nulecule('some-id', '0.0.2', {}, [], 'some/path')
        n.components = [mock_component_1, mock_component_2]
        n.render(provider_key, dryrun)

        mock_component_1.render.assert_called_once_with(
            provider_key=provider_key, dryrun=dryrun)
        mock_component_2.render.assert_called_once_with(
            provider_key=provider_key, dryrun=dryrun)


class TestLoadNuleculeParsing(unittest.TestCase):

    def test_missing_nulecule(self):
        n = Nulecule('some-id', '0.0.2', {}, [], 'some/path')
        with pytest.raises(NuleculeException):
            n.load_from_path(src='foo/bar')

    def test_invalid_nulecule_format(self):
        n = Nulecule('some-id', '0.0.2', {}, [], 'some/path')
        with pytest.raises(NuleculeException):
            n.load_from_path(src=os.path.dirname(__file__) + '/invalid_nulecule/')
