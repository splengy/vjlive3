"""Beat / onset detector for VJLive3 audio engine.

Uses spectral energy flux — robust, real-time safe, no ML required.

Algorithm:
    1. Compute per-frame energy E(t) from AudioAnalyzer.spectrum
    2. Onset strength S(t) = max(0, E(t) - E(t-1))   [half-wave rectify]
    3. Beat when S(t) > adaptive_threshold(S)
    4. BPM estimated from inter-onset intervals (IOIs) with exponential smoothing
"""
from __future__ import annotations

import time
from collections import deque

import numpy as np

from vjlive3.audio.analyzer import AudioAnalyzer
from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)

_MIN_IOI_SEC  = 0.25   # 240 BPM max
_MAX_IOI_SEC  = 2.0    # 30 BPM min
_THRESHOLD_K  = 1.4    # multiplier above mean for beat detection
_SMOOTH_ALPHA = 0.15   # BPM exponential smoothing


class BeatDetector:
    """Onset and BPM estimator driven by an AudioAnalyzer.

    Args:
        history_len: Number of frames used to compute adaptive threshold.

    Example::

        detector = BeatDetector()
        for chunk in audio_stream:
            analyzer.update(chunk)
            detector.update(analyzer)
            if detector.beat:
                trigger_flash()
            print(f"BPM: {detector.bpm:.1f}")
    """

    def __init__(self, history_len: int = 43) -> None:
        self._history: deque[float] = deque(maxlen=history_len)
        self._prev_energy: float = 0.0
        self._last_beat_time: float = 0.0
        self._iois: deque[float] = deque(maxlen=8)  # inter-onset intervals

        # Public state — updated on each call to update()
        self.beat: bool = False
        self.onset_strength: float = 0.0
        self.bpm: float = 0.0

    def update(self, analyzer: AudioAnalyzer) -> None:
        """Process one frame. Call after ``analyzer.update(samples)``.

        Args:
            analyzer: AudioAnalyzer instance (reads .spectrum, .rms)
        """
        # Current frame energy — use RMS-weighted spectrum sum
        energy = float(np.sum(analyzer.spectrum) * (analyzer.rms + 1e-9))

        # Onset strength: half-wave rectified energy flux
        flux = max(0.0, energy - self._prev_energy)
        self._prev_energy = energy
        self.onset_strength = flux
        self._history.append(flux)

        # Adaptive threshold
        if len(self._history) > 1:
            threshold = _THRESHOLD_K * float(np.mean(self._history))
        else:
            threshold = _THRESHOLD_K

        now = time.perf_counter()
        ioi = now - self._last_beat_time

        # Beat = flux above threshold AND minimum IOI respected
        if flux > threshold and ioi >= _MIN_IOI_SEC:
            self.beat = True
            if ioi <= _MAX_IOI_SEC:
                self._iois.append(ioi)
                self._update_bpm()
            self._last_beat_time = now
        else:
            self.beat = False

    # ------------------------------------------------------------------ #
    #  Private                                                             #
    # ------------------------------------------------------------------ #

    def _update_bpm(self) -> None:
        if not self._iois:
            return
        raw_bpm = 60.0 / float(np.mean(self._iois))
        if self.bpm == 0.0:
            self.bpm = raw_bpm
        else:
            # Exponential smoothing
            self.bpm = _SMOOTH_ALPHA * raw_bpm + (1.0 - _SMOOTH_ALPHA) * self.bpm
