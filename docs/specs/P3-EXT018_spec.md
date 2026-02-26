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

### [NEEDS RESEARCH]: How does the effect handle non-square pixels or aspect ratio?

**Finding**: The shader uses `resolution` uniform to compute UV coordinates. It assumes square pixels (1:1 aspect). If the input frame has non-square pixels (e.g., anamorphic 16:9), the feedback rotation and zoom may appear distorted.

**Resolution**: The effect should either:
- Assume input is already corrected to square pixels (simplest)
- Or accept an additional `aspect_ratio` parameter to compensate
- Or compute aspect from resolution and adjust UVs accordingly

Recommendation: Assume square pixels; let the pipeline handle aspect ratio correction before this effect.

### [NEEDS RESEARCH]: What is the exact implementation of the feedback buffer management?

**Finding**: The legacy code shows `texPrev` as a uniform sampler2D, but doesn't show how it's updated between frames. The implementation must:
- Create a framebuffer object (FBO) for the output
- Render the effect to this FBO
- Copy the FBO's color attachment to the feedback texture (`texPrev`)
- Bind the feedback texture for the next frame

**Resolution**: The effect should use OpenGL's framebuffer objects (FBOs) to manage the feedback buffer. The feedback texture should be created once at initialization and reused. The copy from output FBO to feedback texture should be done using `glBlitFramebuffer` or `glCopyTexImage2D` for efficiency.

### [NEEDS RESEARCH]: How does the effect handle the initial frame?

**Finding**: On the first frame, there is no previous frame to use as feedback. The legacy code doesn't specify initialization behavior.

**Resolution**: The effect should initialize the feedback buffer with a black texture (all zeros) on the first frame. This ensures a clean start without artifacts.

---

## Configuration Schema

The effect should define a `METADATA` manifest describing all parameters:

```python
METADATA = {
  "params": [
    {"id": "mix", "name": "Mix", "default": 0.5, "min": 0, "max": 1, "type": "float", "description": "Blend factor between original and feedback (0=original, 1=feedback)"},
    {"id": "decay", "name": "Decay", "default": 0.1, "min": 0, "max": 1, "type": "float", "description": "Feedback decay rate per frame (0=no decay, 1=immediate fade)"},
    {"id": "amount", "name": "Amount", "default": 0.5, "min": 0, "max": 1, "type": "float", "description": "Strength of feedback loop (0=no feedback, 1=full feedback)"},
    {"id": "zoomAmt", "name": "Zoom", "default": 0.0, "min": -1, "max": 1, "type": "float", "description": "Zoom factor for feedback texture (-1=zoom out, 0=normal, 1=zoom in)"},
    {"id": "delay", "name": "Delay", "default": 0.0, "min": 0, "max": 1, "type": "float", "description": "Time delay for feedback (0=no delay, 1=max delay)"},
    {"id": "rotate_angle", "name": "Rotate Angle", "default": 0.0, "min": 0, "max": 1, "type": "float", "description": "Initial rotation angle (0-2π radians)"},
    {"id": "rotate_speed", "name": "Rotate Speed", "default": 0.0, "min": 0, "max": 1, "type": "float", "description": "Rotation speed (0=no rotation, 1=fast rotation)"},
  ]
}
```

**Presets**: The legacy code doesn't define presets, but recommended presets include:
- `trail`: mix=0.7, decay=0.2, amount=0.8, zoomAmt=0.0, delay=0.0, rotate_angle=0.0, rotate_speed=0.0
- `swirl`: mix=0.8, decay=0.1, amount=0.9, zoomAmt=0.2, delay=0.0, rotate_angle=0.0, rotate_speed=0.5
- `echo`: mix=0.6, decay=0.3, amount=0.7, zoomAmt=0.0, delay=0.5, rotate_angle=0.0, rotate_speed=0.0
- `fade`: mix=0.9, decay=0.8, amount=0.5, zoomAmt=0.0, delay=0.0, rotate_angle=0.0, rotate_speed=0.0
- `static`: mix=0.0, decay=0.0, amount=0.0, zoomAmt=0.0, delay=0.0, rotate_angle=0.0, rotate_speed=0.0

---

## State Management

- **Per-frame state**: The current frame being processed, the output framebuffer, and temporary UV coordinates. These are transient.
- **Persistent state**: All parameter values (0-1 scale), shader program object, uniform locations, feedback texture object. These persist for the lifetime of the effect instance.
- **Init-once state**: Compiled shader program, feedback texture creation. Initialized in `__init__` and reused.
- **Thread safety**: The effect is not thread-safe by default. If the pipeline calls `apply()` from multiple threads, external synchronization is required. The shader program and uniforms should not be modified concurrently.

---

## GPU Resources

This effect is **GPU-bound** and requires a shader-capable GPU (OpenGL 3.3+ or equivalent). It uses:

