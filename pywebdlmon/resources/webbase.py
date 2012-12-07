#!/usr/bin/env python

from twisted.web.resource import Resource


class Base(Resource):
    """Application root."""

    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)


