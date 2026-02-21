"""P1-A1 — FFT + Waveform Analysis Engine

Real-time audio analysis for VJLive3 VJ reactivity system.
Captures PCM via PyAudio, runs scipy rfft, extracts bass/mid/high band energies,
RMS amplitude, spectral flux, and waveform data into an immutable AudioFrame.

Falls back to NullAudioAnalyzer when PyAudio is unavailable (CI/headless mode).

Spec: docs/specs/P1-A1_audio_analyzer.md
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

_log = logging.getLogger(__name__)

# ── Optional dependencies ─────────────────────────────────────────────────────
try:
    import pyaudio as _pyaudio
    _HAS_PYAUDIO = True
except ImportError:
    _pyaudio = None  # type: ignore[assignment]
    _HAS_PYAUDIO = False
    _log.warning("pyaudio not installed — AudioAnalyzer will use NullAudioAnalyzer")

try:
    from scipy.fft import rfft as _rfft, rfftfreq as _rfftfreq
    _HAS_SCIPY = True
except ImportError:
    _rfft = None  # type: ignore[assignment]
    _rfftfreq = None  # type: ignore[assignment]
    _HAS_SCIPY = False
    _log.warning("scipy not installed — falling back to numpy FFT")


# ── Public data types ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AudioFrame:
    """Immutable snapshot of one audio analysis tick.

    All normalised values are clamped to 0.0–1.0 unless noted.
    """
    # Frequency band energies
    bass: float           # 20–250 Hz
    mid: float            # 250–4000 Hz
    high: float           # 4000–20000 Hz
    # Amplitude
    rms: float            # root-mean-square (0.0–1.0)
    peak: float           # peak absolute amplitude (0.0–1.0)
    # Spectral
    spectrum: List[float]     # 128 FFT magnitude bins (0.0–1.0)
    waveform: List[float]     # downsampled time-domain (-1.0–1.0)
    spectral_flux: float      # positive spectral change rate (0.0–1.0)
    # Timing
    timestamp: float          # time.monotonic() at capture


def _zeroed_frame() -> AudioFrame:
    return AudioFrame(
        bass=0.0, mid=0.0, high=0.0,
        rms=0.0, peak=0.0,
        spectrum=[0.0] * 128,
        waveform=[0.0] * 128,
        spectral_flux=0.0,
        timestamp=time.monotonic(),
    )


# ── Abstract base ─────────────────────────────────────────────────────────────

class AudioAnalyzerBase:
    """Abstract base — allows hot-swap between real and null implementations."""

    def start(self) -> bool: ...
    def stop(self) -> None: ...
    def get_frame(self) -> AudioFrame: ...
    def set_simulation(self, frame: AudioFrame) -> None: ...

    @property
    def is_running(self) -> bool: ...            # type: ignore[return]

    @property
    def sample_rate(self) -> int: ...            # type: ignore[return]

    @property
    def buffer_size(self) -> int: ...            # type: ignore[return]


# ── NullAudioAnalyzer — hardware-free fallback ────────────────────────────────

class NullAudioAnalyzer(AudioAnalyzerBase):
    """Returns zeroed AudioFrames with no hardware dependency.

    Used in CI, headless servers, and when PyAudio/scipy are absent.
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        buffer_size: int = 2048,
    ) -> None:
        self._sample_rate = sample_rate
        self._buffer_size = buffer_size
        self._running = False
        self._sim_frame: Optional[AudioFrame] = None

    def start(self) -> bool:
        self._running = True
        return True

    def stop(self) -> None:
        self._running = False

    def get_frame(self) -> AudioFrame:
        if self._sim_frame is not None:
            return self._sim_frame
        return _zeroed_frame()

    def set_simulation(self, frame: AudioFrame) -> None:
        self._sim_frame = frame

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def buffer_size(self) -> int:
        return self._buffer_size


# ── Real AudioAnalyzer ────────────────────────────────────────────────────────

