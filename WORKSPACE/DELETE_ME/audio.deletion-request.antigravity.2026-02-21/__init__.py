"""Audio package for VJLive3."""
from vjlive3.audio.analyzer import (
    AudioFrame, AudioAnalyzerBase, AudioAnalyzer,
    NullAudioAnalyzer, create_analyzer,
)
from vjlive3.audio.beat_detector import BeatDetector, BeatState, create_beat_detector
from vjlive3.audio.reactivity import AudioFeature, ReactivityBus
from vjlive3.audio.sources import AudioDeviceInfo, AudioSourceManager

__all__ = [
    "AudioFrame", "AudioAnalyzerBase", "AudioAnalyzer",
    "NullAudioAnalyzer", "create_analyzer",
    "BeatDetector", "BeatState", "create_beat_detector",
    "AudioFeature", "ReactivityBus",
    "AudioDeviceInfo", "AudioSourceManager",
]
