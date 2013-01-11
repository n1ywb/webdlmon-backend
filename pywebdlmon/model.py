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

class UnknownFormat(Exception): pass


class DataObject(object):
    def __init__(self, cfg):
        self.cfg = cfg
        self.template = cfg.templates.get_template(self.template_name)
        self.data = ObservableDict(html='', json='')

    def update(self, data, **kwargs):
        try:
            self.data['html'] = self.template.render(data=data, **kwargs).encode('utf-8')
        except Exception:
            log.err("Error rendering template")
            # twisted.log.msg munges the formatting; use print instead
            print text_error_template().render()
            raise
        self.data['json'] = json.dumps(data, indent=4, sort_keys=True)

    def get_format(self, format, immediate):
        if self.data.has_key(format):
            return self.data.deferred_getitem(format, immediate)
        else:
            raise UnknownFormat(format)


class StationList(DataObject):
    template_name = 'stations.html'

    def __init__(self, instance_name, *args, **kwargs):
        self.instance_name = instance_name
        self.stations=set()
        super(StationList, self).__init__(*args, **kwargs)

    def update(self, updated_stations):
        self.stations |= set(updated_stations['dataloggers'].iterkeys())
        data = {'station_list': list(self.stations)}
        super(StationList, self).update(data, instance=self.instance_name)


class StationStatus(DataObject):
    template_name = 'station_status.html'

    def __init__(self, instance_name, station_name, *args, **kwargs):
        self.instance_name = instance_name
        self.station_name = station_name
        super(StationStatus, self).__init__(*args, **kwargs)

    def update(self, station_status):
        data = dict(station_status=station_status)
        super(StationStatus, self).update(data, instance=self.instance_name, station=self.station_name)


class InstanceStatus(DataObject):
    template_name = 'instance_status.html'

    def __init__(self, instance_name, *args, **kwargs):
        self.instance_name = instance_name
        # Individual station statuses
        self.stations = dict()
        # Full instance status in
        self.status = dict()
        super(InstanceStatus, self).__init__(*args, **kwargs)

    def update(self, updated_stations):
        # Do my own update
        # TODO Geoff wants this to be a list, not a dict, b/c javascript sucks
        self.status.update(updated_stations)
        status = dict(self.status)
        status['dataloggers'] = status['dataloggers'].values()
        data = dict(instance_status=status)
        super(InstanceStatus, self).update(data, instance=self.instance_name)
        # Now update my stations
        for station_name, station_status in updated_stations['dataloggers'].iteritems():
            try:
                station = self.stations[station_name]
            except KeyError:
                station = StationStatus(self.instance_name, station_name, self.cfg)
                self.stations[station_name] = station
            station.update(station_status)

    def get_station(self, station_name):
        try:
            return self.stations[station_name]
        except KeyError:
            raise UnknownStation(station_name)


class InstanceUpdate(DataObject):
    template_name = 'instance_update.html'

    def __init__(self, instance_name, *args, **kwargs):
        self.instance_name = instance_name
        super(InstanceUpdate, self).__init__(*args, **kwargs)

    def update(self, updated_stations):
        if len(updated_stations['dataloggers']) > 0:
            status = dict(updated_stations)
            status['dataloggers'] = status['dataloggers'].values()
            data = dict(instance_update=status)
            super(InstanceUpdate, self).update(data, instance=self.instance_name)


class Instance(DataObject):
    template_name = 'instance.html'

    def __init__(self, instance_name, sources, cfg, *args, **kwargs):
        self.instance_name = instance_name
        #self.status_update = StatusUpdate()
        self.instance_status = InstanceStatus(instance_name, cfg)
        self.station_list = StationList(instance_name, cfg)
        self.instance_update = InstanceUpdate(instance_name, cfg)
        for source in sources:
# TODO Fix async connect packet corruption issue.
#            def on_connect(r):
#                self.reap(source)
#            d = source.connect()
#            d.addCallback(on_connect)
            log.msg("connecting to src %r" % source)
            # NOTE Using sync connect until we fix async connect
            kudu.orb.Orb.connect(source)
            # NOTE this is handy for debugging but maybe not for production
            # source.seek(kudu.orb.ORBOLDEST)
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
        self.instance_status.update(updated_stations, )
        self.station_list.update(updated_stations)
        self.instance_update.update(updated_stations)
        return
        # NOTE not sure yet what if any data instance should export. Probably
        # none. Some metadata would be handy though.
        data = dict()
        data['name'] = self.instance_name
        super(Instance, self).update(data)


class InstanceCollection(DataObject):
    template_name = 'instances.html'

    def __init__(self, cfg):
        super(InstanceCollection, self).__init__(cfg)
        instances = self.instances = {}
        for instance_name, srcs in cfg.instances.iteritems():
            sources = [StatusPktSource(srcname, 'r', select=srccfg.match,
                                                     reject=srccfg.reject)
                        for srcname,srccfg in srcs.iteritems()]
            instance = Instance(instance_name, sources, cfg)
            instances[instance_name] = instance
            log.msg("New dlmon instance: %s" % instance_name)
        self.update()

    def update(self):
        data = dict(instances=self.instances.keys())
        super(InstanceCollection, self).update(data)

    def get_instance(self, instance_name):
        try:
            return self.instances[instance_name]
        except KeyError, e:
            raise UnknownInstance(instance_name)

