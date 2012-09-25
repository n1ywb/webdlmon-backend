#!/usr/bin/env python
import sys
from optparse import OptionParser
import logging
import re
from pprint import pformat
import os
import os.path

from antelope import orb, stock
from antelope.Pkt import Pkt
from antelope import _Pkt


logging.basicConfig(level=logging.DEBUG)

match_regex = r'.*/pf/(st|vtw)'
file_re = re.compile(r'/pf/(st|vtw)')
header = "<?xml version=\"1.0\" encoding=\"iso-8859-1\"?>\n"


def pfmorph(pfname):
    dls  = dict()
    v = stock.pfget( pfname, "dls" )
    if v is not None:
        dls.update(v)
    for sta in dls.keys():
        if dls[sta]['opt'] is not None and dls[sta]['opt'] != "-":
            dls[sta]['acok'] = 1 if dls[sta]['opt'].contains('acok') else 0
            dls[sta]['api'] = 1 if dls[sta]['opt'].contains('api') else 0
            dls[sta]['isp1'] = 1 if dls[sta]['opt'].contains('isp1') else 0
            dls[sta]['isp2'] = 1 if dls[sta]['opt'].contains('isp2') else 0
            dls[sta]['ti'] = 1 if dls[sta]['opt'].contains('ti') else 0
        else:
            dls[sta]['acok'] = "-"
            dls[sta]['api']  = "-"
            dls[sta]['isp1'] = "-"
            dls[sta]['isp2'] = "-"
            dls[sta]['ti']   = "-"
    stock.pfput( "dls", dls, pfname )


def write_pf(pfname, file):
    pfmorph(pfname)
    xmlstring = stock.pf2xml( pfname, "-n", header, "")
    backbuffer_file = file + '+'
    with open(backbuffer_file, 'w') as F:
            F.write(xmlstring)
            os.rename(backbuffer_file, file)


def proc_pfstring(outdir, pfstring, srcname):
    pfstring = pfstring.strip('\0')
    outfile = file_re.sub('', srcname)
    outfile += "_stash.xml"
    outfile = os.path.join(outdir, outfile)
    pfname = "apf"
    stock.pfnew(pfname)
    # TODO why does pfcompile raise a typerror complaining I am not
    # passing a string when I AM passing strings?
    stock.pfcompile(pfstring, pfname)
    write_pf(pfname, outfile)
    # TODO why is the python api missing pffree()? is this a leak?
    # stock.pffree( pfname )


def proc_no_pfstring(outdir, srcname, packet, raw_packet):
    outfile = file_re.sub('', srcname)
    outfile += ".xml"
    outfile = os.path.join(outdir, outfile)
    # packet.pf is a string; do we need to access it for a side
    # effect? why does the perl code call it?
    pfname = packet.pf
    #foo = packet.pf
    #pfname = "Packet::pf"
    pfobj = _Pkt._Pkt_pf_get(raw_packet)
    pfcompile(pfobj, pfname)
    dls  = dict()
    v = stock.pfget( pfname, "dls" )
    if v is not None:
        dls.update(v)
    for sta in dls.keys():
        if dls[sta]['opt'] is not None and dls[sta]['opt'] != "-":
            dls[sta]['acok'] = 1 if dls[sta]['opt'].contains('acok') else 0
            dls[sta]['api'] = 1 if dls[sta]['opt'].contains('api') else 0
            dls[sta]['isp1'] = 1 if dls[sta]['opt'].contains('isp1') else 0
            dls[sta]['isp2'] = 1 if dls[sta]['opt'].contains('isp2') else 0
            dls[sta]['ti'] = 1 if dls[sta]['opt'].contains('ti') else 0
        else:
            dls[sta]['acok'] = "-"
            dls[sta]['api']  = "-"
            dls[sta]['isp1'] = "-"
            dls[sta]['isp2'] = "-"
            dls[sta]['ti']   = "-"
    stock.pfput( "dls", dls, pfname )
    xmlstring = stock.pf2xml( pfname, "-n", header, "")
    backbuffer_file = file + '+'
    with open(backbuffer_file, 'w') as F:
            F.write(xmlstring)
            os.rename(backbuffer_file, file)




def main(args=None):
    if args is None:
        args = sys.argv
    npkts = 0
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
    while (True):
	pktid, srcname, time, raw_packet, nbytes = myorb.reap()
	npkts += 1
        if pktid is None:
            continue
        packet = Pkt(srcname, time, raw_packet)
        # TODO onfirm if this value is equivilent to the 'kind'
        # returned by unstuffpkt
        pkttypename = packet.pkttype['name']
        if pkttypename in ('st', 'pf', 'stash'):
            pfstring = packet.string
            if pfstring is not None and pfstring != '':
                proc_pfstring(outdir, pfstring, srcname)
            else:
                proc_no_pfstring(outdir, srcname, packet, raw_packet)


if __name__ == '__main__':
    exit(main())
