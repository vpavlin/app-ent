import copy
import mock
import unittest
from atomicapp.nulecule.base import NuleculeComponent, Nulecule
from atomicapp.nulecule.exceptions import NuleculeException


class TestNuleculeComponentLoadArtifactPathsForPath(unittest.TestCase):
    """Test loading artifacts from an artifact path"""

    @mock.patch('atomicapp.nulecule.base.os.path.isfile')
    def test_file_path(self, mock_os_path_isfile):
        mock_os_path_isfile.return_value = True

        nc = NuleculeComponent('some-name', 'some/path')

        self.assertEqual(
            nc._get_artifact_paths_for_path('some/path/to/file'),
            ['some/path/to/file'])

    @mock.patch('atomicapp.nulecule.base.os.listdir')
    @mock.patch('atomicapp.nulecule.base.os.path.isdir')
    @mock.patch('atomicapp.nulecule.base.os.path.isfile')
    def test_dir_path(self, mock_os_path_isfile, mock_os_path_isdir,
                      mock_os_listdir):
        mock_os_path_isfile.return_value = False
        mock_os_path_isdir.side_effect = lambda path: True if path.endswith('dir') else False
        mock_os_listdir.return_value = [
            '.foo',
            'some-dir',
            'file1',
            'file2'
        ]

        nc = NuleculeComponent('some-name', 'some/path')

        self.assertEqual(
            nc._get_artifact_paths_for_path('artifacts-dir'),
            ['artifacts-dir/file1', 'artifacts-dir/file2'])


class TestNuleculeComponentLoad(unittest.TestCase):

    @mock.patch('atomicapp.nulecule.base.NuleculeComponent.load_external_application')
    def test_load_without_nodeps(self, mock_load_external_application):
        dryrun = False

        nc = NuleculeComponent('some-name', 'some/path', source='blah')
        nc.load(False, dryrun)

        mock_load_external_application.assert_called_once_with(dryrun)

    @mock.patch(
        'atomicapp.nulecule.base.NuleculeComponent.load_external_application')
    def test_load_with_nodeps(self, mock_load_external_application):
        dryrun = False

        nc = NuleculeComponent('some-name', 'some/path', source='blah')
        nc.load(True, dryrun)

        self.assertEqual(mock_load_external_application.call_count, 0)


class TestNuleculeComponentRun(unittest.TestCase):
    """Test Nulecule component run"""

    def test_run_external_app(self):
        mock_nulecule = mock.Mock(name='nulecule')
        dryrun = False

        nc = NuleculeComponent('some-name', 'some/path')
        nc._app = mock_nulecule
        nc.run('some-provider', dryrun)

        mock_nulecule.run.assert_called_once_with('some-provider', dryrun)

    @mock.patch('atomicapp.nulecule.base.NuleculeComponent.get_provider')
    def test_run_local_artifacts(self, mock_get_provider):
        mock_provider = mock.Mock(name='provider')
        mock_get_provider.return_value = ('some-provider-x', mock_provider)
        dryrun = False
        provider_key = 'some-provider'

        nc = NuleculeComponent('some-name', 'some/path')
        nc.rendered_artifacts = {'some-provider-x': ['a', 'b', 'c']}
        nc.run(provider_key, dryrun)

        mock_get_provider.assert_called_once_with(provider_key, dryrun)
        self.assertEqual(mock_provider.artifacts, ['a', 'b', 'c'])
        mock_provider.init.assert_called_once_with()
        mock_provider.run.assert_called_once_with()


class TestNuleculeComponentStop(unittest.TestCase):
    """Test Nulecule component stop"""

    def test_stop_external_app(self):
        """Test stopping an external application"""
        mock_nulecule = mock.Mock(name='nulecule')
        dryrun = False

        nc = NuleculeComponent('some-name', 'some/path')
        nc._app = mock_nulecule
        nc.stop('some-provider', dryrun)

        mock_nulecule.stop.assert_called_once_with('some-provider', dryrun)

    @mock.patch('atomicapp.nulecule.base.NuleculeComponent.get_provider')
    def test_stop_local_app(self, mock_get_provider):
        """Test stopping a local application"""
        dryrun = False
        provider_key = 'some-provider'
        mock_provider = mock.Mock(name='provider')
        mock_get_provider.return_value = ('some-provider-x', mock_provider)

        nc = NuleculeComponent('some-name', 'some/path')
        nc.rendered_artifacts = {'some-provider-x': ['a', 'b', 'c']}
        nc.stop(provider_key, dryrun)

        mock_get_provider.assert_called_once_with(provider_key, dryrun)
        self.assertEqual(mock_provider.artifacts, ['a', 'b', 'c'])
        mock_provider.init.assert_called_once_with()
        mock_provider.stop.assert_called_once_with()


