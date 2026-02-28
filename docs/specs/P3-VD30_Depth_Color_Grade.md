# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD30_Depth_Color_Grade.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD30 — DepthColorGradeEffect

## Description

The Depth Color Grade effect provides professional-grade, spatially-aware color grading that independently alters the Hue, Saturation, Exposure, and Temperature of Near, Mid, and Far depth zones. This allows for sophisticated depth-based color manipulation where foreground and background elements can be color-graded differently, enabling effects like "warm foreground, cool background" or "saturated subject, desaturated background" without affecting other depth regions.

The effect uses a 3-zone depth model where the depth range is divided into Near, Mid, and Far zones based on configurable boundaries. Each zone receives independent color grading parameters, and smooth blending between zones ensures seamless transitions. The effect integrates with the VJLive3 depth pipeline, consuming a depth map from an `AstraDepthSource` and applying real-time color transformations in a fragment shader.

## What This Module Does

- Consumes a depth map and applies independent color grading to three depth zones: Near, Mid, and Far
- Provides per-zone controls for Hue, Saturation, Temperature, and Exposure
- Implements smooth blending between zones using configurable blend widths
- Supports global contrast and film curve adjustments applied after zone grading
- Integrates with `DepthEffect` base class for consistent depth source management
- Uses GPU-accelerated fragment shaders for real-time performance at 60 FPS
- Allows audio reactivity to modulate color grading parameters based on audio features
- Manages depth texture lifecycle: updates from depth source each frame, handles texture reallocation on resolution changes

## What This Module Does NOT Do

- Does NOT perform basic color grading (use a standard color grade effect for that)
- Does NOT generate depth maps itself (requires external `AstraDepthSource`)
- Does NOT support more than three depth zones (fixed 3-zone model)
- Does NOT implement advanced color science (no color space conversions, LUTs, etc.)
- Does NOT handle audio analysis (relies on `AudioReactor` wrapper for feature extraction)
- Does NOT provide CPU fallback (requires GPU for shader-based color transformations)
- Does NOT manage node graph connections (caller must route depth source to effect)
- Does NOT store persistent state across sessions (all parameters are in-memory)

---

## Detailed Behavior

### 3-Zone Depth Model

The effect divides the depth range into three zones:

- **Near Zone**: Depth values from 0.0 to `zoneNear`
- **Mid Zone**: Depth values from `zoneNear` to `zoneFar`
- **Far Zone**: Depth values from `zoneFar` to 1.0

Each zone has its own color grading parameters:

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `zoneNear` | float | 3.0 | 0.0 - 10.0 | Depth boundary between Near and Mid zones |
| `zoneFar` | float | 7.0 | 0.0 - 10.0 | Depth boundary between Mid and Far zones |
| `zoneBlend` | float | 4.0 | 0.0 - 10.0 | Width of blending region between zones |

### Per-Zone Color Grading

Each zone applies independent color transformations:

**Near Zone Parameters:**
- `nearHue`: float, default 0.0 — Hue shift in degrees (-180 to 180)
- `nearSaturation`: float, default 5.0 — Saturation multiplier (0.0 = grayscale, 2.0 = double saturation)
- `nearTemperature`: float, default 6.0 — Color temperature shift (positive = warmer, negative = cooler)
- `nearExposure`: float, default 5.5 — Exposure compensation (0.0 = no change, 1.0 = +1 stop)

**Mid Zone Parameters:**
- `midHue`: float, default 0.0
- `midSaturation`: float, default 5.0
- `midTemperature`: float, default 6.0
- `midExposure`: float, default 5.5

**Far Zone Parameters:**
- `farHue`: float, default 0.0
- `farSaturation`: float, default 5.0
- `farTemperature`: float, default 6.0
- `farExposure`: float, default 5.5

### Color Transformation Pipeline

For each pixel, the effect executes:

1. **Depth Lookup**: Sample depth value from depth texture
2. **Zone Determination**: Determine which zone the depth belongs to (Near/Mid/Far)
3. **Zone Blending**: Compute blend weights for smooth transitions between zones
4. **Per-Zone Grading**: Apply hue, saturation, temperature, and exposure transforms to each zone
5. **Zone Mixing**: Combine the three zone outputs using blend weights
6. **Global Adjustments**: Apply global contrast and film curve
7. **Output**: Mix with original frame using `u_mix` parameter

