import mock
import unittest

from atomicapp.nulecule.lib import NuleculeBase
from atomicapp.nulecule.exceptions import NuleculeException
from atomicapp.nulecule.config import Config


class TestNuleculeBaseGetProvider(unittest.TestCase):
    """ Test NuleculeBase get_provider"""
    def test_get_provider_success(self):
        """
        Test if get_provider method when passed a particular valid key returns
        the corresponding class.
        """
        nb = NuleculeBase(params = [], basepath = '', namespace = '')
        provider_key = u'openshift'
        # method `get_provider` will read from this config, we give it here
        # since we have neither provided it before nor it is auto-generated
        nb.config = Config(answers={u'general': {u'provider': provider_key}})

        return_provider = mock.Mock()
        # mocking return value of method plugin.getProvider,because it returns
        # provider class and that class gets called with values
        nb.plugin.getProvider = mock.Mock(return_value=return_provider)
        ret_provider_key, ret_provider = nb.get_provider()
        self.assertEqual(provider_key, ret_provider_key)
        return_provider.assert_called_with(
            {'provider': provider_key, 'namespace': 'default'},
            '',
            False)

    def test_get_provider_failure(self):
        """
        Test if get_provider method when passed an invalid key raises an
        exception.
        """
        nb = NuleculeBase(params = [], basepath = '', namespace = '')
        # purposefully give the wrong provider key
        provider_key = u'mesos'
        nb.config = Config(answers={u'general': {u'provider': provider_key}})
        with self.assertRaises(NuleculeException):
            nb.get_provider() 
