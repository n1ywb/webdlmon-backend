#!/usr/bin/env python

from contextlib import contextmanager
import os
import shutil
from subprocess import Popen
import sys
import time

sys.path.append(os.environ['ANTELOPE'] + '/data/python')

from antelope.Pkt import Pkt, suffix2pkttype
from antelope.orb import orbopen, ORBOLDEST, ORBPREV, ORBNEWEST
from antelope.stock import pfnew, pfput, pfget

orbdir = '/export/home/jeff/orb2'
orbname = ':6666'
teststring = 'A' * 1024 * 1024 # 1 MB
orbsrvargs = ('orbserver -P %s -p %s orbserver' % (orbdir, orbname)).split()

@contextmanager
def terminating(x):
    try:
        yield x
    finally:
        x.terminate()

def del_orbdir():
    try:
        shutil.rmtree(orbdir)
    except Exception:
        pass

curpktid = 0
# start orb server
del_orbdir()
os.makedirs(orbdir)
with terminating(Popen(orbsrvargs, cwd=orbdir)) as orbserverproc:
    time.sleep(2)
    orb = orbopen(orbname, "w&")
    for x in xrange(100):
        pf = pfnew()
        pfput('foobar', teststring, pf)
        pkt = Pkt()
        pkt.pfptr = pf
        pkt.srcnameparts = dict(
            net='net',
            sta='sta',
            chan='chan',
            loc='loc',
            suffix='pf',
            subcode='subcode',
        )
        pkt.pkttype = suffix2pkttype("pf")
        (type_, packet, srcname, timestamp) = pkt.stuff()
        assert packet
        pktid = orb.putx(srcname, timestamp, packet, len(packet))
        print "Put packet ID", pktid
        assert pktid == curpktid
        if pktid > 0:
            orb.seek(ORBPREV)
        else:
            orb.seek(ORBOLDEST)
        rpktid = None
        while rpktid is None:
            rpktid, rsrcname, rtimestamp, rpacket, rnbytes = orb.reap_timeout(1)
            print "reap packet ID", rpktid
        # assert same packet
        assert pktid == rpktid
        rpkt = Pkt(rsrcname, rtimestamp, rpacket)
        #assert pkt.string.strip('\0') == rpkt.string.strip('\0')
        assert pfget(rpkt.pfptr, 'foobar')[0] == 'A'
        curpktid += 1

del_orbdir()
# exit
# check valgrind for mem leaks

