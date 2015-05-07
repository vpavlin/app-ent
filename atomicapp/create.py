#!/usr/bin/env python

from __future__ import print_function
import os, sys
import json, subprocess
import urllib2
import collections
import anymarkup

import logging

from params import Params

logger = logging.getLogger(__name__)

ANSWERS_FILE="answers.conf"
PARAMS_FILE="params.conf"
SCHEMA_URL="https://raw.githubusercontent.com/projectatomic/nulecule/master/spec/0.0.1-alpha/schema.json"
class Create():
    name = None
    app_id = None
    dryrun = False
    schema = None
    def __init__(self, name, schema = None, dryrun = False):
        self.name = name
        self.app_id = self._nameToId(name)
        self.dryrun = dryrun
        self.schema_path = schema

        if not self.schema_path: 
            self.schema_path = SCHEMA_URL

        self.params = Params()
        self.params.app = self.app_id

    def _loadSchema(self):    
        if not os.path.isfile(self.schema_path):
            response = urllib2.urlopen(self.schema_path)
            with open(os.path.basename(self.schema_path), "w") as fp:
                fp.write(response.read())
                self.schema_path = os.path.basename(self.schema_path)
        
        with open(self.schema_path, "r") as fp:
            self.schema = json.load(fp)

    def create(self):
        self._loadSchema()
        if self.schema and "elements" in self.schema:
            self._writeFromSchema(self.schema["elements"])
        else:
            print("Corrupted schema, couldn't create app")
    
    def build(self, tag):
        if not tag:
            tag = self.app_id

        cmd = ["docker", "build", "-t", tag, "."]
        if self.dryrun:
            print("Build: %s" % " ".join(cmd))
        else:
            subprocess.call(cmd)


    def _writeFromSchema(self, elements):
        for element in elements:
            value = element["value"]
            if not element["contents"] and not value:
                continue
            if element["name"] == "application":
                value = self.app_id
            print("Writing %s" % element["name"])
            if element["type"] == "directory":
                if value:
                    os.mkdir(value)
                    os.chdir(value)
                    self._writeFromSchema(element["contents"])
                    os.chdir("..")
                else:
                    logger.debug("No value for directory %s" % element["name"])
            elif element["type"] == "file":
                with open(value, "w") as fp:
                    logger.debug(element)
                    if element["contents"]:
                        if isinstance(element["contents"], str) or isinstance(element["contents"], unicode):
                            fp.write(element["contents"])
                        elif isinstance(element["contents"], collections.Mapping):
                            fp.write(anymarkup.serialize(self._generateContents(element["contents"]), format='yaml'))
#                        elif element["contentType"] == "application/json":
#                            if element["name"] == "Atomicfile":
#                                element["contents"] = self._updateAtomicfile(element["contents"])

#                            fp.write(json.dumps(element["contents"]))

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

    def _getName(self, element, content, path = None):
        name = None
        if not "name" in content:
            name = element
        elif not content["name"]:
            name = self._generateValue(path)
            if not name:
                name = self.params._askFor(element, content)
        elif type(content["name"]) is list:
            name = self._pickOne(element, content, content["name"])
        else:
            name = content["name"]

        logger.debug(name)

        return name
    
    def _generateContents(self, contents, path="root"):
        result = {}
        for element, content in contents.iteritems():

            local_path = "%s.%s" % (path, element)
            name = self._getName(element, content, local_path)

            print("Filling %s" % name)
            if not content["required"]:
                skip = self.params._askFor("Element %s not required, do you want to skip it?" % name, {"description": "Type y or n", "default": "Y"})
                if self.params._isTrue(skip):
                    continue
            #logger.debug("Key: %s, value %s" % (element, content["value"]))

            if content["type"] == "object":
                result[name] = self._generateContents(content["value"], local_path)
            elif content["type"] == "list":

                tmp_results = []
                while True:
                    value = self.params._askFor(content["value"].keys()[0], content["value"][content["value"].keys()[0]])
                    if len(value) == 0:
                        break
                    tmp_results.append(value)

                result[name] = tmp_results
            else:
                if not content["value"]:
                    logger.debug(local_path)
                    value = self._generateValue(local_path)
                    if not value:
                        value = self.params._askFor(element, content)
                    logger.debug(value)
                else:
                    value = content["value"]
                result[name] = value

        return result

    def _generateValue(self, element):
        if element == "root.id":
            return self.app_id
        elif element == "root.metadata.name":
            return self.name
        elif element == "root.graph.component":
            return self.app_id

        return None

    def _nameToId(self, name):
        return name.strip().lower().replace(" ", "-")

    def _updateAtomicfile(self, contents):
        print(contents)
        if "name" in contents:
            contents["name"] = self.name
        if "id" in contents:
            contents["id"] = self.app_id
        if "graph" in contents:
            component = {"repository": "", "name": self.app_id}
            contents["graph"].append(component)

        return contents

