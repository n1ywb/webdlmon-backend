from webbase import Base

class Root(Base):
    pass


class InstanceList(Base):
    pass


class Instance(Base):
    pass


class InstanceStatus(Base):
    """A particular named DLMon instance."""

    def __init__(self, name, dlstatus):
        Base.__init__(self)
        self.name = name
        self.dlstatus = dlstatus
        # Monkeypatch dlstatus with my own new-station callback.
        dlstatus.new_stn_cb = self.new_stn

    def new_stn(self, dlstatus, id):
        """Magic new station callback method.

        self.dlstatus calls this method whenever it hears a new station.
        """
        # should probably use a deferred instead of a plain old callback
        # also adding these nodes at all is questionable; might be better to
        # have one concrete node handle requests for virtual station nodes
        log.msg("%s new station %s" % (self.name, id))
        dlmon = DLMonOneStn(dlstatus, id)
        self.putChild(id, dlmon)

    def render(self, request):
        try:
	    request.setHeader("content-type", "application/json")
	    if request.args.has_key('callback'):
		    request.setHeader("content-type", "application/javascript")
		    return request.args['callback'][0] + '(' + self.dlstatus.to_json() + ')'
            return self.dlstatus.to_json()
        except Exception, e:
	    raise


class StationList(Base):
    pass

class Station(Base):
    pass


class StationStatus(Base):
    pass


class StationWaveforms(Base):
    pass


def get_root(cfg, dlstatuses, whatever):
    # create root
    # add child
    # etc
    return root

