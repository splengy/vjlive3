"""DMX fixture profiles and fixture management.

A Fixture maps logical control (set_rgb, set_dim) to specific DMX
channels in a universe. Profiles define the channel layout.

Usage::

    from vjlive3.dmx.fixture import Fixture, FixtureProfile
    from vjlive3.dmx.universe import DMXUniverse

    u = DMXUniverse(0)
    spot = Fixture("spot_1", start_channel=1, profile=FixtureProfile.RGB, universe=u)
    spot.set_rgb(255, 128, 0)   # orange
    spot.set_dim(200)           # works on DIMMER profile
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from vjlive3.utils.logging import get_logger

if TYPE_CHECKING:
    from vjlive3.dmx.universe import DMXUniverse

logger = get_logger(__name__)


class FixtureProfile(str, Enum):
    """Standard DMX fixture channel layouts.

    Channel counts:
        DIMMER:       1   (intensity)
        RGB:          3   (red, green, blue)
        RGBA:         4   (red, green, blue, amber)
        RGBW:         4   (red, green, blue, white)
        MOVING_HEAD:  8   (pan, tilt, pan-fine, tilt-fine, colour, gobo, dim, strobe)
    """
    DIMMER      = "dimmer"       # 1 ch
    RGB         = "rgb"          # 3 ch
    RGBA        = "rgba"         # 4 ch
    RGBW        = "rgbw"         # 4 ch
    MOVING_HEAD = "moving_head"  # 8 ch


_PROFILE_CHANNELS: dict[FixtureProfile, int] = {
    FixtureProfile.DIMMER:      1,
    FixtureProfile.RGB:         3,
    FixtureProfile.RGBA:        4,
    FixtureProfile.RGBW:        4,
    FixtureProfile.MOVING_HEAD: 8,
}


@dataclass
class FixtureChannel:
    """Metadata for a single fixture channel."""
    index:       int   # 0-based within the fixture
    name:        str   # e.g. "red", "intensity"
    default:     int = 0


class Fixture:
    """A DMX fixture mapped to a universe.

    Args:
        name:          Unique fixture name used as a registry key.
        start_channel: 1-indexed DMX start channel in the universe.
        profile:       FixtureProfile describing channel count and layout.
        universe:      DMXUniverse to write values into.
    """

    def __init__(
        self,
        name:          str,
        start_channel: int,
        profile:       FixtureProfile,
        universe:      "DMXUniverse",
    ) -> None:
        self.name          = name
        self.start_channel = start_channel
        self.profile       = profile
        self.universe      = universe
        self.channel_count = _PROFILE_CHANNELS[profile]
        self._values       = [0] * self.channel_count

        logger.debug(
            "Fixture '%s' → universe %d ch%d-%d (%s)",
            name, universe.universe_id,
            start_channel, start_channel + self.channel_count - 1,
            profile.value,
        )

    # ------------------------------------------------------------------ #
    #  Raw channel access                                                  #
    # ------------------------------------------------------------------ #

    def set_channel(self, index: int, value: int) -> None:
        """Set a channel by 0-based index within this fixture."""
        if not 0 <= index < self.channel_count:
            raise ValueError(
                f"Fixture '{self.name}' has {self.channel_count} channels, "
                f"index {index} out of range"
            )
        v = max(0, min(255, int(value)))
        self._values[index] = v
        self.universe.set(self.start_channel + index, v)

    def get_channel(self, index: int) -> int:
        """Get a channel value by 0-based index."""
        return self._values[index]

    # ------------------------------------------------------------------ #
    #  Profile-aware setters                                               #
    # ------------------------------------------------------------------ #

    def set_dim(self, intensity: int) -> None:
        """Set master intensity (ch 0) — works on all profiles."""
        if self.profile == FixtureProfile.DIMMER:
            self.set_channel(0, intensity)
        elif self.profile == FixtureProfile.MOVING_HEAD:
            self.set_channel(6, intensity)  # dim ch = index 6
        else:
            # RGB/RGBA/RGBW — write intensity directly to all colour channels
            for i in range(self.channel_count):
                self.set_channel(i, intensity)

    def set_rgb(self, r: int, g: int, b: int) -> None:
        """Set RGB channels (RGB/RGBA/RGBW/MOVING_HEAD profiles)."""
        if self.profile == FixtureProfile.DIMMER:
            self.set_channel(0, int(0.299 * r + 0.587 * g + 0.114 * b))  # luminance
            return
        self.set_channel(0, r)
        self.set_channel(1, g)
        self.set_channel(2, b)

    def set_all(self, value: int) -> None:
        """Set all channels to the same value."""
        for i in range(self.channel_count):
            self.set_channel(i, value)

    def blackout(self) -> None:
        """Zero all channels."""
        for i in range(self.channel_count):
            self.set_channel(i, 0)
        # Update internal state
        self._values = [0] * self.channel_count

    def get_values(self) -> list[int]:
        """Return a copy of current channel values."""
        return list(self._values)

    # ------------------------------------------------------------------ #
    #  Utility                                                             #
    # ------------------------------------------------------------------ #

    def set_rgb_from_hsv(self, hue: float, sat: float, val: float) -> None:
        """Set RGB from HSV (all in 0.0-1.0 range)."""
        h = hue % 1.0
        i = int(h * 6)
        f = h * 6 - i
        p = val * (1 - sat)
        q = val * (1 - f * sat)
        t = val * (1 - (1 - f) * sat)
        table = [
            (val, t, p), (q, val, p), (p, val, t),
            (p, q, val), (t, p, val), (val, p, q),
        ]
        r, g, b = table[i % 6]
        self.set_rgb(int(r * 255), int(g * 255), int(b * 255))

    def __repr__(self) -> str:
        return (
            f"<Fixture '{self.name}' ch{self.start_channel} "
            f"{self.profile.value} u{self.universe.universe_id}>"
        )
