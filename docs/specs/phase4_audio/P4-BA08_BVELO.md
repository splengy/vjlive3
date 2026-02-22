# Spec: P4-BA08 — BVELO (Envelope Follower)

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

BVELO is an envelope follower plugin for VJLive3. It tracks the amplitude envelope of an audio signal and outputs a control voltage, enabling audio-reactive modulation of parameters in other plugins and effects.

---

## What It Does NOT Do

- Does not process audio output (control signal only)
- Does not include filters (envelope detection only)
- Does not handle recording (analysis only)
- Does not provide automation (real-time only)

---

## Public Interface

```python
class BVELOPlugin:
    def __init__(self, attack: float = 0.01, release: float = 0.1) -> None: ...
    
    def set_attack(self, attack: float) -> None: ...
    def get_attack(self) -> float: ...
    
    def set_release(self, release: float) -> None: ...
    def get_release(self) -> float: ...
    
    def set_threshold(self, threshold: float) -> None: ...
    def get_threshold(self) -> float: ...
    
    def set_output_scale(self, scale: float) -> None: ...
    def get_output_scale(self) -> float: ...
    
    def process(self, audio: AudioBuffer) -> float: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `attack` | `float` | Attack time in seconds | 0.001 to 1.0 |
| `release` | `float` | Release time in seconds | 0.001 to 1.0 |
| `threshold` | `float` | Detection threshold | 0.0 to 1.0 |
| `scale` | `float` | Output scaling factor | 0.0 to 10.0 |
| `audio` | `AudioBuffer` | Input audio buffer | Valid buffer |

**Output:** `float` — Envelope control voltage (0.0-1.0)

---

## Edge Cases and Error Handling

- What happens if attack/release out of range? → Clamp to valid range
- What happens if threshold negative? → Clamp to 0.0
- What happens if audio buffer empty? → Return current envelope
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
| `test_attack_release` | Sets and gets attack/release |
| `test_threshold` | Sets and gets threshold |
| `test_output_scale` | Sets and gets output scale |
| `test_envelope_tracking` | Tracks audio envelope correctly |
| `test_response_time` | Attack/release timing accurate |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA08: BVELO envelope follower` message
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

*Specification based on Bogaudio BVELO module.*