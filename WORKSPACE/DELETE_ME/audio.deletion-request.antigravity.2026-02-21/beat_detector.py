"""P1-A2 — Real-Time Beat Detection (RhythmEngine)

Phase-Locked Loop beat tracker using spectral flux onset detection.
Consumes AudioFrame objects and produces beat events, BPM estimates, beat phase,
and confidence scores. Thread-safe for get_state(); update() must be called from
one thread only.

Spec: docs/specs/P1-A2_beat_detector.md
"""
from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.signal import butter, sosfilt

from vjlive3.audio.analyzer import AudioFrame

_log = logging.getLogger(__name__)


# ── Public data type ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BeatState:
    """Immutable snapshot of one beat-detection tick."""
    beat: bool          # True for one tick when a beat fires
    snare: bool         # True for one tick on snare detection
    bpm: float          # Current BPM estimate (60–200)
    phase: float        # Beat phase 0.0–1.0 (continuous, PLL-driven)
    confidence: float   # Lock confidence 0.0–1.0


# ── Internal PLL state ───────────────────────────────────────────────────────

@dataclass
class _PLLState:
    """Mutable PLL internals (not exposed)."""
    bpm: float = 120.0
    phase: float = 0.0
    confidence: float = 0.0
    prev_spectrum: np.ndarray = field(default_factory=lambda: np.zeros(20))
    flux_history: deque = field(default_factory=lambda: deque(maxlen=43))  # ~1s at 60fps
    last_onset_time: float = 0.0


# ── BeatDetector ─────────────────────────────────────────────────────────────

