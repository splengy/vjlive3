"""
P1-A1 — Audio Feature Dataclasses
Spec: docs/specs/_02_fleshed_out/P1-A1_audio_analyzer.md

Pure data types — no GPU, no audio device, no heavy imports.
Safe to import anywhere.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AudioDevice:
    """Represents a discovered audio input device."""

    id: int
    name: str
    channels: int
    default_samplerate: float


@dataclass
class AudioAnalyzerConfig:
    """Configuration for AudioAnalyzer. All fields have safe defaults."""

    sample_rate: int = 48000
    fft_size: int = 2048
    buffer_size: int = 1024
    hop_size: int = 512
    smoothing_time: float = 0.1          # seconds
    broadcast_rate: float = 60.0         # Hz
    enable_pitch_tracking: bool = True
    enable_beat_detection: bool = True
    enable_onset_detection: bool = True
    enable_loudness_metering: bool = True
    fallback_to_dummy: bool = True


@dataclass
class AudioFeatures:
    """
    Container for all extracted audio features.
    Spec: P1-A1 — AudioFeatures dataclass.

    All float fields are normalised 0.0-1.0 unless noted.
    """

    # Timing
    timestamp: float = field(default_factory=time.time)

    # Beat / onset
    beat: bool = False
    beat_confidence: float = 0.0
    onset: bool = False
    onset_confidence: float = 0.0

    # Frequency bands (normalised)
    bass: float = 0.0       # 20-150 Hz
    mid: float = 0.0        # 150-2000 Hz
    high: float = 0.0       # 2000-20000 Hz
    volume: float = 0.0     # RMS overall

    # Pitch
    pitch: float = 0.0              # Hz (0 = unpitched)
    pitch_confidence: float = 0.0

    # Spectral features (normalised)
    spectral_centroid: float = 0.0
    spectral_rolloff: float = 0.0
    spectral_flux: float = 0.0
    zero_crossing_rate: float = 0.0
    harmony: float = 0.0
    percussive: float = 0.0

    # Smoothed (EMA)
    bass_smooth: float = 0.0
    mid_smooth: float = 0.0
    high_smooth: float = 0.0
    volume_smooth: float = 0.0

    # BPM / phase
    bpm: float = 120.0
    beat_phase: float = 0.0

    # EBU R128 loudness (LUFS / LU)
    loudness_integrated: float = -23.0
    loudness_shortterm: float = -20.0
    loudness_range: float = 10.0

    @classmethod
    def zero(cls) -> "AudioFeatures":
        """Return a feature container with all values at zero / safe defaults."""
        return cls()

    def to_dict(self) -> dict:
        """Serialise to plain dict for plugin bus broadcast."""
        return {
            "timestamp": self.timestamp,
            "beat": self.beat,
            "beat_confidence": self.beat_confidence,
            "onset": self.onset,
            "onset_confidence": self.onset_confidence,
            "bass": self.bass,
            "mid": self.mid,
            "high": self.high,
            "volume": self.volume,
            "pitch": self.pitch,
            "pitch_confidence": self.pitch_confidence,
            "spectral_centroid": self.spectral_centroid,
            "spectral_rolloff": self.spectral_rolloff,
            "spectral_flux": self.spectral_flux,
            "zero_crossing_rate": self.zero_crossing_rate,
            "harmony": self.harmony,
            "percussive": self.percussive,
            "bass_smooth": self.bass_smooth,
            "mid_smooth": self.mid_smooth,
            "high_smooth": self.high_smooth,
            "volume_smooth": self.volume_smooth,
            "bpm": self.bpm,
            "beat_phase": self.beat_phase,
            "loudness_integrated": self.loudness_integrated,
            "loudness_shortterm": self.loudness_shortterm,
            "loudness_range": self.loudness_range,
        }
