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

from __future__ import print_function
import os

import logging
import errno
from constants import (INDEX_IMAGE,
                       INDEX_LOCATION,
                       INDEX_DEFAULT_IMAGE_LOCATION,
                       INDEX_GEN_DEFAULT_OUTPUT_LOC,
                       INDEX_NAME)
from nulecule.container import DockerHandler
from nulecule.base import Nulecule
from atomicapp.nulecule.exceptions import NuleculeException

from copy import deepcopy

import anymarkup
from atomicapp.utils import Utils

logger = logging.getLogger(__name__)


class IndexException(Exception):
    pass


class Index(object):

    """
    This class represents the 'index' command for Atomic App. This lists
    all available packaged applications to use.
    """

    index_template = {"location": ".", "nulecules": []}

    def __init__(self):

        self.index = deepcopy(self.index_template)
        self.index_location = os.path.join(Utils.getUserHome(), INDEX_LOCATION)
        self._load_index_file(self.index_location)

    def list(self):
        """
        This command lists all available Nulecule packaged applications in a
        properly formatted way.
        """

        # In order to "format" it correctly, find the largest length of 'name', 'id', and 'appversion'
        # Set a minimum length of '7' due to the length of each column name
        id_length = 7
        app_length = 7
        location_length = 7

        # Loop through each 'nulecule' and retrieve the largest string length
        for entry in self.index["nulecules"]:
            id = entry.get('id') or ""
            version = entry['metadata'].get('appversion') or ""
            location = entry['metadata'].get('location') or INDEX_DEFAULT_IMAGE_LOCATION

            if len(id) > id_length:
                id_length = len(id)
            if len(version) > app_length:
                app_length = len(version)
            if len(location) > location_length:
                location_length = len(location)

        # Print out the "index bar" with the lengths
        index_format = ("{0:%s}  {1:%s}  {2:10} {3:%s}" % (id_length, app_length, location_length))
        print(index_format.format("ID", "VER", "PROVIDERS", "LOCATION"))

        # Loop through each entry of the index and spit out the formatted line
        for entry in self.index["nulecules"]:
            # Get the list of providers (first letter)
            providers = ""
            for provider in entry["providers"]:
                providers = "%s,%s" % (providers, provider[0].capitalize())

            # Remove the first element, add brackets
            providers = "{%s}" % providers[1:]

            # Retrieve the entry information
            id = entry.get('id') or ""
            version = entry['metadata'].get('appversion') or ""
            location = entry['metadata'].get('location') or INDEX_DEFAULT_IMAGE_LOCATION

            # Print out the row
            print(index_format.format(
                id,
                version,
                providers,
                location))

    def update(self, index_image=INDEX_IMAGE):
        """
        Fetch the latest index image and update the file based upon
        the INDEX_IMAGE attribute. By default, this should pull the
        'official' Nulecule index.
        """

        logger.info("Updating the index list")
        logger.info("Pulling latest index image...")
        self._fetch_index_container()
        logger.info("Index updated")

    # TODO: Error out if the locaiton does not have a Nulecule file / dir
    def generate(self, location, output_location=INDEX_GEN_DEFAULT_OUTPUT_LOC):
        """
        Generate an index.yaml with a provided directory location
        """
        logger.info("Generating index.yaml from %s" % location)
        self.index = deepcopy(self.index_template)

        if not os.path.isdir(location):
            raise Exception("Location must be a directory")

        for f in os.listdir(location):
            nulecule_dir = os.path.join(location, f)
            if f.startswith("."):
                continue
            if os.path.isdir(nulecule_dir):
                try:
                    index_info = self._nulecule_get_info(nulecule_dir)
                except NuleculeException as e:
                    logger.warning("SKIPPING %s. %s" %
                                   (nulecule_dir, e))
                    continue
                index_info["path"] = f
                self.index["nulecules"].append(index_info)

        if len(index_info) > 0:
            anymarkup.serialize_file(self.index, output_location, format="yaml")
        logger.info("index.yaml generated")

    def _fetch_index_container(self, index_image=INDEX_IMAGE):
        """
        Fetch the index container
        """
        # Create the ".atomicapp" dir if it does not exist
        if not os.path.exists(os.path.dirname(self.index_location)):
            try:
                os.makedirs(os.path.dirname(self.index_location))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        dh = DockerHandler()
        dh.pull(index_image)
        dh.extract_files(index_image, "/" + INDEX_NAME, self.index_location)

    def _load_index_file(self, index_file=INDEX_LOCATION):
        """
        Load the index file. If it does not exist, fetch it.
        """
        # If the file/path does not exist, retrieve the index yaml
        if not os.path.exists(index_file):
            logger.warning("Couldn't load index file: %s", index_file)
            logger.info("Retrieving index...")
            self._fetch_index_container()
        self.index = anymarkup.parse_file(index_file)

    def _nulecule_get_info(self, nulecule_dir):
        """
        Get the required information in order to generate an index.yaml
        """
        index_info = {}
        nulecule = Nulecule.load_from_path(
            nulecule_dir, nodeps=True)
        index_info["id"] = nulecule.id
        index_info["metadata"] = nulecule.metadata
        index_info["specversion"] = nulecule.specversion

        if len(nulecule.components) == 0:
            raise IndexException("Unable to load any Nulecule components from folder %s" % nulecule_dir)

        providers_set = set()
        for component in nulecule.components:
            if component.artifacts:
                if len(providers_set) == 0:
                    providers_set = set(component.artifacts.keys())
                else:
                    providers_set = providers_set.intersection(set(component.artifacts.keys()))

        index_info["providers"] = list(providers_set)
        return index_info
