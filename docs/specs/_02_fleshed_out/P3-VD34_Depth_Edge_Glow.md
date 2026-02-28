# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD34_Depth_Edge_Glow.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD34 — DepthEdgeGlowEffect

## Description

The Depth Edge Glow effect is a cyber-punk aesthetic weapon that aggressively edge-detects physical depth boundaries and ignites them with simulated neon tubing. It transforms subjects into glowing wireframe entities by combining multi-scale Sobel edge detection on depth maps with topographic contour lines and bloom effects. The effect dims the original video and adds pulsating, colorful neon edges that follow depth discontinuities, creating a striking visual style perfect for VJ performances.

## What This Module Does

- Performs multi-scale Sobel edge detection on depth maps to identify depth boundaries
- Extracts topographic contour lines at regular depth intervals
- Applies configurable glow (bloom) around edges and contours
- Supports customizable edge colors (RGB) or dynamic hue cycling modes
- Includes pulsation effects synchronized to audio or time
- Dims the original video to make neon edges pop
- Integrates with `DepthEffect` base class for depth source management
- Uses GPU-accelerated fragment shaders for real-time performance at 60 FPS

## What This Module Does NOT Do

- Does NOT generate depth maps (requires external `AstraDepthSource`)
- Does NOT perform edge detection on color video (depth-only)
- Does NOT provide CPU fallback (requires GPU for shader-based processing)
- Does NOT manage node graph connections (caller must route depth source and video)
- Does NOT store persistent state across sessions (all parameters in-memory)
- Does NOT implement advanced bloom (uses simple additive glow, not separable bloom)
- Does NOT support audio reactivity out of the box (relies on `AudioReactor` wrapper)

---

## Detailed Behavior

### Edge Detection

The effect uses Sobel operators to detect depth gradients:

```glsl
// Sobel kernels
float sobel_x[9] = float[](-1, 0, 1, -2, 0, 2, -1, 0, 1);
float sobel_y[9] = float[](-1, -2, -1, 0, 0, 0, 1, 2, 1);

// Compute gradient
float gx = 0.0, gy = 0.0;
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
        float sample = texture(depth_texture, uv + vec2(i-1, j-1) * pixel_size).r;
        gx += sample * sobel_x[i*3 + j];
        gy += sample * sobel_y[i*3 + j];
    }
}
float gradient = sqrt(gx*gx + gy*gy);
```

The `edgeThreshold` parameter controls the sensitivity: gradients above this threshold are considered edges.

### Multi-Scale Edges

The effect computes edges at multiple scales (using different pixel offsets) and combines them:

- **Scale 1**: 1-pixel offset (fine details)
- **Scale 2**: 2-pixel offset (medium)
- **Scale 3**: 4-pixel offset (coarse)

The `edgeThickness` parameter controls how many scales to include and their weighting.

### Contour Lines

In addition to gradient-based edges, the effect extracts iso-depth contour lines:

```glsl
float contour = step(contourWidth, fract(depth * numContours));
```

Where `contourLines` controls the number of contour bands, and `contourWidth` controls their thickness.

### Glow (Bloom)

The glow effect is achieved by blurring the edge mask and adding it back to the image:

```glsl
// Simple box blur for glow
float glow = 0.0;
for (int i = -radius; i <= radius; i++) {
    for (int j = -radius; j <= radius; j++) {
        glow += edge_mask.r;
    }
}
glow /= (2*radius+1)*(2*radius+1);
```

The `glowRadius` controls blur size, and `glowIntensity` controls brightness.

### Colorization

Edges can be colored in several ways:

- **Static RGB**: Use `edgeColorR`, `edgeColorG`, `edgeColorB` as constant color
- **Hue Mode**: If `hueMode > 0`, cycle hue based on time, position, and depth:
  ```glsl
  float hue = time * hueMode + uv.x * 0.5 + depth;
  line_color = hsv2rgb(vec3(hue, 1.0, 1.0));
  ```

### Pulsation

A `pulse` factor modulates edge intensity over time (or via audio):

```glsl
float pulse = 0.5 + 0.5 * sin(time * pulse_frequency);
```

The pulse is applied to both edge intensity and glow.

### Composition

The final output is:

```glsl
vec3 dimmed_source = source.rgb * (1.0 - source_dim * 0.9);
vec3 result = dimmed_source;
result += line_color * total_edge * pulse * glow_intensity;
result += line_color * final_glow * pulse * 0.5;
fragColor = mix(source, vec4(result, 1.0), u_mix);
```

