import distutils.dir_util
import os
import re
import logging
import logging.config
import time
import anymarkup
import datetime
import unittest
import subprocess
from collections import OrderedDict
import tempfile
import uuid

from .providers import kubernetes
from .providers import openshift

LOGGING_CONF = dict(
    version=1,
    formatters=dict(
        bare={
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "format": "[%(asctime)s][%(name)10s %(levelname)7s] %(message)s"
        },
    ),
    handlers=dict(
        console={
            "class": "logging.StreamHandler",
            "formatter": "bare",
            "level": "DEBUG",
            "stream": "ext://sys.stderr",
        }
    ),
    loggers=dict(
        test={
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console"],
        }
    )
)

logging.config.dictConfig(LOGGING_CONF)
logger = logging.getLogger('test')


class BaseProviderTestSuite(unittest.TestCase):
    """
    Base test suite for a provider: docker, kubernetes, etc.
    """

    NULECULE_LIB_REPO = 'https://github.com/projectatomic/nulecule-library'
    NULECULE_LIB_PATH = os.path.join(os.path.dirname(__file__),
                                     'nulecule-library')
    BUILD_DIR = os.path.join(os.path.dirname(__file__), 'build')
    PROVIDER = None

    @classmethod
    def setUpClass(cls):
        cls.fetch_nulecule_lib()
        cls.build()

    @classmethod
    def tearDownClass(cls):
        cls.remove_image()

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
        Deploy app to Docker

        Args:
            app_spec (str): image name or path to application
            answers (dict): Answers data

        Returns:
            Path of the deployed dir.
        """
        destination = self.BUILD_DIR
        answers_path = os.path.join(self.BUILD_DIR, 'answers.conf')
        anymarkup.serialize_file(answers,
                                 answers_path,
                                 format='ini')
        cmd = (
            'atomic run {app_spec} -a {answers} --provider={provider} '
            '--destination={dest}').format(
                app_spec=app_spec,
                answers=answers_path,
                provider=self.PROVIDER,
                dest=destination)
        subprocess.check_call(cmd, stdin=False, stderr=False, shell=True)
        return destination

    def undeploy(self, app_spec, workdir):
        """
        Undeploy app from Docker.

        Args:
            app_spec (str): image name or path to application
            workdir (str): Path to deployed application dir
        """
        cmd = 'atomic stop {app_spec} {workdir}'.format(
            app_spec=app_spec, workdir=workdir)
        subprocess.check_output(cmd, stdin=False, stderr=False, shell=True)

    def get_tmp_answers_file(self, answers):
        f = tempfile.NamedTemporaryFile(delete=False, suffix='.conf')
        f.close()
        anymarkup.serialize_file(answers, f.name, format='ini')
        return f.name

    @property
    def nulecule_lib(self):
        return self.NULECULE_LIB_PATH

    @classmethod
    def fetch_nulecule_lib(cls):
        if not os.path.exists(cls.NULECULE_LIB_PATH):
            subprocess.check_call(
                'git clone {repo} {path}'.format(
                    repo=cls.NULECULE_LIB_REPO, path=cls.NULECULE_LIB_PATH),
                shell=True)
        else:
            subprocess.check_call(
                'cd nulecule-library; git checkout master; '
                'git pull origin master', shell=True)

    @classmethod
    def build(cls):
        app_dir = os.path.join(cls.NULECULE_LIB_PATH, cls.APP_DIR_NAME)

        build_dir = cls.BUILD_DIR

        try:
            os.rmdir(build_dir)
        except:
            pass

        distutils.dir_util.copy_tree(app_dir, build_dir)

        with open(os.path.join(build_dir, 'Dockerfile')) as f:
            s = f.read()

        with open(os.path.join(build_dir, 'Dockerfile'), 'w') as f:
            f.write(re.sub('FROM.*', 'FROM atomicapp:build', s))

        cls.image_name = '{}-{}'.format(
            cls.APP_DIR_NAME, uuid.uuid1().hex[:8])
        subprocess.check_call(
            'docker build -t {image_name} {path}'.format(
                image_name=cls.image_name, path=build_dir),
            stdin=False, stderr=False,
            shell=True)

    @classmethod
    def remove_image(cls):
        subprocess.check_call('docker rmi {}'.format(cls.image_name),
                              stdin=False, stderr=False,
                              shell=True)


class DockerProviderTestSuite(BaseProviderTestSuite):
    """
    Base test suite for Docker.
    """
    PROVIDER = 'docker'

    def tearDown(self):
        _containers = self._get_containers(all=True)

        for container in _containers:
            if container not in self._containers:
                cmd = ['docker', 'rm', '-f', container]
                print cmd
                subprocess.check_output(cmd)

    def assertContainerRunning(self, name, timeout=1):
        start = datetime.datetime.now()
        while (datetime.datetime.now() - start).total_seconds() <= timeout:
            containers = self._get_containers()
            for _id, container in containers.items():
                if container['names'] == name:
                    return True
        raise AssertionError('Container: %s not running.' % name)

    def assertContainerNotRunning(self, name, timeout=1):
        start = datetime.datetime.now()
        while (datetime.datetime.now() - start).total_seconds() <= timeout:
            container_running = False
            containers = self._get_containers()
            for _id, container in containers.items():
                if container.get('name') == name:
                    container_running = True
        if container_running:
            raise AssertionError('Container: %s is running' % name)
        return True

    def get_initial_state(self):
        self._containers = self._get_containers(all=True)

    def _get_containers(self, all=False):
        cmd = ['docker', 'ps']
        if all:
            cmd.append('-a')
        output = subprocess.check_output(cmd)
        _containers = OrderedDict()

        for line in output.splitlines()[1:]:
            container = self._get_container(line)
            _containers[container['id']] = container
        return _containers

    def _get_container(self, line):
        words = re.split(' {2,}', line)
        if len(words) == 6:
            words = words[:-1] + [''] + words[-1:]
        container_id, image, command, created, status, ports, names = words
        return {
            'id': container_id,
            'image': image,
            'command': command,
            'created': created,
            'status': status,
            'ports': ports,
            'names': names
        }


class KubernetesProviderTestSuite(BaseProviderTestSuite):
    """
    Base test suite for Kubernetes.
    """
    PROVIDER = 'kubernetes'

    @classmethod
    def setUpClass(cls):
        super(KubernetesProviderTestSuite, cls).setUpClass()
        logger.debug('setUpClass...')
        logger.debug('Stopping existing kubernetes instance, if any...')
        kubernetes.stop()
        logger.debug('Starting kubernetes instance...')
        kubernetes.start()
        time.sleep(10)
        cls.answers = anymarkup.parse(kubernetes.answers(), 'ini')

    @classmethod
    def tearDownClass(cls):
        kubernetes.stop()

    def tearDown(self):
        kubernetes.clean()
        kubernetes.wait()

    def assertPod(self, name, exists=True, status=None, timeout=1):
        """
        Assert a kubernetes pod, if it exists, what's its status.

        We can also set a timeout to wait for the pod to
        get to the desired state.
        """
        start = datetime.datetime.now()
        cmd = 'kubectl get pod ' + name
        while (datetime.datetime.now() - start).total_seconds() <= timeout:
            try:
                output = subprocess.check_output(cmd, shell=True)
            except subprocess.CalledProcessError:
                if exists is False:
                    return True
                continue
            for line in output.splitlines()[1:]:
                pod = self._get_pod_details(line)
                if exists is False:
                    continue
                result = True
                if status is not None:
                    if pod['status'] == status:
                        result = result and True
                    else:
                        result = result and False
                if result:
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
        cmd = 'kubectl get service ' + name
        start = datetime.datetime.now()
        while (datetime.datetime.now() - start).total_seconds() <= timeout:
            try:
                output = subprocess.check_output(cmd, shell=True)
            except subprocess.CalledProcessError:
                if exists is False:
                    return True
                continue
            for line in output.splitlines()[1:]:
                if exists is False:
                    continue
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
        cmd = 'kubectl get rc ' + name
        start = datetime.datetime.now()
        while (datetime.datetime.now() - start).total_seconds() <= timeout:
            try:
                output = subprocess.check_output(cmd, shell=True)
            except subprocess.CalledProcessError:
                if exists is False:
                    return True
                continue
            for line in output.splitlines()[1:]:
                if exists is False:
                    continue
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
        output = subprocess.check_output('kubectl get services', shell=True)
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
        output = subprocess.check_output('kubectl get pods', shell=True)
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
        output = subprocess.check_output('kubectl get rc', shell=True)
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


class OpenshiftProviderTestSuite(BaseProviderTestSuite):
    """
    Base test suite for Openshift.
    """
    PROVIDER = 'openshift'

    @classmethod
    def setUpClass(cls):
        super(OpenshiftProviderTestSuite, cls).setUpClass()
        openshift.stop()
        openshift.start()
        cls.answers = anymarkup.parse(openshift.answers(), 'ini')
        openshift.wait()

    @classmethod
    def tearDownClass(cls):
        openshift.stop()

    def setUp(self):
        super(OpenshiftProviderTestSuite, self).setUp()
        self.os_exec('oc project %s' % self.answers['general']['namespace'])

    def os_exec(self, cmd):
        output = subprocess.check_output('docker exec -i origin %s' % cmd, shell=True)
        return output

    def tearDown(self):
        pods = self._get_pods()
        services = self._get_services()
        rcs = self._get_rcs()

        # clean up newly created pods
        for pod in pods:
            if pod not in self._pods:
                self.os_exec('oc delete pod %s' % pod)

        # clean up newly created services
        for service in services:
            if service not in self._services:
                self.os_exec('oc delete service %s' % service)

        # clean up newly created rcs
        for rc in rcs:
            if rc not in self._rcs:
                self.os_exec('oc delete rc %s' % rc)

        openshift.wait()

        time.sleep(10)

    def assertPod(self, name, exists=True, status=None, timeout=1):
        """
        Assert a kubernetes pod, if it exists, what's its status.

        We can also set a timeout to wait for the pod to
        get to the desired state.
        """
        start = datetime.datetime.now()
        while (datetime.datetime.now() - start).total_seconds() <= timeout:
            try:
                output = self.os_exec('oc get pod %s' % name)
            except subprocess.CalledProcessError:
                if exists is False:
                    return True
                continue
            for line in output.splitlines()[1:]:
                if exists is False:
                    continue
                pod = self._get_pod_details(line)
                result = True
                if status is not None:
                    if pod['status'] == status:
                        result = result and True
                    else:
                        result = result and False
                if result:
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
        start = datetime.datetime.now()
        while (datetime.datetime.now() - start).total_seconds() <= timeout:
            try:
                output = self.os_exec('oc get service %s' % name)
            except subprocess.CalledProcessError:
                if exists is False:
                    return True
                continue
            for line in output.splitlines()[1:]:
                if exists is False:
                    continue
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
        start = datetime.datetime.now()
        while (datetime.datetime.now() - start).total_seconds() <= timeout:
            try:
                output = self.os_exec('oc get rc %s' % name)
            except subprocess.CalledProcessError:
                if exists is False:
                    return True
                continue
            for line in output.splitlines()[1:]:
                if exists is False:
                    continue
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
        output = self.os_exec('oc get services')
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
        output = self.os_exec('oc get pods')
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
        output = self.os_exec('oc get rc')
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
