# Spec: P4-BA03 — BMatrix81

**File naming:** `docs/specs/phase4_audio/P4-BA03_BMatrix81.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA03 — BMatrix81

**Phase:** Phase 4 / P4-BA03
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

BMatrix81 is an 8→1 matrix mixer that routes 8 input channels to a single output with individual gain controls for each input. It allows for complex signal routing and mixing in modular synthesis setups, with the ability to control the contribution of each input to the final mixed output.

---

## What It Does NOT Do

- Does not provide panning or stereo output
- Does not include built-in effects or processing
- Does not support CV control of gains
- Does not include metering or visual feedback

---

## Public Interface

```python
class BMatrix81:
    def __init__(self) -> None: ...
    
    def set_gain(self, input_channel: int, gain: float) -> None: ...
    def get_gain(self, input_channel: int) -> float: ...
    
    def set_master_gain(self, gain: float) -> None: ...
    def get_master_gain(self) -> float: ...
    
    def process(self, inputs: List[float]) -> float: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `input_channel` | `int` | Input channel index (0-7) | 0 ≤ input_channel ≤ 7 |
| `gain` | `float` | Input gain (-1.0 to 1.0) | -1.0 ≤ gain ≤ 1.0 |
| `inputs` | `List[float]` | Audio input values | Length 8, values in -1.0 to 1.0 range |

**Output:** `float` — Mixed output signal

---

## Edge Cases and Error Handling

- What happens if input_channel is out of range? → Raises ValueError with message
- What happens if gain is out of range? → Clamp to -1.0 to 1.0 range
- What happens if input list length is not 8? → Raises ValueError with message
- What happens if input values are out of range? → Clips to -1.0 to 1.0 range
- What happens on cleanup? → Resets all gains to 0.0

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
| `test_basic_routing` | Routes 8 inputs to single output |
| `test_gain_control` | Individual input gains work |
| `test_master_gain` | Master gain affects output |
| `test_negative_gain` | Negative gains invert signal |
| `test_edge_cases` | Handles invalid inputs gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA03: BMatrix81 8→1 mixer` message
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

*Specification based on Bogaudio BMatrix81 module from legacy VJlive-2 codebase.*