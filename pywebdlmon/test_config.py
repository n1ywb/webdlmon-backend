#!/usr/bin/env python
import sys
from pprint import pprint
import os
import os.path
import unittest
from unittest import TestCase

import config

sys.path.append(os.environ['ANTELOPE'] + '/data/python')

class Dummy(object):
    def __init__(self, **kwargs):
        [setattr(self, k, v) for (k, v) in kwargs.items()]

class TestConfig(TestCase):
    def test_config(self):
        options = Dummy(parameter_file='testconfig',
                        match=None, reject=None,
                        bind_address=None,
                        port=None, root=None)
        c = config.Config(options)
        self.assertEquals(c.bind_address, '0.0.0.0')
        self.assertEquals(c.port, 7000)
        self.assertEquals(c.root, '/data/dlmon')
        self.assertEquals(c.instances['inst1']['src1'].match, 'match1')
        self.assertEquals(c.instances['inst1']['src1'].reject, 'reject1')
        self.assertEquals(c.instances['inst1']['src2'].match, 'globmatch')
        self.assertEquals(c.instances['inst1']['src2'].reject, 'globreject')


class TestConfig2(TestCase):
    def test_config2(self):
        options = Dummy(parameter_file='testconfig2',
                        match=None, reject=None,
                        bind_address=None,
                        port=None, root=None)
        c = config.Config(options)
        self.assertEquals(c.bind_address, '0.0.0.0')
        self.assertEquals(c.port, 7000)
        self.assertEquals(c.root, '/data/dlmon')
        self.assertEquals(c.instances['inst1']['src1'].match, 'match1')
        self.assertEquals(c.instances['inst1']['src1'].reject, 'reject1')
        self.assertEquals(c.instances['inst1']['src2'].match, '.*')
        self.assertEquals(c.instances['inst1']['src2'].reject, '')


if __name__ == '__main__':
    unittest.main()

