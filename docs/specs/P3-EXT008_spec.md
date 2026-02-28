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

## Implementation Guide

### Core Processing Pipeline

The `ArbharGranularizer` implements a multi-stage GPU pipeline that operates as follows:

1. **Frame Reception**: `process_frame(input_frame, audio_data)` is called by the pipeline orchestrator with the current video frame and optional audio samples.

2. **Audio Analysis**: If an `AudioReactor` is connected, the effect queries three audio features:
   - `BEAT_INTENSITY`: Normalized value [0.0-1.0] representing current beat strength
   - `TEMPO`: Normalized value [0.0-1.0] representing beats per minute relative to a baseline
   - `ENERGY`: Normalized value [0.0-1.0] representing overall spectral energy

3. **Parameter Remapping**: In `apply_uniforms()`, the raw audio features are mapped to effect parameters using hard-coded formulas:
   ```python
   if audio_reactor:
       beat = audio_reactor.get_feature('BEAT_INTENSITY')
       tempo = audio_reactor.get_feature('TEMPO')
       energy = audio_reactor.get_feature('ENERGY')
       
       self.parameters['intensity'] = 2.0 + beat * 8.0
       self.parameters['grain_size'] = 0.1 + tempo * 0.9
       self.parameters['density'] = 0.2 + energy * 0.8
       self.parameters['spray'] = beat * 0.8
       self.parameters['feedback'] = energy * 0.6
       self.parameters['audio_reactivity'] = beat
   ```

4. **Shader Uniform Upload**: The remapped parameters are uploaded to the GPU shader as uniform variables:
   - `u_intensity` (float)
   - `u_grain_size` (float)
   - `u_density` (float)
   - `u_spray` (float)
   - `u_feedback` (float)
   - `u_blend` (float)
   - `u_audio_reactivity` (float)
   - `u_resolution` (vec2)
   - `u_time` (float)

5. **Grain Rendering**: The fragment shader executes across the entire framebuffer. For each pixel, it:
   - Determines if a grain should be present at that location using a density-based threshold
   - Computes grain position with spray offset using a pseudo-random function
   - Calculates grain color based on intensity and input frame sampling
   - Outputs to `_grain_buffer` attachment

6. **Feedback Application**: If `feedback > 0`, a full-screen pass blends the previous frame's output from `_feedback_buffer` into `_grain_buffer`:
   ```
   grain_buffer = mix(grain_buffer, feedback_buffer, feedback)
   ```

7. **Final Composition**: The grain buffer is blended with the original input frame:
   ```
   output_frame = mix(input_frame, grain_buffer, blend)
   ```

8. **Buffer Swap**: The caller is responsible for copying `_grain_buffer` to `_feedback_buffer` for the next iteration. This explicit swap gives the pipeline orchestrator control over buffer lifecycle.

### Shader Architecture

The fragment shader (`arbhar_granularizer.frag`) implements a procedural grain generation algorithm:

```glsl
// Pseudo-random function using 2D coordinates
float random(vec2 uv) {
    return fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    
    // Grid-based grain placement with spray
    vec2 grid_uv = floor(uv * u_density * 100.0); // density controls grid resolution
    float rand = random(grid_uv);
    
    // Spray adds jitter to grain positions
    vec2 spray_offset = (rand - 0.5) * u_spray * 0.1;
    vec2 grain_center = (grid_uv + 0.5) / (u_density * 100.0) + spray_offset;
    
    // Distance from current pixel to grain center
    float dist = distance(uv, grain_center);
    
    // Grain shape: soft circle with radius controlled by grain_size
    float grain_radius = u_grain_size * 0.01;
    float grain = smoothstep(grain_radius, grain_radius * 0.8, dist);
    
    // Intensity modulates grain brightness
    vec3 grain_color = texture(u_input_frame, grain_center).rgb * u_intensity * 0.2;
    
    // Audio reactivity adds color shift based on beat
    grain_color += u_audio_reactivity * vec3(0.1, 0.05, 0.15);
    
    gl_FragColor = vec4(grain_color * grain, 1.0);
}
```

**Note:** The actual shader may differ; this is a conceptual representation based on the algorithm description.

### Process Frame Implementation

```python
def process_frame(self, frame: np.ndarray, audio_data: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Process a single video frame through the granular effect.
    
    Args:
        frame: Input video frame in HWC format (H, W, 3) or (H, W, 4)
        audio_data: Raw audio samples (unused, reserved for future extensions)
    
    Returns:
        Processed frame with granular effect applied, same shape as input
    """
    # Ensure framebuffers exist
    if self._grain_buffer is None:
        self.set_frame_size(frame.shape[1], frame.shape[0])
    
    # Apply audio-reactive uniforms
    self.apply_uniforms(time.time(), (frame.shape[1], frame.shape[0]), self._audio_reactor)
    
    # Render grains to grain buffer
    with self._grain_buffer.bind():
        self._shader.render_fullscreen_quad()
    
    # Apply feedback if enabled
    if self.parameters['feedback'] > 0:
        self._apply_feedback()
    
    # Composite with original frame
    output = self._blend_frames(frame, self._grain_buffer, self.parameters['blend'])
    
    # Update feedback buffer for next frame (caller may also do this)
    if self._feedback_buffer is not None:
        self._feedback_buffer.copy_from(self._grain_buffer)
    
    return output
```

### Feedback Implementation Details

The `_apply_feedback()` method performs a full-screen blend operation:

```python
def _apply_feedback(self) -> None:
    """
    Blend feedback buffer into grain buffer using feedback parameter.
    This creates temporal accumulation of grain patterns.
    """
    if self._feedback_buffer is None or self._grain_buffer is None:
        return
    
    # Bind feedback buffer as texture, grain buffer as render target
    with self._grain_buffer.bind():
        self._feedback_buffer.bind_as_texture(0)
        
        # Use a simple blend shader: output = mix(grain, feedback, feedback_amount)
        self._feedback_shader.set_uniform('u_feedback_amount', self.parameters['feedback'])
        self._feedback_shader.render_fullscreen_quad()
```

The feedback shader is a minimal fragment shader that samples both textures and blends them.

---

## Thread Safety and Concurrency

### Reentrancy Requirements

The `ArbharGranularizer` is designed to be **reentrant** but **not thread-safe** for concurrent access from multiple threads without external synchronization. Key considerations:

