# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD62_Depth_Portal_Composite.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD62 — DepthPortalCompositeEffect

## Description

The DepthPortalCompositeEffect creates a depth-keyed composite that isolates the performer (foreground) using depth data and composites them over a second video (background). It's essentially a green screen replacement that uses depth instead of chroma keying. The effect creates a "portal" where the performer appears to be in a different environment, with optional edge glow for an augmented reality aesthetic.

This effect is ideal for VJ performances that want to place performers in virtual environments without requiring a physical green screen. The depth camera naturally separates the performer from the background based on distance, creating clean isolation even in challenging lighting conditions. The effect supports configurable depth ranges, foreground scaling/positioning, and optional edge effects.

## What This Module Does

- Creates depth-based matte for foreground isolation
- Composites foreground over background video
- Supports configurable depth slice (near/far thresholds)
- Allows foreground scaling and offset
- Optional edge glow at matte boundaries
- GPU-accelerated with smooth matte edges
- Handles depth and color from same or separate sources

## What This Module Does NOT Do

- Does NOT provide CPU fallback (GPU required)
- Does NOT include advanced matte refinement (e.g., spill suppression)
- Does NOT support multiple depth layers (binary foreground/background)
- Does NOT store persistent state across sessions
- Does NOT include background blur or other background effects
- Does NOT support 3D reconstruction (2D composite only)

---

## Detailed Behavior

### Depth-Keyed Compositing Pipeline

1. **Capture depth frame**: `depth_current` (HxW, normalized 0-1)
2. **Create depth matte**:
   - Pixels with depth in range `[sliceNear, sliceFar]` → foreground (matte = 1)
   - Pixels outside range → background (matte = 0)
   - Smooth transition at boundaries (feather)