The fragment shader implements this pipeline using vector operations for efficiency.

### Color Transformation Formulas

**Hue Shift**:
```glsl
vec3 hue_shift(vec3 color, float degrees) {
    float radians = degrees * 3.14159 / 180.0;
    mat3 hue_matrix = mat3(
        cos(radians), -sin(radians), 0,
        sin(radians), cos(radians), 0,
        0, 0, 1
    );
    return hue_matrix * color;
}
```

**Saturation**:
```glsl
vec3 adjust_saturation(vec3 color, float factor) {
    float gray = dot(color, vec3(0.299, 0.587, 0.114));
    return mix(vec3(gray), color, factor);
}
```

**Temperature**:
```glsl
vec3 adjust_temperature(vec3 color, float shift) {
    vec3 warm = vec3(1.0, 0.95, 0.9);
    vec3 cool = vec3(0.9, 0.95, 1.0);
    return mix(cool, warm, shift * 0.5 + 0.5);
}
```

**Exposure**:
```glsl
vec3 adjust_exposure(vec3 color, float stops) {
    return color * pow(2.0, stops);
}
```

### Audio Reactivity

When an `AudioReactor` is connected, parameters can be modulated by audio features:
- `nearSaturation` may respond to `BEAT_INTENSITY` (beats increase foreground saturation)
- `farExposure` may respond to `ENERGY` (high energy reduces background exposure)
- `zoneNear` may respond to `TEMPO` (faster tempo pushes near zone boundaries)

The exact mappings are configurable via `audio_reactor.assign_audio_feature()` calls during initialization.

---

## Public Interface

```python
class DepthColorGradeEffect:
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_audio_analyzer(self, audio_analyzer) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame` | `np.ndarray` | Input video frame (HWC, 3 or 4 channels) | dtype: uint8 or float32 |
| `depth_source` | `AstraDepthSource` | Depth map provider | Must implement `get_depth_frame()` |
| `audio_analyzer` | `AudioAnalyzer` | Optional audio feature source | Provides BEAT_INTENSITY, TEMPO, ENERGY |

**Output**: `np.ndarray` — Processed frame with depth-based color grading applied, same shape/format as input

---

## Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `zoneNear` | float | 3.0 | 0.0 - 10.0 | Depth boundary between Near and Mid zones |
| `zoneFar` | float | 7.0 | 0.0 - 10.0 | Depth boundary between Mid and Far zones |
| `zoneBlend` | float | 4.0 | 0.0 - 10.0 | Width of blending region between zones |
| `nearHue` | float | 0.0 | -180.0 - 180.0 | Hue shift for Near zone |
| `nearSaturation` | float | 5.0 | 0.0 - 10.0 | Saturation multiplier for Near zone |
| `nearTemperature` | float | 6.0 | -10.0 - 10.0 | Temperature shift for Near zone |
| `nearExposure` | float | 5.5 | -5.0 - 5.0 | Exposure compensation for Near zone |
| `midHue` | float | 0.0 | -180.0 - 180.0 | Hue shift for Mid zone |
| `midSaturation` | float | 5.0 | 0.0 - 10.0 | Saturation multiplier for Mid zone |
| `midTemperature` | float | 6.0 | -10.0 - 10.0 | Temperature shift for Mid zone |
| `midExposure` | float | 5.5 | -5.0 - 5.0 | Exposure compensation for Mid zone |
| `farHue` | float | 0.0 | -180.0 - 180.0 | Hue shift for Far zone |
| `farSaturation` | float | 5.0 | 0.0 - 10.0 | Saturation multiplier for Far zone |
| `farTemperature` | float | 6.0 | -10.0 - 10.0 | Temperature shift for Far zone |
| `farExposure` | float | 5.5 | -5.0 - 5.0 | Exposure compensation for Far zone |
| `contrast` | float | 0.5 | 0.0 - 1.0 | Global contrast (0.5 = no change) |
| `film_curve` | float | 0.0 | 0.0 - 1.0 | Film curve strength (0.0 = linear) |
| `blend` | float | 0.8 | 0.0 - 1.0 | Blend factor between original and processed frame |

---

## State Management