class AudioAnalyzer(AudioAnalyzerBase):
    """Real-time audio analysis engine using PyAudio + scipy/numpy FFT.

    Thread-safe: PyAudio callback writes to a lock-protected slot; main thread
    reads via get_frame() without blocking.

    Falls back silently to simulation mode if hardware is unavailable.
    """

    # Frequency band definitions (Hz)
    _BASS_LO, _BASS_HI   = 20,   250
    _MID_LO,  _MID_HI    = 250,  4000
    _HIGH_LO, _HIGH_HI   = 4000, 20000
    _TARGET_BINS          = 128
    _ANALYSIS_INTERVAL    = 1.0 / 60   # max 60 analyses/sec

    def __init__(
        self,
        sample_rate: int = 44100,
        buffer_size: int = 2048,
        device_index: Optional[int] = None,
    ) -> None:
        self._sample_rate = sample_rate
        self._buffer_size = buffer_size
        self._device_index = device_index

        self._lock = threading.RLock()
        self._running = False
        self._stream: Optional[Any] = None
        self._pa: Optional[Any] = None

        self._current_frame: AudioFrame = _zeroed_frame()
        self._prev_spectrum: np.ndarray = np.zeros(self._TARGET_BINS)
        self._sim_frame: Optional[AudioFrame] = None
        self._last_analysis_t: float = 0.0
        self._error_recovery_count: int = 0
        self._MAX_ERRORS = 3

        # Pre-compute FFT frequency masks
        self._freqs = (
            _rfftfreq(buffer_size, 1.0 / sample_rate)
            if _HAS_SCIPY else
            np.fft.rfftfreq(buffer_size, 1.0 / sample_rate)
        )
        self._bass_mask = (self._freqs >= self._BASS_LO) & (self._freqs <= self._BASS_HI)
        self._mid_mask  = (self._freqs >= self._MID_LO)  & (self._freqs <= self._MID_HI)
        self._high_mask = (self._freqs >= self._HIGH_LO) & (self._freqs <= self._HIGH_HI)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> bool:
        if not _HAS_PYAUDIO:
            _log.warning("PyAudio unavailable — entering simulation mode")
            self._running = True
            return False

        try:
            self._pa = _pyaudio.PyAudio()
            self._stream = self._pa.open(
                format=_pyaudio.paFloat32,
                channels=1,
                rate=self._sample_rate,
                input=True,
                frames_per_buffer=self._buffer_size,
                input_device_index=self._device_index,
                stream_callback=self._audio_callback,
            )
            self._stream.start_stream()
            self._running = True
            _log.info(
                "AudioAnalyzer started: %dHz, %d-frame buffer",
                self._sample_rate, self._buffer_size,
            )
            return True
        except Exception as exc:
            _log.warning("AudioAnalyzer: hardware init failed (%s) — simulation mode", exc)
            self._cleanup_pa()
            self._running = True  # still "running" but with zeroed frames
            return False

    def stop(self) -> None:
        self._running = False
        self._cleanup_pa()

    def _cleanup_pa(self) -> None:
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._pa:
            try:
                self._pa.terminate()
            except Exception:
                pass
            self._pa = None

    # ── Frame access ──────────────────────────────────────────────────────────

    def get_frame(self) -> AudioFrame:
        """Return last AudioFrame. Thread-safe, never blocks, never raises."""
        if self._sim_frame is not None:
            return self._sim_frame
        with self._lock:
            return self._current_frame

    def set_simulation(self, frame: AudioFrame) -> None:
        self._sim_frame = frame

    def list_devices(self) -> List[Dict]:
        """Return available audio input devices. Empty list if PyAudio unavailable."""
        if not _HAS_PYAUDIO:
            return []
        pa = None
        try:
            pa = _pyaudio.PyAudio()
            devices = []
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0:
                    devices.append({
                        "index": i,
                        "name": info.get("name"),
                        "max_input_channels": info.get("maxInputChannels"),
                        "default_sample_rate": info.get("defaultSampleRate"),
                    })
            return devices
        except Exception as exc:
            _log.error("list_devices failed: %s", exc)
            return []
        finally:
            if pa:
                try: pa.terminate()
                except Exception: pass

    # ── PyAudio callback ──────────────────────────────────────────────────────

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Called by PyAudio on its own thread."""
        now = time.monotonic()
        # Rate-limit analysis to 60fps
        if now - self._last_analysis_t < self._ANALYSIS_INTERVAL:
            pa_continue = _pyaudio.paContinue if _HAS_PYAUDIO else 0
            return (None, pa_continue)

        if in_data:
            try:
                samples = np.frombuffer(in_data, dtype=np.float32)
                if len(samples) == 0:
                    return (None, _pyaudio.paContinue)
                frame = self._analyse(samples, now)
                with self._lock:
                    self._current_frame = frame
                self._last_analysis_t = now
                self._error_recovery_count = 0
            except Exception as exc:
                self._error_recovery_count += 1
                if self._error_recovery_count <= self._MAX_ERRORS:
                    _log.error("Audio analysis error (%d/%d): %s",
                               self._error_recovery_count, self._MAX_ERRORS, exc)
                # Keep returning last good frame

        pa_continue = _pyaudio.paContinue if _HAS_PYAUDIO else 0
        return (None, pa_continue)

    # ── Analysis core ──────────────────────────────────────────────────────────

    def _analyse(self, samples: np.ndarray, timestamp: float) -> AudioFrame:
        # Pad or truncate to buffer_size
        if len(samples) < self._buffer_size:
            samples = np.pad(samples, (0, self._buffer_size - len(samples)))
        else:
            samples = samples[:self._buffer_size]

        # FFT
        if _HAS_SCIPY:
            raw_fft = _rfft(samples)
        else:
            raw_fft = np.fft.rfft(samples)
        magnitudes = np.abs(raw_fft)

        # Normalise
        max_mag = np.max(magnitudes) + 1e-6
        norm_mag = magnitudes / max_mag

        # Band energies
        def band_energy(mask: np.ndarray) -> float:
            vals = norm_mag[mask]
            return float(np.mean(vals)) if len(vals) > 0 else 0.0

        bass  = float(np.clip(band_energy(self._bass_mask), 0.0, 1.0))
        mid   = float(np.clip(band_energy(self._mid_mask),  0.0, 1.0))
        high  = float(np.clip(band_energy(self._high_mask), 0.0, 1.0))

        # Amplitude
        rms  = float(np.clip(np.sqrt(np.mean(samples ** 2)) / (1.0 + 1e-6), 0.0, 1.0))
        peak = float(np.clip(np.max(np.abs(samples)), 0.0, 1.0))

        # 128-bin spectrum (resample/interpolate from full FFT)
        full_len = len(norm_mag)
        if full_len >= self._TARGET_BINS:
            idxs = np.linspace(0, full_len - 1, self._TARGET_BINS, dtype=int)
            spectrum = norm_mag[idxs].tolist()
        else:
            spectrum = list(np.interp(
                np.linspace(0, full_len - 1, self._TARGET_BINS),
                np.arange(full_len), norm_mag,
            ))

        # Waveform (downsample by 4, take first 128 samples)
        step = max(1, len(samples) // 128)
        waveform = samples[::step][:128].tolist()
        if len(waveform) < 128:
            waveform = waveform + [0.0] * (128 - len(waveform))

        # Spectral flux (positive half-wave rectified)
        spectrum_arr = np.array(spectrum)
        flux_raw = float(np.sum(np.maximum(spectrum_arr - self._prev_spectrum, 0.0)))
        spectral_flux = float(np.clip(flux_raw / (max_mag + 1e-6), 0.0, 1.0))
        self._prev_spectrum = spectrum_arr

        return AudioFrame(
            bass=bass, mid=mid, high=high,
            rms=rms, peak=peak,
            spectrum=[float(np.clip(v, 0.0, 1.0)) for v in spectrum],
            waveform=[float(np.clip(v, -1.0, 1.0)) for v in waveform],
            spectral_flux=spectral_flux,
            timestamp=timestamp,
        )

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def buffer_size(self) -> int:
        return self._buffer_size


# ── Factory ───────────────────────────────────────────────────────────────────

def create_analyzer(
    sample_rate: int = 44100,
    buffer_size: int = 2048,
    device_index: Optional[int] = None,
    force_null: bool = False,
) -> AudioAnalyzerBase:
    """Return AudioAnalyzer if hardware+deps available, else NullAudioAnalyzer.

    Args:
        force_null: Always return NullAudioAnalyzer (useful for CI).
    """
    if force_null or not _HAS_PYAUDIO or not _HAS_SCIPY:
        if force_null:
            _log.debug("create_analyzer: force_null=True")
        else:
            _log.warning("create_analyzer: missing deps — returning NullAudioAnalyzer")
        return NullAudioAnalyzer(sample_rate=sample_rate, buffer_size=buffer_size)
    return AudioAnalyzer(
        sample_rate=sample_rate,
        buffer_size=buffer_size,
        device_index=device_index,
    )


__all__ = [
    "AudioFrame", "AudioAnalyzerBase", "AudioAnalyzer",
    "NullAudioAnalyzer", "create_analyzer",
]
