# Spec: P4-AR01 — Audio Reactive Collection

**File naming:** `docs/specs/phase4_audio/P4-AR01_Audio_Reactive_Collection.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-AR01 — Audio Reactive Collection

**Phase:** Phase 4 / P4-AR01
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Audio Reactive Collection ports and verifies all audio-reactive visual effects from the VJlive codebase. It includes plugins like Audio Reactive 3D, Audio Waveform Distortion, Audio Kaleidoscope, Audio Particle System, and any others discovered during audit. These plugins analyze audio and drive visual parameters in real-time.

---

## What It Does NOT Do

- Does not create new audio-reactive effects (ports only)
- Does not include audio processing (analysis only)
- Does not handle audio input routing (delegates to P1-A4)
- Does not provide UI for parameter mapping (plugin parameters only)

---

## Public Interface

```python
class AudioReactivePlugin:
    def __init__(self, audio_source: AudioSource, reactivity_params: ReactivityParams) -> None: ...
    
    def set_audio_source(self, source: AudioSource) -> None: ...
    def get_audio_source(self) -> AudioSource: ...
    
    def set_reactivity(self, param: str, value: float) -> None: ...
    def get_reactivity(self, param: str) -> float: ...
    
    def set_smoothing(self, smoothing: float) -> None: ...
    def get_smoothing(self) -> float: ...
    
    def update(self, audio_data: AudioBuffer, delta_time: float) -> None: ...
    def get_visual_params(self) -> VisualParams: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `audio_source` | `AudioSource` | Source of audio data | Valid source |
| `reactivity_params` | `ReactivityParams` | Reactivity configuration | Valid params |
| `param` | `str` | Reactivity parameter name | Non-empty |
| `value` | `float` | Parameter value | Valid range |
| `smoothing` | `float` | Smoothing time constant | 0.0 to 1.0 |
| `audio_data` | `AudioBuffer` | Audio samples | Valid buffer |
| `delta_time` | `float` | Time since last update | > 0 |

**Output:** `VisualParams` — Derived visual parameters (scale, color, motion, etc.)

---

## Edge Cases and Error Handling

- What happens if audio source missing? → Use last known values, log warning
- What happens if audio buffer empty? → Maintain previous state
- What happens if reactivity params invalid? → Clamp to defaults
- What happens on cleanup? → Release audio source, clear state

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for audio analysis — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.audio.audio_analyzer` (P1-A1)
  - `vjlive3.plugins.api` (for PluginBase)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_audio_source_setting` | Sets and gets audio source |
| `test_reactivity_params` | Sets and gets reactivity |
| `test_smoothing_control` | Smoothing works correctly |
| `test_update_cycle` | Updates from audio correctly |
| `test_visual_params` | Produces correct visual parameters |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-AR01: Audio reactive collection` message
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

*Specification for auditing and porting audio-reactive visual effects from VJlive.*