"""
P1-A2 — Beat Detector
Spec: docs/specs/_02_fleshed_out/P1-A2_beat_detector.md
Tier: 🖥️ Pro-Tier Native

Implements:
  OnsetDetector  — spectral flux + adaptive threshold
  TempoEstimator — inter-onset interval → BPM with smoothing
  BeatTracker    — integrates onset + tempo → beat/phase
  BeatStateMachine — searching / tracking / lost FSM
  BeatDetector   — public API class wrapping all inner components
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class BeatState:
    """Snapshot of beat tracking state."""
    beat: bool = False
    beat_confidence: float = 0.0
    tempo: float = 120.0
    phase: float = 0.0
    confidence: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class BeatDetectionResult:
    """Output of one beat detection cycle."""
    beat: bool = False
    beat_confidence: float = 0.0
    tempo: float = 120.0
    phase: float = 0.0
    confidence: float = 0.0
    timestamp: float = field(default_factory=time.time)


# ---------------------------------------------------------------------------
# OnsetDetector
# ---------------------------------------------------------------------------

class OnsetDetector:
    """
    Onset detection using spectral flux + adaptive threshold.
    Derived from P1-A2 spec: sum of positive spectral differences.
    """

    def __init__(self, sample_rate: int = 48000, hop_size: int = 512) -> None:
        self.sample_rate = sample_rate
        self.hop_size = hop_size
        self._prev_magnitude: Optional[np.ndarray] = None
        self._energy_history: deque = deque(maxlen=43)   # ~1 s at 60 Hz
        self._energy_threshold: float = 1.3

    def detect(self, magnitude: np.ndarray) -> Tuple[bool, float]:
        """Return (onset_detected, confidence 0–1)."""
        if self._prev_magnitude is None or len(self._prev_magnitude) != len(magnitude):
            self._prev_magnitude = magnitude.copy()
            return False, 0.0

        # Spectral flux: sum of positive differences
        diff = magnitude - self._prev_magnitude
        flux = float(np.sum(np.maximum(diff, 0.0)))
        self._prev_magnitude = magnitude.copy()

        # Adaptive threshold from local bass energy
        bass_energy = float(np.sum(magnitude[:20] ** 2))
        self._energy_history.append(bass_energy)

        if len(self._energy_history) < 10:
            return False, 0.0

        local_avg = float(np.mean(list(self._energy_history)[-10:]))
        threshold = local_avg * self._energy_threshold

        if flux > threshold and threshold > 0.0:
            confidence = min(1.0, flux / (threshold * 2.0))
            return True, confidence

        return False, 0.0

    def reset(self) -> None:
        self._prev_magnitude = None
        self._energy_history.clear()


# ---------------------------------------------------------------------------
# TempoEstimator
# ---------------------------------------------------------------------------

class TempoEstimator:
    """
    Estimates tempo from a sequence of onset timestamps using inter-onset
    intervals. Smooths tempo using EMA (70% old + 30% new).
    """

    def __init__(self, sample_rate: int = 48000, hop_size: int = 512) -> None:
        self._onset_times: deque = deque(maxlen=1024)  # ~8 s
        self._tempo_range: Tuple[float, float] = (60.0, 180.0)
        self.current_tempo: float = 120.0
        self.confidence: float = 0.0

    def estimate(self, onset_times: List[float]) -> Tuple[float, float]:
        """Feed onset timestamps; return (bpm, confidence)."""
        self._onset_times.extend(onset_times)

        times = list(self._onset_times)
        if len(times) < 2:
            return self.current_tempo, 0.0

        # Inter-onset intervals
        iois = [t - times[i] for i, t in enumerate(times[1:]) if t - times[i] > 0]
        if len(iois) < 5:
            return self.current_tempo, 0.0

        bpms = [60.0 / ioi for ioi in iois]
        lo, hi = self._tempo_range
        valid = [b for b in bpms if lo <= b <= hi]
        if not valid:
            return self.current_tempo, 0.0

        estimated = float(np.median(valid))

        # Confidence: how tightly clustered the IOIs are
        expected_ioi = 60.0 / estimated
        variance = float(np.mean([abs(ioi - expected_ioi) for ioi in iois]))
        confidence = 1.0 - min(1.0, variance / (expected_ioi * 0.1 + 1e-9))

        if confidence > 0.5:
            self.current_tempo = 0.7 * self.current_tempo + 0.3 * estimated

        self.confidence = confidence
        return self.current_tempo, confidence

    def set_tempo_range(self, min_bpm: float, max_bpm: float) -> None:
        self._tempo_range = (float(min_bpm), float(max_bpm))

    def reset(self) -> None:
        self._onset_times.clear()
        self.current_tempo = 120.0
        self.confidence = 0.0


# ---------------------------------------------------------------------------
# BeatStateMachine
# ---------------------------------------------------------------------------

class BeatStateMachine:
    """Three-state FSM: searching → tracking → lost → searching."""

    _STATES = ("searching", "tracking", "lost")

    def __init__(self) -> None:
        self.state: str = "searching"
        self._state_start: float = time.time()

    def update(self, result: BeatDetectionResult) -> None:
        now = time.time()
        if self.state == "searching":
            if result.confidence > 0.7:
                self.state = "tracking"
                self._state_start = now
        elif self.state == "tracking":
            if result.confidence < 0.3:
                self.state = "lost"
                self._state_start = now
        else:  # lost
            if result.confidence > 0.5:
                self.state = "tracking"
                self._state_start = now
            elif now - self._state_start > 5.0:
                self.state = "searching"
                self._state_start = now

    def get_state_info(self) -> dict:
        messages = {
            "searching": "Waiting for clear beat pattern",
            "tracking": "Following beat pattern",
            "lost": "Lost beat pattern, searching",
        }
        return {"state": self.state, "message": messages[self.state]}


# ---------------------------------------------------------------------------
# BeatDetector (public API)
# ---------------------------------------------------------------------------

class BeatDetector:
    """
    Real-time beat detection and tempo tracking.
    Public API as specified in P1-A2.

    Usage:
        detector = BeatDetector()
        detector.process_frame(magnitude)   # called once per FFT frame
        print(detector.get_bpm(), detector.get_phase())
    """

    METADATA: dict = {"spec": "P1-A2", "tier": "Pro-Tier Native"}

    def __init__(self, tempo_range: Tuple[int, int] = (60, 180)) -> None:
        self._onset = OnsetDetector()
        self._tempo = TempoEstimator()
        self._tempo.set_tempo_range(*tempo_range)
        self._fsm = BeatStateMachine()

        self._latest: Optional[BeatDetectionResult] = None
        self._history: deque = deque(maxlen=3600)
        self._last_onset_time: float = 0.0

    def process_frame(self, magnitude: np.ndarray) -> BeatDetectionResult:
        """Process one FFT magnitude frame; return BeatDetectionResult."""
        onset, onset_conf = self._onset.detect(magnitude)

        if onset:
            self._last_onset_time = time.time()
            self._tempo.estimate([self._last_onset_time])

        phase = self._compute_phase()
        beat = phase < 0.1
        strength = self._compute_strength(phase)

        result = BeatDetectionResult(
            beat=beat,
            beat_confidence=strength,
            tempo=self._tempo.current_tempo,
            phase=phase,
            confidence=self._tempo.confidence,
            timestamp=time.time(),
        )
        self._fsm.update(result)
        self._latest = result
        self._history.append(result)
        return result

    def _compute_phase(self) -> float:
        if self._last_onset_time == 0.0:
            return 0.0
        beat_interval = 60.0 / max(self._tempo.current_tempo, 1.0)
        elapsed = time.time() - self._last_onset_time
        return (elapsed % beat_interval) / beat_interval

    def _compute_strength(self, phase: float) -> float:
        if phase < 0.1:
            return self._tempo.confidence
        if phase < 0.2:
            return self._tempo.confidence * 0.5
        return 0.0

    # ---- Convenience accessors -------------------------------------------

    def get_current_state(self) -> BeatState:
        r = self._latest or BeatDetectionResult()
        return BeatState(
            beat=r.beat,
            beat_confidence=r.beat_confidence,
            tempo=r.tempo,
            phase=r.phase,
            confidence=r.confidence,
        )

    def reset(self) -> None:
        self._onset.reset()
        self._tempo.reset()
        self._fsm = BeatStateMachine()
        self._latest = None
        self._history.clear()
        self._last_onset_time = 0.0

    def set_tempo_range(self, min_bpm: int, max_bpm: int) -> None:
        self._tempo.set_tempo_range(min_bpm, max_bpm)

    def get_tempo_estimate(self) -> float:
        return self._tempo.current_tempo

    def get_beat_phase(self) -> float:
        return self._compute_phase()

    def get_confidence(self) -> float:
        return self._tempo.confidence

    def get_beat_history(self, duration_seconds: float) -> List[BeatDetectionResult]:
        cutoff = time.time() - duration_seconds
        return [r for r in self._history if r.timestamp >= cutoff]

    def is_beat(self) -> bool:
        return self._latest.beat if self._latest else False

    def get_bpm(self) -> float:
        return self._tempo.current_tempo

    def get_phase(self) -> float:
        return self._compute_phase()

    def get_beat_strength(self) -> float:
        return self._latest.beat_confidence if self._latest else 0.0
