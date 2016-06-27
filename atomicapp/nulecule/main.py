# -*- coding: utf-8 -*-
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
from collections import OrderedDict
from copy import deepcopy
from distutils.dir_util import copy_tree, remove_tree
from itertools import product
from logging import getLogger
import os
from string import Template
from tempfile import mkdtemp
from urllib import urlopen
from urlparse import urlparse

from anymarkup import serialize_file
from networkx import DiGraph, topological_sort

from atomicapp.constants import (ANSWERS_FILE,
                                 ANSWERS_FILE_SAMPLE,
                                 ANSWERS_FILE_SAMPLE_FORMAT,
                                 ANSWERS_RUNTIME_FILE,
                                 DEFAULT_ANSWERS,
                                 EXTERNAL_APP_DIR,
                                 GLOBAL_CONF,
                                 LOGGER_COCKPIT,
                                 LOGGER_DEFAULT,
                                 MAIN_FILE,
                                 NAME_KEY,
                                 PROVIDER_KEY,
                                 __ATOMICAPPVERSION__,
                                 __NULECULESPECVERSION__)
from atomicapp.nulecule.base import Nulecule
from atomicapp.nulecule.exceptions import NuleculeException
from atomicapp.utils import Utils

cockpit_logger = getLogger(LOGGER_COCKPIT)
logger = getLogger(LOGGER_DEFAULT)


