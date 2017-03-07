import unittest
import os
import tempfile

from atomicapp.utils import Utils


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="atomicapp-test-utils", dir="/tmp")
        self.tmpfile = open(os.path.join(self.tmpdir, 'test.txt'), 'w+')

    def test_setFileOwnerGroup(self):
        """
        Use the function to set the file owner ship
        """
        u = Utils
        u.setFileOwnerGroup(self.tmpdir)
