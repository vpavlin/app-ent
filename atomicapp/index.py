"""
 Copyright 2015 Red Hat, Inc.

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

# Based on https://github.com/DBuildService/dock/blob/master/dock/plugin.py

from __future__ import print_function
import os

import imp

import logging
from utils import Utils
from constants import DEFAULT_INDEX_IMAGE
from nulecule.base import Nulecule
from nulecule.container import DockerHandler

from git import Repo
import tempfile
from copy import deepcopy


import anymarkup

logger = logging.getLogger(__name__)


class Index(object):
    index_template = {"location": "", "nulecules": []}
   
    def __init__(self, dryrun=False):
        self.dryrun = dryrun
        self.index = deepcopy(self.index_template)
        self._load_index_file()

    def generate(self, location):
        self.index = deepcopy(self.index_template)
        if not os.path.exists(location):
            location = self._get_repo(location)

        if not os.path.isdir(location):
            raise Exception("Location has to be a directory")

        for f in os.listdir(location):
            nulecule_dir = os.path.join(location, f)
            if f.startswith("."):
                continue
            if os.path.isdir(nulecule_dir):
                index_info = self._nulecule_get_info(nulecule_dir)
                index_info["path"] = f
                self.index["nulecules"].append(index_info)

        if len(index_info) > 0:
            anymarkup.serialize_file(self.index, "gen_index.yaml", format="yaml")

    def fetch(self, index_image=DEFAULT_INDEX_IMAGE):
        dh = DockerHandler(self.dryrun)
        dh.pull(index_image)
        dh.extract(index_image, "/gen_index.yaml", ".")

    def list(self):
        for entry in self.index["nulecules"]:
            print(("{}{:>%s}   {}" % (50-len(entry["metadata"]["name"]))).format(entry["metadata"]["name"], entry["id"], entry["metadata"]["appversion"]))

    def info(self, app_id):

        entry = self._get_entry(app_id)
        if entry:
            self._print_entry(entry)

    def _nulecule_get_info(self, nulecule_dir):
        index_info = {}
        nulecule = Nulecule.load_from_path(
            nulecule_dir, nodeps=True, dryrun=self.dryrun)
        index_info["id"] = nulecule.id
        index_info["metadata"] = nulecule.metadata
        index_info["specversion"] = nulecule.specversion

        providers_set = set()
        for component in nulecule.components:
            if component.artifacts:
                if len(providers_set) == 0:
                    providers_set = set(component.artifacts.keys())
                else:
                    providers_set = providers_set.intersection(set(component.artifacts.keys()))
            print(providers_set)

        index_info["providers"] = list(providers_set)
        return index_info

    def _get_entry(self, app_id):
        for entry in self.index["nulecules"]:
            if entry["id"] == app_id:
                return entry
        return None

    def _print_entry(self, entry, tab=""):
        for key, val in entry.iteritems():
            if type(val) == dict:
                print("%s%s:" % (tab,key))
                self._print_entry(val, tab+"  ")
            elif type(val) == list:
                print("%s%s: %s" % (tab, key, ", ".join(val)))
            else:
                print("%s%s: %s" % (tab, key, val))
        
        if entry.get("path"):
            print("\n\nInclude as a graph component:\n\n"
                    "- name: %s\n" 
                    "  source: docker://%s/%s" % (entry["id"], "projectatomic", entry["path"]))

    def _load_index_file(self, index_file="gen_index.yaml"):
        if os.path.exists(index_file):
            self.index = anymarkup.parse_file(index_file)
        else:
            logger.warning("Couldn't load index file %s", index_file)

    def _get_repo(self, git_link):
        tmp = tempfile.mkdtemp(prefix="atomicapp-index-XXXXXX")
        self.index["location"] = git_link
        repo = Repo.clone_from(git_link, tmp)
        return tmp
