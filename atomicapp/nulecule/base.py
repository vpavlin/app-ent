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
from collections import defaultdict
from copy import deepcopy
from logging import getLogger
import os
import re
from string import Template

from anymarkup import AnyMarkupError, parse, serialize
from jsonpointer import resolve_pointer, set_pointer, JsonPointerException
from yaml import parser

from atomicapp.constants import (APP_ENT_PATH,
                                 DEFAULTNAME_KEY,
                                 DEFAULT_PROVIDER,
                                 GLOBAL_CONF,
                                 GRAPH_KEY,
                                 INHERIT_KEY,
                                 LOGGER_COCKPIT,
                                 LOGGER_DEFAULT,
                                 MAIN_FILE,
                                 NAME_KEY,
                                 PARAMS_KEY,
                                 PROVIDERS,
                                 PROVIDER_KEY,
                                 RESOURCE_KEY)
from atomicapp.utils import Utils
from atomicapp.plugin import Plugin
from atomicapp.requirements import Requirements
from atomicapp.nulecule.container import DockerHandler
from atomicapp.nulecule.exceptions import NuleculeException
from atomicapp.providers.openshift import OpenshiftProvider

cockpit_logger = getLogger(LOGGER_COCKPIT)
logger = getLogger(LOGGER_DEFAULT)


