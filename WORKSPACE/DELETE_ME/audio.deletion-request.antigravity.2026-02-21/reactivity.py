"""P1-A3 — Audio-Reactive Effect Framework (ReactivityBus)

Bridges audio analysis (P1-A1 AudioFrame) to visual effect parameters.
Manages bindings: {layer → {param → (feature, range, smoothing)}}, applies
frame-rate-independent EMA smoothing, maps 0-1 audio values to [min, max]
parameter ranges, and returns modulated values in a thread-safe manner.

Spec: docs/specs/P1-A3_reactivity_bus.md
Dependencies: P1-A1 (AudioFrame), stdlib only
"""
from __future__ import annotations

import logging
import math
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from vjlive3.audio.analyzer import AudioFrame

_log = logging.getLogger(__name__)


# ── AudioFeature enum ─────────────────────────────────────────────────────────

class AudioFeature(str, Enum):
    """Audio features that can be bound to parameters."""
    BASS          = "bass"
    MID           = "mid"
    HIGH          = "high"
    RMS           = "rms"
    PEAK          = "peak"
    SPECTRAL_FLUX = "spectral_flux"
    # Beat features (provided as 0-or-1 / 0-1 valued fields in AudioFrame;
    # ReactivityBus reads them gracefully — if AudioFrame doesn't have beat
    # attributes yet it returns 0.0 safely via getattr)
    BEAT          = "beat"
    BEAT_PHASE    = "beat_phase"
    # Spectrum energy in arbitrary Hz band — specified via SpectrumBandFeature
    SPECTRUM_BAND = "spectrum_band"


# ── Binding data ──────────────────────────────────────────────────────────────

@dataclass
class Binding:
    """One audio→parameter binding record (internal)."""
    feature:       AudioFeature
    min_val:       float
    max_val:       float
    smoothing:     float          # 0.0 = no smooth, 1.0 = frozen
    # Spectrum band (Hz) — only used when feature == SPECTRUM_BAND
    band_lo:       float = 0.0
    band_hi:       float = 0.0
    # Runtime state
    _smoothed:     float = field(default=0.0, init=False, repr=False)
    _initialized:  bool  = field(default=False, init=False, repr=False)

    def smoothing_coeff(self, dt: float) -> float:
        """Frame-rate-independent smoothing coefficient.

        Converts the per-frame α into a dt-based α so smoothing feels the
        same regardless of FPS.  Uses the formula:
            alpha_dt = 1 - (1 - alpha_60) ^ (dt * 60)
        where alpha_60 is the smoothing constant calibrated at 60 fps.
        """
        if self.smoothing <= 0.0:
            return 1.0             # no smoothing → full snap
        if self.smoothing >= 1.0:
            return 0.0             # effectively frozen
        alpha_60 = 1.0 - self.smoothing
        exponent = dt * 60.0
        return 1.0 - math.pow(max(self.smoothing, 1e-9), exponent)


# ── BindingKey ────────────────────────────────────────────────────────────────

BindingKey = Tuple[str, str]   # (layer_id, param_name)


# ── ReactivityBus ─────────────────────────────────────────────────────────────

