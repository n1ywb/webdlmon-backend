#!/usr/bin/env python

from mako.template import Template
from mako.lookup import TemplateLookup

templates = TemplateLookup(directories=['pywebdlmon'])

from webbase import Base as WebBase

class Base(WebBase):
    # do something to automate templating; override render or something

    def render(self, request):
        mytemplate = templates.get_template('.'.join(self.__class__, 'html'))
        r = str(mytemplate.render(resource=self))
        request.setHeader("content-type", "text/html")
        request.setHeader("response-code", 200)
        return r


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


def get_root(cfg, dlstatuses, whatever):
    # create root
    # add child
    # etc
    return root

