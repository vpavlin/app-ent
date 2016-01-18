import logging

from atomicapp.constants import REQUIREMENT_FUNCTIONS
from atomicapp.plugin import Plugin

logger = logging.getLogger(__name__)


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
        self.plugin.load_plugins()

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
        logging.debug("Checking if %s matches any of %s" %
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
            # if it does not: fail
            try:
                requirement = getattr(self.provider, requirement_function)
            except AttributeError:
                raise RequirementFailedException(
                    "Requirement %s does not exist within %s." %
                    (requirement_function, self.provider))

            # Run the requirement function
            requirement(req[key_name], action)


class RequirementFailedException(Exception):
    pass
