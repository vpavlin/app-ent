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

import anymarkup
import urlparse
import os
from atomicapp.plugin import Provider, ProviderFailedException
from atomicapp.utils import printErrorStatus
from atomicapp.utils import Utils
from atomicapp.constants import PROVIDER_API_KEY
from atomicapp.display import Display


class Marathon(Provider):

    key = "marathon"
    config_file = None
    marathon_api_version = "v2"
    # use localhost as default, when no providerurl is specified
    marathon_api = "http://localhost:8080/%s/" % marathon_api_version
    marathon_artifacts = []

    def init(self):
        self.marathon_artifacts = []
        self.display = Display()

        self.display.debug("Given config: %s" % self.config)
        if self.config.get(PROVIDER_API_KEY):
            self.marathon_api = self.config.get(PROVIDER_API_KEY)
            self.marathon_api = urlparse.urljoin(self.marathon_api, "v2/")

        self.display.debug("marathon_api = %s" % self.marathon_api)
        self._process_artifacts()

    def run(self):
        """ Deploys the app by given resource manifests.
        """
        for artifact in self.marathon_artifacts:
            url = urlparse.urljoin(self.marathon_api, "apps/")

            if self.dryrun:
                self.display.info("DRY-RUN: %s" % url)
                continue

            self.display.debug("Deploying appid: %s" % artifact["id"])
            (status_code, return_data) = \
                Utils.make_rest_request("post", url, data=artifact)
            if status_code == 201:
                self.display.info(
                    "Marathon app %s sucessfully deployed." %
                    artifact["id"])
            else:
                msg = "Error deploying app: %s, Marathon API response %s - %s" % (
                    artifact["id"], status_code, return_data)
                self.display.error(msg)
                raise ProviderFailedException(msg)

    def stop(self):
        """ Undeploys the app by given resource manifests.
        Undeploy operation deletes Marathon apps from cluster.
        """
        for artifact in self.marathon_artifacts:
            url = urlparse.urljoin(
                self.marathon_api,
                "apps/%s" %
                artifact["id"])

            if self.dryrun:
                self.display.info("DRY-RUN: %s" % url)
                continue

            self.display.debug("Deleting appid: %s" % artifact["id"])
            (status_code, return_data) =  \
                Utils.make_rest_request("delete", url, data=artifact)
            if status_code == 200:
                self.display.info(
                    "Marathon app %s sucessfully deleted." %
                    artifact["id"])
            else:
                msg = "Error deleting app: %s, Marathon API response %s - %s" % (
                    artifact["id"], status_code, return_data)
                self.display.error(msg)
                raise ProviderFailedException(msg)

    def _process_artifacts(self):
        """ Parse and validate Marathon artifacts
        Parsed artifacts are saved  to self.marathon_artifacts
        """
        for artifact in self.artifacts:
            self.display.debug("Procesesing artifact: %s" % artifact)
            data = None
            with open(os.path.join(self.path, artifact), "r") as fp:
                try:
                    # env variables in marathon artifacts have to be string:string
                    # force_types=None respects types from json file
                    data = anymarkup.parse(fp, force_types=None)
                    self.display.debug("Parsed artifact %s" % data)
                    # every marathon app has to have id. 'id' key  is also used for showing messages
                    if "id" not in data.keys():
                        msg = "Error processing %s artifact. There is no id" % artifact
                        printErrorStatus(msg)
                        raise ProviderFailedException(msg)
                except anymarkup.AnyMarkupError, e:
                    msg = "Error processing artifact - %s" % e
                    printErrorStatus(msg)
                    raise ProviderFailedException(msg)
                self.marathon_artifacts.append(data)