**Persistent State:**
- `parameters: dict` — Current parameter values (see table above)
- `_depth_source: Optional[AstraDepthSource]` — Depth map provider
- `_depth_frame: Optional[np.ndarray]` — Cached depth map (updated each frame)
- `_depth_texture: int` — OpenGL texture ID for depth map
- `_shader: ShaderProgram` — Compiled fragment shader
- `_frame_width: int` — Current frame width (default 1920)
- `_frame_height: int` — Current frame height (default 1080)

**Per-Frame State:**
- Temporary shader uniform values
- Intermediate framebuffer bindings

**Initialization:**
- Depth texture created on first `update_depth_data()` or `process_frame()`
- Shader compiled in `__init__()`
- Framebuffer created in `set_frame_size()` if needed

**Cleanup:**
- Delete depth texture (`glDeleteTextures`)
- Delete shader program
- Delete any framebuffers

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_R8 or GL_RGBA8 | frame size | Created on first depth update, recreated if resolution changes |
| Main shader | GLSL program | vertex + fragment | N/A | Init once |
| Work FBO (optional) | Framebuffer | RGBA8 | frame size | Init once if intermediate rendering needed |

**Memory Budget (1080p):**
- Depth texture: 1920 × 1080 × 1 byte = ~2.1 MB (GL_R8)
- Total VRAM: ~2.1 MB + shader overhead

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth source not set | `RuntimeError("No depth source")` | Call `set_depth_source()` before `process_frame()` |
| Depth frame missing | `RuntimeError("Depth data not available")` | Ensure depth source is providing frames |
| Shader compilation failure | `ShaderCompilationError` | Log error, effect becomes no-op |
| Depth texture creation fails | `RuntimeError` | Propagate to caller; may indicate out of GPU memory |
| Invalid parameter value | Shader undefined behavior | Document ranges; optionally clamp in `apply_uniforms()` |
| Resolution mismatch | Depth texture size ≠ frame size | Effect should resize depth texture automatically or raise error |
| Negative zone boundaries | Undefined behavior | Validate `zoneNear <= zoneFar` in `apply_uniforms()` |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations must occur on the thread owning the OpenGL context. Multiple instances can run on different threads with separate contexts. The `_depth_frame` cache is per-instance and mutated each frame, so concurrent `process_frame()` calls on the same instance will cause race conditions.

---

## Performance

**Expected Frame Time (1080p):**
- Depth lookup and zone determination: ~0.5 ms
- Per-zone color transformations: ~1-2 ms
- Global adjustments: ~0.5 ms
- Total: ~2-3 ms on discrete GPU

**Optimization Strategies:**
- Use `GL_R8` for depth texture to minimize memory bandwidth
- Precompute zone boundaries in vertex shader if possible
- Early-out if `blend == 0` (return original frame)
- Cache depth texture between frames; only update if depth source provides new data

---

## Integration Checklist

- [ ] Depth source is connected via `set_depth_source()` before processing
- [ ] Depth map resolution matches frame resolution (or effect handles resizing)
- [ ] Shader compiles successfully on all target platforms
- [ ] Parameters are validated before being sent to shader
- [ ] `cleanup()` is called when effect is destroyed to release GPU resources
- [ ] Pipeline orchestrator calls `update_depth_data()` each frame to refresh depth texture

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect instantiates without errors |
| `test_set_depth_source` | Depth source is stored correctly |
| `test_update_depth_data` | Depth texture is created/updated with valid data |
| `test_process_frame_no_depth` | Raises error if depth source not set |
| `test_process_frame_with_depth` | Applies color grading and returns frame of correct shape |
| `test_zone_boundaries` | `zoneNear` and `zoneFar` correctly divide depth range |
| `test_color_transformations` | Hue, saturation, temperature, exposure applied correctly |
| `test_blending` | Smooth transitions between zones using `zoneBlend` |
| `test_global_adjustments` | Contrast and film curve applied after zone grading |
| `test_cleanup` | All GPU resources released |
| `test_audio_reactivity` | Audio features modulate parameters if reactor connected |
| `test_blend_factor` | `blend=0` returns original, `blend=1` returns fully processed |

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD30: depth_color_grade` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_color_grade.py` — Original VJLive implementation
- `plugins/core/depth_color_grade/__init__.py` — VJLive-2 version with presets
- `plugins/vdepth/__init__.py` — Registration in depth plugin module
- `gl_leaks.txt` — Notes on texture allocation (missing `glDeleteTextures`)

