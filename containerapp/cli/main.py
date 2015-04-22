#!/usr/bin/python

from containerapp.run import Run
from containerapp.install import Install
from containerapp import create
from containerapp import params
import os, sys, json
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import logging

from containerapp import set_logging
from containerapp.constants import ANSWERS_FILE, MAIN_FILE

def cli_install(args):
    print(args)
    install = Install(**vars(args))
    install.install()

def cli_create(args):
    raise Exception("This is broken, sorry:/")
    ac = create.AtomicappCreate(args.NAME, args.schema, args.dryrun)
    ac.create()

def cli_build(args):
    if os.path.isfile(os.path.join(os.getcwd(), MAIN_FILE)):
        with open(os.path.join(os.getcwd(), MAIN_FILE), "r") as fp:
            data = json.load(fp)
            ac = create.AtomicappCreate(data["id"], args.dryrun)
            ac.build(args.TAG)

def cli_run(args):
    print(vars(args)["answers"])
    ae = Run(**vars(args))
    ae.run()

class CLI():
    def __init__(self):
        self.parser = ArgumentParser(description='TBD', formatter_class=RawDescriptionHelpFormatter)

    def set_arguments(self):

        self.parser.add_argument("-v", "--verbose", dest="verbose", default=False, action="store_true", help="Verbose output mode.")
        self.parser.add_argument("-q", "--quiet", dest="quiet", default=False, action="store_true", help="Quiet output mode.")

        self.parser.add_argument("--dry-run", dest="dryrun", default=False, action="store_true", help="Don't actually call provider. The commands that should be run will be sent to stdout but not run.")

        subparsers = self.parser.add_subparsers(dest="action")

        parser_create = subparsers.add_parser("create")
        parser_create.add_argument("--schema", default=None, help="Schema for the app spec")
        parser_create.add_argument("NAME", help="App name")
        parser_create.set_defaults(func=cli_create)

    
        parser_run = subparsers.add_parser("run")
        self.parser.add_argument("-a", "--answers", dest="answers", default=os.path.join(os.getcwd(), ANSWERS_FILE), help="Path to %s" % ANSWERS_FILE)
        parser_run.add_argument("APP", nargs="?", help="Path to the directory where the image is installed (current directory by default).")
        parser_run.set_defaults(func=cli_run)
    
        parser_install = subparsers.add_parser("install")

        parser_install.add_argument("-r", "--recursive", dest="recursive", default=True, help="Pull and populate full dependency tree")
        parser_install.add_argument("-u", "--update", dest="update", default=False, action="store_true", help="Re-pull images and overwrite existing files")
        parser_install.add_argument("-p", "--path", dest="target_path", default=None, help="Target directory for install")
        parser_install.add_argument("APP",  default=None, help="Application to run. This is a container image that has the metadata describing the whole application.")
        parser_install.set_defaults(func=cli_install)
    
        parser_build = subparsers.add_parser("build")
        parser_build.add_argument("TAG", nargs="?", default=None, help="Name of the image containing your app")
        parser_build.set_defaults(func=cli_build)

    def run(self):
        self.set_arguments()
        args = self.parser.parse_args()
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
            if True or args.verbose:
                raise
            else:
                logger.error("Exception caught: %s", repr(ex))   



def main():
    cli = CLI()
    cli.run()

if __name__ == '__main__':
    main()
