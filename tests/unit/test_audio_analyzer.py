"""Tests for AudioAnalyzer."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import numpy as np
import pytest
from vjlive3.audio.analyzer import AudioAnalyzer


def _sine(freq_hz: float, duration_samples: int, sr: int = 44100) -> np.ndarray:
    t = np.arange(duration_samples) / sr
    return np.sin(2 * np.pi * freq_hz * t).astype(np.float32)


def test_spectrum_shape():
    a = AudioAnalyzer(fft_size=1024)
    a.update(_sine(440, 1024))
    assert a.spectrum.shape == (513,)  # fft_size // 2 + 1


def test_sine_energy_in_correct_bin():
    """440 Hz sine should register in mids more than highs."""
    a = AudioAnalyzer(sample_rate=44100, fft_size=2048)
    a.update(_sine(440, 2048))
    # Normalised spectrum: most bins ≈ 0; mids > highs is the key invariant
    assert a.mids > a.highs, "440 Hz sine: mids should exceed highs"
    assert a.mids > 0.0, "440 Hz sine should have non-zero mids energy"


def test_rms_silence():
    a = AudioAnalyzer(fft_size=1024)
    a.update(np.zeros(1024, dtype=np.float32))
    assert a.rms == pytest.approx(0.0, abs=1e-6)


def test_rms_full_scale():
    a = AudioAnalyzer(fft_size=1024)
    a.update(np.ones(1024, dtype=np.float32))
    assert a.rms == pytest.approx(1.0, abs=1e-4)


def test_frequency_band_returns_expected():
    a = AudioAnalyzer(sample_rate=44100, fft_size=2048)
    a.update(_sine(100, 2048))           # 100 Hz → bass
    bass = a.frequency_band(20, 250)
    highs = a.frequency_band(4000, 20000)
    assert bass > highs, "100 Hz sine: bass should dominate highs"


def test_short_sample_no_crash():
    """Fewer samples than fft_size shouldn't raise."""
    a = AudioAnalyzer(fft_size=2048)
    a.update(np.zeros(512, dtype=np.float32))  # shorter than fft_size


def test_fft_size_not_power_of_two_raises():
    with pytest.raises(ValueError):
        AudioAnalyzer(fft_size=1000)