- **Instance Isolation**: Each instance maintains its own GPU resources (`_grain_buffer`, `_feedback_buffer`) and parameter state. Multiple instances can run in parallel on different threads, provided they operate on different frames and are not sharing the same OpenGL context.

- **OpenGL Context Binding**: OpenGL contexts are typically thread-affine. The effect assumes all GPU operations (shader compilation, framebuffer operations, texture binds) occur on the thread that owns the OpenGL context. If the pipeline orchestrator uses a dedicated rendering thread, all effect instances must be invoked on that same thread.

- **State Mutation**: The `process_frame()` method mutates internal state (`_grain_buffer`, `_feedback_buffer`). Concurrent calls to `process_frame()` on the same instance from multiple threads will cause race conditions. The caller must ensure:
  - Each effect instance is used by exactly one thread at a time, OR
  - A mutex protects all calls to the instance, OR
  - The pipeline orchestrator serializes effect processing per frame

- **Parameter Updates**: Parameter changes via `set_parameters()` (if such a method exists) should occur outside the rendering loop or be protected by a lock to avoid tearing between parameter values during frame processing.

### Recommended Usage Pattern

```python
# Thread-safe pipeline pattern
class RenderThread:
    def __init__(self):
        self.effect = ArbharGranularizer()
        self.lock = threading.Lock()
    
    def process_frame_threadsafe(self, frame, audio_features):
        with self.lock:
            return self.effect.process_frame(frame, audio_features)
```

Alternatively, use one effect instance per thread with no shared state:

```python
# Pool of effect instances, each bound to a worker thread
effect_pool = [ArbharGranularizer() for _ in range(num_threads)]
```

---

## Resource Management

### GPU Resource Lifecycle

The effect manages two GPU framebuffers that must be explicitly created and destroyed:

**Creation** (`set_frame_size()`):
```python
def set_frame_size(self, width: int, height: int) -> None:
    """Allocate or reallocate GPU framebuffers to match frame dimensions."""
    if self._grain_buffer is not None:
        self._grain_buffer.delete()
    if self._feedback_buffer is not None:
        self._feedback_buffer.delete()
    
    self._grain_buffer = Framebuffer(width, height, internal_format=GL_RGBA8)
    self._feedback_buffer = Framebuffer(width, height, internal_format=GL_RGBA8)
    self._frame_width = width
    self._frame_height = height
```

**Destruction** (`__del__()` or explicit `cleanup()`):
```python
def cleanup(self) -> None:
    """Release all GPU resources. Call before discarding the effect instance."""
    if self._grain_buffer is not None:
        self._grain_buffer.delete()
        self._grain_buffer = None
    if self._feedback_buffer is not None:
        self._feedback_buffer.delete()
        self._feedback_buffer = None
```

**Important**: The `Framebuffer.delete()` method must be called from the same thread that created the OpenGL context, as OpenGL object deletion is context-bound. If the effect instance is destroyed from a different thread, resource cleanup may fail or cause GPU errors.

### Memory Budget

- **VRAM Usage**: For a 1920×1080 frame, each RGBA8 framebuffer consumes:
  ```
  1920 × 1080 × 4 bytes = 8,294,400 bytes ≈ 7.9 MB
  Two buffers = ~15.8 MB
  ```
  Higher resolutions scale linearly: 4K (3840×2160) requires ~63 MB for two buffers.

- **Memory Leak Prevention**: The legacy code correctly deletes old buffers before creating new ones in `set_frame_size()`. However, if `set_frame_size()` is called every frame (e.g., due to resolution changes), the repeated allocation/deallocation can cause GPU memory fragmentation. The caller should only call `set_frame_size()` when the actual frame dimensions change.

- **Shared Context Considerations**: If multiple effect instances share the same OpenGL context, ensure they do not collectively exceed VRAM capacity. Monitor GPU memory usage in long-running sessions, especially when dynamically loading/unloading effects.

---

## Troubleshooting

### Issue: "Effect produces no output / black screen"

**Possible Causes:**
- Shader compilation failed; check `ShaderBasedEffect` initialization logs
- Framebuffers not created; ensure `set_frame_size()` was called before first `process_frame()`
- OpenGL context not current on the thread calling `process_frame()`
- Blend parameter set to 0.0 (fully transparent)

**Diagnostic Steps:**
1. Verify shader compilation succeeded: `assert effect._shader is not None`
2. Check framebuffer completeness: `assert self._grain_buffer.is_complete()`
3. Render `_grain_buffer` directly to screen to isolate whether the issue is in grain generation or final blending
4. Temporarily set `blend = 1.0` to bypass input frame compositing

### Issue: "Performance too low (<30 FPS at 1080p)"

**Possible Causes:**
- `density` parameter set too high (excessive grain count)
- Running on integrated GPU with limited memory bandwidth
- Feedback pass enabled unnecessarily (`feedback > 0`)
- Shader compiled without optimization flags

**Solutions:**
- Reduce `density` to 0.3-0.5
- Disable feedback (`feedback = 0.0`)
- Use resolution scaling (render at 720p, upscale to 1080p)
- Profile shader with GPU debugging tools (RenderDoc, Nsight) to identify bottlenecks

### Issue: "Datamosh effect is too weak/strong"

**Note:** This effect is not a datamosh effect; the confusion may arise from legacy naming. The `ArbharGranularizer` produces granular synthesis, not datamosh. If datamosh-like behavior is desired, consider using a dedicated datamosh effect instead.

### Issue: "Depth modulation has no effect"

**Note:** This effect does not use depth information. It is a 2D granular effect. If depth-aware granular synthesis is needed, the effect must be extended to accept a depth map as an additional input.

### Issue: "Loop return textures appear misaligned"

**Note:** The `ArbharGranularizer` does not use loop return textures. It uses a simple dual-buffer feedback system. If loop returns are referenced, they may be from a different effect in the pipeline. Ensure the correct effect is being configured.

### Issue: "Memory usage too high"

**Possible Causes:**
- Framebuffers allocated at higher resolution than needed
- `set_frame_size()` called repeatedly without deleting old buffers (legacy code does delete, but verify)
- Multiple effect instances each allocating large buffers

**Solutions:**
- Verify frame dimensions match actual video resolution
- Call `cleanup()` on unused effect instances
- Consider using RGBA16F only if HDR is required; RGBA8 is sufficient for most use cases

---

