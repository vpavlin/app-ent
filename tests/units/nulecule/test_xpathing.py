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

import os
import unittest

import mock
import pytest

from atomicapp.nulecule.base import Nulecule
from atomicapp.nulecule.exceptions import NuleculeException

def mock_params_get_call():
    return {"image": ["/spec/containers/0/image", "/metadata/labels/app"],
            "host": ["/spec/containers/0/ports/0/hostPort"]}

class TestNuleculeXpathing(unittest.TestCase):

    # Create a temporary directory for our setup as well as load the required Nulecule
    def setUp(self):
        self.example_dir = os.path.dirname(__file__) + '/artifact_xpath_test/'
        self.artifact_path = os.path.dirname(__file__) + '/artifact_xpath_test/xpath.json'
        self.artifact_content = open(self.artifact_path, 'r').read()
        self.test = Nulecule('some-id', '0.0.2', basepath=self.example_dir, params=None)

    def tearDown(self):
        pass

    # Let's check to see that xpathing is actually working. Fake the params get call
    @mock.patch("atomicapp.nulecule.base.Nulecule.grab_artifact_params", mock_params_get_call)
    def test_xpathing_parse(self):
        self.test.apply_pointers(content=self.artifact_content, params={"image": ["/spec/containers/0/image"]})

    # Fail if we're unable to replace the /spec/containers/1/image pointer
    @mock.patch("atomicapp.nulecule.base.Nulecule.grab_artifact_params", mock_params_get_call)
    def test_xpathing_not_found(self):
        with pytest.raises(NuleculeException):
            self.test.apply_pointers(content=self.artifact_content, params={"image": ["/spec/containers/1/image"]})

    # Test using the artifact path
    def test_artifact_path(self):
        self.test.artifacts = {"docker": [{"file://artifacts/docker/hello-apache-pod_run"}], "kubernetes": [{"file://artifacts/kubernetes/hello-apache-pod.json"}]}
        self.test.get_artifact_paths_for_provider("kubernetes")

    # Test the artifact with the "resource: " pointer
    def test_artifact_path_with_resource(self):
        self.test.artifacts = {"docker": [{"resource":"file://artifacts/docker/hello-apache-pod_run"}], "kubernetes": [{"resource":"file://artifacts/kubernetes/hello-apache-pod.json"}]}
        self.test.get_artifact_paths_for_provider("kubernetes")

    # Test combination of using "resource" and not
    def test_artifact_path_with_resource_and_old(self):
        self.test.artifacts = {"docker": [{"resource":"file://artifacts/docker/hello-apache-pod_run"}], "kubernetes": [{"file://artifacts/kubernetes/hello-apache-pod.json"}]}
        self.test.get_artifact_paths_for_provider("kubernetes")

