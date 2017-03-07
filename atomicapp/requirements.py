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
import logging

from atomicapp.constants import (LOGGER_DEFAULT,
                                 REQUIREMENT_FUNCTIONS)
from atomicapp.plugin import Plugin

logger = logging.getLogger(LOGGER_DEFAULT)


class Requirements:

    """
    Requirements will search what is currently being used under
    the requirements section of Nulecule and deploy in accordance
    to the graph variables as well as whether or not said requirement
    exists within the provider.

    The REQUIREMENTS_FUNCTIONS dictionary maps all current requirement
    names to the function names for each provider.

    For example, the persistentVolume requirement in Nulecule is mapped as
    the persistent_storage function within each provider.

    Requirements tries to be as modular as possible.
    """

    def __init__(self, config, basepath, graph, provider, dryrun):
        self.plugin = Plugin()

        self.config = config
        self.basepath = basepath
        self.graph = graph
        self.dryrun = dryrun

        # We initialize the provider in order to gather provider-specific
        # information
        p = self.plugin.getProvider(provider)
        self.provider = p(config, basepath, dryrun)
        self.provider.init()

    def run(self):
        self._exec("run")

    def stop(self):
        self._exec("stop")

    # Find if the requirement does not exist within REQUIREMENT_FUNCTIONS
    def _find_requirement_function_name(self, key):
        logger.debug("Checking if %s matches any of %s" %
                     (key, REQUIREMENT_FUNCTIONS))
        if key in REQUIREMENT_FUNCTIONS.keys():
            return REQUIREMENT_FUNCTIONS[key]
        raise RequirementFailedException("Requirement %s does not exist." % key)

    # We loop through the given requirements graph and
    # execute each passed requirement
    def _exec(self, action):
        for req in self.graph:
            key_name = req.keys()[0]
            requirement_function = self._find_requirement_function_name(key_name)

            # Check to see if the function exists in the provider,
            # if it does not: warn the user
            try:
                requirement = getattr(self.provider, requirement_function)
            except AttributeError:
                logger.warning(
                    "Requirement %s does not exist within %s. Skipping." %
                    (requirement_function, self.provider))
                continue

            # Run the requirement function
            requirement(req[key_name], action)


class RequirementFailedException(Exception):
    pass
