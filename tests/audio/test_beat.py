"""Tests for P1-A2 — BeatDetector, OnsetDetector, TempoEstimator (beat.py)"""
import time
import numpy as np
import pytest
from vjlive3.audio.beat import (
    BeatDetector, BeatDetectionResult, BeatStateMachine,
    OnsetDetector, TempoEstimator,
)


# ---- OnsetDetector -------------------------------------------------------

def test_onset_no_prev_magnitude():
    """First call returns (False, 0.0) because no previous magnitude exists."""
    od = OnsetDetector()
    mag = np.random.rand(1025).astype(np.float32)
    onset, conf = od.detect(mag)
    assert onset is False
    assert conf == pytest.approx(0.0)


def test_onset_spike_detected():
    """Large positive flux relative to baseline triggers onset=True."""
    od = OnsetDetector()
    # Warm up energy history
    baseline = np.ones(1025, dtype=np.float32) * 0.1
    for _ in range(15):
        od.detect(baseline)
    # Spike: magnitude 10× the baseline
    spike = np.ones(1025, dtype=np.float32) * 10.0
    onset, conf = od.detect(spike)
    assert onset is True
    assert 0.0 < conf <= 1.0


def test_onset_reset():
    """After reset(), first call again returns False."""
    od = OnsetDetector()
    mag = np.random.rand(1025).astype(np.float32)
    od.detect(mag)
    od.detect(mag)
    od.reset()
    onset, _ = od.detect(mag)
    assert onset is False


# ---- TempoEstimator -------------------------------------------------------

def test_tempo_estimator_empty():
    """Empty onset list returns default 120 BPM and 0 confidence."""
    te = TempoEstimator()
    bpm, conf = te.estimate([])
    assert bpm == pytest.approx(120.0)
    assert conf == pytest.approx(0.0)


def test_tempo_estimator_120bpm():
    """10 onsets at 0.5 s intervals (120 BPM) → tempo ≈ 120, confidence > 0.5."""
    te = TempoEstimator()
    now = time.time()
    onsets = [now + i * 0.5 for i in range(10)]
    bpm, conf = te.estimate(onsets)
    assert abs(bpm - 120.0) < 6.0, f"Expected ~120 BPM, got {bpm:.1f}"
    assert conf > 0.5


def test_tempo_estimator_range_filter():
    """IOIs that map outside (60, 180) BPM are filtered out."""
    te = TempoEstimator()
    # IOIs of 5s → 12 BPM — should be filtered
    now = time.time()
    onsets = [now + i * 5.0 for i in range(10)]
    bpm, conf = te.estimate(onsets)
    # Stays at default 120 because no valid BPMs
    assert bpm == pytest.approx(120.0)
    assert conf == pytest.approx(0.0)


# ---- BeatDetector (public API) -------------------------------------------

def test_beat_detector_smoke():
    """process_frame returns a BeatDetectionResult without error."""
    bd = BeatDetector()
    mag = np.random.rand(1025).astype(np.float32)
    result = bd.process_frame(mag)
    assert isinstance(result, BeatDetectionResult)
    assert 0.0 <= result.beat_confidence <= 1.0
    assert result.tempo > 0


def test_beat_detector_accessors():
    """is_beat, get_bpm, get_phase, get_beat_strength return valid values."""
    bd = BeatDetector()
    mag = np.ones(1025, dtype=np.float32)
    bd.process_frame(mag)
    assert isinstance(bd.is_beat(), bool)
    assert bd.get_bpm() > 0
    assert 0.0 <= bd.get_phase() <= 1.0
    assert 0.0 <= bd.get_beat_strength() <= 1.0


def test_beat_detector_reset():
    """reset() clears latest result and returns fresh state."""
    bd = BeatDetector()
    bd.process_frame(np.ones(1025, dtype=np.float32))
    bd.reset()
    assert bd._latest is None
    assert bd.get_confidence() == pytest.approx(0.0)


def test_beat_state_machine_searching_to_tracking():
    """High-confidence result transitions state from searching → tracking."""
    from vjlive3.audio.beat import BeatDetectionResult
    fsm = BeatStateMachine()
    assert fsm.state == "searching"
    high_conf = BeatDetectionResult(confidence=0.9)
    fsm.update(high_conf)
    assert fsm.state == "tracking"


def test_beat_history_duration():
    """get_beat_history returns only results within the time window."""
    bd = BeatDetector()
    mag = np.ones(1025, dtype=np.float32)
    for _ in range(5):
        bd.process_frame(mag)
    history = bd.get_beat_history(duration_seconds=5.0)
    assert len(history) >= 5
    history_0 = bd.get_beat_history(duration_seconds=0.0)
    assert len(history_0) <= len(history)


def test_beat_detection_latency():
    """1000 process_frame calls complete in < 10 s (10ms/call budget)."""
    import time as T
    bd = BeatDetector()
    mag = np.random.rand(1025).astype(np.float32)
    start = T.perf_counter()
    for _ in range(1000):
        bd.process_frame(mag)
    elapsed = T.perf_counter() - start
    assert elapsed < 10.0, f"1000 detections took {elapsed:.2f}s > 10s"
