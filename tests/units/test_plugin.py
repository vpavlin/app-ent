import mock
import unittest

from atomicapp.plugin import Plugin
from atomicapp.providers.docker import DockerProvider
from atomicapp.providers.kubernetes import KubernetesProvider
 
class TestPluginGetProvider(unittest.TestCase):
 
    """Test Plugin getProvider"""
    def test_getProvider(self):
        """
        Test if getProvider is returning appropriate classes to the
        corresponding keys.
        """
        p = Plugin()
       
        docker_mock = DockerProvider
        kubernetes_mock = KubernetesProvider
        # keep some mock objects in place of the actual corresponding
        # classes, getProvider reads from `plugins` dict.
        p.plugins = {
            'docker': docker_mock,
            'kubernetes': kubernetes_mock,
        }
        self.assertEqual(p.getProvider('docker'), docker_mock)
        self.assertEqual(p.getProvider('kubernetes'), kubernetes_mock)

        # if non-existent key provided
        self.assertEqual(p.getProvider('some_random'), None)
