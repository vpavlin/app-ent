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

import os
import sys

import argparse
import logging

from atomicapp.applogging import Logging
from atomicapp.constants import (__ATOMICAPPVERSION__,
                                 __NULECULESPECVERSION__,
                                 ANSWERS_FILE,
                                 ANSWERS_FILE_SAMPLE_FORMAT,
                                 APP_ENT_PATH,
                                 CACHE_DIR,
                                 HOST_DIR,
                                 LOGGER_DEFAULT,
                                 PROVIDERS)
from atomicapp.nulecule import NuleculeManager
from atomicapp.nulecule.exceptions import NuleculeException, DockerException
from atomicapp.plugin import ProviderFailedException
from atomicapp.utils import Utils
from atomicapp.index import Index

logger = logging.getLogger(LOGGER_DEFAULT)


def print_app_location(app_path):
    if app_path.startswith(HOST_DIR):
        app_path = app_path[len(HOST_DIR):]
    print("\nYour application resides in %s" % app_path)
    print("Please use this directory for managing your application")


def cli_genanswers(args):
    argdict = args.__dict__
    nm = NuleculeManager(app_spec=argdict['app_spec'],
                         destination='none')
    nm.genanswers(**argdict)
    Utils.rm_dir(nm.app_path)  # clean up files
    sys.exit(0)


def cli_fetch(args):
    argdict = args.__dict__
    destination = argdict['destination']
    nm = NuleculeManager(app_spec=argdict['app_spec'],
                         destination=destination,
                         cli_answers=argdict['cli_answers'],
                         answers_file=argdict['answers'],
                         answers_format=argdict.get('answers_format'))
    nm.fetch(**argdict)
    # Clean up the files if the user asked us to. Otherwise
    # notify the user where they can manage the application
    if destination and destination.lower() == 'none':
        Utils.rm_dir(nm.app_path)
    else:
        print_app_location(nm.app_path)
    sys.exit(0)


def cli_run(args):
    argdict = args.__dict__
    destination = argdict['destination']
    nm = NuleculeManager(app_spec=argdict['app_spec'],
                         destination=destination,
                         cli_answers=argdict['cli_answers'],
                         answers_file=argdict['answers'],
                         answers_format=argdict.get('answers_format'))
    nm.run(**argdict)
    # Clean up the files if the user asked us to. Otherwise
    # notify the user where they can manage the application
    if destination and destination.lower() == 'none':
        Utils.rm_dir(nm.app_path)
    else:
        print_app_location(nm.app_path)
    sys.exit(0)


def cli_stop(args):
    argdict = args.__dict__
    nm = NuleculeManager(app_spec=argdict['app_spec'])
    nm.stop(**argdict)
    sys.exit(0)


def cli_init(args):
    try:
        argdict = args.__dict__
        appdir = NuleculeManager.init(argdict['app_name'],
                                      argdict['destination'])
        if appdir:
            print('\nAtomic App: %s initialized at %s' %
                  (argdict['app_name'], appdir))
        sys.exit(0)
    except Exception as e:
        logger.error(e, exc_info=True)
        sys.exit(1)


def cli_index(args):
    argdict = args.__dict__
    i = Index()
    if argdict["index_action"] == "list":
        i.list()
    elif argdict["index_action"] == "update":
        i.update()
    elif argdict["index_action"] == "generate":
        i.generate(argdict["location"])
    sys.exit(0)


# Create a custom action parser. Need this because for some args we don't
# want to store a value if the user didn't provide one. "store_true" does
# not allow this; it will always create an attribute and store a value.
class TrueOrFalseAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        if values.lower() == 'true':
            booleanvalue = True
        else:
            booleanvalue = False
        setattr(namespace, self.dest, booleanvalue)


def cli_func_exec(cli_func, cli_func_args):
    try:
        cli_func(cli_func_args)
    except DockerException as e:
        logger.error(e)
        sys.exit(1)
    except NuleculeException as e:
        logger.error(e)
        sys.exit(1)
    except ProviderFailedException as e:
        logger.error(e)
        sys.exit(1)
    except Exception as e:
        logger.error(e, exc_info=True)
        sys.exit(1)


