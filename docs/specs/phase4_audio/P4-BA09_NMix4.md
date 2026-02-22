# Spec: P4-BA09 — NMix4

**File naming:** `docs/specs/phase4_audio/P4-BA09_NMix4.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA09 — NMix4

**Phase:** Phase 4 / P4-BA09
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

NMix4 is a 4-channel mixer that combines multiple audio signals into a single output. It provides individual level controls for each input channel and a master output level, allowing for precise mixing of audio sources in a modular synthesis environment.

---

## What It Does NOT Do

- Does not provide panning or stereo positioning
- Does not include built-in effects or processing
- Does not support CV control of levels
- Does not include metering or visual feedback

---

## Public Interface

```python
class NMix4:
    def __init__(self) -> None: ...
    
    def set_level(self, channel: int, level: float) -> None: ...
    def get_level(self, channel: int) -> float: ...
    
    def set_master_level(self, level: float) -> None: ...
    def get_master_level(self) -> float: ...
    
    def process(self, inputs: List[float]) -> float: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `channel` | `int` | Input channel index (0-3) | 0 ≤ channel ≤ 3 |
| `level` | `float` | Channel level (0.0-1.0) | 0.0 ≤ level ≤ 1.0 |
| `inputs` | `List[float]` | Audio input values | Length 4, values in -1.0 to 1.0 range |

**Output:** `float` — Mixed output signal

---

## Edge Cases and Error Handling

- What happens if channel index is out of range? → Raises ValueError with message
- What happens if input list length is not 4? → Raises ValueError with message
- What happens if input values are out of range? → Clips to -1.0 to 1.0 range
- What happens on cleanup? → Resets all levels to 0.0

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
| `test_basic_mixing` | Combines 4 inputs correctly |
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
- [ ] Git commit with `[Phase-4] P4-BA09: NMix4 4-channel mixer` message
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

*Specification based on Bogaudio NMix4 module from legacy VJlive-2 codebase.*