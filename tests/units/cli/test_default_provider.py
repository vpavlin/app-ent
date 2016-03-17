import os
import sys
import pytest

import atomicapp.cli.main


class TestCli(object):
    # We're using object instead of UnitTest for this in order to use capsys effectively

    def exec_cli(self, command):
        saved_args = sys.argv
        sys.argv = command
        atomicapp.cli.main.main()
        sys.argv = saved_args

    def set_up(self):
        self.examples_dir = os.path.dirname(__file__) + '/test_examples/'

    def tear_down(self):
        top = os.path.dirname(__file__) + '/test_examples/'
        for root, dirs, files in os.walk(top):
            for f in files:
                if f.startswith('.'):
                    os.remove(os.path.join(root, f))
                elif f == "answers.conf.gen":
                    os.remove(os.path.join(root, f))

    def test_run_helloapache_app(self, capsys):
        # Let's set this example up!
        self.set_up()

        # Prepare the CLI arguments
        command = [
            "main.py",
            "--verbose",
            "--dry-run",
            "run",
            self.examples_dir + 'oneprovider-helloapache/'
        ]

        # Run the dry-run command
        with pytest.raises(SystemExit) as exec_info:
            self.exec_cli(command)
        stdout, stderr = capsys.readouterr()

        # Tear down and remove all those useless generated files
        self.tear_down()

        # Print out what we've captured just in case the test fails
        print stdout

        # Since this a Docker-only provider test, docker *should* be in it, NOT Kubernetes
        assert "u'provider': u'docker'" in stdout
        assert "Deploying to Kubernetes" not in stdout

        assert exec_info.value.code == 0
