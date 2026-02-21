"""DMX network output backends.

Provides an abstract DMXOutput base and two concrete implementations:
- NullOutput  — silent sink (testing / hardware absent)
- ArtNetOutput — UDP ArtNet packet sender (no pyartnet required)

ArtNet packet spec: http://www.artisticlicence.com/WebSiteMaster/User%20Guides/art-net.pdf

Usage::

    output = ArtNetOutput(host="192.168.1.100")
    output.send(universe_id=0, frame=universe.get_frame())
    output.close()
"""
from __future__ import annotations

import socket
import struct
from abc import ABC, abstractmethod

from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)

# ArtNet constants
_ARTNET_PORT    = 6454
_ARTNET_ID      = b"Art-Net\x00"
_ARTNET_OPCODE  = 0x5000  # OpDmx
_ARTNET_VERSION = 14


def _build_artnet_packet(universe_id: int, frame: bytes) -> bytes:
    """Build a raw ArtNet OpDmx UDP packet.

    Args:
        universe_id: 0-based universe number (0-32767).
        frame:       512 bytes of DMX data.

    Returns:
        Bytes ready to send via UDP.
    """
    length = len(frame)
    # Pad to 512 if short, but keep even length
    if length < 512:
        frame = frame + bytes(512 - length)

    header = struct.pack(
        "<8sHHBBHH",
        _ARTNET_ID,           # ID
        _ARTNET_OPCODE,       # OpCode (little-endian)
        _ARTNET_VERSION,      # ProtVer (big-endian in spec but many use 14 big)
        0,                    # Sequence (0 = disabled)
        0,                    # Physical
        universe_id & 0x7FFF, # Universe
        512,                  # Length (big-endian)
    )
    return header + frame[:512]


class DMXOutput(ABC):
    """Abstract DMX output backend."""

    @abstractmethod
    def send(self, universe_id: int, frame: bytes) -> None:
        """Send a 512-byte DMX frame for this universe."""

    @abstractmethod
    def close(self) -> None:
        """Release resources."""


class NullOutput(DMXOutput):
    """Discards all DMX data — for testing or hardware-absent environments."""

    def send(self, universe_id: int, frame: bytes) -> None:
        pass  # intentionally silent

    def close(self) -> None:
        pass

    def __repr__(self) -> str:
        return "<NullOutput>"


class ArtNetOutput(DMXOutput):
    """Sends ArtNet UDP packets without requiring pyartnet.

    Args:
        host:      Target IP address (broadcast or unicast).
        port:      UDP port (default 6454).
        broadcast: If True, bind as broadcast socket.
    """

    def __init__(
        self,
        host:      str  = "127.0.0.1",
        port:      int  = _ARTNET_PORT,
        broadcast: bool = False,
    ) -> None:
        self._host      = host
        self._port      = port
        self._broadcast = broadcast
        self._sock: socket.socket | None = None
        self._open()

    def _open(self) -> None:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if self._broadcast:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._sock = s
            logger.info("ArtNetOutput → %s:%d", self._host, self._port)
        except OSError as exc:
            logger.error("ArtNetOutput: socket error: %s — falling back to NullOutput", exc)
            self._sock = None

    def send(self, universe_id: int, frame: bytes) -> None:
        if self._sock is None:
            return
        try:
            packet = _build_artnet_packet(universe_id, frame)
            self._sock.sendto(packet, (self._host, self._port))
        except OSError as exc:
            logger.debug("ArtNetOutput.send error: %s", exc)

    def close(self) -> None:
        if self._sock:
            self._sock.close()
            self._sock = None

    def __repr__(self) -> str:
        return f"<ArtNetOutput {self._host}:{self._port}>"
