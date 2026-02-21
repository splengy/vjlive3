"""Tests for BeatDetector."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import numpy as np
import pytest
from vjlive3.audio.analyzer import AudioAnalyzer
from vjlive3.audio.beat_detector import BeatDetector


def _feed_silence(analyzer, detector, n_frames=50):
    for _ in range(n_frames):
        analyzer.update(np.zeros(1024, dtype=np.float32))
        detector.update(analyzer)


def _feed_energy_spike(analyzer, detector):
    """Feed a strong impulse — should trigger a beat."""
    analyzer.update(np.ones(1024, dtype=np.float32))
    detector.update(analyzer)


def test_silence_produces_no_beats():
    a = AudioAnalyzer(fft_size=1024)
    d = BeatDetector()
    _feed_silence(a, d, n_frames=100)
    assert not d.beat


def test_energy_spike_detected():
    a = AudioAnalyzer(fft_size=1024)
    d = BeatDetector()
    _feed_silence(a, d, n_frames=10)    # warm up history
    _feed_energy_spike(a, d)
    assert d.beat, "Strong impulse after silence should trigger beat"


def test_rapid_beats_throttled():
    """Second spike within _MIN_IOI_SEC should NOT trigger a beat."""
    a = AudioAnalyzer(fft_size=1024)
    d = BeatDetector()
    _feed_silence(a, d, n_frames=10)
    _feed_energy_spike(a, d)       # first beat
    _feed_energy_spike(a, d)       # too soon — should be suppressed
    assert not d.beat


def test_onset_strength_positive_after_spike():
    a = AudioAnalyzer(fft_size=1024)
    d = BeatDetector()
    _feed_silence(a, d, n_frames=5)
    _feed_energy_spike(a, d)
    assert d.onset_strength > 0.0


def test_bpm_nonzero_after_beats():
    """Feed synthetic beats with 0.5s IOI by manipulating internal timestamps."""
    a = AudioAnalyzer(fft_size=1024)
    d = BeatDetector()
    import time
    _feed_silence(a, d, n_frames=10)
    # Manually drive 3 beats 0.5s apart by back-dating _last_beat_time
    for i in range(3):
        d._last_beat_time = time.perf_counter() - 0.6  # fake gap > MIN_IOI
        _feed_energy_spike(a, d)
    assert d.bpm > 0.0, "BPM should be non-zero after several synthetic beats"
