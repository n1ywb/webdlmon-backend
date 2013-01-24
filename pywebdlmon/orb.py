#!/usr/bin/env python
"""Orb Status Packet Interface"""

import time
from datetime import datetime
from calendar import timegm

from twisted.python import log

from antelope import _stock
from antelope import _brttpkt

from kudu.exc import OrbIncomplete
from kudu.twisted.orbreapthread import OrbReapThread
from kudu.pkt import Pkt


pktno = 0


class StatusPktSource(OrbReapThread):
    """Represents a datalogger status data source, i.e. an orb reap thread."""

    def pfstring_to_pfdict(self, pfstring):
        """Return a dictionary from the 'string' field of a status packet which
        contains a parameter file."""
        pfstring = pfstring.strip('\0')
        pfptr = _stock._pfnew()
        try:
            r = _stock._pfcompile(pfstring, pfptr)
            if r != 0: raise Exception("pfcompile failed")
            pfdict = _stock._pfget(pfptr, None)
            return pfdict
        finally:
            _stock._pffree(pfptr)

    def pfmorph(self, pfdict, timestamp):
        """Apply arcane transformations to incoming status data."""
        rx_timestamp = str(int(timegm(datetime.utcnow().utctimetuple())))
        # TODO Would it be more appropriate for this to live in model.py?
        dls = dict()
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

        # More arcane transforms
        updated_stations=dict(dataloggers={}, metadata={})
        for stn,status in pfdict['dls'].items():
            net, sep, stnonly = stn.partition('_')
            updated_stations['dataloggers'][stn] = {
                        'name': stn,
                        'values': status,
                        'timestamp': timestamp,
                    }
        updated_stations['metadata']['timestamp'] = rx_timestamp
        return updated_stations

    def on_get(self, r):
        """OrpReapThread.get callback method."""
        global pktno
        rc, pktid, srcname, timestamp, raw_packet, nbytes = r
        if rc != _brttpkt.ORBREAPTHR_OK:
            raise OrbIncomplete()
        pktno += 1
        log.msg("%r reap pkt #%d: %d bytes" % (self.orbname, pktno, nbytes))
        # TODO Should this jazz be pushed down the callback chain?
        packet = Pkt(srcname, timestamp, raw_packet)
        pkttypename = packet.pkttype['name']
        if pkttypename not in ('st', 'pf', 'stash'):
            raise OrbIncomplete()
        pfstring = packet.string
        if pfstring is not None and pfstring != '':
            pfdict = self.pfstring_to_pfdict(pfstring)
        else:
            pfdict = packet.pfdict
        updated_stations = self.pfmorph(pfdict, timestamp)
        return updated_stations

    def get(self):
        d = super(StatusPktSource, self).get()
        d.addCallback(self.on_get)
        return d

