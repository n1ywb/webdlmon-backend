#!/usr/bin/env python

import json

from twisted.python import log
from twisted.internet.protocol import Factory, Protocol


class Controller(object):
    """Routes controller"""

    def __init__(self, instances):
        self.streams = set()
        self.instances = instances

    def instance_status(self, protocol, format, instance_name):
        # get instance
        instance = self.instances[instance_name]
        protocol.instance = instance
        protocol.instance_name = instance_name
        instance.updated_stations.addCallback(protocol.instance_status_cb)

    def station_status(self, protocol, format, instance_name, station):
        instance = self.instances[instance_name]
        protocol.instance = instance
        protocol.instance_name = instance_name
        protocol.station = station
        instance.updated_stations.addCallback(protocol.station_status_cb)


class FakeRequest(object):
    args = dict()
    @staticmethod
    def setHeader(*args, **kwargs):
        pass


class Stream(Protocol):
    def __init__(self, dispatcher, controller):
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
            webcontroller = result.get('controller', None)
            self.webcontroller = self.dispatcher._controllers.get(webcontroller)
            del result['controller']
            action = result.get('action', None)
            if action is not None:
                del result['action']
                handler = getattr(controller, action, None)
        log.msg(repr((controller, handler)))
        if handler:
            handler(self, **result)
        else:
            self.transport.write(json.dumps({
                'error': 404,
                'path': self.transport.location}))
            #self.transport.loseConnection()

    def instance_status_cb(self, updated_stations):
        self.instance.updated_stations.addCallback(self.instance_status_cb)
        if updated_stations is not None:
            for stn in updated_stations:
                r = self.webcontroller.station_status(FakeRequest, 'json',
                        self.instance_name, stn)
                self.transport.write(r)

    def station_status_cb(self, updated_stations):
        self.instance.updated_stations.addCallback(self.station_status_cb)
        if updated_stations is not None and self.station in updated_stations:
            r = self.webcontroller.station_status(FakeRequest, 'json', self.instance_name, self.station)
            self.transport.write(r)


class StreamFactory(Factory):
    def __init__(self, dispatcher, instances):
        self.dispatcher = dispatcher
        self.controller = Controller(instances)
    def buildProtocol(self, addr):
        return Stream(self.dispatcher, self.controller)

