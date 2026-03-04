"""
P1-A5 — Audio Reactivity
Spec: docs/specs/_02_fleshed_out/P1-A5_audio_reactivity.md
Tier: 🖥️ Pro-Tier Native

Classes:
  AudioReactivityFeatures — dataclass: band energies, beat, spectral, MFCCs
  ParameterMapper         — scale/offset/clamp mapping from feature → param value
  AudioReactivityManager  — processes raw audio frames → features + mappings
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

_HANN_CACHE: Dict[int, np.ndarray] = {}


def _hann(n: int) -> np.ndarray:
    if n not in _HANN_CACHE:
        _HANN_CACHE[n] = np.hanning(n).astype(np.float32)
    return _HANN_CACHE[n]


# ---------------------------------------------------------------------------
# AudioReactivityFeatures
# ---------------------------------------------------------------------------

@dataclass
class AudioReactivityFeatures:
    """
    Container for audio reactivity analysis output.
    All energies normalised 0.0–1.0 unless noted.
    """

    bass_energy: float = 0.0
    mid_energy: float = 0.0
    high_energy: float = 0.0
    beat_confidence: float = 0.0
    tempo_estimate: float = 120.0
    phase: float = 0.0
    spectral_centroid: float = 0.0
    spectral_rolloff: float = 0.0
    spectral_flatness: float = 0.0
    mfcc_1: float = 0.0
    mfcc_2: float = 0.0
    mfcc_3: float = 0.0
    mfcc_4: float = 0.0
    mfcc_5: float = 0.0
    mfcc_6: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "AudioReactivityFeatures":
        known = {k: v for k, v in data.items() if k in AudioReactivityFeatures.__dataclass_fields__}
        return AudioReactivityFeatures(**known)


# ---------------------------------------------------------------------------
# ParameterMapper
# ---------------------------------------------------------------------------

class ParameterMapper:
    """
    Maps audio feature values to effect parameter values.
    Config: {'scale': float, 'offset': float, 'target_range': [min, max]}
    Output = clamp(value * scale + offset, target_range)
    """

    def __init__(self) -> None:
        self._mappings: Dict[str, Dict[str, dict]] = {}

    def set_mapping(self, effect_name: str, parameter_name: str, config: dict) -> bool:
        self._mappings.setdefault(effect_name, {})[parameter_name] = dict(config)
        return True

    def get_mapping(self, effect_name: str, parameter_name: str) -> dict:
        return dict(self._mappings.get(effect_name, {}).get(parameter_name, {}))

    def get_active_mappings(self) -> List[dict]:
        result = []
        for eff, params in self._mappings.items():
            for param, cfg in params.items():
                result.append({"effect": eff, "parameter": param, **cfg})
        return result

    def map_features_to_parameter(
        self,
        effect_name: str,
        parameter_name: str,
        feature_value: float,
        config: dict,
    ) -> float:
        """Apply scale → offset → clamp. Returns 0.0 if config is empty."""
        if not config:
            return 0.0
        scale = float(config.get("scale", 1.0))
        offset = float(config.get("offset", 0.0))
        lo, hi = config.get("target_range", [0.0, 1.0])
        return float(np.clip(feature_value * scale + offset, lo, hi))


# ---------------------------------------------------------------------------
# AudioReactivityManager
# ---------------------------------------------------------------------------

class AudioReactivityManager:
    """
    Processes raw audio frames into AudioReactivityFeatures.
    Uses numpy FFT (no external audio libs required).
    Optionally drives a ParameterMapper for effect parameter control.
    """

    METADATA: dict = {"spec": "P1-A5", "tier": "Pro-Tier Native"}

    def __init__(
        self,
        sample_rate: int = 44100,
        hop_size: int = 1024,
        confidence_threshold: float = 0.5,
    ) -> None:
        self._sample_rate = sample_rate
        self._hop_size = hop_size
        self._confidence_threshold = confidence_threshold

        self._freq_bins = np.fft.rfftfreq(hop_size, 1.0 / sample_rate)
        self._mapper = ParameterMapper()
        self._history: deque = deque(maxlen=3600)
        self._latest: Optional[AudioReactivityFeatures] = None
        self._subscribers: List[Callable] = []
        self.error_state: bool = False
        self.last_error: Optional[str] = None
        self._recovery_attempts: int = 0

        # Beat tracking state
        self._prev_magnitude: Optional[np.ndarray] = None
        self._energy_history: deque = deque(maxlen=60)
        self._last_onset_time: float = 0.0
        self._bpm: float = 120.0
        self._beat_times: deque = deque(maxlen=64)

    # ---- Frame processing --------------------------------------------------

    def process_audio_frame(self, audio_frame: np.ndarray) -> AudioReactivityFeatures:
        """
        Process a single audio frame and extract all reactivity features.
        Returns AudioReactivityFeatures (and stores as latest).
        """
        try:
            return self._process_frame(audio_frame)
        except Exception as exc:
            self.error_state = True
            self.last_error = str(exc)
            logger.error("AudioReactivityManager: %s", exc)
            return self._safe_fallback()

    def _process_frame(self, audio: np.ndarray) -> AudioReactivityFeatures:
        n = len(audio)
        window = _hann(n)
        windowed = audio * window

        # FFT
        spectrum = np.abs(np.fft.rfft(windowed))
        freqs = self._freq_bins if len(self._freq_bins) == len(spectrum) else np.fft.rfftfreq(n, 1.0 / self._sample_rate)

        total = float(np.sum(spectrum)) + 1e-9

        # Band energies
        bass = self._band_energy(spectrum, freqs, 20, 150)
        mid = self._band_energy(spectrum, freqs, 150, 2000)
        high = self._band_energy(spectrum, freqs, 2000, 20000)

        # Spectral centroid (normalised 0-1)
        centroid_hz = float(np.sum(freqs * spectrum)) / total
        centroid = min(1.0, centroid_hz / (self._sample_rate / 2.0))

        # Spectral rolloff (frequency where 85% of energy is below)
        cumsum = np.cumsum(spectrum)
        rolloff_idx = np.searchsorted(cumsum, 0.85 * cumsum[-1])
        rolloff_hz = float(freqs[min(rolloff_idx, len(freqs) - 1)])
        rolloff = min(1.0, rolloff_hz / (self._sample_rate / 2.0))

        # Spectral flatness (geometric vs arithmetic mean)
        geomean = float(np.exp(np.mean(np.log(spectrum + 1e-10))))
        arithmean = float(np.mean(spectrum + 1e-10))
        flatness = min(1.0, geomean / (arithmean + 1e-9))

        # Pseudo-MFCC: use band sums across mel-like bands (6 bands)
        mfccs = self._pseudo_mfcc(spectrum, freqs, 6)

        # Simple onset detection → beat tracking
        beat_conf, phase, bpm = self._detect_beat(spectrum)

        features = AudioReactivityFeatures(
            bass_energy=bass,
            mid_energy=mid,
            high_energy=high,
            beat_confidence=beat_conf,
            tempo_estimate=bpm,
            phase=phase,
            spectral_centroid=centroid,
            spectral_rolloff=rolloff,
            spectral_flatness=flatness,
            mfcc_1=mfccs[0] if len(mfccs) > 0 else 0.0,
            mfcc_2=mfccs[1] if len(mfccs) > 1 else 0.0,
            mfcc_3=mfccs[2] if len(mfccs) > 2 else 0.0,
            mfcc_4=mfccs[3] if len(mfccs) > 3 else 0.0,
            mfcc_5=mfccs[4] if len(mfccs) > 4 else 0.0,
            mfcc_6=mfccs[5] if len(mfccs) > 5 else 0.0,
            timestamp=time.time(),
        )

        self._latest = features
        self._history.append(features)
        self._notify(features)
        return features

    def _band_energy(self, spectrum: np.ndarray, freqs: np.ndarray, lo: float, hi: float) -> float:
        mask = (freqs >= lo) & (freqs < hi)
        if not np.any(mask):
            return 0.0
        raw = float(np.mean(spectrum[mask] ** 2)) ** 0.5
        return min(1.0, raw)

    def _pseudo_mfcc(self, spectrum: np.ndarray, freqs: np.ndarray, n_bands: int) -> List[float]:
        """Divides spectrum into log-spaced bands, returns normalised energies."""
        lo_hz, hi_hz = 20.0, self._sample_rate / 2.0
        edges = np.logspace(np.log10(lo_hz + 1), np.log10(hi_hz), n_bands + 1)
        energies = []
        for i in range(n_bands):
            mask = (freqs >= edges[i]) & (freqs < edges[i + 1])
            val = float(np.mean(spectrum[mask])) if np.any(mask) else 0.0
            energies.append(min(1.0, val))
        return energies

    def _detect_beat(self, magnitude: np.ndarray) -> tuple:
        """Minimal onset→beat detection. Returns (confidence, phase, bpm)."""
        if self._prev_magnitude is None or len(self._prev_magnitude) != len(magnitude):
            self._prev_magnitude = magnitude.copy()
            return 0.0, 0.0, self._bpm

        flux = float(np.sum(np.maximum(magnitude - self._prev_magnitude, 0.0)))
        self._prev_magnitude = magnitude.copy()

        bass_energy = float(np.sum(magnitude[:20] ** 2))
        self._energy_history.append(bass_energy)
        avg = float(np.mean(list(self._energy_history))) if self._energy_history else 1.0

        onset = flux > avg * 1.3 and avg > 0
        confidence = 0.0
        now = time.time()

        if onset:
            self._beat_times.append(now)
            self._last_onset_time = now
            confidence = min(1.0, flux / (avg * 2.6 + 1e-9))

            # BPM from recent IOIs
            times = list(self._beat_times)
            if len(times) >= 3:
                iois = [t - times[i] for i, t in enumerate(times[1:])]
                valid_bpms = [60.0 / ioi for ioi in iois if 60.0 / ioi > 40]
                if valid_bpms:
                    self._bpm = float(np.median(valid_bpms))

        # Phase
        phase = 0.0
        if self._last_onset_time > 0:
            interval = 60.0 / max(self._bpm, 1.0)
            phase = ((now - self._last_onset_time) % interval) / interval

        return confidence, phase, self._bpm

    # ---- Accessors ---------------------------------------------------------

    def get_features(self) -> AudioReactivityFeatures:
        return self._latest or AudioReactivityFeatures()

    def get_feature_history(self, duration_seconds: float) -> List[AudioReactivityFeatures]:
        cutoff = time.time() - duration_seconds
        return [f for f in self._history if f.timestamp >= cutoff]

    def get_confidence(self, feature_type: str) -> float:
        f = self.get_features()
        return float(getattr(f, feature_type, 0.0))

    def set_confidence_threshold(self, threshold: float) -> None:
        self._confidence_threshold = threshold

    def get_stats(self) -> dict:
        return {
            "history_size": len(self._history),
            "active_mappings": len(self._mapper.get_active_mappings()),
            "error_state": self.error_state,
            "bpm_estimate": self._bpm,
        }

    # ---- Mapping API -------------------------------------------------------

    def set_mapping(self, effect_name: str, parameter_name: str, config: dict) -> bool:
        return self._mapper.set_mapping(effect_name, parameter_name, config)

    def get_mapping(self, effect_name: str, parameter_name: str) -> dict:
        return self._mapper.get_mapping(effect_name, parameter_name)

    def update_mappings(self) -> None:
        pass  # reserved for future reactive mapping updates

    def get_active_mappings(self) -> List[dict]:
        return self._mapper.get_active_mappings()

    @property
    def mapper(self) -> ParameterMapper:
        return self._mapper

    # ---- Subscriber pattern ------------------------------------------------

    def subscribe(self, callback: Callable) -> None:
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _notify(self, features: AudioReactivityFeatures) -> None:
        for cb in list(self._subscribers):
            try:
                cb(features)
            except Exception as exc:
                logger.debug("AudioReactivityManager subscriber: %s", exc)

    def _safe_fallback(self) -> AudioReactivityFeatures:
        return AudioReactivityFeatures()
