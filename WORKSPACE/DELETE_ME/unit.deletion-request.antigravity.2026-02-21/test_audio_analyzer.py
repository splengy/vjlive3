"""Tests for P1-A1 AudioAnalyzer

All tests run without audio hardware (force_null=True or NullAudioAnalyzer directly).
No PyAudio required.
"""
import math
import threading
import time

import numpy as np
import pytest

from vjlive3.audio.analyzer import (
    AudioAnalyzer,
    AudioFrame,
    NullAudioAnalyzer,
    _zeroed_frame,
    create_analyzer,
)


# ── NullAudioAnalyzer tests ───────────────────────────────────────────────────

def test_null_analyzer_returns_frame():
    a = NullAudioAnalyzer()
    f = a.get_frame()
    assert isinstance(f, AudioFrame)
    assert f.bass == 0.0
    assert f.rms == 0.0


def test_null_start_returns_true():
    a = NullAudioAnalyzer()
    assert a.start() is True
    assert a.is_running is True


def test_null_stop_noop():
    a = NullAudioAnalyzer()
    a.start()
    a.stop()   # must not raise
    assert a.is_running is False


def test_create_analyzer_force_null():
    a = create_analyzer(force_null=True)
    assert isinstance(a, NullAudioAnalyzer)


# ── AudioFrame semantics ──────────────────────────────────────────────────────

def test_audio_frame_is_frozen():
    f = _zeroed_frame()
    with pytest.raises((TypeError, AttributeError)):
        f.bass = 1.0  # type: ignore[misc]


def test_audio_frame_band_range():
    """After injection, all band values stay in 0–1."""
    a = NullAudioAnalyzer()
    a.start()
    frame = AudioFrame(
        bass=0.5, mid=0.3, high=0.1,
        rms=0.4, peak=0.8,
        spectrum=[0.1] * 128,
        waveform=[0.0] * 128,
        spectral_flux=0.2,
        timestamp=time.monotonic(),
    )
    a.set_simulation(frame)
    f = a.get_frame()
    assert 0.0 <= f.bass <= 1.0
    assert 0.0 <= f.mid <= 1.0
    assert 0.0 <= f.high <= 1.0


def test_spectrum_length():
    f = _zeroed_frame()
    assert len(f.spectrum) == 128


def test_waveform_values():
    f = _zeroed_frame()
    for v in f.waveform:
        assert -1.0 <= v <= 1.0


def test_simulation_injection():
    a = NullAudioAnalyzer()
    a.start()
    injected = AudioFrame(
        bass=0.9, mid=0.0, high=0.0,
        rms=0.9, peak=0.9,
        spectrum=[0.9] * 128,
        waveform=[0.5] * 128,
        spectral_flux=0.0,
        timestamp=time.monotonic(),
    )
    a.set_simulation(injected)
    assert a.get_frame() is injected


# ── Analysis tests (no hardware — use _analyse directly) ─────────────────────

@pytest.fixture
def analyzer():
    """AudioAnalyzer instance, not started (no hardware needed for _analyse)."""
    return AudioAnalyzer(sample_rate=44100, buffer_size=2048)


def _sine(freq_hz: float, sample_rate: int = 44100, n: int = 2048) -> np.ndarray:
    t = np.arange(n) / sample_rate
    return np.sin(2 * np.pi * freq_hz * t).astype(np.float32)


def test_spectral_flux_silent(analyzer):
    samples = np.zeros(2048, dtype=np.float32)
    f = analyzer._analyse(samples, time.monotonic())
    assert f.spectral_flux == 0.0


def test_list_devices_no_crash(analyzer):
    devices = analyzer.list_devices()
    assert isinstance(devices, list)


def test_analyze_sine_wave_bass(analyzer):
    samples = _sine(100.0)  # 100 Hz → bass
    f = analyzer._analyse(samples, time.monotonic())
    assert f.bass > 0.01, f"Expected bass energy for 100 Hz sine, got {f.bass}"
    assert f.high < f.bass, "High should be lower than bass for 100 Hz"


def test_analyze_sine_wave_high(analyzer):
    samples = _sine(8000.0)  # 8kHz → high
    f = analyzer._analyse(samples, time.monotonic())
    assert f.high > 0.01, f"Expected high energy for 8kHz sine, got {f.high}"
    assert f.bass < f.high, "Bass should be lower than high for 8kHz"


def test_thread_safety(analyzer):
    """100 concurrent get_frame() calls from different threads — no crash."""
    a = NullAudioAnalyzer()
    a.start()
    errors = []

    def reader():
        try:
            for _ in range(10):
                _ = a.get_frame()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=reader) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert not errors


def test_rms_silence(analyzer):
    samples = np.zeros(2048, dtype=np.float32)
    f = analyzer._analyse(samples, time.monotonic())
    assert f.rms == pytest.approx(0.0, abs=1e-5)


def test_rms_full_scale(analyzer):
    """Full-scale square wave → rms ≈ 1.0."""
    samples = np.ones(2048, dtype=np.float32)  # DC full-scale
    f = analyzer._analyse(samples, time.monotonic())
    # RMS of DC = 1.0, but we normalise by (1.0 + 1e-6), so very close
    assert f.rms > 0.9


def test_start_stop_lifecycle():
    """start() → get_frame() → stop() without crash — force_null for CI."""
    a = create_analyzer(force_null=True)
    result = a.start()
    assert result is True
    f = a.get_frame()
    assert isinstance(f, AudioFrame)
    a.stop()
    assert a.is_running is False
