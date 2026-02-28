# Spec: P6-G1 — Morphagene Generator (Granular Synthesis)

**File naming:** `docs/specs/phase6_generators/P6-G1_Morphagene_Generator.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-G1 — Morphagene Generator

**Phase:** Phase 6 / P6-G1
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Morphagene Generator is a granular synthesis engine that manipulates audio buffers in real-time. It provides grain size control, density, pitch shifting, and randomization, creating evolving textures and soundscapes from any input audio source.

---

## What It Does NOT Do

- Does not include built-in audio effects (delegates to effect plugins)
- Does not handle audio file loading (delegates to audio sources)
- Does not provide CV control of parameters (manual control only)
- Does not include preset management (basic parameters only)

---

## Public Interface

```python
class MorphageneGenerator:
    def __init__(self) -> None: ...
    
    def set_buffer(self, audio: np.ndarray, sample_rate: int) -> None: ...
    def clear_buffer(self) -> None: ...
    
    def set_grain_size(self, size: float) -> None: ...
    def get_grain_size(self) -> float: ...
    
    def set_density(self, density: float) -> None: ...
    def get_density(self) -> float: ...
    
    def set_pitch(self, pitch: float) -> None: ...
    def get_pitch(self) -> float: ...
    
    def set_randomness(self, randomness: float) -> None: ...
    def get_randomness(self) -> float: ...
    
    def generate(self, num_samples: int) -> np.ndarray: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `audio` | `np.ndarray` | Source audio buffer | 1D float array |
| `sample_rate` | `int` | Sample rate | 8000-192000 |
| `size` | `float` | Grain size (normalized) | 0.001 to 1.0 |
| `density` | `float` | Grain density | 0.0 to 1.0 |
| `pitch` | `float` | Pitch shift factor | 0.25 to 4.0 |
| `randomness` | `float` | Randomization amount | 0.0 to 1.0 |
| `num_samples` | `int` | Output length | > 0 |

**Output:** `np.ndarray` — Granular synthesized audio

---

## Edge Cases and Error Handling

- What happens if buffer is empty? → Output silence
- What happens if grain size is too small? → May produce clicks
- What happens if density is 0? → Output silence
- What happens if pitch is extreme? → May cause artifacts
- What happens on cleanup? → Clear buffer, reset parameters

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for audio processing — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.plugins.PluginBase`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_buffer_setting` | Sets source buffer correctly |
| `test_grain_control` | Grain size affects output |
| `test_density_control` | Density affects output |
| `test_pitch_shift` | Pitch shifting works |
| `test_randomness` | Randomization affects output |
| `test_silence_input` | Handles empty buffer |
| `test_edge_cases` | Handles extreme parameters |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-6] P6-G1: Morphagene generator` message
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

*Specification based on VJlive-2 Morphagene Generator module.*