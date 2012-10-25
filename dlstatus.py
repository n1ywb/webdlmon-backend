#!/usr/bin/env python
import logging
from pprint import pformat
import json
from datetime import datetime
import time

from twisted.internet.threads import deferToThread

from antelope import orb, stock
from antelope.Pkt import Pkt

import crap


logging.basicConfig(level=logging.DEBUG)

DEFAULT_MATCH = r'.*/pf/(st|vtw)'

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


import gc

pktno = 0

class DLSource(object):
    def __init__(self, orbname, match, rej):
        myorb = orb.orbopen( orbname, "r&" )
        myorb.select(match)
        myorb.reject(rej)
        self.orb = myorb
        self.sinks = []
        d = deferToThread(crap.orbreap_timeout, self.orb, 1.0)
        d.addCallback(self.reap_cb)
        d.addErrback(self.reap_eb)
    def reap_eb(self,e):
        return e
    def add_sink(self, sink_func):
        self.sinks.append(sink_func)
    def reap_cb(self, r):
        global pktno
        pktid, srcname, time, raw_packet, nbytes = r
        if pktid is not None:
            pktno += 1
            logging.debug("orbreap packet #%d: %d bytes" % (pktno, nbytes))
            packet = Pkt(srcname, time, raw_packet)
            pkttypename = packet.pkttype['name']
            if pkttypename in ('st', 'pf', 'stash'):
                pfstring = packet.string
                if pfstring is not None and pfstring != '':
                    logging.debug("calling pfstring_to_pfdict(pfstring)")
                    pfdict = pfstring_to_pfdict(pfstring)
                else:
                    logging.debug("calling stock.pfget(packet.pfptr, '')")
                    pfdict = stock.pfget(packet.pfptr, '')
                for sink in self.sinks:
                    sink(pfdict)
        gc.collect()
        d = deferToThread(crap.orbreap_timeout, self.orb, 10.0)
        d.addCallback(self.reap_cb)
        d.addErrback(self.reap_eb)
    def __del__(self):
        self.orb.close()


class DLStatus(object):
    def __init__(self):
        self.seen_stns = set()
        self.status = {
            'metadata': {
                'timestamp': None
            },
            'dataloggers': {}
        }

    @staticmethod
    def new_stn_cb(dlmon, id):
        """Monkey patch over this as necessary."""
        pass

    def update_status(self, pfdict):
        """Updates status from pfdict"""
        pfdict = self.pfmorph(pfdict)
        for stn,status in pfdict['dls'].items():
            if not stn in self.seen_stns:
                self.seen_stns.add(stn)
                self.new_stn_cb(self, stn)
            net, sep, stnonly = stn.partition('_')
            sort_order = str(SORTORDERS[status['con']]) + stnonly
            self.status['dataloggers'][stn] = {
                    'sortorder': sort_order,
                    'name': stn,
                    'values': status }
        self.status['metadata']['timestamp'] = str(int(time.mktime(
                datetime.utcnow().timetuple())))

    def to_json(self):
        status = dict(self.status)
        status['dataloggers'] = status['dataloggers'].values()
        return json.dumps(status, sort_keys=True, indent=4)

    def stn_to_json(self, id):
        stn = self.status['dataloggers'][id]
        return json.dumps(stn, sort_keys=True, indent=4)

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



