"""
VJLive3 Core Audio Infrastructure
Handles multi-source capture, FFT analysis, beat detection, and synchronization.
"""

from .config import AudioConfig, AudioSourceType, AudioDeviceConfig
from .source import AudioSource, MicrophoneSource, DummySource, AudioFeatures
from .analyzer import AudioAnalyzer
from .engine import AudioEngine

__all__ = [
    "AudioConfig",
    "AudioSourceType",
    "AudioDeviceConfig",
    "AudioSource",
    "MicrophoneSource",
    "DummySource",
    "AudioFeatures",
    "AudioAnalyzer",
    "AudioEngine"
]
