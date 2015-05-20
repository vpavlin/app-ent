#!/usr/bin/env python

from atomicapp.run import Run
from atomicapp.install import Install
import os
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import logging
from atomicapp.rest import Rest
from atomicapp import context
import threading

from atomicapp import set_logging
from atomicapp.constants import ANSWERS_FILE, __ATOMICAPPVERSION__, __NULECULESPECVERSION__

logger = logging.getLogger(__name__)

def cli_install(args):
    install = Install(**vars(args))
    install.install()
    context.globalCtx.addStatus("Install Successful." ,status_type="COMPLETED")

def cli_run(args):
    ae = Run(**vars(args))
    ae.run()
    context.globalCtx.addStatus("Run Successful." ,status_type="COMPLETED")

def cli_stop(args):
    stop = Run(stop = True, **vars(args))
    stop.run()

def format_answers_path(cargs):
    if cargs.APP and os.path.exists(cargs.APP):
        cargs.answers = os.path.join(cargs.APP, ANSWERS_FILE)

    return cargs

# see https://docs.python.org/release/2.2.3/whatsnew/sect-rellinks.html
class CLI(object):
    def __init__(self):
        self.parser = ArgumentParser(prog='atomicapp', description='This will install and run an atomicapp, a containerized application conforming to the Nulecule Specification', formatter_class=RawDescriptionHelpFormatter)

    def set_arguments(self):

        self.parser.add_argument("-V", "--version", action='version', version='atomicapp %s, Nulecule Specification %s' % (__ATOMICAPPVERSION__, __NULECULESPECVERSION__), help="show the version and exit.") # TODO refactor program name and version to some globals
        self.parser.add_argument("-v", "--verbose", dest="verbose", default=False, action="store_true", help="Verbose output mode.")
        self.parser.add_argument("-q", "--quiet", dest="quiet", default=False, action="store_true", help="Quiet output mode.")
        self.parser.add_argument("-d", "--daemon", dest="daemon", default=False, action="store_true",  help="Run the CLI as a REST server daemon.")

        self.parser.add_argument("--dry-run", dest="dryrun", default=False, action="store_true", help="Don't actually call provider. The commands that should be run will be sent to stdout but not run.")
        self.parser.add_argument("-a", "--answers", dest="answers", default=os.path.join(os.getcwd(), ANSWERS_FILE), help="Path to %s" % ANSWERS_FILE)

        subparsers = self.parser.add_subparsers(dest="action")

        parser_run = subparsers.add_parser("run")
        parser_run.add_argument("--write-answers", dest="answers_output", help="A file which will contain anwsers provided in interactive mode")
        parser_run.add_argument("--ask", default=False, action="store_true", help="Ask for params even if the defaul value is provided")
        parser_run.add_argument("APP", help="Path to the directory where the image is installed.")
        parser_run.set_defaults(func=cli_run)

        parser_install = subparsers.add_parser("install")

        parser_install.add_argument("--no-deps", dest="nodeps", default=False, action="store_true", help="Skip pulling dependencies of the app")
        parser_install.add_argument("-u", "--update", dest="update", default=False, action="store_true", help="Re-pull images and overwrite existing files")
        parser_install.add_argument("--destination", dest="target_path", default=None, help="Destination directory for install")
        parser_install.add_argument("APP",  help="Application to run. This is a container image or a path that contains the metadata describing the whole application.")
        parser_install.set_defaults(func=cli_install)

        parser_stop = subparsers.add_parser("stop")
        parser_stop.add_argument("APP", help="Path to the directory where the atomicapp is installed or an image containing atomicapp which should be stopped.")
        parser_stop.set_defaults(func=cli_stop)

    def get_args(self):
        self.set_arguments()
        args = self.parser.parse_args()
        return args

    def run(self, args):
        if args.verbose:
            set_logging(level=logging.DEBUG)
        elif args.quiet:
            set_logging(level=logging.WARNING)
        else:
            set_logging(level=logging.INFO)
        try:
            args.func(args)
        except AttributeError:
            if hasattr(args, 'func'):
                raise
            else:
                self.parser.print_help()
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            context.globalCtx.addStatus("Exception raised: %s" % ex ,status_type="ERROR")
            if args.verbose:
                raise
            else:
                logger.error("Exception caught: %s", repr(ex))
                logger.error("Run the command again with -v option to get more information.")



def main():
    context.globalCtx = context.Config(False)
    cli = CLI()
    cargs = cli.get_args()
    if cargs.daemon:
        #fetch answers file from app location
        cargs = format_answers_path(cargs)
        t = threading.Thread(target=cli.run, args=(cargs,))
        t.start()
        start_restapp(debug=False, port=5000)
    else:
        cli.run(cargs)

def start_restapp(debug, port):
    rest = Rest()
    rest.run(debug, port)

if __name__ == '__main__':
    main()
