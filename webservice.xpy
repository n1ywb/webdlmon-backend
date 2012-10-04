import sys
import json
#import datetime
from pprint import pprint
#from subprocess import Popen,PIPE

try:
    from twisted.python import log
    from twisted.internet import reactor, defer
    from twisted.internet.threads import deferToThread
    from twisted.web.resource import Resource
    from twisted.web.server import Site

except Exception,e:
    sys.exit('Error importing Twisted: %s' % e)

#{{{
#def print_(result):
#    print result
#
#def running():
#    "Prints a few dots on stdout while the reactor is running."
#    sys.stdout.write("."); sys.stdout.flush()
#    reactor.callLater(.1, running)
#
#def _stop():
#    print "\nend\n"
#    reactor.stop()
#
#def sleep(sec):
#    "A blocking function magically converted in a non-blocking one."
#    print '\nstart sleep %s\n' % sec
#    time.sleep(sec)
#    print '\nend sleep %s\n' % sec
#    return 
#
#def _deferred():
#    d = deferToThread(sleep,5)
#    d.addCallback(print_)
#    return d
#}}}

class ROOT(Resource):
    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)

    def render(self, request):
        log.msg('Got request: %s' % request)
        args = request.uri.split("/")[1:]
        log.msg('Got args: %s' % args)
        request.setHeader("content-type", "text/html")
        request.setHeader("response-code", 500)
        return json.dumps( "Unknown query type:(%s)" % args )

class dlmon(Resource):
    def __init__(self):
        self.data = {}
        self.json_data_file = 'data.json'
        reactor.callLater(0,self._reload)

    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)

    def _encode_json(self, uri):
        return json.dumps(self.data)
        

    def render(self, request):
        try:
            d = defer.Deferred()
            d.addCallback( self._encode_json )
            d.addCallback( request.write )
            d.addCallback( lambda x: request.finish() )
            reactor.callInThread(d.callback, request)

            log.msg("Done with defer call. now return server.NOT_DONE_YET")

            return server.NOT_DONE_YET

        except Exception,e:
            # Just template... never getting here now
            log.msg('Got request: %s' % request)
            args = request.uri.split("/")[1:]
            log.msg('Got args: %s' % args)
            request.setHeader("content-type", "text/html")
            request.setHeader("response-code", 500)
            return json.dumps( "Unknown query type:(%s)" % args )

    def data(self):
        log.msg('Query for json data.')
        return 

    def _reload(self):
        json_data = open(self.json_data_file)
        self.data = json.load(json_data)
        pprint(self.data)
        json_data.close()
        reactor.callLater(120,self._reload)
        return 

try:
    log.startLogging(sys.stdout)
except Exception,e:
    sys.exit('Problems during log setup. [%s]' % e)

#
# Setup and run server
#
#{{{

try:
    log.msg('Set root site:')
    root = ROOT()
    log.msg('\t\t\t\t\t=> OK')

    log.msg('Append service:')
    log.msg('\t\tdlmon()')
    root.putChild("dlmon", dlmon())
    log.msg('\t\t\t\t\t=> OK')

    log.msg('Build as site object:')
    website = Site( root )
    log.msg('\t\t\t\t\t=> OK')

    log.msg('Setup TCP port:')
    reactor.listenTCP(8880, website)
    log.msg('\t\t\t\t\t=> OK')

    log.msg('Run reactor:')
    reactor.run()
except Exception,e:
    sys.exit('EXIT REACTOR. [%s]' % e)

#}}}
