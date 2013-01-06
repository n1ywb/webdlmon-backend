#!/usr/bin/env python
"""Python Web DLMON Daemon

This is the twisted.web application.
"""

# Std lib
import sys

# Twisted
from twisted.python import log
from twisted.internet import reactor
from twisted.web.server import Site

# Web sockets
from txws import WebSocketFactory

# StreamProxy
from streamprox.proxy import BufferingProxyFactory
from streamprox.packet_buffer import PacketBuffer
from streamprox.dispatcher import ExampleDispatcher

# This project
import config
from transport.webbase import get_dispatcher
from transport.ws import StreamFactory
from model import InstanceCollection


class App(object):
    """The twisted.web application."""
    def run(self, options):
        """Run the app. Options as parsed by optparse."""
        log.startLogging(sys.stdout)
        cfg = config.Config(options)
        instances = InstanceCollection(cfg)

        # website
        log.msg('Build as site object:')
        dispatcher = get_dispatcher(cfg, instances)
        website = Site( dispatcher )
        log.msg('\t\t\t\t\t=> OK')

        # websockets
        # Somehow the websocket server needs to be commanded to send updated
        # state data.
        # Sending a keepalive might be good too
        log.msg('Setup TCP port:')

        factory = BufferingProxyFactory()
        factory.buffer_factory = PacketBuffer

        websocketfactory = WebSocketFactory(StreamFactory(dispatcher,
            instances))

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