class ReactivityBus:
    """Thread-safe audio-to-parameter routing bus.

    Usage::

        bus = ReactivityBus()
        bus.bind("layer_fx", "intensity",
                 AudioFeature.BASS, min_val=0.0, max_val=1.0, smoothing=0.3)
        # each render frame:
        bus.tick(analyzer.get_frame(), dt=0.016)
        val = bus.get("layer_fx", "intensity", base_value=0.5)

    The bus does NOT own the AudioAnalyzer — it only reads the AudioFrame
    snapshot provided via tick().
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # {(layer_id, param_name): Binding}
        self._bindings: Dict[BindingKey, Binding] = {}
        # Last frame used for spectrum band calculations
        self._last_frame: Optional[AudioFrame] = None

    # ── Binding management ────────────────────────────────────────────────────

    def bind(
        self,
        layer_id: str,
        param_name: str,
        feature: AudioFeature,
        min_val: float = 0.0,
        max_val: float = 1.0,
        smoothing: float = 0.0,
        *,
        band_lo: float = 0.0,
        band_hi: float = 0.0,
    ) -> None:
        """Create or replace a binding.

        Args:
            layer_id:   Logical layer identifier (e.g. "blur_fx", "layer_0").
            param_name: Parameter name on that layer (e.g. "intensity").
            feature:    AudioFeature enum value.
            min_val:    Output range minimum (mapped from feature value 0.0).
            max_val:    Output range maximum (mapped from feature value 1.0).
            smoothing:  0.0 = instant snap; 0.9 = very slow follow.
                        Frame-rate-independent EMA is applied internally.
            band_lo:    Lower Hz bound for SPECTRUM_BAND feature.
            band_hi:    Upper Hz bound for SPECTRUM_BAND feature.

        Raises:
            ValueError: If layer_id or param_name is empty.
            ValueError: If smoothing not in [0, 1].
        """
        if not layer_id:
            raise ValueError("layer_id must be non-empty")
        if not param_name:
            raise ValueError("param_name must be non-empty")
        if not 0.0 <= smoothing <= 1.0:
            raise ValueError(f"smoothing must be in [0, 1], got {smoothing}")

        binding = Binding(
            feature=feature,
            min_val=min_val,
            max_val=max_val,
            smoothing=smoothing,
            band_lo=band_lo,
            band_hi=band_hi,
        )
        with self._lock:
            self._bindings[(layer_id, param_name)] = binding
        _log.debug("Bound %s.%s → %s [%.2f, %.2f] smooth=%.2f",
                    layer_id, param_name, feature.value, min_val, max_val, smoothing)

    def unbind(self, layer_id: str, param_name: str) -> bool:
        """Remove a binding.

        Returns:
            True if the binding existed and was removed, False otherwise.
        """
        key: BindingKey = (layer_id, param_name)
        with self._lock:
            if key in self._bindings:
                del self._bindings[key]
                return True
        return False

    def unbind_layer(self, layer_id: str) -> int:
        """Remove all bindings for a given layer.

        Returns:
            Number of bindings removed.
        """
        with self._lock:
            keys_to_remove = [k for k in self._bindings if k[0] == layer_id]
            for k in keys_to_remove:
                del self._bindings[k]
        return len(keys_to_remove)

    def clear(self) -> None:
        """Remove all bindings and reset smoothing state."""
        with self._lock:
            self._bindings.clear()

    def has_binding(self, layer_id: str, param_name: str) -> bool:
        """Return True if a binding exists for a layer/param pair."""
        with self._lock:
            return (layer_id, param_name) in self._bindings

    def list_bindings(self) -> List[Dict]:
        """Return a snapshot of all bindings as plain dicts (for inspection/UI)."""
        with self._lock:
            return [
                {
                    "layer_id":   k[0],
                    "param_name": k[1],
                    "feature":    b.feature.value,
                    "min_val":    b.min_val,
                    "max_val":    b.max_val,
                    "smoothing":  b.smoothing,
                    "band_lo":    b.band_lo,
                    "band_hi":    b.band_hi,
                }
                for k, b in self._bindings.items()
            ]

    # ── Tick (called once per render frame) ───────────────────────────────────

    def tick(self, frame: AudioFrame, dt: float) -> None:
        """Update all smoothed binding values from a new AudioFrame.

        Must be called once per render frame before reading values via get().
        Thread-safe — multiple non-overlapping threads may call tick() as long
        as only one calls it at a time per frame (render loop convention).

        Args:
            frame:  Latest AudioFrame from P1-A1 AudioAnalyzer.
            dt:     Elapsed seconds since last frame (e.g. 0.016 at 60 fps).
        """
        if dt <= 0.0:
            dt = 1.0 / 60.0  # guard against zero/negative dt

        with self._lock:
            self._last_frame = frame
            for binding in self._bindings.values():
                raw = self._extract(frame, binding)
                alpha = binding.smoothing_coeff(dt)
                if not binding._initialized:
                    binding._smoothed = raw
                    binding._initialized = True
                else:
                    binding._smoothed = binding._smoothed + alpha * (raw - binding._smoothed)

    # ── Get modulated value ───────────────────────────────────────────────────

    def get(
        self,
        layer_id: str,
        param_name: str,
        base_value: float = 0.0,
    ) -> float:
        """Return the modulated parameter value.

        If no binding exists, returns base_value unchanged.
        Call after tick() — returns the last-smoothed value mapped to [min, max].

        Args:
            layer_id:    Layer identifier.
            param_name:  Parameter name.
            base_value:  Value returned if no binding registered (pass-through).

        Returns:
            Float in the binding's [min_val, max_val] range, or base_value.
        """
        key: BindingKey = (layer_id, param_name)
        with self._lock:
            binding = self._bindings.get(key)
            if binding is None:
                return base_value
            # Map smoothed [0, 1] to [min_val, max_val]
            t = max(0.0, min(1.0, binding._smoothed))
            return binding.min_val + t * (binding.max_val - binding.min_val)

    def get_raw(self, layer_id: str, param_name: str) -> Optional[float]:
        """Return the raw (un-mapped) smoothed audio value in [0, 1].

        Useful for visualisation or downstream processing.
        Returns None if no binding exists.
        """
        key: BindingKey = (layer_id, param_name)
        with self._lock:
            binding = self._bindings.get(key)
            if binding is None:
                return None
            return max(0.0, min(1.0, binding._smoothed))

    # ── Feature extraction ────────────────────────────────────────────────────

    def _extract(self, frame: AudioFrame, binding: Binding) -> float:
        """Extract the raw [0,1] feature value from an AudioFrame."""
        feature = binding.feature

        if feature == AudioFeature.BASS:
            return float(frame.bass)
        elif feature == AudioFeature.MID:
            return float(frame.mid)
        elif feature == AudioFeature.HIGH:
            return float(frame.high)
        elif feature == AudioFeature.RMS:
            return float(frame.rms)
        elif feature == AudioFeature.PEAK:
            return float(frame.peak)
        elif feature == AudioFeature.SPECTRAL_FLUX:
            return float(frame.spectral_flux)
        elif feature == AudioFeature.BEAT:
            # BeatState may or may not be on the frame yet.
            # Read via getattr for forward-compat; return 0.0 if absent.
            return float(getattr(frame, "beat", 0.0))
        elif feature == AudioFeature.BEAT_PHASE:
            return float(getattr(frame, "beat_phase", 0.0))
        elif feature == AudioFeature.SPECTRUM_BAND:
            return self._spectrum_band_energy(frame, binding.band_lo, binding.band_hi)
        else:
            _log.warning("Unknown feature %s — returning 0.0", feature)
            return 0.0

    def _spectrum_band_energy(
        self,
        frame: AudioFrame,
        lo_hz: float,
        hi_hz: float,
    ) -> float:
        """Return mean normalised energy in a custom frequency band.

        The 128-bin spectrum in AudioFrame is treated as log-spaced bins
        from 0 Hz to (sample_rate / 2) Hz, defaulting to 22050 Hz.
        """
        if not frame.spectrum:
            return 0.0

        n_bins = len(frame.spectrum)
        nyquist = 22050.0  # Hz — matches 44100 default sample rate

        lo_idx = int((lo_hz / nyquist) * n_bins)
        hi_idx = int((hi_hz / nyquist) * n_bins)
        lo_idx = max(0, min(lo_idx, n_bins - 1))
        hi_idx = max(lo_idx + 1, min(hi_idx, n_bins))

        band_vals = frame.spectrum[lo_idx:hi_idx]
        if not band_vals:
            return 0.0
        return float(sum(band_vals) / len(band_vals))

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def binding_count(self) -> int:
        """Number of registered bindings."""
        with self._lock:
            return len(self._bindings)

    @property
    def last_frame(self) -> Optional[AudioFrame]:
        """Last AudioFrame passed to tick(), or None if tick() not yet called."""
        with self._lock:
            return self._last_frame


__all__ = [
    "AudioFeature",
    "Binding",
    "ReactivityBus",
]
