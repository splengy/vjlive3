# Spec Template — P2-H1 MIDI Controller Input

**File naming:** `docs/specs/P2-H1_midi_controller.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-H1 — MIDI Controller Input

**Phase:** Phase 2
**Assigned To:** Worker
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module handles receiving MIDI input from connected hardware controllers. It manages device discovery, connection lifecycle, and translating incoming raw MIDI messages (Note On, Note Off, Control Change) into unified internal events that can drive the Node Graph or other system parameters.

---

## What It Does NOT Do

- It does not map MIDI events to specific visual parameters (that is handled by the routing matrix/node graph).
- It does not send MIDI output to controllers (e.g., motor fader feedback), as this is out of scope for the initial input integration.

---

## Public Interface

```python
from typing import List, Callable, Optional

class MidiEvent:
    type: str # 'note_on', 'note_off', 'cc'
    channel: int
    note: int
    velocity: int
    value: int # for cc

class MidiDeviceStatus:
    name: str
    is_connected: bool

class MidiController:
    def __init__(self) -> None: ...
    def scan_devices(self) -> List[str]: ...
    def connect(self, device_name: str) -> bool: ...
    def disconnect(self) -> None: ...
    def register_callback(self, callback: Callable[[MidiEvent], None]) -> None: ...
    def poll(self) -> None: ...
    def get_status(self) -> MidiDeviceStatus: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `device_name` | `str` | Name of the MIDI device | Must be in `scan_devices()` |
| `callback` | `Callable` | Function to call on MIDI event | Fast, non-blocking |

---

## Edge Cases and Error Handling

- What happens if the MIDI device disconnects unexpectedly? → The module catches the error, sets `is_connected` to False, and attempts reconnection periodically (Fail-Graceful).
- What happens if an invalid device name is provided? → `connect` returns False without raising an exception.

---

## Dependencies

- External libraries needed: `mido`, `python-rtmidi`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_midi_scan` | Devices are scanned without error |
| `test_midi_event_parsing` | Raw messages correctly translate to MidiEvent objects |
| `test_device_disconnect_graceful` | Disconnecting does not crash the application |
| `test_callback_invocation` | Registered callbacks are fired on incoming messages |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-H1: MIDI controller input` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
