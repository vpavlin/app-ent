# -*- coding: utf-8 -*-
import anymarkup
import copy
import logging
import os

from collections import defaultdict
from string import Template

from atomicapp.constants import (APP_ENT_PATH,
                                 EXTERNAL_APP_DIR,
                                 GLOBAL_CONF,
                                 MAIN_FILE,
                                 RESOURCE_KEY,
                                 PARAMS_KEY,
                                 NAME_KEY,
                                 INHERIT_KEY,
                                 ARTIFACTS_KEY,
                                 REQUIREMENTS_KEY,
                                 PROVIDER_KEY,
                                 DEFAULTPROVIDER_KEY,
                                 DEFAULT_PROVIDER)
from atomicapp.utils import Utils
from atomicapp.requirements import Requirements
from atomicapp.nulecule.lib import NuleculeBase
from atomicapp.nulecule.container import DockerHandler
from atomicapp.nulecule.exceptions import NuleculeException

from jsonpointer import resolve_pointer, set_pointer, JsonPointerException

logger = logging.getLogger(__name__)


class Nulecule(NuleculeBase):

    """
    This represents an application compliant with Nulecule specification.
    A Nulecule instance can have instances of Nulecule and Nulecule as
    components. A Nulecule instance knows everything about itself and its
    componenents, but does not have access to its parent's scope.
    """

    def __init__(self, id, specversion, metadata, graph, basepath,
                 requirements=None, params=None, config=None,
                 namespace=GLOBAL_CONF):
        """
        Create a Nulecule instance.

        Args:
            id (str): Nulecule application ID
            specversion (str): Nulecule spec version
            metadata (dict): Nulecule metadata
            graph (list): Nulecule graph of components
            basepath (str): Basepath for Nulecule application
            requirements (dict): Requirements for the Nulecule application
            params (list): List of params for the Nulecule application
            config (dict): Config data for the Nulecule application
            namespace (str): Namespace of the current Nulecule application

        Returns:
            A Nulecule instance
        """
        super(Nulecule, self).__init__(basepath, params, namespace)
        self.id = id
        self.specversion = specversion
        self.metadata = metadata
        self.graph = graph
        self.requirements = requirements
        self.config = config or {}

    @classmethod
    def unpack(cls, image, dest, config=None, namespace=GLOBAL_CONF,
               nodeps=False, dryrun=False, update=False):
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
        logger.info('Unpacking image: %s to %s' % (image, dest))
        docker_handler = DockerHandler(dryrun=dryrun)
        docker_handler.pull(image)
        docker_handler.extract(image, APP_ENT_PATH, dest, update)
        return cls.load_from_path(
            dest, config=config, namespace=namespace, nodeps=nodeps,
            dryrun=dryrun, update=update)

    @classmethod
    def load_from_path(cls, src, config=None, namespace=GLOBAL_CONF,
                       nodeps=False, dryrun=False, update=False):
        """
        Load a Nulecule application from a path in the source path itself, or
        in the specified destination path.

        Args:
            src (str): Path to load Nulecule application from.
            config (dict): Config data for Nulecule application.
            namespace (str): Namespace for Nulecule application.
            nodeps (bool): Do not pull external applications if True.
            dryrun (bool): Do not make any change to underlying host.
            update (bool): Update existing application if True, else reuse it.

        Returns:
            A Nulecule instance or None in case of some dry run (installing
            from image).
        """
        nulecule_path = os.path.join(src, MAIN_FILE)
        if dryrun and not os.path.exists(nulecule_path):
            raise NuleculeException("Installed Nulecule components are required to initiate dry-run. "
                                    "Please specify your app via atomicapp --dry-run /path/to/your-app")
        nulecule_data = anymarkup.parse_file(nulecule_path)
        nulecule = Nulecule(config=config, basepath=src,
                            namespace=namespace, **nulecule_data)
        nulecule.load_components(nodeps, dryrun)
        return nulecule

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

        # Process preliminary requirements
        # Pass configuration, path of the app, graph, provider as well as dry-run
        # for provider init()
        if REQUIREMENTS_KEY in self.graph[0]:
            logger.debug("Requirements key detected. Running action.")
            r = Requirements(self.config, self.basepath, self.graph[0][REQUIREMENTS_KEY],
                             provider_key, dryrun)
            r.run()

        # Process components
        for component in self.components:
            component.run(provider_key, dryrun)

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
        for component in self.components:
            component.stop(provider_key, dryrun)

    # TODO: NOT YET IMPLEMENTED
    def uninstall(self):
        for component in self.components:
            component.uninstall()

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
        super(Nulecule, self).load_config(
            config=config, ask=ask, skip_asking=skip_asking)

        if not self.config[GLOBAL_CONF].get(PROVIDER_KEY):
            self.config[GLOBAL_CONF][PROVIDER_KEY] = (
                self.metadata.get(DEFAULTPROVIDER_KEY) or
                DEFAULT_PROVIDER
            )
        for component in self.components:
            # FIXME: Find a better way to expose config data to components.
            #        A component should not get access to all the variables,
            #        but only to variables it needs.
            component.load_config(config=copy.deepcopy(self.config),
                                  ask=ask, skip_asking=skip_asking)
            self.merge_config(self.config, component.config)

    def load_components(self, nodeps=False, dryrun=False):
        """
        Load components for the Nulecule application. Sets a list of
        NuleculeComponent instances to self.components.

        Args:
            nodeps (bool): When True, do not external dependencies of a
                           Nulecule component
            dryrun (bool): When True, do not make any change to the host
                           system

        Returns:
            None
        """
        components = []
        for node in self.graph:
            node_name = node[NAME_KEY]
            source = Utils.getSourceImage(node)
            component = NuleculeComponent(
                node_name, self.basepath, source,
                node.get(PARAMS_KEY), node.get(ARTIFACTS_KEY))
            component.load(nodeps, dryrun)
            components.append(component)
        self.components = components

    def render(self, provider_key=None, dryrun=False):
        """
        Render the artifact files for the entire Nulecule application from
        config data.

        Args:
            provider_key (str): Provider for which artifacts need to be
                                rendered. If it's None, we render artifacts
                                for all providers.
            dryrun (bool): Do not make any change to the host system when True

        Returns:
            None
        """
        for component in self.components:
            component.render(provider_key=provider_key, dryrun=dryrun)


