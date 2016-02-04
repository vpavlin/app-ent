import mock
import unittest
from atomicapp.nulecule.base import Nulecule


class TestNuleculeRun(unittest.TestCase):

    """Test Nulecule run"""

    def test_run(self):
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

    def test_stop(self):
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

        n = Nulecule(id='some-id', specversion='0.0.2', metadata={}, graph=[], basepath='some/path')
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

        n = Nulecule(id='some-id', specversion='0.0.2', metadata={}, graph=[],
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

        n = Nulecule(id='some-id', specversion='0.0.2', metadata={}, graph=[],
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

        n = Nulecule('some-id', '0.0.2', graph, 'some/path', {})
        n.load_components()

        MockNuleculeComponent.assert_any_call(
            graph[0]['name'], n.basepath, 'somecontainer',
            graph[0]['params'], None, {})
        MockNuleculeComponent.assert_any_call(
            graph[1]['name'], n.basepath, None,
            graph[1].get('params'), graph[1].get('artifacts'), {})


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