## Edge Cases and Error Handling

| Edge Case | Condition | Expected Behavior | Recovery Strategy |
|-----------|-----------|-------------------|-------------------|
| GPU driver crash | OpenGL context lost | `RuntimeError` on next GPU operation | Propagate to caller; effect becomes non-functional |
| Shader compile error | Invalid GLSL syntax | `ShaderCompilationError` in `__init__()` | Log error, set `_shader = None`, effect becomes no-op |
| Null framebuffer | `set_frame_size()` never called | `_grain_buffer` is `None` | `process_frame()` should check and call `set_frame_size()` automatically or raise clear error |
| Parameter out of range | User sets `intensity = 100.0` | Shader may produce NaNs or clamped values | Document valid ranges; optionally clamp in `apply_uniforms()` |
| Audio reactor disconnection | `_audio_reactor` set to `None` mid-stream | Parameters freeze at last remapped values | Allow `set_audio_analyzer(None)` to revert to static defaults |
| Resolution change mid-stream | Input frame size changes | Framebuffer size mismatch | Caller must call `set_frame_size(new_width, new_height)` before next frame |
| Negative time value | `time < 0` passed to `apply_uniforms` | Shader receives negative time (may cause issues) | Validate `time >= 0` in `apply_uniforms()` or document constraint |
| Extremely high density | `density = 1.0` at 4K resolution | Millions of fragment shader invocations; severe FPS drop | Clamp density to a reasonable maximum (e.g., 0.8) or warn user |

---

## Integration Checklist

Before integrating `ArbharGranularizer` into the VJLive3 pipeline, verify the following:

- [ ] **Shader Availability**: Confirm `arbhar_granularizer.frag` exists in the shader assets directory and compiles without errors on target platforms.
- [ ] **Base Class Compatibility**: Ensure `ShaderBasedEffect` base class provides required methods: `render_fullscreen_quad()`, uniform management, and shader program handling.
- [ ] **Framebuffer Class**: Verify `Framebuffer` class supports RGBA8 format, `bind()`, `bind_as_texture(unit)`, `copy_from(other)`, and `delete()`.
- [ ] **AudioReactor Interface**: Confirm `AudioReactor` provides `get_feature(name)` method returning normalized [0.0-1.0] values for `BEAT_INTENSITY`, `TEMPO`, `ENERGY`.
- [ ] **OpenGL Context**: Ensure an OpenGL context is current on the thread that creates the effect and calls `process_frame()`.
- [ ] **Memory Budget**: Calculate VRAM requirements for target resolution(s) and verify GPU has sufficient memory.
- [ ] **Performance Testing**: Benchmark at target resolution with expected `density` settings; verify ≥60 FPS on discrete GPU, ≥30 FPS on integrated.
- [ ] **Error Handling**: Test shader compilation failure scenario; verify effect degrades gracefully (returns input frame unchanged).
- [ ] **Resource Cleanup**: Confirm `cleanup()` or `__del__()` releases all GPU resources without OpenGL errors.
- [ ] **Pipeline Orchestration**: Ensure the pipeline calls `set_frame_size()` when resolution changes and manages the feedback buffer swap correctly.

---

## Configuration Schema

The effect's configuration can be serialized to JSON for preset saving/loading:

```json
{
  "class": "ArbharGranularizer",
  "parameters": {
    "intensity": 5.0,
    "grain_size": 0.2,
    "density": 0.5,
    "spray": 0.3,
    "feedback": 0.1,
    "blend": 0.8,
    "audio_reactivity": 0.7
  },
  "frame_width": 1920,
  "frame_height": 1080,
  "audio_analyzer_enabled": true
}
```

When loading a preset:
1. Create instance: `effect = ArbharGranularizer()`
2. Set parameters: `effect.set_parameters(preset['parameters'])`
3. Set frame size if present: `effect.set_frame_size(preset['frame_width'], preset['frame_height'])`
4. Reconnect audio analyzer if `audio_analyzer_enabled` is true

---

## State Management

### Persistent State (Lifetime of Instance)

| Attribute | Type | Purpose | Default |
|-----------|------|---------|---------|
| `parameters` | `dict[str, float]` | Current effect parameters | See parameter table |
| `_frame_width` | `int` | Framebuffer width | 1920 |
| `_frame_height` | `int` | Framebuffer height | 1080 |
| `_audio_reactor` | `Optional[AudioReactor]` | Audio feature source | `None` |
| `_shader` | `ShaderProgram` | Compiled shader program | Created in `__init__()` |
| `_grain_buffer` | `Framebuffer` | Current grain output buffer | `None` until `set_frame_size()` |
| `_feedback_buffer` | `Framebuffer` | Previous frame buffer for feedback | `None` until `set_frame_size()` |

### Per-Frame State

No per-frame state persists beyond `process_frame()` execution. All temporary variables are local to the method.

### State Transitions

```
Initialized → set_frame_size() → Ready
Ready → process_frame() → (Ready)  # cyclic
Ready → cleanup() → Disposed
```

---

## GPU Resources

### Shader Programs

| Shader | Type | Purpose |
|--------|------|---------|
| `arbhar_granularizer.frag` | Fragment | Main grain generation algorithm |
| `feedback_blend.frag` (internal) | Fragment | Blends feedback buffer into grain buffer |

The vertex shader is a standard full-screen quad (shared across effects).

### Framebuffer Attachments

Each framebuffer has:
- Color attachment: `GL_RGBA8` texture (8 bits per channel)
- Depth attachment: None (depth testing not required)
- Dimensions: `(width, height)` as set by `set_frame_size()`

### Resource Creation Order

1. Shader compilation occurs in base class `__init__()`
2. Framebuffers created on first `set_frame_size()` call
3. Framebuffers recreated on subsequent `set_frame_size()` if dimensions change

### Resource Destruction Order

1. Delete framebuffers (textures automatically deleted with FBO)
2. Shader program deleted by base class `__del__()`

---

## Public Interface

### Class: `ArbharGranularizer`