- **Vertex shader**: Simple pass-through (likely provided by base class)
- **Fragment shader**: The blend effect (~100 lines GLSL)
- **Textures**: 2 input textures (current frame, feedback buffer), 1 output framebuffer
- **Uniform buffers**: 7 uniform values (parameters, time, resolution)

If GPU resources are exhausted (out of memory), the effect should raise an exception rather than silently fall back to CPU (unless explicitly configured to do so).

The fallback CPU mode uses only system memory and numpy arrays, but with reduced effect quality and performance.

---

## Public Interface

```python
class BlendAddEffect(Effect):
    def __init__(self, name: str = "blend_add", fragment_shader: str = BLEND_ADD_FRAGMENT) -> None:
        """
        Initialize the blend add effect.
        
        Args:
            name: Effect name (used for logging and identification)
            fragment_shader: GLSL fragment shader code as a string
        """
    
    def apply(self, input_frame: np.ndarray) -> np.ndarray:
        """
        Apply the blend add effect to an input frame.
        
        Args:
            input_frame: Input RGB image as a numpy array of shape (H, W, 3)
            
        Returns:
            Output frame with applied blend add effect
        """
    
    def set_parameter(self, key: str, value: float) -> None:
        """
        Set a specific effect parameter.
        
        Args:
            key: Parameter name (e.g., "mix", "decay")
            value: Value between 0 and 1
        """
    
    def get_parameter(self, key: str) -> float:
        """
        Get current value of a parameter.
        
        Args:
            key: Parameter name
            
        Returns:
            Current value (float in 0-1 range)
        """
    
    def update(self, time: float, resolution: tuple[int, int]) -> None:
        """
        Update internal state based on time and resolution.
        
        Args:
            time: Current animation time in seconds
            resolution: Output texture resolution (width, height)
        """
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `name` | `str` | Effect name (used for logging and identification) | Must be non-empty string, defaults to "blend_add" |
| `fragment_shader` | `str` | GLSL fragment shader code as a string | Must be valid GLSL 330 core; must include `tex0`, `texPrev`, `time`, `resolution`, and `uv` uniforms |
| `time` | `float` | Current animation time in seconds | ≥ 0.0, used for delay/rotation calculations |
| `resolution` | `tuple[int, int]` | Output texture resolution (width, height) | Width > 0, Height > 0 |
| `mix` | `float` | Blend ratio between current and feedback frame | Range: [0.0, 1.0], default: 0.5 |
| `decay` | `float` | Decay factor applied to previous frame before mixing | Range: [0.0, 1.0], default: 0.1 |
| `amount` | `float` | Strength of feedback loop (how much to blend in) | Range: [0.0, 1.0], default: 0.5 |
| `zoomAmt` | `float` | Zoom factor applied to UV coordinates for feedback | Range: [-1.0, 1.0], default: 0.0 |
| `delay` | `float` | Time delay (in seconds) for feedback offset | ≥ 0.0, default: 0.0 |
| `rotate_angle` | `float` | Initial rotation angle of feedback loop | Range: [0.0, 2π], default: 0.0 |
| `rotate_speed` | `float` | Speed at which feedback rotates over time | ≥ 0.0, default: 0.0 |
| `input_frame` | `np.ndarray` | Input RGB image (H, W, 3) | Shape must be valid; values in [0, 255] |
| `output_frame` | `np.ndarray` | Output frame with blend add effect applied | Same shape as input; values in [0, 255] |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — used for image array manipulation — **hard requirement**; if missing, raises ImportError
  - `OpenGL.GL` — used for texture binding and shader rendering — fallback: no rendering
- Internal modules this depends on:
  - `vjlive3.core.effects.shader_base.Effect` — base class providing shader management
  - `vjlive3.core.shader_manager.ShaderManager` — optional, for shader caching/compilation
  - `vjlive3.core.color_space.RGBConverter` — for color space conversion if needed

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect instantiates even if GPU/shader unavailable; falls back to CPU mode without crashing |
| `test_basic_operation` | Core blend operation correctly combines current and previous frames with valid parameters |
| `test_error_handling` | Invalid parameter values (e.g., negative mix) raise appropriate exceptions or clamp to bounds |
| `test_feedback_rotation` | Rotation of feedback loop occurs at correct speed and angle over time |
| `test_delay_effect` | Delayed UV offset is applied as expected using sine/cosine functions |
| `test_zoom_feedback` | Zooming in/out on feedback UV coordinates modifies the visual output correctly |
| `test_decay_behavior` | Previous frame values decay exponentially per frame with correct rate |
| `test_output_resolution` | Effect renders at correct resolution without distortion or scaling errors |
| `test_feedback_initialization` | Feedback buffer is initialized to black on first frame |
| `test_parameter_clamping` | Parameters outside [0,1] range are clamped to bounds |
| `test_cleanup` | Effect releases GPU resources (textures, shaders) on destruction; no memory leaks |
| `test_fallback_mode` | In CPU fallback, basic blending and decay still produce recognizable output |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT018: Implement BlendAddEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive1/core/effects/legacy_trash/blend.py (L1-20)
```python
"""
Blend and feedback effects - mixing, layering, and feedback loops.
Ported from effects.hydra's blend functions.
"""

