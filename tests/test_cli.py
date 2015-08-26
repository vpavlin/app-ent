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

__author__ = "goern"

import os
import sys
import logging

import pytest
import json

import atomicapp.cli.main

logger = logging.getLogger('atomicapp.tests')
tests_root = os.path.dirname(os.path.dirname(__file__)) + '/tests/'

# TEST-SUITE SETUP
def setup_module(module):
    return

def teardown_module(module):
    return

# TESTS
class TestCLISuite(object):
    # this is how we call the CLI...

    def exec_cli(self, command):
        saved_args = sys.argv
        sys.argv = command
        atomicapp.cli.main.main()
        sys.argv = saved_args

    def is_json(self, myjson):
        try:
            json_object = json.loads(myjson)
        except ValueError, e:
            return False
        return True

    # lets test if we can run a simple atomicapp
    def test_run_with_helloapache(self):
            # prepare the atomicapp command to dry run
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "run",
            tests_root + 'cached_nulecules/helloapache/'
        ]

        # run the command and check if it was successful
        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

    # lets test if we can install a simple atomicapp
    def test_install_with_helloapache(self):
        # prepare the atomicapp command to dry run
        command = [
            "main.py",
            "--verbose",
            "--answers-format=json",
            "--dry-run",
            "install",
            tests_root + 'cached_nulecules/helloapache/'
        ]

        # run the command and check if it was successful
        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        json_data = open(tests_root + "cached_nulecules/helloapache/answers.conf.sample").read()

        assert exec_info.value.code == 0
        assert self.is_json(json_data)

    # test it with the famous WordPress Nulecule
    # wordpress-centos7-atomicapp
    def test_run_with_wordpress_centos7_atomicapp(self):
        # prepare the atomicapp command to dry run
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "run",
            tests_root + 'cached_nulecules/wordpress-centos7-atomicapp/'
        ]

        # run the command and check if it was successful
        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

    # lets test the stop command with the wordpress-centos7-atomicapp
    # wordpress-centos7-atomicapp
    def test_stop_with_wordpress_app(self):
        # prepare the atomicapp command to dry run
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "run",
            tests_root + 'cached_nulecules/wordpress-centos7-atomicapp/'
        ]

        # run the command and check if it was successful
        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "stop",
            tests_root + 'cached_nulecules/wordpress-centos7-atomicapp/'
        ]

        # run the command and check if it was successful
        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0
