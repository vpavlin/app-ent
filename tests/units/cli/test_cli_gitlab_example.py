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

import unittest
import pytest

import atomicapp.cli.main
from atomicapp.constants import WORKDIR

class TestGitLabCli(unittest.TestCase):

    def exec_cli(self, command):
        saved_args = sys.argv
        sys.argv = command
        atomicapp.cli.main.main()
        sys.argv = saved_args

    def setUp(self):
        logger = logging.getLogger('atomicapp.tests')
        self.examples_dir = os.path.dirname(__file__) + '/test_examples/'
        self.work_dir = os.path.join(
                self.examples_dir,
                "gitlab/%s" % WORKDIR)

        if os.path.isdir(self.work_dir):
           shutil.rmtree(self.work_dir)

    def tearDown(self):
        if os.path.isdir(self.work_dir):
           shutil.rmtree(self.work_dir)

    def test_install_gitlab_app(self):
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "install",
            self.examples_dir + 'gitlab/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

        work_dir = os.path.join(
            self.examples_dir,
            "gitlab/%s" % WORKDIR)

        assert os.path.isdir(work_dir) == False

    def test_run_gitlab_app(self):
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "run",
            self.examples_dir + 'gitlab/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

        work_dir = os.path.join(
            self.examples_dir,
            "gitlab/%s" % WORKDIR)
        assert set(os.listdir(work_dir)) == \
            set(["gitlab", "postgresql", "redis"])

    def test_stop_gitlab_app(self):
        self.test_run_gitlab_app()
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "stop",
            self.examples_dir + 'gitlab/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

        work_dir = os.path.join(
            self.examples_dir,
            "gitlab/%s" % WORKDIR)
        assert set(os.listdir(work_dir)) == \
            set(["gitlab", "postgresql", "redis"])

