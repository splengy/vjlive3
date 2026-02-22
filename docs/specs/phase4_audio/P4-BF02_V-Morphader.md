# Spec: P4-BF02 — V-Morphader (Morphing Filter)

**File naming:** `docs/specs/phase4_audio/P4-BF02_V-Morphader.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BF02 — V-Morphader

**Phase:** Phase 4 / P4-BF02
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

V-Morphader is a morphing filter plugin for VJLive3. It provides two filter states (A and B) with continuous morphing between them, enabling dynamic filter sweeps, transitions, and evolving sound textures.

---

## What It Does NOT Do

- Does not provide distortion effects (filter only)
- Does not include multi-band filtering (single filter)
- Does not handle recording (playback only)
- Does not include automation (manual control only)

---

## Public Interface

```python
class VMorphaderPlugin:
    def __init__(self) -> None: ...
    
    def set_filter_a(self, frequency: float, q: float, gain: float) -> None: ...
    def get_filter_a(self) -> Tuple[float, float, float]: ...
    
    def set_filter_b(self, frequency: float, q: float, gain: float) -> None: ...
    def get_filter_b(self) -> Tuple[float, float, float]: ...
    
    def set_morph(self, morph: float) -> None: ...
    def get_morph(self) -> float: ...
    
    def set_mode(self, mode: str) -> None: ...
    def get_mode(self) -> str: ...
    
    def process(self, audio: AudioBuffer) -> AudioBuffer: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frequency` | `float` | Filter cutoff frequency in Hz | 20.0 to 20000.0 |
| `q` | `float` | Filter resonance | 0.1 to 20.0 |
| `gain` | `float` | Filter gain (dB) | -24.0 to 24.0 |
| `morph` | `float` | Morph position between A and B | 0.0 (A) to 1.0 (B) |
| `mode` | `str` | Filter mode | 'lowpass', 'highpass', 'bandpass', 'notch', 'peak' |
| `audio` | `AudioBuffer` | Input audio buffer | Valid buffer |

**Output:** `AudioBuffer` — Filtered audio with morphing

---

## Edge Cases and Error Handling

- What happens if parameters out of range? → Clamp to valid ranges
- What happens if morph invalid? → Clamp to 0.0-1.0
- What happens if filter mode invalid? → Use default (lowpass)
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
| `test_filter_a_b_setting` | Sets and gets filter A/B parameters |
| `test_morph_control` | Morphs between filter states |
| `test_mode_setting` | Changes filter modes |
| `test_filter_morphing` | Morphing produces smooth transitions |
| `test_audio_processing` | Processes audio correctly |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BF02: V-Morphader morphing filter` message
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

*Specification based on Befaco V-Morphader module.*