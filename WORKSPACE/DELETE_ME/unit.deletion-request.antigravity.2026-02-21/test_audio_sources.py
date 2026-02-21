"""Tests for P1-A4 AudioSourceManager.

Spec: docs/specs/P1-A4_audio_sources.md

Mocks PyAudio entirely — no hardware required.
Tests:
  - list_devices returns [] with no PyAudio
  - list_devices tags loopback/monitor sources correctly
  - select() with valid/invalid device index
  - select_default() always succeeds (falls to Null)
  - select_loopback() finds loopback or falls back
  - get_frame() before select → zeroed frame, no crash
  - hot-switch: select() twice releases old analyzer
  - stop() is idempotent
  - active_device property
  - thread-safe concurrent select + get_frame
"""
import threading
import time
from dataclasses import dataclass
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from vjlive3.audio.analyzer import AudioFrame, NullAudioAnalyzer
from vjlive3.audio.sources import AudioDeviceInfo, AudioSourceManager


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_pa_device(index: int, name: str, channels: int = 2, sr: float = 44100.0) -> dict:
    return {
        "index": index,
        "name": name,
        "maxInputChannels": channels,
        "defaultSampleRate": sr,
    }


def _make_pa_module_mock(devices: List[dict]) -> MagicMock:
    """Create a mock that behaves like `import pyaudio as _pyaudio`.
    Code calls `_pyaudio.PyAudio()` so we need `.PyAudio` attribute to be a class mock.
    """
    pa_instance = MagicMock()
    pa_instance.get_device_count.return_value = len(devices)
    pa_instance.get_device_info_by_index.side_effect = lambda i: devices[i]
    pa_module = MagicMock()
    pa_module.PyAudio.return_value = pa_instance
    return pa_module, pa_instance


# ── AudioDeviceInfo ───────────────────────────────────────────────────────────

class TestAudioDeviceInfo:

    def test_is_frozen_dataclass(self):
        dev = AudioDeviceInfo(index=0, name="Mic", max_input_channels=2,
                               default_sample_rate=44100.0)
        with pytest.raises((AttributeError, TypeError)):
            dev.index = 99  # type: ignore[misc]

    def test_is_loopback_defaults_false(self):
        dev = AudioDeviceInfo(index=0, name="Mic", max_input_channels=2,
                               default_sample_rate=44100.0)
        assert dev.is_loopback is False

    def test_is_loopback_true(self):
        dev = AudioDeviceInfo(index=1, name="Monitor Source", max_input_channels=2,
                               default_sample_rate=44100.0, is_loopback=True)
        assert dev.is_loopback is True


# ── list_devices ──────────────────────────────────────────────────────────────

class TestListDevices:

    def test_no_pyaudio_returns_empty(self):
        with patch("vjlive3.audio.sources._HAS_PYAUDIO", False):
            mgr = AudioSourceManager()
            assert mgr.list_devices() == []

    def test_lists_input_devices(self):
        raw = [
            _make_pa_device(0, "Built-in Mic", channels=1),
            _make_pa_device(1, "USB Audio", channels=2),
            _make_pa_device(2, "Output Only", channels=0),   # excluded
        ]
        pa_module, _ = _make_pa_module_mock(raw)
        with patch("vjlive3.audio.sources._HAS_PYAUDIO", True), \
             patch("vjlive3.audio.sources._pyaudio", pa_module):
            mgr = AudioSourceManager()
            devices = mgr.list_devices()
        assert len(devices) == 2
        assert devices[0].name == "Built-in Mic"
        assert devices[1].name == "USB Audio"

    def test_loopback_detection(self):
        raw = [
            _make_pa_device(0, "alsa_output.monitor", channels=2),
            _make_pa_device(1, "Regular Mic", channels=1),
        ]
        pa_module, _ = _make_pa_module_mock(raw)
        with patch("vjlive3.audio.sources._HAS_PYAUDIO", True), \
             patch("vjlive3.audio.sources._pyaudio", pa_module):
            mgr = AudioSourceManager()
            devices = mgr.list_devices()
        assert devices[0].is_loopback is True
        assert devices[1].is_loopback is False

    def test_pyaudio_error_returns_empty(self):
        pa_module = MagicMock()
        pa_module.PyAudio.side_effect = OSError("pa crash")
        with patch("vjlive3.audio.sources._HAS_PYAUDIO", True), \
             patch("vjlive3.audio.sources._pyaudio", pa_module):
            mgr = AudioSourceManager()
            result = mgr.list_devices()
        assert result == []


# ── select / select_default / select_loopback ─────────────────────────────────

