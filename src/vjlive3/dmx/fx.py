"""DMX FX engine — time-based lighting effects.

Each effect implements a tick(dt) that returns channel overrides for a
set of fixtures. The DMXEngine applies these on top of the base state.

Usage::

    from vjlive3.dmx.fx import ChaseEffect, StrobeEffect, RainbowEffect

    chase = ChaseEffect(fixtures=[fix1, fix2, fix3], speed=2.0)
    chase.tick(dt=0.016)   # drives the fixtures directly

    rainbow = RainbowEffect(fixtures=[fix1, fix2, fix3], speed=0.5)
    rainbow.tick(dt=0.016)
"""
from __future__ import annotations

import math
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from vjlive3.utils.logging import get_logger

if TYPE_CHECKING:
    from vjlive3.dmx.fixture import Fixture

logger = get_logger(__name__)


class DMXEffect(ABC):
    """Abstract base for all DMX time-based effects."""

    def __init__(self, fixtures: list["Fixture"]) -> None:
        self.fixtures = list(fixtures)
        self.enabled  = True
        self._t       = 0.0   # accumulated time

    def tick(self, dt: float) -> None:
        """Advance the effect by dt seconds and write to fixtures."""
        if not self.enabled or not self.fixtures:
            return
        self._t += dt
        self._apply(dt)

    @abstractmethod
    def _apply(self, dt: float) -> None:
        """Effect-specific update — writes to self.fixtures directly."""

    def reset(self) -> None:
        self._t = 0.0


class ChaseEffect(DMXEffect):
    """Sequential dimmer chase across fixtures.

    One fixture at a time lights to `colour`, cycling at `speed` Hz.

    Args:
        fixtures: List of Fixture objects to chase across.
        speed:    Chase speed in fixtures-per-second (e.g. 2.0 = 2/sec).
        colour:   RGB tuple (0-255 each). Default white.
    """

    def __init__(
        self,
        fixtures: list["Fixture"],
        speed:    float = 2.0,
        colour:   tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        super().__init__(fixtures)
        self.speed  = speed
        self.colour = colour

    def _apply(self, dt: float) -> None:
        n = len(self.fixtures)
        if n == 0:
            return
        period = 1.0 / max(0.01, self.speed)
        idx = int(self._t / period) % n
        for i, fix in enumerate(self.fixtures):
            if i == idx:
                fix.set_rgb(*self.colour)
            else:
                fix.blackout()


class StrobeEffect(DMXEffect):
    """Timed strobe across all fixtures.

    Args:
        fixtures: Fixtures to strobe.
        rate_hz:  Flashes per second (e.g. 10.0).
        colour:   RGB colour of the flash. Default white.
    """

    def __init__(
        self,
        fixtures: list["Fixture"],
        rate_hz:  float = 10.0,
        colour:   tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        super().__init__(fixtures)
        self.rate_hz = rate_hz
        self.colour  = colour

    def _apply(self, dt: float) -> None:
        period = 1.0 / max(0.1, self.rate_hz)
        phase  = self._t % period
        on     = phase < period * 0.5
        for fix in self.fixtures:
            if on:
                fix.set_rgb(*self.colour)
            else:
                fix.blackout()


class RainbowEffect(DMXEffect):
    """HSV rainbow cycle spread across fixtures.

    Each fixture gets a different hue offset so all colours are visible
    simultaneously when multiple fixtures are used.

    Args:
        fixtures: Fixtures in the rainbow.
        speed:    Hue rotation speed in full cycles per second.
        saturation: Colour saturation (0.0-1.0).
    """

    def __init__(
        self,
        fixtures:   list["Fixture"],
        speed:      float = 0.2,
        saturation: float = 1.0,
    ) -> None:
        super().__init__(fixtures)
        self.speed      = speed
        self.saturation = saturation

    def _apply(self, dt: float) -> None:
        n = max(1, len(self.fixtures))
        base_hue = (self._t * self.speed) % 1.0
        for i, fix in enumerate(self.fixtures):
            hue = (base_hue + i / n) % 1.0
            fix.set_rgb_from_hsv(hue, self.saturation, 1.0)


class FadeEffect(DMXEffect):
    """Smooth intensity fade to a target value over `duration` seconds.

    After reaching target the effect is marked complete (enabled=False).

    Args:
        fixtures: Fixtures to fade.
        target:   Target intensity 0-255.
        duration: Fade duration in seconds.
        start:    Starting intensity (default 0).
    """

    def __init__(
        self,
        fixtures: list["Fixture"],
        target:   int   = 255,
        duration: float = 1.0,
        start:    int   = 0,
    ) -> None:
        super().__init__(fixtures)
        self.target   = target
        self.duration = max(0.001, duration)
        self.start    = start

    def _apply(self, dt: float) -> None:
        progress = min(1.0, self._t / self.duration)
        value    = int(self.start + (self.target - self.start) * progress)
        for fix in self.fixtures:
            fix.set_dim(value)
        if progress >= 1.0:
            self.enabled = False
