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

``class_name`` may be the requested type, or may be an ``error`` object;
clients should test this to gracefully handle error conditions.

Error Object
~~~~~~~~~~~~

The error object may be returned by any query.

Example error object: ``{"error": {"msg": "Unknown Station: 'TA_Y22'", "code": 404}}`` 

``msg`` contains a human readable message describing the error.

``code`` contains an error code; codes are drawn from the HTTP specification.

Instance Status
~~~~~~~~~~~~~~~

Immediately returns full instance status in ``instance_status`` object. For
async clients, such as WS, it then sends ``instance_update`` objects as packets
arrive from the orb(s).

Instances
~~~~~~~~~

Immediately returns the which list of named DLMon
instances. This is static at runtime so there's really no reason to query it
more than once.

Station List
~~~~~~~~~~~~

Immediately sends the ``stations`` object, which full station list, the re-sends the station list whenever
it changes.

Notes
-----

.. [*]  It's possible that other older websockets protocols are also supported
 but, seriously, just upgrade your browser.