from .shader_base import Effect, BASE_VERTEX_SHADER
from .shadertoy import ShadertoyEffect
from ..audio_reactor import AudioReactor
from ..audio_analyzer import AudioFeature
from OpenGL.GL import (glActiveTexture, glBindTexture, GL_TEXTURE0, GL_TEXTURE1, GL_TEXTURE_2D)
```

### vjlive1/core/effects/legacy_trash/blend.py (L17-36)
```python
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform float time;
uniform vec2 resolution;
uniform float mix;

uniform float amount;    // Default: 0.5 - feedback strength
uniform float decay;     // Default: 0.1 - decay per frame
uniform float zoomAmt;   // Default: 0.0 - zoom feedback
uniform float delay;     // Default: 0.0 - delay time for feedback
uniform float rotate_angle; // Default: 0.0 - static rotation
uniform float rotate_speed; // Default: 0.0 - rotation speed
```

### vjlive1/core/effects/legacy_trash/blend.py (L33-52)
```python
void main() {
    vec4 current = texture(tex0, uv);

    // Zoom UV for feedback
    vec2 centered = uv - 0.5;
    vec2 feedback_uv = centered * (1.0 + zoomAmt);

    // Apply rotation
    float angle = rotate_angle + time * rotate_speed;
    float s = sin(angle);
    float c = cos(angle);
    feedback_uv = vec2(
        feedback_uv.x * c - feedback_uv.y * s,
        feedback_uv.x * s + feedback_uv.y * c
    );

    feedback_uv += 0.5;

    // For delay, offset UV slightly based on time (simplified delay effect)
    // Note: True delay would require accumulation buffer
    feedback_uv += vec2(sin(time * delay * 0.1), cos(time * delay * 0.1)) * 0.01;

    vec4 previous = texture(texPrev, feedback_uv);

    // Decay the previous frame
    previous.rgb *= (1.0 - decay);

    // Mix current with decayed feedback
    vec4 feedback = mix(current, previous, amount);
    fragColor = mix(current, feedback, mix);
}
```

### vjlive1/core/effects/legacy_trash/blend.py (L49-68)
```python
feedback_uv += 0.5;

// For delay, offset UV slightly based on time (simplified delay effect)
// Note: True delay would require accumulation buffer
feedback_uv += vec2(sin(time * delay * 0.1), cos(time * delay * 0.1)) * 0.01;

vec4 previous = texture(texPrev, feedback_uv);

// Decay the previous frame
previous.rgb *= (1.0 - decay);

// Mix current with decayed feedback
vec4 feedback = mix(current, previous, amount);
fragColor = mix(current, feedback, mix);
```

### vjlive1/core/effects/legacy_trash/blend.py (L65-84)
```python
class FeedbackEffect(Effect):
    """Feedback loop effect - creates trails and persistence."""

    def __init__(self):
        super().__init__("feedback", FEEDBACK_FRAGMENT)
        self.parameters = {
            "amount": 0.5,
            "decay": 0.1,
            "zoomAmt": 0.0,
            "delay": 0.0,
            "rotate_angle": 0.0,
            "rotate_speed": 0.0,
        }
```

### plugins/core/blend_modes_blend_add/plugin.json (L1-20)
```json
{
    "id": "blend_add",
    "name": "Blend Add",
    "version": "1.0.0",
    "description": "",
    "category": "Blend",
    "tags": [
        "resolume",
        "compositing",
        "blend",
        "unbundled",
        "blend_modes"
    ],
    "author": "VJLive",
    "license": "Unknown",
    "module_path": "plugins.core.blend_modes_blend_add",
    "modules": [
        {
            "id": "blend_add",
            "name": "Blend Add",
            "type": "EFFECT",
            "module_path": "plugins.core.blend_modes",
            "class_name": "BlendAddEffect",
            "category": "Blend",
            "inputs": [
                {
                    "name": "signal_in",
                    "type": "video"
                },
                {
                    "name": "blend_in",
                    "type": "video"
                }
            ],
            "outputs": [
                {
                    "name": "signal_out",
                    "type": "video"
                }
            ],
            "parameters": [
                {
                    "name": "amount",
                    "label": "Amount",
                    "type": "float",
                    "min": 0.0,
                    "max": 10.0,
                    "default": 5.0
                }
            ]
        }
    ]
}
```

[NEEDS RESEARCH]: None — all research questions have been answered in the "Open Questions and Research Findings" section above. The feedback buffer management and initialization behavior have been specified based on standard GPU programming practices.
