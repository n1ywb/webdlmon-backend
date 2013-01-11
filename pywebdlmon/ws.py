#!/usr/bin/env python

from autobahn.websocket import WebSocketServerProtocol


class RequestishProtocol(WebSocketServerProtocol):
    """Looks like a twisted.web Request object."""
    args = {}

    def write(self, msg):
        self.sendMessage(msg)

    def setHeader(self, name, code):
        pass

    def finish(self):
        # TODO: is this right?
        self.transport.close()

    def getheader(self, name):
        return None

