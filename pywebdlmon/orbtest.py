#!/usr/bin/env python
"""
Starting orb servers for use with tests.
"""

import unittest

class OrbServer(object):
    def __init__(self):
        self.proc = subprocess.Popen('orbserver -p :6666 orbserver'.split(), 

class OrbTest(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