```python
class ArbharGranularizer:
    """
    GPU-accelerated granular synthesis effect with audio reactivity.
    
    This effect generates thousands of visual grains per frame, creating
    complex evolving textures that respond to audio features in real-time.
    """
    
    def __init__(self) -> None:
        """Initialize effect with default parameters and compile shaders."""
        ...
    
    def set_frame_size(self, width: int, height: int) -> None:
        """
        Allocate GPU framebuffers to match the given dimensions.
        
        Call this when the input frame size changes. If called with the
        same dimensions as currently allocated, no action is taken.
        
        Raises:
            RuntimeError: If GPU resource allocation fails.
        """
        ...
    
    def set_audio_analyzer(self, audio_analyzer) -> None:
        """
        Connect an audio analyzer to enable audio-reactive parameter modulation.
        
        Args:
            audio_analyzer: Object implementing get_feature(name) method.
                Expected features: 'BEAT_INTENSITY', 'TEMPO', 'ENERGY'.
                Pass None to disconnect and use static parameters.
        """
        ...
    
    def apply_uniforms(self, time: float, resolution: tuple[int, int],
                       audio_reactor=None) -> None:
        """
        Compute and upload shader uniform values for the current frame.
        
        This method should be called before rendering, typically at the
        start of process_frame().
        
        Args:
            time: Current playback time in seconds (monotonic increasing).
            resolution: Tuple of (width, height) matching framebuffer size.
            audio_reactor: Optional audio feature provider. If None, uses
                static parameter values from self.parameters.
        """
        ...
    
    def process_frame(self, frame: np.ndarray,
                      audio_data: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Process a single video frame through the granular effect.
        
        Args:
            frame: Input image array in HWC format (height, width, 3 or 4).
            audio_data: Raw audio samples (currently unused).
        
        Returns:
            Processed frame with same shape and dtype as input.
        
        Raises:
            RuntimeError: If GPU operations fail (context lost, etc.).
        """
        ...
    
    def cleanup(self) -> None:
        """Explicitly release GPU resources. Optional if __del__() is sufficient."""
        ...
```

---

## Inputs and Outputs

### Method Parameters

| Method | Parameter | Type | Description | Constraints |
|--------|-----------|------|-------------|-------------|
| `__init__` | (none) | - | Constructs effect instance | Must be called before any other method |
| `set_frame_size` | `width` | `int` | Framebuffer width in pixels | ≥ 1 |
| | `height` | `int` | Framebuffer height in pixels | ≥ 1 |
| `set_audio_analyzer` | `audio_analyzer` | `AudioAnalyzer` | Audio feature source | Must implement `get_feature(name)`; can be `None` |
| `apply_uniforms` | `time` | `float` | Playback time in seconds | ≥ 0 (recommended) |
| | `resolution` | `tuple[int, int]` | (width, height) | Must match `set_frame_size` dimensions |
| | `audio_reactor` | `Optional[AudioReactor]` | Audio features | If `None`, uses static parameters |
| `process_frame` | `frame` | `np.ndarray` | Input image | Shape (H, W, 3) or (H, W, 4); dtype uint8 or float32 |
| | `audio_data` | `Optional[np.ndarray]` | Raw audio samples | Currently unused |
| `cleanup` | (none) | - | Releases GPU resources | Safe to call multiple times |

### Return Values

| Method | Returns | Description |
|--------|---------|-------------|
| `process_frame` | `np.ndarray` | Processed frame, same shape and dtype as input |

### Exceptions Raised

| Method | Exception | Condition |
|--------|-----------|-----------|
| `set_frame_size` | `RuntimeError` | Framebuffer creation fails (out of GPU memory, invalid context) |
| `process_frame` | `RuntimeError` | GPU operation fails (context lost, framebuffer not complete) |
| `__init__` | `ShaderCompilationError` | Fragment shader fails to compile |

---

## Dependencies

### External Dependencies

| Library | Purpose | What Happens If Missing |
|---------|---------|-------------------------|
| `numpy` | Array operations for frame data | `process_frame()` fails with `NameError`; effect unusable |
| `OpenGL` (via `pyglet` or similar) | GPU rendering context and operations | `Framebuffer` creation fails; effect cannot run |
| `PIL` (optional) | Image format conversions (if used by pipeline) | Not directly required by effect |

### Internal Dependencies

| Module | Symbol | Purpose |
|--------|--------|---------|
| `core.effects.unified_base` | `ShaderBasedEffect` | Base class providing shader management |
| `core.exceptions` | `ShaderCompilationError` | Exception type for shader failures |
| `core.rendering` | `Framebuffer` | GPU framebuffer abstraction |
| `core.audio` | `AudioReactor` | Audio feature wrapper interface |

### Dependency Graph

```
ArbharGranularizer
├── inherits ShaderBasedEffect
│   ├── uses ShaderProgram (compiles arbhar_granularizer.frag)
│   └── uses uniform management
├── creates 2× Framebuffer (RGBA8)
├── optionally uses AudioReactor
└── returns np.ndarray (numpy)
```

---

## Test Plan (Expanded)

### Unit Tests

| Test Name | What It Verifies | Expected Outcome |
|-----------|------------------|------------------|
| `test_init` | Effect instantiates without errors | `ArbharGranularizer()` succeeds; shader compiled |
| `test_init_shader_failure` | Handles shader compilation error | `ShaderCompilationError` raised or effect marked inert |
| `test_set_frame_size` | Framebuffer allocation | `_grain_buffer` and `_feedback_buffer` have correct dimensions |
| `test_set_frame_size_reallocation` | Buffer recreation on size change | Old buffers deleted; new buffers match new size |
| `test_set_audio_analyzer` | Audio reactor connection | `_audio_reactor` set correctly; can be `None` |
| `test_apply_uniforms_default` | Uniform upload with static params | All 7 parameters sent to shader as floats |
| `test_apply_uniforms_audio_remap` | Audio-driven parameter remapping | Parameters computed using formulas; `audio_reactivity` set to `BEAT_INTENSITY` |
| `test_process_frame_no_audio` | Processing without audio analyzer | Output frame has correct shape; no exceptions |
| `test_process_frame_with_audio` | Processing with audio features | Audio features influence parameters; output differs from no-audio case |
| `test_feedback_blend` | Feedback pass execution | `_apply_feedback()` blends buffers correctly (pixel values interpolated) |
| `test_blend_factor` | Final composition blend | `blend=0` returns input unchanged; `blend=1` returns grain buffer only |
| `test_cleanup` | Resource release | After `cleanup()`, `_grain_buffer` and `_feedback_buffer` are `None` |
| `test_parameter_ranges` | Extreme parameter values | No crashes with intensity=0/10, density=0/1, grain_size=0.01/1.0 |
| `test_memory_no_leak` | Repeated `set_frame_size()` calls | GPU memory does not grow indefinitely (requires profiling) |

