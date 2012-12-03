#!/usr/bin/env python
# Copyright 2012 UC Regents
"""
Demonstrate various bugs in the Antelope Python API.

Usage:
[jeff@anfdevl pydlmon]$ python ./bug.py -v
test_1 (__main__.Test_1_packet_string) ... FAIL
test_1 (__main__.Test_2_packet_pf) ... 2012-269 00:38:45 python *fatal*: invalid pf type = 8012240

Changelog:
2012-09-24 JML Initial Revision
"""

import unittest
import sys
import os

sys.path.append(os.environ['ANTELOPE'] + '/data/python')

from antelope import orb
from antelope import stock
from antelope import elog
from antelope.Pkt import Pkt


pfname = 'testpf'
match_regex = r'.*/pf/(st|vtw)'


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.orb = orb.orbopen('anfexport.ucsd.edu:prelim', "r&" )
        nsources = self.orb.select(match_regex)

    def tearDown(self):
        self.orb.close()

    def get_packet(self):
        while True:
            pktid, srcname, time, packet, nbytes = self.orb.reap()
            if pktid is None:
                continue
            packet = Pkt(srcname, time, packet)
            pkttypename = packet.pkttype['name']
            if pkttypename in ('st', 'pf', 'stash'):
                return packet

    def get_pf_packet(self):
        while True:
            packet = self.get_packet()
            if not (packet.string is not None and packet.string != ''):
                return packet

    def get_non_pf_packet(self):
        while True:
            packet = self.get_packet()
            if packet.string is not None and packet.string != '':
                return packet


class Test_1_packet_string(BaseTest):
    """Test contents of string member of Pkt object for trailing nulls."""
    def test_1(self):
        packet = self.get_non_pf_packet()
        pfstring = packet.string
        self.assertFalse(pfstring.endswith('\0'))


class Test_2_packet_pf(BaseTest):
    """Test usability of PF packets."""
    def test_1(self):
        packet = self.get_pf_packet()
        pfname = packet.pfptr
        v = stock.pfget( pfname, "dls" )


if __name__ == '__main__':
    unittest.main()

