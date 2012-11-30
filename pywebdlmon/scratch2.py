#!/usr/bin/env python
import sys
from optparse import OptionParser
import logging
import re
from pprint import pformat
import os
import os.path
import json

from antelope import orb, stock
from antelope.Pkt import Pkt
from antelope import _Pkt


logging.basicConfig(level=logging.DEBUG)


def main(args=None):
    if args is None:
        args = sys.argv
    pf = stock.pfget('foo', '')
    print json.dumps(pf, sort_keys=True, indent=4)
    #with open('foo.pf') as pff:
    #    pfstr = pff.read()
    return 0


if __name__ == '__main__':
    exit(main())