3. **Sample foreground color**: From color frame (or depth source's color)
4. **Sample background color**: From second video feed
5. **Composite**:
   ```
   result = mix(background, foreground, matte * u_mix)
   ```
6. **Optional edge glow**: Detect matte edges, add colored glow
7. **Apply foreground transform**: Scale and offset foreground before compositing

### Depth Slice

The `sliceNear` and `sliceFar` parameters define the depth range that is considered foreground:
- `sliceNear`: Near depth threshold (0-10 → normalized 0-1)
- `sliceFar`: Far depth threshold (0-10 → normalized 0-1)
- Foreground: `sliceNear <= depth <= sliceFar`
- Background: `depth < sliceNear` or `depth > sliceFar`
- Feather: Smooth transition of width `feather` near boundaries

### Matte Smoothing

To avoid hard edges, the matte is smoothed:
```glsl
float near_edge = smoothstep(sliceNear - feather, sliceNear + feather, depth);
float far_edge = 1.0 - smoothstep(sliceFar - feather, sliceFar + feather, depth);
float matte = near_edge * far_edge;
```

### Foreground Transform

The foreground can be scaled and offset before compositing:
- `fgScale`: Scale factor (0.0-10.0 → 0.0-2.0 typically)
- `fgOffsetX`, `fgOffsetY`: Translation in normalized UV space

### Edge Glow

Optional edge detection on the matte to create an AR-style glow:
```glsl
float edge = abs(dFdx(matte)) + abs(dFdy(matte));
vec3 edge_color = vec3(0.3, 0.6, 1.0) * edge * 4.0;
result += edge_color * 0.3;
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `sliceNear` | float | 1.5 | 0.0-10.0 | Near depth threshold for foreground |
| `sliceFar` | float | 4.0 | 0.0-10.0 | Far depth threshold for foreground |
| `feather` | float | 0.5 | 0.0-10.0 | Matte edge softness |
| `fgScale` | float | 5.0 | 0.0-10.0 | Foreground scale (1.0 = original) |
| `fgOffsetX` | float | 5.0 | 0.0-10.0 | Foreground X offset (normalized) |
| `fgOffsetY` | float | 5.0 | 0.0-10.0 | Foreground Y offset (normalized) |
| `edgeGlow` | float | 0.0 | 0.0-10.0 | Edge glow intensity (0=off) |
| `edgeColorR` | float | 3.0 | 0.0-10.0 | Edge glow red (0-1) |
| `edgeColorG` | float | 6.0 | 0.0-10.0 | Edge glow green (0-1) |
| `edgeColorB` | float | 10.0 | 0.0-10.0 | Edge glow blue (0-1) |

**Inherited from Effect**: `u_mix`

---

## Public Interface

```python
class DepthPortalCompositeEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def set_background_source(self, source) -> None: ...  # Second video
    def update_depth_and_color(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray, background: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) — foreground source |
| `background` | `np.ndarray` | Background video (HxWxC, RGB) |
| **Output** | `np.ndarray` | Composite output (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Current depth frame
- `_color_frame: Optional[np.ndarray]` — Color frame (if separate from depth source)
- `_background_source: Optional[VideoSource]` — Background video source
- `_background_frame: Optional[np.ndarray]` — Current background frame
- `_parameters: dict` — Composite parameters
- `_shader: ShaderProgram` — Compiled shader
- `_fg_texture: int` — Foreground texture
- `_bg_texture: int` — Background texture
- `_depth_texture: int` — Depth texture

**Per-Frame:**
- Update depth and color from source
- Update background from background source
- Upload textures (foreground, background, depth)
- Set shader uniforms
- Render composite
- Return result

**Initialization:**
- Create foreground texture
- Create background texture
- Create depth texture
- Compile shader
- Default parameters: sliceNear=1.5, sliceFar=4.0, feather=0.5, fgScale=5.0, fgOffsetX=5.0, fgOffsetY=5.0, edgeGlow=0.0, edgeColorR=3.0, edgeColorG=6.0, edgeColorB=10.0

**Cleanup:**
- Delete foreground texture
- Delete background texture
- Delete depth texture
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Foreground texture | GL_TEXTURE_2D | GL_RGBA8 | frame size | Updated each frame |
| Background texture | GL_TEXTURE_2D | GL_RGBA8 | background size | Updated each frame |
| Depth texture | GL_TEXTURE_2D | GL_RED, GL_UNSIGNED_BYTE | depth_frame size | Updated each frame |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Foreground texture: 921,600 bytes
- Background texture: 921,600 bytes
- Depth texture: 307,200 bytes
- Shader: ~20-30 KB
- Total: ~2.2 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| No depth source | Use uniform matte (0.5) | Normal operation |
| No background source | Use black background | Normal operation |
| Texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and texture updates must occur on the thread with the OpenGL context. The effect updates multiple textures each frame, and concurrent `process_frame()` calls will cause race conditions and corrupted rendering. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Texture uploads (3 textures): ~1.5-3 ms
- Shader execution (matte + composite + edge): ~2-4 ms
- Total: ~3.5-7 ms on GPU

**Optimization Strategies:**
- Reduce texture uploads by caching unchanged frames
- Use lower resolution for depth texture
- Disable edge glow if not needed
- Combine foreground and depth into single texture if possible
- Use simpler matte (no feather) for performance

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Background source set and providing video frames
- [ ] Composite parameters configured (slice, feather, transform)
- [ ] Edge glow configured (if needed)
- [ ] `process_frame()` called each frame with both videos
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_depth_matte` | Depth correctly creates binary matte |
| `test_slice_range` | sliceNear/sliceFar control foreground range |
| `test_feather` | Feather smooths matte edges |
| `test_foreground_transform` | Scale and offset applied to foreground |
| `test_edge_glow` | Edge glow appears at matte boundaries |
| `test_composite` | Foreground correctly composited over background |
| `test_no_background` | Falls back to black background |
| `test_no_depth` | Falls back to uniform matte |
| `test_cleanup` | All GPU resources released |
| `test_no_memory_leak` | Repeated init/cleanup cycles don't leak |

**Minimum coverage:** 85%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD62: depth_portal_composite_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_portal_composite.py` — VJLive Original implementation
- `plugins/core/depth_portal_composite/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_portal_composite/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthPortalCompositeEffect` allocates `glGenTextures` and must free them
- `assets/gists/depth_portal_composite.json` — Gist documentation

Design decisions inherited:
- Effect name: `depth_portal_composite`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for matte generation
- Parameters: `sliceNear`, `sliceFar`, `feather`, `fgScale`, `fgOffsetX`, `fgOffsetY`, `edgeGlow`, `edgeColorR`, `edgeColorG`, `edgeColorB`
- Allocates GL resources: foreground texture, background texture, depth texture
- Shader implements depth-based matte, foreground transform, and edge glow
- Method `_update_depth_and_color()` fetches both depth and color

---

## Notes for Implementers

1. **Core Concept**: This effect uses depth to create a matte (alpha mask) that separates foreground (performer) from background. It's a depth-based keyer that composites the performer over a second video.

2. **Depth Matte Generation**:
   ```glsl
   float depth = texture(depth_tex, uv).r;
   float near = sliceNear;  // 0-1 normalized
   float far = sliceFar;    // 0-1 normalized
   
   float near_edge = smoothstep(near - feather, near + feather, depth);
   float far_edge = 1.0 - smoothstep(far - feather, far + feather, depth);
   float matte = near_edge * far_edge;
   ```
   This creates a matte that is 1 for depths between `sliceNear` and `sliceFar`, 0 outside, with smooth transitions.

3. **Foreground Transform**:
   Before compositing, the foreground UV can be scaled and offset:
   ```glsl
   vec2 fg_uv = uv;
   fg_uv = (fg_uv - 0.5) * fgScale + 0.5;  // Scale about center
   fg_uv += vec2(fgOffsetX, fgOffsetY);    // Offset
   vec4 fg_color = texture(fg_tex, fg_uv);
   ```

4. **Edge Glow**:
   Detect edges in the matte using derivatives:
   ```glsl
   if (edgeGlow > 0.0) {
       float edge = abs(dFdx(matte)) + abs(dFdy(matte));
       vec3 edge_color = vec3(edgeColorR, edgeColorG, edgeColorB) * edge * 4.0;
       result += edge_color * edgeGlow * 0.3;
   }
   ```

5. **Composite**:
   ```glsl
   vec3 bg_color = texture(bg_tex, uv).rgb;
   vec3 fg_color = texture(fg_tex, uv).rgb;  // or transformed UV
   vec3 result = mix(bg_color, fg_color, matte * u_mix);
   ```

6. **Parameter Mapping**:
   - `sliceNear`, `sliceFar`: 0-10 → 0.0-1.0 (divide by 10)
   - `feather`: 0-10 → 0.0-0.1 (divide by 100) or similar
   - `fgScale`: 0-10 → 0.0-2.0 (5.0 = 1.0, so 5/10=0.5? Actually: scale = param/5.0? Need to check legacy)
   - `fgOffsetX`, `fgOffsetY`: 0-10 → -0.5 to +0.5 (map 5=0, 0=-0.5, 10=+0.5)
   - `edgeGlow`: 0-10 → 0.0-1.0 (divide by 10)
   - `edgeColorR/G/B`: 0-10 → 0.0-1.0 (divide by 10)

7. **Shader Uniforms**:
   ```glsl
   uniform sampler2D fg_tex;        // Foreground (performer)
   uniform sampler2D bg_tex;        // Background
   uniform sampler2D depth_tex;     // Depth for matte
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float sliceNear;         // 0-1
   uniform float sliceFar;          // 0-1
   uniform float feather;           // 0-0.1
   uniform float fgScale;           // 0-2
   uniform vec2 fgOffset;           // -0.5 to 0.5
   uniform float edgeGlow;          // 0-1
   uniform vec3 edgeColor;          // 0-1 RGB
   ```

8. **Two-Video Inputs**: The effect needs two video sources:
   - Foreground: The performer (from depth camera's color or separate source)
   - Background: The second video to composite onto
   The legacy may use the same source for both, or separate. Document the expected usage.

9. **Depth Source Color**: The depth source may also provide a color frame (`get_color_frame()`). If available, use that as foreground. Otherwise, use the input `frame` as foreground.

10. **PRESETS**:
    ```python
    PRESETS = {
        "clean": {
            "sliceNear": 1.5, "sliceFar": 4.0, "feather": 0.5,
            "fgScale": 1.0, "fgOffsetX": 0.0, "fgOffsetY": 0.0,
            "edgeGlow": 0.0,
        },
        "tight": {
            "sliceNear": 2.0, "sliceFar": 3.5, "feather": 0.2,
            "fgScale": 1.0, "fgOffsetX": 0.0, "fgOffsetY": 0.0,
            "edgeGlow": 0.0,
        },
        "loose": {
            "sliceNear": 1.0, "sliceFar": 5.0, "feather": 1.0,
            "fgScale": 1.0, "fgOffsetX": 0.0, "fgOffsetY": 0.0,
            "edgeGlow": 0.0,
        },
        "ar_glow": {
            "sliceNear": 1.5, "sliceFar": 4.0, "feather": 0.3,
            "fgScale": 1.0, "fgOffsetX": 0.0, "fgOffsetY": 0.0,
            "edgeGlow": 5.0, "edgeColorR": 0.3, "edgeColorG": 0.6, "edgeColorB": 1.0,
        },
        "zoomed_in": {
            "sliceNear": 1.5, "sliceFar": 4.0, "feather": 0.5,
            "fgScale": 1.5, "fgOffsetX": 0.0, "fgOffsetY": 0.0,
            "edgeGlow": 0.0,
        },
    }
    ```

11. **Testing Strategy**:
    - Test with synthetic depth (gradient, step function)
    - Verify matte correctly isolates depth range
    - Test feather: edges should be smooth
    - Test foreground transform: scaling and offset
    - Test edge glow: appears only at matte boundaries
    - Test composite: foreground over background

12. **Performance**: The effect is relatively lightweight. Main cost is texture uploads and shader execution. Optimize by:
    - Caching textures if sources don't change
    - Using lower resolution depth texture
    - Disabling edge glow if not needed

13. **Future Extensions**:
    - Add background blur (depth-of-field effect)
    - Add spill suppression (remove color spill from background)
    - Add multiple depth layers (multi-plane composite)
    - Add depth-based color correction on foreground
    - Add audio reactivity to edge glow

---
-

## References

- Alpha compositing: https://en.wikipedia.org/wiki/Alpha_compositing
- Chroma key: https://en.wikipedia.org/wiki/Chroma_key
- Depth of field: https://en.wikipedia.org/wiki/Depth_of_field
- Edge detection: https://en.wikipedia.org/wiki/Edge_detection
- VJLive legacy: `plugins/vdepth/depth_portal_composite.py`

---

## Implementation Tips

1. **Full Shader**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D fg_tex;        // Foreground (performer)
   uniform sampler2D bg_tex;        // Background
   uniform sampler2D depth_tex;     // Depth for matte
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float sliceNear;         // 0-1
   uniform float sliceFar;          // 0-1
   uniform float feather;           // 0-0.1
   uniform float fgScale;           // 0-2
   uniform vec2 fgOffset;           // -0.5 to 0.5
   uniform float edgeGlow;          // 0-1
   uniform vec3 edgeColor;          // 0-1 RGB
   
   void main() {
       // Get depth
       float depth = texture(depth_tex, uv).r;
       
       // Compute matte
       float near_edge = smoothstep(sliceNear - feather, sliceNear + feather, depth);
       float far_edge = 1.0 - smoothstep(sliceFar - feather, sliceFar + feather, depth);
       float matte = near_edge * far_edge;
       
       // Foreground transform
       vec2 fg_uv = uv;
       fg_uv = (fg_uv - 0.5) * fgScale + 0.5;
       fg_uv += fgOffset;
       
       // Sample colors
       vec3 bg_color = texture(bg_tex, uv).rgb;
       vec3 fg_color = texture(fg_tex, fg_uv).rgb;
       
       // Composite
       vec3 result = mix(bg_color, fg_color, matte * u_mix);
       
       // Edge glow
       if (edgeGlow > 0.0) {
           float edge = abs(dFdx(matte)) + abs(dFdy(matte));
           result += edgeColor * edge * 4.0 * edgeGlow * 0.3;
       }
       
       fragColor = vec4(result, 1.0);
   }
   ```

2. **Python Implementation**:
   ```python
   class DepthPortalCompositeEffect(Effect):
       def __init__(self):
           super().__init__("depth_portal_composite", PORTAL_VERTEX, PORTAL_FRAGMENT)
           
           self.depth_source = None
           self.depth_frame = None
           self.color_frame = None
           
           self.background_source = None
           self.background_frame = None
           
           self.fg_texture = 0
           self.bg_texture = 0
           self.depth_texture = 0
           
           self.parameters = {
               'sliceNear': 1.5,
               'sliceFar': 4.0,
               'feather': 0.5,
               'fgScale': 5.0,
               'fgOffsetX': 5.0,
               'fgOffsetY': 5.0,
               'edgeGlow': 0.0,
               'edgeColorR': 3.0,
               'edgeColorG': 6.0,
               'edgeColorB': 10.0,
           }
           
           self.shader = None
       
       def _ensure_textures(self, width, height):
           if self.fg_texture == 0:
               self.fg_texture = glGenTextures(1)
               glBindTexture(GL_TEXTURE_2D, self.fg_texture)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
               
           if self.bg_texture == 0:
               self.bg_texture = glGenTextures(1)
               # ... similar setup
               
           if self.depth_texture == 0:
               self.depth_texture = glGenTextures(1)
               # ... setup for GL_RED
   ```

3. **Parameter Mapping**:
   ```python
   def _map_param(self, name, out_min, out_max):
       raw = self.parameters.get(name, 5.0)
       return out_min + (raw / 10.0) * (out_max - out_min)
   
   def _apply_uniforms(self, time, resolution):
       self.shader.set_uniform("sliceNear", self._map_param("sliceNear", 0.0, 1.0))
       self.shader.set_uniform("sliceFar", self._map_param("sliceFar", 0.0, 1.0))
       self.shader.set_uniform("feather", self._map_param("feather", 0.0, 0.1))
       self.shader.set_uniform("fgScale", self._map_param("fgScale", 0.5, 1.5))  # or 0-2
       self.shader.set_uniform("fgOffset", vec2(
           self._map_param("fgOffsetX", -0.5, 0.5),
           self._map_param("fgOffsetY", -0.5, 0.5)
       ))
       self.shader.set_uniform("edgeGlow", self._map_param("edgeGlow", 0.0, 1.0))
       self.shader.set_uniform("edgeColor", vec3(
           self._map_param("edgeColorR", 0.0, 1.0),
           self._map_param("edgeColorG", 0.0, 1.0),
           self._map_param("edgeColorB", 0.0, 1.0)
       ))
   ```

4. **Process Frame**:
   ```python
   def process_frame(self, frame, background):
       h, w = frame.shape[:2]
       self._ensure_textures(w, h)
       
       # Update depth and color
       self._update_depth_and_color()
       
       # Upload textures
       glActiveTexture(GL_TEXTURE0)
       glBindTexture(GL_TEXTURE_2D, self.fg_texture)
       glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, frame)
       
       glActiveTexture(GL_TEXTURE1)
       glBindTexture(GL_TEXTURE_2D, self.bg_texture)
       glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, background)
       
       glActiveTexture(GL_TEXTURE2)
       glBindTexture(GL_TEXTURE_2D, self.depth_texture)
       if self.depth_frame is not None:
           glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, w, h, 0, GL_RED, GL_UNSIGNED_BYTE, self.depth_frame)
       
       # Render
       glBindFramebuffer(GL_FRAMEBUFFER, 0)
       self.shader.use()
       self._apply_uniforms(time, (w, h))
       
       glUniform1i(glGetUniformLocation(self.shader.program, "fg_tex"), 0)
       glUniform1i(glGetUniformLocation(self.shader.program, "bg_tex"), 1)
       glUniform1i(glGetUniformLocation(self.shader.program, "depth_tex"), 2)
       
       draw_fullscreen_quad()
       
       result = self._read_pixels()
       return result
   ```

5. **Depth and Color Update**: The legacy method `_update_depth_and_color()` suggests that the depth source may provide both depth and color. If the depth source has a `get_color_frame()` method, use that as the foreground. Otherwise, use the input `frame`.

6. **Edge Glow Color**: The default edge color is `(0.3, 0.6, 1.0)` (light blue), typical for AR interfaces. This can be customized via `edgeColorR/G/B`.

7. **Feather**: The feather parameter controls the width of the smooth transition between foreground and background. Larger values create softer edges but may cause halo artifacts.

8. **Testing**: Create a depth map with a clear foreground/background separation (e.g., a person against a wall). Verify the matte correctly isolates the person. Test with different `sliceNear`/`sliceFar` values to ensure the depth range is respected.

9. **Performance**: The effect is relatively fast. The main cost is texture uploads. If the sources are static, consider caching textures to avoid re-uploading identical frames.

10. **Future Work**: Could add a "despill" parameter to remove color spill from background onto foreground edges, a common issue with keying.

---

## Conclusion

The DepthPortalCompositeEffect provides a clean, depth-based method for isolating performers and compositing them onto arbitrary backgrounds. By leveraging depth data, it avoids the pitfalls of chroma keying (lighting constraints, color spills) and provides a natural, hardware-accelerated solution for augmented reality-style composites. With configurable depth ranges, foreground transforms, and optional edge effects, it's a versatile tool for VJ performances that need to place performers in virtual environments.

---
