"""
VJLive3 OSCQuery — Advanced OSC Discovery & Control

Provides a fully RFC-compliant OSCQuery server with typed address space
and both UDP (OSC) and HTTP (OSCQuery) interfaces.
"""

from vjlive3.osc.address_space import OSCAddressSpace, OSCNode, OSCType
from vjlive3.osc.client import OSCClient
from vjlive3.osc.server import NullOSCServer, OSCServer
from vjlive3.osc.query_server import OSCQueryServer

__all__ = [
    "OSCAddressSpace",
    "OSCNode",
    "OSCType",
    "OSCClient",
    "OSCServer",
    "NullOSCServer",
    "OSCQueryServer",
]
