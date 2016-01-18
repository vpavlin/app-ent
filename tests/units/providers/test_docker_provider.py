"""
 Copyright 2015 Red Hat, Inc.

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
import pytest
import mock
import tempfile
import os
import json
from atomicapp.plugin import Plugin, ProviderFailedException
from atomicapp.nulecule.lib import NuleculeBase
from atomicapp.providers.docker import DockerProvider
from atomicapp.constants import DEFAULT_CONTAINER_NAME, DEFAULT_NAMESPACE

def mock_name_get_call(self):
    return ["test_centos-httpd_e9b9a7bfe8f9"]

class TestDockerProviderBase(unittest.TestCase):
    
    # Create a temporary directory for our setup as well as load the required providers
    def setUp(self):
        self.nulecule_base = NuleculeBase(params = [], basepath = os.getcwd(), namespace = "test")
        self.tmpdir = tempfile.mkdtemp(prefix = "atomicapp-test", dir = "/tmp")
        self.artifact_dir = os.path.dirname(__file__) + '/docker_artifact_test/'

    def tearDown(self):
        pass
    
    # Lets prepare the docker provider with pre-loaded configuration and use the DockerProvider
    def prepare_provider(self, data):
        self.nulecule_base.load_config(data)
        config = self.nulecule_base.config
        provider = DockerProvider(config, self.tmpdir, dryrun = True)
        return provider

    # Test deploying multiple artifacts within docker
    def test_multiple_artifact_load(self):
        data = {'namespace': 'test', 'provider': 'docker'}
        provider = self.prepare_provider(data)
        provider.init()
        provider.artifacts = [
                self.artifact_dir + 'hello-world-one',
                self.artifact_dir + 'hello-world-two',
                self.artifact_dir + 'hello-world-three'
                ]
        # Mock the effects of 'docker ps -a'. As if each deployment adds the container to the host
        mock_container_list = mock.Mock(side_effect = [
            ["test_fedora-httpd_e9b9a7bfe8f9"], 
            ["test_fedora-httpd_e9b9a7bfe8f9", "test_centos-httpd_e9b9a7bfe8f9"],
            ["test_fedora-httpd_e9b9a7bfe8f9", "test_centos-httpd_e9b9a7bfe8f9", "test_centos-httpd_e9b9a7bfe8f9"]
            ])
        with mock.patch("atomicapp.providers.docker.DockerProvider._get_containers", mock_container_list):
            provider.run()

   
    # Patch in a general container list and make sure it fails if there is already a container with the same name 
    @mock.patch("atomicapp.providers.docker.DockerProvider._get_containers", mock_name_get_call)
    def test_namespace_name_check(self):
        data = {'namespace': 'test', 'provider': 'docker', 'image': 'centos/httpd'}
        provider = self.prepare_provider(data)
        provider.init()
        provider.artifacts = [self.artifact_dir + 'hello-world-one']
        with pytest.raises(ProviderFailedException):
            provider.run()
