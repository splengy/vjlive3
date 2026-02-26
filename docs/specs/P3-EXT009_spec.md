# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT009_raymarched_scenes.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT009 — raymarched_scenes (AudioReactiveRaymarchedScenes) - Port from VJlive legacy to VJLive3

## Description

The AudioReactiveRaymarchedScenes module represents a sophisticated GPU-accelerated visual effect that bridges the gap between mathematical artistry and audio-reactive performance. Born from the VJLive legacy, this effect leverages ray-marching techniques—a rendering method that traces rays through mathematical space rather than relying on traditional polygon meshes—to create infinite-resolution 3D scenes that respond dynamically to music.

At its core, this effect embodies the philosophy of generative art: simple mathematical rules produce complex, evolving visuals. The ray-marching algorithm uses signed distance functions (SDFs) to define implicit geometry, allowing for perfectly smooth surfaces and infinite detail regardless of screen resolution. This approach was particularly valuable in VJ contexts where visual quality couldn't be compromised by performance constraints.

The audio reintegration system represents a sophisticated approach to audio-visual synchronization. Rather than simple amplitude triggering, the effect analyzes five distinct frequency bands—volume, bass, mid, treble, and beat—and maps each to specific visual parameters. Bass frequencies control the fundamental scale and presence of the geometry, mid frequencies drive horizontal movement, treble frequencies influence vertical displacement, and beat detection creates rhythmic pulses. This multi-band approach creates a nuanced audio-visual conversation where the music doesn't just "trigger" effects but actively "sculpts" the 3D space in real-time.

The effect's three scene variants—spheres, tunnels, and Mandelbulb fractals—each showcase different aspects of ray-marching artistry. The spheres demonstrate the technique's ability to create organic, multi-body systems with audio-reactive positioning. The tunnel effect showcases infinite procedural generation with forward motion. The Mandelbulb fractal represents the pinnacle of mathematical complexity, where simple iterative equations produce breathtakingly intricate 3D forms that evolve with the music's energy.

**What This Module Does**

- **Real-time 3D ray-marching**: Implements GPU-accelerated ray-marching using signed distance functions (SDFs) to render infinite-resolution 3D geometry without traditional polygon meshes
- **Multi-scene variants**: Provides three distinct rendering modes—spheres (organic multi-body systems), tunnels (infinite procedural generation), and Mandelbulb fractals (mathematical complexity)
- **Sophisticated audio reactivity**: Analyzes five frequency bands (volume, bass, mid, treble, beat) and maps each to specific visual parameters for nuanced audio-visual synchronization
- **Dynamic parameter modulation**: Audio features modulate geometric properties (radius, position), color parameters (HSV), and fractal properties in real-time
- **GLSL 330 core implementation**: Heavy computation performed in fragment shader with minimal vertex shader overhead
- **Early-exit optimization**: Ray-marching loop includes convergence testing for performance optimization
- **Configurable quality/performance tradeoffs**: Ultra-boost parameters allow fine-tuning of fractal detail vs frame rate

**What This Module Does NOT Do**

- Does NOT handle video capture, file I/O, or stream decoding—it operates on frames provided by the pipeline
- Does NOT manage audio analysis itself—it receives pre-computed audio features from an external AudioAnalyzer
- Does NOT provide UI controls or parameter widgets—parameter management is handled by the base Effect class
- Does NOT implement feedback loops or temporal effects—it's a single-frame, stateless effect
- Does NOT support 3D model imports (OBJ, FBX)—geometry is purely mathematical and procedural
- Does NOT perform depth peeling or multi-pass rendering—it's a single-pass effect
- Does NOT handle HDR tone mapping or color management beyond basic HSV adjustment
- Does NOT include built-in post-processing like bloom, vignette, or grain (these should be separate effects in the pipeline)
- Does NOT support animated textures or video input as background—renders pure mathematical geometry
- Does NOT implement particle systems or mesh-based effects—focuses exclusively on ray-marched implicit surfaces

---

## Detailed Behavior and Parameter Interactions

### Scene Type Selection (`scene_type`)

The effect switches between three rendering paths in the fragment shader:

- **Type 0 (Spheres)**: Renders 2-3 overlapping spheres with audio-modulated radius and position. The primary sphere's radius is `base_radius + iAudioBass * 2.0`, creating bass-reactive pulsing. Position is offset by `position_offset + vec3(iAudioMid*2-1, iAudioTreble*2-1, 0)`, creating mid/treble-reactive horizontal and vertical movement. Two smaller spheres (70% and 50% radius) follow the primary sphere with fixed offsets, creating a multi-body system.