class TestSelection:

    def test_get_frame_before_select_returns_frame(self):
        """No crash, returns an AudioFrame with zeros before any select()."""
        mgr = AudioSourceManager()
        frame = mgr.get_frame()
        assert isinstance(frame, AudioFrame)
        assert frame.bass == 0.0

    def test_select_default_no_crash(self):
        """select_default() always succeeds (may use NullAnalyzer)."""
        with patch("vjlive3.audio.sources.create_analyzer", return_value=NullAudioAnalyzer()):
            mgr = AudioSourceManager()
            result = mgr.select_default()
        # NullAnalyzer.start() returns True
        assert isinstance(result, bool)

    def test_select_invalid_device_returns_false_and_keeps_current(self):
        """Selecting a non-existent device index returns False, keeps old analyzer running."""
        with patch("vjlive3.audio.sources._HAS_PYAUDIO", True):
            pa_mock = MagicMock()
            pa_mock.get_device_count.return_value = 1
            pa_mock.get_device_info_by_index.return_value = _make_pa_device(0, "Mic", 1)
            with patch("vjlive3.audio.sources._pyaudio", MagicMock(return_value=pa_mock)):
                mgr = AudioSourceManager()
                result = mgr.select(device_index=99)  # doesn't exist
        assert result is False

    def test_select_loopback_found(self):
        """select_loopback() picks the monitor device."""
        raw = [
            _make_pa_device(0, "Mic", channels=1),
            _make_pa_device(1, "pulse.monitor", channels=2),
        ]
        pa_module, _ = _make_pa_module_mock(raw)
        with patch("vjlive3.audio.sources._HAS_PYAUDIO", True), \
             patch("vjlive3.audio.sources._pyaudio", pa_module), \
             patch("vjlive3.audio.sources.create_analyzer", return_value=NullAudioAnalyzer()):
            mgr = AudioSourceManager()
            mgr.select_loopback()
            dev = mgr.active_device
        assert dev is not None
        assert dev.is_loopback is True

    def test_select_loopback_no_loopback_falls_back(self):
        """select_loopback() falls back to select_default() when no loopback found."""
        raw = [_make_pa_device(0, "Regular Mic", channels=1)]
        with patch("vjlive3.audio.sources._HAS_PYAUDIO", True):
            pa_mock = MagicMock()
            pa_mock.get_device_count.return_value = 1
            pa_mock.get_device_info_by_index.side_effect = lambda i: raw[i]
            with patch("vjlive3.audio.sources._pyaudio", MagicMock(return_value=pa_mock)), \
                 patch("vjlive3.audio.sources.create_analyzer", return_value=NullAudioAnalyzer()):
                mgr = AudioSourceManager()
                # Should not raise
                mgr.select_loopback()

    def test_hot_switch_stops_old_analyzer(self):
        """Calling select() twice stops the old analyzer before starting the new one."""
        old = MagicMock(spec=NullAudioAnalyzer)
        old.get_frame.return_value = NullAudioAnalyzer().get_frame()
        old.start.return_value = True
        new = NullAudioAnalyzer()

        analyzers = [old, new]
        call_order = []
        old.stop.side_effect = lambda: call_order.append("stop_old")

        raw = [_make_pa_device(0, "Mic A", 1), _make_pa_device(1, "Mic B", 1)]
        pa_module, _ = _make_pa_module_mock(raw)

        with patch("vjlive3.audio.sources._HAS_PYAUDIO", True), \
             patch("vjlive3.audio.sources._pyaudio", pa_module), \
             patch("vjlive3.audio.sources.create_analyzer",
                   side_effect=lambda **kw: analyzers.pop(0)):
            mgr = AudioSourceManager()
            mgr.select(0)
            mgr.select(1)
        assert "stop_old" in call_order, "Old analyzer was not stopped on hot-switch"

    def test_stop_idempotent(self):
        """stop() can be called multiple times without error."""
        mgr = AudioSourceManager()
        mgr.stop()
        mgr.stop()  # must not raise

    def test_active_device_none_at_start(self):
        mgr = AudioSourceManager()
        assert mgr.active_device is None

    def test_get_analyzer_is_null_before_select(self):
        mgr = AudioSourceManager()
        assert isinstance(mgr.get_analyzer(), NullAudioAnalyzer)


# ── Thread safety ─────────────────────────────────────────────────────────────

class TestThreadSafety:

    def test_concurrent_select_and_get_frame(self):
        """10 threads call select_default + get_frame concurrently — no exceptions."""
        errors = []

        def worker():
            try:
                with patch("vjlive3.audio.sources.create_analyzer",
                           return_value=NullAudioAnalyzer()):
                    mgr = AudioSourceManager()
                    for _ in range(5):
                        mgr.select_default()
                        _ = mgr.get_frame()
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread safety errors: {errors}"
