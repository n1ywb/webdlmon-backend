#!/usr/bin/env python
import logging
from pprint import pformat
import json
from datetime import datetime
import time

from twisted.internet.threads import deferToThread

from kudu.exc import OrbIncomplete
from kudu.orb import Orb
from kudu.pkt import Pkt
from antelope import _stock

logging.basicConfig(level=logging.DEBUG)

REAP_TIMEOUT = 2
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
        myorb = Orb( orbname, "r&" )
        myorb.select(match)
        myorb.reject(rej)
        self.orb = myorb
        self.sinks = []
        d = deferToThread(self.orb.reap_timeout, REAP_TIMEOUT)
        d.addCallback(self.reap_cb)
        d.addErrback(self.reap_eb)
    def __enter__(self):
        pass
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
    def reap_eb(self,failure):
        print "in reap_eb"
        failure.trap(OrbIncomplete)
        d = deferToThread(self.orb.reap_timeout, REAP_TIMEOUT)
        d.addCallback(self.reap_cb)
        d.addErrback(self.reap_eb)
        return None
    def add_sink(self, sink_func):
        self.sinks.append(sink_func)
    def reap_cb(self, r):
        print "in reap_cb"
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
                    pfdict = packet.pfdict
                for sink in self.sinks:
                    sink(pfdict)
        gc.collect()
        d = deferToThread(self.orb.reap_timeout, REAP_TIMEOUT)
        d.addCallback(self.reap_cb)
        d.addErrback(self.reap_eb)
    def close(self):
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
    pfptr = _stock._pfnew()
    try:
        r = _stock._pfcompile(pfstring, pfptr)
        if r != 0: raise Exception("pfcompile failed")
        pfdict = _stock._pfget(pfptr, None)
        return pfdict
    finally:
        _stock._pffree(pfptr)

