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


class Controller(object):
    def __init__(self, cfg, instances):
        self.cfg = cfg
        self.instances = instances

    def _error(self, request, code, msg):
        # TODO return JSON error object for json queries
        # TODO Fix template lookup
        request.setHeader("content-type", "text/html")
        request.setHeader("response-code", code)
        return str(self.templates.get_template('error.html').render(cfg=self.cfg, code=code, msg=msg))

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

    def instance_status(self, request, format, instance):
        # TODO Move exception handling to a common location for all handlers
        # TODO If this controller is to be unified with the WS controller, we
        # need a way to differentiate between sync and async requests.
        try:
            instance = self.instances.get_instance(instance)
        except UnknownInstance:
            return self._error(request, 404, "Unknown DLMon Instance: %r" % instance)

        try:
            status = instance.instance_status.data.deferred_getitem('json', immediate=True)
        except KeyError:
            # Seriously, consolidate this crap somewhere else
            return self._error(request, 404, "Unknown Format: %r" % instance)

        def cb(r):
            assert r is not None
            request.write(r)
            request.finish()

        status.addCallback(cb)

        return server.NOT_DONE_YET

    def stations(self, request, format, instance):
        try:
            instance = self.instances[instance]
        except KeyError:
            return self._error(request, 404, "Unknown DLMon Instance: %r" % instance)
        data['formats'] = dict(
            # add instance name to urls
            html='/html/instances/%s/stations' % instance,
            json='/json/instances/%s/stations' % instance,
        )
        return self._render(request, format, template='stations', data=data,
                instance=instance)

    def station_status(self, request, format, instance, station):
        try:
            instance = self.instances[instance]
        except KeyError:
            return self._error(request, 404, "Unknown DLMon Instance: %r" % instance)
        return self._render(request, format, template='station_status',
                data=data, instance=instance, station=station)


def get_dispatcher(cfg, instances):
    c = Controller(cfg, instances)
    d = Dispatcher()
    def connect(name, url):
        d.connect(name, url, c, action=name)
#    connect('root',            '/')
#    connect('static',          '/static/{file}')
#    connect('index',           '/{format}')
#    connect('instances',       '/{format}/instances')
    connect('instance_status', '/{format}/instances/{instance}/status')
    connect('stations',        '/{format}/instances/{instance}/stations')
#    connect('station_status',  '/{format}/instances/{instance}/stations/{station}/status')
    return d

