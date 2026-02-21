"""
vjlive3.audio
=============
Real-time audio analysis and I/O for VJLive3.

Sub-modules (added as Phase 1 tasks complete):
    analyzer   — P1-A1: FFT + waveform analysis engine
    beat       — P1-A2: Real-time beat detection
    reactor    — P1-A3: Audio-reactive effect framework
    sources    — P1-A4: Multi-source audio input (sounddevice streams)

Import pattern — LAZY LOAD librosa:
    librosa triggers numba JIT compilation on first import (2-5 second hit).
    Import librosa inside analysis functions, never at module top-level.

Audio I/O uses sounddevice (NOT pyaudio — broken on Python 3.12).
All audio callbacks receive numpy arrays, never raw bytes.

Reference: VJlive-2/core/audio_analyzer.py, audio_reactor.py, audio/
"""
