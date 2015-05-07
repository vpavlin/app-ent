#!/usr/bin/env python

from __future__ import print_function
import os, sys
import subprocess
import urllib2
import collections
import anymarkup
import copy

from atomicapp.params import Params
from atomicapp.constants import SCHEMA_URL

import logging

logger = logging.getLogger(__name__)

class Core():
    def __init__(self, app, schema = SCHEMA_URL):
        self.params = Params()
        logger.debug(os.path.exists(app))
        if os.path.exists(app):
            self.params.loadMainfile(app)
        else:
            self.params.app = app

        self.params.loadSchema(schema)

    def addComponent(self, name, data):
        logger.debug("Adding %s with %s" % (name, data))
        parent, component = self._findObject("graph.component")

        logger.debug(component["description"])
        logger.debug({name: self._generateContents(component["value"], "root.graph.component")})

    def addMetadataItem(self, name, data):
        logger.debug("Adding %s with %s" % (name, data))

    def addArtifact(self, component, provider, data):
        logger.debug("Adding artifact to %s:%s with %s" % (component, provider, data))
        #parent, component = self._findObject("graph.component.artifacts.provider")

        #logger.debug(self._generateContents(component["value"], "root.graph.component.artifacts.provider", data))
        if component in self.params.mainfile_data["graph"]:
            if not "artifacts" in self.params.mainfile_data["graph"][component]:
                self.params.mainfile_data["graph"][component]["artifacts"] = {}

            if not provider in self.params.mainfile_data["graph"][component]["artifacts"]:
                self.params.mainfile_data["graph"][component]["artifacts"][provider] = []

            if provider in self.params.mainfile_data["graph"][component]["artifacts"]:
                self.params.mainfile_data["graph"][component]["artifacts"][provider].append(data["artifact"])
        else:
            logger.error("Component %s does not exist" % component)

        logger.debug(self.params.mainfile_data)

    def addParam(self, component, name, data):
        logger.debug("Adding %s with %s" % (name, data))


    def loadMainfileToSchema(self):
        nulecule = None
        for element in self.params.schema["elements"]:
            if element["name"] == "Atomicfile":
                nulecule = copy.deepcopy(element["contents"])

        result = copy.deepcopy(nulecule)

        self.fillNulecule(nulecule, result, self.params.mainfile_data)
        anymarkup.serialize_file(result, "test.yaml")
        anymarkup.serialize_file(self._generateContents(result, ask_if_null=False), "test2.yaml")


    def fillNulecule(self, nulecule, result, data):
        logger.debug("%s \nvs\n%s" % (result.keys(), nulecule.keys()))
        remove_after = set()
        for element, content in nulecule.iteritems():
            
            names = []
            value = None
            if "name" in content:
                if not content["name"] or content["type"] == "list":
                    if data:
                        for nc_item, nc_content in data.iteritems():
                            logger.debug("Next name: %s" % nc_item)
                            names.append(nc_item)
                    else:
                        names.append(element)
            else:
                names.append(element)
            
            for name in names:
                logger.debug("Name: %s, Element: %s, Data: %s" % (name,element,data))
                if not name in result:
                    logger.debug("Setting name %s -> %s" % (element, name))
                    result[name] = copy.deepcopy(content)
                    result[name]["name"] = name

                if content["type"] == "object":
                    new_data = data[name] if data and name in data else None
                    self.fillNulecule(content["value"], result[name]["value"], new_data)
                else:
                    result[name]["value"] = data[name] if data and name in data else None

            if not element in names and element in result:
                logger.debug("Removing %s" % element)
                remove_after.add(element)

        for element in remove_after:
            del result[element]







    def _findObject(self, path):
        parent = None
        this = None

        stack = path.split(".")
        logger.debug(stack)
        contents = None
        MAIN_FILE = "Atomicfile" #FIXME
        for element in self.params.schema["elements"]:
            if element["name"] == MAIN_FILE:
                contents = element["contents"]

        this = contents
        for part in stack:
            logger.debug(part)

            parent = this
            this = this[part]["value"]

        return parent, parent[part]

    def _generateContents(self, contents, path="root", data=None, ask_if_null=True):
        result = {}
        for element, content in contents.iteritems():

            local_path = "%s.%s" % (path, element)
            
            name = self._getName(element, content, local_path, ask_if_null)
            if not ask_if_null and not name:
                continue

            print("Filling %s" % name)
            if ask_if_null and not content["required"]:
                skip = self.params._askFor("Element %s not required, do you want to skip it?" % name, {"description": "Type y or n", "default": "Y"})
                if self.params._isTrue(skip):
                    continue
            #logger.debug("Key: %s, value %s" % (element, content["value"]))

            if content["type"] == "object":
                value = self._generateContents(content["value"], local_path, data, ask_if_null)
            elif ask_if_null and not value and content["type"] == "list":
                logger.debug(ask_if_null)
                tmp_results = []
                while True:
                    value = self.params._askFor(content["value"].keys()[0], content["value"][content["value"].keys()[0]])
                    if len(value) == 0:
                        break
                    tmp_results.append(value)

                result[name] = tmp_results
            else:
                if data and name in data:
                    value = data[name]
                elif ask_if_null and not content["value"]:
                    logger.debug(local_path)
                    value = self._generateValue(local_path)
                    if  not value:
                        value = self.params._askFor(element, content)
                    logger.debug(value)
                else:
                    value = content["value"]
            if value:        
                result[name] = value
        if result == {}:
            result = None
        return result

    def _pickOne(self, what, info, options):
        options_text = ""
        for i, option in enumerate(options):
            options_text += "%s. %s\n" % (i+1, option)

        required = False

        if "required" in info:
            required = info["required"]

        value = raw_input("%s (%s)\n Options:\n%s\nYour choice (default: 1): " % (what, info["description"], options_text))
        if len(value) == 0:
            value = 1
        elif int(value) == 0 and not required:
            return None

        return options[int(value)-1]

    def _getName(self, element, content, path = None, ask_if_null=True):
        name = None
        if not "name" in content:
            name = element
        elif ask_if_null and not content["name"]:
            name = self._generateValue(path)
            if not name:
                name = self.params._askFor(element, content)
        elif ask_if_null and type(content["name"]) is list:
            name = self._pickOne(element, content, content["name"])
        else:
            if "name" in content and not type(content["name"]) == list:
                name = content["name"]
            else:
                name = None

        logger.debug(name)

        return name
  
    def _generateValue(self, element):
        if element == "root.id":
            return self.app_id
        elif element == "root.metadata.name":
            return self.name
        elif element == "root.graph.component":
            return self.app_id

        return None
