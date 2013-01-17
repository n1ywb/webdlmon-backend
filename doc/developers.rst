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

When designing this application, my initial approach was similar to most other
web applications; render data into strings in response to client requests.

This design has the advantage that data products are only rendered when they
are actually being used, avoiding rendering a bunch of data that nobody is
using at a point in time. This probably has good average-case performance when
the volume of incoming data is large and the number of clients is small.
However when the inverse is true, the worst case performance could be quite
bad.

One important difference from other web apps is that the data served up is NOT
dynamic; regardless of when the data is rendered, all users requesting a
particular resource see the same data. Thus rendering data in response to
queries seems wasteful whenever multiple users are requesting the same
resource.

The obvious solution to the performance issue is some sort of cacheing scheme;
render the data on the first request, cache it for subsequent requests, and
flush it when new data arrives from the orb. This scheme would certainly work
although it adds an awful lot of complexity to the application. Caching is
notoriously difficult to get right. 

The other less traditional approach is to render data products to strings in
response to packets from the orb rather than client requests. This approach is
much simpler; no caching layer is required. It also simplifies the handler
code, since by the time the handler executes all it has to do is lookup a
string from somewhere; it need not be bothered with rendering anything. This
approach requires substanially fewer lines of code.

The performance characteristics of this approach differ slightly. The load to
render the data is relative to the volume of incoming data, which is
roughly constant over periods of days and weeks. So even with zero clients the
server is rendering everything all the time, and this may be seen as wasteful.
In practice, the load this puts on the server is negligable, therefor doing
anything to improve it would be a premature optimization.

Performance relative to the number of clients should be similar to the caching
solution described previously. Again in practice, in a heavily used system with
many clients, the rendering load will be negligable compared to the request
handling load.

