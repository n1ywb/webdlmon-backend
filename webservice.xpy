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

from dlstatus import DLStatus, match_regex


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
    dlstatus = DLStatus(os.path.join(outdir, 'webdlmon.json'), myorb)

    log.startLogging(sys.stdout)

    log.msg('Set root site:')
    root = ROOT()
    log.msg('\t\t\t\t\t=> OK')

    log.msg('Append service:')
    log.msg('\t\tdlmon()')
    root.putChild("dlmon", DLMon(dlstatus))
    log.msg('\t\t\t\t\t=> OK')

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