class CLI():

    def __init__(self):
        self.parser = self.create_parser()

    def create_parser(self):

        # We will have a few parsers that we use. The toplevel parser
        # will be the parser that ultimately gets called. It will consist
        # of subparsers for each "action" and each of those subparsers will
        # inherit from a parser for all global options.

        # === TOPLEVEL PARSER ===
        # Create the toplevel parser. This is the one we will return
        toplevel_parser = argparse.ArgumentParser(
            prog='atomicapp',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False,
            description=(
                "This will fetch and run an Atomic App, "
                "a containerized application conforming to the Nulecule Specification"))
        # Add a help function to the toplevel parser but don't output
        # help information for it. We need this because of the way we
        # are stitching help output together from multiple parsers
        toplevel_parser.add_argument(
            "-h",
            "--help",
            action='help',
            help=argparse.SUPPRESS)
        toplevel_parser.add_argument(
            "-V",
            "--version",
            action='version',
            version='atomicapp %s, Nulecule Specification %s' % (
                __ATOMICAPPVERSION__, __NULECULESPECVERSION__),
            help=argparse.SUPPRESS)
        # Allow for subparsers of the toplevel_parser. Store the name
        # in the "action" attribute
        toplevel_subparsers = toplevel_parser.add_subparsers(dest="action")

        # === GLOBAL OPTIONS PARSER ===
        # Create the globals argument parser next. This will be a
        # parent parser for the subparsers
        globals_parser = argparse.ArgumentParser(add_help=False)
        # Adding version argument again to avoid optional arguments from
        # being listed twice in -h. This only serves the help message.
        globals_parser.add_argument(
            "-V",
            "--version",
            action="store_true",
            help="Show the version and exit.")
        globals_parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            default=False,
            action="store_true",
            help="Verbose output mode.")
        globals_parser.add_argument(
            "-q",
            "--quiet",
            dest="quiet",
            default=False,
            action="store_true",
            help="Quiet output mode.")
        globals_parser.add_argument(
            "--logtype",
            dest="logtype",
            choices=['cockpit', 'color', 'nocolor', 'none'],
            help="""
                Override the default logging output. The options are:
                    nocolor: we will only log to stdout;
                    color: log to stdout with color;
                    cockpit: used with cockpit integration;
                    none: atomicapp will disable any logging.
                If nothing is set and logging to file then 'nocolor' by default.
                If nothing is set and logging to tty then 'color' by default.""")
        globals_parser.add_argument(
            "--mode",
            dest="mode",
            default=None,
            choices=['fetch', 'run', 'stop', 'genanswers'],
            help=('''
                 The mode Atomic App is run in. This option has the
                 effect of switching the 'verb' that was passed by the
                 user as the first positional argument. This is useful
                 in cases where a user is not using the Atomic App cli
                 directly, but through another interface such as the
                 Atomic CLI. EX: `atomic run <IMAGE> --mode=genanswers`'''))

        # === DEPLOY PARSER ===
        # Create a 'deploy parser' that will include flags related to deploying
        # and answers files
        deploy_parser = argparse.ArgumentParser(add_help=False)
        deploy_parser.add_argument(
            "--dry-run",
            dest="dryrun",
            default=False,
            action="store_true",
            help=(
                "Don't actually call provider. The commands that should be "
                "run will be logged but not run."))
        deploy_parser.add_argument(
            "--answers-format",
            dest="answers_format",
            default=ANSWERS_FILE_SAMPLE_FORMAT,
            choices=['ini', 'json', 'xml', 'yaml'],
            help="The format for the answers.conf.sample file. Default: %s" % ANSWERS_FILE_SAMPLE_FORMAT)
        deploy_parser.add_argument(
            "--namespace",
            dest="namespace",
            help=('The namespace to use in the target provider'))
        deploy_parser.add_argument(
            "--provider-tlsverify",
            dest="provider-tlsverify",
            action=TrueOrFalseAction,
            choices=['True', 'False'],
            help=('''
                Value for provider-tlsverify answers option.
                --providertlsverify=False to disable tls verification'''))
        deploy_parser.add_argument(
            "--provider-config",
            dest="provider-config",
            help='Value for provider-config answers option.')
        deploy_parser.add_argument(
            "--provider-cafile",
            dest="provider-cafile",
            help='Value for provider-cafile answers option.')
        deploy_parser.add_argument(
            "--provider-api",
            dest="provider-api",
            help='Value for provider-api answers option.')
        deploy_parser.add_argument(
            "--provider-auth",
            dest="provider-auth",
            help='Value for provider-auth answers option.')

        # === "run" SUBPARSER ===
        run_subparser = toplevel_subparsers.add_parser(
            "run", parents=[globals_parser, deploy_parser])
        run_subparser.add_argument(
            "-a",
            "--answers",
            dest="answers",
            help="Path to %s" % ANSWERS_FILE)
        run_subparser.add_argument(
            "--write-answers",
            dest="answers_output",
            help="A file which will contain anwsers provided in interactive mode")
        run_subparser.add_argument(
            "--provider",
            dest="provider",
            choices=PROVIDERS,
            help="The provider to use. Overrides provider value in answerfile.")
        run_subparser.add_argument(
            "--ask",
            default=False,
            action="store_true",
            help="Ask for params even if the default value is provided")
        run_subparser.add_argument(
            "app_spec",
            nargs='?',
            default=None,
            help=(
                "Application to run. This is a container image or a path "
                "that contains the metadata describing the whole application."))
        run_subparser.add_argument(
            "--destination",
            dest="destination",
            default=None,
            help=('''
                Destination directory for fetching. This defaults to a
                directory under %s. Specify 'none' to not persist
                files and have them cleaned up when finished.''' % CACHE_DIR))
        run_subparser.set_defaults(func=cli_run)

        # === "fetch" SUBPARSER ===
        fetch_subparser = toplevel_subparsers.add_parser(
            "fetch", parents=[globals_parser, deploy_parser])
        fetch_subparser.add_argument(
            "-a",
            "--answers",
            dest="answers",
            help="Path to %s" % ANSWERS_FILE)
        fetch_subparser.add_argument(
            "--no-deps",
            dest="nodeps",
            default=False,
            action="store_true",
            help="Skip pulling dependencies of the app")
        fetch_subparser.add_argument(
            "-u",
            "--update",
            dest="update",
            default=False,
            action="store_true",
            help="Re-pull images and overwrite existing files")
        fetch_subparser.add_argument(
            "--destination",
            dest="destination",
            default=None,
            help=('''
                Destination directory for fetch. This defaults to a
                directory under %s. Specify 'none' to not persist
                files and have them cleaned up when finished.''' % CACHE_DIR))
        fetch_subparser.add_argument(
            "app_spec",
            nargs='?',
            default=None,
            help=(
                "Application to run. This is a container image or a path "
                "that contains the metadata describing the whole application."))
        fetch_subparser.set_defaults(func=cli_fetch)

        # === "stop" SUBPARSER ===
        stop_subparser = toplevel_subparsers.add_parser(
            "stop", parents=[globals_parser, deploy_parser])
        stop_subparser.add_argument(
            "--provider",
            dest="cli_provider",
            choices=PROVIDERS,
            help="The provider to use. Overrides provider value in answerfile.")
        stop_subparser.add_argument(
            "app_spec",
            help=('''
                Path to the directory where the Atomic App is fetched
                that is to be stopped.'''))
        stop_subparser.set_defaults(func=cli_stop)

        # === "genanswers" SUBPARSER ===
        gena_subparser = toplevel_subparsers.add_parser(
            "genanswers", parents=[globals_parser])
        gena_subparser.add_argument(
            "app_spec",
            nargs='?',
            default=None,
            help='The name of a container image containing an Atomic App.')
        gena_subparser.set_defaults(func=cli_genanswers)

        # === "index" SUBPARSER ===
        index_subparser = toplevel_subparsers.add_parser(
            "index", parents=[globals_parser])
        index_action = index_subparser.add_subparsers(dest="index_action")

        index_list = index_action.add_parser("list")
        index_list.set_defaults(func=cli_index)

        index_update = index_action.add_parser("update")
        index_update.set_defaults(func=cli_index)

        index_generate = index_action.add_parser("generate")
        index_generate.add_argument(
            "location",
            help=(
                "Path containing Nulecule applications "
                "which will be part of the generated index"))
        index_generate.set_defaults(func=cli_index)

        # === "init" SUBPARSER ===
        init_subparser = toplevel_subparsers.add_parser(
            "init", parents=[globals_parser])
        init_subparser.add_argument(
            "app_name",
            help="App name.")
        init_subparser.add_argument(
            "--destination",
            dest="destination",
            default=None,
            help=('''
                Path to the directory where the Atomic App
                is to be initialized.'''))
        init_subparser.set_defaults(func=cli_init)

        # Some final fixups.. We want the "help" from the global
        # parser to be output when someone runs 'atomicapp --help'
        # To get that functionality we will add the help from the
        # globals parser to the epilog of the toplevel parser and also
        # suppress the usage message from being output from the
        # globals parser.
        globals_parser.usage = argparse.SUPPRESS
        deploy_parser.usage = argparse.SUPPRESS
        toplevel_parser.epilog = globals_parser.format_help()
        toplevel_parser.epilog = deploy_parser.format_help()

        # Return the toplevel parser
        return toplevel_parser

    def run(self):
        cmdline = sys.argv[1:]  # Grab args from cmdline
        if len(cmdline) == 0:
            cmdline = ['-h']    # Show help if no arguments are given
        # Initial setup of logging (to allow for a few early debug statements)
        Logging.setup_logging(verbose=True, quiet=False)

        # If we are running in an openshift pod (via `oc new-app`) then
        # there is no cmdline but we want to default to "atomicapp run".
        if Utils.running_on_openshift():
            cmdline = 'run -v --dest=none --provider=openshift /{}'
            cmdline = cmdline.format(APP_ENT_PATH).split()  # now a list

        # If the user has elected to provide all arguments via the
        # ATOMICAPP_ARGS environment variable then set it now
        argstr = os.environ.get('ATOMICAPP_ARGS')
        if argstr:
            logger.debug("Setting cmdline args to: {}".format(argstr))
            cmdline = argstr.split()

        # If the user has elected to provide some arguments via the
        # ATOMICAPP_APPEND_ARGS environment variable then add those now
        argstr = os.environ.get('ATOMICAPP_APPEND_ARGS')
        if argstr:
            logger.debug("Appending args to cmdline: {}".format(argstr))
            cmdline.extend(argstr.split())

        # We want to be able to place options anywhere on the command
        # line. We have added all global options to each subparser,
        # but subparsers require all options to be after the 'action'
        # keyword. In order to handle this we just need to figure out
        # what subparser will be used and move it's keyword to the front
        # of the line.
        # NOTE: Also allow "mode" to override 'action' if specified
        args, _ = self.parser.parse_known_args(cmdline)
        cmdline.remove(args.action)     # Remove 'action' from the cmdline
        if hasattr(args, 'mode') and args.mode:
            args.action = args.mode     # Allow mode to override 'action'
        cmdline.insert(0, args.action)  # Place 'action' at front

        # Finally, parse args and give error if necessary
        args = self.parser.parse_args(cmdline)

        # Setup logging (now with arguments from cmdline) and log a few msgs
        Logging.setup_logging(args.verbose, args.quiet, args.logtype)

        logger.info("Atomic App: %s - Mode: %s"
                    % (__ATOMICAPPVERSION__,
                        str(args.action).capitalize()))

        logger.debug("Final parsed cmdline: {}".format(' '.join(cmdline)))

        # In the case of Atomic CLI we want to allow the user to specify
        # a directory if they want to for "run". For that reason we won't
        # default the RUN label for Atomic App to provide an app_spec argument.
        # In this case pick up app_spec from $IMAGE env var (set by RUN label).
        if args.action != 'init' and args.action != 'index' and args.app_spec is None:
            if os.environ.get('IMAGE') is not None:
                logger.debug("Setting app_spec based on $IMAGE env var")
                args.app_spec = os.environ['IMAGE']
            else:
                print("Error. Too few arguments. Must provide app_spec.")
                print("Run with '--help' for more info")
                sys.exit(1)

        # Take the arguments that correspond to "answers" config file data
        # and make a dictionary of it to pass along in args.
        setattr(args, 'cli_answers', {})
        for item in ['provider-api', 'provider-cafile', 'provider-auth',
                     'provider-config', 'provider-tlsverify', 'namespace',
                     'provider']:
            if hasattr(args, item) and getattr(args, item) is not None:
                args.cli_answers[item] = getattr(args, item)

        try:
            cli_func_exec(args.func, args)
        except AttributeError:
            if hasattr(args, 'func'):
                raise
            else:
                self.parser.print_help()
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            if args.verbose:
                raise
            else:
                logger.error("Exception caught: %s", repr(ex))
                logger.error(
                    "Run the command again with -v option to get more information.")


def main():
    cli = CLI()
    cli.run()


if __name__ == '__main__':
    main()
