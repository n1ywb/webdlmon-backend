#!/usr/bin/env python

"""Data objects.

Each data object has at minimum the attributes listed in the DataObject parent
class.

Data objects implement the observer pattern; IE they listen to each other for
update events to know when to update their own data.

Data objects pre-generate their data in serialized format in response to each
update. Thus data access clients must simply read the appropriate serialized
datum at the appropriate data object.

Furthermore, asynchronous clients may listen to the update event to know when
new data is available.
"""


import json
from twisted.python import log
from twisted.internet.defer import Deferred


class UnknownStation(Exception): pass


class DataObject(object):
    def __init__(self, on_update):
        self.parent_on_update = on_update
        self.deferred = Deferred()
        self.reset()

    def reset(self):
        d = self.parent_on_update()
        d.addCallback(self.update)

    def update(self, data):
        self.html = '' # render template
        self.json = '' # serialize to json
        old_deferred = self.deferred
        self.deferred = Deferred()
        old_deferred.callback(data)
        self.reset()

    def on_update(self):
        d = Deferred()
        self.deferred.chainDeferred(d)
        return d


class StatusUpdate(DataObject):
    pass


class StationStatus(DataObject):
    pass


class StationList(DataObject):
    def update(self, parent_data):
        stations=parent_data['InstanceStatus']['stations']
        data = {'stations': stations.keys()}
        data = {str(self.__class__): data}
        super(Instance, self).update(data)
        return data


class InstanceStatus(DataObject):
    def __init__(self, *args, **kwargs):
        self.stations = dict()
        super(InstanceStatus, self).__init__(*args, **kwargs)

    def update(self, parent_data):
        # This doesn't really follow the observer pattern, but seemed like the
        # most efficient way.
        status = dict()
        updated_stations = parent_data['Aggregator']['updated_stations']
        for station_name, station_status in updated_stations:
            try:
                station = self.stations[station_name]
            except KeyError:
                station = selt.stations[station_name] = Station()
            status.update(station.update(station_status))
        data = dict(status=status)
        data = {str(__class__): data}
        super(Instance, self).update(data)
        return data

    def get_station(self, name):
        try:
            return self.stations[name]
        except KeyError:
            raise UnknownStation(name)


class Instance(DataObject):
    def __init__(self, name):
        self.name = name
        self.stations = {}

        # make orbs
        # make aggregator
        # wire orbs to aggregator

        self.status_update = StatusUpdate(self.on_update)
        self.instance_status = InstanceStatus(self.on_update)
        self.station_list = StationList(self.instance_status.on_update)

    def update(self, updated_stations):
        data = dict()
        data.update(self.instance_status.update(updated_stations))
        data.update(self.station_set.update(updated_stations))
        data['name'] = self.name
        data = {str(__class__): data}
        super(Instance, self).update(data)
        return data

