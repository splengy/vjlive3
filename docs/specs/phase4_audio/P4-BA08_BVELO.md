# Spec: P4-BA08 — BVELO

**File naming:** `docs/specs/phase4_audio/P4-BA08_BVELO.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA08 — BVELO

**Phase:** Phase 4 / P4-BA08
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

BVELO (Bogaudio Velocity VCA) is a voltage-controlled amplifier that uses a velocity or CV signal to control the amplitude of an audio signal. It provides level and response controls, making it ideal for dynamic amplitude modulation, envelope following, and velocity-sensitive synthesis.

---

## What It Does NOT Do

- Does not include built-in envelope generators
- Does not provide stereo processing (mono only)
- Does not include built-in effects or processing
- Does not support CV inputs for level (manual control only)

---

## Public Interface

```python
class BVELO:
    def __init__(self) -> None: ...
    
    def set_level(self, level: float) -> None: ...
    def get_level(self) -> float: ...
    
    def set_response(self, response: float) -> None: ...
    def get_response(self) -> float: ...
    
    def process(self, audio: float, cv: float) -> float: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `level` | `float` | Base amplitude level | 0.0 to 1.0 |
| `response` | `float` | CV response curve | 0.0 to 1.0 |
| `audio` | `float` | Audio input signal | -1.0 to 1.0 |
| `cv` | `float` | Control voltage (velocity) | 0.0 to 1.0 |

**Output:** `float` — Amplified audio signal

---

## Edge Cases and Error Handling

- What happens if level is 0? → Output is silent regardless of audio
- What happens if response is extreme? → May cause nonlinear amplification
- What happens if audio or CV are out of range? → Clamp to valid range
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
| `test_level_control` | Level parameter scales output |
| `test_cv_response` | CV signal affects amplitude |
| `test_response_curve` | Response parameter shapes CV curve |
| `test_zero_level` | Level=0 produces silence |
| `test_edge_cases` | Handles extreme parameter values |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA08: BVELO velocity VCA` message
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

*Specification based on Bogaudio BVELO module from legacy VJlive-2 codebase.*