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

# This project
from pywebdlmon import config
from pywebdlmon.controller import get_dispatcher
from pywebdlmon.model import InstanceCollection


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
        log.msg('Listening on %s' % cfg.bind_address)

        reactor.listenTCP(cfg.port, website, interface=cfg.bind_address)
        log.msg('\t\t\t\t\t=> OK')

        log.msg('Run reactor:')
        reactor.run()

