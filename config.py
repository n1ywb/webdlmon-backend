#!/usr/bin/env python
import sys
#import datetime
from pprint import pprint
#from subprocess import Popen,PIPE
import os
import os.path
import logging

sys.path.append(os.environ['ANTELOPE'] + '/data/python')

from antelope import _stock


DEFAULT_PFNAME = 'pywebdlmonconfig'

DEFAULTS = dict(
        match='.*',
        reject='',
        bind_address='0.0.0.0',
        port=7000,
        root='/data/dlmon',
)


class SourceConfig(object):
    def __init__(self, global_config, source_config_dict):
        self.match = source_config_dict.get('match', global_config.match)
        self.reject = source_config_dict.get('reject', global_config.reject)

    def __repr__(self):
        return '<SourceConfig: match=%s, reject=%s>' % (repr(self.match),
                repr(self.reject))


class Config(object):
    """Global config object.

    Global match and or reject are applied to sources which do not specify
    them.

    properties:
    bind_address = str
    port = int
    root = str
    match = str
    reject = str
    instances = dict(
        instname = dict(
            sourcename: SourceConfig(match=str, reject=str),
            [sourcename2: SourceConfig(match=str, reject=str),]
            ...
        )
    )
    """

    def __init__(self, pfname=DEFAULT_PFNAME):
        r, confpf = _stock._pfread(pfname)
        if r < 0:
            raise Exception("Failed to open configuration parameter file %s." %
                    repr(CONF_PF))
        [self.set_val(k, confpf) for k in DEFAULTS.iterkeys()]
        self.instances={}
        instdict = _stock._pfget(confpf,'instances')
        for instname, instcfg in instdict.iteritems():
            sources = {}
            for srcname, srccfg in instcfg.iteritems():
                srccfg = {} if srccfg == '' else srccfg
                source = SourceConfig(self, srccfg)
                sources[srcname] = source
            self.instances[instname] = sources

    def set_val(self, k, pf):
        v = _stock._pfget(pf,k)
        try:
            v = int(v)
        except (ValueError, TypeError):
            pass
        if v is None:
            v = DEFAULTS[k]
        setattr(self, k, v)