Design decisions inherited:
- Effect name: `"depth_color_grade"`
- 3-zone model with `zoneNear`, `zoneFar`, `zoneBlend` parameters
- Per-zone parameters: `nearHue`, `nearSaturation`, `nearTemperature`, `nearExposure`, etc.
- Uses `DEPTH_COLOR_GRADE_FRAGMENT` shader (likely implements the 3-zone grading pipeline)
- Texture resource management: allocates with `glGenTextures`, must free with `glDeleteTextures` (noted as missing in legacy)
- Inherits from base `Effect` class (not `DepthEffect` specifically, though it uses depth source)

---

## Notes for Implementers

1. **Zone Boundaries**: The `zoneNear` and `zoneFar` parameters are in arbitrary depth units (0.0-10.0). The shader should normalize depth to [0,1] and then map to these zones. For example, if `zoneNear=3.0`, then depths 0.0-0.3 are "near", 0.3-0.7 are "mid", 0.7-1.0 are "far".

2. **Color Space**: The effect should work in linear RGB space for accurate color transformations. If the input is sRGB, convert to linear before applying hue/saturation/temperature, then convert back to sRGB for output.

3. **Temperature Shift**: The `nearTemperature` parameter should shift the color temperature. A positive value (e.g., 6.0) makes the zone warmer (more red/yellow), negative makes it cooler (more blue). Implement using a warm/cool color blend.

4. **Film Curve**: The `film_curve` parameter should apply a film-like tone curve (s-shaped) to the final graded image. This can be implemented as a simple gamma curve or a more complex film response curve.

5. **Performance**: The effect should be able to run at 60 FPS on a GTX 1060 or better at 1080p. If `zoneBlend` is large, the shader may need to compute more complex blend weights.

6. **Presets**: Consider implementing preset configurations for common use cases:
   - "warm_foreground": nearTemperature=8.0, farTemperature=-4.0
   - "saturated_subject": nearSaturation=8.0, farSaturation=2.0
   - "high_contrast": contrast=0.8, film_curve=0.3

7. **Audio Smoothing**: Audio features can be noisy. Consider applying exponential smoothing to audio-driven parameter changes to avoid flickering artifacts.

8. **Edge Cases**: Handle cases where `zoneNear > zoneFar` by swapping them or raising an error. Also handle `zoneBlend=0` (hard boundaries) and `zoneBlend=10` (very soft transitions).

---

## Easter Egg Idea

When the `nearTemperature` is set exactly to 6.0 and `farTemperature` to exactly -6.0, and the depth map contains a perfect gradient (smooth depth transition), the color grading briefly forms a hidden "thermal vision" pattern where the near zone glows with a subtle heat shimmer effect for exactly 3.33 seconds before returning to normal. The shimmer is visible only in the near zone and creates a subtle "heat haze" effect that VJs can feel rather than see.

---

## References

- VJLive1 legacy codebase: `vjlive1/plugins/depth_color_grade.py` (if exists)
- Color grading tutorials: https://learnopengl.com/Advanced-Lighting/SSAO
- Film color science: "Color Correction Handbook" by Alexis Van Hurkman
- Depth-based effects: https://www.shadertoy.com/view/4dlyR4

---

## Notes for Implementers

1. **Shader Precision**: Use `highp float` precision in GLSL for consistent color transformations, especially for hue rotation.

2. **Randomness**: The shader's pseudo-random function should be deterministic across frames when parameters don't change, to avoid flickering. Seed with `gl_FragCoord.xy` and `u_time`.

3. **Feedback Quality**: To avoid feedback accumulation artifacts, ensure the feedback blend uses linear interpolation in sRGB-correct space or convert to linear before blending.

4. **Audio Smoothing**: While the spec says no smoothing, consider adding optional smoothing (via `audio_smoothing` parameter) in a future extension to reduce jitter from beat detection noise.

5. **Extensibility**: The color grading algorithm could be extended with:
   - Color palette controls
   - Grain shape variations (circles, squares, textures)
   - Motion blur per grain
   - Depth-based grain scaling (if depth map provided)

---
>>>>>>> REPLACE