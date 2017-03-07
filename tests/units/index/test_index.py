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
import os
import tempfile

from atomicapp.index import Index


def mock_index_load_call(self, test):
    self.index = {'location': '.', 'nulecules': [
        {'providers': ['docker'], 'id': 'test', 'metadata':{'appversion': '0.0.1', 'location': 'foo'}}]}


class TestIndex(unittest.TestCase):

    """
    Tests the index
    """

    # Tests listing the index with a patched self.index
    @mock.patch("atomicapp.index.Index._load_index_file", mock_index_load_call)
    def test_list(self):
        a = Index()
        a.list()

    # Test generation with current test_examples in cli
    @mock.patch("atomicapp.index.Index._load_index_file", mock_index_load_call)
    def test_generate(self):
        self.tmpdir = tempfile.mkdtemp(prefix="atomicapp-generation-test", dir="/tmp")
        a = Index()
        a.generate("tests/units/cli/test_examples", os.path.join(self.tmpdir, "index.yaml"))
