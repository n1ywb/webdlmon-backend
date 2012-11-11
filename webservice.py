#!/usr/bin/env python
import functools
import traceback
from optparse import OptionParser
import sys
#import datetime
from pprint import pprint
#from subprocess import Popen,PIPE
import os
import os.path
import logging

from twisted.python import log
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site

sys.path.append(os.environ['ANTELOPE'] + '/data/python')

from dlstatus import DLStatus, DLSource, DEFAULT_MATCH


config = {
        # 'dlmon_name': [('orb1', 'match regex (None for default)', 'reject
        # regex (None for default)'), ... ],
        'dlmon': [('anfexport:status', None, None), ('anfexport:cascadia_status', None, None)],
        'foo': [('anfexport:prelim', None, None)],
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


class DLMon(ROOT):
    def __init__(self, name, dlstatus):
        ROOT.__init__(self)
        self.name = name
        self.dlstatus = dlstatus
        # This is a little ugly but supports compartmentalization
        dlstatus.new_stn_cb = self.new_stn

    def new_stn(self, dlstatus, id):
        print "%s new station %s" % (self.name, id)
        dlmon = DLMonOneStn(dlstatus, id)
        self.putChild(id, dlmon)

    def render(self, request):
        try:
	    request.setHeader("content-type", "application/json")
	    if request.args.has_key('callback'):
		    request.setHeader("content-type", "application/javascript")
		    return request.args['callback'][0] + '(' + self.dlstatus.to_json() + ')'
            return self.dlstatus.to_json()
        except Exception, e:
	    raise


class DLMonOneStn(ROOT):
    def __init__(self, dlstatus, id):
        """id == station id"""
        ROOT.__init__(self)
        self.dlstatus = dlstatus
        self.id = id

    def render(self, request):
        f = functools.partial(self.dlstatus.stn_to_json, self.id)
        try:
	    request.setHeader("content-type", "application/json")
	    if request.args.has_key('callback'):
		    request.setHeader("content-type", "application/javascript")
		    return request.args['callback'][0] + '(' + f() + ')'
            return f()
        except Exception, e:
	    raise


class App(object):
    def run(self):
        root = ROOT()
        dlstatuses = {}
        for dlstatus_name,v in config.items():
            dlstatus = DLStatus()
            dlmon = DLMon(dlstatus_name, dlstatus)
            dlstatuses[dlstatus_name] = dlstatus
            for orbname,match,rej in v:
                match = match if match is not None else DEFAULT_MATCH
                rej = rej if rej is not None else ''
                source = DLSource(orbname,match,rej)
                source.add_sink(dlstatus.update_status)
            log.msg("New dlstatus: %s" % dlstatus_name)
            root.putChild(dlstatus_name, dlmon)


        log.msg('Build as site object:')
        website = Site( root )
        log.msg('\t\t\t\t\t=> OK')

        log.msg('Setup TCP port:')
        reactor.listenTCP(7000, website)
        log.msg('\t\t\t\t\t=> OK')

        log.msg('Run reactor:')
        reactor.run()


def main(args=None):
    if args is None:
        args = sys.argv
    op = OptionParser()
    op.add_option("-v", "--verbose", dest="verbose",
                     action="store_true")
    (options, args) = op.parse_args(args[1:])
    app = App()
    app.run()


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    exit(main())

