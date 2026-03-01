# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT018_blend.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT018 — BlendAddEffect

**What This Module Does**

The `BlendAddEffect` module implements a feedback-based additive blending system that creates motion trails, persistence effects, and visual echoes by combining the current frame with a decayed version of the previous frame. This effect is fundamental for creating organic, flowing visualizations that respond to audio or time-based inputs, commonly used in live VJ performances to generate trailing effects behind moving objects.

The effect operates by maintaining a feedback buffer that stores the previous frame's output. Each new frame is blended with this buffer using a configurable mix ratio, decay factor, and amount parameter. The feedback buffer is then updated with the blended result, creating a recursive system where visual elements persist and gradually fade out.

The implementation uses a single-pass GPU shader that samples from two textures:
- `tex0`: The current input frame
- `texPrev`: The previous frame's output (feedback buffer)

The shader applies geometric transformations to the feedback texture (zoom, rotation, delay) before blending, allowing for complex motion trails and swirling effects.

**What This Module Does NOT Do**

- Does not implement any of the 35 other blend modes (additive blending is the only operation)
- Does not handle audio-reactive behavior directly (though it can be driven by audio-reactive parameters)
- Does not perform color space conversion or manipulation beyond RGB blending
- Does not implement temporal anti-aliasing or motion blur
- Does not support multi-layer blending (only two inputs: current and feedback)
- Does not provide automatic scene detection or content-aware blending
- Does not handle video file I/O or persistence

---

## Detailed Behavior and Parameter Interactions

### Parameter Mapping Philosophy

All user-facing parameters use a normalized 0-1 scale for consistency, unlike the legacy code's 0-10 scale. This simplifies implementation and reduces the risk of parameter overflow.

```python
# Parameter mapping in implementation:
# All parameters are clamped to [0.0, 1.0] range
# No internal remapping required
```

### Core Blending Algorithm

The effect implements a recursive feedback loop with the following mathematical structure:

```
output = mix(current, feedback, mix)
feedback = mix(current, decayed_prev, amount)
decayed_prev = prev * (1.0 - decay)
```

This creates a system where:
- `mix` controls the overall blend between original and feedback
- `amount` controls how much of the decayed feedback is blended into the new feedback buffer
- `decay` controls how quickly the feedback fades out (0.0 = no decay, 1.0 = instant fade)

### Feedback Transformations

The feedback texture undergoes geometric transformations before blending:

**Zoom (`zoomAmt`, 0-1 → -1.0 to 1.0)**
Applies a zoom effect to the feedback texture coordinates. Values > 0 zoom in (magnifying the feedback), values < 0 zoom out (reducing the feedback). The transformation is:

```glsl
vec2 centered = uv - 0.5;
vec2 feedback_uv = centered * (1.0 + zoomAmt);
feedback_uv += 0.5;
```

This creates a "lens" effect where the feedback appears to be viewed through a magnifying glass centered on the screen.

**Rotation (`rotate_angle`, `rotate_speed`, 0-1 → 0 to 2π)**
Applies a rotational transformation to the feedback texture coordinates. `rotate_angle` sets the initial rotation, `rotate_speed` controls how fast the rotation changes over time:

```glsl
float angle = rotate_angle + time * rotate_speed;
float s = sin(angle);
float c = cos(angle);
feedback_uv = vec2(
    feedback_uv.x * c - feedback_uv.y * s,
    feedback_uv.x * s + feedback_uv.y * c
);
```

This creates swirling, vortex-like motion trails that rotate around the center of the screen.

**Delay (`delay`, 0-1 → 0 to 1)**
Applies a time-delayed offset to the feedback texture coordinates using a sine/cosine function:

```glsl
feedback_uv += vec2(sin(time * delay * 0.1), cos(time * delay * 0.1)) * 0.01;
```

This creates a subtle "ghosting" effect where the feedback appears slightly offset in time, creating a trailing effect that lags behind the current image.

