#!/usr/bin/env python

import json

from twisted.python import log
from twisted.internet.protocol import Factory, Protocol


class Controller(object):
    """Routes controller"""
    def instance_status(self, protocol, format, instance):
        protocol.start_stream_cb(protocol, instance)

    def station_status(self, protocol):
        pass


class UnknownInstance(Exception): pass

class Stream(Protocol):
    def __init__(self, start_stream_cb, dispatcher, controller):
        self.start_stream_cb = start_stream_cb
        self.dispatcher = dispatcher
        self.controller = controller

    def connectionMade(self):
        log.msg("Connected on websockets port, loc: %r" %
                self.transport.location)
        # monkey patch txws to notify us after it parses the location field
        # should this use a deferred?
        oldValidateHeaders = self.transport.validateHeaders
        def wrap(*args, **kwargs):
            r = oldValidateHeaders(*args, **kwargs)
            if r: self.headersValidated()
            return r
        self.transport.validateHeaders = wrap

    def headersValidated(self):
        log.msg("Websocket headers validated, loc: %r" %
                self.transport.location)
        result = self.dispatcher._mapper.match(self.transport.location)
        log.msg(result)

        handler = None

        controller = self.controller

        if result is not None:
            del result['controller']
            action = result.get('action', None)

            if action is not None:
                del result['action']
                handler = getattr(controller, action, None)

        log.msg(repr((controller, handler)))

        if handler:
            return handler(self, **result)
        else:
            self.transport.write(json.dumps({
                'error': 404,
                'path': self.transport.location}))
            self.transport.loseConnection()


class StreamFactory(Factory):
    def __init__(self, start_stream_cb, dispatcher):
        self.start_stream_cb = start_stream_cb
        self.dispatcher = dispatcher
        self.controller = Controller()
    def buildProtocol(self, addr):
        return Stream(self.start_stream_cb, self.dispatcher, self.controller)





