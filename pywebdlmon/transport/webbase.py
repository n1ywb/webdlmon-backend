#!/usr/bin/env python

import os.path
import json

from twisted.python import log
from twisted.web import server
from twisted.web.resource import Resource
from twisted.web.static import File as StaticFile

from txroutes import Dispatcher

from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions

from pywebdlmon.model import UnknownInstance, UnknownStation, UnknownFormat

class Controller(object):
    def __init__(self, cfg, instances):
        self.cfg = cfg
        self.instances = instances

    def _error(self, request, code, msg):
        # TODO return JSON error object for json queries
        request.setHeader("content-type", "text/html")
        request.setHeader("response-code", code)
        return str(self.cfg.templates.get_template('error.html').render(cfg=self.cfg, code=code, msg=msg))

    def _render(self, request, format, template, data, **kwargs):
        # TODO Need to keep this header-setting functionality
        request.setHeader("response-code", 200)
        if format == 'json':
	    request.setHeader("content-type", "application/json")
	    if request.args.has_key('callback'):
		    request.setHeader("content-type", "application/javascript")
		    return request.args['callback'][0] + '(' + self._jsondumps(data) + ')'
            return self._jsondumps(data)

        elif format == 'html':
            request.setHeader("content-type", "text/html")
            template = self.templates.get_template(template + '.html')
            try:
                r = template.render(cfg=self.cfg, data=data, **kwargs)
            except Exception:
                log.err(exceptions.text_error_template().render())
                return self._error(request, 500, "Template Error")
            return str(template.render(cfg=self.cfg, data=data, **kwargs))

        else:
            return self._error(request, 400, "Unknown format %r" % format)

    def root(self, request):
        return self.index(request, 'html')

    def static(self, request, file):
        # TODO santize file
        return StaticFile(os.path.join('static', file)).render(request)

    def index(self, request, format):
        data = dict(
                    formats=dict(
                        html='/html',
                        json='/json',
                    ),
                   resources=dict(
                       instances=dict(
                           html='/html/instances',
                           json='/json/instances'
                           )
                       )
                   )
        return self._render(request, format, template='index', data=data)

    def instances(self, request, format):
        stations = self.instances.keys()
        data = dict(
                formats=dict(
                    html='/html/instances',
                    json='/json/instances',
                ),
                # this one is sort of special
        )
        return self._render(request, format, template='instances', data=data)

    def _handler_helper(inner_func):
        def wrapper_func(self, request, *args, **kwargs):
            try:
                status = inner_func(self, request, *args, **kwargs)
            except UnknownInstance, e:
                return self._error(request, 404, "Unknown DLMon Instance '%s'" % e)
            except UnknownStation, e:
                return self._error(request, 404, "Unknown Station: '%s'" % e)
            except UnknownFormat, e:
                return self._error(request, 404, "Unknown Format: '%s'" % e)
            def cb(r):
                assert r is not None
                request.write(r)
                request.finish()
            status.addCallback(cb)
            return server.NOT_DONE_YET
        return wrapper_func

    @_handler_helper
    def instance_status(self, request, transport, instance, format):
        # TODO If this controller is to be unified with the WS controller, we
        # need a way to differentiate between sync and async requests.
        instance = self.instances.get_instance(instance)
        status = instance.instance_status.get_format(format, immediate=True)
        return status

    @_handler_helper
    def station_list(self, request, transport, instance, format):
        instance = self.instances.get_instance(instance)
        status = instance.station_list.get_format(format, immediate=True)
        return status

    @_handler_helper
    def station_status(self, request, transport, instance, station, format):
        instance = self.instances.get_instance(instance)
        station = instance.instance_status.get_station(station)
        status = station.get_format(format, immediate=True)
        return status


def get_dispatcher(cfg, instances):
    c = Controller(cfg, instances)
    d = Dispatcher()
    def connect(name, url):
        d.connect(name, url, c, action=name)
#    connect('root',            '/')
#    connect('static',          '/static/{file}')
#    connect('index',           '/{format}')
#    connect('instances',       '/{format}/instances')
    connect('instance_status', '/{transport}/dlmon/instances/{instance}/status{.format}')
    connect('station_list',    '/{transport}/dlmon/instances/{instance}/stations{.format}')
    connect('station_status',  '/{transport}/dlmon/instances/{instance}/stations/{station}/status{.format}')
    return d

