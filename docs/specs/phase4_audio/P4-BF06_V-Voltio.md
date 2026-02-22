# Spec: P4-BF06 — V-Voltio

**File naming:** `docs/specs/phase4_audio/P4-BF06_V-Voltio.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BF06 — V-Voltio

**Phase:** Phase 4 / P4-BF06
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

V-Voltio (Befaco Voltage Converter) provides precise voltage scaling and offset adjustment for control signals. It allows conversion between different voltage ranges (e.g., 0-10V to -1 to 1) and adds DC offset, making it essential for interfacing between different parts of a modular system.

---

## What It Does NOT Do

- Does not process audio signals (CV only)
- Does not include amplification or attenuation beyond scaling
- Does not provide signal inversion (use separate inverter)
- Does not include CV inputs for gain/offset (manual control only)

---

## Public Interface

```python
class VVoltio:
    def __init__(self) -> None: ...
    
    def set_gain(self, gain: float) -> None: ...
    def get_gain(self) -> float: ...
    
    def set_offset(self, offset: float) -> None: ...
    def get_offset(self) -> float: ...
    
    def process(self, cv: float) -> float: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `gain` | `float` | Voltage gain multiplier | 0.0 to 2.0 |
| `offset` | `float` | DC offset to add | -5.0 to 5.0 |
| `cv` | `float` | Control voltage input | -1.0 to 1.0 (or wider) |

**Output:** `float` — Converted control voltage

---

## Edge Cases and Error Handling

- What happens if gain is 0? → Output is offset only
- What happens if offset is extreme? → May exceed normal CV range
- What happens if cv is out of range? → Clamp to valid input range
- What happens on cleanup? → Reset to default (gain=1.0, offset=0.0)

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
| `test_gain_scaling` | Gain parameter scales input correctly |
| `test_offset_addition` | Offset parameter adds correctly |
| `test_combined` | Gain and offset work together |
| `test_zero_gain` | Zero gain produces offset only |
| `test_edge_cases` | Handles extreme parameter values |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BF06: V-Voltio voltage converter` message
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

*Specification based on Befaco V-Voltio module from legacy VJlive-2 codebase.*