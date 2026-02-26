# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT008_arbhar_granularizer.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

## Task: P3-EXT008 — arbhar_granularizer (ArbharGranularizer)

## Description

The Arbhar Granularizer is a sophisticated GPU-accelerated granular synthesis effect inspired by the Arbhar granular sampler. It creates complex, evolving textures by generating thousands of small audio-visual "grains" that are processed in real-time through shader-based rendering. The effect dynamically modulates grain parameters based on audio analysis, creating organic, reactive visual patterns that respond to beat intensity, tempo, and overall energy of the audio source.

This module represents a significant evolution from traditional granular synthesis by leveraging GPU parallel processing for real-time performance. The grains are not just visual elements but are part of a feedback system where previous outputs influence future generations, creating complex, self-similar patterns that evolve over time. The audio reactivity system maps specific audio features to granular parameters, allowing the visual output to dance in sync with the music's rhythm and intensity.

## What This Module Does

- Provides GPU-accelerated granular synthesis using shader-based processing
- Generates thousands of small grains that create complex, evolving textures
- Modulates grain parameters in real-time based on audio analysis (beat intensity, tempo, energy)
- Implements a feedback system where previous outputs influence future grain generation
- Creates organic, reactive visual patterns that sync with audio features
- Manages dual buffer system (grain buffer and feedback buffer) for smooth transitions
- Applies blend modes to composite processed grains with the original frame

## What This Module Does NOT Do

- Does not handle file I/O or persistence of grain states
- Does not provide manual grain positioning or individual grain control
- Does not implement traditional granular synthesis audio processing (visual grains only)
- Does not support CPU fallback mode for GPU rendering
- Does not handle audio analysis itself (relies on external AudioAnalyzer)
- Does not provide parameter smoothing or interpolation between frames

---

## Public Interface

```python
class ArbharGranularizer:
    def __init__(self) -> None: ...
    def set_frame_size(self, width: int, height: int) -> None: ...
    def set_audio_analyzer(self, audio_analyzer) -> None: ...
    def apply_uniforms(self, time: float, resolution: tuple[int, int], audio_reactor=None) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| width | int | Frame width for buffer creation | ≥ 1 |
| height | int | Frame height for buffer creation | ≥ 1 |
| audio_analyzer | AudioAnalyzer | Source of audio features | Must be set before apply_uniforms |
| time | float | Current playback time | ≥ 0 |
| resolution | tuple[int, int] | Output frame dimensions | Matches width/height |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for array operations — fallback: basic math
  - `pyglet` — for GPU rendering — fallback: CPU fallback mode
- Internal modules this depends on:
  - `core.effects.unified_base.ShaderBasedEffect`
  - `core.exceptions.ShaderCompilationError`
  - `core.rendering.Framebuffer`
  - `core.audio.AudioReactor`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing if GPU unavailable |
| `test_basic_operation` | apply_uniforms sets shader uniforms with default params |
| `test_audio_reactivity` | Audio features modulate grain parameters correctly |
| `test_cleanup` | set_frame_size and cleanup release buffers safely |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT008: arbhar_granularizer` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written