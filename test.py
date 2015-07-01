#!/usr/bin/env python

import os, sys, logging
import unittest

from atomicapp.cli import *

class TestAtomicappCLU(unittest.TestCase):
    def test_with_helloapache(self):
        os.chdir('tests/cached_nulecules/helloapache/')

        sys.argv = []
        sys.argv.append('--verbose')
        sys.argv.append('--dry-run')
        sys.argv.append('run')
        sys.argv.append('.')

        cli = main.CLI()
        self.assertTrue(cli.run())

if __name__ == '__main__':
    __CWD__ = os.getcwd()

    unittest.main()
