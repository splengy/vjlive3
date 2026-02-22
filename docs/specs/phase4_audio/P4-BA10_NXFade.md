# Spec: P4-BA10 — NXFade

**File naming:** `docs/specs/phase4_audio/P4-BA10_NXFade.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA10 — NXFade

**Phase:** Phase 4 / P4-BA10
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

NXFade is a crossfader module that smoothly transitions between two audio inputs based on a position parameter. It provides curve control for shaping the transition curve and level controls for each input, making it ideal for smooth transitions between audio sources.

---

## What It Does NOT Do

- Does not provide panning or stereo positioning
- Does not include built-in effects or processing
- Does not support CV control of position
- Does not include metering or visual feedback

---

## Public Interface

```python
class NXFade:
    def __init__(self) -> None: ...
    
    def set_position(self, position: float) -> None: ...
    def get_position(self) -> float: ...
    
    def set_curve(self, curve: float) -> None: ...
    def get_curve(self) -> float: ...
    
    def set_level1(self, level: float) -> None: ...
    def get_level1(self) -> float: ...
    
    def set_level2(self, level: float) -> None: ...
    def get_level2(self) -> float: ...
    
    def process(self, input1: float, input2: float) -> float: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `position` | `float` | Crossfade position | 0.0 to 1.0 |
| `curve` | `float` | Transition curve shape | 0.0 to 1.0 |
| `level1` | `float` | Input 1 level | 0.0 to 1.0 |
| `level2` | `float` | Input 2 level | 0.0 to 1.0 |
| `input1` | `float` | First audio input | -1.0 to 1.0 |
| `input2` | `float` | Second audio input | -1.0 to 1.0 |

**Output:** `float` — Crossfaded audio signal

---

## Edge Cases and Error Handling

- What happens if position is 0 or 1? → Full output from input 1 or 2 respectively
- What happens if curve is extreme? → May cause abrupt transitions
- What happens if levels are 0? → Output is silent regardless of position
- What happens if inputs are out of range? → Clips to -1.0 to 1.0 range
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
| `test_basic_crossfade` | Transitions between inputs correctly |
| `test_position_control` | Position parameter works |
| `test_curve_control` | Curve parameter shapes transition |
| `test_level_control` | Individual input levels work |
| `test_edge_cases` | Handles invalid inputs gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA10: NXFade crossfader` message
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

*Specification based on Bogaudio NXFade module from legacy VJlive-2 codebase.*