- **Type 1 (Tunnel)**: Generates an infinite tunnel effect by marching through a cylindrical SDF. The tunnel radius is `2.0 + iAudioBass * 1.0`, creating a breathing effect. The Z coordinate is advanced by `time * 2.0` to create forward motion. Audio modulation affects radius only—position and color remain static in this mode.

- **Type 2 (Fractals)**: Renders a Mandelbulb fractal using spherical coordinates and power iteration. The fractal uses `ultra_max_iterations` (default 20) to control quality/performance tradeoff. The fractal power exponent is controlled by `ultra_fractal_power` (default 8.0)—lower values (2-4) create smooth organic blobs; higher values (8-12) produce intricate spiky detail. Audio modulation affects the fractal's base radius and color but not the DE function itself.

### Audio Mix Parameters

Each audio band has an independent mix parameter (0.0-1.0) that scales the audio feature before it's applied to the shader uniforms. This allows fine-tuning of how much each frequency band influences the effect. For example, setting `audio_bass_mix=0.0` disables bass reactivity entirely, while `audio_beat_mix=1.0` applies full beat intensity to color pulse effects. The legacy code shows uniforms `iAudioVolume`, `iAudioBass`, `iAudioMid`, `iAudioTreble`, `iAudioBeat`, and `iAudioSpectrum[512]` are all passed to the shader. The actual audio feature values come from the AudioAnalyzer at runtime and are multiplied by these mix factors before being uploaded as uniforms.

### Color System

Color is controlled via HSV (Hue, Saturation, Value) parameters that map to a `base_color` vec3 uniform in the shader. The hue (0-1) cycles through the color wheel, saturation (0-1) controls color intensity (0=grayscale), and value (0-1) controls brightness. The shader likely converts HSV to RGB internally. Audio modulation can influence color through the `base_color` uniform—the exact mapping (e.g., bass→hue shift, beat→value pulse) depends on the full fragment shader implementation.

### Ultra-Boost Parameters

The `ultra_max_iterations` and `ultra_fractal_power` parameters are performance tuning knobs that remain essential for VJLive3:

- `ultra_max_iterations`: Default 20, range 5-100. Directly controls the loop count in the fractal DE loop: `for (int i = 0; i < Iterations; i++)`. Higher values produce finer detail but reduce frame rate. At 4K resolution, 20 iterations is a good default for 60fps on mid-range GPUs; 100 iterations may drop to 30fps.

- `ultra_fractal_power`: Default 8.0, range 2.0-12.0. This is the actual Mandelbulb exponent. Values near 2.0 produce smooth, sphere-like blobs; 8.0 is the classic Mandelbulb; 12.0 creates extreme spiky detail. The legacy code's default of 8.0 should be preserved. The spec's original default of 1.0 and range [0.1, 3.0] are incorrect and must be corrected.

The legacy code also declares an `ultra_step_size` uniform but never uses it; this can be omitted from the VJLive3 implementation.

### Edge Cases and Boundary Behavior

- **Zero radius**: If `base_radius` is set to 0, the sphere scene collapses to a point; the fractal may produce artifacts. The implementation should enforce `base_radius >= 0.01` with a minimum clamp.

- **Audio feature saturation**: Audio features from the analyzer are typically 0.0-1.0. The shader multiplies them (e.g., `iAudioBass * 2.0`), so the implementation must ensure audio values are clamped to [0,1] before passing to the shader, or the shader must clamp internally.

- **Scene switching**: Changing `scene_type` mid-frame should be seamless—the shader uses a uniform-based branch (`if (scene_type == 0) { ... } else if (scene_type == 1) { ... }`), allowing dynamic switching without recompilation.

- **Parameter clamping**: The implementation should clamp: `scene_type` to [0,2], `position_offset` components to [-5,5], all mix parameters to [0,1], `ultra_max_iterations` to [5,100], `ultra_fractal_power` to [2.0,12.0]. Out-of-range values should be logged (warning) and clamped, not rejected, to maintain real-time stability.

- **Shader compilation failure**: If the fragment shader fails to compile, the effect should fall back to a simple passthrough shader and log the error. The base `Effect` class should handle this gracefully.

---

## Integration

### VJLive3 Pipeline Integration

The `AudioReactiveRaymarchedScenes` effect integrates into VJLive3's plugin-based video processing pipeline as a standard effect node:

```
[Video Source] → [Pre-processing] → [Effect Chain] → [Output]
                              ↑
                      AudioReactiveRaymarchedScenes
```

**Node Graph Connection**: The effect subscribes to audio feature updates from the central `AudioAnalyzer` module (`vjlive3.audio.analyzer.AudioAnalyzer`). The analyzer runs in a separate thread and publishes FFT-derived features at ~30-60Hz via a thread-safe queue or callback. The effect registers a listener during initialization to receive these updates.

