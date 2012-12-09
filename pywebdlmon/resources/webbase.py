#!/usr/bin/env python

import os.path
import json

from twisted.python import log
from twisted.web.resource import Resource
from twisted.web.static import File as StaticFile
from txroutes import Dispatcher
from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions



FORMATS = ('html', 'json')


class Controller(object):
    def __init__(self, cfg, dlstatuses):
        self.templates = TemplateLookup(directories=['templates'])
        self.cfg = cfg
        self.dlstatuses = dlstatuses

    def _error(self, request, code, msg):
            request.setHeader("content-type", "text/html")
            request.setHeader("response-code", code)
            return str(self.templates.get_template('error.html').render(cfg=self.cfg, code=code, msg=msg))

    def _jsondumps(self, data):
        return json.dumps(data, indent=4, sort_keys=True)

    def _render(self, request, format, template, data, **kwargs):
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
        stations = self.dlstatuses.keys()
        data = dict(
                formats=dict(
                    html='/html/instances',
                    json='/json/instances',
                ),
                instances=[
                        dict(
                            name=stn,
                            status=dict(
                                ((fmt, '/'.join(('',fmt,'instances',stn,'status')))
                                    for fmt in FORMATS)),
                            stations=dict(
                                ((fmt,
                                    '/'.join(('',fmt,'instances',stn,'stations')))
                                    for fmt in FORMATS)),
                        )
                        for stn in stations
                ]
        )
        return self._render(request, format, template='instances', data=data)

    def instance_status(self, request, format, instance):
        try:
            dlstatus = self.dlstatuses[instance]
        except KeyError:
            return self._error(request, 404, "Unknown DLMon Instance: %r" % instance)
        data = dict(instance_status=dict(dlstatus.status))
        data['formats'] = dict(
            # add instance name to urls
            html='/html/instances/%s/status' % instance,
            json='/json/instances/%s/status' % instance,
        )
        data['instance_status']['dataloggers'] = data['instance_status']['dataloggers'].values()
        return self._render(request, format, template='instance_status',
                data=data, instance=instance)

    def stations(self, request, format, instance):
        try:
            dlstatus = self.dlstatuses[instance]
        except KeyError:
            return self._error(request, 404, "Unknown DLMon Instance: %r" % instance)
        data=dict(stations=dlstatus.status['dataloggers'].keys())
        data['formats'] = dict(
            # add instance name to urls
            html='/html/instances/%s/stations' % instance,
            json='/json/instances/%s/stations' % instance,
        )
        return self._render(request, format, template='stations', data=data,
                instance=instance)

    def station_status(self, request, format, instance, station):
        try:
            dlstatus = self.dlstatuses[instance]
        except KeyError:
            return self._error(request, 404, "Unknown DLMon Instance: %r" % instance)
        dataloggers = dlstatus.status['dataloggers']
        try:
            data = dict(station_status=dataloggers[station.decode('utf8')])
        except KeyError:
            return self._error(request, 404, "Unknown Station: %r" % station)
        # add formats
        data['formats'] = dict(
            # add instance name to urls
            html='/html/instances/%s/stations/%s/status' % (instance, station),
            json='/json/instances/%s/stations/%s/status' % (instance, station),
        )
        return self._render(request, format, template='station_status',
                data=data, instance=instance, station=station)


def get_dispatcher(cfg, dlstatuses):
    c = Controller(cfg, dlstatuses)
    d = Dispatcher()
    def connect(name, url):
        d.connect(name, url, c, action=name)
    connect('root',            '/')
    connect('static',          '/static/{file}')
    connect('index',           '/{format}')
    connect('instances',       '/{format}/instances')
    connect('instance_status', '/{format}/instances/{instance}/status')
    connect('stations',        '/{format}/instances/{instance}/stations')
    connect('station_status',  '/{format}/instances/{instance}/stations/{station}/status')
    return d

