#!/usr/bin/env python

import anymarkup
import os
import logging
import collections

from constants import MAIN_FILE, GLOBAL_CONF, DEFAULT_PROVIDER

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
        if GLOBAL_CONF in config:
            if "provider" in config[GLOBAL_CONF]:
                return config[GLOBAL_CONF]["provider"]
        return self.__provider

    def __init__(self, recursive=True, update=False, target_path=None):
        self.target_path = target_path
        self.recursive = self._isTrue(recursive)
        self.update = self._isTrue(update)

    def loadParams(self, data = {}):
        if os.path.exists(data):
            logger.debug("Path given, loading %s" % data)
            data = anymarkup.parse_file(data)
        else:
            logger.debug("Data given: %s" % data)

        if "specversion" in data:
            logger.debug("Params part of %s" % MAIN_FILE)
            data = data[PARAMS_KEY]
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

        return self.mainfile_data

    def loadAnswers(self, data = {}):
        if os.path.exists(data):
            logger.debug("Path to answers file given, loading %s" % data)
            data = anymarkup.parse_file(data)
        elif not len(data):
            raise Exception("No data answers data given")

        self.answers_data = data
        return self.answers_data

    def get(self, component = None):
        params = None
        if component:
            params = self._mergeParamsComponent(component)
        else:
            params = self._mergeParams()

        return params

    def _mergeParams(self):
        config = self.params_data
        if self.answers_data:
            if config:
                config = self._update(config, self.answers_data)
            else:
                config = self.answers_data

        return config

    def _mergeParamsComponent(self, component):
        config = self._mergeParams()
        component_config = config[GLOBAL_CONF] if GLOBAL_CONF in config else {}
        config = dict((name, p["default"] if "default" in p else None) 
                for name, p in self.mainfile_data["graph"][component]["params"].iteritems())
        component_config = self._update(component_config, config)

        return component_config

    def _update(self, old_dict, new_dict):
        for key, val in new_dict.iteritems():
            if isinstance(val, collections.Mapping):
                tmp = self._update(old_dict.get(key, { }), val)
                old_dict[key] = tmp
            elif isinstance(val, list):
                old_dict[key] = (old_dict[key] + val)
            else:
                old_dict[key] = new_dict[key]
        return old_dict

    def _isTrue(self, val):
        return True if str(val).lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'sure'] else False

    
