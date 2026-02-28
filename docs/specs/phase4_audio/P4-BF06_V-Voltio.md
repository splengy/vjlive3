# Spec: P4-BF06 — V-Voltio (Voltage-Controlled Amplifier)

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

V-Voltio is a voltage-controlled amplifier (VCA) plugin for VJLive3. It provides amplitude control via CV (control voltage), exponential/logarithmic response options, and soft clipping, enabling dynamic gain modulation and amplitude shaping.

---

## What It Does NOT Do

- Does not provide distortion effects (amplification only)
- Does not include effects processing (VCA only)
- Does not handle recording (playback only)
- Does not include automation (CV control only)

---

## Public Interface

```python
class VVoltioPlugin:
    def __init__(self, response: str = "linear") -> None: ...
    
    def set_gain(self, gain: float) -> None: ...
    def get_gain(self) -> float: ...
    
    def set_cv_amount(self, amount: float) -> None: ...
    def get_cv_amount(self) -> float: ...
    
    def set_response(self, response: str) -> None: ...
    def get_response(self) -> str: ...
    
    def set_soft_clip(self, enabled: bool) -> None: ...
    def get_soft_clip(self) -> bool: ...
    
    def process(self, audio: AudioBuffer, cv: float = 0.0) -> AudioBuffer: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `response` | `str` | Gain response curve | 'linear', 'exponential', 'logarithmic' |
| `gain` | `float` | Base gain in dB | -60.0 to 24.0 |
| `amount` | `float` | CV modulation amount | 0.0 to 1.0 |
| `enabled` | `bool` | Soft clip enable | True/False |
| `audio` | `AudioBuffer` | Input audio buffer | Valid buffer |
| `cv` | `float` | Control voltage input | 0.0 to 1.0 |

**Output:** `AudioBuffer` — Amplified audio

---

## Edge Cases and Error Handling

- What happens if gain out of range? → Clamp to valid range
- What happens if CV amount invalid? → Clamp to 0.0-1.0
- What happens if response type invalid? → Use default (linear)
- What happens on cleanup? → Reset all parameters, release resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for audio processing — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.audio.audio_buffer` (for AudioBuffer type)
  - `vjlive3.plugins.api` (for PluginBase)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_gain_control` | Sets and gets gain correctly |
| `test_cv_modulation` | CV modulation works |
| `test_response_curve` | Response curves work correctly |
| `test_soft_clip` | Soft clipping works |
| `test_amplification` | Amplifies audio correctly |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BF06: V-Voltio voltage-controlled amplifier` message
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

*Specification based on Befaco V-Voltio module.*