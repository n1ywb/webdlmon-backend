from webbase import Base as WebBase

class Base(WebBase):
    # do something to automate templating; override render or something
    pass


class Root(Base):
    pass


class InstanceList(Base):
    pass


class Instance(Base):
    pass


class InstanceStatus(Base):
    pass


class StationList(Base):
    pass


class Station(Base):
    pass


class StationStatus(Base):
    pass


class StationWaveforms(Base):
    pass

