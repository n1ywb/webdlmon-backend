#!/usr/bin/env python
import sys
from optparse import OptionParser
import logging
import re
from pprint import pformat
import os
import os.path
import json
from datetime import datetime
import time

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
    def __init__(self, filename):
        self.filename = filename
        self.status = {
            'metadata': {
                'timestamp': None
            },
            'dataloggers': {}
        }

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

    def save(self):
        jsonstr = json.dumps(self.status, sort_keys=True, indent=4)
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


def proc_pfstring(pfstring):
    pfstring = pfstring.strip('\0')
    pfptr = stock.pfnew()
    stock.pfcompile(pfstring, pfptr)
    pfdict = stock.pfget(pfptr, '')
    return pfdict


def get_pf(myorb):
    while True:
        pktid, srcname, time, raw_packet, nbytes = myorb.reap()
        if pktid is None:
            continue
        packet = Pkt(srcname, time, raw_packet)
        # TODO onfirm if this value is equivilent to the 'kind'
        # returned by unstuffpkt
        pkttypename = packet.pkttype['name']
        if pkttypename in ('st', 'pf', 'stash'):
            pfstring = packet.string
            if pfstring is not None and pfstring != '':
                pfdict = proc_pfstring(pfstring)
            else:
                pfdict = stock.pfget(packet.pfptr, '')
            yield pfdict


def main(args=None):
    if args is None:
        args = sys.argv
    op = OptionParser()
    op.add_option("-a", "--after", dest="after",
                     help="rewinds the orbserver packet stream to the time specified.")
    op.add_option("-v", "--verbose", dest="verbose",
                     action="store_true")
    op.add_option("-m", "--match", dest="match", default=match_regex,
                     help="match expression to use against orb source names.")
    (options, args) = op.parse_args(args[1:])
    outdir = args.pop()
    orbname = args.pop()
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    myorb = orb.orbopen( orbname, "r&" )
    if options.after is not None:
        # options.after to epoch
        myorb.after(after_time)
    nsources = myorb.select(options.match)
    logging.info("%d sources" % nsources)
    dlstatus = DLStatus(os.path.join(outdir, 'webdlmon.json'))
    for pfdict in get_pf(myorb):
        dlstatus.update_status(pfdict)



if __name__ == '__main__':
    exit(main())

