"""
Audio Analysis pipeline.
Extracts FFT, bands, RMS and checks for beats.
"""

import time
import numpy as np
import logging
from typing import Tuple

from .config import AudioConfig
from .source import AudioFeatures

logger = logging.getLogger(__name__)

class AudioAnalyzer:
    """
    Stateful analyzer that processes chunks of audio data.
    Maintains beat history and previous spectrum for onset detection.
    """
    
    def __init__(self, config: AudioConfig):
        self.config = config
        
        # Pre-calculate frequency bin indices for bands
        nyquist = self.config.sample_rate / 2.0
        n_bins = self.config.fft_resolution // 2 + 1
        freqs = np.linspace(0, nyquist, n_bins)
        
        self._bass_idx = np.where((freqs >= config.bass_range[0]) & (freqs <= config.bass_range[1]))[0]
        self._mid_idx = np.where((freqs >= config.mid_range[0]) & (freqs <= config.mid_range[1]))[0]
        self._treble_idx = np.where((freqs >= config.high_range[0]) & (freqs <= config.high_range[1]))[0]
        
        # State for beat detection
        self._prev_spectrum = np.zeros(n_bins, dtype=np.float32)
        self._spectral_flux_history = np.zeros(30, dtype=np.float32) # History for dynamic thresholding
        self._history_idx = 0
        self._last_beat_time = 0.0
        
        # Window function to reduce spectral leakage
        self._window = np.hanning(self.config.buffer_size)
        
    def analyze(self, audio_data: np.ndarray) -> AudioFeatures:
        """
        Process a single buffer of audio and return features.
        audio_data is assumed to be float32 in [-1.0, 1.0].
        """
        features = AudioFeatures()
        
        if len(audio_data) == 0:
            return features
            
        # Pad or truncate to expected buffer size
        if len(audio_data) < self.config.buffer_size:
            audio_data = np.pad(audio_data, (0, self.config.buffer_size - len(audio_data)))
        elif len(audio_data) > self.config.buffer_size:
            audio_data = audio_data[:self.config.buffer_size]
            
        # Time-domain features
        features.rms = float(np.sqrt(np.mean(audio_data ** 2)))
        features.peak = float(np.max(np.abs(audio_data)))
        
        # Frequency-domain (FFT)
        windowed = audio_data * self._window
        
        # Compute rfft
        fft_result = np.fft.rfft(windowed, n=self.config.fft_resolution)
        magnitude = np.abs(fft_result) * 2.0 / self.config.buffer_size # Normalize
        
        # Update bands
        if len(self._bass_idx) > 0:
            features.bass = float(np.mean(magnitude[self._bass_idx]))
        if len(self._mid_idx) > 0:
            features.mid = float(np.mean(magnitude[self._mid_idx]))
        if len(self._treble_idx) > 0:
            features.treble = float(np.mean(magnitude[self._treble_idx]))
            
        # Downsample spectrum for the 128-bin output representation
        num_output_bins = 128
        # We only care about the lower frequency range for visualization usually (up to ~10kHz)
        max_viz_bin = min(len(magnitude), int(10000 / (self.config.sample_rate / self.config.fft_resolution)))
        viz_bins = magnitude[:max_viz_bin]
        
        # Decimate/interpolate to exactly 128 bins
        if len(viz_bins) > 0:
             indices = np.linspace(0, len(viz_bins) - 1, num_output_bins).astype(int)
             features.spectrum = viz_bins[indices]
             
        # Beat Detection (Spectral Flux)
        if self.config.enable_beat_detection:
            self._detect_beat(magnitude, features)
            
        self._prev_spectrum = magnitude.copy()
        
        return features

    def _detect_beat(self, current_spectrum: np.ndarray, features: AudioFeatures) -> None:
        """Simple onset detection via spectral flux."""
        current_time = time.time()
        
        # Calculate positive difference
        flux = np.sum(np.maximum(0, current_spectrum - self._prev_spectrum))
        
        # Update history
        self._spectral_flux_history[self._history_idx] = flux
        self._history_idx = (self._history_idx + 1) % len(self._spectral_flux_history)
        
        # Threshold is mean of history + some multiplier
        mean_flux = np.mean(self._spectral_flux_history)
        std_flux = np.std(self._spectral_flux_history)
        threshold = mean_flux + (1.5 * std_flux) + 0.05 # Add tiny offset to prevent noise floor triggering
        
        # Must be separated by at least 150ms (~400 BPM max)
        time_since_last = current_time - self._last_beat_time
        
        if flux > threshold and flux > 0.1 and time_since_last > 0.15:
            features.is_beat = True
            self._last_beat_time = current_time
        else:
            features.is_beat = False
            
        # Estimate coarse beat phase (0.0 to 1.0)
        # Assumes 120bpm for generic decay
        decay_time = 0.5 # 500ms
        phase = 1.0 - min(1.0, time_since_last / decay_time)
        features.beat_phase = max(0.0, phase)
