# Spec: P4-BA07 — BVCO

**File naming:** `docs/specs/phase4_audio/P4-BA07_BVCO.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA07 — BVCO

**Phase:** Phase 4 / P4-BA07
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

BVCO (Bogaudio Voltage Controlled Oscillator) is a versatile oscillator that generates periodic audio waveforms. It provides multiple waveform outputs (sine, triangle, sawtooth, square, pulse), frequency control, fine tuning, pulse width modulation, and frequency modulation capabilities.

---

## What It Does NOT Do

- Does not include built-in envelope generators
- Does not provide synchronization or hard sync features
- Does not include built-in effects or processing
- Does not support self-oscillation

---

## Public Interface

```python
class BVCO:
    def __init__(self) -> None: ...
    
    def set_frequency(self, freq: float) -> None: ...
    def get_frequency(self) -> float: ...
    
    def set_fine(self, fine: float) -> None: ...
    def get_fine(self) -> float: ...
    
    def set_pw(self, pw: float) -> None: ...
    def get_pw(self) -> float: ...
    
    def set_fm(self, fm: float) -> None: ...
    def get_fm(self) -> float: ...
    
    def get_sine(self) -> float: ...
    def get_triangle(self) -> float: ...
    def get_sawtooth(self) -> float: ...
    def get_square(self) -> float: ...
    def get_pulse(self) -> float: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `freq` | `float` | Base frequency (logarithmic) | -54.0 to 54.0 |
| `fine` | `float` | Fine tuning | -1.0 to 1.0 |
| `pw` | `float` | Pulse width (for pulse/square) | 0.0 to 1.0 |
| `fm` | `float` | FM amount | 0.0 to 1.0 |
| `waveform` | `str` | Waveform type | 'sine', 'triangle', 'sawtooth', 'square', 'pulse' |

**Outputs:** `float` — Audio waveform in range -1.0 to 1.0

---

## Edge Cases and Error Handling

- What happens if frequency is extreme? → May produce inaudible or unstable output
- What happens if fine tuning is extreme? → May cause detuning beyond audible range
- What happens if pw is 0 or 1? → May produce silence or extreme pulse width
- What happens if fm is extreme? → May cause frequency modulation beyond range
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
| `test_sine_waveform` | Produces clean sine wave |
| `test_triangle_waveform` | Produces triangle wave |
| `test_sawtooth_waveform` | Produces sawtooth wave |
| `test_square_waveform` | Produces square wave |
| `test_pulse_waveform` | Produces pulse wave with PW control |
| `test_frequency_control` | Frequency parameter works |
| `test_fine_tuning` | Fine tuning parameter works |
| `test_fm_modulation` | FM modulation affects frequency |
| `test_edge_cases` | Handles extreme parameter values |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA07: BVCO voltage controlled oscillator` message
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

*Specification based on Bogaudio BVCO module from legacy VJlive-2 codebase.*