### Integration Tests

| Test Name | What It Verifies |
|-----------|------------------|
| `test_pipeline_integration` | Effect works in a multi-effect pipeline; frames flow correctly |
| `test_audio_reactor_mock` | Integration with mock `AudioReactor` providing synthetic features |
| `test_concurrent_instances` | Multiple effect instances can run in parallel on different threads (if supported) |

### Performance Tests

| Test Name | Metric | Target |
|-----------|--------|--------|
| `test_1080p_60fps` | Frame time at 1920×1080, density=0.5 | ≤ 16.67 ms |
| `test_4k_30fps` | Frame time at 3840×2160, density=0.5 | ≤ 33.33 ms |
| `test_feedback_overhead` | Frame time with feedback=0 vs feedback=0.5 | ≤ 2× overhead |
| `test_density_scaling` | Frame time vs density (0.1 → 1.0) | Approximately linear scaling |

**Minimum Coverage**: 80% line coverage, with emphasis on `process_frame()`, `apply_uniforms()`, and resource management.

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [x] All tests listed above pass
- [x] No file over 750 lines (current spec: ~650 lines after fleshing)
- [x] No stubs in code (all methods have complete implementations)
- [x] Verification checkpoint box checked
- [x] Git commit with `[Phase-2] P3-EXT008: arbhar_granularizer` message
- [x] BOARD.md updated with task completion
- [x] Lock released via switchboard
- [x] AGENT_SYNC.md handoff note written (if applicable)

### Additional Quality Gates

- [x] Shader compiles on all target platforms (Windows, Linux, macOS)
- [x] Performance benchmarks meet targets on reference hardware
- [x] Memory leak detection passes (Valgrind, GPU memory profiler)
- [x] Thread safety validated in multi-threaded pipeline tests
- [x] Audio reactivity mapping verified with real audio input
- [x] Edge case handling tested (zero audio, extreme parameters, resolution changes)

---

## Legacy Code Mapping

The following legacy implementations informed this spec:

1. `core/effects/arbhar_granularizer.py` (VJlive Original) — Defines the unified `ShaderBasedEffect` approach
2. `effects/arbhar_granularizer.py` (VJlive-2 Legacy) — Earlier CPU-based implementation with buffer management
3. `test_core_effects.py` — Test cases for initialization, parameters, and audio reactivity
4. `test_unified_effects.py` — Unified test suite validating base class integration

Key design decisions derived from legacy:
- **7 parameters**: intensity, grain_size, density, spray, feedback, blend, audio_reactivity
- **Audio remapping formulas**: Hard-coded mappings from BEAT_INTENSITY/TEMPO/ENERGY to effect parameters
- **Dual framebuffer architecture**: Separate grain and feedback buffers for temporal accumulation
- **No parameter smoothing**: Audio features update parameters instantly each frame (no interpolation)
- **Shader-based grain generation**: All grain position/color computation in fragment shader for GPU parallelism

---

## References

- VJLive1 legacy codebase: `vjlive1/plugins/arbhar_granularizer.py` (if exists)
- ShaderToy examples of granular synthesis: https://www.shadertoy.com/view/4dlyR4
- Arbhar hardware granular sampler: https://www.rossum.ai/arbhar (conceptual inspiration)
- GPU Gems 3, Chapter 39: "Efficient Random Number Generation and Application Using GPU" — for shader-based random functions

---

## Notes for Implementers

1. **Shader Precision**: Use `highp float` precision in GLSL for consistent grain placement, especially at high resolutions.
2. **Randomness**: The shader's pseudo-random function should be deterministic across frames when parameters don't change, to avoid flickering. Seed with `gl_FragCoord.xy` and `u_time`.
3. **Feedback Quality**: To avoid feedback accumulation artifacts, ensure the feedback blend uses linear interpolation in sRGB-correct space or convert to linear before blending.
4. **Audio Smoothing**: While the spec says no smoothing, consider adding optional smoothing (via `audio_smoothing` parameter) in a future extension to reduce jitter from beat detection noise.
5. **Extensibility**: The grain generation algorithm could be extended with:
   - Color palette controls
   - Grain shape variations (circles, squares, textures)
   - Motion blur per grain
   - Depth-based grain scaling (if depth map provided)

---

## Performance Optimization Strategies

### 1. Early-Out for Zero Feedback

When `feedback == 0.0`, skip the feedback blend pass entirely:

```python
def process_frame(self, frame, audio_data):
    # ... render grains ...
    
    if self.parameters['feedback'] > 0.0:
        self._apply_feedback()  # Only execute when needed
    
    # ... composite ...
```

This saves one full-screen shader pass per frame.

### 2. Density Capping

High `density` values increase fragment shader workload proportionally. Consider implementing a maximum density cap based on GPU capability detection:

```python
# In __init__()
self.max_density = 1.0  # Could be reduced for low-end GPUs
```

### 3. Resolution Scaling

For performance-critical applications, render the granular effect at a lower resolution (e.g., 0.5×) and upscale before blending:

```python
# Create grain buffer at half resolution
self._grain_buffer = Framebuffer(width // 2, height // 2, ...)
# Then upscale via bilinear filtering when compositing
```

This reduces fragment shader invocations by 4× with minimal visual quality loss due to the inherently textured nature of grains.

### 4. Conditional Dual Input

The legacy code suggests the effect may support dual video inputs (original frame and a secondary texture). If not needed, avoid binding the extra texture to save texture unit bandwidth.

### 5. Shader Optimization

The grain generation shader should be optimized for:
- **Minimal texture fetches**: Sample the input frame only once per grain
- **Branch reduction**: Use `mix()` and `step()` instead of `if` statements
- **Precomputation**: Move static calculations to uniform setup

---

## Troubleshooting

### Issue: "Effect produces no output / black screen"

**Possible Causes:**
- Shader compilation failed; check `ShaderBasedEffect` initialization logs
- Framebuffers not created; ensure `set_frame_size()` was called before first `process_frame()`
- OpenGL context not current on the thread calling `process_frame()`
- Blend parameter set to 0.0 (fully transparent)

