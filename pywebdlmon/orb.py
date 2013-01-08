#!/usr/bin/env python
"""Orb Status Packet Interface"""

from pprint import pformat

from twisted.python import log

from antelope import _stock

from kudu.exc import OrbIncomplete
from kudu.twisted.orb import Orb
from kudu.pkt import Pkt


REAP_TIMEOUT = 2

pktno = 0


class StatusPktSource(Orb):
    """Represents a datalogger status data source, i.e. an orb."""

    def pfstring_to_pfdict(self, pfstring):
        """Return a dictionary from the 'string' field of a status packet which
        contains a parameter file."""
        # TODO Should this be a method on DLSource since that's the only place
        # it's used?
        pfstring = pfstring.strip('\0')
        pfptr = _stock._pfnew()
        try:
            r = _stock._pfcompile(pfstring, pfptr)
            if r != 0: raise Exception("pfcompile failed")
            pfdict = _stock._pfget(pfptr, None)
            return pfdict
        finally:
            _stock._pffree(pfptr)

    def pfmorph(self, pfdict):
        """Apply arcane transformations to incoming status data."""
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
        # TODO Convert to JSON-able right here.
        # TODO this could be added as a callback.
        # TODO or even move this out of this module.
        return pfdict

    def on_reap(self, r):
        """Orbreap callback method."""
        global pktno
        pktid, srcname, time, raw_packet, nbytes = r
        # I want Kudu to prevent pktid from ever being None.
        # but why?
        assert pktid is not None
        pktno += 1
        log.msg("orbreap packet #%d: %d bytes" % (pktno, nbytes))
        # TODO Should this jazz be pushed down the callback chain?
        packet = Pkt(srcname, time, raw_packet)
        pkttypename = packet.pkttype['name']
        if pkttypename not in ('st', 'pf', 'stash'):
            raise OrbIncomplete()
        pfstring = packet.string
        if pfstring is not None and pfstring != '':
            pfdict = self.pfstring_to_pfdict(pfstring)
        else:
            pfdict = packet.pfdict
        pfdict = self.pfmorph(pfdict)
        return dict(dataloggers=pfdict['dls'])

    def reap_timeout(self, *args, **kwargs):
        d = super(StatusPktSource, self).reap_timeout(*args, **kwargs)
        d.addCallback(self.on_reap)
        return d

