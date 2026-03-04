"""
P1-A1 — Audio Analyzer
Spec: docs/specs/_02_fleshed_out/P1-A1_audio_analyzer.md
Tier: 🖥️ Pro-Tier Native

Classes:
  AudioAnalyzer      — threaded FFT feature extraction engine
  DummyAudioAnalyzer — synthetic beat simulation (fallback, no hardware)
  AudioReactor       — per-frame pull adapter for effects
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from typing import Callable, List, Optional

import numpy as np

from vjlive3.audio.features import AudioAnalyzerConfig, AudioDevice, AudioFeatures
from vjlive3.audio.beat import BeatDetector

logger = logging.getLogger(__name__)

_ALPHA_SLOW = 0.05   # smoothing constant for _smooth()


class _TemporalSmoother:
    """Exponential moving average for named float features."""

    def __init__(self, alpha: float = _ALPHA_SLOW) -> None:
        self._alpha = alpha
        self._state: dict = {}

    def smooth(self, name: str, value: float) -> float:
        if name not in self._state:
            self._state[name] = value
        else:
            self._state[name] = self._alpha * value + (1.0 - self._alpha) * self._state[name]
        return self._state[name]


# ---------------------------------------------------------------------------
# AudioAnalyzer — main engine
# ---------------------------------------------------------------------------

class AudioAnalyzer:
    """
    Real-time audio feature extraction.
    Uses numpy.fft (no pyfftw required).
    sounddevice imported lazily — falls back to DummyAudioAnalyzer when
    config.fallback_to_dummy=True and no device is available.
    """

    METADATA: dict = {"spec": "P1-A1", "tier": "Pro-Tier Native"}

    def __init__(self, config: Optional[AudioAnalyzerConfig] = None) -> None:
        self.config = config or AudioAnalyzerConfig()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        # Ring buffer (deque acts as sliding window)
        self._ring: deque = deque(
            maxlen=self.config.fft_size * 4,
        )
        for _ in range(self.config.fft_size):
            self._ring.append(0.0)

        # Hann window for FFT
        self._window = np.hanning(self.config.fft_size).astype(np.float32)
        self._freq_bins = np.fft.rfftfreq(self.config.fft_size, 1.0 / self.config.sample_rate)

        # Feature state
        self._latest: AudioFeatures = AudioFeatures.zero()
        self._history: deque = deque(maxlen=3600)  # 1 min at 60 Hz
        self._smoother = _TemporalSmoother()
        self._beat_detector = BeatDetector()

        # Plugin bus
        self._broadcaster: Optional[Callable] = None
        self._spectrum: np.ndarray = np.zeros(self.config.fft_size // 2 + 1)
        self._waveform: np.ndarray = np.zeros(self.config.buffer_size)

        # RMS / peak tracking
        self._peak: float = 0.0
        self._rms: float = 0.0
        self._clipping = False

    # ---- Device discovery --------------------------------------------------

    def list_input_devices(self) -> List[AudioDevice]:
        """Enumerate available microphone / line-in devices."""
        try:
            import sounddevice as sd  # lazy
            devices = []
            for i, dev in enumerate(sd.query_devices()):
                if dev["max_input_channels"] > 0:
                    devices.append(
                        AudioDevice(
                            id=i,
                            name=dev["name"],
                            channels=dev["max_input_channels"],
                            default_samplerate=dev["default_samplerate"],
                        )
                    )
            return devices
        except Exception as exc:
            logger.warning("list_input_devices failed: %s", exc)
            return []

    def select_input_device(self, device_id: int) -> bool:
        """Select input device. Returns False if device unavailable."""
        try:
            import sounddevice as sd  # lazy
            sd.check_input_settings(device=device_id)
            return True
        except Exception as exc:
            logger.error("select_input_device(%d): %s", device_id, exc)
            return False

    # ---- Lifecycle ---------------------------------------------------------

    def start(self) -> None:
        """Start background audio processing thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._processing_loop,
            name="AudioAnalyzer",
            daemon=True,
        )
        self._thread.start()
        logger.info("AudioAnalyzer: started")

    def stop(self) -> None:
        """Stop processing thread cleanly."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("AudioAnalyzer: stopped")

    def reset(self) -> None:
        """Reset all state without stopping the thread."""
        with self._lock:
            self._latest = AudioFeatures.zero()
            self._history.clear()
            self._smoother = _TemporalSmoother()
            self._beat_detector.reset()
            self._peak = 0.0
            self._rms = 0.0
            self._clipping = False

    # ---- Processing loop ---------------------------------------------------

    def _processing_loop(self) -> None:
        """Main loop: pull from ring buffer, run FFT, extract features."""
        fft_size = self.config.fft_size
        while self._running:
            # Grab latest fft_size samples from ring buffer
            with self._lock:
                buf = list(self._ring)[-fft_size:]
            if len(buf) < fft_size:
                time.sleep(0.001)
                continue

            audio = np.array(buf, dtype=np.float32)
            self._process_frame(audio)
            time.sleep(1.0 / self.config.broadcast_rate)

    def _process_frame(self, audio: np.ndarray) -> None:
        """Single FFT + feature extraction pass."""
        # Peak / RMS / clipping
        self._rms = float(np.sqrt(np.mean(audio ** 2)))
        self._peak = float(np.max(np.abs(audio)))
        self._clipping = self._peak >= 0.99

        # FFT
        windowed = audio * self._window
        spectrum = np.abs(np.fft.rfft(windowed))
        self._spectrum = spectrum

        # Update waveform buffer
        self._waveform = audio[-self.config.buffer_size:]

        # Band energies (20–150 / 150–2000 / 2000–20000 Hz), normalised
        freqs = self._freq_bins
        bass_idx = np.where((freqs >= 20) & (freqs < 150))[0]
        mid_idx = np.where((freqs >= 150) & (freqs < 2000))[0]
        high_idx = np.where((freqs >= 2000))[0]

        def _band_energy(idx: np.ndarray) -> float:
            if len(idx) == 0:
                return 0.0
            raw = float(np.mean(spectrum[idx] ** 2))
            return min(1.0, raw ** 0.5)

        bass = _band_energy(bass_idx)
        mid = _band_energy(mid_idx)
        high = _band_energy(high_idx)
        volume = min(1.0, self._rms)

        # Beat detection
        beat_result = self._beat_detector.process_frame(spectrum)

        # Spectral centroid (normalised 0-1)
        total = float(np.sum(spectrum))
        centroid = 0.0
        if total > 0:
            centroid = min(1.0, float(np.sum(freqs * spectrum)) / (total * 24000))

        # Smoothed features
        bass_s = self._smoother.smooth("bass", bass)
        mid_s = self._smoother.smooth("mid", mid)
        high_s = self._smoother.smooth("high", high)
        vol_s = self._smoother.smooth("volume", volume)

        features = AudioFeatures(
            timestamp=time.time(),
            beat=beat_result.beat,
            beat_confidence=beat_result.beat_confidence,
            onset=beat_result.beat,
            onset_confidence=beat_result.beat_confidence,
            bass=bass,
            mid=mid,
            high=high,
            volume=volume,
            spectral_centroid=centroid,
            bass_smooth=bass_s,
            mid_smooth=mid_s,
            high_smooth=high_s,
            volume_smooth=vol_s,
            bpm=beat_result.tempo,
            beat_phase=beat_result.phase,
        )

        with self._lock:
            self._latest = features
            self._history.append(features)

        if self._broadcaster is not None:
            try:
                self._broadcaster(features.to_dict())
            except Exception as exc:
                logger.debug("AudioAnalyzer broadcaster: %s", exc)

    # ---- Public read API ---------------------------------------------------

    def get_latest_features(self) -> AudioFeatures:
        with self._lock:
            return self._latest

    def get_feature_history(self, duration_seconds: float) -> List[AudioFeatures]:
        cutoff = time.time() - duration_seconds
        with self._lock:
            return [f for f in self._history if f.timestamp >= cutoff]

    def set_plugin_bus(self, bus: object) -> None:
        """Connect to plugin bus. Bus must have a publish(topic, data) method."""
        self._broadcaster = lambda data: bus.publish("audio_features", data)

    def get_signal_flow_manager(self) -> None:
        return None  # Placeholder — P1-A4 AudioSourceManager handles routing

    def get_spectrum_data(self) -> np.ndarray:
        return self._spectrum.copy()

    def get_waveform_data(self) -> np.ndarray:
        return self._waveform.copy()

    def get_peak_level(self) -> float:
        return self._peak

    def get_rms_level(self) -> float:
        return self._rms

    def is_clipping(self) -> bool:
        return self._clipping

    def get_latency(self) -> float:
        """Approximate end-to-end latency in seconds based on buffer size."""
        return self.config.buffer_size / self.config.sample_rate

    def write_audio(self, audio: np.ndarray) -> None:
        """
        Push raw audio samples into the ring buffer.
        Called by sounddevice callback or test harness.
        """
        with self._lock:
            self._ring.extend(audio.tolist())


# ---------------------------------------------------------------------------
# DummyAudioAnalyzer — synthetic fallback (no hardware)
# ---------------------------------------------------------------------------

class DummyAudioAnalyzer(AudioAnalyzer):
    """
    Generates synthetic audio features at 120 BPM.
    Used when no audio device is available (config.fallback_to_dummy=True).
    """

    METADATA: dict = {"spec": "P1-A1", "tier": "Pro-Tier Native", "dummy": True}

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._simulate_loop,
            name="DummyAudioAnalyzer",
            daemon=True,
        )
        self._thread.start()
        logger.info("DummyAudioAnalyzer: started (no audio device)")

    def _simulate_loop(self) -> None:
        """Generate synthetic features at ~60 Hz."""
        while self._running:
            t = time.time()
            phase = (t % 0.5) / 0.5  # 120 BPM = 0.5 s/beat
            beat = phase < 0.1

            features = AudioFeatures(
                timestamp=t,
                beat=beat,
                beat_confidence=0.8 if beat else 0.0,
                onset=beat,
                onset_confidence=0.7 if beat else 0.0,
                bass=0.5 + 0.3 * float(np.sin(phase * 2 * np.pi)),
                mid=0.3,
                high=0.2,
                volume=0.4,
                spectral_centroid=0.3,
                spectral_rolloff=0.4,
                bass_smooth=0.5,
                mid_smooth=0.3,
                high_smooth=0.2,
                volume_smooth=0.4,
                bpm=120.0,
                beat_phase=phase,
                percussive=0.7 if beat else 0.3,
            )
            with self._lock:
                self._latest = features
                self._history.append(features)

            time.sleep(1.0 / 60.0)


# ---------------------------------------------------------------------------
# AudioReactor — per-frame pull adapter for effects
# ---------------------------------------------------------------------------

class AudioReactor:
    """
    Wraps an AudioAnalyzer for per-frame feature consumption by effects.
    Call update() once per frame, then use get_feature() / get_band_energy().
    """

    def __init__(self, analyzer: AudioAnalyzer) -> None:
        self._analyzer = analyzer
        self._current: Optional[AudioFeatures] = None

    def update(self) -> None:
        """Pull latest features from the analyzer."""
        self._current = self._analyzer.get_latest_features()

    def get_feature(self, name: str, default: float = 0.0) -> float:
        """Return a named feature value (float) or default if unavailable."""
        if self._current is None:
            return default
        return float(getattr(self._current, name, default))

    def get_band_energy(self, band: str) -> float:
        """Return smoothed band energy for 'bass', 'mid', or 'high'."""
        mapping = {"bass": "bass_smooth", "mid": "mid_smooth", "high": "high_smooth"}
        return self.get_feature(mapping.get(band, band))
