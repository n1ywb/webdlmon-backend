Developers Guide
================

This documentation is intended for developers who wish to improve or extend the
webdlmon-backend itself.


Adding A New Data Resource
--------------------------

Adding a new data resource always involves adding a new request handler to
controller.py, and may require modifications to model.py, or the addition of a
new model.

Request Handlers
~~~~~~~~~~~~~~~~

Request handlers live in the controller.Controller class. This is a singleton;
IE exactly one instance of Controller is created by the application.

Handlers take a request object and various other arguments parsed from the URL
path. Standard arguments are documented below.

Handlers must return a deferred, which when fired must send a string to it's
callback with the data to be written to the transport. It's perfectly valid for
the deferred to have been fired prior to being returned; this case the data is
written to the transport immediately.

Handlers may be called an arbitrary number of times with the same request
object to facilitate streaming data e.g. on WebSockets. 

Handler Arguments
'''''''''''''''''

``request``: All handlers get a request object. For streaming connections, the
handler is called repeatedly with the same request object. The request.repeat
flag is set to False on the first request and True for subsequent requests.
The handler my query this flag and return different data on the first request.
This facilitiates the pattern of sending a full data set immediately upon
connection, followed by deltas only.

``transport``: All handlers get a transport string. This argument is parsed
from the URL path. 

``format``: All handlers get a format string. Currently allowed values are
``json`` and ``html``. In all existing handlers, this argument is used to look
up pre-rendered data from the model, although conceivable a future handler
might use this argument to render json, html, or some other format on the fly.

Other arguments: Handlers may accept arbitrary arguments parsed from the URL
path. ``instance`` and ``stations`` are common. Please refer to the Python
Routes documentation for details on url to handler mapping.

URL to Handler Mapping
''''''''''''''''''''''

The get_dispatcher function in controller.py is responsible for connecting
handlers to URLs using txroutes, a Twisted adapter for the Routes packages.

Model Objects
-------------

Model objects may be implemented in any fashion; there really are no constraints on the exact details of how handlers should retrieve data from their models. 

However, this application currently ships with various DLMon related objects in
model.py. These all follow a common pattern, which is documented here.

All current model objects have an ObservableDict instance in their .data
member. ObservableDict is part of the kudu project; refer to the kudu
documentation for the full details. However I will describe it briefly here.

ObservableDict is a subclass of dict, with added functionality for returning Twisted Deferred objects. When requesting a deferred, the user my specify that the deferred should be fired immediately, calling back with the current value stored at the specified key. Alternatively the user may request that the deferred fire when the value at the specified key changes, calling back with the new value.

The DLMon model listens to one or more Orb objects for new status packets. As
packets arrive they are distributed to the various model objects by passing to
the update method. 

The update method is responsible for transforming the update data into an end
data product, in the form of a JSON-serializable dict.  The DataObject
superclass update method serializes this dict to a JSON string and stores it in
it's data['json'] member. The method also renders the appropriate HTML
template, passing in the serializable dict; the template may take arbitrary
action but must return a string which is then stored in data['html'].

Design Discussion
-----------------

This application primarily receives datalogger status packets from Antelope
orbs and transforms those data into web-friendly data products and makes them
available to both synchronous clients and asynchronous streaming clients. 

When designing this application, my initial approach was similar to most other
web applications; render data into strings in response to client requests.

This design has the advantage that data products are only rendered when they
are actually being used, avoiding rendering a bunch of data that nobody is
using at a point in time. This should have good average-case performance when
the volume of incoming data is large and the number of clients is small.  When
the inverse is true, however, the worst case performance could be quite bad.

One important difference from other web apps is that the data served up is NOT
dynamic. It's not like a blog app or something where every request pulls some
data from a database and dynamically renders a template with it; regardless of
when the data is rendered, all users requesting a particular resource see the
same data, until the next packet arrives from the orb. Thus rendering data in
response to queries is wasteful when multiple users request the same resource.

The obvious solution is to implement some sort of cacheing scheme; render the
data on the first request, cache it for subsequent requests, and flush it when
new data arrives from the orb. This scheme would certainly work although it
adds an awful lot of complexity to the application. Caching is notoriously
difficult to get right. Add in the fact that some of our connections are
long-lived and streaming live data and things go downhill fast.

The other disadvantage to this approach is the fact that the model is taking
some action on the data in response to packets off the orb ANYWAY, typically
performing some processing and then storing it in objects until requested by a
handler.

The superior approach in this application is to render data products all the
way to transport-writeable strings in response to packets from the orb. It's
simple for the model to do and no caching is required. It also simplifies the
handler code; all it must do is lookup a string-returning deferred from
somewhere. This approach is much less complex and requires substanially fewer
lines of code.

The performance characteristics of this approach differ slightly. The load to
render the data is relative to the volume of incoming data, which is roughly
constant over periods of days and weeks. So even with zero clients the server
is rendering everything all the time, and this may be seen as wasteful.  In
practice, the load this puts on the server is negligable. While it would be
possible to implement some sort of scheme for only rendering data when clients
are acively requesting it, that would be a premature optimization.

Performance of pre-rendering relative to the number of clients should be
similar to the caching solution described previously. Again in practice, in a
heavily used system with many clients, the rendering load will be negligable
compared to the request handling load.