class NuleculeManager(object):

    """
    Interface to fetch, run, stop a Nulecule application.
    """

    def __init__(self, app_spec, destination=None, cli_answers=None,
                 answers_file=None):
        """
        init function for NuleculeManager. Sets a few instance variables.

        Args:
            app_spec: either a path to an unpacked nulecule app or a
                      container image name where a nulecule can be found
            destination: where to unpack a nulecule to if it isn't local
            cli_answers: some answer file values provided from cli args
            answers_file: the location of the answers file
        """
        self.answers = deepcopy(DEFAULT_ANSWERS)
        self.cli_answers = cli_answers
        self.answers_file = None  # The path to an answer file
        self.app_path = None  # The path where the app resides or will reside
        self.image = None     # The container image to pull the app from

        self.__dict__.update(self._process_app_spec(app_spec, destination))

        # Adjust answer file path if absolute.
        if answers_file and os.path.isabs(answers_file):
            answers_file = Utils.get_real_abspath(answers_file)

        logger.debug("NuleculeManager init app_path: %s", self.app_path)
        logger.debug("NuleculeManager init image: %s", self.image)

        # Set where the main nulecule file should be
        self.main_file = os.path.join(self.app_path, MAIN_FILE)

        # Process answers.
        self.answers_file = answers_file
        self._process_answers()

    @staticmethod
    def init(app_name, destination=None, app_version='1.0',
             app_desc='App description'):
        """Initialize a new Nulecule app

        Args:
            app_name (str): Application name
            destination (str): Destination path
            app_version (str): Application version
            app_desc (str): Application description

        Returns:
            destination (str)
        """

        # context to render template files for Atomic App
        context = dict(
            app_name=app_name,
            app_version=app_version,
            app_desc=app_desc,
            atomicapp_version=__ATOMICAPPVERSION__,
            nulecule_spec_version=__NULECULESPECVERSION__
        )

        if destination is None:
            destination = os.path.join('.', app_name)

        # Check if destination directory exists and is not empty
        if os.path.exists(destination) and \
           os.path.isdir(destination) and os.listdir(destination):
            value = raw_input('Destination directory is not empty! '
                              'Do you still want to proceed? [Y]/n: ')
            value = value or 'y'
            if value.lower() != 'y':
                return  # Exit out as the user has chosen not to proceed

        # Temporary working dir to render the templates
        tmpdir = mkdtemp(prefix='nulecule-new-app-')
        template_dir = os.path.join(os.path.dirname(__file__),
                                    'external/templates/nulecule')

        try:
            # Copy template dir to temporary working directory and render templates
            copy_tree(template_dir, tmpdir)
            for item in os.walk(tmpdir):
                parent_dir, _, files = item
                for filename in files:
                    if not filename.endswith('.tpl'):
                        continue
                    templ_path = os.path.join(parent_dir, filename)
                    if parent_dir.endswith('artifacts/docker') or \
                       parent_dir.endswith('artifacts/kubernetes'):
                        file_path = os.path.join(
                            parent_dir,
                            '{}_{}'.format(app_name, filename[:-4]))
                    else:
                        file_path = os.path.join(parent_dir, filename[:-4])
                    with open(templ_path) as f:
                        s = f.read()
                    t = Template(s)
                    with open(file_path, 'w') as f:
                        f.write(t.safe_substitute(**context))
                    os.remove(templ_path)

            # Copy rendered templates to destination directory
            copy_tree(tmpdir, destination, True)
        finally:
            # Remove temporary working directory
            remove_tree(tmpdir)
        return destination

    def digraph(self, update=False, dryrun=False, nodeps=False, config=None,
                **kwargs):
        """
        Args:
            update (bool): Update existing Nulecule application in
                           app_path, if True
            dryrun (bool): Do not make any change to the host system
            nodeps (bool): Do not unpack external dependencies
            config (dict): Config data, if any, to use for unpacking
            kwargs (dict): Extra keyword arguments

        Returns:
            networkx.DiGraph of Nulecule objects
        """
        digraph = DiGraph()

        (progenitor,
         internals,
         externals) = self.unpack(config=config, dryrun=dryrun, nodeps=nodeps,
                                  update=update, **kwargs)

        digraph.add_node(progenitor)

        for internal in internals:
            digraph.add_edge(progenitor, internal)

        for external in externals:
            app_spec = Utils.getSourceImage(external)
            name = external[NAME_KEY]
            destination = "%s/%s/%s" % (self.app_path, EXTERNAL_APP_DIR, name)
            if app_spec is not None:
                kwargs.update({'namespace': name})
                kwargs.update(self._process_app_spec(app_spec, destination))
                subgraph = self.digraph(**kwargs)
                if subgraph.order() > 0:
                    patronage = internals or [progenitor]
                    subprogenitor = topological_sort(subgraph, reverse=False)[0]
                    digraph.add_edges_from(product(patronage, [subprogenitor]))
                    digraph.add_edges_from(subgraph.edges())

        return digraph

    def unpack(self, update=False, dryrun=False, config=None, **kwargs):
        """
        Unpacks a Nulecule application from a Nulecule image to a path
        or load a Nulecule that already exists locally.

        Args:
            update (bool): Update existing Nulecule application in
                           app_path, if True
            dryrun (bool): Do not make any change to the host system
            nodeps (bool): Do not unpack external dependencies
            config (dict): Config data, if any, to use for unpacking
            kwargs (dict): Extra keyword arguments

        Returns:
            A Nulecule instance.
        """
        namespace = kwargs.get("namespace", GLOBAL_CONF)
        app_path = kwargs.get("app_path", self.app_path)
        image = kwargs.get("image", self.image)

        # If the user provided an image then unpack it and return the
        # resulting Nulecule. Else, load from existing path
        if image:
            logger.debug('Request to unpack to %s to %s', image, app_path)

            return Nulecule.unpack(image, app_path, config=config,
                                   dryrun=dryrun, update=update,
                                   namespace=namespace)
        else:
            return Nulecule.load_from_path(app_path, dryrun=dryrun,
                                           config=config, namespace=namespace)

    def genanswers(self, dryrun=False, answers_format=None, **kwargs):
        """
        Renders artifacts and then generates an answer file. Finally
        copies answer file to the current working directory.

        Args:
            dryrun (bool): Do not make any change to the host system if True
            answers_format (str): File format for writing sample answers file
            kwargs (dict): Extra keyword arguments

        Returns:
            None
        """
        # Check to make sure an answers.conf file doesn't exist already
        answers_file = os.path.join(os.getcwd(), ANSWERS_FILE)
        if os.path.exists(answers_file):
            raise NuleculeException(
                "Can't generate answers.conf over existing file")

        # Call digraph to get the app code
        digraph = self.digraph(update=False, dryrun=dryrun, config=self.answers)
        progenitor = topological_sort(digraph, reverse=False)[0]

        answers = {}
        for nulecule in topological_sort(digraph, reverse=True):
            nulecule.load_config(config=progenitor.config, skip_asking=True)
            nulecule.load_config(config=nulecule.config, skip_asking=True)
            # Get answers and write them out to answers.conf in cwd
            answers.update(self._get_runtime_answers(nulecule.config, None))
        self._write_answers(answers_file, answers, answers_format)

    def fetch(self, update=False, dryrun=False,
              answers_format=ANSWERS_FILE_SAMPLE_FORMAT, **kwargs):
        """
        Installs (unpacks) a Nulecule application from a Nulecule image
        to a target path.
        Args:
            answers (dict or str): Answers data or local path to answers file
            update (bool): Pull requisite Nulecule image and install or
                           update already installed Nulecule application
            dryrun (bool): Do not make any change to the host system if True
            answers_format (str): File format for writing sample answers file
            kwargs (dict): Extra keyword arguments
        Returns:
            None
        """
        # Call digraph. If the app doesn't exist it will be pulled. If
        # it does exist it will be just be loaded and returned
        digraph = self.digraph(update, dryrun, config=self.answers)
        progenitor = topological_sort(digraph, reverse=False)[0]

        answers = {}
        for nulecule in topological_sort(digraph, reverse=True):
            nulecule.load_config(config=progenitor.config, skip_asking=True)
            nulecule.load_config(config=nulecule.config, skip_asking=True)
            answers.update(self._get_runtime_answers(nulecule.config, None))
        # write sample answers file
        self._write_answers(
            os.path.join(self.app_path, ANSWERS_FILE_SAMPLE),
            answers, answers_format)

    cockpit_logger.info("Install Successful.")

    def run(self, cli_provider, answers_output, ask,
            answers_format=ANSWERS_FILE_SAMPLE_FORMAT, **kwargs):
        """
        Runs a Nulecule application from a local path or a Nulecule image
        name.

        Args:
            answers (dict or str): Answers data or local path to answers file
            cli_provider (str): Provider to use to run the Nulecule
                                application
            answers_output (str): Path to file to export runtime answers data
                                  to
            ask (bool): Ask for values for params with default values from
                        user, if True
            answers_format (str): File format for writing sample answers file
            kwargs (dict): Extra keyword arguments

        Returns:
            None
        """
        dryrun = kwargs.get('dryrun') or False

        # Call digraph. If the app doesn't exist it will be pulled. If
        # it does exist it will be just be loaded and returned
        digraph = self.digraph(dryrun=dryrun, config=self.answers)
        progenitor = topological_sort(digraph, reverse=False)[0]

        # If we didn't find an answers file before then call _process_answers
        # again just in case the app developer embedded an answers file
        if not self.answers_file:
            self._process_answers()

        answers = {}
        for nulecule in topological_sort(digraph, reverse=True):
            nulecule.load_config(config=progenitor.config, ask=ask)
            nulecule.load_config(config=nulecule.config, ask=ask)
            nulecule.render(cli_provider)
            nulecule.run(cli_provider, dryrun)
            answers.update(self._get_runtime_answers(
                nulecule.config, cli_provider))
        self._write_answers(
            os.path.join(self.app_path, ANSWERS_RUNTIME_FILE),
            answers, answers_format)
        if answers_output:
            self._write_answers(answers_output, answers, answers_format)

    def stop(self, cli_provider, **kwargs):
        """
        Stops a running Nulecule application.

        Args:
            cli_provider (str): Provider running the Nulecule application
            kwargs (dict): Extra keyword arguments
        """
        # For stop we use the generated answer file from the run
        self.answers_file = os.path.join(self.app_path, ANSWERS_RUNTIME_FILE)
        self._process_answers()

        dryrun = kwargs.get('dryrun') or False
        digraph = self.digraph(dryrun=dryrun, config=self.answers)

        for nulecule in topological_sort(digraph, reverse=False):
            nulecule.load_config(config=self.answers)
            nulecule.render(cli_provider)
            nulecule.stop(cli_provider, dryrun)

    def clean(self, force=False):
        # For future use
        # self.uninstall()
        # remove_tree(self.unpack_path)
        # self.initialize()
        raise NotImplementedError

    @staticmethod
    def _process_app_spec(app_spec, destination):
        """
        Args:
            app_spec: either a path to an unpacked nulecule app or a
                      container image name where a nulecule can be found
            destination: where to unpack a nulecule to if it isn't local

        Returns:
            app_path, image (dict)
        """
        app_path = None
        image = None

        # Adjust app_spec, and destination paths if absolute.
        if os.path.isabs(app_spec):
            app_spec = Utils.get_real_abspath(app_spec)
        if destination and os.path.isabs(destination):
            destination = Utils.get_real_abspath(destination)

        # If the user doesn't want the files copied to a permanent
        # location then he provides 'none'. If that is the case we'll
        # use a temporary directory
        if destination and destination.lower() == 'none':
            logger.debug("'none' destination requested. Using tmp dir")
            destination = mkdtemp(prefix='atomicapp')

        # Determine if the user passed us an image or a path to an app
        if not os.path.exists(app_spec):
            image = app_spec
        else:
            app_path = app_spec

        # Doesn't really make much sense to provide an app path and destination,
        # but if they want to we'll simply just copy the files for them
        if app_path and destination:
            Utils.copy_dir(app_path, destination, update=True)
            app_path = destination

        # If the user provided an image, make sure we have a destination
        if image:
            if destination:
                app_path = destination
            else:
                app_path = Utils.getNewAppCacheDir(image)

        # Create the app_path if it doesn't exist yet
        if not os.path.isdir(app_path):
            os.makedirs(app_path)

        return {'app_path': app_path, 'image': image}

    def _process_answers(self):
        """
        Processes answer files to load data from them and then merges
        any cli provided answers into the config.

        NOTE: This function should be called once on startup and then
        once more after the application has been extracted, but only
        if answers file wasn't found on the first invocation. The idea
        is to allow for people to embed an answers file in the application
        if they want, which won't be available until after extraction.

        Returns:
            None
        """
        app_path_answers = os.path.join(self.app_path, ANSWERS_FILE)

        # If the user didn't provide an answers file then check the app
        # dir to see if one exists.
        if not self.answers_file:
            if os.path.isfile(app_path_answers):
                self.answers_file = app_path_answers

        # At this point if we have an answers file, load it
        if self.answers_file:

            # If this is a url then download answers file to app directory
            if urlparse(self.answers_file).scheme != "":
                logger.debug("Retrieving answers file from: %s",
                             self.answers_file)
                with open(app_path_answers, 'w+') as f:
                    stream = urlopen(self.answers_file)
                    f.write(stream.read())
                self.answers_file = app_path_answers

            # Check to make sure the file exists
            if not os.path.isfile(self.answers_file):
                raise NuleculeException(
                    "Provided answers file doesn't exist: {}".format(self.answers_file))

            # Load answers
            self.answers = Utils.loadAnswers(self.answers_file)

        # If there is answers data from the cli then merge it in now
        if self.cli_answers:
            for k, v in self.cli_answers.iteritems():
                self.answers[GLOBAL_CONF][k] = v

    @staticmethod
    def _write_answers(path, answers, answers_format):
        """
        Write answers data to file.

        Args:
            path (str): path to answers file to write to
            answers (dict): Answers data
            answers_format (str): Format to use to dump answers data to file,
                                  e.g., json
        Returns:
            None
        """
        answers = OrderedDict(sorted(answers.items(), key=lambda i: (i[0] != 'general', i[0])))
        logger.debug("Writing answers to file.")
        logger.debug("FILE: %s", path)
        logger.debug("ANSWERS: %s", answers)
        serialize_file(answers, path, format=answers_format)

    # TODO - once we rework config data we shouldn't need this
    # function anymore, we should be able to take the data
    # straight from the config object since the defaults and args
    # provided from the cli would have already been merged.
    @staticmethod
    def _get_runtime_answers(config, cli_provider):
        """
        Get runtime answers data from config (Nulecule config) by adding
        default data if missing.

        Args:
            config (dict): Nulecule config data
            cli_provider (str): Provider used for running Nulecule application

        Returns:
            dict
        """
        _config = deepcopy(config)
        _config[GLOBAL_CONF] = config.get(GLOBAL_CONF) or {}

        # If a provider is provided via CLI, override the config parameter
        if cli_provider:
            _config[GLOBAL_CONF][PROVIDER_KEY] = cli_provider

        return _config
