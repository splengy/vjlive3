"""Audio-reactive DMX bridge.

Wires `ReactivityBus` audio snapshots to DMX fixture parameters.
Mapping rules are registered via `map()` and evaluated on every
`tick(snapshot)` call.

Usage::

    from vjlive3.dmx.audio_reactive import AudioDMXBridge

    bridge = AudioDMXBridge()
    bridge.map("rms",  "spot_1", mode="dim",   scale=255.0)
    bridge.map("bass", "wash_1", mode="red",   scale=200.0)
    bridge.map("beat", "strobe", mode="flash",  scale=255.0)

    # In the main loop:
    snapshot = reactivity_bus.snapshot()
    bridge.tick(snapshot, fixture_registry)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from vjlive3.utils.logging import get_logger

if TYPE_CHECKING:
    from vjlive3.dmx.fixture import Fixture

logger = get_logger(__name__)

# Supported audio features from AudioSnapshot
_AUDIO_FEATURES = {"rms", "bass", "mids", "highs", "beat", "bpm", "onset_strength"}

# Write modes applied to fixtures
_MODES = {"dim", "red", "green", "blue", "rgb_uniform", "flash"}


@dataclass
class AudioMapping:
    """A single audio-feature → fixture parameter mapping.

    Attributes:
        id:           Unique mapping id
        feature:      AudioSnapshot field name (rms, bass, beat, …)
        fixture_name: Target fixture name in the registry
        mode:         How to apply the value (dim, red, green, blue, flash, rgb_uniform)
        scale:        Multiply audio value by this before applying (default 255.0)
        offset:       Add this after scaling (default 0.0)
    """
    feature:      str
    fixture_name: str
    mode:         str   = "dim"
    scale:        float = 255.0
    offset:       float = 0.0
    id:           str   = field(default_factory=lambda: str(uuid.uuid4())[:8])


class AudioDMXBridge:
    """Maps audio snapshot values to DMX fixture parameters.

    Thread-safe for tick() calls from the audio thread, while mappings
    are added from the control thread.
    """

    def __init__(self) -> None:
        self._mappings: dict[str, AudioMapping] = {}

    # ------------------------------------------------------------------ #
    #  Mapping management                                                  #
    # ------------------------------------------------------------------ #

    def map(
        self,
        feature:      str,
        fixture_name: str,
        mode:         str   = "dim",
        scale:        float = 255.0,
        offset:       float = 0.0,
    ) -> str:
        """Register an audio → DMX mapping.

        Args:
            feature:      Audio snapshot field (rms/bass/mids/highs/beat/bpm/onset_strength)
            fixture_name: Name of the target fixture in the DMXEngine registry
            mode:         Write mode: dim | red | green | blue | rgb_uniform | flash
            scale:        Multiplier applied to the audio value
            offset:       Additive offset after scaling

        Returns:
            The mapping id string (use to remove later).

        Raises:
            ValueError: For unknown feature or mode.
        """
        if feature not in _AUDIO_FEATURES:
            raise ValueError(f"Unknown audio feature: '{feature}'. Valid: {sorted(_AUDIO_FEATURES)}")
        if mode not in _MODES:
            raise ValueError(f"Unknown mode: '{mode}'. Valid: {sorted(_MODES)}")

        mapping = AudioMapping(
            feature=feature, fixture_name=fixture_name,
            mode=mode, scale=scale, offset=offset,
        )
        self._mappings[mapping.id] = mapping
        logger.debug("AudioDMXBridge: mapped %s → %s.%s", feature, fixture_name, mode)
        return mapping.id

    def unmap(self, mapping_id: str) -> bool:
        """Remove a mapping by id."""
        return self._mappings.pop(mapping_id, None) is not None

    def list_mappings(self) -> list[AudioMapping]:
        return list(self._mappings.values())

    # ------------------------------------------------------------------ #
    #  Tick                                                                #
    # ------------------------------------------------------------------ #

    def tick(
        self,
        snapshot: Any,                        # AudioSnapshot
        fixtures: dict[str, "Fixture"],
    ) -> None:
        """Apply all mappings from the audio snapshot to DMX fixtures.

        Args:
            snapshot: An AudioSnapshot from ReactivityBus.snapshot()
            fixtures: dict of fixture_name → Fixture (from DMXEngine)
        """
        for m in self._mappings.values():
            fix = fixtures.get(m.fixture_name)
            if fix is None:
                continue

            raw = getattr(snapshot, m.feature, 0.0)
            # bool (beat) → float
            if isinstance(raw, bool):
                raw = 1.0 if raw else 0.0
            value = max(0, min(255, int(float(raw) * m.scale + m.offset)))

            try:
                if m.mode == "dim":
                    fix.set_dim(value)
                elif m.mode == "red":
                    fix.set_channel(0, value)
                elif m.mode == "green":
                    fix.set_channel(1, value)
                elif m.mode == "blue":
                    fix.set_channel(2, value)
                elif m.mode == "rgb_uniform":
                    fix.set_rgb(value, value, value)
                elif m.mode == "flash":
                    # Beat flash: full on / off based on bool beat
                    is_beat = bool(getattr(snapshot, "beat", False))
                    fix.set_dim(255 if is_beat else 0)
            except Exception as exc:
                logger.debug("AudioDMXBridge apply error (%s.%s): %s", m.fixture_name, m.mode, exc)
