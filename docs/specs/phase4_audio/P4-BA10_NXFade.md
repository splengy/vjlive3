# Spec: P4-BA10 — NXFade (Crossfader)

**File naming:** `docs/specs/phase4_audio/P4-BA10_NXFade.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA10 — NXFade

**Phase:** Phase 4 / P4-BA10
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

NXFade is a crossfader plugin for VJLive3. It provides smooth crossfading between two audio sources with adjustable curve, preview functions, and DJ-style crossfader behavior, enabling seamless transitions between tracks.

---

## What It Does NOT Do

- Does not provide effects processing (crossfade only)
- Does not handle recording (playback only)
- Does not include beat matching (manual control only)
- Does not manage multiple sources (two inputs only)

---

## Public Interface

```python
class NXFadePlugin:
    def __init__(self) -> None: ...
    
    def set_fade_position(self, position: float) -> None: ...
    def get_fade_position(self) -> float: ...
    
    def set_fade_curve(self, curve: str) -> None: ...
    def get_fade_curve(self) -> str: ...
    
    def set_preview(self, channel: int, enabled: bool) -> None: ...
    def get_preview(self, channel: int) -> bool: ...
    
    def set_swap(self, enabled: bool) -> None: ...
    def get_swap(self) -> bool: ...
    
    def process(self, audio_a: AudioBuffer, audio_b: AudioBuffer) -> AudioBuffer: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `position` | `float` | Crossfade position | 0.0 (A) to 1.0 (B) |
| `curve` | `str` | Fade curve shape | 'linear', 'exponential', 'logarithmic', 's-curve' |
| `channel` | `int` | Channel for preview | 0 (A) or 1 (B) |
| `enabled` | `bool` | Preview/swap state | True/False |
| `audio_a` | `AudioBuffer` | Input A audio buffer | Valid buffer |
| `audio_b` | `AudioBuffer` | Input B audio buffer | Valid buffer |

**Output:** `AudioBuffer` — Crossfaded output audio

---

## Edge Cases and Error Handling

- What happens if position out of range? → Clamp to 0.0-1.0
- What happens if curve invalid? → Use default linear
- What happens if audio buffers different lengths? → Use shorter, pad with zeros
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
| `test_fade_position` | Sets and gets fade position |
| `test_fade_curve` | Changes fade curves |
| `test_preview_control` | Preview channels work |
| `test_swap` | Swap function works |
| `test_crossfade` | Crossfades correctly |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA10: NXFade crossfader` message
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

*Specification based on Bogaudio NXFade module.*