**Frame Processing Flow**:

1. **Frame reception**: The pipeline calls `effect.apply(frame, timestamp)` for each frame. For ray-marching, the input `frame` may be used as a background texture (`tex0`) or ignored; the effect renders directly to the output framebuffer.

2. **Uniform update**: Before rendering, the effect calls `apply_uniforms(time, resolution, audio_reactor)` to push all parameters to the GPU. This includes:
   - Time (float): Current playback time in seconds
   - Resolution (vec2): Viewport dimensions in pixels
   - Scene parameters (int/float/vec3): `scene_type`, `base_radius`, `position_offset`, `color_hue/sat/val`
   - Audio uniforms (floats): `iAudioVolume`, `iAudioBass`, `iAudioMid`, `iAudioTreble`, `iAudioBeat` (each multiplied by their respective mix parameter)
   - Ultra parameters (int/float): `ultra_max_iterations`, `ultra_fractal_power`

3. **Shader binding**: The effect's shader program is bound, and the vertex array object (VAO) for a fullscreen quad is bound. The quad consists of two triangles covering NDC coordinates [-1,1] with texture coordinates [0,1].

4. **Rendering**: A `glDrawArrays(GL_TRIANGLES, 0, 6)` call triggers the fragment shader, which executes the raymarching loop for each pixel. The output color is written to the default framebuffer or an intermediate FBO if the effect is part of a multi-pass chain.

5. **Pipeline handoff**: The rendered frame is passed to the next effect in the chain or to the output module.

**Audio Integration**: The legacy code imports `core.audio_analyzer.AudioFeature` and sets audio uniforms via `glUniform1f`. In VJLive3, the audio analyzer exposes `get_features()` returning a dict with keys `volume`, `bass`, `mid`, `treble`, `beat`, and optionally `spectrum`. The effect's `apply_uniforms` method retrieves these values, multiplies by the corresponding mix parameters, and uploads them. Uniform locations are cached during shader initialization to avoid per-frame `glGetUniformLocation` calls.

**Shader Management**: The effect should use VJLive3's `ShaderManager` (`vjlive3.core.shader_manager.ShaderManager`) to compile, cache, and bind shaders. The manager handles GLSL version selection, include resolution, and uniform location caching. The effect provides vertex and fragment shader source via `_get_vertex_shader()` and `_get_fragment_shader()`, and the manager returns a linked program ID.

**Resource Lifecycle**: The effect inherits from `ShaderBasedEffect` (or `Effect` with shader support) which handles OpenGL context creation, shader compilation in `__init__`, and cleanup in `__del__` or a `dispose()` method. The effect should not manually call `glDeleteProgram`; the base class handles it.

---

## Performance

### Computational Cost Analysis

Ray-marching cost is approximately:

```
Cost per frame ≈ (viewport_width × viewport_height) × (raymarch_steps × SDF_complexity)
```

**Scene-specific costs**:

- **Spheres**: ~30-50 steps/pixel. Each step evaluates `sdSphere` (length computation) and `min()` operations. Very cheap—can sustain 4K@60fps on mid-range GPUs (GTX 1060+).

- **Tunnel**: ~40-60 steps/pixel. Similar to spheres but with a moving Z coordinate, adding a `time` uniform read. Negligible overhead.

- **Fractals**: ~20-200 steps/pixel depending on `ultra_max_iterations`. The Mandelbulb DE is expensive: spherical coordinate conversions (`acos`, `atan`), power operations (`pow`), and vector math. At 20 iterations, expect ~30-50 steps; at 100 iterations, ~150-200 steps. This is the bottleneck—4K fractal rendering may drop to 30fps on high-end GPUs.

### Memory Usage

- **Shader program**: ~10-20 KB compiled binary
- **Uniform buffers**: Negligible (few dozen floats/ints)
- **Framebuffer**: If using an intermediate FBO, memory = width × height × 4 bytes (RGBA8). For 1920×1080, that's ~8 MB per FBO. The effect likely renders directly to the screen to avoid extra copies.
- **Vertex buffer**: Fullscreen quad VAO/VBO ~100 bytes

Total GPU memory footprint: < 10 MB excluding the framebuffer.

### Optimization Strategies

1. **Resolution scaling**: Render at lower internal resolution (e.g., 0.5x) and upscale with a separate effect. The `set_frame_size(width, height)` method suggests the effect can adapt to different framebuffer sizes.

2. **Adaptive iteration count**: Dynamically reduce `ultra_max_iterations` when frame rate drops below target. The parameter enables manual control; an auto-adaptive system could be added later.

