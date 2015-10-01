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

from atomicapp.run import Run
from atomicapp.install import Install
import os
import sys

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import logging
from lockfile import LockFile
from lockfile import AlreadyLocked

from atomicapp.constants import \
    ANSWERS_FILE, __ATOMICAPPVERSION__, \
    __NULECULESPECVERSION__, ANSWERS_FILE_SAMPLE_FORMAT, \
    LOCK_FILE
from atomicapp.utils import Utils
from atomicapp.display import Display, set_logging


def cli_install(args):
    install = Install(**vars(args))

    if install.install() is not None:
        sys.exit(True)
    else:
        sys.exit(False)


def cli_run(args):
    ae = Run(**vars(args))

    if ae.run() is not None:
        sys.exit(True)
    else:
        sys.exit(False)


def cli_stop(args):
    stop = Run(stop=True, **vars(args))

    if stop.run() is not None:
        sys.exit(True)
    else:
        sys.exit(False)


class CLI():

    def __init__(self):
        self.parser = ArgumentParser(
            prog='atomicapp',
            description=(
                "This will install and run an Atomic App, "
                "a containerized application conforming to the Nulecule Specification"),
            formatter_class=RawDescriptionHelpFormatter)
        self.display = Display()

    def set_arguments(self):

        self.parser.add_argument(
            "-V",
            "--version",
            action='version',
            version='atomicapp %s, Nulecule Specification %s' % (
                __ATOMICAPPVERSION__, __NULECULESPECVERSION__),
            help="show the version and exit.")
        # TODO refactor program name and version to some globals

        self.parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            default=False,
            action="store_true",
            help="Verbose output mode.")

        self.parser.add_argument(
            "-q",
            "--quiet",
            dest="quiet",
            default=False,
            action="store_true",
            help="Quiet output mode.")

        self.parser.add_argument(
            "--dry-run",
            dest="dryrun",
            default=False,
            action="store_true",
            help=(
                "Don't actually call provider. The commands that should be "
                "run will be sent to stdout but not run."))

        self.parser.add_argument(
            "-a",
            "--answers",
            dest="answers",
            default=os.path.join(os.getcwd(), ANSWERS_FILE),
            help="Path to %s" % ANSWERS_FILE)

        self.parser.add_argument(
            "--answers-format",
            dest="answers_format",
            default=ANSWERS_FILE_SAMPLE_FORMAT,
            help=(
                "The format for the answers.conf.sample file.Default is "
                "'ini', Valid formats are 'ini', 'json', 'xml', 'yaml'."))

        subparsers = self.parser.add_subparsers(dest="action")

        parser_run = subparsers.add_parser("run")
        parser_run.add_argument(
            "--write-answers",
            dest="answers_output",
            help="A file which will contain anwsers provided in interactive mode")

        parser_run.add_argument(
            "--provider",
            dest="cli_provider",
            choices=['docker', 'kubernetes', 'openshift'],
            help="The provider to use. Overrides provider value in answerfile.")

        parser_run.add_argument(
            "--ask",
            default=False,
            action="store_true",
            help="Ask for params even if the defaul value is provided")

        parser_run.add_argument(
            "APP",
            help="Path to the directory where the image is installed.")

        parser_run.set_defaults(func=cli_run)

        parser_install = subparsers.add_parser("install")

        parser_install.add_argument(
            "--no-deps",
            dest="nodeps",
            default=False,
            action="store_true",
            help="Skip pulling dependencies of the app")

        parser_install.add_argument(
            "-u",
            "--update",
            dest="update",
            default=False,
            action="store_true",
            help="Re-pull images and overwrite existing files")

        parser_install.add_argument(
            "--destination",
            dest="target_path",
            default=None,
            help="Destination directory for install")

        parser_install.add_argument(
            "APP",
            help=(
                "Application to run. This is a container image or a path "
                "that contains the metadata describing the whole application."))

        parser_install.set_defaults(func=cli_install)

        parser_stop = subparsers.add_parser("stop")
        parser_stop.add_argument(
            "--provider",
            dest="cli_provider",
            choices=['docker', 'kubernetes', 'openshift'],
            help="The provider to use. Overrides provider value in answerfile.")

        parser_stop.add_argument(
            "APP",
            help=(
                "Path to the directory where the Atomic App is installed or "
                "an image containing an Atomic App which should be stopped."))

        parser_stop.set_defaults(func=cli_stop)

    def run(self):
        self.set_arguments()
        args = self.parser.parse_args()
        if args.verbose:
            set_logging(level=logging.DEBUG)
        elif args.quiet:
            set_logging(level=logging.WARNING)
        else:
            set_logging(level=logging.INFO)

        lock = LockFile(os.path.join(Utils.getRoot(), LOCK_FILE))
        try:
            lock.acquire(timeout=-1)
            args.func(args)
        except AttributeError:
            if hasattr(args, 'func'):
                raise
            else:
                self.parser.print_help()
        except KeyboardInterrupt:
            pass
        except AlreadyLocked:
            self.display.error("Could not proceed - there is probably another instance of Atomic App running on this machine.")
        except Exception as ex:
            if args.verbose:
                raise
            else:
                self.display.error("Exception caught: %s" % repr(ex))
                self.display.error("Run the command again with -v option to get more information.")
        finally:
            if lock.i_am_locking():
                lock.release()


def main():
    cli = CLI()
    cli.run()

if __name__ == '__main__':
    main()