class NuleculeComponent(NuleculeBase):

    """
    Represents a component in a Nulecule application. It receives props
    from its parent and can add new props and override props at its local
    scope. It does not have direct access to props of sibling Nulecule
    components, but can request the value of sibling's property from its
    parent.
    """

    def __init__(self, name, basepath, source=None, params=None,
                 artifacts=None, config=None):
        super(NuleculeComponent, self).__init__(basepath, params, name)
        self.name = name
        self.source = source
        self.artifacts = artifacts
        self.rendered_artifacts = defaultdict(list)
        self._app = None

    def load(self, nodeps=False, dryrun=False):
        """
        Load external application of the Nulecule component.
        """
        if self.source:
            if nodeps:
                logger.info(
                    'Skipping to load external application: %s' % self.name)
            else:
                self.load_external_application(dryrun)

    def run(self, provider_key, dryrun=False):
        """
        Run the Nulecule component with the specified provider,
        """
        if self._app:
            self._app.run(provider_key, dryrun)
            return
        provider_key, provider = self.get_provider(provider_key, dryrun)
        provider.artifacts = self.rendered_artifacts.get(provider_key, [])
        provider.init()
        provider.deploy()

    def stop(self, provider_key=None, dryrun=False):
        """
        Stop the Nulecule component with the specified provider.
        """
        if self._app:
            self._app.stop(provider_key, dryrun)
            return
        provider_key, provider = self.get_provider(provider_key, dryrun)
        provider.artifacts = self.rendered_artifacts.get(provider_key, [])
        provider.init()
        provider.undeploy()

    def load_config(self, config=None, ask=False, skip_asking=False):
        """
        Load config for the Nulecule component.
        """
        super(NuleculeComponent, self).load_config(
            config, ask=ask, skip_asking=skip_asking)
        if isinstance(self._app, Nulecule):
            self._app.load_config(config=copy.deepcopy(self.config),
                                  ask=ask, skip_asking=skip_asking)
            self.merge_config(self.config, self._app.config)

    def load_external_application(self, dryrun=False, update=False):
        """
        Loads an external application for the NuleculeComponent.

        Args:
            dryrun (bool): When True, skips pulling an external application.
            update (bool): When True, it ignores an already pulled external
                           application, and tries to pull the external
                           application and update the existing one.

        Returns:
            A Nulecule instance or None
        """
        nulecule = None
        external_app_path = os.path.join(
            self.basepath, EXTERNAL_APP_DIR, self.name)
        if os.path.isdir(external_app_path) and not update:
            logger.info(
                'Found existing external application for %s. '
                'Loading it.' % self.name)
            nulecule = Nulecule.load_from_path(
                external_app_path, dryrun=dryrun, update=update)
        elif not dryrun:
            logger.info('Pulling external application for %s.' % self.name)
            nulecule = Nulecule.unpack(
                self.source,
                external_app_path,
                namespace=self.namespace,
                dryrun=dryrun,
                update=update
            )
        self._app = nulecule

    @property
    def components(self):
        """
        If the Nulecule component is an external application, list Nulecule
        components of the external Nulecule application.
        """
        if self._app:
            return self._app.components

    def render(self, provider_key=None, dryrun=False):
        """
        Render the artifact files for the Nuelcule component. If the component
        is an external Nulecule application, recurse into it to load it and
        render it's artifacts. If provider_key is specified, render artifacts
        only for that provider, else, render artifacts for all providers.

        Args:
            provider_key (str or None): Provider name.

        Returns:
            None
        """
        if self._app:
            self._app.render(provider_key=provider_key, dryrun=dryrun)
            return
        context = self.get_context()
        if provider_key and provider_key not in self.artifacts:
            raise NuleculeException(
                "Data for provider \"%s\" are not part of this app"
                % provider_key)
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
        for artifact in artifacts:
            # Convert dict if the Nulecule file references "resource"
            if isinstance(artifact, dict) and artifact.get(RESOURCE_KEY):
                artifact = artifact[RESOURCE_KEY]
                logger.debug("Resource xpath added: %s" % artifact)

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

    def apply_pointers(self, content, params):
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
        obj = anymarkup.parse(content)

        if type(obj) != dict:
            logger.debug("Artifact file not json/haml, assuming it's $VARIABLE substitution")
            return content

        if params is None:
            # Nothing to do here!
            return content

        for name, pointers in params.items():

            if not pointers:
                logger.warning("Could not find pointer for %s" % name)
                continue

            for pointer in pointers:
                try:
                    resolve_pointer(obj, pointer)
                    set_pointer(obj, pointer, name)
                    logger.debug("Replaced %s pointer with %s param" % (pointer, name))
                except JsonPointerException:
                    logger.debug("Error replacing %s with %s" % (pointer, name))
                    logger.debug("Artifact content: %s", obj)
                    raise NuleculeException("Error replacing pointer %s with %s." % (pointer, name))
        return anymarkup.serialize(obj, format="json")

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

    def _get_artifact_paths_for_path(self, path):
        """
        Get artifact paths for a local filesystem path. We support path to
        an artifact file or a directory containing artifact files as its
        immediate children, i.e., we do not deal with nested artifact
        directories at this moment.

        Args:
            path (str): Local path

        Returns:
            list: A list of artifact paths
        """
        artifact_paths = []
        if os.path.isfile(path):
            artifact_paths.append(path)
        elif os.path.isdir(path):
            for dir_child in os.listdir(path):
                dir_child_path = os.path.join(path, dir_child)
                if dir_child.startswith('.') or os.path.isdir(dir_child_path):
                    continue
                artifact_paths.append(dir_child_path)
        return artifact_paths