class TestNuleculeComponentLoadConfig(unittest.TestCase):
    """Test loading config for a Nulecule component"""

    def test_load_config_local_app(self):
        """Test load config for local app"""
        params = [
            {'name': 'key1'},
            {'name': 'key2'}
        ]
        initial_config = {
            'general': {'a': 'b', 'key2': 'val2'},
            'some-app': {'key1': 'val1'}
        }

        nc = NuleculeComponent('some-app', 'some/path', params=params)
        nc.load_config(config=copy.deepcopy(initial_config))

        self.assertEqual(nc.config, {
            'general': {'a': 'b', 'key2': 'val2'},
            'some-app': {'key1': 'val1', 'key2': 'val2'}
        })

    @mock.patch('atomicapp.nulecule.base.NuleculeComponent.merge_config')
    def test_load_config_external_app(self, mock_merge_config):
        """Test load config for external app"""
        mock_nulecule = mock.Mock(
            name='nulecule',
            spec=Nulecule('some-id', '0.0.2', {}, [], 'some/path')
        )
        params = [
            {'name': 'key1'},
            {'name': 'key2'}
        ]
        initial_config = {
            'general': {'a': 'b', 'key2': 'val2'},
            'some-app': {'key1': 'val1'}
        }

        nc = NuleculeComponent('some-app', 'some/path', params=params)
        nc._app = mock_nulecule
        nc.load_config(config=copy.deepcopy(initial_config))

        mock_nulecule.load_config.assert_called_once_with(
            config={
                'general': {'a': 'b', 'key2': 'val2'},
                'some-app': {'key1': 'val1', 'key2': 'val2'}
            }, ask=False, skip_asking=False)
        mock_merge_config.assert_called_once_with(
            nc.config, mock_nulecule.config)


class TestNuleculeComponentLoadExternalApplication(unittest.TestCase):
    """
    Test loading an external Nulecule application from a Nulecule
    component.
    """

    @mock.patch('atomicapp.nulecule.base.Nulecule')
    @mock.patch('atomicapp.nulecule.base.os.path.isdir')
    def test_loading_existing_app(self, mock_os_path_isdir, mock_Nulecule):
        dryrun, update = False, False
        mock_os_path_isdir.return_value = True
        expected_external_app_path = 'some/path/external/some-app'

        nc = NuleculeComponent('some-app', 'some/path')
        nc.load_external_application(dryrun=dryrun, update=update)

        mock_os_path_isdir.assert_called_once_with(
            expected_external_app_path)
        mock_Nulecule.load_from_path.assert_called_once_with(
            expected_external_app_path, dryrun=dryrun, update=update)

    @mock.patch('atomicapp.nulecule.base.Nulecule')
    @mock.patch('atomicapp.nulecule.base.os.path.isdir')
    def test_loading_app_by_unpacking(self, mock_os_path_isdir,
                                      mock_Nulecule):
        dryrun, update = False, False
        mock_os_path_isdir.return_value = False
        expected_external_app_path = 'some/path/external/some-app'

        nc = NuleculeComponent('some-app', 'some/path')
        nc.load_external_application(dryrun=dryrun, update=update)

        mock_os_path_isdir.assert_called_once_with(
            expected_external_app_path)
        mock_Nulecule.unpack.assert_called_once_with(
            nc.source, expected_external_app_path,
            namespace=nc.namespace, config=None, dryrun=dryrun, update=update)


class TestNuleculeComponentComponents(unittest.TestCase):
    """Test accessing components attribute of a Nulecule component"""

    def test_components_for_local_app(self):
        nc = NuleculeComponent('some-app', 'some/path')

        self.assertFalse(nc.components)

    def test_components_for_external_app(self):
        nc = NuleculeComponent('some-app', 'some/path')
        nc._app = mock.Mock(name='nulecule')
        nc._app.components = ['a', 'b', 'c']

        self.assertEqual(nc.components, ['a', 'b', 'c'])


