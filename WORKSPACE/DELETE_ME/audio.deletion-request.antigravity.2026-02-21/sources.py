"""P1-A4 — Multi-Source Audio Input (AudioSourceManager)

Manages audio input device enumeration and hot-switching at runtime.
A thin orchestration layer above P1-A1's AudioAnalyzerBase — it selects
a device, instantiates an AudioAnalyzer for it, and exposes the same
AudioFrame API so callers don't need to know which device is active.

Falls back to NullAudioAnalyzer gracefully when PyAudio is absent or
the device becomes unavailable.

Spec: docs/specs/P1-A4_audio_sources.md
Dependencies: P1-A1 (AudioAnalyzerBase, create_analyzer, AudioFrame)
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import List, Optional

from vjlive3.audio.analyzer import (
    AudioAnalyzerBase,
    AudioFrame,
    NullAudioAnalyzer,
    create_analyzer,
)

_log = logging.getLogger(__name__)

# ── Optional PyAudio ──────────────────────────────────────────────────────────
try:
    import pyaudio as _pyaudio
    _HAS_PYAUDIO = True
except ImportError:
    _pyaudio = None           # type: ignore[assignment]
    _HAS_PYAUDIO = False


# ── Device info ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AudioDeviceInfo:
    """Metadata for a discovered audio input device."""
    index: int                     # PyAudio device index
    name: str                      # Human-readable name
    max_input_channels: int
    default_sample_rate: float
    is_loopback: bool = False      # True for PulseAudio monitor sources


# ── AudioSourceManager ────────────────────────────────────────────────────────

class AudioSourceManager:
    """
    Manages audio input device enumeration and hot-switching.

    Usage::

        mgr = AudioSourceManager()
        devices = mgr.list_devices()
        mgr.select_default()
        frame = mgr.get_frame()

        # Switch at runtime (hot-swap):
        mgr.select(devices[1].index)

        mgr.stop()

    Thread-safe: select() / stop() can be called from any thread while
    the render loop calls get_frame() concurrently.
    """

    # Keyword that PulseAudio uses for monitor (loopback) source names
    _LOOPBACK_KEYWORDS = ("monitor", ".monitor")

    def __init__(
        self,
        sample_rate: int = 44100,
        buffer_size: int = 2048,
    ) -> None:
        self._sample_rate = sample_rate
        self._buffer_size = buffer_size
        # Protected by _lock
        self._lock = threading.RLock()
        self._analyzer: AudioAnalyzerBase = NullAudioAnalyzer(sample_rate, buffer_size)
        self._active_device: Optional[AudioDeviceInfo] = None
        self._started = False

    # ── Device enumeration ────────────────────────────────────────────────────

    def list_devices(self) -> List[AudioDeviceInfo]:
        """Return all available audio input devices.

        Includes PulseAudio monitor sources (is_loopback=True) if present.
        Returns an empty list when PyAudio is unavailable.
        """
        if not _HAS_PYAUDIO:
            _log.warning("PyAudio unavailable — list_devices returns []")
            return []

        pa = None
        try:
            pa = _pyaudio.PyAudio()
            devices: List[AudioDeviceInfo] = []
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) < 1:
                    continue
                name = info.get("name", f"Device {i}")
                is_loopback = any(kw in name.lower() for kw in self._LOOPBACK_KEYWORDS)
                devices.append(AudioDeviceInfo(
                    index=i,
                    name=name,
                    max_input_channels=int(info.get("maxInputChannels", 1)),
                    default_sample_rate=float(info.get("defaultSampleRate", 44100.0)),
                    is_loopback=is_loopback,
                ))
            return devices
        except Exception as exc:
            _log.error("list_devices error: %s", exc)
            return []
        finally:
            if pa:
                try:
                    pa.terminate()
                except Exception:
                    pass

    # ── Device selection ──────────────────────────────────────────────────────

    def select(self, device_index: int) -> bool:
        """Switch to a specific audio input device by index.

        Stops the current analyzer, creates a new one for the requested device,
        and starts it. Thread-safe — safe to call while render loop is running.

        Returns:
            True if the new analyzer started with hardware successfully.
            False if hardware is unavailable (NullAnalyzer activated, frames continue).
        """
        # Find device info (best-effort, non-fatal if not found)
        info: Optional[AudioDeviceInfo] = None
        for dev in self.list_devices():
            if dev.index == device_index:
                info = dev
                break

        if info is None and _HAS_PYAUDIO:
            _log.error("select(%d): device not found — keeping current analyzer", device_index)
            return False

        return self._swap_analyzer(device_index, info)

    def select_default(self) -> bool:
        """Select the system default audio input device.

        Returns:
            True if hardware started, False if falling back to NullAnalyzer.
        """
        return self._swap_analyzer(device_index=None, info=None)

    def select_loopback(self) -> bool:
        """Select a PulseAudio monitor (loopback) source, if available.

        Falls back to select_default() with a WARNING if no loopback found.

        Returns:
            True if hardware started, False if falling back.
        """
        for dev in self.list_devices():
            if dev.is_loopback:
                _log.info("AudioSourceManager: loopback device found — %s", dev.name)
                return self._swap_analyzer(dev.index, dev)

        _log.warning("No loopback device found — falling back to system default")
        return self.select_default()

    # ── Frame access ──────────────────────────────────────────────────────────

    def get_frame(self) -> AudioFrame:
        """Return the latest AudioFrame from the active analyzer.

        Never blocks. Returns a zeroed frame before any device is selected.
        Thread-safe.
        """
        with self._lock:
            return self._analyzer.get_frame()

    def get_analyzer(self) -> AudioAnalyzerBase:
        """Return the active analyzer instance (NullAnalyzer if none selected)."""
        with self._lock:
            return self._analyzer

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def stop(self) -> None:
        """Stop the current analyzer and release all resources. Idempotent."""
        with self._lock:
            self._stop_current()
            self._active_device = None
            self._started = False

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def active_device(self) -> Optional[AudioDeviceInfo]:
        """Info for the currently active device, or None if none selected."""
        with self._lock:
            return self._active_device

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def buffer_size(self) -> int:
        return self._buffer_size

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _swap_analyzer(
        self,
        device_index: Optional[int],
        info: Optional[AudioDeviceInfo],
    ) -> bool:
        """Stop old analyzer, start new one for device_index. Thread-safe."""
        with self._lock:
            self._stop_current()
            new_analyzer = create_analyzer(
                sample_rate=self._sample_rate,
                buffer_size=self._buffer_size,
                device_index=device_index,
            )
            started = new_analyzer.start()
            self._analyzer = new_analyzer
            self._active_device = info
            self._started = True

        if started:
            name = info.name if info else "system default"
            _log.info("AudioSourceManager: active device → %s", name)
        else:
            _log.warning(
                "AudioSourceManager: hardware unavailable for device %s — NullAnalyzer active",
                device_index,
            )
        return started

    def _stop_current(self) -> None:
        """Stop and discard the current analyzer (must hold _lock)."""
        try:
            self._analyzer.stop()
        except Exception as exc:
            _log.warning("Error stopping analyzer: %s", exc)


__all__ = ["AudioDeviceInfo", "AudioSourceManager"]
