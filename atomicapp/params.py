#!/usr/bin/env python

import anymarkup
import os
import logging
import collections
import re
import pprint
from collections import OrderedDict

from constants import MAIN_FILE, GLOBAL_CONF, DEFAULT_PROVIDER, PARAMS_KEY, ANSWERS_FILE, DEFAULT_ANSWERS

import utils


logger = logging.getLogger(__name__)

class Params(object):
    answers_data = None
    params_data = None
    mainfile_data = None
    target_path = None
    recursive = True
    app_id = None
    app_path = None
    __provider = DEFAULT_PROVIDER
    __app = None
    ask = False

    @property
    def app(self):
        if not self.__app and self.mainfile_data:
            self.__app = self.app_id
        return self.__app

    @app.setter
    def app(self, val):
        self.__app = val

    @property
    def provider(self):
        config = self.get()
        if "provider" in config:
            return config["provider"]
        return self.__provider

    def __init__(self, recursive=True, update=False, target_path=None):
        self.target_path = target_path
        self.recursive = self._isTrue(recursive)
        self.update = self._isTrue(update)
        self.override = self._isTrue(False)

    def loadParams(self, data = {}):
        if type(data) == dict:
            logger.debug("Data given: %s" % data)
        elif os.path.exists(data):
            logger.debug("Path given, loading %s" % data)
            data = anymarkup.parse_file(data)
        else:
            raise Exception("Given params are broken: %s" % data)

        if "specversion" in data:
            logger.debug("Params part of %s" % MAIN_FILE)
            tmp = {}
            tmp[GLOBAL_CONF] = data[PARAMS_KEY]
            data = tmp
        else:
            logger.debug("Params in separate file")

        if self.params_data:
                self.params_data = self._update(self.params_data, data)
        else:
            self.params_data = data

        return self.params_data

    def loadMainfile(self, path = None):
        if not os.path.exists(path):
            raise Exception("%s not found: %s" % (MAIN_FILE, path))

        self.mainfile_data = anymarkup.parse_file(path)
        logger.debug("Setting app id to %s" % self.mainfile_data["id"])
        if "id" in self.mainfile_data:
            self.app_id = self.mainfile_data["id"]
        else:
            raise Exception ("Missing ID in %s" % self.mainfile_data)

        if PARAMS_KEY in self.mainfile_data:
            logger.debug("Loading params")
            self.loadParams(self.mainfile_data)


        return self.mainfile_data

    def loadAnswers(self, data = {}):
        if not data:
            raise Exception("No data answers data given")

        if type(data) == dict:
            logger.debug("Data given %s" % data)
        elif os.path.exists(data):
            logger.debug("Path to answers file given, loading %s" % data)
            if os.path.isdir(data):
                if os.path.isfile(os.path.join(data, ANSWERS_FILE)):
                    data = os.path.isfile(os.path.join(data, ANSWERS_FILE))
                else:
                    logger.warning("No answers file found.")
                    data = DEFAULT_ANSWERS

            if os.path.isfile(data):
                data = anymarkup.parse_file(data)
        else:
            logger.warning("No answers file found.")
            data = DEFAULT_ANSWERS

        if self.answers_data:
            self.answers_data = self._update(self.answers_data, data)
        else:
            self.answers_data = data
        return self.answers_data

    def get(self, component = None):
        params = None
        if component:
            params = self._mergeParamsComponent(component)
        else:
            params = self._mergeParamsComponent()#self._mergeParams()

        return params

    def getValues(self, component = GLOBAL_CONF):
        params = self.get(component)

        a = self._getComponentValues(params)
        for n, p  in a.iteritems():
            self._updateAnswers(component, n, p)
        return a


    def _mergeGlobalParams(self):
        config = self.params_data
        if self.answers_data:
            if config:
                config = self._update(config, self.answers_data)
            else:
                config = self.answers_data
        return config

    def _mergeParamsComponent(self, component=GLOBAL_CONF):
        component_config = self._mergeParamsComponent() if not component == GLOBAL_CONF else {}
        if component==GLOBAL_CONF:
            if self.mainfile_data and PARAMS_KEY in self.mainfile_data:
                component_config = self._update(component_config, self.mainfile_data[PARAMS_KEY])
        elif component in self.mainfile_data["graph"] and PARAMS_KEY in self.mainfile_data["graph"][component]:
            config = self.mainfile_data["graph"][component][PARAMS_KEY]
            component_config = self._update(component_config, config)

        if component in self.answers_data:
            component_config = self._update(component_config, self.answers_data[component])
        return component_config

    def _getValue(self, param, name):
        value = None
        if type(param) == dict:
            if "default" in param:
                value = param["default"]
            if (self.ask or not value) and "description" in param: #FIXME
                logger.debug("Ask for %s: %s" % (name, param["description"]))
                value = self._askFor(name, param)
            elif not value:
                logger.debug("Skipping %s" % name)
                value = param
        else:
            value = param

        return value

    def _getComponentValues(self, data):
        result = {}
        for name, p in data.iteritems():
            value = self._getValue(p, name)
            result[name] = value
        return result

    def _askFor(self, what, info):
        repeat = True
        desc = info["description"]
        const_text = ""
        constraints = None
        if "constraints" in info:
            constraints = info["constraints"]
        while repeat:
            repeat = False
            if "default" in info:
                value = raw_input("%s (%s, default: %s): " % (what, desc, info["default"]))
                if len(value) == 0:
                    value = info["default"]
            else:
                value = raw_input("%s (%s): " % (what, desc))
            if constraints:
                for constraint in constraints:
                    logger.debug("Checking pattern: %s" % constraint["allowed_pattern"])
                    if not re.match("^%s$" % constraint["allowed_pattern"], value):
                        logger.error(constraint["description"])
                        repeat = True

        return value

    def _updateAnswers(self, component, param, value):
        if not component in self.answers_data:
            self.answers_data[component] = {}

        if component != GLOBAL_CONF and param in self.answers_data[GLOBAL_CONF] and value == self.answers_data[GLOBAL_CONF][param]:
            logger.debug("Param %s already in %s with value %s" % (param, GLOBAL_CONF, value))
            return

        if not param in self.answers_data[component]:
            self.answers_data[component][param] = None

        self.answers_data[component][param] = value

    def writeAnswers(self, path):
        anymarkup.serialize_file(self.answers_data, path, format='yaml')

    def _update(self, old_dict, new_dict):
        for key, val in new_dict.iteritems():
            if isinstance(val, collections.Mapping):
                tmp = self._update(old_dict.get(key, { }), val)
                old_dict[key] = tmp
            elif isinstance(val, list) and key in old_dict:
                res = (old_dict[key] + val)
                if isinstance(val[0], collections.Mapping):
                    old_dict[key] = [dict(y) for y in set(tuple(x.items()) for x in res)]
                else:
                    old_dict[key] = list(set(res))
            else:
#                print("%s %s %s" % (old_dict, val, new_dict))
                old_dict[key] = new_dict[key]
        return old_dict

    def _isTrue(self, val):
        return True if str(val).lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'sure'] else False

    