class BeatDetector:
    """Phase-Locked Loop beat tracker.

    Call update() once per audio analysis tick (aligned with AudioFrame production).
    Call get_state() at any time from any thread to read the latest BeatState.

    Thread-safe for get_state(); update() must be called from one thread only
    (the audio analysis thread or a dedicated beat thread).
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        buffer_size: int = 2048,
        bpm_min: float = 60.0,
        bpm_max: float = 200.0,
        initial_bpm: float = 120.0,
    ) -> None:
        """
        Args:
            sample_rate: Must match AudioAnalyzer sample rate.
            buffer_size: Must match AudioAnalyzer buffer size.
            bpm_min / bpm_max: Clamp for PLL BPM tracking.
            initial_bpm: Starting BPM before any audio input.
        """
        self._sample_rate = sample_rate
        self._buffer_size = buffer_size
        self._bpm_min = bpm_min
        self._bpm_max = bpm_max

        # PLL state (mutable, updated by update())
        self._state = _PLLState(bpm=initial_bpm)

        # Thread-safety: read-only snapshot for get_state()
        self._snapshot = BeatState(
            beat=False, snare=False, bpm=initial_bpm, phase=0.0, confidence=0.0
        )
        self._snapshot_lock = threading.RLock()

        # Snare bandpass filter (250–4000 Hz) using second-order sections for stability
        self._nyquist = sample_rate / 2.0
        self._snare_sos = butter(
            5, [250 / self._nyquist, 4000 / self._nyquist], btype='band', output='sos'
        )
        # Initialize filter state to zeros to avoid startup transient
        # sosfilt expects zi shape (n_sections, 2)
        self._snare_zi = np.zeros((self._snare_sos.shape[0], 2), dtype=np.float64)

        _log.debug("BeatDetector initialized: %.0f–%.0f BPM, initial=%.1f", bpm_min, bpm_max, initial_bpm)

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, frame: 'AudioFrame', dt: float) -> BeatState:
        """
        Process one AudioFrame and advance the PLL.

        Args:
            frame: Latest AudioFrame from P1-A1.
            dt:    Elapsed seconds since last update() call.

        Returns:
            Updated BeatState (also stored internally for get_state()).
        """
        # Cap dt to prevent runaway phase on long gaps (spec: max 1.0s)
        if dt > 1.0:
            dt = 1.0
        elif dt <= 0:
            dt = 0.016  # assume 60fps fallback

        # Onset detection: prefer frame.spectral_flux (authoritative from P1-A1)
        # fallback to delta-spectrum for cases where spectral_flux is not provided
        spectrum = np.array(frame.spectrum[:20], dtype=np.float32)
        spec_flux = float(np.sum(np.maximum(0.0, spectrum - self._state.prev_spectrum)))
        self._state.prev_spectrum = spectrum

        # Primary onset signal: frame.spectral_flux if non-zero, else delta-spectrum
        onset_signal = frame.spectral_flux if frame.spectral_flux > 0.0 else spec_flux
        self._state.flux_history.append(onset_signal)

        # Adaptive threshold: mean(flux_history) * 1.5
        threshold = 0.0
        if len(self._state.flux_history) > 0:
            threshold = float(np.mean(self._state.flux_history)) * 1.5

        is_onset = onset_signal > threshold and onset_signal > 0.0

        # 2. PLL phase advance
        period = 60.0 / self._state.bpm
        self._state.phase += dt / period
        beat_fired = False

        if self._state.phase >= 1.0:
            self._state.phase -= 1.0
            beat_fired = True

        # 3. PLL error correction (on onset)
        if is_onset:
            # Compute phase error: how far from 0 (beat)?
            error = self._state.phase if self._state.phase < 0.5 else self._state.phase - 1.0
            alpha = 0.1 + (1.0 - self._state.confidence) * 0.2
            self._state.phase -= error * alpha

            # Adjust tempo only on confident onsets (abs(error) < 0.2)
            if abs(error) < 0.2:
                new_period = period + error * 0.01
                new_bpm = 60.0 / new_period
                # Smooth BPM estimate (90% old, 10% new) and clamp
                self._state.bpm = np.clip(
                    0.9 * self._state.bpm + 0.1 * new_bpm,
                    self._bpm_min,
                    self._bpm_max
                )
                self._state.confidence = min(1.0, self._state.confidence + 0.1)
            else:
                self._state.confidence = max(0.0, self._state.confidence - 0.005)
        else:
            # No onset: confidence decays slowly
            self._state.confidence = max(0.0, self._state.confidence - 0.005)

        # Ensure phase stays in [0, 1)
        if self._state.phase < 0:
            self._state.phase += 1.0
        elif self._state.phase >= 1.0:
            self._state.phase -= 1.0

        # Clamp BPM to range
        self._state.bpm = np.clip(self._state.bpm, self._bpm_min, self._bpm_max)

        # 4. Snare detection (mid-band energy via sosfilt — stateful)
        snare_fired = False
        if frame.waveform:
            signal = np.array(frame.waveform, dtype=np.float64)
            if len(signal) >= 20:  # need enough samples for filter
                filtered, self._snare_zi = sosfilt(self._snare_sos, signal, zi=self._snare_zi)
                snare_energy = float(np.sum(filtered ** 2)) / max(len(signal), 1)
                snare_fired = snare_energy > 0.3  # per-sample threshold — tuned to reject bass transients

        # Build BeatState
        state = BeatState(
            beat=beat_fired,
            snare=snare_fired,
            bpm=float(self._state.bpm),
            phase=float(self._state.phase),
            confidence=float(self._state.confidence),
        )

        # Update snapshot (thread-safe)
        with self._snapshot_lock:
            self._snapshot = state

        return state

    def get_state(self) -> BeatState:
        """
        Return most recent BeatState. Thread-safe, never blocks.
        Returns zeroed state if update() has never been called.
        """
        with self._snapshot_lock:
            return self._snapshot

    def reset(self, bpm: float = 120.0) -> None:
        """Reset PLL to a known BPM, zeroing phase and confidence."""
        with self._snapshot_lock:
            self._state = _PLLState(bpm=np.clip(bpm, self._bpm_min, self._bpm_max))
            self._snapshot = BeatState(
                beat=False, snare=False, bpm=self._state.bpm, phase=0.0, confidence=0.0
            )
        _log.debug("BeatDetector reset: bpm=%.1f", bpm)


# ── Helper: filter initial conditions ─────────────────────────────────────────

def lfilter_zi(b, a, x0=0):
    """Compute initial state for lfilter to match steady-state."""
    # Simplified: return zeros matching filter order
    return np.zeros(max(len(a), len(b)) - 1, dtype=np.float32)


# ── Factory ───────────────────────────────────────────────────────────────────

def create_beat_detector(
    sample_rate: int = 44100,
    buffer_size: int = 2048,
    bpm_min: float = 60.0,
    bpm_max: float = 200.0,
    initial_bpm: float = 120.0,
) -> BeatDetector:
    """Factory for BeatDetector with standard parameters."""
    return BeatDetector(
        sample_rate=sample_rate,
        buffer_size=buffer_size,
        bpm_min=bpm_min,
        bpm_max=bpm_max,
        initial_bpm=initial_bpm,
    )


__all__ = [
    "BeatState", "BeatDetector", "create_beat_detector",
]
