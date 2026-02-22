# Spec: P4-BA05 — BSwitch

**File naming:** `docs/specs/phase4_audio/P4-BA05_BSwitch.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA05 — BSwitch

**Phase:** Phase 4 / P4-BA05
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

BSwitch is a signal routing module that selects between multiple audio inputs and routes the selected signal to the output. It provides manual control over which input is active, allowing for quick switching between different audio sources or signal paths.

---

## What It Does NOT Do

- Does not provide crossfading between inputs
- Does not include built-in effects or processing
- Does not support CV control of switching
- Does not include metering or visual feedback

---

## Public Interface

```python
class BSwitch:
    def __init__(self, num_inputs: int = 2) -> None: ...
    
    def set_position(self, position: int) -> None: ...
    def get_position(self) -> int: ...
    
    def set_input(self, index: int, audio: float) -> None: ...
    def get_input(self, index: int) -> float: ...
    
    def process(self) -> float: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `num_inputs` | `int` | Number of switch positions | 2 ≤ num_inputs ≤ 8 |
| `position` | `int` | Active input position | 0 ≤ position < num_inputs |
| `index` | `int` | Input index | 0 ≤ index < num_inputs |
| `audio` | `float` | Input audio sample | -1.0 to 1.0 |

**Output:** `float` — Selected input audio sample

---

## Edge Cases and Error Handling

- What happens if position is out of range? → Raises ValueError with message
- What happens if input index is out of range? → Raises ValueError with message
- What happens if num_inputs is out of range? → Raises ValueError with message
- What happens if audio input clips? → Clips to -1.0 to 1.0 range
- What happens on cleanup? → Reset to position 0

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
| `test_basic_switching` | Switches between inputs correctly |
| `test_position_control` | Position parameter works |
| `test_multiple_inputs` | Handles multiple input channels |
| `test_edge_cases` | Handles invalid inputs gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA05: BSwitch signal router` message
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

*Specification based on Bogaudio BSwitch module from legacy VJlive-2 codebase.*