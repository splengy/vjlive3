# Spec: P4-BA02 — BLFO

**File naming:** `docs/specs/phase4_audio/P4-BA02_BLFO.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA02 — BLFO

**Phase:** Phase 4 / P4-BA02
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

BLFO (Bogaudio Low Frequency Oscillator) is a modulation source that generates periodic control signals in the sub-audio range (typically 0.005 Hz to 30 Hz). It provides multiple waveform shapes, rate control, and output scaling for use in controlling other audio and CV parameters.

---

## What It Does NOT Do

- Does not generate audio-rate signals (above 20 Hz)
- Does not include built-in envelope followers or amplitude modulation
- Does not provide synchronization or clocking features
- Does not output audio signals directly (CV only)

---

## Public Interface

```python
class BLFO:
    def __init__(self) -> None: ...
    
    def set_rate(self, rate: float) -> None: ...
    def get_rate(self) -> float: ...
    
    def set_shape(self, shape: float) -> None: ...
    def get_shape(self) -> float: ...
    
    def set_pw(self, pw: float) -> None: ...
    def get_pw(self) -> float: ...
    
    def set_offset(self, offset: float) -> None: ...
    def get_offset(self) -> float: ...
    
    def set_scale(self, scale: float) -> None: ...
    def get_scale(self) -> float: ...
    
    def process(self) -> float: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `rate` | `float` | Oscillation speed | -5.0 to 10.0 (logarithmic) |
| `shape` | `float` | Waveform shape morph | 0.0 to 1.0 |
| `pw` | `float` | Pulse width (for square/pulse) | 0.0 to 1.0 |
| `offset` | `float` | DC offset added to output | -1.0 to 1.0 |
| `scale` | `float` | Output amplitude multiplier | 0.0 to 1.0 |

**Output:** `float` — LFO signal in range -1.0 to 1.0 (after scaling)

---

## Edge Cases and Error Handling

- What happens if rate is negative? → Absolute value used, sign determines direction
- What happens if shape/pw/offset/scale are out of range? → Clamp to valid range
- What happens on initialization? → Set defaults: rate=1.0, shape=0.5, pw=0.5, offset=0.0, scale=1.0
- What happens on cleanup? → Reset internal state

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
| `test_default_output` | Produces signal in expected range |
| `test_rate_control` | Rate parameter affects frequency |
| `test_shape_morph` | Shape parameter morphs waveform |
| `test_scale_offset` | Scale and offset affect output correctly |
| `test_edge_cases` | Handles extreme parameter values |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA02: BLFO low frequency oscillator` message
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

*Specification based on Bogaudio BLFO module from legacy VJlive-2 codebase.*