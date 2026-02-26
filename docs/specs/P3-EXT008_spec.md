# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT008_arbhar_granularizer.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

## Task: P3-EXT008 — arbhar_granularizer (ArbharGranularizer)

## Description

The Arbhar Granularizer is a sophisticated GPU-accelerated granular synthesis effect inspired by the Arbhar granular sampler. It creates complex, evolving textures by generating thousands of small audio-visual "grains" that are processed in real-time through shader-based rendering. The effect dynamically modulates grain parameters based on audio analysis, creating organic, reactive visual patterns that respond to beat intensity, tempo, and overall energy of the audio source.

This module represents a significant evolution from traditional granular synthesis by leveraging GPU parallel processing for real-time performance. The grains are not just visual elements but are part of a feedback system where previous outputs influence future generations, creating complex, self-similar patterns that evolve over time. The audio reactivity system maps specific audio features to granular parameters, allowing the visual output to dance in sync with the music's rhythm and intensity.

## What This Module Does

- Provides GPU-accelerated granular synthesis using shader-based processing via `ShaderBasedEffect` base class
- Generates thousands of small visual grains that create complex, evolving textures through fragment shader rendering
- Modulates grain parameters in real-time based on audio analysis features: `BEAT_INTENSITY`, `TEMPO`, and `ENERGY`
- Implements a feedback system where previous outputs influence future grain generation via dual framebuffer ping-pong
- Creates organic, reactive visual patterns that sync with audio features through parameter remapping
- Manages dual buffer system (grain buffer and feedback buffer) for smooth temporal transitions and accumulation
- Applies blend modes to composite processed grain output with the original input frame
- Handles framebuffer lifecycle: creates on `set_frame_size()`, deletes safely on resize/cleanup
- Integrates with `AudioReactor` wrapper to normalize audio feature values into 0.0-1.0 range

## What This Module Does NOT Do

- Does NOT handle file I/O or persistence of grain states (entirely in-memory, per-session)
- Does NOT provide manual grain positioning or individual grain control (grain positions are algorithmic/shaders)
- Does NOT implement traditional granular synthesis audio processing (visual grains only, no audio output)
- Does NOT support CPU fallback mode for GPU rendering (requires OpenGL/DirectX12/Vulkan-capable GPU)
- Does NOT handle audio analysis itself (relies on external `AudioAnalyzer` providing feature values)
- Does NOT provide parameter smoothing or interpolation between frames (parameters update instantly each frame)
- Does NOT manage the node graph or pipeline orchestration (caller invokes `process_frame()` per frame)
- Does NOT perform shader compilation (delegated to `ShaderBasedEffect` base class)

---

## Detailed Behavior

### Grain Generation Algorithm

The granular synthesis operates by rendering thousands of small grain sprites across the frame. The exact grain positions are computed in the fragment shader using a combination of:

- **Grid-based placement**: Grains are distributed across a virtual grid covering the entire framebuffer
- **Spray parameter**: Adds random offset to each grain's position, breaking up grid alignment for organic appearance
- **Grain size**: Controls the radius/diameter of each grain sprite (likely a soft-edged circle or textured particle)
- **Density**: Scales the number of grains; at maximum density, the grid is fully populated; at minimum, sparse placement

The shader likely uses a pseudo-random function seeded by pixel coordinates to determine grain presence and properties, ensuring deterministic output across frames unless parameters change.

### Audio Reactivity Mapping

When an `AudioReactor` is connected, the following automatic parameter remapping occurs each frame:

1. `BEAT_INTENSITY` (0.0-1.0) → boosts `intensity` (2.0→10.0) and `spray` (0.0→0.8)
2. `TEMPO` (0.0-1.0) → increases `grain_size` (0.1→1.0)
3. `ENERGY` (0.0-1.0) → raises `density` (0.2→1.0) and `feedback` (0.0→0.6)

The `audio_reactivity` parameter itself is set to the current `BEAT_INTENSITY`, providing a direct scalar for the shader to weight audio influence.

**Important:** These mappings are hard-coded in `apply_uniforms()`; they are not user-configurable. The user can only globally scale audio influence via the `audio_reactivity` parameter's default value (0.7), but this gets overwritten each frame when audio is active.

### Feedback Loop

The feedback system creates temporal accumulation:

1. `_grain_buffer` holds the current frame's grain rendering
2. `_feedback_buffer` holds the previous frame's final output (after blending)
3. If `feedback > 0`, the effect blends a portion of `_feedback_buffer` into `_grain_buffer` before final compositing
4. After returning the output frame, the caller (or internal logic) should copy `_grain_buffer` to `_feedback_buffer` for the next iteration

The legacy code shows `_apply_feedback()` as a placeholder; its implementation likely performs a full-screen shader pass or texture blit with a blend factor equal to `feedback`.

### Blend Modes

The final step composites the grain buffer with the original input frame using the `blend` parameter (0.0-1.0). The exact blend mode is unspecified but likely:

- `blend = 1.0` → show only grain buffer (full effect)
- `blend = 0.0` → show only original frame (no effect)
- Intermediate values → linear interpolation: `output = blend * grain_buffer + (1 - blend) * input_frame`