### Decay Behavior

The decay parameter controls the exponential fading of the feedback buffer:

```glsl
previous.rgb *= (1.0 - decay);
```

- `decay = 0.0`: Feedback persists indefinitely (no decay)
- `decay = 0.1`: Feedback fades slowly (10% per frame)
- `decay = 0.5`: Feedback fades moderately (50% per frame)
- `decay = 0.9`: Feedback fades rapidly (90% per frame)
- `decay = 1.0`: Feedback disappears immediately (no persistence)

The decay is applied before blending, ensuring that older feedback contributes less to the final image.

### Mix and Amount Parameters

The `mix` parameter controls the final blend between the original input and the feedback result:

```glsl
fragColor = mix(current, feedback, mix);
```

- `mix = 0.0`: Only the original input is visible
- `mix = 0.5`: Equal blend of original and feedback
- `mix = 1.0`: Only the feedback result is visible

The `amount` parameter controls how much of the decayed feedback is blended into the new feedback buffer:

```glsl
vec4 feedback = mix(current, previous, amount);
```

- `amount = 0.0`: Feedback buffer is unchanged (no new input)
- `amount = 0.5`: Half of the current frame is blended into feedback
- `amount = 1.0`: Feedback buffer is completely replaced by current frame

This creates a complex interaction where `amount` controls the "memory" of the system, while `mix` controls the visibility of that memory.

---

## Integration

### VJLive3 Pipeline Integration

The `BlendAddEffect` integrates as a frame processor in the effects pipeline:

```
[Video Source] → [BlendAddEffect] → [Output]
```

**Position**: This effect is typically placed in the middle or end of the effects chain to blend multiple layers of visual content. It can be chained with other effects to create complex visualizations.

**Frame Processing**:

1. The pipeline calls `effect.apply(input_frame)` for each frame.
2. The effect uploads the frame to a GPU texture (if not already a texture).
3. A full-screen quad is rendered with the blend shader.
4. The shader reads from `tex0` (current frame) and `texPrev` (previous frame feedback buffer).
5. The shader applies geometric transformations to the feedback texture.
6. The shader applies decay and blending operations.
7. The output is written to a framebuffer.
8. The output framebuffer is stored as `texPrev` for the next frame.
9. The output frame is returned as a numpy array (read back from GPU if necessary).

**Parameter Configuration**: The effect uses a dictionary of parameters that are updated via `set_parameter(name, value)`. All parameters are clamped to [0.0, 1.0] range. The effect maintains internal state for the feedback buffer texture.

**Shader Management**: The effect should compile/link the shader at initialization and reuse it for all frames. Uniform locations should be cached for performance. The shader source should be embedded as a string constant or loaded from a resource file.

