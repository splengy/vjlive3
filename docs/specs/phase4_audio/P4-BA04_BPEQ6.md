# Spec: P4-BA04 — BPEQ6

**File naming:** `docs/specs/phase4_audio/P4-BA04_BPEQ6.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA04 — BPEQ6

**Phase:** Phase 4 / P4-BA04
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

BPEQ6 is a 6-band parametric equalizer that provides precise control over audio frequency content. Each band has independent gain and frequency controls, allowing for detailed tonal shaping, surgical frequency correction, and creative sound design.

---

## What It Does NOT Do

- Does not include built-in spectrum analysis or visualization
- Does not support stereo processing (mono only)
- Does not include dynamic compression or limiting
- Does not provide phase adjustment controls

---

## Public Interface

```python
class BPEQ6:
    def __init__(self) -> None: ...
    
    def set_band_gain(self, band: int, gain: float) -> None: ...
    def get_band_gain(self, band: int) -> float: ...
    
    def set_band_freq(self, band: int, freq: float) -> None: ...
    def get_band_freq(self, band: int) -> float: ...
    
    def process(self, audio: float) -> float: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `band` | `int` | Band index (0-5) | 0 ≤ band ≤ 5 |
| `gain` | `float` | Band gain in dB | -12.0 to 12.0 |
| `freq` | `float` | Band frequency (normalized) | 0.0 to 1.0 |
| `audio` | `float` | Input audio sample | -1.0 to 1.0 |

**Output:** `float` — Equalized audio sample

---

## Edge Cases and Error Handling

- What happens if band index is out of range? → Raises ValueError with message
- What happens if gain is out of range? → Clamp to -12.0 to 12.0 dB
- What happens if freq is out of range? → Clamp to 0.0 to 1.0
- What happens if audio input clips? → Clips to -1.0 to 1.0 range
- What happens on cleanup? → Reset all bands to default (gain=0.0, freq=preset values)

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
| `test_flat_response` | With all gains at 0, EQ is transparent |
| `test_band_gain` | Individual band gains affect output correctly |
| `test_band_freq` | Frequency controls shift affected range |
| `test_bypass` | Can effectively bypass all bands |
| `test_edge_cases` | Handles extreme parameter values |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA04: BPEQ6 6-band parametric EQ` message
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

*Specification based on Bogaudio BPEQ6 module from legacy VJlive-2 codebase.*