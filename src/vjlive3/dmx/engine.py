"""DMX central engine — orchestrates universes, fixtures, effects, output.

Usage::

    from vjlive3.dmx import DMXEngine, FixtureProfile, NullOutput

    engine = DMXEngine(output=NullOutput())
    engine.add_universe(0)
    engine.add_fixture("front_wash", universe_id=0, start_channel=1,
                       profile=FixtureProfile.RGB)
    engine.get_fixture("front_wash").set_rgb(255, 0, 0)

    engine.add_effect(RainbowEffect([engine.get_fixture("front_wash")]))
    engine.tick(dt=0.016)
"""
from __future__ import annotations

import threading
import time
from typing import Any

from vjlive3.dmx.universe import DMXUniverse
from vjlive3.dmx.fixture import Fixture, FixtureProfile
from vjlive3.dmx.output import DMXOutput, NullOutput
from vjlive3.dmx.fx import DMXEffect
from vjlive3.dmx.audio_reactive import AudioDMXBridge
from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_SEND_HZ = 30


class DMXEngine:
    """Central DMX orchestrator.

    Owns universes, fixtures, active effects, and the output backend.
    Call ``tick(dt)`` each frame to drive FX and flush to output.

    Args:
        output:   DMXOutput backend (default NullOutput).
        send_hz:  Target output refresh rate (default 30 Hz).
    """

    def __init__(
        self,
        output:  DMXOutput | None = None,
        send_hz: int               = _DEFAULT_SEND_HZ,
    ) -> None:
        self._output:   DMXOutput           = output or NullOutput()
        self.send_hz:   int                 = send_hz
        self._universes: dict[int, DMXUniverse] = {}
        self._fixtures:  dict[str, Fixture]     = {}
        self._effects:   list[DMXEffect]        = []
        self._bridge:    AudioDMXBridge         = AudioDMXBridge()
        self._lock       = threading.Lock()

        # Background sender thread
        self._running    = False
        self._thread:    threading.Thread | None = None

    # ------------------------------------------------------------------ #
    #  Universe management                                                  #
    # ------------------------------------------------------------------ #

    def add_universe(self, universe_id: int) -> DMXUniverse:
        """Create and register a universe. Returns the new DMXUniverse."""
        if universe_id in self._universes:
            return self._universes[universe_id]
        u = DMXUniverse(universe_id)
        self._universes[universe_id] = u
        logger.info("DMXEngine: added universe %d", universe_id)
        return u

    def get_universe(self, universe_id: int) -> DMXUniverse | None:
        return self._universes.get(universe_id)

    # ------------------------------------------------------------------ #
    #  Fixture management                                                   #
    # ------------------------------------------------------------------ #

    def add_fixture(
        self,
        name:        str,
        universe_id: int,
        start_channel: int,
        profile:     FixtureProfile,
    ) -> Fixture:
        """Register a fixture. Creates universe if it doesn't exist yet.

        Raises:
            ValueError: If a fixture with that name already exists.
        """
        if name in self._fixtures:
            raise ValueError(f"Fixture '{name}' already registered")
        u = self._universes.get(universe_id)
        if u is None:
            u = self.add_universe(universe_id)
        fix = Fixture(name, start_channel, profile, u)
        with self._lock:
            self._fixtures[name] = fix
        logger.info("DMXEngine: fixture '%s' ch%d %s", name, start_channel, profile.value)
        return fix

    def get_fixture(self, name: str) -> Fixture | None:
        return self._fixtures.get(name)

    def list_fixtures(self) -> list[str]:
        return sorted(self._fixtures)

    def fixtures(self) -> dict[str, Fixture]:
        return dict(self._fixtures)

    # ------------------------------------------------------------------ #
    #  FX                                                                  #
    # ------------------------------------------------------------------ #

    def add_effect(self, effect: DMXEffect) -> None:
        """Add a running effect. Effects are ticked each engine tick."""
        with self._lock:
            self._effects.append(effect)

    def remove_effect(self, effect: DMXEffect) -> bool:
        with self._lock:
            try:
                self._effects.remove(effect)
                return True
            except ValueError:
                return False

    def clear_effects(self) -> None:
        with self._lock:
            self._effects.clear()

    # ------------------------------------------------------------------ #
    #  Audio-reactive                                                      #
    # ------------------------------------------------------------------ #

    @property
    def audio_bridge(self) -> AudioDMXBridge:
        """Direct access to the AudioDMXBridge for registering mappings."""
        return self._bridge

    # ------------------------------------------------------------------ #
    #  Tick                                                                #
    # ------------------------------------------------------------------ #

    def tick(self, dt: float = 0.016, audio_snapshot: Any = None) -> None:
        """Advance all active effects and flush universes to output.

        Args:
            dt:             Frame delta time in seconds.
            audio_snapshot: Optional AudioSnapshot from ReactivityBus.
        """
        with self._lock:
            effects = list(self._effects)

        # Run FX
        for fx in effects:
            if fx.enabled:
                fx.tick(dt)

        # Cull finished effects
        with self._lock:
            self._effects = [e for e in self._effects if e.enabled]

        # Apply audio mappings
        if audio_snapshot is not None:
            self._bridge.tick(audio_snapshot, self._fixtures)

        # Flush universes → output
        for uid, u in self._universes.items():
            self._output.send(uid, u.get_frame())

    # ------------------------------------------------------------------ #
    #  Background sender thread                                            #
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """Start background thread that ticks at send_hz."""
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(
            target=self._sender_loop, daemon=True, name="DMXEngine"
        )
        self._thread.start()
        logger.info("DMXEngine started at %d Hz", self.send_hz)

    def stop(self, timeout: float = 2.0) -> None:
        """Stop the background sender thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=timeout)
        self._output.close()
        logger.info("DMXEngine stopped")

    def _sender_loop(self) -> None:
        interval  = 1.0 / self.send_hz
        last_time = time.perf_counter()
        while self._running:
            now = time.perf_counter()
            dt  = now - last_time
            last_time = now
            self.tick(dt=dt)
            elapsed = time.perf_counter() - now
            sleep_t = max(0.0, interval - elapsed)
            time.sleep(sleep_t)

    # ------------------------------------------------------------------ #
    #  Utility                                                             #
    # ------------------------------------------------------------------ #

    def blackout_all(self) -> None:
        """Zero all channels in all fixtures and universes."""
        for fix in self._fixtures.values():
            fix.blackout()
        for uid, u in self._universes.items():
            self._output.send(uid, u.get_frame())

    def __repr__(self) -> str:
        return (
            f"<DMXEngine universes={len(self._universes)} "
            f"fixtures={len(self._fixtures)} effects={len(self._effects)}>"
        )