Alternatively, a more sophisticated blend (screen, add, overlay) could be used; the shader would implement it.

### Edge Cases

- **Zero audio reactor**: Parameters remain at their static defaults; no audio-driven modulation occurs
- **Extreme density (0.0)**: Very few grains; effect appears sparse
- **Extreme density (1.0)**: Maximum grain count; may cause visual clutter or performance drop
- **Feedback = 1.0**: Infinite temporal accumulation; previous frames never fully decay, creating smearing trails
- **Feedback = 0.0**: No temporal integration; each frame independent
- **Large grain_size (≥ 0.5)**: Grains may overlap heavily, reducing texture detail
- **Small grain_size (≤ 0.1)**: Grains become sub-pixel; effect may appear as noise or smooth texture

---

## Dependencies

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `intensity` | float | 5.0 | 0.0 - 10.0 | Controls the overall strength of the granular effect. Higher values produce more pronounced grain structures and visual density. |
| `grain_size` | float | 0.2 | 0.01 - 1.0 | Size of individual grains in normalized coordinates. Smaller values create finer textures; larger values produce chunkier, more visible grains. |
| `density` | float | 0.5 | 0.0 - 1.0 | Number of grains per unit area. At 1.0, maximum grain count is reached; at 0.0, minimal grains are generated. |
| `spray` | float | 0.3 | 0.0 - 1.0 | Random displacement applied to grain positions. Creates organic, non-uniform distribution vs. grid-aligned placement. |
| `feedback` | float | 0.1 | 0.0 - 1.0 | Blend ratio between current grain output and previous frame's output. At 0.0, no feedback; at 1.0, full temporal accumulation. |
| `blend` | float | 0.8 | 0.0 - 1.0 | Blend mode factor for compositing grain buffer with original input frame. Controls how much of the effect vs. original image is visible. |
| `audio_reactivity` | float | 0.7 | 0.0 - 1.0 | Global multiplier for audio feature influence. At 0.0, audio has no effect; at 1.0, full audio reactivity. |

**Note:** When audio reactor is active, these parameters are automatically remapped each frame based on audio features:
- `intensity` = 2.0 + `BEAT_INTENSITY` × 8.0
- `grain_size` = 0.1 + `TEMPO` × 0.9
- `density` = 0.2 + `ENERGY` × 0.8
- `spray` = `BEAT_INTENSITY` × 0.8
- `feedback` = `ENERGY` × 0.6
- `audio_reactivity` = `BEAT_INTENSITY`

---

## State Management

**Persistent State (lifetime of instance):**
- `parameters: dict` — Current parameter values (intensity, grain_size, density, spray, feedback, blend, audio_reactivity)
- `_frame_width: int` — Current framebuffer width (default 1920)
- `_frame_height: int` — Current framebuffer height (default 1080)
- `_audio_reactor: Optional[AudioReactor]` — Audio feature wrapper, set via `set_audio_analyzer()`

**Per-Frame State (updated in `process_frame()`):**
- `_grain_buffer: Framebuffer` — GPU framebuffer for grain rendering output
- `_feedback_buffer: Framebuffer` — GPU framebuffer storing previous frame's output for feedback accumulation

**Initialization:**
- Buffers are `None` until `set_frame_size()` is called
- Parameters initialized in `__init__()` with defaults listed above
- `ShaderBasedEffect` base class handles shader program loading/compilation

**Cleanup:**
- `Framebuffer.delete()` must be called on both buffers before destruction to release GPU resources
- No explicit `cleanup()` method in skeleton; implement via `__del__()` or manual resource management

---

## GPU Resources

**Shaders:**
- Vertex shader: Full-screen quad (standard, likely shared across effects)
- Fragment shader: `arbhar_granularizer.frag` — Contains grain generation logic, position calculation, color output
- Shader compilation handled by `ShaderBasedEffect` base class; may raise `ShaderCompilationError`

**Framebuffers (GPU memory):**
- `_grain_buffer` — RGBA texture attachment, dimensions = `(width, height)`
- `_feedback_buffer` — RGBA texture attachment, dimensions = `(width, height)`
- Both allocated in GPU VRAM; total memory ≈ 2 × width × height × 4 bytes (RGBA8)

**Resource Lifecycle:**
- Created in `set_frame_size()` when width/height change
- Deleted and recreated if `set_frame_size()` called with new dimensions
- Must be released before OpenGL context destruction to avoid memory leaks

---

## Integration

**Node Graph Position:**
- This is a **filter/effect node** that takes an input frame and produces a transformed output frame
- Expected to be placed in a processing pipeline where each frame passes through `process_frame()`

**Inputs:**
- `frame: np.ndarray` — Input image in HWC or CHW format (legacy code suggests HWC, shape `(H, W, 3)` or `(H, W, 4)`)
- `audio_data: Optional[np.ndarray]` — Raw audio samples (unused in current implementation but may be used for future extensions)

**Outputs:**
- `np.ndarray` — Processed frame with granular effect applied, same shape/format as input

