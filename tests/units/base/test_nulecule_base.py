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
from atomicapp.nulecule_base import Nulecule_Base

class TestNuleculeBase(unittest.TestCase):

    def setUp(self):
        self.nulecule_base = Nulecule_Base(
            dryrun=True,
            cli_provider="kubernetes")

    def tearDown(self):
        pass

    def test_answers_config(self):
        data = {'general': {'namespace': 'testing', 'provider': 'kubernetes'}}
        self.nulecule_base.loadAnswers(data)
        config = self.nulecule_base.getValues()
        self.assertEqual(config["namespace"], "testing")

    def test_answers_config_with_skip(self):
        data = {'general': {'namespace': 'testing', 'provider': 'kubernetes'}}
        self.nulecule_base.loadAnswers(data)
        config = self.nulecule_base.getValues(skip_asking=True)
        self.assertEqual(config["namespace"], "testing")
