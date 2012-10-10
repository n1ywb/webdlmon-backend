#!/usr/bin/env python
from pprint import pprint

from ctypes import CDLL, create_string_buffer, string_at
from ctypes import c_bool, c_char, c_wchar, c_byte, c_ubyte, c_short, c_ushort
from ctypes import c_int, c_uint, c_long, c_ulong, c_longlong, c_ulonglong
from ctypes import c_float, c_double, c_longdouble, c_char_p, c_wchar_p
from ctypes import c_void_p, POINTER, pointer, byref

__all__ = ['orbreap_timeout']

ORBSRCNAME_SIZE = 64

liborb = CDLL("liborb.so.3")
liborb.orbreap_timeout.argtypes = [c_int, c_double, POINTER(c_int),
            c_char_p, POINTER(c_double), POINTER(POINTER(c_char)),
            POINTER(c_int)]
liborb.orbreap_timeout.restype = c_int

def orbreap_timeout(orbfd, maxseconds=0.0):
    """pktid, srcname, time, packet, nbytes = orb.orbreap_timeout (orbfd,
    maxseconds)"""

    # int orbreap_timeout(int orbfd, double maxseconds, int *pktid,
    #                     char *srcname, double *pkttime,
    #                     char **pkt, int *nbytes,
    #                     int *bufsize)

    orbfd = orbfd._orbfd
    pktid = c_int()
    pkttime = c_double()
    srcname = create_string_buffer(ORBSRCNAME_SIZE)
    packet = pointer(c_char())
    nbytes = c_int()
    bufsize = c_int(0)
    r = liborb.orbreap_timeout(orbfd, maxseconds, byref(pktid), srcname, byref(pkttime),
                byref(packet), byref(nbytes), byref(bufsize))
    # The stock bindings swallow r; we could return it...
    if r < 0:
        pktid, srcname, pkttime, packet, nbytes = None, None, None, None, None
    else:
        pktid = pktid.value
        srcname = string_at(srcname)
        pkttime = pkttime.value
        packet = string_at(packet, nbytes)
        nbytes = nbytes.value
#    pprint(dict(
#            pktid=pktid,
#            srcname=srcname,
#            pkttime=pkttime,
#            packet=str(packet)[:50],
#            nbytes=nbytes,
#        ))
    return pktid, srcname, pkttime, packet, nbytes

