"""P2-X2 extension — Phase-Locked Loop for beat/clock synchronisation.

A general-purpose digital PLL that can lock to any periodic signal:
BPM-derived beat triggers, external timecode pulses, or MIDI clock.

The PLL maintains phase and frequency (BPM) estimates, applying
proportional-integral corrections on each pulse to minimise phase error.

Used by TimecodeEngine (external lock) and BeatDetector (beat-phase tracking).

Dependencies: stdlib math, threading only.
"""
from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass, field
from typing import Optional


# ── PLLState ──────────────────────────────────────────────────────────────────

@dataclass
class PLLState:
    """Snapshot of current PLL output."""
    phase:      float   # 0.0–1.0 cycle position
    frequency:  float   # Hz (BPM / 60 for beat PLL)
    bpm:        float   # frequency * 60
    confidence: float   # 0.0–1.0 lock confidence
    locked:     bool    # True when confidence > threshold


# ── PLL ───────────────────────────────────────────────────────────────────────

class PLL:
    """
    Digital Phase-Locked Loop.

    Call ``update(dt)`` every frame.
    Call ``pulse()`` when a beat/tick is detected.

    The loop corrects phase and frequency on each pulse using
    proportional (Kp) and integral (Ki) gains.

    Example — 120 BPM beat tracker::

        pll = PLL(nominal_freq=2.0)   # 2 Hz = 120 BPM
        pll.pulse()                   # on each detected beat
        state = pll.update(dt=0.016)  # each render frame
        print(state.bpm, state.phase)
    """

    #: Phase correction fraction applied per pulse (proportional gain)
    _DEFAULT_KP: float = 0.3
    #: Frequency correction fraction per pulse (integral gain)
    _DEFAULT_KI: float = 0.02
    #: Maximum frequency deviation fraction before clamping
    _MAX_FREQ_DEVIATION: float = 0.5
    #: Confidence decay per frame at 60fps
    _CONFIDENCE_DECAY: float = 0.005
    #: Confidence boost per pulse
    _CONFIDENCE_BOOST: float = 0.15
    #: Lock threshold
    _LOCK_THRESHOLD: float = 0.6

    def __init__(
        self,
        nominal_freq: float = 2.0,       # Hz (2 Hz = 120 BPM)
        kp: float = _DEFAULT_KP,
        ki: float = _DEFAULT_KI,
        min_freq: float = 0.5,           # Hz (30 BPM)
        max_freq: float = 8.0,           # Hz (480 BPM)
    ) -> None:
        self._kp = kp
        self._ki = ki
        self._min_freq = min_freq
        self._max_freq = max_freq

        self._lock = threading.Lock()
        self._freq: float = nominal_freq
        self._phase: float = 0.0
        self._confidence: float = 0.0
        self._last_pulse_t: Optional[float] = None
        self._last_update_t: float = time.monotonic()

    # ── Public API ────────────────────────────────────────────────────────────

    def pulse(self, t: Optional[float] = None) -> None:
        """Signal an external reference pulse (beat hit, MIDI tick, etc).

        Args:
            t: Timestamp of the pulse (defaults to time.monotonic()).
        """
        now = t if t is not None else time.monotonic()
        with self._lock:
            if self._last_pulse_t is not None:
                interval = now - self._last_pulse_t
                if interval > 0.01:   # ignore pulses < 10ms apart (double-hit guard)
                    measured_freq = 1.0 / interval
                    measured_freq = max(self._min_freq,
                                        min(self._max_freq, measured_freq))
                    # Frequency correction (integral)
                    freq_err = measured_freq - self._freq
                    self._freq += self._ki * freq_err
                    self._freq = max(self._min_freq, min(self._max_freq, self._freq))

                    # Phase correction (proportional) — pull phase toward 0
                    phase_err = self._phase   # ideal pulse at phase=0
                    if phase_err > 0.5:
                        phase_err -= 1.0      # wrap to [-0.5, 0.5]
                    self._phase -= self._kp * phase_err
                    self._phase %= 1.0

                    # Confidence boost
                    self._confidence = min(1.0, self._confidence + self._CONFIDENCE_BOOST)

            self._last_pulse_t = now

    def update(self, dt: Optional[float] = None) -> PLLState:
        """Advance the PLL by dt seconds and return current state.

        If dt is None, computes elapsed seconds since last update automatically.
        """
        now = time.monotonic()
        if dt is None:
            dt = now - self._last_update_t
        self._last_update_t = now

        with self._lock:
            # Advance phase
            if self._freq > 0:
                self._phase = (self._phase + self._freq * dt) % 1.0

            # Decay confidence
            self._confidence = max(0.0, self._confidence - self._CONFIDENCE_DECAY)

            return PLLState(
                phase=self._phase,
                frequency=self._freq,
                bpm=self._freq * 60.0,
                confidence=self._confidence,
                locked=self._confidence >= self._LOCK_THRESHOLD,
            )

    def reset(self, nominal_freq: Optional[float] = None) -> None:
        """Reset phase and confidence. Optionally reset frequency."""
        with self._lock:
            self._phase = 0.0
            self._confidence = 0.0
            self._last_pulse_t = None
            if nominal_freq is not None:
                self._freq = nominal_freq

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def bpm(self) -> float:
        with self._lock:
            return self._freq * 60.0

    @property
    def phase(self) -> float:
        with self._lock:
            return self._phase

    @property
    def confidence(self) -> float:
        with self._lock:
            return self._confidence

    @property
    def is_locked(self) -> bool:
        with self._lock:
            return self._confidence >= self._LOCK_THRESHOLD


__all__ = ["PLL", "PLLState"]
