# Spec Template — P2-D1 DMX512 Core Engine + Fixture Profiles

**File naming:** `docs/specs/P2-D1_dmx_engine.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-D1 — DMX512 Core Engine + Fixture Profiles

**Phase:** Phase 2
**Assigned To:** Worker Alpha
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module provides the core DMX512 lighting control engine for VJLive3. It manages universes, schedules DMX packet transmission over Art-Net (via `pyartnet` or a custom UDP fallback), and defines a robust `FixtureProfile` system so users can map internal state (e.g., color, intensity) to raw DMX channel values for physical lights. It acts as the bridge between VJLive3's visual engine and real-world stage lighting.

---

## What It Does NOT Do

- It does NOT handle audio-reactive beat detection (that belongs to the Audio Engine).
- It does NOT implement complex DMX chases, rainbows, or strobes (that belongs to P2-D3 DMX FX engine).
- It does NOT implement sACN output (that belongs to P2-D2).

---

## Public Interface

```python
from enum import Enum
from typing import Dict, List, Optional

class FixtureProfile(Enum):
    DIMMER = "dimmer"
    RGB = "rgb"
    RGBW = "rgbw"

class DMXFixture:
    def __init__(self, name: str, start_channel: int, channel_count: int) -> None: ...
    def set_channel(self, channel_index: int, value: int) -> None: ...
    def set_rgb(self, r: int, g: int, b: int) -> None: ...
    def get_values(self) -> List[int]: ...

class DMXController:
    def __init__(self, ip_address: str = "127.0.0.1", port: int = 6454) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def add_fixture(self, name: str, start_channel: int, channel_count: int) -> DMXFixture: ...
    def set_channel(self, fixture_name: str, channel_index: int, value: int) -> None: ...
    def set_rgb(self, fixture_name: str, r: int, g: int, b: int) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `ip_address` | `str` | Destination IP for Art-Net | Valid IPv4 |
| `port` | `int` | Destination Port | Default 6454 |
| `start_channel`| `int` | DMX start channel | 1 to 512 |
| `channel_index`| `int` | Zero-based offset from start | 0 to `channel_count - 1` |
| `value` | `int` | DMX channel value | 0 to 255 |

---

## Edge Cases and Error Handling

- What happens if `pyartnet` is missing or fails to bind? → The engine gracefully falls back to a "Mock" mode, logging a warning but continuing to run without crashing (NullDevice pattern).
- What happens on bad input (e.g., channel > 512, value > 255)? → The value is clamped to 0-255. Start channels out of bounds raise a `ValueError` with a clear message.
- What is the cleanup path? → The `stop()` method gracefully stops the async transmission thread and asyncio loop, joining the thread to ensure no orphaned processes.

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `pyartnet` — used for Art-Net transmission — fallback: Mock mode (logs only)
  - `asyncio` & `threading` (Standard Library)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_dmx_fixture_channel_clamping` | Values passed to set_channel are clamped to 0-255 |
| `test_dmx_controller_mock_mode` | Controller starts and stops cleanly without pyartnet installed/running |
| `test_dmx_add_and_retrieve_fixture` | Fixtures are correctly stored and updated via the controller |
| `test_dmx_out_of_bounds_channel` | Adding a fixture with invalid channel raises ValueError |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-D1: DMX core engine` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
