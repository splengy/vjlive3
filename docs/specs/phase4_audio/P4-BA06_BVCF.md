# Spec: P4-BA06 — BVCF

**File naming:** `docs/specs/phase4_audio/P4-BA06_BVCF.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA06 — BVCF

**Phase:** Phase 4 / P4-BA06
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

BVCF (Bogaudio Voltage Controlled Filter) is a multi-mode filter that shapes the frequency content of audio signals. It provides continuous control over cutoff frequency, resonance, and filter mode (lowpass, highpass, bandpass, notch), making it essential for sound design and tonal shaping.

---

## What It Does NOT Do

- Does not include built-in envelope followers or modulation sources
- Does not provide stereo processing (mono only)
- Does not include distortion or saturation effects
- Does not support self-oscillation

---

## Public Interface

```python
class BVCF:
    def __init__(self) -> None: ...
    
    def set_frequency(self, freq: float) -> None: ...
    def get_frequency(self) -> float: ...
    
    def set_resonance(self, res: float) -> None: ...
    def get_resonance(self) -> float: ...
    
    def set_mode(self, mode: int) -> None: ...
    def get_mode(self) -> int: ...
    
    def set_fm(self, fm: float) -> None: ...
    def get_fm(self) -> float: ...
    
    def process(self, audio: float) -> float: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `freq` | `float` | Cutoff frequency (normalized) | 0.0 to 1.0 |
| `res` | `float` | Resonance/Q | 0.0 to 1.0 |
| `mode` | `int` | Filter mode | 0=LP, 1=HP, 2=BP, 3=Notch |
| `fm` | `float` | FM amount | 0.0 to 1.0 |
| `audio` | `float` | Input audio sample | -1.0 to 1.0 |

**Output:** `float` — Filtered audio sample

---

## Edge Cases and Error Handling

- What happens if frequency is 0 or 1? → Extreme settings, may cause instability
- What happens if resonance is too high? → May cause clipping, limit to safe range
- What happens if mode is invalid? → Clamp to 0-3 range
- What happens if audio input clips? → Clips to -1.0 to 1.0 range
- What happens on cleanup? → Reset all parameters to defaults

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for filter coefficient calculations — fallback: use math module
- Internal modules this depends on:
  - `vjlive3.plugins.PluginBase`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_lowpass_mode` | Lowpass filter attenuates high frequencies |
| `test_highpass_mode` | Highpass filter attenuates low frequencies |
| `test_bandpass_mode` | Bandpass filter isolates frequency band |
| `test_notch_mode` | Notch filter rejects specific frequency |
| `test_resonance` | Resonance control affects Q factor |
| `test_fm` | FM modulation affects cutoff |
| `test_edge_cases` | Handles extreme parameter values |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA06: BVCF voltage controlled filter` message
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

*Specification based on Bogaudio BVCF module from legacy VJlive-2 codebase.*