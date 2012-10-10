#!/usr/bin/env python
import traceback
from optparse import OptionParser
import sys
import json
#import datetime
from pprint import pprint
#from subprocess import Popen,PIPE
import os
import os.path
import logging

from twisted.python import log
from twisted.internet import reactor, defer
from twisted.internet.threads import deferToThread
from twisted.web.resource import Resource
from twisted.web.server import Site

sys.path.append(os.environ['ANTELOPE'] + '/data/python')

from antelope import orb, stock
from antelope.Pkt import Pkt
from antelope import _Pkt

from dlstatus import DLStatus, DLSource, match_regex


config = {
        'dlmon': [('anfexport:prelim', None, None)],
        'foo': [('anfexport:status', None, None)],
        'bar': [('anfexport:status', None, None), ('anfexport:prelim', None,
            None)],
}


class ROOT(Resource):
    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)

    def render(self, request):
        log.msg('Got request: %s' % request)
        args = request.uri.split("/")[1:]
        log.msg('Got args: %s' % args)
        request.setHeader("content-type", "text/html")
        request.setHeader("response-code", 500)
        return "Unknown query type:(%s)" % args


class DLMon(Resource):
    def __init__(self, dlstatus):
        self.dlstatus = dlstatus

    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)

    def render(self, request):
        try:
	    request.setHeader("content-type", "application/json")
	    if request.args.has_key('callback'):
		    request.setHeader("content-type", "application/javascript")
		    return request.args['callback'][0] + '(' + self.dlstatus.to_json() + ')'
            return self.dlstatus.to_json()
        except Exception, e:
	    raise


def main(args=None):
    if args is None:
        args = sys.argv
    op = OptionParser()
    op.add_option("-v", "--verbose", dest="verbose",
                     action="store_true")
    (options, args) = op.parse_args(args[1:])

    root = ROOT()

    dlstatuses = {}
    for dlstatus_name,v in config.items():
        dlstatus = DLStatus()
        dlstatuses[dlstatus_name] = dlstatus
        for orbname,match,rej in v:
            match = match if match is not None else match_regex
            rej = rej if rej is not None else ''
            source = DLSource(orbname,match,rej)
            source.add_sink(dlstatus.update_status)
        root.putChild(dlstatus_name, DLMon(dlstatus))

    log.startLogging(sys.stdout)

    log.msg('Build as site object:')
    website = Site( root )
    log.msg('\t\t\t\t\t=> OK')

    log.msg('Setup TCP port:')
    reactor.listenTCP(7000, website)
    log.msg('\t\t\t\t\t=> OK')

    log.msg('Run reactor:')
    reactor.run()


if __name__ == '__main__':
    exit(main())