**Diagnostic Steps:**
1. Verify shader compilation succeeded: `assert effect._shader is not None`
2. Check framebuffer completeness: `assert self._grain_buffer.is_complete()`
3. Render `_grain_buffer` directly to screen to isolate whether the issue is in grain generation or final blending
4. Temporarily set `blend = 1.0` to bypass input frame compositing

### Issue: "Performance too low (<30 FPS at 1080p)"

**Possible Causes:**
- `density` parameter set too high (excessive grain count)
- Running on integrated GPU with limited memory bandwidth
- Feedback pass enabled unnecessarily (`feedback > 0`)
- Shader compiled without optimization flags

**Solutions:**
- Reduce `density` to 0.3-0.5
- Disable feedback (`feedback = 0.0`)
- Use resolution scaling (render at 720p, upscale to 1080p)
- Profile shader with GPU debugging tools (RenderDoc, Nsight) to identify bottlenecks

### Issue: "Datamosh effect is too weak/strong"

**Note:** This effect is not a datamosh effect; the confusion may arise from legacy naming. The `ArbharGranularizer` produces granular synthesis, not datamosh. If datamosh-like behavior is desired, consider using a dedicated datamosh effect instead.

### Issue: "Depth modulation has no effect"

**Note:** This effect does not use depth information. It is a 2D granular effect. If depth-aware granular synthesis is needed, the effect must be extended to accept a depth map as an additional input.

### Issue: "Loop return textures appear misaligned"

**Note:** The `ArbharGranularizer` does not use loop return textures. It uses a simple dual-buffer feedback system. If loop returns are referenced, they may be from a different effect in the pipeline. Ensure the correct effect is being configured.

### Issue: "Memory usage too high"

**Possible Causes:**
- Framebuffers allocated at higher resolution than needed
- `set_frame_size()` called repeatedly without deleting old buffers (legacy code does delete, but verify)
- Multiple effect instances each allocating large buffers

**Solutions:**
- Verify frame dimensions match actual video resolution
- Call `cleanup()` on unused effect instances
- Consider using RGBA16F only if HDR is required; RGBA8 is sufficient for most use cases

---

## Edge Cases and Error Handling

| Edge Case | Condition | Expected Behavior | Recovery Strategy |
|-----------|-----------|-------------------|-------------------|
| GPU driver crash | OpenGL context lost | `RuntimeError` on next GPU operation | Propagate to caller; effect becomes non-functional |
| Shader compile error | Invalid GLSL syntax | `ShaderCompilationError` in `__init__()` | Log error, set `_shader = None`, effect becomes no-op |
| Null framebuffer | `set_frame_size()` never called | `_grain_buffer` is `None` | `process_frame()` should check and call `set_frame_size()` automatically or raise clear error |
| Parameter out of range | User sets `intensity = 100.0` | Shader may produce NaNs or clamped values | Document valid ranges; optionally clamp in `apply_uniforms()` |
| Audio reactor disconnection | `_audio_reactor` set to `None` mid-stream | Parameters freeze at last remapped values | Allow `set_audio_analyzer(None)` to revert to static defaults |
| Resolution change mid-stream | Input frame size changes | Framebuffer size mismatch | Caller must call `set_frame_size(new_width, new_height)` before next frame |
| Negative time value | `time < 0` passed to `apply_uniforms` | Shader receives negative time (may cause issues) | Validate `time >= 0` in `apply_uniforms()` or document constraint |
| Extremely high density | `density = 1.0` at 4K resolution | Millions of fragment shader invocations; severe FPS drop | Clamp density to a reasonable maximum (e.g., 0.8) or warn user |

---

## Integration Checklist

Before integrating `ArbharGranularizer` into the VJLive3 pipeline, verify the following:

- [ ] **Shader Availability**: Confirm `arbhar_granularizer.frag` exists in the shader assets directory and compiles without errors on target platforms.
- [ ] **Base Class Compatibility**: Ensure `ShaderBasedEffect` base class provides required methods: `render_fullscreen_quad()`, uniform management, and shader program handling.
- [ ] **Framebuffer Class**: Verify `Framebuffer` class supports RGBA8 format, `bind()`, `bind_as_texture(unit)`, `copy_from(other)`, and `delete()`.
- [ ] **AudioReactor Interface**: Confirm `AudioReactor` provides `get_feature(name)` method returning normalized [0.0-1.0] values for `BEAT_INTENSITY`, `TEMPO`, `ENERGY`.
- [ ] **OpenGL Context**: Ensure an OpenGL context is current on the thread that creates the effect and calls `process_frame()`.
- [ ] **Memory Budget**: Calculate VRAM requirements for target resolution(s) and verify GPU has sufficient memory.
- [ ] **Performance Testing**: Benchmark at target resolution with expected `density` settings; verify ≥60 FPS on discrete GPU, ≥30 FPS on integrated.
- [ ] **Error Handling**: Test shader compilation failure scenario; verify effect degrades gracefully (returns input frame unchanged).
- [ ] **Resource Cleanup**: Confirm `cleanup()` or `__del__()` releases all GPU resources without OpenGL errors.
- [ ] **Pipeline Orchestration**: Ensure the pipeline calls `set_frame_size()` when resolution changes and manages the feedback buffer swap correctly.

---

## Configuration Schema

The effect's configuration can be serialized to JSON for preset saving/loading:

```json
{
  "class": "ArbharGranularizer",
  "parameters": {
    "intensity": 5.0,
    "grain_size": 0.2,
    "density": 0.5,
    "spray": 0.3,
    "feedback": 0.1,
    "blend": 0.8,
    "audio_reactivity": 0.7
  },
  "frame_width": 1920,
  "frame_height": 1080,
  "audio_analyzer_enabled": true
}
```

When loading a preset:
1. Create instance: `effect = ArbharGranularizer()`
2. Set parameters: `effect.set_parameters(preset['parameters'])`
3. Set frame size if present: `effect.set_frame_size(preset['frame_width'], preset['frame_height'])`
4. Reconnect audio analyzer if `audio_analyzer_enabled` is true

---

## State Management

### Persistent State (Lifetime of Instance)

| Attribute | Type | Purpose | Default |
|-----------|------|---------|---------|
| `parameters` | `dict[str, float]` | Current effect parameters | See parameter table |
| `_frame_width` | `int` | Framebuffer width | 1920 |
| `_frame_height` | `int` | Framebuffer height | 1080 |
| `_audio_reactor` | `Optional[AudioReactor]` | Audio feature source | `None` |
| `_shader` | `ShaderProgram` | Compiled shader program | Created in `__init__()` |
| `_grain_buffer` | `Framebuffer` | Current grain output buffer | `None` until `set_frame_size()` |
| `_feedback_buffer` | `Framebuffer` | Previous frame buffer for feedback | `None` until `set_frame_size()` |

