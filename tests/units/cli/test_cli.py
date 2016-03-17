import os
import sys
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
            json.loads(myjson)
        except ValueError:
            return False
        return True

    def setUp(self):
        self.examples_dir = os.path.dirname(__file__) + '/test_examples/'

    @classmethod
    def tearDownClass(cls):
        top = os.path.dirname(__file__) + '/test_examples/'
        for root, dirs, files in os.walk(top):
            for f in files:
                if f.startswith('.'):
                    os.remove(os.path.join(root, f))
                elif f == "answers.conf.gen":
                    os.remove(os.path.join(root, f))

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

    def test_fetch_helloapache_app(self):
        command = [
            "main.py",
            "--verbose",
            "--answers-format=json",
            "--dry-run",
            "fetch",
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

    def test_run_helloapache_app_marathon(self):
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "run",
            "--provider=marathon",
            self.examples_dir + 'helloapache'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

    def test_fetch_helloapache_app_docker(self):
        command = [
            "main.py",
            "--verbose",
            "--answers-format=json",
            "--dry-run",
            "fetch",
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
            "stop",
            self.examples_dir + 'wordpress-centos7-atomicapp/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

    def test_run_k8s_app_multiple_artifacts(self):
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "run",
            "--provider=docker",
            self.examples_dir + 'kubernetes-atomicapp/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

    def test_stop_k8s_app_multiple_artifacts(self):
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "stop",
            "--provider=docker",
            self.examples_dir + 'kubernetes-atomicapp/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0
