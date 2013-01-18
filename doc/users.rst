Users Guide
===========

This documentation is intended for developers building services on top of the
webdlmon-backend web services.

The backend provides a number of data resources. The underlying mechanics are
uniform accross data resources, and as such they all support similar
functionality.


Data Formats
------------

All resources are available in both JSON and HTML format. The HTML format is
intended primarily as a mechanism to ease development; it's basically just a
pretty-printed dump of the JSON data. The JSON data is what most developers
will use for their applications.

Format is specified by the file extension on the URL; e.g. ``.json`` or
``.html``.


Access Methods
--------------

All resources are available via both HTTP and RFC6455 [*]_ WebSockets.

Access method is denoted by both the URL protocol specifier and in the path.
The path component is intended to support future HTTP-based methods.

WebSockets URL:
ws://anfwebapi.ucsd.edu/ws/dlmon/instances/dlmon/status.json

HTTP URL:
http://anfwebapi.ucsd.edu/http/dlmon/instances/dlmon/status.json

If you mix up the ws and http bits, the result is undefined.


JSON Object Reference
---------------------

All json objects follow this pattern:

``{"class_name": { ... }}``

``class_name`` indicates the type of object which was returned.


Error Handling
~~~~~~~~~~~~~~

Queries may return an object(s) of the requested type(s) or may return an error
object. Clients should test if class_name == ``error``.

As a defensive measure, clients may optionally verify that the received
class_name matches the resource they requested. A mismatch would indicate a bug
in the server, and is thus (hopefully) unlikely.

.. js:data:: error
  Returned when an error has occured.

.. js:attribute:: error.msg
  Human readable string describing the error.

.. js:attribute:: error.code
  Integer error code; codes are drawn from the HTTP specification. 

Example::

  { "error": { "msg": "Unknown Station: 'TA_Y22'", 
               "code": 404 }}


Instance Status
~~~~~~~~~~~~~~~

Immediately returns full instance status in ``instance_status`` object. For
async clients, such as WS, it then sends ``instance_update`` objects as packets
arrive from the orb(s).

Station Status
~~~~~~~~~~~~~~

Very similar to the Instance Status object, except returns data for only the specified station.

.. js:data:: station_status

  Status data for a single station.

.. js:attribute:: station_status.name

  The name of the station. It should match the name of the requested station,
  and clients may verify this.

.. js:attribute:: station_status.timestamp

  The timestamp from the orb packet header. UTC seconds since UNIX epoch.

.. js:attribute:: station_status.values

  Contains the actual status data fields. For details, refer to the
  documentation for the particular datalogger to orb program, e.g. q3302orb.

Example::

    {
        "station_status": {
            "name": "TA_Y22D", 
            "timestamp": 1357929110.673179, 
            "values": {
                "aa": "0.011", 
                "acok": 1, 
                "api": 0, 
                ...
            }
        }
    }

Instances
~~~~~~~~~

Immediately returns the which list of named DLMon
instances. This is static at runtime so there's really no reason to query it
more than once.


Station List
~~~~~~~~~~~~

Immediately sends the ``stations`` object, which full station list, the
re-sends the station list whenever it changes.


Notes
-----

.. [*]  Other older websockets protocols may work but, seriously, upgrade your
 browser.