**Time Handling**: The shader uses a `time` uniform for time-based effects (rotation, delay). The effect must increment this each frame (or pass the frame's timestamp) to ensure smooth animation.

**Resolution Handling**: The shader requires `resolution` uniform (vec2) to compute UV coordinates. This should be updated if the frame size changes.

**GPU Fallback**: If `pyshader` or GPU hardware is unavailable, the effect should fall back to a CPU-based approximation. This could be a simplified implementation using numpy/scipy that applies only the core blending and decay operations with reduced fidelity. The fallback should be clearly documented as lower quality.

### Texture Management

The effect requires two textures:
- `tex0`: Input texture (current frame)
- `texPrev`: Feedback texture (previous frame output)

These textures must be:
- Created with the same dimensions as the input frame
- Using a format that supports floating-point values (e.g., GL_RGBA32F)
- Reused across frames to avoid memory allocation overhead
- Properly bound to texture units before rendering

The feedback texture (`texPrev`) is updated after each frame by copying the output framebuffer to it.

---

## Performance

### Computational Cost

The effect is **GPU-bound** and highly efficient when hardware acceleration is available. The fragment shader performs a few dozen arithmetic operations per pixel plus several texture reads. On modern integrated or discrete GPUs:

- **1080p (1920×1080)**: ~0.5-1.5 ms per frame on Intel Iris Xe, NVIDIA GTX 1060, or AMD RX 580
- **4K (3840×2160)**: ~2-5 ms per frame on the same hardware
- **720p (1280×720)**: <0.5 ms per frame

The effect is real-time capable at 60fps on most GPUs released since 2015. Memory bandwidth is the main bottleneck due to the feedback texture reads.

### Memory Usage

- **GPU memory**: Two input textures (frame) + one output framebuffer. For 1080p RGBA32F, that's ~32 MB + 32 MB = 64 MB.
- **CPU memory**: The numpy arrays for input/output. Same size as GPU textures if using staging buffers.
- **Shader program**: Negligible (<100 KB for compiled shader binary).

### Optimization Strategies

1. **Texture format**: Use GPU-native texture formats (e.g., GL_RGBA32F) to avoid conversion overhead.
2. **Framebuffer reuse**: Reuse the output framebuffer if the effect is applied repeatedly without size changes.
3. **Uniform batching**: Update only changed uniforms instead of all every frame.
4. **Resolution scaling**: For performance, render at lower resolution and upscale (though this reduces effect quality).
5. **Parameter culling**: Skip shader execution if all parameters are zero (no effect applied). This is important when the effect is in the chain but disabled.

### Platform-Specific Considerations

- **Desktop**: GPU acceleration via OpenGL 3.3+ or Vulkan is expected. `pyshader` provides cross-platform shader compilation.
- **Embedded (Raspberry Pi, Orange Pi)**: May have limited GPU performance. The fallback CPU mode should be tested for viability. Consider reducing resolution or effect complexity on these platforms.
- **Headless/CPU-only**: The fallback implementation must work without GPU. It should use numpy operations (convolution for blur, random noise generation, etc.) but may omit some effects (e.g., rotation) for speed.

### Performance Testing Recommendations

- Benchmark at various resolutions (480p, 720p, 1080p, 4K) with all parameters at maximum to find worst-case
- Measure frame time with individual effect categories enabled to identify bottlenecks
- Test memory usage with long-running sessions to ensure no leaks
- Verify that parameter changes don't cause shader recompilation (should be uniform-only)
- Check that the fallback CPU mode completes within the frame budget (e.g., <16ms for 60fps at 720p)

---

## Test Plan (Expanded)

The existing test plan is minimal. Expand with:

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect instantiates even if GPU/shader unavailable; falls back to CPU mode without crashing |
| `test_basic_operation` | apply() returns valid output with default parameters (all zeros) |
| `test_parameter_clamping` | Setting parameter outside 0-1 range clamps to bounds (0.0 or 1.0) |
| `test_feedback_decay` | When decay > 0, feedback fades out over time (not persistent) |
| `test_feedback_persistence` | When decay = 0, feedback persists indefinitely (accumulates) |
| `test_mix_parameter` | mix=0 returns original frame; mix=1 returns full feedback; intermediate values blend correctly |
| `test_amount_parameter` | amount=0 keeps feedback unchanged; amount=1 replaces feedback with current frame |
| `test_zoom_effect` | When zoomAmt > 0, feedback appears magnified; when < 0, feedback appears reduced |
| `test_rotation_effect` | When rotate_speed > 0, feedback rotates continuously over time |
| `test_delay_effect` | When delay > 0, feedback appears slightly offset in time (ghosting effect) |
| `test_resolution_change` | Changing input frame size updates resolution uniform and effect adapts without artifacts |
| `test_error_invalid_frame` | Invalid frame (None, wrong shape, wrong dtype) raises appropriate exception |
| `test_cleanup` | Effect releases GPU resources (textures, shaders) on destruction; no memory leaks |
| `test_fallback_mode` | In CPU fallback, basic blending and decay still produce recognizable output |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