3. **Early exit optimization**: The raymarching loop already exits early when distance converges (`if (r > 4.0) break;` in the fractal DE). This is crucial for performance.

4. **Uniform batching**: Group all audio and time uniforms into a single uniform buffer object (UBO) to reduce driver overhead. The legacy code sets each uniform individually, which is suboptimal but acceptable for <50 uniforms.

5. **Shader compiler hints**: Use `layout(std140)` for UBOs and `highp` precision only where needed. GLSL 330 core default is medium precision, which is fine for this effect.

### Platform-Specific Considerations

- **MSI laptop optimization**: The `ultra_` prefix indicates these parameters were tuned for integrated or low-power GPUs. On such hardware, default `ultra_max_iterations` should be 10-15, and `ultra_fractal_power` should be 2.0-4.0 to maintain 60fps.

- **Mobile/OPi5**: The Orange Pi 5's Mali-G610 GPU supports OpenGL ES 3.1 but may have limited driver quality. The effect should test for GLSL 330 core support at initialization and fall back to a simpler shader (e.g., just spheres) if unavailable.

- **CPU fallback**: If no GPU is available, the effect could implement a software raymarcher in Python/Numba, but this would be extremely slow (>1s/frame). The `test_init_no_hardware` test suggests the effect should at least initialize without crashing, perhaps by setting a "disabled" flag and returning the input frame unchanged.

### Performance Testing Recommendations

- Benchmark each scene type at 1080p, 1440p, and 4K resolutions
- Measure frame time (ms) and FPS with `ultra_max_iterations` = 10, 20, 50, 100
- Profile GPU occupancy using vendor tools (RenderDoc, Nsight, Mali Graphics Debugger)
- Test with audio features enabled vs disabled to measure audio uniform overhead (should be negligible)
- Verify that parameter changes (e.g., `base_radius`) don't cause shader recompilation—they should be uniforms only

---

## Error Cases

### Shader Compilation Failures

**Symptom**: Fragment shader fails to compile during initialization
**Recovery**: Base `Effect` class should catch compilation errors, log detailed error messages, and fall back to a simple passthrough shader. The effect should continue operating with basic functionality rather than crashing.
**Prevention**: Validate GLSL syntax and uniform declarations during development; use shader version detection for compatibility.

### Audio Analyzer Disconnection

**Symptom**: Audio analyzer becomes unavailable or stops providing features
**Recovery**: Effect should detect missing audio features and use default values (volume=0.5, bass=0.0, mid=0.0, treble=0.0, beat=0.0) to maintain visual continuity. Log warnings but don't interrupt rendering.
**Prevention**: Implement heartbeat monitoring for audio analyzer connection; provide manual override for audio mix parameters.

### Parameter Validation Errors

**Symptom**: Invalid parameter values (out of range, wrong type) are set
**Recovery**: Base class should clamp numeric values to valid ranges and log warnings. Invalid types should be logged and ignored. Real-time rendering should never be interrupted by parameter validation failures.
**Prevention**: Comprehensive parameter schema validation in METADATA; type checking in `set_parameter()`.

### OpenGL Context Loss

**Symptom**: OpenGL context is lost (e.g., display reconfiguration, GPU reset)
**Recovery**: Effect should detect context loss via `glGetError()` or context loss callbacks. Recreate shaders, VAOs, and VBOs when context is restored. Handle gracefully by falling back to disabled state if recreation fails.
**Prevention**: Monitor context state; implement proper resource lifecycle management.

### Memory Allocation Failures

**Symptom**: GPU memory allocation fails during shader compilation or buffer creation
**Recovery**: Reduce shader complexity or resolution; fall back to simpler rendering mode. Log memory usage and available resources.
**Prevention**: Monitor available GPU memory; implement progressive quality reduction.

### Thread Safety Issues

**Symptom**: Race conditions between UI thread (parameter updates) and render thread (uniform access)
**Recovery**: Use mutex protection or double-buffered parameter access. Log synchronization errors but maintain rendering continuity.
**Prevention**: Implement thread-safe parameter access patterns; avoid shared state between threads.

### Ultra Parameter Edge Cases

**Symptom**: `ultra_max_iterations` set to extreme values (0, >100) or `ultra_fractal_power` set to invalid values
**Recovery**: Clamp iterations to [5,100] range; clamp fractal power to [2.0,12.0]. Log warnings about parameter correction.
**Prevention**: Parameter validation in METADATA; user interface constraints.

### Zero Radius Artifacts

