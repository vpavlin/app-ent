#!/usr/bin/env python

from __future__ import print_function
import os, sys
import subprocess
import urllib2
import collections
import anymarkup

from atomicapp.constants import SCHEMA_URL
from core import Core

import logging

logger = logging.getLogger(__name__)

class API():
    def __init__(self, app, schema = SCHEMA_URL):
        self.core = Core(app)
        self.params = self.core.params 

    def getMethods(self):
        methods = dir(self.core)

        output = []
        for m in methods:
            if callable(getattr(self.core,m)) and not m.startswith("_") and not m is "call":
                output.append(m)
                logger.debug(m)

        return output
                
    def call(self, method, kwargs):
        method_handler = getattr(self.core, method)
        
        if kwargs:
            kwargs = anymarkup.parse(kwargs)
        else:
            kwargs = {}
        if method_handler:
            logger.debug("Calling method %s with args\n%s" % (method, kwargs))
            method_handler(**kwargs)


    
