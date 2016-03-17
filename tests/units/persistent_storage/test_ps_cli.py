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

    def test_run_k8s_persistent_storage(self):
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "run",
            "--provider=kubernetes",
            self.examples_dir + 'ps-helloapache/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0

    def test_stop_k8s_persistent_storage(self):
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "stop",
            "--provider=kubernetes",
            self.examples_dir + 'ps-helloapache/'
        ]

        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)

        assert exec_info.value.code == 0
