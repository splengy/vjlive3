# Spec: P4-BF02 — V-Morphader

**File naming:** `docs/specs/phase4_audio/P4-BF02_V-Morphader.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BF02 — V-Morphader

**Phase:** Phase 4 / P4-BF02
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

V-Morphader (Befaco Morphader) is a 4-channel crossfader that smoothly transitions between four audio inputs based on a position parameter. It provides individual level controls for each input and a master output, making it ideal for complex mixing and crossfading between multiple audio sources.

---

## What It Does NOT Do

- Does not provide panning or stereo positioning
- Does not include built-in effects or processing
- Does not support CV control of position
- Does not include metering or visual feedback

---

## Public Interface

```python
class VMorphader:
    def __init__(self) -> None: ...
    
    def set_position(self, position: float) -> None: ...
    def get_position(self) -> float: ...
    
    def set_level(self, channel: int, level: float) -> None: ...
    def get_level(self, channel: int) -> float: ...
    
    def set_master_level(self, level: float) -> None: ...
    def get_master_level(self) -> float: ...
    
    def process(self, input1: float, input2: float, input3: float, input4: float) -> float: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `position` | `float` | Crossfade position (0-1) | 0.0 to 1.0 |
| `channel` | `int` | Input channel index (0-3) | 0 ≤ channel ≤ 3 |
| `level` | `float` | Channel level | 0.0 to 1.0 |
| `input1-4` | `float` | Audio inputs | -1.0 to 1.0 |

**Output:** `float` — Crossfaded audio signal

---

## Edge Cases and Error Handling

- What happens if position is out of range? → Clamp to 0.0-1.0
- What happens if channel index is out of range? → Raise ValueError
- What happens if levels are 0? → Output is silent
- What happens if inputs are out of range? → Clamp to -1.0 to 1.0
- What happens on cleanup? → Reset all parameters to defaults

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - None required for basic functionality
- Internal modules this depends on:
  - `vjlive3.plugins.PluginBase`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_basic_morphing` | Crossfades between 4 inputs correctly |
| `test_position_control` | Position parameter works |
| `test_level_control` | Individual channel levels work |
| `test_master_level` | Master level affects output |
| `test_edge_cases` | Handles invalid inputs gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BF02: V-Morphader 4-channel crossfader` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Verification Checkpoint

- [ ] Spec reviewed and approved
- [ ] Implementation ready to begin
- [ ] All dependencies verified
- [ ] Test plan complete
- [ ] Definition of Done clear

---

*Specification based on Befaco V-Morphader module from legacy VJlive-2 codebase.*