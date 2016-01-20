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

import unittest
import pytest

import atomicapp.cli.main


class TestGitLabCli(unittest.TestCase):

    def exec_cli(self, command):
        saved_args = sys.argv
        sys.argv = command
        atomicapp.cli.main.main()
        sys.argv = saved_args

    def setUp(self):
        self.examples_dir = os.path.dirname(__file__) + '/test_examples/'
        self.answers_conf = os.path.join(
            self.examples_dir,
            "gitlab/answers.conf.sample")

        # "work dir" of the kubernetes artifacts
        self.work_dir = os.path.join(
            self.examples_dir,
            "gitlab/artifacts/kubernetes/")

        # A list of artifacts that should be there during install / run / stop
        self.artifacts_array = [
            "gitlab-http-service.json",
            ".gitlab-http-service.json",
            "gitlab-rc.json",
            ".gitlab-rc.json",
            "postgres-rc.json",
            ".postgres-rc.json",
            "postgres-service.json",
            ".postgres-service.json",
            "redis-rc.json",
            ".redis-rc.json",
            "redis-service.json",
            ".redis-service.json"]

    # Remove the examples answers.conf file as well as the dotfiles created
    def tearDown(self):
        if os.path.isfile(self.answers_conf):
            os.remove(self.answers_conf)

    @classmethod
    def tearDownClass(cls):
        top = os.path.dirname(__file__) + '/test_examples/'
        for root, dirs, files in os.walk(top):
            for f in files:
                if f.startswith('.'):
                    os.remove(os.path.join(root, f))
                elif f == "answers.conf.gen":
                    os.remove(os.path.join(root, f))

    # Installs the gitlab example similarly to `test_cli.py` examples
    def test_fetch_gitlab_app(self):
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "fetch",
            self.examples_dir + 'gitlab/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

    # When running, we check that the multiple artifacts are created / there in the folder
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

        assert set(os.listdir(self.work_dir)) == \
            set(self.artifacts_array)

    # Similarly to run, we stop the atomicapp and check to see if the artifacts include the dotfiles
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

        assert set(os.listdir(self.work_dir)) == \
            set(self.artifacts_array)
