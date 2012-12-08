#!/usr/bin/env python
"""Python Web DLMON Daemon

This is the twisted.web application.
"""

import functools
import traceback
from optparse import OptionParser
import sys
#import datetime
from pprint import pprint, pformat
#from subprocess import Popen,PIPE
import os
import os.path
import logging

from twisted.python import log
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web import static

sys.path.append(os.environ['ANTELOPE'] + '/data/python')

from antelope import _stock

from dlstatus import DLStatus, DLSource, DEFAULT_MATCH
import config

from resources.webbase import get_dispatcher

# Twisted websockets
from twisted.application import internet
from twisted.application.service import Application, Service

from txws import WebSocketFactory



# Websockets
STATIC_ROOT='html'
WEBSOCKETS_PORT=6998

import json
import time

from twisted.internet.protocol import Factory, Protocol


class UnknownInstance(Exception): pass

class Stream(Protocol):
    def __init__(self, start_stream_cb):
        self.start_stream_cb = start_stream_cb

    def connectionMade(self):
        log.msg("Connected on websockets port, loc: %r" %
                self.transport.location)
        # monkey patch txws to notify us after it parses the location field
        oldValidateHeaders = self.transport.validateHeaders
        def wrap(*args, **kwargs):
            r = oldValidateHeaders(*args, **kwargs)
            if r: self.headersValidated()
            return r
        self.transport.validateHeaders = wrap

    def headersValidated(self):
        log.msg("Websocket headers validated, loc: %r" %
                self.transport.location)
        # start streaming?
        try:
            path = self.transport.location.split('/')
            bl1, ws, name = path
        except Exception:
            self.transport.write(json.dumps({'error': 400,
                'path': self.transport.location}))
            self.transport.loseConnection()
            return
        try:
            self.start_stream_cb(self, name)
        except UnknownInstance, e:
            self.transport.write(json.dumps({'error': 404,
                'path': self.transport.location}))
            self.transport.loseConnection()
        except Exception, e:
            self.transport.write(json.dumps({'error': 500}))
            self.transport.loseConnection()


class StreamFactory(Factory):
    def __init__(self, start_stream_cb):
        self.start_stream_cb = start_stream_cb
    def buildProtocol(self, addr):
        return Stream(self.start_stream_cb)


# StreamProxy
from streamprox.proxy import BufferingProxyFactory
from streamprox.packet_buffer import PacketBuffer
from streamprox.dispatcher import ExampleDispatcher


class App(object):
    """The twisted.web application."""
    def run(self, options):
        """Run the app. Options as parsed by optparse."""
        log.startLogging(sys.stdout)
        cfg = config.Config(options)
        dlstatuses = {}
        for dlstatus_name, srcs in cfg.instances.iteritems():
            dlstatus = DLStatus()
            dlstatuses[dlstatus_name] = dlstatus
            for srcname,srccfg in srcs.iteritems():
                source = DLSource(srcname, srccfg.match, srccfg.reject)
                # TODO use deferreds instead?
                source.add_sink(dlstatus.update_status)
            log.msg("New dlstatus: %s" % dlstatus_name)

        # website
        log.msg('Build as site object:')
        dispatcher = get_dispatcher(cfg, dlstatuses)
        website = Site( dispatcher )
        log.msg('\t\t\t\t\t=> OK')

        # TODO deferrable?
        def start_stream_cb(stream, name):
            try:
                dlstatuses[name].add_stream(stream)
            except KeyError:
                log.err("404 not found: %r " % name)
                raise UnknownInstance(name)
            else:
                log.msg("streaming %r" % name)

        # websockets
        # Somehow the websocket server needs to be commanded to send updated
        # state data.
        # Sending a keepalive might be good too
        log.msg('Setup TCP port:')

        factory = BufferingProxyFactory()
        factory.buffer_factory = PacketBuffer

        websocketfactory = WebSocketFactory(StreamFactory(start_stream_cb))

        # route /ws to websockets, everything else including / to http
        ExampleDispatcher.prefix1 = "/ws"
        ExampleDispatcher.site1 = websocketfactory

        ExampleDispatcher.prefix2 = "/"
        ExampleDispatcher.site2 = website

        factory.dispatcher_factory = ExampleDispatcher

        reactor.listenTCP(cfg.port, factory, interface=cfg.bind_address)
        log.msg('\t\t\t\t\t=> OK')

        log.msg('Run reactor:')
        reactor.run()

