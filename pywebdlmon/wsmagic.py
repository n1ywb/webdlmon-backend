###############################################################################
##
## Copyright 2012 Tavendo GmbH
## Copyright 2013 Regents of the University of California, All Rights Reserved
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
## http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##
###############################################################################

from twisted.protocols.policies import ProtocolWrapper


class NoProtocol(Exception): pass


def upgrade(request, factory):
      """
Render the resource. This will takeover the transport underlying
the request, create a WebSocketServerProtocol and let that do
any subsequent communication.
"""

      ## Create Autobahn WebSocket protocol.
      ##
      protocol = factory.buildProtocol(request.transport.getPeer())
      if not protocol:
        raise NoProtocol()

      ## Take over the transport from Twisted Web
      ##
      transport, request.transport = request.transport, None

      ## Connect the transport to our protocol. Once #3204 is fixed, there
      ## may be a cleaner way of doing this.
      ## http://twistedmatrix.com/trac/ticket/3204
      ##
      if isinstance(transport, ProtocolWrapper):
         ## i.e. TLS is a wrapping protocol
         transport.wrappedProtocol = protocol
      else:
         transport.protocol = protocol
      protocol.makeConnection(transport)

      ## We recreate the request and forward the raw data. This is somewhat
      ## silly (since Twisted Web already did the HTTP request parsing
      ## which we will do a 2nd time), but it's totally non-invasive to our
      ## code. Maybe improve this.
      ##
      data = "%s %s HTTP/1.1\x0d\x0a" % (request.method, request.path)
      for h in request.requestHeaders.getAllRawHeaders():
         data += "%s: %s\x0d\x0a" % (h[0], ",".join(h[1]))
      data += "\x0d\x0a"
      data += request.content.read() # we need this for Hixie-76
      protocol.dataReceived(data)

      return protocol