class TestNuleculeComponentRender(unittest.TestCase):
    """Test rendering artifacts for a Nulecule component"""

    def test_render_for_external_app(self):
        """Test rendering a nulecule component pointing to an external app"""
        mock_nulecule = mock.Mock(name='nulecule')
        provider_key = 'some-provider'
        dryrun = False

        nc = NuleculeComponent(name='some-app', basepath='some/path')
        nc._app = mock_nulecule
        nc.render(provider_key, dryrun)

        mock_nulecule.render.assert_called_once_with(
            provider_key=provider_key, dryrun=dryrun)

    def test_render_for_local_app_with_missing_artifacts_for_provider(self):
        """
        Test rendering a Nulecule component with missing artifacts for a
        provider.
        """
        provider_key = 'some-provider'
        dryrun = False

        nc = NuleculeComponent(name='some-app', basepath='some/path')
        nc.config = {}
        nc.artifacts = {'x': ['some-artifact']}

        self.assertRaises(NuleculeException, nc.render, provider_key, dryrun)

    @mock.patch('atomicapp.nulecule.base.NuleculeComponent.get_context')
    @mock.patch('atomicapp.nulecule.base.NuleculeComponent.'
                'get_artifact_paths_for_provider')
    @mock.patch('atomicapp.nulecule.base.NuleculeComponent.render_artifact')
    def test_render_for_local_app_with_artifacts_for_provider(
            self, mock_render_artifact, mock_get_artifact_paths_for_provider,
            mock_get_context):
        """Test rendering artifacts for a local Nulecule component"""
        provider_key = 'some-provider'
        dryrun = False
        expected_rendered_artifacts = [
            'some/path/.artifact1', 'some/path/.artifact2']
        context = {'a': 'b'}
        mock_get_artifact_paths_for_provider.return_value = [
            'some/path/artifact1', 'some/path/artifact2']
        mock_render_artifact.side_effect = lambda path, context, provider: path.replace('artifact', '.artifact')
        mock_get_context.return_value = context

        nc = NuleculeComponent(name='some-app', basepath='some/path')
        nc.config = {'general': {'key1': 'val1'}, 'some-provider': {'a': 'b'}}
        nc.artifacts = {
            'some-provider': ['artifact1', 'artifact2'],
            'x': ['foo']
        }
        nc.render(provider_key, dryrun)

        mock_get_artifact_paths_for_provider.assert_called_once_with(
            provider_key)
        mock_render_artifact.assert_any_call('some/path/artifact1', context,
                                             'some-provider')
        mock_render_artifact.assert_any_call('some/path/artifact2', context,
                                             'some-provider')
        mock_get_artifact_paths_for_provider.assert_called_once_with(
            provider_key)
        self.assertEqual(nc.rendered_artifacts[provider_key],
                         expected_rendered_artifacts)


class TestNuleculeComponentGetArtifactPathsForProvider(unittest.TestCase):
    """Test creating artifact paths for a Nulecule component"""

    @mock.patch('atomicapp.nulecule.base.NuleculeComponent.'
                '_get_artifact_paths_for_path')
    def test_artifact_paths_for_provider(
            self, mock_get_artifact_paths_for_path):
        provider_key = 'some-provider'
        expected_artifact_paths = [
            'some/path/relative/path/to/artifact1',
            '/abs/path/to/artifact2',
            'some/path/x/artifact3'
        ]
        mock_get_artifact_paths_for_path.side_effect = lambda path: [path]

        nc = NuleculeComponent(name='some-app', basepath='some/path')
        nc.artifacts = {
            provider_key: [
                'file://relative/path/to/artifact1',
                'file:///abs/path/to/artifact2',
                {
                    'inherit': ['x-provider']
                }
            ],
            'x-provider': [
                'file://x/artifact3'
            ]
        }

        self.assertEqual(nc.get_artifact_paths_for_provider(provider_key),
                         expected_artifact_paths)


class TestNuleculeComponentRenderArtifact(unittest.TestCase):
    """Test rendering an artifact in a NuleculeComponent"""

    @mock.patch('atomicapp.nulecule.base.open', create=True)
    def test_render_artifact(self, mock_open):
        source_content = 'some text: $key1'
        expected_rendered_content = 'some text: val1'
        context = {'key1': 'val1'}

        # Mock context for opening file.
        mock_open_source_file_context = mock.MagicMock(
            name='source_artifact_context')
        mock_open_target_file_context = mock.MagicMock(
            name='target_artifact_context')

        # Mock file objects
        mock_source_file = mock_open_source_file_context.__enter__()
        mock_target_file = mock_open_target_file_context.__enter__()
        mock_source_file.read.return_value = source_content

        def mock_open_resp(path, mode):
            if path == 'some/path/artifact':
                return mock_open_source_file_context
            elif path == 'some/path/.artifact':
                return mock_open_target_file_context

        mock_open.side_effect = mock_open_resp

        nc = NuleculeComponent(name='some-name', basepath='some/path')
        nc.artifacts = {'some-provider': [{}]}

        self.assertEqual(
            nc.render_artifact('some/path/artifact', context, 'some-provider'),
            '.artifact')
        mock_source_file.read.assert_called_once_with()
        mock_target_file.write.assert_called_once_with(
            expected_rendered_content)
