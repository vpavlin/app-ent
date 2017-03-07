import copy
import logging

from atomicapp.constants import (GLOBAL_CONF,
                                 LOGGER_COCKPIT,
                                 DEFAULT_PROVIDER,
                                 DEFAULT_ANSWERS)
from collections import defaultdict

cockpit_logger = logging.getLogger(LOGGER_COCKPIT)


class Config(object):
    """
    This class allows to store config data in different scopes along with
    source info for the data. When fetching the value for a key in a scope,
    the source info and the PRIORITY order of sources is taken into account.

    Data sources:
        cli: Config data coming from the CLI
        runtime: Config data resolved during atomic app runtime. For example,
            when the value for a parameter in a Nulecule or Nulecule graph
            item is missing in answers data, we first try to load the default
            value for the parameter. When there's no default value, or when
            the user has specified to forcefully ask the user for values, we
            ask the user for data. These data collected/resolved during runtime
            form the runtime data.
        answers: Config data coming from answers file
        defaults: Default config data specified in atomicapp/constants.py

    The priority order of the data sources is:
    cli > runtime > answers > defaults
    """

    PRIORITY = (
        'cli',
        'runtime',
        'answers',
        'defaults'
    )

    def __init__(self, answers=None, cli=None):
        """
        Initialize a Config instance.

        Args:
            answers (dict): Answers data
            cli (dict): CLI data
        """
        answers = answers or {}
        cli = cli or {}
        # We use a defaultdict of defaultdicts so that we can avoid doing
        # redundant checks in a nested dictionary if the value of the keys
        # are dictionaries or None.
        self._data = defaultdict(defaultdict)
        # Initialize default data dict
        self._data['defaults'] = defaultdict(defaultdict)
        # Initialize answers data dict
        self._data['answers'] = defaultdict(defaultdict)
        # Initialize cli data dict
        self._data['cli'] = defaultdict(defaultdict)
        # Initialize runtime data dict
        self._data['runtime'] = defaultdict(defaultdict)

        # Load default answers
        for scope, data in DEFAULT_ANSWERS.items():
            for key, value in data.items():
                self.set(key, value, scope=scope, source='defaults')
        self.set('provider', DEFAULT_PROVIDER, scope=GLOBAL_CONF, source='defaults')

        # Load answers data
        for scope, data in answers.items():
            for key, value in data.items():
                self.set(key, value, scope=scope, source='answers')

        # Load cli data
        for key, value in cli.items():
            self.set(key, value, scope=GLOBAL_CONF, source='cli')

    def get(self, key, scope=GLOBAL_CONF, ignore_sources=[]):
        """
        Get the value of a key in a scope. This takes care of resolving
        the value by going through the PRIORITY order of the various
        sources of data.

        Args:
            key (str): Key
            scope (str): Scope from which to fetch the value for the key

        Returns:
            Value for the key.
        """
        for source in self.PRIORITY:
            if source in ignore_sources:
                continue
            value = self._data[source][scope].get(key) or self._data[source][
                GLOBAL_CONF].get(key)
            if value:
                return value
        return None

    def set(self, key, value, source, scope=GLOBAL_CONF):
        """
        Set the value for a key within a scope along with specifying the
        source of the value.

        Args:
            key (str): Key
            value: Value
            scope (str): Scope in which to store the value
            source (str): Source of the value
        """
        self._data[source][scope][key] = value

    def context(self, scope=GLOBAL_CONF):
        """
        Get context data for the scope of Nulecule graph item by aggregating
        the data from various sources taking their priority order into
        account. This context data, which is a flat dictionary, is used to
        render the variables in the artifacts of Nulecule graph item.

        Args:
            scope (str): Scope (or namespace) for the Nulecule graph item.
        Returns:
            A dictionary
        """
        result = {}
        for source in reversed(self.PRIORITY):
            source_data = self._data[source]
            result.update(copy.deepcopy(source_data.get(GLOBAL_CONF) or {}))
            if scope != GLOBAL_CONF:
                result.update(copy.deepcopy(source_data.get(scope) or {}))
        return result

    def runtime_answers(self):
        """
        Get runtime answers.

        Returns:
            A defaultdict containing runtime answers data.
        """
        answers = defaultdict(dict)

        for source in reversed(self.PRIORITY):
            for scope, data in (self._data.get(source) or {}).items():
                answers[scope].update(copy.deepcopy(data))

        # Remove empty sections for answers
        for key, value in answers.items():
            if not value:
                answers.pop(key)

        return answers

    def update_source(self, source, data):
        """
        Update answers data for a source.

        Args:
            source (str): Source name
            data (dict): Answers data
        """
        data = data or {}
        if source not in self._data:
            raise

        # clean up source data
        for k in self._data[source]:
            self._data[source].pop(k)

        for scope, data in data.items():
            for key, value in data.items():
                self.set(key, value, scope=scope, source=source)
