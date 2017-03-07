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

import unittest
import mock
import tempfile
import os
import json
from atomicapp.plugin import Plugin, ProviderFailedException
from atomicapp.nulecule.lib import NuleculeBase
from atomicapp.providers.kubernetes import KubernetesProvider

MOCK_CONTENT = "mock_provider_call_content"

class TestKubernetesProviderBase(unittest.TestCase):

    # Create a temporary directory for our setup as well as load the required providers
    def setUp(self):
        self.nulecule_base = NuleculeBase(params = [], basepath = os.getcwd(), namespace = "test")
        self.tmpdir = tempfile.mkdtemp(prefix = "atomicapp-test", dir = "/tmp")
        self.artifact_dir = os.path.dirname(__file__) + '/docker_artifact_test/'

    def tearDown(self):
        pass

    def create_temp_file(self):
        return tempfile.mktemp(prefix = "test-config", dir = self.tmpdir)

    # Lets prepare the docker provider with pre-loaded configuration and use the KubernetesProvider
    def prepare_provider(self, data):
        self.nulecule_base.load_config(data)
        config = self.nulecule_base.config
        provider = KubernetesProvider(config, self.tmpdir, dryrun = True)
        return provider

    # Check that the provider configuration file exists
    def test_provider_config_exist(self):
        provider_config_path = self.create_temp_file()
        mock_content = "%s_%s" % (MOCK_CONTENT, "_unchanged")
        with open(provider_config_path, "w") as fp:
            fp.write(mock_content)

        data = {'namespace': 'testing', 'provider': 'kubernetes', 'provider-config': provider_config_path}
        
        provider = self.prepare_provider(data)

        self.assertEqual(provider.config_file, provider_config_path)
        provider.checkConfigFile()  # should exist since we just created it
        with open(provider_config_path, "r") as fp:
            self.assertEqual(fp.read(), mock_content)

    # If we call checkConfigFile but do not provide a configuration file: fail
    def test_provider_check_config_fail(self):
        path = self.create_temp_file()
        data = {'namespace': 'testing', 'provider': 'openshift'}
        provider = self.prepare_provider(data)
        self.assertRaises(ProviderFailedException, provider.checkConfigFile)
