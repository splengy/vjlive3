"""Shared audio reactivity bus for VJLive3.

Provides a thread-safe snapshot of current audio state that effect plugins
consume without needing direct access to the audio engine.

Usage::

    bus = ReactivityBus()
    bus.push(analyzer, detector)       # called by audio thread
    snap = bus.snapshot()              # called by render thread
    if snap.beat:
        effect.trigger_flash()
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field

import numpy as np

from vjlive3.audio.analyzer import AudioAnalyzer
from vjlive3.audio.beat_detector import BeatDetector
from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class AudioSnapshot:
    """Immutable audio state snapshot — safe to share between threads.

    Attributes:
        rms:            Root-mean-square power, 0.0–1.0
        bass:           Bass band energy, 0.0–1.0
        mids:           Mid-range band energy, 0.0–1.0
        highs:          High-frequency band energy, 0.0–1.0
        beat:           True if a beat was detected this frame
        bpm:            Estimated beats per minute (0 = unknown)
        onset_strength: Raw onset flux, 0.0–∞ (normalised to ~0-1 in practice)
        spectrum:       Full FFT magnitude array (read-only copy)
    """
    rms:            float
    bass:           float
    mids:           float
    highs:          float
    beat:           bool
    bpm:            float
    onset_strength: float
    spectrum:       np.ndarray = field(compare=False)

    @classmethod
    def silence(cls, fft_bins: int = 1025) -> "AudioSnapshot":
        """Return a silent/zero-state snapshot (useful for initialisation)."""
        return cls(
            rms=0.0, bass=0.0, mids=0.0, highs=0.0,
            beat=False, bpm=0.0, onset_strength=0.0,
            spectrum=np.zeros(fft_bins, dtype=np.float32),
        )


class ReactivityBus:
    """Thread-safe audio reactivity bus.

    The audio thread calls ``push()`` each time new audio is analysed.
    The render thread calls ``snapshot()`` to get the latest state.

    Subscribers can register callbacks that fire on each ``push()``.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latest: AudioSnapshot = AudioSnapshot.silence()
        self._subscribers: list = []
        logger.debug("ReactivityBus initialised")

    def push(self, analyzer: AudioAnalyzer, detector: BeatDetector) -> None:
        """Update the bus from current analyzer and detector state.

        Thread-safe. Called by the audio thread.

        Args:
            analyzer: Freshly updated AudioAnalyzer
            detector: Freshly updated BeatDetector
        """
        snap = AudioSnapshot(
            rms=analyzer.rms,
            bass=analyzer.bass,
            mids=analyzer.mids,
            highs=analyzer.highs,
            beat=detector.beat,
            bpm=detector.bpm,
            onset_strength=detector.onset_strength,
            spectrum=analyzer.spectrum.copy(),   # copy for immutability
        )
        with self._lock:
            self._latest = snap

        # Notify subscribers (called without the lock to avoid deadlocks)
        for cb in list(self._subscribers):
            try:
                cb(snap)
            except Exception:
                logger.exception("ReactivityBus subscriber raised an exception")

    def snapshot(self) -> AudioSnapshot:
        """Return the latest audio snapshot.

        Thread-safe. Called by the render thread.
        Returns a new snapshot with a **copied** spectrum so callers cannot
        mutate the internally stored state.
        """
        with self._lock:
            s = self._latest
        # Return fresh snapshot with copied spectrum — cheap scalar fields reused
        return AudioSnapshot(
            rms=s.rms, bass=s.bass, mids=s.mids, highs=s.highs,
            beat=s.beat, bpm=s.bpm, onset_strength=s.onset_strength,
            spectrum=s.spectrum.copy(),
        )

    def subscribe(self, callback) -> None:
        """Register a callable that fires on every push.

        Args:
            callback: ``(snapshot: AudioSnapshot) -> None``
        """
        self._subscribers.append(callback)

    def unsubscribe(self, callback) -> None:
        """Remove a previously registered callback."""
        try:
            self._subscribers.remove(callback)
        except ValueError:
            pass