Where `source_dim` is a parameter controlling how much to dim the original.

---

## Public Interface

```python
class DepthEdgeGlowEffect:
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
| `audio_analyzer` | `AudioAnalyzer` | Optional audio feature source | Provides BEAT_INTENSITY, TEMPO |

**Output**: `np.ndarray` — Processed frame with neon edge glow, same shape/format as input

---

## Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `edgeThreshold` | float | 4.0 | 0.0 - 20.0 | Sensitivity of edge detection (higher = fewer edges) |
| `edgeThickness` | float | 4.0 | 1.0 - 10.0 | Thickness of edges (number of scales) |
| `glowRadius` | float | 5.0 | 0.0 - 20.0 | Blur radius for glow effect (in pixels) |
| `glowIntensity` | float | 6.0 | 0.0 - 20.0 | Brightness of the glow |
| `contourLines` | float | 4.0 | 1.0 - 20.0 | Number of topographic contour bands |
| `contourWidth` | float | 3.0 | 0.1 - 10.0 | Thickness of contour lines |
| `hueMode` | float | 3.3 | 0.0 - 10.0 | Hue cycling speed (0 = static RGB) |
| `edgeColorR` | float | 0.0 | 0.0 - 1.0 | Red component of static edge color |
| `edgeColorG` | float | 1.0 | 0.0 - 1.0 | Green component of static edge color |
| `edgeColorB` | float | 0.0 | 0.0 - 1.0 | Blue component of static edge color |
| `sourceDim` | float | 0.5 | 0.0 - 1.0 | How much to dim the original video (0 = no dim) |
| `pulseFrequency` | float | 2.0 | 0.0 - 10.0 | Frequency of pulsation (Hz) |
| `pulseAmplitude` | float | 0.5 | 0.0 - 1.0 | Amplitude of pulsation (0 = constant) |
| `blend` | float | 0.8 | 0.0 - 1.0 | Blend factor between original and processed output |

---

## State Management

**Persistent State:**
- `parameters: dict` — Current parameter values (see table above)
- `_depth_source: Optional[AstraDepthSource]` — Depth map provider
- `_depth_frame: Optional[np.ndarray]` — Cached depth map (updated each frame)
- `_depth_texture: int` — OpenGL texture ID for depth map
- `_shader: ShaderProgram` — Compiled fragment shader
- `_frame_width: int` — Current frame width
- `_frame_height: int` — Current frame height

**Per-Frame State:**
- Temporary shader uniform values (time, pulse)
- Intermediate framebuffer bindings (for glow blur)

**Initialization:**
- Depth texture created on first `update_depth_data()` or `process_frame()`
- Shader compiled in `__init__()`
- Glow FBO/texture created on demand

**Cleanup:**
- Delete depth texture (`glDeleteTextures`)
- Delete glow FBO/texture if allocated
- Delete shader program

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_R8 or GL_RGBA8 | frame size | Created on first depth update |
| Glow FBO (optional) | Framebuffer | RGBA8 | frame size + blur radius | Created on first glow pass |
| Glow texture (optional) | GL_TEXTURE_2D | RGBA8 | frame size + blur radius | Created with FBO |
| Main shader | GLSL program | vertex + fragment | N/A | Init once |

**Memory Budget (1080p):**
- Depth texture: ~2.1 MB (GL_R8)
- Glow FBO + texture: ~8.3 MB each (if used)
- Total: ~2.1 - 18.6 MB depending on glow usage

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth source not set | `RuntimeError("No depth source")` | Call `set_depth_source()` before `process_frame()` |
| Depth frame missing | `RuntimeError("Depth data not available")` | Ensure depth source is providing frames |
| Shader compilation failure | `ShaderCompilationError` | Log error, effect becomes no-op |
| Texture/FBO creation fails | `RuntimeError` | Propagate to caller; may indicate out of GPU memory |
| `edgeThreshold < 0` | No edges detected | Document valid range; optionally clamp |
| `glowRadius` too large | Performance degradation | Warn if `glowRadius > 20` |
| `hueMode = 0` with static RGB color | Uses `edgeColorR/G/B` | This is expected behavior |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations must occur on the thread owning the OpenGL context. The `_depth_frame` cache is per-instance and mutated each frame, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (1080p):**
- Sobel edge detection (3 scales): ~2-3 ms
- Contour line extraction: ~0.5 ms
- Glow blur (if radius=5): ~1-2 ms (separable blur recommended)
- Colorization and composition: ~0.5 ms
- Total: ~4-6 ms on discrete GPU, ~10-15 ms on integrated GPU

**Optimization Strategies:**
- Use `GL_R8` for depth texture to minimize memory bandwidth
- Implement separable blur for glow (horizontal + vertical) instead of 2D convolution
- Early-out if `glowRadius=0` (skip blur pass)
- Cache depth texture between frames; only update if depth source provides new data
- Consider using lower resolution for glow pass (downsample, blur, upsample)

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
| `test_process_frame_basic` | Applies edge glow and returns frame of correct shape |
| `test_sobel_edge_detection` | Edges detected at depth discontinuities |
| `test_contour_lines` | Contour lines appear at regular depth intervals |
| `test_glow_radius` | Larger radius creates softer, bigger glow |
| `test_glow_intensity` | Intensity controls brightness of glow |
| `test_color_modes` | Static RGB vs. hue cycling produce different results |
| `test_pulsation` | Pulse modulates edge intensity over time |
| `test_source_dimming` | `sourceDim` controls how much original is visible |
| `test_edge_threshold` | Higher threshold reduces number of edges |
| `test_cleanup` | All GPU resources released |
| `test_audio_reactivity` | Audio can modulate pulse or intensity if reactor connected |

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD34: depth_edge_glow` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_edge_glow.py` — Original VJLive implementation
- `plugins/core/depth_edge_glow/__init__.py` — VJLive-2 version
- `plugins/vdepth/__init__.py` — Registration in depth plugin module
- `gl_leaks.txt` — Notes on texture allocation (missing `glDeleteTextures`)

Design decisions inherited:
- Effect name: `"depth_edge_glow"`
- Multi-scale Sobel edge detection
- Contour line extraction using `fract(depth * numContours)`
- Glow via blur and additive blending
- Parameters: `edgeThreshold`, `edgeThickness`, `glowRadius`, `glowIntensity`, `contourLines`, `contourWidth`, `hueMode`, `edgeColorR/G/B`, `sourceDim`, `pulseFrequency`, `pulseAmplitude`
- Uses `DEPTH_EDGE_GLOW_FRAGMENT` shader
- Texture resource management: allocates with `glGenTextures`, must free with `glDeleteTextures` (noted as missing in legacy)
- Inherits from base `Effect` class (not `DepthEffect` specifically, though it uses depth source)

---

## Notes for Implementers

1. **Sobel Edge Detection**: The Sobel operator is a 3x3 gradient filter. Compute Gx and Gy separately, then magnitude `sqrt(Gx² + Gy²)`. For performance, you can use `abs(Gx) + abs(Gy)` as an approximation.

2. **Multi-Scale**: Compute Sobel at multiple pixel offsets (1, 2, 4) and combine with weights. This captures edges at different scales. The `edgeThickness` parameter can control how many scales to include.

3. **Contour Lines**: Contours are iso-depth lines. Use `fract(depth * contourLines)` to get repeating bands, then `step(contourWidth, value)` to get thin lines. For anti-aliased contours, use `smoothstep`.

4. **Glow Implementation**: The glow is essentially a bloom effect. Blur the combined edge mask (Sobel edges + contours) using a separable Gaussian or box blur, then additively blend back to the image. A simple box blur is acceptable but Gaussian looks better.

5. **Color Modes**:
   - If `hueMode == 0`, use static RGB from `edgeColorR/G/B`.
   - If `hueMode > 0`, compute dynamic hue: `hue = time * hueMode + uv.x * 0.5 + depth`. Convert HSV to RGB.
   - The `+ depth` term makes hue vary with depth, creating rainbow depth-coded edges.

6. **Pulsation**: The pulse factor can be time-based: `pulse = 0.5 + 0.5 * sin(time * pulse_frequency * 2π)`. Multiply by `pulseAmplitude` to control strength. For audio reactivity, replace time with audio feature (e.g., beat intensity).

7. **Source Dimming**: The original video is multiplied by `(1.0 - sourceDim * 0.9)` to make it darker, so the neon edges stand out. `sourceDim=0` leaves original unchanged; `sourceDim=1` makes it nearly black.

8. **Performance**: Sobel is the most expensive part. Consider:
   - Using a smaller kernel (3x3 is already small)
   - Downsampling depth for edge detection, then upsampling mask
   - Early-out if pixel is not near an edge (skip blur)

9. **Shader Precision**: Use `mediump` or `highp` for depth gradients to avoid banding. Edge detection is sensitive to precision.

10. **Resource Management**: The legacy code notes missing `glDeleteTextures`. Ensure your `cleanup()` deletes the depth texture and any FBOs/textures used for glow.

---

## Easter Egg Idea

When `edgeThreshold` is set exactly to 3.33, `contourLines` to exactly 7, and `hueMode` to exactly 0.618, and the depth map contains a perfect gradient, the edge detection briefly reveals a hidden "golden ratio" pattern in the edge mask's alpha channel that lasts exactly 6.66 seconds before returning to normal. The pattern is visible only in debug mode but subtly influences the glow's color distribution in a way that VJs can feel rather than see.

---

## References

- VJLive1 legacy codebase: `vjlive1/plugins/depth_edge_glow.py` (if exists)
- Sobel edge detection: https://en.wikipedia.org/wiki/Sobel_operator
- Bloom effect: https://learnopengl.com/Advanced-Lighting/Bloom
- HSV to RGB conversion: https://en.wikipedia.org/wiki/HSL_and_HSV

---

## Implementation Tips

1. **Shader Structure**:
   ```glsl
   uniform sampler2D u_depth_texture;
   uniform float u_edge_threshold;
   uniform float u_edge_thickness;
   uniform float u_glow_radius;
   uniform float u_glow_intensity;
   uniform float u_contour_lines;
   uniform float u_contour_width;
   uniform float u_hue_mode;
   uniform vec3 u_edge_color;
   uniform float u_source_dim;
   uniform float u_pulse;
   uniform float u_time;
   
   float sobel_edge(vec2 uv, float offset) {
       vec2 pixel = vec2(offset / u_resolution);
       // ... compute sobel gradient ...
       return gradient;
   }
   
   float get_contours(float depth) {
       return step(u_contour_width, fract(depth * u_contour_lines));
   }
   
   vec3 hsv2rgb(vec3 hsv) { /* standard conversion */ }
   
   void main() {
       float depth = texture(u_depth_texture, uv).r;
       
       // Multi-scale Sobel
       float edge = 0.0;
       for (float i = 1.0; i <= 3.0; i *= 2.0) {
           if (i <= u_edge_thickness) {
               edge += sobel_edge(uv, i);
           }
       }
       edge = smoothstep(u_edge_threshold - 1.0, u_edge_threshold + 1.0, edge);
       
       // Contours
       float contours = get_contours(depth);
       
       // Combine
       float total_edge = max(edge, contours);
       
       // Glow (blur)
       float final_glow = blur_edge_mask(total_edge, u_glow_radius);
       
       // Color
       vec3 line_color;
       if (u_hue_mode > 0.0) {
           float hue = u_time * u_hue_mode + uv.x * 0.5 + depth;
           line_color = hsv2rgb(vec3(hue, 1.0, 1.0));
       } else {
           line_color = u_edge_color;
       }
       
       // Pulse
       float pulse = 0.5 + 0.5 * sin(u_time * u_pulse_frequency * 6.28318);
       
       // Compose
       vec3 dimmed = source.rgb * (1.0 - u_source_dim * 0.9);
       vec3 result = dimmed;
       result += line_color * total_edge * pulse * u_glow_intensity;
       result += line_color * final_glow * pulse * 0.5;
       
       fragColor = mix(source, vec4(result, 1.0), u_mix);
   }
   ```

2. **Separable Blur**: Implement glow blur as two passes (horizontal + vertical) for O(N) instead of O(N²). Use a temporary FBO between passes.

3. **Edge Threshold Tuning**: The `edgeThreshold` is in depth gradient units (not normalized). You may need to scale depth to 0-1 and multiply by a sensitivity factor. Provide a good default (4.0) and allow range 0-20.

4. **Testing**: Create synthetic depth maps with sharp edges (step functions) to verify edge detection. Also test with smooth gradients to ensure contours work.

5. **Debug View**: Provide a debug output that shows just the edge mask or glow to tune parameters.

6. **Audio Reactivity**: Map `BEAT_INTENSITY` to `pulseAmplitude` or `glowIntensity` for beat-synchronized pulsing.

7. **Performance**: If the effect is too slow, consider:
   - Using a lower resolution for edge detection (e.g., half-res) and upsampling mask
   - Reducing number of Sobel scales
   - Using a smaller glow kernel (radius 3 instead of 5)

---
>>>>>>> REPLACE