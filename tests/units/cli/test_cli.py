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

import os
import sys
import logging
import shutil
import json

import unittest
import pytest

import atomicapp.cli.main

class TestCli(unittest.TestCase):

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

    def setUp(self):
        logger = logging.getLogger('atomicapp.tests')
        self.examples_dir = os.path.dirname(__file__) + '/test_examples/'

    def tearDown(self):
        pass

    def test_run_helloapache_app(self):
        # Prepare the CLI arguments
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "run",
            self.examples_dir + 'helloapache/'
        ]
        
        # Run the dry-run command
        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

    def test_install_helloapache_app(self):
        command = [
            "main.py",
            "--verbose",
            "--answers-format=json",
            "--dry-run",
            "install",
            self.examples_dir + 'helloapache/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        json_data = open(self.examples_dir + "helloapache/answers.conf.sample").read()

        assert exec_info.value.code == 0
        assert self.is_json(json_data)

    def test_run_helloapache_app_docker(self):
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "run",
            "--provider=docker",
            self.examples_dir + 'helloapache/'
        ]
        
        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

    def test_install_helloapache_app_docker(self):
        command = [
            "main.py",
            "--verbose",
            "--answers-format=json",
            "--dry-run",
            "install",
            self.examples_dir + 'helloapache/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        json_data = open(self.examples_dir + "helloapache/answers.conf.sample").read()

        assert exec_info.value.code == 0
        assert self.is_json(json_data)

    def test_stop_helloapache_app_docker(self):
        command = [
            "main.py",
            "--verbose",
            "--answers-format=json",
            "--dry-run",
            "stop",
            "--provider=docker",
            self.examples_dir + 'helloapache/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        json_data = open(self.examples_dir + "helloapache/answers.conf.sample").read()

        assert exec_info.value.code == 0
        assert self.is_json(json_data)

    def test_run_wordpress_app(self):
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "run",
            self.examples_dir + 'wordpress-centos7-atomicapp/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

    def test_stop_wordpress_app(self):
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "run",
            self.examples_dir + 'wordpress-centos7-atomicapp/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "stop",
            self.examples_dir + 'wordpress-centos7-atomicapp/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