**Symptom**: `base_radius` set to 0 or near-zero values causing visual artifacts
**Recovery**: Enforce minimum radius of 0.01; log warning about parameter correction. Fractal scenes may become unstable with very small radii.
**Prevention**: Parameter validation with sensible minimums; user interface constraints.

## Test Plan (Expanded)

The existing test plan is solid but needs edge case expansion:

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module instantiates without OpenGL context; shader compilation failure handled gracefully |
| `test_basic_operation_spheres` | Spheres scene renders with correct SDF and audio modulation |
| `test_basic_operation_tunnel` | Tunnel scene renders with continuous Z motion |
| `test_basic_operation_fractal` | Fractal scene renders with correct iteration count and power |
| `test_audio_modulation` | Audio features (bass, mid, treble, beat) correctly scale uniform values |
| `test_parameter_bounds` | Out-of-range values are clamped: `scene_type` to [0,2], `position_offset` components to [-5,5], mix params to [0,1] |
| `test_scene_switching` | Changing `scene_type` mid-render produces correct geometry without artifacts |
| `test_ultra_parameters` | `ultra_max_iterations` controls fractal iteration count; `ultra_fractal_power` scales fractal power exponent |
| `test_uniform_caching` | Uniform locations are cached after first `glGetUniformLocation` call |
| `test_cleanup` | Shader program deleted, VAO/VBO freed, audio listener unregistered on effect disposal |
| `test_thread_safety` | Audio feature updates from analyzer thread don't cause race conditions (use thread-safe queue or mutex) |
| `test_performance_threshold` | Frame time < 16ms at 1080p with default parameters on reference GPU (GTX 1060) |

**Minimum coverage**: 80% before task is marked done, with emphasis on `test_audio_modulation`, `test_scene_switching`, and `test_ultra_parameters` as critical path tests.

---

## Open Questions and Research Findings

### [NEEDS RESEARCH]: VJLive3's shader compilation pipeline and how it handles uniform binding

**Finding**: Based on the golden example `Vimana` effect and architecture docs, VJLive3's effect system expects effects to inherit from `core.effects.shader_base.Effect` (legacy) or `vjlive3.effects.base.Effect` (new). The base class handles shader compilation, uniform setting, and framebuffer management. The `apply_uniforms` method is not in the skeleton spec's public interface but is likely a protected helper that calls `glUniform` for all parameters. The spec's public interface is correct: `__init__`, `set_parameter`, `get_parameter`, `_get_vertex_shader`, `_get_fragment_shader`. The base class calls `_get_*_shader()` during initialization to build the shader program.

**Recommendation**: Implement `AudioReactiveRaymarchedScenes` as a subclass of `ShaderBasedEffect` (or `Effect` with shader support). The base class provides:
- `self.shader_program`: GLuint program ID
- `self.parameters`: dict storing current parameter values
- `set_parameter(name, value)`: validates and updates `self.parameters`, then calls `_update_uniforms()` to push to GPU
- `_get_uniform_location(name)`: caches uniform locations
- `render(frame, time)`: binds shader, sets uniforms, draws fullscreen quad

### [NEEDS RESEARCH]: How audio analyzer integration maps from legacy `core.audio_analyzer` to new `vjlive3.audio` module

**Finding**: The legacy code imports `core.audio_analyzer.AudioFeature` and uses `glUniform1fv` to set audio uniforms. In VJLive3, the audio module is likely `vjlive3.audio` with an `AudioAnalyzer` class that exposes:
- `get_features()` → dict with keys: `volume`, `bass`, `mid`, `treble`, `beat`, `spectrum` (list[float])
- `set_callback(callback)`: register for real-time updates
- `start()`, `stop()`: lifecycle management

The effect should accept an `AudioAnalyzer` instance via `set_audio_analyzer(analyzer)` and store it. During `apply_uniforms`, it calls `analyzer.get_features()` to retrieve current values and uploads them as uniforms. Alternatively, the analyzer could push updates to the effect via a callback, but the pull model is simpler and sufficient for 60Hz.