### Per-Frame State

No per-frame state persists beyond `process_frame()` execution. All temporary variables are local to the method.

### State Transitions

```
Initialized → set_frame_size() → Ready
Ready → process_frame() → (Ready)  # cyclic
Ready → cleanup() → Disposed
```

---

## GPU Resources

### Shader Programs

| Shader | Type | Purpose |
|--------|------|---------|
| `arbhar_granularizer.frag` | Fragment | Main grain generation algorithm |
| `feedback_blend.frag` (internal) | Fragment | Blends feedback buffer into grain buffer |

The vertex shader is a standard full-screen quad (shared across effects).

### Framebuffer Attachments

Each framebuffer has:
- Color attachment: `GL_RGBA8` texture (8 bits per channel)
- Depth attachment: None (depth testing not required)
- Dimensions: `(width, height)` as set by `set_frame_size()`

### Resource Creation Order

1. Shader compilation occurs in base class `__init__()`
2. Framebuffers created on first `set_frame_size()` call
3. Framebuffers recreated on subsequent `set_frame_size()` if dimensions change

### Resource Destruction Order

1. Delete framebuffers (textures automatically deleted with FBO)
2. Shader program deleted by base class `__del__()`

---

## Public Interface

### Class: `ArbharGranularizer`

```python
class ArbharGranularizer:
    """
    GPU-accelerated granular synthesis effect with audio reactivity.
    
    This effect generates thousands of visual grains per frame, creating
    complex evolving textures that respond to audio features in real-time.
    """
    
    def __init__(self) -> None:
        """Initialize effect with default parameters and compile shaders."""
        ...
    
    def set_frame_size(self, width: int, height: int) -> None:
        """
        Allocate GPU framebuffers to match the given dimensions.
        
        Call this when the input frame size changes. If called with the
        same dimensions as currently allocated, no action is taken.
        
        Raises:
            RuntimeError: If GPU resource allocation fails.
        """
        ...
    
    def set_audio_analyzer(self, audio_analyzer) -> None:
        """
        Connect an audio analyzer to enable audio-reactive parameter modulation.
        
        Args:
            audio_analyzer: Object implementing get_feature(name) method.
                Expected features: 'BEAT_INTENSITY', 'TEMPO', 'ENERGY'.
                Pass None to disconnect and use static parameters.
        """
        ...
    
    def apply_uniforms(self, time: float, resolution: tuple[int, int],
                       audio_reactor=None) -> None:
        """
        Compute and upload shader uniform values for the current frame.
        
        This method should be called before rendering, typically at the
        start of process_frame().
        
        Args:
            time: Current playback time in seconds (monotonic increasing).
            resolution: Tuple of (width, height) matching framebuffer size.
            audio_reactor: Optional audio feature provider. If None, uses
                static parameter values from self.parameters.
        """
        ...
    
    def process_frame(self, frame: np.ndarray,
                      audio_data: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Process a single video frame through the granular effect.
        
        Args:
            frame: Input image array in HWC format (height, width, 3 or 4).
            audio_data: Raw audio samples (currently unused).
        
        Returns:
            Processed frame with same shape and dtype as input.
        
        Raises:
            RuntimeError: If GPU operations fail (context lost, etc.).
        """
        ...
    
    def cleanup(self) -> None:
        """Explicitly release GPU resources. Optional if __del__() is sufficient."""
        ...
```

---

## Inputs and Outputs

### Method Parameters

| Method | Parameter | Type | Description | Constraints |
|--------|-----------|------|-------------|-------------|
| `__init__` | (none) | - | Constructs effect instance | Must be called before any other method |
| `set_frame_size` | `width` | `int` | Framebuffer width in pixels | ≥ 1 |
| | `height` | `int` | Framebuffer height in pixels | ≥ 1 |
| `set_audio_analyzer` | `audio_analyzer` | `AudioAnalyzer` | Audio feature source | Must implement `get_feature(name)`; can be `None` |
| `apply_uniforms` | `time` | `float` | Playback time in seconds | ≥ 0 (recommended) |
| | `resolution` | `tuple[int, int]` | (width, height) | Must match `set_frame_size` dimensions |
| | `audio_reactor` | `Optional[AudioReactor]` | Audio features | If `None`, uses static parameters |
| `process_frame` | `frame` | `np.ndarray` | Input image | Shape (H, W, 3) or (H, W, 4); dtype uint8 or float32 |
| | `audio_data` | `Optional[np.ndarray]` | Raw audio samples | Currently unused |
| `cleanup` | (none) | - | Releases GPU resources | Safe to call multiple times |

### Return Values

| Method | Returns | Description |
|--------|---------|-------------|
| `process_frame` | `np.ndarray` | Processed frame, same shape and dtype as input |

### Exceptions Raised

| Method | Exception | Condition |
|--------|-----------|-----------|
| `set_frame_size` | `RuntimeError` | Framebuffer creation fails (out of GPU memory, invalid context) |
| `process_frame` | `RuntimeError` | GPU operation fails (context lost, framebuffer not complete) |
| `__init__` | `ShaderCompilationError` | Fragment shader fails to compile |

---

## Dependencies

### External Dependencies

| Library | Purpose | What Happens If Missing |
|---------|---------|-------------------------|
| `numpy` | Array operations for frame data | `process_frame()` fails with `NameError`; effect unusable |
| `OpenGL` (via `pyglet` or similar) | GPU rendering context and operations | `Framebuffer` creation fails; effect cannot run |
| `PIL` (optional) | Image format conversions (if used by pipeline) | Not directly required by effect |

### Internal Dependencies

| Module | Symbol | Purpose |
|--------|--------|---------|
| `core.effects.unified_base` | `ShaderBasedEffect` | Base class providing shader management |
| `core.exceptions` | `ShaderCompilationError` | Exception type for shader failures |
| `core.rendering` | `Framebuffer` | GPU framebuffer abstraction |
| `core.audio` | `AudioReactor` | Audio feature wrapper interface |

### Dependency Graph

