# Spec: P4-BA04 — BPEQ6 (6-Band Parametric EQ)

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

BPEQ6 is a 6-band parametric equalizer plugin for VJLive3. It provides individual frequency, gain, and Q controls for each band, plus global input/output gain, enabling precise tonal shaping and frequency correction for audio signals.

---

## What It Does NOT Do

- Does not provide spectrum analysis (controls only)
- Does not include auto-EQ (manual control only)
- Does not handle multi-band compression (EQ only)
- Does not include filter presets (manual settings only)

---

## Public Interface

```python
class BPEQ6Plugin:
    def __init__(self, num_bands: int = 6) -> None: ...
    
    def set_band_frequency(self, band: int, frequency: float) -> None: ...
    def get_band_frequency(self, band: int) -> float: ...
    
    def set_band_gain(self, band: int, gain: float) -> None: ...
    def get_band_gain(self, band: int) -> float: ...
    
    def set_band_q(self, band: int, q: float) -> None: ...
    def get_band_q(self, band: int) -> float: ...
    
    def set_input_gain(self, gain: float) -> None: ...
    def get_input_gain(self) -> float: ...
    
    def set_output_gain(self, gain: float) -> None: ...
    def get_output_gain(self) -> float: ...
    
    def process(self, audio: AudioBuffer) -> AudioBuffer: ...
    
    def reset(self) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `num_bands` | `int` | Number of EQ bands | 1-16 |
| `band` | `int` | Band index | 0 to num_bands-1 |
| `frequency` | `float` | Center frequency in Hz | 20.0 to 20000.0 |
| `gain` | `float` | Gain in dB | -24.0 to 24.0 |
| `q` | `float` | Quality factor | 0.1 to 20.0 |
| `audio` | `AudioBuffer` | Input audio buffer | Valid buffer |

**Output:** `AudioBuffer` — Equalized audio

---

## Edge Cases and Error Handling

- What happens if band out of range? → Clamp or raise error
- What happens if frequency out of range? → Clamp to 20-20k Hz
- What happens if gain/q invalid? → Clamp to valid range
- What happens on cleanup? → Reset all parameters, release resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for audio processing — fallback: raise ImportError
  - `scipy` — for filter design — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.audio.audio_buffer` (for AudioBuffer type)
  - `vjlive3.plugins.api` (for PluginBase)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_band_parameters` | Sets and gets band parameters |
| `test_input_output_gain` | Sets and gets I/O gain |
| `test_equalization` | Applies EQ correctly |
| `test_band_interaction` | Bands interact correctly |
| `test_bypass` | Bypass works correctly |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA04: BPEQ6 parametric equalizer` message
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

*Specification based on Bogaudio BPEQ6 module.*