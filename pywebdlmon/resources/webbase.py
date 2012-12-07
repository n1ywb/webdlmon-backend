#!/usr/bin/env python

from twisted.web.resource import Resource


class Controller(object):
    def __init__(self, cfg, dlstatuses)
        self.cfg = cfg
        self.dlstatuses = dlstatuses

    def _error(self, request, code, msg):
            request.setHeader("content-type", "text/html")
            request.setHeader("response-code", code)
            return str(templates.get_template('error.html').render(cfg=self.cfg, code=code, msg=msg))

    def _render(self, request, format, template, data):
        request.setHeader("response-code", 200)
        if format == 'json':
	    request.setHeader("content-type", "application/json")
	    if request.args.has_key('callback'):
		    request.setHeader("content-type", "application/javascript")
		    return request.args['callback'][0] + '(' + json.dumps(data) + ')'
            return json.dumps(data)

        elif format == 'html':
            request.setHeader("content-type", "text/html")
            template = templates.get_template(template + '.html')
            return str(template.render(cfg=self.cfg, data=data))

        else:
            return self._error(request, 400, "Unknown format %r" % format)

    def index(self, request):
        return self._render(request, format, template=__name__, data=None)

    def instances(self, request, format):
        return self._render(request, format, template=__name__,
                data=self.dlstatuses.iterkeys())

    def instance_status(self, request, format, instance):
        try:
            dlstatus = self.dlstatuses[instance]
        except KeyError:
            return self._error(request, 404, "Unknown DLMon Instance: %r" % instance)
        data = dict(dlstatus.status)
        data['dataloggers'] = data['dataloggers'].values()
        return self._render(request, format, template=__name__, data=data)

    def stations(self, request, format, instance):
        try:
            dlstatus = self.dlstatuses[instance]
        except KeyError:
            return self._error(request, 404, "Unknown DLMon Instance: %r" % instance)
        data=dlstatus.status['dataloggers'].iterkeys()
        return self._render(request, format, template=__name__, data=data)

    def station_status(self, request, format, instance, station):
        try:
            dlstatus = self.dlstatuses[instance]
        except KeyError:
            return self._error(request, 404, "Unknown DLMon Instance: %r" % instance)
        dataloggers = dlstatus.status['dataloggers'] # 500 if this fails
        try:
            data = dataloggers[id]
        except KeyError:
            # TODO set status code to 404
            # TODO return an error template instead of a dumb string
            return self._error(request, 404, "Unknown Station: %r" % station)
        return self._render(request, format, template=__name__, data=data)


def get_dispatcher(dlstatuses or whatever):
    c = Controller(cfg, dlstatuses)
    d = Dispatcher()
    d.connect('index',             '/', c, action='index')
    d.connect('instances',         '/{format}/instances', c, action='instances')
    d.connect('instance_status',   '/{format}/instances/{instance}/status', c,
        action='instance_status')
    d.connect('stations',          '/{format}/instances/{instance}/stations', c,
        action='instance_stations')
    d.connect('station_status',    '/{format}/instances/{instance}/stations/{station}/status', c,
        action='station_status')
    return d
