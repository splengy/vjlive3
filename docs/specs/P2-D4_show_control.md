# Spec Template — P2-D4 Show Control System

**File naming:** `docs/specs/P2-D4_show_control.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-D4 — Show Control System

**Phase:** Phase 2
**Priority:** P1
**Assigned To:** Unassigned
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module implements a professional-grade theatrical show control system for the DMX engine. It manages `Cue`s (lighting states with fade times) and organizes them into `CueStack`s. It handles crossfading between cues over time, halting/resuming fades, and releasing stacks. It also provides a central `ShowController` to manage multiple active stacks and serialize/deserialize show data (saving/loading shows).

---

## What It Does NOT Do

- It does NOT communicate directly with ArtNet/sACN (that is P2-D2).
- It does NOT handle procedural effects like rainbows or chases (that is P2-D3).
- It does NOT map universes directly (it interpolates channel values and provides them to the main engine).

---

## Public Interface

```python
from typing import List, Dict, Optional, Any

class Cue:
    def __init__(self, cue_number: float, name: str, fade_in: float = 3.0, fade_out: float = 3.0, state: Dict[str, Any] = None) -> None: ...
    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Cue': ...

class CueStack:
    def __init__(self, name: str = "Stack") -> None: ...
    def add_cue(self, cue: Cue) -> None: ...
    def remove_cue(self, cue_number: float) -> bool: ...
    def go(self) -> None: ...
    def back(self) -> None: ...
    def halt(self) -> None: ...
    def resume(self) -> None: ...
    def release(self, fade_time: float) -> None: ...
    def process_frame(self, delta_time: float) -> Optional[Dict[str, Any]]: ...
    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CueStack': ...

class ShowController:
    def __init__(self) -> None: ...
    def add_stack(self, name: str) -> CueStack: ...
    def remove_stack(self, stack_id: str) -> bool: ...
    def select_stack(self, stack_id: str) -> bool: ...
    def go(self) -> None: ...
    def back(self) -> None: ...
    def halt(self) -> None: ...
    def resume(self) -> None: ...
    def release(self, fade_time: float) -> None: ...
    def process_frame(self, delta_time: float) -> Dict[str, Any]: ...
    def save_show(self, filepath: str) -> bool: ...
    def load_show(self, filepath: str) -> bool: ...
    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShowController': ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `delta_time` | `float` | Time elapsed since last frame | > 0.0 |
| `fade_in`/`fade_out` | `float` | Time in seconds for crossfades | >= 0.0 |
| `state` | `Dict` | Fixture/channel target values | DMX bounds (0-255) |
| `cue_number` | `float` | Unique identifier for order | Positive |

---

## Edge Cases and Error Handling

- What happens if a cue fade time is 0? → The state snaps instantly on `go()`.
- What happens if `go()` is pressed while a crossfade is already happening? → It should smoothly transition from the current interpolated state towards the new cue target.
- What happens if we try to load a corrupted show file? → Returns `False` and logs an error without crashing the active show.

---

## Dependencies

- Standard Library: `json` (for serialization), `time`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_cue_creation` | Cues initialize with correct defaults and fields |
| `test_cue_stack_go` | Stack progresses sequentially and triggers fade timing |
| `test_cue_halt_resume` | Fades pause and resume correctly |
| `test_crossfade_interpolation` | Channel values smoothly transition between states based on time |
| `test_show_serialization` | ShowController state correctly saves to and loads from dictionary |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-D4: Show control system` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
