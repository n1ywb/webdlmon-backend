#!/usr/bin/env python
"""
Configuration reading module.

Supports reading configuration from a prameter file and marshalling those data
into useful objects which the application can use.
"""

import sys
import os

from mako.lookup import TemplateLookup

sys.path.append(os.environ['ANTELOPE'] + '/data/python')

from antelope import stock


DEFAULTS = dict(
        match='.*',
        reject='',
        bind_address='0.0.0.0',
        port=7000,
        root='/data/dlmon',
)


class SourceConfig(object):
    """Represents a data source, usually an orb.

    match = match string, always populated
    reject = reject string, always populated
    """

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

    def __init__(self, options):
        confpf = stock.pfread(options.parameter_file)
        [self.set_val(k, confpf, options) for k in DEFAULTS.iterkeys()]
        self.instances={}
        instdict = confpf['instances']
        for instname, instcfg in instdict.iteritems():
            sources = {}
            for srcname, srccfg in instcfg.iteritems():
                srccfg = {} if srccfg == '' else srccfg
                source = SourceConfig(self, srccfg)
                sources[srcname] = source
            self.instances[instname] = sources
        self.templates = TemplateLookup(directories=['templates'])



    def set_val(self, k, pf, options=None):
        """Sets the attribute 'k'.

        Look first in options, then in pf.

        Always converts type to int if at all possible, which is kludgy, but
        acceptable at the moment.
        """
        v = None
        if options is not None:
            try:
                v = getattr(options, k)
            except AttributeError:
                pass
        if v is None:
            v = pf.get(k, DEFAULTS[k])
        try:
            v = int(v)
        except (ValueError, TypeError):
            pass
        setattr(self, k, v)

