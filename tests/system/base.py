import os
import anymarkup
import datetime
import unittest
import subprocess
from collections import OrderedDict
import tempfile


class BaseProviderTestSuite(unittest.TestCase):
    """
    Base test suite for a provider: docker, kubernetes, etc.
    """

    def setUp(self):
        self.get_initial_state()

    def tearDown(self):
        self.restore_initial_state()

    def get_initial_state(self):
        raise NotImplementedError

    def restore_initial_state(self):
        raise NotImplementedError

    def deploy(self, app_spec, answers):
        """
        Deploy to provider
        """
        raise NotImplementedError

    def undeploy(self, app_spec, answers):
        """
        Undeploy from provider
        """
        raise NotImplementedError

    def get_tmp_answers_file(self, answers):
        f = tempfile.NamedTemporaryFile(delete=False, suffix='.conf')
        f.close()
        anymarkup.serialize_file(answers, f.name, format='ini')
        return f.name

    @property
    def nulecule_lib(self):
        return os.environ['NULECULE_LIB']


class DockerProviderTestSuite(BaseProviderTestSuite):
    pass


class KubernetesProviderTestSuite(BaseProviderTestSuite):
    """
    Base test suite for Kubernetes.
    """

    def tearDown(self):
        pods = self._get_pods()
        services = self._get_services()
        rcs = self._get_rcs()

        # clean up newly created pods
        for pod in pods:
            if pod not in self._pods:
                subprocess.check_output(['/usr/bin/kubectl', 'delete', 'pod', pod])

        # clean up newly created services
        for service in services:
            if service not in self._services:
                subprocess.check_output(['/usr/bin/kubectl', 'delete', 'service', service])

        # clean up newly created rcs
        for rc in rcs:
            if rc not in self._rcs:
                subprocess.check_output(['/usr/bin/kubectl', 'delete', 'rc', rc])

    def deploy(self, app_spec, answers):
        """
        Deploy app to kuberntes

        Args:
            app_spec (str): image name or path to application
            answers (dict): Answers data

        Returns:
            Path of the deployed dir.
        """
        destination = tempfile.mkdtemp()
        answers_path = self.get_tmp_answers_file(answers)
        cmd = ['atomicapp', 'run', '--answers=%s' % answers_path,
               '--provider=kubernetes',
               '--destination=%s' % destination, app_spec]
        subprocess.check_output(cmd)
        return destination

    def undeploy(self, workdir):
        """
        Undeploy app from kubernetes.

        Args:
            workdir (str): Path to deployed application dir
        """
        cmd = ['atomicapp', 'stop', workdir]
        subprocess.check_output(cmd)

    def assertPod(self, name, exists=True, status=None, timeout=1):
        """
        Assert a kubernetes pod, if it exists, what's its status.

        We can also set a timeout to wait for the pod to
        get to the desired state.
        """
        start = datetime.datetime.now()
        cmd = ['/usr/bin/kubectl', 'get', 'pod', name]
        while (datetime.datetime.now() - start).total_seconds() <= timeout:
            try:
                output = subprocess.check_output(cmd)
            except subprocess.CalledProcessError:
                if exists is False:
                    return True
                continue
            for line in output.splitlines()[1:]:
                pod = self._get_pod_details(line)
                result = True
                if status is not None:
                    if pod['status'] == status:
                        result = result and True
                    else:
                        result = result and False
                if result:
                    return True
            else:
                if exists is False:
                    return True
        if exists:
            message = "Pod: %s does not exist" % name
            if status is not None:
                message += ' with status: %s' % status
        else:
            message = "Pod: %s exists." % name
        raise AssertionError(message)

    def assertService(self, name, exists=True, timeout=1):
        """
        Assert a kubernetes service, if it exists.

        We can also set a timeout to wait for the service to
        get to the desired state.
        """
        cmd = ['/usr/bin/kubectl', 'get', 'service', name]
        start = datetime.datetime.now()
        while (datetime.datetime.now() - start).total_seconds() <= timeout:
            try:
                output = subprocess.check_output(cmd)
            except subprocess.CalledProcessError:
                if exists is False:
                    return True
                continue
            for line in output.splitlines()[1:]:
                return True
            else:
                if exists is False:
                    return True
        if exists:
            message = "Service: %s does not exist" % name
        else:
            message = "Service: %s exists." % name
        raise AssertionError(message)

    def assertRc(self, name, exists=True, timeout=1):
        """
        Assert a kubernetes rc, if it exists.

        We can also set a timeout to wait for the rc to
        get to the desired state.
        """
        cmd = ['/usr/bin/kubectl', 'get', 'rc', name]
        start = datetime.datetime.now()
        while (datetime.datetime.now() - start).total_seconds() <= timeout:
            try:
                output = subprocess.check_output(cmd)
            except subprocess.CalledProcessError:
                if exists is False:
                    return True
                continue
            for line in output.splitlines()[1:]:
                return True
            else:
                if exists is False:
                    return True
        if exists:
            message = "RC: %s does not exist" % name
        else:
            message = "RC: %s exists." % name
        raise AssertionError(message)

    def get_initial_state(self):
        """Save initial state of the provider"""
        self._services = self._get_services()
        self._pods = self._get_pods()
        self._rcs = self._get_rcs()

    def _get_services(self):
        output = subprocess.check_output(['/usr/bin/kubectl', 'get', 'services'])
        services = OrderedDict()
        for line in output.splitlines()[1:]:
            service = self._get_service_details(line)
            services[service['name']] = service
        return services

    def _get_service_details(self, line):
        name, labels, selector, ips, ports = line.split()
        service = {
            'name': name,
            'labels': labels,
            'selector': selector,
            'ips': ips,
            'ports': ports
        }
        return service

    def _get_pods(self):
        output = subprocess.check_output(['/usr/bin/kubectl', 'get', 'pods'])
        pods = OrderedDict()
        for line in output.splitlines()[1:]:
            pod = self._get_pod_details(line)
            pods[pod['name']] = pod
        return pods

    def _get_pod_details(self, line):
        name, ready, status, restarts, age = line.split()
        pod = {
            'name': name,
            'ready': ready,
            'status': status,
            'restarts': restarts,
            'age': age
        }
        return pod

    def _get_rcs(self):
        output = subprocess.check_output(['/usr/bin/kubectl', 'get', 'rc'])
        rcs = OrderedDict()
        for line in output.splitlines()[1:]:
            rc = self._get_rc_details(line)
            rcs[rc['controller']] = rc
        return rcs

    def _get_rc_details(self, line):
        controller, container, image, selector, replicas = line.split()
        rc = {
            'controller': controller,
            'container': container,
            'image': image,
            'selector': selector,
            'replicas': replicas
        }
        return rc
