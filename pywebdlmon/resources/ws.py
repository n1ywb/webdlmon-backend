#!/usr/bin/env python

import json

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



# Should these be different factories? Well we don't even know what the URI is
# until AFTER we read data, so that wouldn't work. Somehow the protocol class
# needs to delegate to one of these appropriately. Using deferreds?

class Base(Object):
    pass


class InstanceStatus(Base):
    pass


class StationStatus(Base):
    pass


class StationWaveforms(Base):
    pass

