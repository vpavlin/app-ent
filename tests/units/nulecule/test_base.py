import unittest

import mock

from atomicapp.nulecule.base import Nulecule
from atomicapp.nulecule.exceptions import NuleculeException


class TestNuleculeGetProvider(unittest.TestCase):
    """ Test Nulecule get_provider"""
    def test_get_provider_success(self):
        """
        Test if get_provider method when passed a particular valid key returns
        the corresponding class.
        """
        nulecule = Nulecule('some-id', '0.0.2', params=[], basepath='', namespace='')
        provider_key = u'openshift'
        # method `get_provider` will read from this config, we give it here
        # since we have neither provided it before nor it is auto-generated
        nulecule.config = {u'general': {u'provider': provider_key}}

        return_provider = mock.Mock()
        # mocking return value of method plugin.getProvider,because it returns
        # provider class and that class gets called with values
        nulecule.plugin.getProvider = mock.Mock(return_value=return_provider)
        ret_provider_key, _ = nulecule.get_provider()
        self.assertEqual(provider_key, ret_provider_key)
        return_provider.assert_called_with({u'provider': provider_key},
                                           '', False)

    def test_get_provider_failure(self):
        """
        Test if get_provider method when passed an invalid key raises an
        exception.
        """
        nulecule = Nulecule('some-id', '0.0.2', params=[], basepath='', namespace='')
        # purposefully give the wrong provider key
        provider_key = u'mesos'
        nulecule.config = {u'general': {u'provider': provider_key}}
        with self.assertRaises(NuleculeException):
            nulecule.get_provider()
