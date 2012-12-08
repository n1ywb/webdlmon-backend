#!/usr/bin/env python

import json

from twisted.web.resource import Resource
from txroutes import Dispatcher
from mako.template import Template
from mako.lookup import TemplateLookup


class Controller(object):
    def __init__(self, cfg, dlstatuses):
        self.templates = TemplateLookup(directories=['templates'])
        self.cfg = cfg
        self.dlstatuses = dlstatuses

    def _error(self, request, code, msg):
            request.setHeader("content-type", "text/html")
            request.setHeader("response-code", code)
            return str(self.templates.get_template('error.html').render(cfg=self.cfg, code=code, msg=msg))

    def _render(self, request, format, template, data, **kwargs):
        request.setHeader("response-code", 200)
        if format == 'json':
	    request.setHeader("content-type", "application/json")
	    if request.args.has_key('callback'):
		    request.setHeader("content-type", "application/javascript")
		    return request.args['callback'][0] + '(' + json.dumps(data) + ')'
            return json.dumps(data)

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

    def index(self, request):
        return self._render(request, 'html', template='index', data=None)

    def instances(self, request, format):
        return self._render(request, format, template='instances',
                data=self.dlstatuses.keys())

    def instance_status(self, request, format, instance):
        try:
            dlstatus = self.dlstatuses[instance]
        except KeyError:
            return self._error(request, 404, "Unknown DLMon Instance: %r" % instance)
        data = dict(dlstatus.status)
        data['dataloggers'] = data['dataloggers'].values()
        return self._render(request, format, template='instance_status',
                data=data, instance=instance)

    def stations(self, request, format, instance):
        try:
            dlstatus = self.dlstatuses[instance]
        except KeyError:
            return self._error(request, 404, "Unknown DLMon Instance: %r" % instance)
        data=dlstatus.status['dataloggers'].keys()
        return self._render(request, format, template='stations', data=data,
                instance=instance)

    def station_status(self, request, format, instance, station):
        try:
            dlstatus = self.dlstatuses[instance]
        except KeyError:
            return self._error(request, 404, "Unknown DLMon Instance: %r" % instance)
        dataloggers = dlstatus.status['dataloggers']
        try:
            data = dataloggers[station.decode('utf8')]
        except KeyError:
            return self._error(request, 404, "Unknown Station: %r" % station)
        return self._render(request, format, template='station_status',
                data=data, instance=instance, station=station)


def get_dispatcher(cfg, dlstatuses):
    c = Controller(cfg, dlstatuses)
    d = Dispatcher()
    def connect(name, url):
        d.connect(name, url, c, action=name)
    connect('index',           '/')
    connect('instances',       '/{format}/instances')
    connect('instance_status', '/{format}/instances/{instance}/status')
    connect('stations',        '/{format}/instances/{instance}/stations')
    connect('station_status',  '/{format}/instances/{instance}/stations/{station}/status')
    return d
