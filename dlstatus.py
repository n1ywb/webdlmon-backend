#!/usr/bin/env python
import sys
import logging
import re
from pprint import pformat
import os
import os.path
import json
from datetime import datetime
import time
from threading import Lock

from twisted.internet.threads import deferToThread

from antelope import orb, stock
from antelope.Pkt import Pkt
from antelope import _Pkt


logging.basicConfig(level=logging.DEBUG)

match_regex = r'.*/pf/(st|vtw)'
file_re = re.compile(r'/pf/(st|vtw)')


SORTORDERS = {
    'yes': 4,
    'waiting': 4,
    'su': 1,
    'reg': 1,
    'sleeping': 1,
    'hibernating': 1,
    'no': 1,
    'stopped': 0,
}


class DLStatus(object):
    def __init__(self, filename, myorb):
        self.filename = filename
        self.myorb = myorb
        self.status = {
            'metadata': {
                'timestamp': None
            },
            'dataloggers': {}
        }
        d = deferToThread(self.block_forever)
        #d = deferToThread(self.myorb.reap)
        #d.addCallback(self.reap_cb)

    def block_forever(self, *args, **kwargs):
        l = Lock()
        print "Trying to block forever."
        l.acquire(True)
        l.acquire(True)
        print "oops, didn't block forever afterall."

    def reap_cb(self, r):
        pktid, srcname, time, raw_packet, nbytes = r
        if pktid is not None:
            packet = Pkt(srcname, time, raw_packet)
            pkttypename = packet.pkttype['name']
            if pkttypename in ('st', 'pf', 'stash'):
                pfstring = packet.string
                if pfstring is not None and pfstring != '':
                    pfdict = pfstring_to_pfdict(pfstring)
                else:
                    pfdict = stock.pfget(packet.pfptr, '')
                self.update_status(pfdict)
        d = deferToThread(self.myorb.reap)
        d.addCallback(self.reap_cb)

    def update_status(self, pfdict):
        """Updates status from pfdict"""
        pfdict = self.pfmorph(pfdict)
        for stn,status in pfdict['dls'].items():
            net, sep, stnonly = stn.partition('_')
            sort_order = str(SORTORDERS[status['con']]) + stnonly
            self.status['dataloggers'][stn] = {
                    'sortorder': sort_order,
                    'values': status }
        self.status['metadata']['timestamp'] = time.mktime(
                datetime.utcnow().timetuple())
        self.save()

    def to_json(self):
        return json.dumps(self.status, sort_keys=True, indent=4)

    def save(self):
        jsonstr = self.to_json()
        backbuffer_file = self.filename + '+'
        with open(backbuffer_file, 'w') as F:
                F.write(jsonstr)
        os.rename(backbuffer_file, self.filename)

    def pfmorph(self, pfdict):
        dls  = dict()
        if pfdict.has_key('dls'):
            dls = pfdict['dls']
        for sta in dls.keys():
            if dls[sta]['opt'] is not None and dls[sta]['opt'] != "-":
                dls[sta]['acok'] = 1 if 'acok' in dls[sta]['opt'] else 0
                dls[sta]['api'] = 1 if 'api' in dls[sta]['opt'] else 0
                dls[sta]['isp1'] = 1 if 'isp1' in dls[sta]['opt'] else 0
                dls[sta]['isp2'] = 1 if 'isp2' in dls[sta]['opt'] else 0
                dls[sta]['ti'] = 1 if 'ti' in dls[sta]['opt'] else 0
            else:
                dls[sta]['acok'] = "-"
                dls[sta]['api']  = "-"
                dls[sta]['isp1'] = "-"
                dls[sta]['isp2'] = "-"
                dls[sta]['ti']   = "-"
        pfdict['dls'] = dls
        return pfdict


def pfstring_to_pfdict(pfstring):
    pfstring = pfstring.strip('\0')
    pfptr = stock.pfnew()
    stock.pfcompile(pfstring, pfptr)
    pfdict = stock.pfget(pfptr, '')
    return pfdict