**Connections:**
- `set_audio_analyzer(audio_analyzer)` — Connects to upstream `AudioAnalyzer` node providing feature extraction
- `apply_uniforms(time, resolution, audio_reactor)` — Called internally before rendering; sets shader uniform values
- `_update_grains()` — Updates grain positions/parameters (implementation detail, may be shader-based)
- `_apply_feedback()` — Blends previous output into current grain buffer based on `feedback` parameter

**Pipeline Flow:**
1. Caller invokes `process_frame(input_frame, audio_data)` each tick
2. `ArbharGranularizer` binds `_grain_buffer`, renders grains via shader
3. If `feedback > 0`, calls `_apply_feedback()` to blend `_feedback_buffer` into `_grain_buffer`
4. Blends `_grain_buffer` content with original `input_frame` using `blend` factor
5. Returns composited frame
6. `_grain_buffer` content is copied to `_feedback_buffer` for next frame (implicit in feedback step)

---

## Performance

**Expected Frame Rate Impact:**
- **GPU-bound**: Rendering thousands of grains in fragment shader is parallelized on GPU; expect 1-3ms per 1080p frame on modern GPU
- **Memory bandwidth**: Dual framebuffer ping-pong doubles texture memory traffic; may impact integrated GPUs
- **Target performance**: 60 FPS at 1920×1080 on discrete GPU (GTX 1060 / RX 580 equivalent or better)
- **Lower bound**: 30 FPS at 1080p on integrated GPU (Intel Iris Xe / AMD Vega 8)

**Memory Usage:**
- **GPU VRAM**: ~16 MB for two 1080p RGBA8 framebuffers (2 × 1920 × 1080 × 4 bytes)
- **System RAM**: Minimal; only stores parameter dict and small state objects (< 1 KB)
- **Audio feature buffer**: Negligible (few floats per frame)

**Optimization Notes:**
- Grain count likely controlled by `density` parameter; higher density = more fragment shader invocations
- `spray` parameter adds randomness but does not significantly impact performance
- Feedback pass adds one extra full-screen blend operation per frame
- Consider using half-float framebuffers (RGBA16F) if HDR processing is needed (would double VRAM usage)

---

## Error Cases

**Shader Compilation Failure:**
- **Exception:** `ShaderCompilationError` raised by `ShaderBasedEffect` base class if fragment shader fails to compile
- **Recovery:** Log error, fall back to no-op (return input frame unchanged). Effect becomes inert until shader fixed.
- **Detection:** Check shader status during `__init__()`; if failed, set `_shader = None` and skip rendering in `process_frame()`

**GPU Unavailable / OpenGL Context Lost:**
- **Exception:** Likely `RuntimeError` from `pyglet`/OpenGL when creating framebuffers or binding
- **Recovery:** Propagate exception to caller; pipeline should handle by disabling effect or attempting context restoration
- **Mitigation:** Check `set_frame_size()` for GPU errors; if framebuffer creation fails, set buffers to `None` and skip rendering

**Audio Reactor Not Set:**
- **Condition:** `apply_uniforms()` called with `audio_reactor=None`
- **Behavior:** Uses default parameter values from `self.parameters` (no audio modulation)
- **No exception:** Silent fallback to static parameters

**Invalid Parameter Values:**
- **Condition:** User manually sets `parameters[...]` outside declared ranges
- **Behavior:** Shader may produce undefined visual artifacts (clamping not enforced in code)
- **Mitigation:** Document ranges clearly; optionally add runtime validation in `apply_uniforms()` (not in legacy)

**Framebuffer Size Mismatch:**
- **Condition:** `resolution` passed to `apply_uniforms()` differs from `_frame_width/_frame_height`
- **Behavior:** Shader rendering may be stretched or clipped; undefined behavior
- **Recovery:** Ensure `set_frame_size()` is called with correct dimensions before first `process_frame()`

**Memory Leak:**
- **Condition:** `set_frame_size()` called repeatedly without deleting old buffers
- **Legacy behavior:** Code checks `if self._grain_buffer is not None: self._grain_buffer.delete()` before recreating — this is correct
- **Risk:** If `delete()` fails silently, VRAM leak accumulates. Monitor GPU memory in long-running sessions.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module instantiates without crashing even if GPU unavailable (mock GPU errors) |
| `test_basic_operation` | `apply_uniforms()` sets all 7 shader uniforms with default params when `audio_reactor=None` |
| `test_audio_reactivity` | When `audio_reactor` provides feature values, parameters are remapped according to formulas and uniforms updated |
| `test_cleanup` | `set_frame_size()` creates buffers; calling again with new size deletes old buffers and creates new ones without leaks |
| `test_feedback_blend` | `_apply_feedback()` correctly blends `_feedback_buffer` into `_grain_buffer` based on `feedback` parameter |
| `test_parameter_ranges` | Setting parameters to extreme values (0.0, 1.0, 10.0) does not crash shader and produces expected visual extremes |
| `test_missing_audio_analyzer` | `process_frame()` works when `set_audio_analyzer()` never called (uses static defaults) |
| `test_shader_compilation_error` | Simulate shader compile failure; effect returns input frame unchanged and does not crash |

**Minimum coverage:** 80% before task is marked done.

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