class Nulecule(object):

    """
    This represents an application compliant with Nulecule specification.
    A Nulecule instance can have instances of Nulecule and Nulecule as
    components. A Nulecule instance knows everything about itself and its
    componenents, but does not have access to its parent's scope.
    """

    def __init__(self, id, specversion, basepath, metadata=None,
                 requirements=None, params=None, config=None,
                 namespace=GLOBAL_CONF, artifacts=None, progenitor=False):
        """
        Create a Nulecule instance.

        Args:
            id (str): Nulecule application ID
            specversion (str): Nulecule spec version
            basepath (str): Basepath for Nulecule application
            metadata (dict): Nulecule metadata
            requirements (dict): Requirements for the Nulecule application
            params (list): List of params for the Nulecule application
            config (dict): Config data for the Nulecule application
            namespace (str): Namespace of the current Nulecule application
            progenitor (bool): Whether or not Nulecule instance is attributable
                to parent manifest as opposed to deployable graph component

        Returns:
            A Nulecule instance
        """
        self.artifacts = artifacts
        self.basepath = basepath
        self.config = config or {}
        self.id = id
        self.metadata = metadata or {}
        self.namespace = namespace
        self.params = params or []
        self.plugin = Plugin()
        self.rendered_artifacts = defaultdict(list)
        self.requirements = requirements
        self.specversion = specversion
        self.progenitor = progenitor

    def __eq__(self, other):
        return self.id == other.id and self.progenitor == other.progenitor

    def __hash__(self):
        return hash((self.id, self.progenitor,))

    @classmethod
    def unpack(cls, image, dest, config=None, namespace=GLOBAL_CONF,
               dryrun=False, update=False):
        """
        Pull and extracts a docker image to the specified path, and loads
        the Nulecule application from the path.

        Args:
            image (str): A Docker image name.
            dest (str): Destination path where Nulecule data from Docker
                        image should be extracted.
            config (dict): Dictionary, config data for Nulecule application.
            namespace (str): Namespace for Nulecule application.
            nodeps (bool): Don't pull external Nulecule dependencies when
                           True.
            update (bool): Don't update contents of destination directory
                           if False, else update it.

        Returns:
            A Nulecule instance, or None in case of dry run.
        """
        logger.info('Unpacking image %s to %s', image, dest)
        if Utils.running_on_openshift():
            # pass general config data containing provider specific data
            # to Openshift provider
            op = OpenshiftProvider(config.get('general', {}), './', False)
            op.artifacts = []
            op.init()
            op.extract(image, APP_ENT_PATH, dest, update)
        else:
            if os.path.isfile("%s/Nulecule" % dest) and not update:
                logger.info('Found existing destination %s ', dest)
            else:
                docker_handler = DockerHandler(dryrun=dryrun)
                docker_handler.pull(image)
                docker_handler.extract(image, APP_ENT_PATH, dest, update)
                cockpit_logger.info("All dependencies installed successfully.")
        return cls.load_from_path(
            dest, config=config, namespace=namespace, dryrun=dryrun)

    @classmethod
    def load_from_path(cls, src, config=None, namespace=GLOBAL_CONF,
                       dryrun=False):
        """
        Load a Nulecule application from a path in the source path itself, or
        in the specified destination path.

        Args:
            src (str): Path to load Nulecule application from.
            config (dict): Config data for Nulecule application.
            namespace (str): Namespace for Nulecule application.
            nodeps (bool): Do not pull external applications if True.
            dryrun (bool): Do not make any change to underlying host.

        Returns:
            A tuple of internal and external Nulecule instances.
        """
        progenitor = None
        internals = []
        externals = []

        nulecule_path = os.path.join(src, MAIN_FILE)

        if os.path.exists(nulecule_path):
            with open(nulecule_path, 'r') as f:
                nulecule_data = f.read()
        else:
            raise NuleculeException("No Nulecule file exists in directory: %s" % src)

        if dryrun and not os.path.exists(nulecule_path):
            raise NuleculeException("Fetched Nulecule components are required to initiate dry-run. "
                                    "Please specify your app via atomicapp --dry-run /path/to/your-app")

        # By default, AnyMarkup converts all formats to YAML when parsing.
        # Thus the rescue works either on JSON or YAML.
        try:
            nulecule_data = parse(nulecule_data)
        except (parser.ParserError, AnyMarkupError) as e:
            line = re.search(r'line (\d+)', str(e)).group(1)
            column = re.search(r'column (\d+)', str(e)).group(1)

            output = ""
            for i, l in enumerate(nulecule_data.splitlines()):
                if (i == int(line) - 1) or (i == int(line)) or (i == int(line) + 1):
                    output += "%s %s\n" % (str(i), str(l))

            raise NuleculeException("Failure parsing %s file. Validation error on line %s, column %s:\n%s"
                                    % (nulecule_path, line, column, output))
        else:
            kwargs = deepcopy(nulecule_data)
            kwargs['progenitor'] = True
            del kwargs[GRAPH_KEY]
            progenitor = Nulecule(config=config, basepath=src,
                                  namespace=namespace, **kwargs)

            for item in nulecule_data.get(GRAPH_KEY, []):
                if Utils.isExternal(item):
                    externals += [item]
                else:
                    kwargs = deepcopy(nulecule_data)
                    kwargs.update(item)
                    del kwargs[GRAPH_KEY]
                    del kwargs[NAME_KEY]
                    internals += [Nulecule(config=config, basepath=src,
                                           namespace=kwargs['id'], **kwargs)]

        return (progenitor, internals, externals)

    def run(self, provider_key=None, dryrun=False):
        """
        Runs a nulecule application.

        Args:
            provider_key (str): Provider to use for running Nulecule
                                application
            dryrun (bool): Do not make changes to host when True

        Returns:
            None
        """
        provider_key, provider = self.get_provider(provider_key, dryrun)

        # Process preliminary requirements before componenets
        if self.requirements:
            logger.debug("Requirements detected. Running action.")
            Requirements(self.config, self.basepath, self.requirements,
                         provider_key, dryrun).run()

        cockpit_logger.info("Deploying component %s ...", self.id)
        provider_key, provider = self.get_provider(provider_key, dryrun)
        provider.artifacts = self.rendered_artifacts.get(provider_key, [])
        provider.init()
        # TODO: add idempotency to provider requests
        provider.run()
        cockpit_logger.info("Component %s installed successfully", provider_key)

    def stop(self, provider_key=None, dryrun=False):
        """
        Stop the Nulecule application.

        Args:
            provider_key (str): Provider to use for running Nulecule
                                application
            dryrun (bool): Do not make changes to host when True

        Returns:
            None
        """
        provider_key, provider = self.get_provider(provider_key, dryrun)
        # stop the Nulecule application
        provider_key, provider = self.get_provider(provider_key, dryrun)
        provider.artifacts = self.rendered_artifacts.get(provider_key, [])
        provider.init()
        # TODO: add idempotency to provider requests
        provider.stop()

    def load_config(self, config=None, ask=False, skip_asking=False):
        """
        Load config data for the entire Nulecule application, by traversing
        through all the Nulecule components in a DFS fashion.

        It updates self.config.

        Args:
            config (dict): Existing config data, may be from ANSWERS
                           file or any other source.

        Returns:
            None
        """
        for param in self.params:
            value = config.get(self.namespace, {}).get(param[NAME_KEY]) or \
                config.get(GLOBAL_CONF, {}).get(param[NAME_KEY])
            if value is None and (ask or (
                    not skip_asking and param.get(DEFAULTNAME_KEY) is None)):
                cockpit_logger.info("%s is missing in answers.conf.", param[NAME_KEY])
                value = Utils.askFor(param[NAME_KEY], param)
            elif value is None:
                value = param.get(DEFAULTNAME_KEY)
            if config.get(self.namespace) is None:
                config[self.namespace] = {}
            config[self.namespace][param[NAME_KEY]] = value
        self.config = config

        if self.config[GLOBAL_CONF].get('provider') is None:
            self.config[GLOBAL_CONF]['provider'] = DEFAULT_PROVIDER
            logger.info("Provider not specified, using default provider - %s",
                        DEFAULT_PROVIDER)

    def render(self, provider_key=None):
        """
        Render the artifact files for the entire Nulecule application from
        config data.

        Args:
            provider_key (str): Provider for which artifacts need to be
                                rendered. If it's None, we render artifacts
                                for all providers.

        Returns:
            None
        """
        if not self.progenitor and self.artifacts is None:
            raise NuleculeException(
                "No artifacts specified in the Nulecule file")
        if not self.progenitor and provider_key and provider_key not in self.artifacts:
            raise NuleculeException(
                "Data for provider \"%s\" are not part of this app"
                % provider_key)
        context = self.get_context()
        if not self.progenitor:
            for provider in self.artifacts:
                if provider_key and provider != provider_key:
                    continue
                for artifact_path in self.get_artifact_paths_for_provider(
                        provider):
                    self.rendered_artifacts[provider].append(
                        self.render_artifact(artifact_path, context, provider))

    def get_artifact_paths_for_provider(self, provider_key):
        """
        Get artifact file paths of a Nulecule component for a provider.

        Args:
            provider_key (str): Provider name

        Returns:
            list: A list of artifact paths.
        """
        artifact_paths = []
        artifacts = self.artifacts.get(provider_key)

        # If there are no artifacts for the requested provider then error
        # This can happen for incorrectly named inherited provider (#435)
        if artifacts is None:
            raise NuleculeException(
                "No artifacts for provider {}".format(provider_key))

        for artifact in artifacts:
            # Convert dict if the Nulecule file references "resource"
            if isinstance(artifact, dict) and artifact.get(RESOURCE_KEY):
                artifact = artifact[RESOURCE_KEY]
                logger.debug("Resource xpath added: %s", artifact)

            # Sanitize the file structure
            if isinstance(artifact, basestring):
                path = Utils.sanitizePath(artifact)
                path = os.path.join(self.basepath, path) \
                    if path[0] != '/' else path
                artifact_paths.extend(self._get_artifact_paths_for_path(path))

            # Inherit if inherit name is referenced
            elif isinstance(artifact, dict) and artifact.get(INHERIT_KEY) and \
                    isinstance(artifact.get(INHERIT_KEY), list):
                for inherited_provider_key in artifact.get(INHERIT_KEY):
                    artifact_paths.extend(
                        self.get_artifact_paths_for_provider(
                            inherited_provider_key)
                    )
            else:
                logger.error('Invalid artifact file')
        return artifact_paths

    def grab_artifact_params(self, provider):
        """
        Check to see if params exist in the artifact. If so, return it.

        Args:
            provider(str): name of the provider

        Returns:
            str (dict): list of params

        """
        artifact = self.artifacts.get(provider)[0]
        if PARAMS_KEY in artifact:
            return artifact.get(PARAMS_KEY)
        else:
            return None

    def get_context(self):
        """
        Get context data from config data for rendering an artifact.
        """
        context = {}
        context.update(self.config.get(GLOBAL_CONF) or {})
        context.update(self.config.get(self.namespace) or {})
        return context

    def get_provider(self, provider_key=None, dry=False):
        """
        Get provider key and provider instance.

        Args:
            provider_key (str or None): Name of provider
            dry (bool): Do not make change to the host system while True

        Returns:
            tuple: (provider key, provider instance)
        """
        # If provider_key isn't provided via CLI, let's grab it the configuration
        if provider_key is None:
            provider_key = self.config.get(GLOBAL_CONF)[PROVIDER_KEY]
        provider_class = self.plugin.getProvider(provider_key)
        if provider_class is None:
            raise NuleculeException("Invalid Provider - '{}', provided in "
                                    "answers.conf (choose from {})"
                                    .format(provider_key, ', '
                                            .join(PROVIDERS)))
        return provider_key, provider_class(
            self.get_context(), self.basepath, dry)

    @staticmethod
    def apply_pointers(content, params):
        """
        Let's apply all the json pointers!
        Valid params in Nulecule:

            param1:
                - /spec/containers/0/ports/0/hostPort
                - /spec/containers/0/ports/0/hostPort2
            or
            param1:
                - /spec/containers/0/ports/0/hostPort, /spec/containers/0/ports/0/hostPort2

        Args:
            content (str): content of artifact file
            params (dict): list of params with pointers to replace in content

        Returns:
            str: content with replaced pointers

        Todo:
            In the future we need to change this to detect haml, yaml, etc as we add more providers
            Blocked by: github.com/bkabrda/anymarkup-core/blob/master/anymarkup_core/__init__.py#L393
        """
        obj = parse(content)

        if not isinstance(obj, dict):
            logger.debug("Artifact file not json/yaml, assuming it's $VARIABLE substitution")
            return content

        if params is None:
            # Nothing to do here!
            return content

        for name, pointers in params.items():

            if not pointers:
                logger.warning("Could not find pointer for %s", name)
                continue

            for pointer in pointers:
                try:
                    resolve_pointer(obj, pointer)
                    set_pointer(obj, pointer, name)
                    logger.debug("Replaced %s pointer with %s param", pointer, name)
                except JsonPointerException:
                    logger.debug("Error replacing %s with %s", pointer, name)
                    logger.debug("Artifact content: %s", obj)
                    raise NuleculeException("Error replacing pointer %s with %s.", pointer, name)
        return serialize(obj, format="json")

    def render_artifact(self, path, context, provider):
        """
        Render artifact file at path with context to a file at the same
        level. The rendered file has a name a dot '.' prefixed to the
        name of the source artifact file.

        Args:
            path (str): path to the artifact file
            context (dict): data to render in the artifact file
            provider (str): what provider is being used

        Returns:
            str: Relative path to the rendered artifact file from the
                 immediate parent Nuelcule application
        """
        basepath, tail = os.path.split(path)
        render_path = os.path.join(basepath, '.{}'.format(tail))

        with open(path, 'r') as f:
            content = f.read()
            params = self.grab_artifact_params(provider)
            if params is not None:
                content = self.apply_pointers(content, params)
            template = Template(content)
            rendered_content = template.safe_substitute(context)

        with open(render_path, 'w') as f:
            f.write(rendered_content)

        render_path = render_path.split(
            self.basepath + ('' if self.basepath.endswith('/') else '/'),
            1)[1]
        return render_path

    @staticmethod
    def _get_artifact_paths_for_path(path):
        """
        Get artifact paths for a local filesystem path. We support path to
        an artifact file or a directory containing artifact files as its
        immediate children, i.e., we do not deal with nested artifact
        directories at this moment.

        If a file or directory is not found, raise an exception.

        Args:
            path (str): Local path

        Returns:
            list: A list of artifact paths
        """
        artifact_paths = []
        if os.path.isfile(path):
            artifact_paths.append(path)
        elif os.path.isdir(path):
            if os.listdir(path) == []:
                raise NuleculeException("Artifact directory %s is empty" % path)
            for dir_child in os.listdir(path):
                dir_child_path = os.path.join(path, dir_child)
                if dir_child.startswith('.') or os.path.isdir(dir_child_path):
                    continue
                artifact_paths.append(dir_child_path)
        else:
            raise NuleculeException("Unable to find artifact %s" % path)

        return artifact_paths
