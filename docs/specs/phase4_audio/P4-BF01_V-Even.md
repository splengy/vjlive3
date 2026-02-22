# Spec: P4-BF01 — V-Even (Even Harmonic Distortion)

**File naming:** `docs/specs/phase4_audio/P4-BF01_V-Even.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BF01 — V-Even

**Phase:** Phase 4 / P4-BF01
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

V-Even is an even harmonic distortion plugin for VJLive3. It adds even-order harmonics (2nd, 4th, 6th, 8th) to audio signals, providing warm, tube-like saturation and harmonic enrichment for sound coloring and enhancement.

---

## What It Does NOT Do

- Does not provide odd harmonics (even only)
- Does not include effects processing (distortion only)
- Does not handle recording (playback only)
- Does not include convolution (harmonic generation only)

---

## Public Interface

```python
class VEvenPlugin:
    def __init__(self) -> None: ...
    
    def set_drive(self, drive: float) -> None: ...
    def get_drive(self) -> float: ...
    
    def set_tone(self, tone: float) -> None: ...
    def get_tone(self) -> float: ...
    
    def set_level(self, level: float) -> None: ...
    def get_level(self) -> float: ...
    
    def set_harmonic_order(self, order: int) -> None: ...
    def get_harmonic_order(self) -> int: ...
    
    def process(self, audio: AudioBuffer) -> AudioBuffer: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `drive` | `float` | Input drive/gain | 0.0 to 2.0 |
| `tone` | `float` | Tone control (high-frequency rolloff) | 0.0 to 1.0 |
| `level` | `float` | Output level | 0.0 to 2.0 |
| `order` | `int` | Maximum harmonic order | 2, 4, 6, or 8 |
| `audio` | `AudioBuffer` | Input audio buffer | Valid buffer |

**Output:** `AudioBuffer` — Distorted audio with even harmonics

---

## Edge Cases and Error Handling

- What happens if drive/level out of range? → Clamp to valid range
- What happens if harmonic order invalid? → Use default (4)
- What happens if audio buffer clipped? → Soft clip or wrap based on policy
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
| `test_drive_control` | Sets and gets drive correctly |
| `test_tone_control` | Sets and gets tone correctly |
| `test_level_control` | Sets and gets level correctly |
| `test_harmonic_order` | Sets harmonic order |
| `test_distortion` | Applies distortion correctly |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BF01: V-Even even harmonic distortion` message
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

*Specification based on Befaco V-Even module.*