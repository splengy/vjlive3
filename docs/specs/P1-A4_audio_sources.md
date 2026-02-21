# Spec: P1-A4 — Multi-Source Audio Input

**Phase:** Phase 1 / P1-A4
**Assigned To:** TBD (awaiting Manager assignment)
**Spec Written By:** Antigravity (Agent 3)
**Date:** 2026-02-21
**Source References:** `vjlive/core/audio_analyzer.py` (list_devices), `VJlive-2/core/audio_analyzer.py`
**Depends On:** P1-A1 (AudioAnalyzer)
**Priority:** P1 (can be deferred until after A1–A3 are working)

---

## What This Module Does

Extends the P1-A1 audio pipeline to support selecting and switching between multiple
audio input sources at runtime. Provides a device discovery API, a device selector, and
a factory that instantiates an `AudioAnalyzer` configured for a specific device. Also
supports a "loopback" mode for capturing system audio output as an input source.
The current active analyzer is swappable at runtime without restarting the application
(hot-switch).

---

## What It Does NOT Do

- Does NOT implement a mixer or combine signals from multiple sources simultaneously
- Does NOT record or write audio to disk
- Does NOT stream audio over a network
- Does NOT perform analysis (that is P1-A1 through P1-A3)
- Does NOT manage MIDI (that is P2-H1)

---

## Public Interface

```python
# vjlive3/audio/sources.py

from typing import List, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class AudioDeviceInfo:
    """Metadata for a discovered audio input device."""
    index: int                    # PyAudio device index
    name: str                     # Human-readable name
    max_input_channels: int
    default_sample_rate: float
    is_loopback: bool = False     # True for system-audio capture (PulseAudio monitor sources)


class AudioSourceManager:
    """
    Manages audio input device enumeration and hot-switching.

    Usage:
        mgr = AudioSourceManager()
        devices = mgr.list_devices()
        mgr.select(devices[0].index)
        frame = mgr.get_frame()   # from currently active analyzer
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        buffer_size: int = 2048,
    ) -> None:
        """Create manager. Does NOT start any analyzer until select() is called."""

    def list_devices(self) -> List[AudioDeviceInfo]:
        """
        Return all available audio input devices.

        Includes PulseAudio monitor sources (loopback) if present.
        Returns empty list if PyAudio unavailable.
        """

    def select(self, device_index: int) -> bool:
        """
        Switch to a specific audio input device.

        Stops the current analyzer (if any), creates a new AudioAnalyzer
        configured for device_index, and starts it.

        Returns True on success, False if device unavailable (falls back to NullAnalyzer).
        Thread-safe — can be called while render loop is running.
        """

    def select_default(self) -> bool:
        """Select the system default audio input device."""

    def select_loopback(self) -> bool:
        """
        Select system audio loopback (PulseAudio monitor source on Linux).

        Falls back to default if no loopback device is found.
        """

    def get_frame(self) -> 'AudioFrame':
        """Return current frame from active analyzer. Never blocks."""

    def get_analyzer(self) -> 'AudioAnalyzerBase':
        """Return the active AudioAnalyzerBase instance."""

    def stop(self) -> None:
        """Stop current analyzer and release all resources."""

    @property
    def active_device(self) -> Optional[AudioDeviceInfo]:
        """Return info for the currently active device, or None."""
```

---

## Inputs and Outputs

| Item | Type | Description |
|------|------|-------------|
| `device_index` | `int` | PyAudio device index |
| **Output** `list_devices()` | `List[AudioDeviceInfo]` | All available inputs |
| **Output** `get_frame()` | `AudioFrame` | Latest frame from active source |
| **Output** `select()` return | `bool` | True = success |

---

## Edge Cases

- **No PyAudio:** `list_devices()` returns `[]`; `select()` returns False, uses NullAnalyzer.
- **Invalid device index:** log ERROR, keep current analyzer running.
- **Device disconnect mid-stream:** AudioAnalyzer recovers or falls back to NullAnalyzer (RAIL 6).
- **Hot-switch:** old analyzer stopped and cleaned up before new one started (no resource leak).
- **Loopback not found:** `select_loopback()` falls back to `select_default()` with WARNING.

---

## Dependencies

### External
- `pyaudio >= 0.2.13` (optional)

### Internal
- `vjlive3.audio.analyzer.AudioAnalyzerBase` (P1-A1)
- `vjlive3.audio.analyzer.create_analyzer` (P1-A1)
- `vjlive3.audio.analyzer.AudioFrame` (P1-A1)

---

## Test Plan

| Test ID | What It Verifies |
|---------|-----------------|
| `test_list_devices_no_pyaudio` | Returns [] when PyAudio absent |
| `test_select_force_null` | select() on null system returns False, uses NullAnalyzer |
| `test_get_frame_before_select` | get_frame() returns zeroed frame before select() called |
| `test_select_default_no_crash` | select_default() runs without exception |
| `test_hot_switch_no_leak` | select() called twice — old analyzer stopped, no resource leak |
| `test_active_device_after_select` | active_device returns correct DeviceInfo after select() |
| `test_stop_idempotent` | stop() called twice — no error |
| `test_loopback_fallback` | select_loopback() succeeds or falls back gracefully |

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] All 8 tests pass
- [ ] No file over 750 lines
- [ ] No stubs
- [ ] BOARD.md P1-A4 marked ✅
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