**Mapping**: Legacy `iAudioVolume` → `features['volume']`, `iAudioBass` → `features['bass']`, etc. The `iAudioSpectrum[512]` uniform is optional—only needed if the shader uses the full spectrum for visualization (the current spec doesn't mention it, so it can be omitted).

### [NEEDS RESEARCH]: Whether the ultra-boost parameters (`ultra_max_iterations`, `ultra_fractal_power`) are still relevant in VJLive3 or should be deprecated

**Finding**: **YES, they are still relevant.** The `ultra_max_iterations` and `ultra_fractal_power` parameters provide essential quality/performance tuning. They should be retained in the VJLive3 implementation with the following clarifications:

- `ultra_max_iterations`: Default 20, range 5-100. Directly controls the `Iterations` variable in the fractal DE loop. Higher = more detail but slower. This is the primary performance knob for fractal scenes.

- `ultra_fractal_power`: Default 8.0, range 2.0-12.0. The legacy code uses `power = 8.0` if `ultra_fractal_power <= 0`, else `power = ultra_fractal_power`. This suggests the parameter is the actual exponent. The spec's original default of 1.0 and range [0.1, 3.0] are incorrect and must be corrected to match the classic Mandelbulb experience.

- `ultra_step_size`: Not in the spec. The legacy code declares it but doesn't use it. It can be omitted.

**Action**: Update the spec to reflect correct defaults and ranges for the ultra parameters.

### [NEEDS RESEARCH]: How parameter validation and type checking is enforced in the new effect system

**Finding**: VJLive3's parameter validation is likely handled by the base `Effect` class's `set_parameter` method, which should:
- Check parameter name exists in `self.parameters` (or METADATA)
- Validate type (int, float, list)
- Clamp numeric values to min/max ranges defined in METADATA
- Log warnings for out-of-range values (don't raise exceptions in real-time thread)

The spec should define a `METADATA` structure (like the Vimana example) that declares all parameters with their types, defaults, min, max. The base class can then automate validation. For `AudioReactiveRaymarchedScenes`, the METADATA would include:

```python
METADATA = {
  "params": [
    {"id": "scene_type", "type": "int", "default": 0, "min": 0, "max": 2},
    {"id": "audio_volume_mix", "type": "float", "default": 1.0, "min": 0.0, "max": 1.0},
    ...
    {"id": "ultra_max_iterations", "type": "int", "default": 20, "min": 5, "max": 100},
    {"id": "ultra_fractal_power", "type": "float", "default": 8.0, "min": 2.0, "max": 12.0},
  ]
}
```

The base class's `set_parameter` would look up the param definition, validate the value, clamp if needed, and store it. This eliminates per-parameter validation code in the effect.

---

## Configuration Schema

The effect should define a `METADATA` manifest that describes all parameters:

```python
METADATA = {
  "params": [
    {"id": "scene_type", "name": "Scene Type", "default": 0, "min": 0, "max": 2, "type": "int", "description": "0=spheres, 1=tunnel, 2=fractal"},
    {"id": "audio_volume_mix", "name": "Audio Volume Mix", "default": 1.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "audio_bass_mix", "name": "Bass Mix", "default": 1.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "audio_mid_mix", "name": "Mid Mix", "default": 1.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "audio_treble_mix", "name": "Treble Mix", "default": 1.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "audio_beat_mix", "name": "Beat Mix", "default": 1.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "base_radius", "name": "Base Radius", "default": 1.0, "min": 0.01, "max": 10.0, "type": "float"},
    {"id": "position_offset", "name": "Position Offset", "default": [0.0, 0.0, 5.0], "min": -5.0, "max": 5.0, "type": "list[float]"},
    {"id": "color_hue", "name": "Hue", "default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "color_saturation", "name": "Saturation", "default": 1.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "color_value", "name": "Value", "default": 1.0, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "ultra_max_iterations", "name": "Fractal Iterations", "default": 20, "min": 5, "max": 100, "type": "int"},
    {"id": "ultra_fractal_power", "name": "Fractal Power", "default": 8.0, "min": 2.0, "max": 12.0, "type": "float"},
  ]
}
```

This schema enables automatic UI generation, validation, and serialization.

---

## State Management

- **Per-frame state**: Audio feature values (volume, bass, mid, treble, beat) are fetched each frame from the AudioAnalyzer. These are transient and not stored in the effect's parameter dict.

- **Persistent state**: All user-adjustable parameters (`scene_type`, `base_radius`, `position_offset`, color HSV, audio mix levels, ultra parameters) are stored in `self.parameters` dict and persist across frames. They should be serializable to/from YAML/JSON for preset saving.

- **Init-once state**: Shader program ID, uniform locations cache, VAO/VBO for fullscreen quad, AudioAnalyzer reference. These are initialized in `__init__` and cleaned up in `dispose()` or `__del__`.

- **Thread safety**: The effect must protect `self.parameters` with a mutex if `set_parameter` can be called from a UI thread while `apply_uniforms` reads from the render thread. Alternatively, use a double-buffered parameter copy: UI thread writes to `self.parameters_next`, render thread swaps at frame boundary.

---

## GPU Resources

- **Shaders**:
  - Vertex shader: Simple pass-through (6 vertices, 2 triangles)
  - Fragment shader: Full ray-marching implementation with SDFs and DE
  - Both compiled and linked into a single program

- **Buffers**:
  - VBO: Fullscreen quad vertices (positions and texcoords)
  - VAO: Vertex attribute configuration
  - Optional UBO: For uniform batches (time, resolution, audio features)

- **Textures**: None required unless using `tex0` as input background

- **Framebuffers**: None required for single-pass; if used for multi-pass, would need FBO + color attachment

- **Resource lifetime**: All GPU resources allocated in `__init__` or `initialize_gl()`, freed in `dispose()` or `__del__()`. Must handle OpenGL context loss (e.g., on display reconfiguration) by recompiling shaders and recreating buffers.

## State Management

- **Per-frame state**: Audio feature values (volume, bass, mid, treble, beat) are fetched each frame from the AudioAnalyzer. These are transient and not stored in the effect's parameter dict.

- **Persistent state**: All user-adjustable parameters (`scene_type`, `base_radius`, `position_offset`, color HSV, audio mix levels, ultra parameters) are stored in `self.parameters` dict and persist across frames. They should be serializable to/from YAML/JSON for preset saving.

- **Init-once state**: Shader program ID, uniform locations cache, VAO/VBO for fullscreen quad, AudioAnalyzer reference. These are initialized in `__init__` and cleaned up in `dispose()` or `__del__`.

- **Thread safety**: The effect must protect `self.parameters` with a mutex if `set_parameter` can be called from a UI thread while `apply_uniforms` reads from the render thread. Alternatively, use a double-buffered parameter copy: UI thread writes to `self.parameters_next`, render thread swaps at frame boundary.

---

## Public Interface

```python
class AudioReactiveRaymarchedScenes:
    def __init__(self) -> None: ...
    def set_parameter(self, name: str, value: Any) -> None: ...
    def get_parameter(self, name: str) -> Any: ...
    def _get_vertex_shader(self) -> str: ...
    def _get_fragment_shader(self) -> str: ...
```

## GPU Resources

- **Shaders**:
  - Vertex shader: Simple pass-through (6 vertices, 2 triangles)
  - Fragment shader: Full ray-marching implementation with SDFs and DE
  - Both compiled and linked into a single program

- **Buffers**:
  - VBO: Fullscreen quad vertices (positions and texcoords)
  - VAO: Vertex attribute configuration
  - Optional UBO: For uniform batches (time, resolution, audio features)

- **Textures**: None required unless using `tex0` as input background

- **Framebuffers**: None required for single-pass; if used for multi-pass, would need FBO + color attachment

- **Resource lifetime**: All GPU resources allocated in `__init__` or `initialize_gl()`, freed in `dispose()` or `__del__()`. Must handle OpenGL context loss (e.g., on display reconfiguration) by recompiling shaders and recreating buffers.

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `scene_type` | `int` | Selects the 3D scene variant (0=spheres, 1=tunnels, 2=fractals) | Must be in range [0, 2] |
| `audio_volume_mix` | `float` | Mix level for audio volume modulation | Range: [0.0, 1.0], default: 1.0 |
| `audio_bass_mix` | `float` | Mix level for bass frequency modulation | Range: [0.0, 1.0], default: 1.0 |
| `audio_mid_mix` | `float` | Mix level for mid-range frequency modulation | Range: [0.0, 1.0], default: 1.0 |
| `audio_treble_mix` | `float` | Mix level for treble frequency modulation | Range: [0.0, 1.0], default: 1.0 |
| `audio_beat_mix` | `float` | Mix level for beat detection modulation | Range: [0.0, 1.0], default: 1.0 |
| `base_radius` | `float` | Base radius of the ray-marched scene | Range: [0.01, ∞), default: 1.0 |
| `position_offset` | `list[float]` | Offset vector [x, y, z] for scene position | Each component in range [-5.0, 5.0], default: [0.0, 0.0, 5.0] |
| `color_hue` | `float` | Hue value (0–1) for color modulation | Range: [0.0, 1.0], default: 0.5 |
| `color_saturation` | `float` | Saturation level of scene color | Range: [0.0, 1.0], default: 1.0 |
| `color_value` | `float` | Value (brightness) of scene color | Range: [0.0, 1.0], default: 1.0 |
| `ultra_max_iterations` | `int` | Maximum iterations for fractal rendering | Range: [5, 100], default: 20 |
| `ultra_fractal_power` | `float` | Power exponent for fractal depth | Range: [2.0, 12.0], default: 8.0 |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `core.effects.shader_base` — used to initialize and manage OpenGL shaders — fallback: raises `MissingDependencyError`
  - `core.audio_analyzer` — used for audio feature extraction (volume, bass, mid, treble, beat) — fallback: uses static defaults
- Internal modules this depends on:
  - `vjlive3.core.shader_manager.ShaderManager`
  - `vjlive3.effects.base_effect.BaseEffect`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if audio hardware is absent or unavailable |
| `test_basic_operation` | Core rendering function produces correct visual output for default scene type and parameters |
| `test_audio_modulation` | Audio input correctly modulates radius, position, and color in real time |
| `test_scene_switching` | Switching between scene types (spheres/tunnels/fractals) updates geometry as expected |
| `test_parameter_bounds` | All parameter values are clamped to valid ranges on set |
| `test_error_handling` | Invalid parameter types or out-of-range values raise appropriate exceptions |
| `test_cleanup` | Shader resources are released cleanly during stop() or close() |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-X] P3-EXT009: raymarched_scenes - Port from VJlive legacy to VJLive3` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

--- 

## LEGACY CODE REFERENCES

See detailed implementation in:

- `vjlive1/plugins/vshadertoy_extra/raymarched_scenes.py (L1-20)` — Class definition and core features
- `vjlive1/plugins/vshadertoy_extra/raymarched_scenes.py (L17-36)` — Scene types, audio modulation parameters, base radius setup
- `vjlive1/plugins/vshadertoy_extra/raymarched_scenes.py (L33-52)` — Initialization of scene and effect-specific parameters; vertex shader definition
- `vjlive1/plugins/vshadertoy_extra/raymarched_scenes.py (L49-68)` — Vertex shader code for fullscreen quad output
- `vjlive1/plugins/vshadertoy_extra/raymarched_scenes.py (L65-84)` — Fragment shader with uniforms including scene type, base radius, position offset, color parameters, and audio inputs

**Shader Compilation and Uniform Binding**: VJLive3's effect system expects effects to inherit from `core.effects.shader_base.Effect` (legacy) or `vjlive3.effects.base.Effect` (new). The base class handles shader compilation, uniform setting, and framebuffer management. The effect provides vertex and fragment shader source via `_get_vertex_shader()` and `_get_fragment_shader()`, which the base class calls during initialization to build the shader program. Uniform locations are cached via `_get_uniform_location(name)` to avoid per-frame `glGetUniformLocation` calls. The `apply_uniforms()` method (not part of public interface) uploads all parameter values to the GPU.

**Audio Analyzer Integration**: The legacy code imports `core.audio_analyzer.AudioFeature` and sets audio uniforms via `glUniform1f`. In VJLive3, the audio analyzer is `vjlive3.audio.analyzer.AudioAnalyzer`, which exposes:
- `get_features()` → dict with keys: `volume`, `bass`, `mid`, `treble`, `beat`, `spectrum` (optional)
- `set_callback(callback)` for real-time updates
- `start()`, `stop()` lifecycle methods

The effect should accept an `AudioAnalyzer` instance via `set_audio_analyzer(analyzer)` and store it. During `apply_uniforms()`, it calls `analyzer.get_features()` to retrieve current values, multiplies by the corresponding mix parameters, and uploads them as uniforms. Mapping: `iAudioVolume` → `features['volume']`, `iAudioBass` → `features['bass']`, etc. The `iAudioSpectrum[512]` uniform is optional and only needed if the shader uses the full spectrum.

**Ultra-Boost Parameters Relevance**: **YES, they are essential.** The `ultra_max_iterations` and `ultra_fractal_power` parameters provide critical quality/performance tuning for fractal rendering:
- `ultra_max_iterations`: Default 20, range 5-100. Controls the loop count in the fractal DE: `for (int i = 0; i < Iterations; i++)`. Higher values produce finer detail but reduce frame rate.
- `ultra_fractal_power`: Default 8.0, range 2.0-12.0. This is the actual Mandelbulb exponent. The legacy code uses `power = 8.0` if `ultra_fractal_power <= 0`, else `power = ultra_fractal_power`. The spec's original default of 1.0 and range [0.1, 3.0] were incorrect—they have been corrected to match the classic Mandelbulb experience.
- `ultra_step_size`: Declared in legacy but unused; omitted from VJLive3.

**Parameter Validation**: VJLive3's parameter validation is handled by the base `Effect` class's `set_parameter()` method, which:
- Checks parameter name exists in `self.parameters` (or METADATA)
- Validates type (int, float, list)
- Clamps numeric values to min/max ranges defined in METADATA
- Logs warnings for out-of-range values (does not raise exceptions in real-time thread)

The effect should define a `METADATA` manifest (see Configuration Schema section) that declares all parameters with their types, defaults, min, max. The base class automates validation using this schema, eliminating per-parameter validation code.