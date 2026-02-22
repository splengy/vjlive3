# Spec: P4-BF04 — V-Pony

**File naming:** `docs/specs/phase4_audio/P4-BF04_V-Pony.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BF04 — V-Pony

**Phase:** Phase 4 / P4-BF04
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

V-Pony (Befaco Pony VCO) is a compact voltage-controlled oscillator that generates periodic audio waveforms. It provides frequency control, fine tuning, and pulse width modulation, offering a simple yet versatile sound source for modular synthesis.

---

## What It Does NOT Do

- Does not include multiple waveform outputs (single output only)
- Does not provide FM or sync modulation
- Does not include built-in envelope generators
- Does not support self-oscillation

---

## Public Interface

```python
class VPony:
    def __init__(self) -> None: ...
    
    def set_frequency(self, freq: float) -> None: ...
    def get_frequency(self) -> float: ...
    
    def set_fine(self, fine: float) -> None: ...
    def get_fine(self) -> float: ...
    
    def set_pw(self, pw: float) -> None: ...
    def get_pw(self) -> float: ...
    
    def get_output(self) -> float: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `freq` | `float` | Base frequency (normalized) | 0.0 to 1.0 |
| `fine` | `float` | Fine tuning | -1.0 to 1.0 |
| `pw` | `float` | Pulse width | 0.0 to 1.0 |

**Output:** `float` — Audio waveform in range -1.0 to 1.0

---

## Edge Cases and Error Handling

- What happens if frequency is extreme? → May produce inaudible or unstable output
- What happens if fine tuning is extreme? → May cause detuning beyond audible range
- What happens if pw is 0 or 1? → May produce silence or extreme pulse width
- What happens on cleanup? → Reset all parameters to defaults

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for waveform generation — fallback: use math module
- Internal modules this depends on:
  - `vjlive3.plugins.PluginBase`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_oscillator_output` | Produces periodic waveform |
| `test_frequency_control` | Frequency parameter works |
| `test_fine_tuning` | Fine tuning parameter works |
| `test_pw_control` | Pulse width affects waveform |
| `test_edge_cases` | Handles extreme parameter values |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BF04: V-Pony oscillator` message
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

*Specification based on Befaco V-Pony module from legacy VJlive-2 codebase.*