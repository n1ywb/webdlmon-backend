#!/usr/bin/env python

import json

from twisted.python import log

from mako.exceptions import text_error_template

from kudu.exc import OrbIncomplete
from kudu.twisted.util import ObservableDict
import kudu.orb

from orb import StatusPktSource


FORMATS = ('html', 'json')

REAP_TIMEOUT = 2.0


class UnknownInstance(Exception): pass

class UnknownStation(Exception): pass


class DataObject(object):
    def __init__(self, cfg):
        self.template = cfg.templates.get_template(self.template_name)
        self.data = ObservableDict(html=None, json=None)

    # this super should make templates and json
    # subclasses should connect incoming updates to html/json maker
    def update(self, data):
        try:
            self.data['html'] = self.template.render(data=data)
        except Exception:
            log.err("Error rendering template")
            print text_error_template().render()
        self.data['json'] = json.dumps(data, indent=4, sort_keys=True)


class StationList(DataObject):
    template_name = 'stations.html'

    def __init__(self, *args, **kwargs):
        self.stations=set()
        super(StationList, self).__init__(*args, **kwargs)

    def update(self, updated_stations):
        self.stations |= set(updated_stations['dataloggers'].iterkeys())
        data = {'stations': list(self.stations)}
        super(StationList, self).update(data)


class Station(dict):
    pass


class InstanceStatus(DataObject):
    template_name = 'instance_status.html'

    def __init__(self, *args, **kwargs):
        # Store individual station statuses in here
        self.stations = dict()

        # Store full instance status in here
        self.status = dict()

        super(InstanceStatus, self).__init__(*args, **kwargs)

    def update(self, updated_stations):
        updated_stations = updated_stations['dataloggers']
        self.status.update(updated_stations)
#        for station_name, station_status in updated_stations.iteritems():
#            try:
#                station = self.stations[station_name]
#            except KeyError:
#                station = self.stations[station_name] = Station()
#            status.update(station.update(station_status))
        data = dict(instance_status=self.status)
        super(InstanceStatus, self).update(data)

    def get_station(self, name):
        try:
            return self.stations[name]
        except KeyError:
            raise UnknownStation(name)


class Instance(DataObject):
    # TODO FIXME
    template_name = 'index.html'

    def __init__(self, name, sources, cfg, *args, **kwargs):
        self.name = name
        #self.status_update = StatusUpdate()
        self.instance_status = InstanceStatus(cfg)
        self.station_list = StationList(cfg)
        for source in sources:
# TODO Fix async connect packet corruption issue
#            def on_connect(r):
#                self.reap(source)
#            d = source.connect()
#            d.addCallback(on_connect)
            log.msg("connecting to src %r" % source)
            # NOTE Using syncronous connect until we fix async connect
            kudu.orb.Orb.connect(source)
            source.seek(kudu.orb.ORBOLDEST)
            self.reap(source)
        super(Instance, self).__init__(cfg, *args, **kwargs)

    def reap(self, source):
        d = source.reap_timeout(REAP_TIMEOUT)
        d.addCallbacks(self.on_reap, errback=self.on_reap_error,
                callbackKeywords=dict(source=source),
                errbackKeywords=dict(source=source), )
        return d

    def on_reap_error(self, failure, source):
        failure.trap(OrbIncomplete)
        return self.reap(source)

    def on_reap(self, pfdict, source):
        r = self.update(pfdict)
        self.reap(source)
        return r

    def update(self, updated_stations):
        self.instance_status.update(updated_stations)
        self.station_list.update(updated_stations)
        return
        # NOTE not sure yet what if any data instance should export
        data = dict()
        data['name'] = self.name
        super(Instance, self).update(data)


class InstanceCollection(object):
    """A collection of dlmon instances."""
    def __init__(self, cfg):
        instances = self.instances = {}
        for name, srcs in cfg.instances.iteritems():
            sources = [StatusPktSource(srcname, 'r', select=srccfg.match,
                                                     reject=srccfg.reject)
                        for srcname,srccfg in srcs.iteritems()]
            instance = Instance(name, sources, cfg)
            instances[name] = instance
            log.msg("New dlmon instance: %s" % name)

    def get_instance(self, name):
        try:
            return self.instances[name]
        except KeyError, e:
            raise UnknownInstance(name)