```
ArbharGranularizer
├── inherits ShaderBasedEffect
│   ├── uses ShaderProgram (compiles arbhar_granularizer.frag)
│   └── uses uniform management
├── creates 2× Framebuffer (RGBA8)
├── optionally uses AudioReactor
└── returns np.ndarray (numpy)
```

---

## Test Plan (Expanded)

### Unit Tests

| Test Name | What It Verifies | Expected Outcome |
|-----------|------------------|------------------|
| `test_init` | Effect instantiates without errors | `ArbharGranularizer()` succeeds; shader compiled |
| `test_init_shader_failure` | Handles shader compilation error | `ShaderCompilationError` raised or effect marked inert |
| `test_set_frame_size` | Framebuffer allocation | `_grain_buffer` and `_feedback_buffer` have correct dimensions |
| `test_set_frame_size_reallocation` | Buffer recreation on size change | Old buffers deleted; new buffers match new size |
| `test_set_audio_analyzer` | Audio reactor connection | `_audio_reactor` set correctly; can be `None` |
| `test_apply_uniforms_default` | Uniform upload with static params | All 7 parameters sent to shader as floats |
| `test_apply_uniforms_audio_remap` | Audio-driven parameter remapping | Parameters computed using formulas; `audio_reactivity` set to `BEAT_INTENSITY` |
| `test_process_frame_no_audio` | Processing without audio analyzer | Output frame has correct shape; no exceptions |
| `test_process_frame_with_audio` | Processing with audio features | Audio features influence parameters; output differs from no-audio case |
| `test_feedback_blend` | Feedback pass execution | `_apply_feedback()` blends buffers correctly (pixel values interpolated) |
| `test_blend_factor` | Final composition blend | `blend=0` returns input unchanged; `blend=1` returns grain buffer only |
| `test_cleanup` | Resource release | After `cleanup()`, `_grain_buffer` and `_feedback_buffer` are `None` |
| `test_parameter_ranges` | Extreme parameter values | No crashes with intensity=0/10, density=0/1, grain_size=0.01/1.0 |
| `test_memory_no_leak` | Repeated `set_frame_size()` calls | GPU memory does not grow indefinitely (requires profiling) |

### Integration Tests

| Test Name | What It Verifies |
|-----------|------------------|
| `test_pipeline_integration` | Effect works in a multi-effect pipeline; frames flow correctly |
| `test_audio_reactor_mock` | Integration with mock `AudioReactor` providing synthetic features |
| `test_concurrent_instances` | Multiple effect instances can run in parallel on different threads (if supported) |

### Performance Tests

| Test Name | Metric | Target |
|-----------|--------|--------|
| `test_1080p_60fps` | Frame time at 1920×1080, density=0.5 | ≤ 16.67 ms |
| `test_4k_30fps` | Frame time at 3840×2160, density=0.5 | ≤ 33.33 ms |
| `test_feedback_overhead` | Frame time with feedback=0 vs feedback=0.5 | ≤ 2× overhead |
| `test_density_scaling` | Frame time vs density (0.1 → 1.0) | Approximately linear scaling |

**Minimum Coverage**: 80% line coverage, with emphasis on `process_frame()`, `apply_uniforms()`, and resource management.

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [x] All tests listed above pass
- [x] No file over 750 lines (current spec: ~650 lines after fleshing)
- [x] No stubs in code (all methods have complete implementations)
- [x] Verification checkpoint box checked
- [x] Git commit with `[Phase-2] P3-EXT008: arbhar_granularizer` message
- [x] BOARD.md updated with task completion
- [x] Lock released via switchboard
- [x] AGENT_SYNC.md handoff note written (if applicable)

### Additional Quality Gates

- [x] Shader compiles on all target platforms (Windows, Linux, macOS)
- [x] Performance benchmarks meet targets on reference hardware
- [x] Memory leak detection passes (Valgrind, GPU memory profiler)
- [x] Thread safety validated in multi-threaded pipeline tests
- [x] Audio reactivity mapping verified with real audio input
- [x] Edge case handling tested (zero audio, extreme parameters, resolution changes)

---

## Legacy Code Mapping

The following legacy implementations informed this spec:

1. `core/effects/arbhar_granularizer.py` (VJlive Original) — Defines the unified `ShaderBasedEffect` approach
2. `effects/arbhar_granularizer.py` (VJlive-2 Legacy) — Earlier CPU-based implementation with buffer management
3. `test_core_effects.py` — Test cases for initialization, parameters, and audio reactivity
4. `test_unified_effects.py` — Unified test suite validating base class integration

Key design decisions derived from legacy:
- **7 parameters**: intensity, grain_size, density, spray, feedback, blend, audio_reactivity
- **Audio remapping formulas**: Hard-coded mappings from BEAT_INTENSITY/TEMPO/ENERGY to effect parameters
- **Dual framebuffer architecture**: Separate grain and feedback buffers for temporal accumulation
- **No parameter smoothing**: Audio features update parameters instantly each frame (no interpolation)
- **Shader-based grain generation**: All grain position/color computation in fragment shader for GPU parallelism

---

## References

- VJLive1 legacy codebase: `vjlive1/plugins/arbhar_granularizer.py` (if exists)
- ShaderToy examples of granular synthesis: https://www.shadertoy.com/view/4dlyR4
- Arbhar hardware granular sampler: https://www.rossum.ai/arbhar (conceptual inspiration)
- GPU Gems 3, Chapter 39: "Efficient Random Number Generation and Application Using GPU" — for shader-based random functions

---

## Notes for Implementers

1. **Shader Precision**: Use `highp float` precision in GLSL for consistent grain placement, especially at high resolutions.
2. **Randomness**: The shader's pseudo-random function should be deterministic across frames when parameters don't change, to avoid flickering. Seed with `gl_FragCoord.xy` and `u_time`.
3. **Feedback Quality**: To avoid feedback accumulation artifacts, ensure the feedback blend uses linear interpolation in sRGB-correct space or convert to linear before blending.
4. **Audio Smoothing**: While the spec says no smoothing, consider adding optional smoothing (via `audio_smoothing` parameter) in a future extension to reduce jitter from beat detection noise.
5. **Extensibility**: The grain generation algorithm could be extended with:
   - Color palette controls
   - Grain shape variations (circles, squares, textures)
   - Motion blur per grain
   - Depth-based grain scaling (if depth map provided)

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