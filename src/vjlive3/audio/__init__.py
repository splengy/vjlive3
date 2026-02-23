"""
VJLive3 Core Audio Infrastructure
Handles multi-source capture, FFT analysis, beat detection, and synchronization.
"""

from .config import AudioConfig, AudioSourceType, AudioDeviceConfig

__all__ = [
    "AudioConfig",
    "AudioSourceType",
    "AudioDeviceConfig"
]
