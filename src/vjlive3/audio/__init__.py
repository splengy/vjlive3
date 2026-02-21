"""Audio engine for VJLive3.

Exports:
    AudioAnalyzer    — real-time FFT analysis
    BeatDetector     — onset / BPM estimation
    ReactivityBus    — shared audio snapshot bus for effects
    AudioSnapshot    — immutable data snapshot consumed by effects
    NullAudioSource  — silence (CI/headless safe)
    FileAudioSource  — WAV file input
    SystemAudioSource — live microphone / sounddevice input
"""

from vjlive3.audio.analyzer import AudioAnalyzer
from vjlive3.audio.beat_detector import BeatDetector
from vjlive3.audio.reactivity_bus import ReactivityBus, AudioSnapshot
from vjlive3.audio.sources import AudioSource, NullAudioSource, FileAudioSource

__all__ = [
    "AudioAnalyzer",
    "BeatDetector",
    "ReactivityBus",
    "AudioSnapshot",
    "AudioSource",
    "NullAudioSource",
    "FileAudioSource",
]
