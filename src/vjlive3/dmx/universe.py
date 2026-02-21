"""DMX512 universe — 512-channel byte buffer.

The universe is the atomic unit of DMX output. Each channel stores a
byte value (0-255). The universe provides thread-safe read/write and
produces output frames as immutable bytes.

Usage::

    u = DMXUniverse(universe_id=0)
    u.set(1, 255)          # Channel 1 = full
    u.set_range(1, [255, 128, 64])  # Ch1=R, Ch2=G, Ch3=B
    frame = u.get_frame()  # →  bytes(512)
"""
from __future__ import annotations

import threading

from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)

DMX_CHANNELS = 512


class DMXUniverse:
    """A 512-channel DMX512 universe.

    Channel numbers are **1-indexed** (as per the DMX512 spec).
    All values are clamped to [0, 255].

    Args:
        universe_id: Integer universe number (0-based, following ArtNet convention).
    """

    def __init__(self, universe_id: int = 0) -> None:
        self.universe_id = universe_id
        self._data = bytearray(DMX_CHANNELS)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    #  Writes                                                              #
    # ------------------------------------------------------------------ #

    def set(self, channel: int, value: int) -> None:
        """Set a single channel value.

        Args:
            channel: 1-indexed DMX channel (1-512).
            value:   Byte value 0-255.

        Raises:
            ValueError: If channel is outside 1-512.
        """
        if not 1 <= channel <= DMX_CHANNELS:
            raise ValueError(f"DMX channel must be 1-512, got {channel}")
        with self._lock:
            self._data[channel - 1] = max(0, min(255, int(value)))

    def set_range(self, start_channel: int, values: list[int]) -> None:
        """Set consecutive channels starting at start_channel.

        Args:
            start_channel: 1-indexed start channel.
            values:        Iterable of byte values (0-255 each).

        Raises:
            ValueError: If the range exceeds 512 channels.
        """
        end = start_channel + len(values) - 1
        if not (1 <= start_channel <= DMX_CHANNELS and end <= DMX_CHANNELS):
            raise ValueError(
                f"Channel range {start_channel}-{end} exceeds 1-512"
            )
        with self._lock:
            for i, v in enumerate(values):
                self._data[start_channel - 1 + i] = max(0, min(255, int(v)))

    def blackout(self) -> None:
        """Set all channels to 0."""
        with self._lock:
            for i in range(DMX_CHANNELS):
                self._data[i] = 0

    # ------------------------------------------------------------------ #
    #  Reads                                                               #
    # ------------------------------------------------------------------ #

    def get(self, channel: int) -> int:
        """Get a single channel value (1-indexed)."""
        if not 1 <= channel <= DMX_CHANNELS:
            raise ValueError(f"DMX channel must be 1-512, got {channel}")
        with self._lock:
            return self._data[channel - 1]

    def get_frame(self) -> bytes:
        """Return an immutable snapshot of all 512 channels.

        Safe to pass to output threads without holding the lock.
        """
        with self._lock:
            return bytes(self._data)

    def __repr__(self) -> str:
        return f"<DMXUniverse id={self.universe_id}>"
