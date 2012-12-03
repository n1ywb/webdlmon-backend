#!/usr/bin/env python
"""Datalogger Status"""

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

pktno = 0


def pfstring_to_pfdict(pfstring):
    """Return a dictionary from the 'string' field of a status packet which
    contains a parameter file."""
    # TODO Should this be a method on DLSource since that's the only place it's
    # used?
    pfstring = pfstring.strip('\0')
    pfptr = _stock._pfnew()
    try:
        r = _stock._pfcompile(pfstring, pfptr)
        if r != 0: raise Exception("pfcompile failed")
        pfdict = _stock._pfget(pfptr, None)
        return pfdict
    finally:
        _stock._pffree(pfptr)


class DLSource(object):
    """Represents a datalogger status data source, i.e. an orb.

    DLSource objects are normally associated with one or more data-sink
    objects, whose callback(s) are called with new data.
    """
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
        """Orbreap errback method."""
        print "in reap_eb"
        failure.trap(OrbIncomplete)
        d = deferToThread(self.orb.reap_timeout, REAP_TIMEOUT)
        d.addCallback(self.reap_cb)
        d.addErrback(self.reap_eb)
        return None
    def add_sink(self, sink_func):
        """Registers the data-sink's callback function."""
        self.sinks.append(sink_func)
    def reap_cb(self, r):
        """Orbreap callback method."""
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
        d = deferToThread(self.orb.reap_timeout, REAP_TIMEOUT)
        d.addCallback(self.reap_cb)
        d.addErrback(self.reap_eb)
    def close(self):
        self.orb.close()


class DLStatus(object):
    """Represents a particular named DLMON instance."""
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
        """This method is called whenever a new station is heard.

        Monkey patch this with your own callback."""
        pass

    def update_status(self, pfdict):
        """Updates status from pfdict"""
        pfdict = self.pfmorph(pfdict)
        for stn,status in pfdict['dls'].items():
            if not stn in self.seen_stns:
                self.seen_stns.add(stn)
                self.new_stn_cb(self, stn)
            net, sep, stnonly = stn.partition('_')
            self.status['dataloggers'][stn] = {
                    'name': stn,
                    'values': status }
        self.status['metadata']['timestamp'] = str(int(time.mktime(
                datetime.utcnow().timetuple())))

    def to_json(self):
        """Return state of all stations in json format."""
        status = dict(self.status)
        status['dataloggers'] = status['dataloggers'].values()
        return json.dumps(status, sort_keys=True, indent=4)

    def stn_to_json(self, id):
        """Return state of a particular station in json format."""
        stn = self.status['dataloggers'][id]
        return json.dumps(stn, sort_keys=True, indent=4)

    def pfmorph(self, pfdict):
        """Apply arcane transformations to incoming status data."""
        dls  = dict()
        if pfdict.has_key('dls'):
            dls = pfdict['dls']
        for sta in dls.keys():
            if 'opt' in dls[sta] and dls[sta]['opt'] != "-":
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


