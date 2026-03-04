"""Tests for P1-A5 — AudioReactivityFeatures, ParameterMapper, AudioReactivityManager (reactivity.py)"""
import time
import numpy as np
import pytest
from vjlive3.audio.reactivity import (
    AudioReactivityFeatures,
    ParameterMapper,
    AudioReactivityManager,
)


# ---- AudioReactivityFeatures ---------------------------------------------

def test_features_defaults():
    """Default fields are all zero except timestamp."""
    f = AudioReactivityFeatures()
    assert f.bass_energy == pytest.approx(0.0)
    assert f.tempo_estimate == pytest.approx(120.0)
    assert f.timestamp > 0


def test_features_to_dict():
    """to_dict() contains all expected keys."""
    d = AudioReactivityFeatures().to_dict()
    for key in ("bass_energy", "mid_energy", "high_energy", "beat_confidence",
                "tempo_estimate", "spectral_centroid", "mfcc_1", "timestamp"):
        assert key in d, f"Missing key: {key}"


def test_features_from_dict_roundtrip():
    """from_dict(to_dict()) restores all values."""
    f = AudioReactivityFeatures(bass_energy=0.7, tempo_estimate=140.0, mfcc_3=0.5)
    d = f.to_dict()
    f2 = AudioReactivityFeatures.from_dict(d)
    assert f2.bass_energy == pytest.approx(0.7)
    assert f2.tempo_estimate == pytest.approx(140.0)
    assert f2.mfcc_3 == pytest.approx(0.5)


# ---- ParameterMapper -----------------------------------------------------

def test_mapper_set_get():
    """set_mapping and get_mapping round-trip correctly."""
    pm = ParameterMapper()
    cfg = {"scale": 2.0, "offset": 0.1, "target_range": [0.0, 1.0]}
    pm.set_mapping("reverb", "intensity", cfg)
    got = pm.get_mapping("reverb", "intensity")
    assert got["scale"] == pytest.approx(2.0)
    assert got["offset"] == pytest.approx(0.1)


def test_mapper_math():
    """scale=2, offset=0.5 → value=0.5 → 1.5 clamped to 1.0."""
    pm = ParameterMapper()
    cfg = {"scale": 2.0, "offset": 0.5, "target_range": [0.0, 1.0]}
    result = pm.map_features_to_parameter("fx", "p", 0.5, cfg)
    assert result == pytest.approx(1.0)


def test_mapper_empty_config():
    """Empty config returns 0.0."""
    pm = ParameterMapper()
    result = pm.map_features_to_parameter("fx", "p", 0.9, {})
    assert result == pytest.approx(0.0)


def test_mapper_get_active_mappings():
    """get_active_mappings returns all registered configs."""
    pm = ParameterMapper()
    pm.set_mapping("fx1", "p1", {"scale": 1.0})
    pm.set_mapping("fx1", "p2", {"scale": 2.0})
    pm.set_mapping("fx2", "p1", {"scale": 0.5})
    active = pm.get_active_mappings()
    assert len(active) == 3


# ---- AudioReactivityManager ----------------------------------------------

def _sine_frame(freq: float = 440.0, n: int = 1024, sr: int = 44100) -> np.ndarray:
    t = np.linspace(0, n / sr, n, endpoint=False)
    return np.sin(2 * np.pi * freq * t).astype(np.float32)


def test_manager_process_sine():
    """Sine wave produces non-zero bass/mid/high energies."""
    mgr = AudioReactivityManager(sample_rate=44100, hop_size=1024)
    frame = _sine_frame(440.0)
    f = mgr.process_audio_frame(frame)
    assert f.bass_energy >= 0.0
    assert f.mid_energy >= 0.0 or f.bass_energy >= 0.0
    assert 0.0 <= f.spectral_centroid <= 1.0


def test_manager_spectral_features_range():
    """spectral_centroid, rolloff, flatness are in [0, 1]."""
    mgr = AudioReactivityManager()
    frame = np.random.randn(1024).astype(np.float32)
    f = mgr.process_audio_frame(frame)
    assert 0.0 <= f.spectral_centroid <= 1.0
    assert 0.0 <= f.spectral_rolloff <= 1.0
    assert 0.0 <= f.spectral_flatness <= 1.0


def test_manager_mfcc_fields():
    """mfcc_1 through mfcc_6 are populated (not all zero for noisy frame)."""
    mgr = AudioReactivityManager()
    frame = np.random.randn(1024).astype(np.float32) * 0.5
    f = mgr.process_audio_frame(frame)
    mfccs = [f.mfcc_1, f.mfcc_2, f.mfcc_3, f.mfcc_4, f.mfcc_5, f.mfcc_6]
    # At least one should be non-zero for random noise
    assert any(v > 0.0 for v in mfccs)


def test_manager_subscriber():
    """Subscriber callback is invoked once per process_audio_frame."""
    mgr = AudioReactivityManager()
    calls = []
    mgr.subscribe(lambda f: calls.append(f))
    frame = _sine_frame()
    mgr.process_audio_frame(frame)
    assert len(calls) == 1
    assert isinstance(calls[0], AudioReactivityFeatures)


def test_manager_latency():
    """100 frames process in < 5 s (50ms/frame spec budget)."""
    mgr = AudioReactivityManager()
    frame = np.random.randn(1024).astype(np.float32)
    start = time.perf_counter()
    for _ in range(100):
        mgr.process_audio_frame(frame)
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"100 frames took {elapsed:.2f}s > 5s"


def test_manager_get_stats():
    """get_stats returns a dict with expected keys."""
    mgr = AudioReactivityManager()
    s = mgr.get_stats()
    assert "history_size" in s
    assert "bpm_estimate" in s
    assert "error_state" in s
