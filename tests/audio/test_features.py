"""Tests for P1-A1 — AudioFeatures, AudioAnalyzerConfig, AudioDevice (features.py)"""
import time
import pytest
from vjlive3.audio.features import AudioFeatures, AudioAnalyzerConfig, AudioDevice


def test_audio_features_defaults():
    """Default AudioFeatures values are zero/False."""
    f = AudioFeatures()
    assert f.beat is False
    assert f.bass == pytest.approx(0.0)
    assert f.bpm == pytest.approx(120.0)
    assert f.loudness_integrated == pytest.approx(-23.0)


def test_audio_features_zero_classmethod():
    """zero() returns an instance with all numeric fields at 0."""
    f = AudioFeatures.zero()
    assert f.beat is False
    assert f.volume == pytest.approx(0.0)
    assert f.bass_smooth == pytest.approx(0.0)


def test_audio_features_to_dict_keys():
    """to_dict() returns all required keys."""
    d = AudioFeatures().to_dict()
    for key in ("beat", "bass", "mid", "high", "volume", "bpm", "beat_phase",
                "spectral_centroid", "onset", "beat_confidence", "timestamp"):
        assert key in d, f"Missing key: {key}"


def test_audio_features_to_dict_values():
    """to_dict() values match the dataclass fields."""
    f = AudioFeatures(bass=0.42, bpm=140.0, beat=True)
    d = f.to_dict()
    assert d["bass"] == pytest.approx(0.42)
    assert d["bpm"] == pytest.approx(140.0)
    assert d["beat"] is True


def test_audio_analyzer_config_defaults():
    """AudioAnalyzerConfig has correct defaults."""
    cfg = AudioAnalyzerConfig()
    assert cfg.sample_rate == 48000
    assert cfg.fft_size == 2048
    assert cfg.fallback_to_dummy is True
    assert cfg.broadcast_rate == pytest.approx(60.0)


def test_audio_device_fields():
    """AudioDevice stores all provided fields correctly."""
    dev = AudioDevice(id=3, name="USB Mic", channels=2, default_samplerate=44100.0)
    assert dev.id == 3
    assert dev.name == "USB Mic"
    assert dev.channels == 2
    assert dev.default_samplerate == pytest.approx(44100.0)
