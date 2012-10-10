#!/usr/bin/env python
from time import sleep
from pprint import pprint
import sys
import os

sys.path.append(os.environ['ANTELOPE'] + '/data/python')

from antelope import orb, stock

import crap

ORBNAME='anfexport.ucsd.edu:prelim'


def main(args=None):
    if args is None:
        args = sys.argv
    myorb = orb.orbopen( ORBNAME, "r&" )
    pprint(vars(myorb))
    print myorb
    while True:
        id, namebuf, pkttime, packet, nbytes = crap.orbreap_timeout(myorb, 0)
        pprint(dict(
            id=id,
            namebuf=namebuf,
            pkttime=pkttime,
            packet=packet[:50],
            nbytes=nbytes,
        ))
        sleep(1)

#    orbreap = 
#    int orbreap(int orb, int *id, char *nm, double *t, char **p,
#        int *n, int *sz)



if __name__ == '__main__':
    exit(main())
