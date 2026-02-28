# Spec: P4-BA06 — BVCF (Voltage-Controlled Filter)

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

BVCF is a voltage-controlled filter plugin for VJLive3. It provides multiple filter types (lowpass, highpass, bandpass, notch), cutoff frequency, resonance, and envelope modulation, enabling dynamic frequency shaping and filtering effects.

---

## What It Does NOT Do

- Does not provide distortion effects (filter only)
- Does not include multi-mode filtering (single filter)
- Does not handle recording (playback only)
- Does not include automation (manual control only)

---

## Public Interface

```python
class BVCFPlugin:
    def __init__(self, filter_type: str = "lowpass") -> None: ...
    
    def set_cutoff(self, frequency: float) -> None: ...
    def get_cutoff(self) -> float: ...
    
    def set_resonance(self, q: float) -> None: ...
    def get_resonance(self) -> float: ...
    
    def set_filter_type(self, filter_type: str) -> None: ...
    def get_filter_type(self) -> str: ...
    
    def set_envelope_amount(self, amount: float) -> None: ...
    def get_envelope_amount(self) -> float: ...
    
    def process(self, audio: AudioBuffer) -> AudioBuffer: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `filter_type` | `str` | Filter type | 'lowpass', 'highpass', 'bandpass', 'notch' |
| `frequency` | `float` | Cutoff frequency in Hz | 20.0 to 20000.0 |
| `q` | `float` | Resonance/Quality | 0.1 to 20.0 |
| `amount` | `float` | Envelope modulation amount | 0.0 to 1.0 |
| `audio` | `AudioBuffer` | Input audio buffer | Valid buffer |

**Output:** `AudioBuffer` — Filtered audio

---

## Edge Cases and Error Handling

- What happens if frequency out of range? → Clamp to 20-20k Hz
- What happens if q invalid? → Clamp to 0.1-20.0
- What happens if filter type invalid? → Use default
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
| `test_cutoff_control` | Sets and gets cutoff frequency |
| `test_resonance_control` | Sets and gets resonance |
| `test_filter_type` | Changes filter types |
| `test_envelope_mod` | Envelope modulation works |
| `test_filtering` | Applies filter correctly |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA06: BVCF voltage-controlled filter` message
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

*Specification based on Bogaudio BVCF module.*