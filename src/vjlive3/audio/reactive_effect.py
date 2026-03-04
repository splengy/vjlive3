"""
P1-A3 — Audio-Reactive Effect Framework
Spec: docs/specs/_02_fleshed_out/P1-A3_audio_reactive_framework.md
Tier: 🖥️ Pro-Tier Native

Classes:
  AudioReactiveEffect  — mixin for effects that respond to audio data
  AudioEffectBus       — fan-out registry: analyzer → N effects per frame
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

from vjlive3.audio.features import AudioFeatures
from vjlive3.audio.analyzer import AudioAnalyzer, DummyAudioAnalyzer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# AudioReactiveEffect — Mixin
# ---------------------------------------------------------------------------

class AudioReactiveEffect:
    """
    Mixin that any Effect can inherit to receive audio features per frame.
    Spec: P1-A3 — AudioReactiveEffect protocol.

    Usage:
        class MyEffect(SomeBase, AudioReactiveEffect):
            def __init__(self):
                AudioReactiveEffect.__init__(self)
    """

    def __init__(self) -> None:
        self._audio_sensitivity: float = 1.0
        self._last_features: Optional[AudioFeatures] = None

    # ---- Protocol methods -----------------------------------------------

    def on_audio_features(self, features: AudioFeatures) -> None:
        """
        Called by AudioEffectBus once per frame with the latest audio data.
        Override to react; call super() to retain the features reference.
        """
        self._last_features = features

    def get_audio_params(self) -> Dict[str, Any]:
        """
        Return current audio parameters scaled by sensitivity.
        Returns safe defaults if no audio data has been received.
        """
        if self._last_features is None:
            return {
                "bass": 0.0,
                "mid": 0.0,
                "high": 0.0,
                "volume": 0.0,
                "beat": False,
                "bpm": 120.0,
                "beat_phase": 0.0,
            }
        s = self._audio_sensitivity
        f = self._last_features
        return {
            "bass": f.bass_smooth * s,
            "mid": f.mid_smooth * s,
            "high": f.high_smooth * s,
            "volume": f.volume_smooth * s,
            "beat": f.beat,
            "bpm": f.bpm,
            "beat_phase": f.beat_phase,
        }

    def set_audio_sensitivity(self, sensitivity: float) -> None:
        """Adjust how strongly audio features influence effect parameters."""
        self._audio_sensitivity = max(0.0, float(sensitivity))

    def get_audio_sensitivity(self) -> float:
        return self._audio_sensitivity


# ---------------------------------------------------------------------------
# AudioEffectBus
# ---------------------------------------------------------------------------

class AudioEffectBus:
    """
    Fan-out registry that connects one AudioAnalyzer to N registered effects.

    Per-frame sequence (driven by EffectChain.render(audio_reactor=bus)):
      1. bus.process_frame() → pull AudioFeatures from analyzer
      2. Invoke on_audio_features() on every registered effect
      3. EffectChain can also call bus.get_energy() / get_band() for
         AudioReactor-compatible API usage.

    Falls back to DummyAudioAnalyzer when no real device is provided.
    """

    METADATA: dict = {"spec": "P1-A3", "tier": "Pro-Tier Native"}

    def __init__(self, analyzer: Optional[AudioAnalyzer] = None) -> None:
        self._analyzer: AudioAnalyzer = analyzer or DummyAudioAnalyzer()
        self._effects: List[Any] = []
        self._lock = threading.RLock()
        self._frame_count: int = 0
        self._last_features: AudioFeatures = AudioFeatures.zero()
        self._last_frame_ms: float = 0.0

    # ---- Effect registration --------------------------------------------

    def register(self, effect: Any) -> None:
        """Register an effect to receive audio data each frame."""
        with self._lock:
            if effect not in self._effects:
                self._effects.append(effect)
                logger.debug("AudioEffectBus: registered %r", effect)

    def unregister(self, effect: Any) -> None:
        """Unregister an effect from the bus."""
        with self._lock:
            if effect in self._effects:
                self._effects.remove(effect)
                logger.debug("AudioEffectBus: unregistered %r", effect)

    # ---- Per-frame dispatch ---------------------------------------------

    def process_frame(self) -> AudioFeatures:
        """
        Pull latest AudioFeatures and distribute to all registered effects.
        Should be called once per render frame. Returns the features used.
        <1ms overhead target per spec P1-A3.
        """
        t0 = time.monotonic()

        features = self._analyzer.get_latest_features()
        self._last_features = features

        with self._lock:
            effects = list(self._effects)

        for effect in effects:
            if hasattr(effect, "on_audio_features"):
                try:
                    effect.on_audio_features(features)
                except Exception as exc:
                    logger.debug("AudioEffectBus: on_audio_features error on %r: %s", effect, exc)

        self._frame_count += 1
        self._last_frame_ms = (time.monotonic() - t0) * 1000.0
        return features

    # ---- AudioReactor-compatible API (used by EffectChain.render) -------

    def get_latest_features(self) -> AudioFeatures:
        return self._last_features

    def get_energy(self) -> float:
        """Overall volume — AudioReactor-compatible."""
        return self._last_features.volume_smooth

    def get_band(self, band: str = "bass") -> float:
        """Band energy by name — AudioReactor-compatible."""
        mapping = {"bass": "bass_smooth", "mid": "mid_smooth", "high": "high_smooth"}
        return float(getattr(self._last_features, mapping.get(band, band), 0.0))

    def get_feature(self, name: str, default: float = 0.0) -> float:
        """Named feature accessor — AudioReactor-compatible."""
        return float(getattr(self._last_features, name, default))

    # ---- Configuration / introspection ----------------------------------

    def set_analyzer(self, analyzer: AudioAnalyzer) -> None:
        """Hot-swap the audio analyzer (e.g., to switch input device)."""
        self._analyzer = analyzer

    @property
    def effect_count(self) -> int:
        with self._lock:
            return len(self._effects)

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def last_frame_ms(self) -> float:
        """Processing time of the last frame in milliseconds."""
        return self._last_frame_ms
