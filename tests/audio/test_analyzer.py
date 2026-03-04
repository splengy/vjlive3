"""Tests for P1-A1 — AudioAnalyzer, DummyAudioAnalyzer, AudioReactor (analyzer.py)"""
import time
import threading
import numpy as np
import pytest
from vjlive3.audio.analyzer import AudioAnalyzer, DummyAudioAnalyzer, AudioReactor
from vjlive3.audio.features import AudioAnalyzerConfig, AudioFeatures


# ---- DummyAudioAnalyzer --------------------------------------------------

def test_dummy_start_stop():
    """DummyAudioAnalyzer starts and stops cleanly without error."""
    da = DummyAudioAnalyzer()
    da.start()
    assert da._running is True
    da.stop()
    assert da._running is False


def test_dummy_produces_features():
    """After ~100ms, DummyAudioAnalyzer provides non-zero features."""
    da = DummyAudioAnalyzer()
    da.start()
    time.sleep(0.15)
    f = da.get_latest_features()
    da.stop()
    assert isinstance(f, AudioFeatures)
    assert f.bpm == pytest.approx(120.0)
    # Beat phase should have advanced
    assert f.timestamp > 0


def test_dummy_idempotent_start():
    """Calling start() twice is a no-op (does not create extra threads)."""
    da = DummyAudioAnalyzer()
    da.start()
    da.start()  # should not raise
    assert da._running is True
    da.stop()


# ---- AudioAnalyzer -------------------------------------------------------

def test_analyzer_write_audio():
    """write_audio() feeds samples into ring buffer without error."""
    cfg = AudioAnalyzerConfig(fft_size=256, buffer_size=64)
    a = AudioAnalyzer(config=cfg)
    audio = np.random.randn(256).astype(np.float32)
    a.write_audio(audio)
    # Ring buffer should now have data
    assert len(a._ring) >= 256


def test_analyzer_get_latest_zero():
    """Before start(), get_latest_features returns zero-valued features."""
    a = AudioAnalyzer()
    f = a.get_latest_features()
    assert f.beat is False
    assert f.bass == pytest.approx(0.0)


def test_analyzer_get_spectrum():
    """get_spectrum_data returns a numpy ndarray."""
    a = AudioAnalyzer()
    spec = a.get_spectrum_data()
    assert isinstance(spec, np.ndarray)


def test_analyzer_get_waveform():
    """get_waveform_data returns a numpy ndarray."""
    a = AudioAnalyzer()
    wave = a.get_waveform_data()
    assert isinstance(wave, np.ndarray)


def test_analyzer_peak_rms():
    """After write + _process_frame, peak and rms are set."""
    cfg = AudioAnalyzerConfig(fft_size=256, buffer_size=64)
    a = AudioAnalyzer(config=cfg)
    audio = np.ones(256, dtype=np.float32) * 0.5
    a.write_audio(audio)
    a._process_frame(audio)
    assert a.get_peak_level() == pytest.approx(0.5, rel=0.01)
    assert a.get_rms_level() == pytest.approx(0.5, rel=0.01)
    assert a.is_clipping() is False


def test_analyzer_clipping():
    """Amplitude >= 0.99 is detected as clipping."""
    cfg = AudioAnalyzerConfig(fft_size=256)
    a = AudioAnalyzer(config=cfg)
    hot = np.ones(256, dtype=np.float32)  # max amplitude = 1.0
    a._process_frame(hot)
    assert a.is_clipping() is True


def test_analyzer_latency():
    """get_latency returns a positive float."""
    a = AudioAnalyzer()
    lat = a.get_latency()
    assert lat > 0.0


def test_analyzer_feature_history():
    """get_feature_history returns a list."""
    cfg = AudioAnalyzerConfig(fft_size=256)
    a = AudioAnalyzer(config=cfg)
    audio = np.random.randn(256).astype(np.float32)
    a._process_frame(audio)
    hist = a.get_feature_history(1.0)
    assert isinstance(hist, list)
    assert len(hist) >= 1


# ---- AudioReactor --------------------------------------------------------

def test_audio_reactor_update():
    """reactor.update() calls the analyzer and stores features."""
    da = DummyAudioAnalyzer()
    da.start()
    time.sleep(0.1)
    reactor = AudioReactor(da)
    reactor.update()
    da.stop()
    assert reactor._current is not None


def test_audio_reactor_band_energy():
    """get_band_energy('bass'/'mid'/'high') returns values in [0,1]."""
    da = DummyAudioAnalyzer()
    da.start()
    time.sleep(0.1)
    reactor = AudioReactor(da)
    reactor.update()
    da.stop()
    for band in ("bass", "mid", "high"):
        e = reactor.get_band_energy(band)
        assert 0.0 <= e <= 1.0, f"band '{band}' energy {e} out of range"
