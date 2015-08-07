from atomicapp.plugin import Provider, ProviderFailedException

from collections import OrderedDict
import os, anymarkup, subprocess
from distutils.spawn import find_executable

import logging

logger = logging.getLogger(__name__)

class OpenShiftProvider(Provider):
    key = "openshift"
    cli_str = "oc"
    cli = None
    config_file = None
    template_data = None

    def init(self):
        self.cli = find_executable(self.cli_str)
        if self.container and not self.cli:
            host_path = []
            for path in os.environ.get("PATH").split(":"):
                host_path.append("/host%s" % path)
            self.cli = find_executable(self.cli_str, path=":".join(host_path))
            if not self.cli:
                # if run as non-root we need a symlink in the container
                os.symlink("/host/usr/bin/openshift", "/usr/bin/oc")
                self.cli = "/usr/bin/oc"

        if not self.cli or not os.access(self.cli, os.X_OK):
            raise ProviderFailedException("Command %s not found" % self.cli)
        else:
            logger.debug("Using %s to run OpenShift commands.", self.cli)

        if "openshiftconfig" in self.config:
            self.config_file = self.config["openshiftconfig"]
        else:
            logger.warning("Configuration option 'openshiftconfig' not found")

        if not self.config_file or not os.access(self.config_file, os.R_OK):
            raise ProviderFailedException("Cannot access configuration file %s" % self.config_file)

    def _callCli(self, path, action="create"):
        cmd = [self.cli, "--config=%s" % self.config_file, action, "-f", path]

        if self.dryrun:
            logger.info("Calling: %s", " ".join(cmd))
        else:
            subprocess.check_call(cmd)

    def _processTemplate(self, path):
        cmd = [self.cli, "--config=%s" % self.config_file, "process", "-f", path]

        name = "config-%s" % os.path.basename(path)
        output_path = os.path.join(self.path, name)
        if self.cli and not self.dryrun:
            output = subprocess.check_output(cmd)
            logger.debug("Writing processed template to %s", output_path)
            with open(output_path, "w") as fp:
                fp.write(output)
        return name

    def loadArtifact(self, path):
        data = super(self.__class__, self).loadArtifact(path)
        self.template_data = anymarkup.parse(data, force_types=None)
        if "kind" in self.template_data and self.template_data["kind"].lower() == "template":
            if "parameters" in self.template_data:
                return anymarkup.serialize(self.template_data["parameters"], format="json")

        return data

    def saveArtifact(self, path, data):
        if self.template_data:
            if "kind" in self.template_data and self.template_data["kind"].lower() == "template":
                if "parameters" in self.template_data:
                    passed_data = anymarkup.parse(data, force_types=None)
                    self.template_data["parameters"] = passed_data
                    data = anymarkup.serialize(self.template_data, format=os.path.splitext(path)[1].strip(".")) #FIXME

        super(self.__class__, self).saveArtifact(path, data)

    def deploy(self):
        kube_order = OrderedDict([("service", None), ("rc", None), ("pod", None)]) #FIXME
        for artifact in self.artifacts:
            data = None
            artifact_path = os.path.join(self.path, artifact)
            with open(artifact_path, "r") as fp:
                data = anymarkup.parse(fp, force_types=None)
            if "kind" in data:
                if data["kind"].lower() == "template":
                    logger.info("Processing template")
                    artifact = self._processTemplate(artifact_path)
                kube_order[data["kind"].lower()] = artifact
            else:
                raise ProviderFailedException("Malformed artifact file")

        for artifact in kube_order:
            if not kube_order[artifact]:
                continue

            k8s_file = os.path.join(self.path, kube_order[artifact])
            self._callCli(k8s_file)

    def undeploy(self):
        logger.info("Undeploying from OpenShift")
        for artifact in self.artifacts:
            data = None
            artifact_path = os.path.join(self.path, artifact)
            with open(artifact_path, "r") as fp:
                data = anymarkup.parse(fp, force_types=None)
            if "kind" in data:
                if data["kind"].lower() == "template":
                    raise NotImplementedError()
            self._callCli(artifact_path, "stop")

