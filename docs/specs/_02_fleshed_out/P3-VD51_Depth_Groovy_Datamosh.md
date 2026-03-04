# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD51_Depth_Groovy_Datamosh.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD51 — DepthGroovyDatamoshEffect

## Description

The DepthGroovyDatamoshEffect is a maximalist psychedelic depth effect that combines multiple visual techniques into one overwhelming, "everything turned up to 11" experience. It integrates rainbow hue cycling, kaleidoscopic mirroring, spiral feedback vortices, breathing depth layers, pixel-sort displacement, organic melt warping, recursive zoom, block datamosh, and neon color saturation. All these effects are modulated by depth data, creating a trippy, depth-reactive visual experience.

This effect is designed for VJ performances that need maximum visual impact. It's not subtle—it's a complete sensory overload that uses depth to control the intensity and distribution of multiple simultaneous effects. The effect is highly configurable, allowing individual components to be tuned or disabled.

## What This Module Does

- Applies multiple psychedelic visual effects simultaneously
- Uses depth data to modulate effect intensity and distribution
- Implements rainbow hue cycling with depth-based variation
- Creates kaleidoscopic mirroring patterns
- Generates spiral feedback vortices with depth gating
- Adds breathing depth layers (pulsing based on depth)
- Performs pixel-sort displacement along depth gradients
- Applies organic melt warping
- Implements recursive zoom effects
- Adds block datamosh artifacts
- Boosts color saturation to neon levels
- GPU-accelerated fragment shader

## What This Module Does NOT Do

- Does NOT provide individual effects as separate modules (all-in-one)
- Does NOT offer CPU fallback (GPU required)
- Does NOT implement true 3D rendering (2D screen-space)
- Does NOT store persistent state across sessions
- Does NOT include audio reactivity (may be added later)
- Does NOT provide preset management (hardcoded only)

---

## Detailed Behavior

### Effect Pipeline

The effect applies multiple stages in sequence:

1. **Depth Sampling**: Get depth value `d` from depth texture
2. **Rainbow Hue Cycling**: Rotate hue based on depth and time
3. **Kaleidoscopic Mirroring**: Mirror UV coordinates based on depth
4. **Spiral Feedback Vortices**: Create swirling feedback loops
5. **Breathing Depth Layers**: Pulsing effect synchronized with depth
6. **Pixel-Sort Displacement**: Sort pixels along depth gradient
7. **Organic Melt Warping**: Warp image with organic noise
8. **Recursive Zoom**: Zoom with feedback
9. **Block Datamosh**: Create blocky artifacts
10. **Neon Saturation**: Boost saturation to extreme levels
11. **Strobe Flash**: Optional depth-phased strobe
12. **Final Mix**: Blend with original

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `rainbowIntensity` | float | 5.0 | 0.0-10.0 | Strength of rainbow hue cycling |
| `kaleidoscopeSegments` | float | 6.0 | 3.0-12.0 | Number of kaleidoscope segments |
| `spiralStrength` | float | 4.0 | 0.0-10.0 | Intensity of spiral feedback |
| `breathSpeed` | float | 2.0 | 0.0-10.0 | Speed of breathing layers |
| `breathDepth` | float | 3.0 | 0.0-10.0 | Depth influence on breathing |
| `pixelSortAmount` | float | 3.0 | 0.0-10.0 | Strength of pixel-sort displacement |
| `meltStrength` | float | 4.0 | 0.0-10.0 | Organic melt warping intensity |
| `zoomFactor` | float | 1.02 | 1.0-1.1 | Recursive zoom per frame |
| `blockSize` | float | 8.0 | 2.0-20.0 | Size of datamosh blocks |
| `blockIntensity` | float | 5.0 | 0.0-10.0 | Strength of block datamosh |
| `saturationBoost` | float | 3.0 | 0.0-10.0 | Neon saturation multiplier |
| `strobeFlash` | float | 0.0 | 0.0-10.0 | Strobe frequency (0=off) |
| `depthInfluence` | float | 5.0 | 0.0-10.0 | How much depth modulates effects |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class DepthGroovyDatamoshEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| **Output** | `np.ndarray` | Groovy datamosh frame (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Latest depth frame
- `_depth_texture: int` — GL texture for depth data
- `_parameters: dict` — Groovy parameters
- `_shader: ShaderProgram` — Compiled shader
- `_feedback_texture: int` — For spiral feedback and zoom
- `_previous_frame_texture: int` — For temporal effects
- `_framebuffer: int` — For ping-pong rendering

**Per-Frame:**
- Update depth data from source
- Upload depth texture
- Bind feedback textures
- Render through full shader pipeline
- Store output in feedback texture for next frame
- Return final result

**Initialization:**
- Create depth texture (lazy)
- Create feedback textures (ping-pong pair)
- Create framebuffer
- Compile shader
- Default parameters (from legacy)

**Cleanup:**
- Delete depth texture
- Delete feedback textures
- Delete framebuffer
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_RED, GL_UNSIGNED_BYTE | depth_frame size | Updated each frame |
| Feedback texture | GL_TEXTURE_2D | GL_RGBA8 | frame size | Updated each frame |
| Previous frame texture | GL_TEXTURE_2D | GL_RGBA8 | frame size | Updated each frame |
| Framebuffer | GL_FRAMEBUFFER | N/A | frame size | Persistent |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Depth texture: 307,200 bytes
- Feedback textures: 2 × 921,600 = 1,843,200 bytes
- Framebuffer: negligible
- Shader: ~50-100 KB (complex)
- Total: ~2.2 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | Use uniform depth (0.5) | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Feedback texture creation fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and texture updates must occur on the thread with the OpenGL context. Multiple textures are updated each frame, and the complex shader uses feedback loops, so concurrent `process_frame()` calls will cause race conditions and visual artifacts. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth texture upload: ~0.5-1 ms
- Shader execution (complex multi-stage): ~8-15 ms
- Texture copies for feedback: ~1-2 ms
- Total: ~9.5-18 ms on GPU

**Optimization Strategies:**
- Reduce resolution of feedback textures
- Disable expensive stages via parameters (set intensity=0)
- Use simpler shader branches for disabled effects
- Reduce `blockSize` for faster datamosh
- Lower `kaleidoscopeSegments` for fewer mirrors
- Use compute shader for parallel processing
- Cache depth texture if depth hasn't changed

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Groovy parameters configured (individual effect intensities)
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_rainbow_hue_cycling` | Hue rotates over time and with depth |
| `test_kaleidoscope` | Mirroring creates symmetric patterns |
| `test_spiral_feedback` | Spiral vortices appear with feedback |
| `test_breathing_layers` | Depth layers pulse with time |
| `test_pixel_sort` | Pixels displaced along depth gradient |
| `test_melt_warping` | Organic warping distorts image |
| `test_recursive_zoom` | Zoom effect creates tunnel vision |
| `test_block_datamosh` | Blocky artifacts appear |
| `test_neon_saturation` | Colors become highly saturated |
| `test_strobe_flash` | Strobe flashes at configured frequency |
| `test_depth_influence` | Depth modulates all effects |
| `test_process_frame_no_depth` | Falls back to uniform depth |
| `test_process_frame_with_depth` | Depth modulates effects correctly |
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
- [ ] Git commit with `[Phase-3] P3-VD51: depth_groovy_datamosh_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_groovy_datamosh.py` — VJLive Original implementation
- `plugins/core/depth_groovy_datamosh/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_groovy_datamosh/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthGroovyDatamoshEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_groovy_datamosh`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for depth modulation
- Parameters: `rainbowIntensity`, `kaleidoscopeSegments`, `spiralStrength`, `breathSpeed`, `breathDepth`, `pixelSortAmount`, `meltStrength`, `zoomFactor`, `blockSize`, `blockIntensity`, `saturationBoost`, `strobeFlash`, `depthInfluence`
- Allocates GL resources: depth texture, feedback textures, framebuffer
- Shader implements all effects in one massive pipeline
- Maximalist design: all effects combined

---

## Notes for Implementers

1. **Shader Complexity**: This is a massive shader combining many effects. Consider:
   - Using `#define` flags to enable/disable effects at compile time
   - Branching based on intensity parameters (if intensity=0, skip stage)
   - Splitting into multiple passes if too heavy
   - Optimizing by precomputing common terms

2. **Effect Stages**: The shader should be organized into logical stages:
   ```glsl
   // Stage 1: Depth-based UV modification
   vec2 uv = base_uv;
   uv = apply_kaleidoscope(uv, depth);
   uv = apply_spiral(uv, depth, time);
   
   // Stage 2: Sample and modify color
   vec4 color = texture(tex0, uv);
   color.rgb = apply_hue_cycle(color.rgb, depth, time);
   color.rgb = apply_melt_warp(color.rgb, uv, depth);
   
   // Stage 3: Feedback and zoom
   vec4 feedback = texture(feedback_tex, uv);
   color = apply_zoom_feedback(color, feedback, depth);
   
   // Stage 4: Pixel sort and block datamosh
   color.rgb = apply_pixel_sort(color.rgb, depth);
   color.rgb = apply_block_datamosh(color.rgb, uv, depth);
   
   // Stage 5: Saturation and strobe
   color.rgb = boost_saturation(color.rgb);
   color.rgb = apply_strobe(color.rgb, time);
   
   // Stage 6: Breathing depth layers
   color.rgb = apply_breathing_layers(color.rgb, depth, time);
   
   // Stage 7: Final mix
   fragColor = mix(original, color, u_mix);
   ```

3. **Rainbow Hue Cycling**:
   ```glsl
   vec3 apply_hue_cycle(vec3 color, float depth, float time) {
       vec3 hsv = rgb2hsv(color);
       float hue_shift = time * 0.1 + depth * rainbowIntensity * 0.1;
       hsv.x = fract(hsv.x + hue_shift);
       return hsv2rgb(hsv);
   }
   ```

4. **Kaleidoscopic Mirroring**:
   ```glsl
   vec2 apply_kaleidoscope(vec2 uv, float depth) {
       float segments = kaleidoscopeSegments;
       float angle = atan(uv.y - 0.5, uv.x - 0.5);
       float radius = length(uv - 0.5);
       angle = mod(angle, 6.28318 / segments);
       if (mod(floor(angle * segments / 6.28318), 2.0) == 1.0) {
           angle = -angle;  // Mirror alternate segments
       }
       return vec2(0.5 + cos(angle)*radius, 0.5 + sin(angle)*radius);
   }
   ```

5. **Spiral Feedback Vortices**:
   ```glsl
   vec2 apply_spiral(vec2 uv, float depth, float time) {
       vec2 center = vec2(0.5);
       vec2 pos = uv - center;
       float angle = atan(pos.y, pos.x);
       float radius = length(pos);
       angle += time * spiralStrength * 0.1 + depth * 0.5;
       return center + vec2(cos(angle), sin(angle)) * radius;
   }
   ```

6. **Breathing Depth Layers**:
   ```glsl
   vec3 apply_breathing_layers(vec3 color, float depth, float time) {
       float breath = sin(time * breathSpeed + depth * breathDepth);
       breath = breath * 0.5 + 0.5;  // 0-1
       return color * (0.8 + breath * 0.4);  // 0.8-1.2x intensity
   }
   ```

7. **Pixel-Sort Displacement**:
   ```glsl
   vec3 apply_pixel_sort(vec3 color, float depth) {
       // Sort pixels along depth gradient (simplified)
       float sort_dir = depth > 0.5 ? 1.0 : -1.0;
       vec2 offset = vec2(sort_dir * pixelSortAmount * 0.01, 0.0);
       vec3 sorted = texture(tex0, uv + offset).rgb;
       return mix(color, sorted, depth);
   }
   ```

8. **Organic Melt Warping**:
   ```glsl
   vec3 apply_melt_warp(vec3 color, vec2 uv, float depth) {
       vec2 noise_uv = uv + time * 0.05;
       float noise = texture(noise_tex, noise_uv).r;
       vec2 warp_offset = vec2(noise - 0.5) * meltStrength * 0.02;
       return texture(tex0, uv + warp_offset).rgb;
   }
   ```

9. **Recursive Zoom**:
   ```glsl
   vec4 apply_zoom_feedback(vec4 current, vec4 previous, float depth) {
       // Zoom out previous frame
       vec2 center = vec2(0.5);
       vec2 uv_scaled = (uv - center) * zoomFactor + center;
       vec4 zoomed = texture(feedback_tex, uv_scaled);
       // Mix with current
       return mix(current, zoomed, depth * 0.5);
   }
   ```

10. **Block Datamosh**:
    ```glsl
    vec3 apply_block_datamosh(vec3 color, vec2 uv, float depth) {
        // Quantize UV to block grid
        vec2 block_uv = floor(uv * resolution / blockSize) * blockSize / resolution;
        vec3 block_color = texture(tex0, block_uv).rgb;
        // Shift blocks based on depth
        vec2 shift = vec2(depth - 0.5) * blockIntensity * 0.01;
        return mix(color, block_color + shift, depth);
    }
    ```

11. **Neon Saturation**:
    ```glsl
    vec3 boost_saturation(vec3 color) {
        vec3 hsv = rgb2hsv(color);
        hsv.y = min(1.0, hsv.y * saturationBoost);
        return hsv2rgb(hsv);
    }
    ```

12. **Strobe Flash**:
    ```glsl
    vec3 apply_strobe(vec3 color, float time) {
        if (strobe_flash > 0.0) {
            float flash = pow(max(0.0, sin(time * strobe_flash * 8.0)), 8.0);
            flash *= pow(max(0.0, sin(time * strobe_flash * 8.0 + depth * 3.14)), 4.0);
            color += vec3(flash * 0.5);
        }
        return color;
    }
    ```

13. **Noise Texture**: For melt warping, create a noise texture (Perlin or simplex) at initialization.

14. **Feedback Loop**: Use ping-pong textures for feedback effects (spiral, zoom):
    ```python
    # Two textures: fb_A and fb_B
    # Read from current, render to other, swap
    ```

15. **Parameter Ranges**: Map 0-10 UI ranges to shader values:
    - `rainbowIntensity`: 0-10 (multiplier)
    - `kaleidoscopeSegments`: 3-12 (integer or float)
    - `spiralStrength`: 0-10 (multiplier)
    - `breathSpeed`: 0-10 (Hz or multiplier)
    - `breathDepth`: 0-10 (multiplier)
    - `pixelSortAmount`: 0-10 (pixel offset)
    - `meltStrength`: 0-10 (warp amplitude)
    - `zoomFactor`: 1.0-1.1 (1.0 = no zoom, >1 = zoom out)
    - `blockSize`: 2-20 (pixels)
    - `blockIntensity`: 0-10 (offset multiplier)
    - `saturationBoost`: 0-10 (maps to 0-10x, but clamp to reasonable)
    - `strobeFlash`: 0-10 (Hz, 0=off)
    - `depthInfluence`: 0-10 (multiplier for depth modulation)

16. **Performance**: This is a heavy effect. Consider:
    - Running at lower resolution and upscaling
    - Disabling stages with intensity=0 via `#define` or branching
    - Using simpler noise for melt
    - Reducing feedback texture resolution
    - Profiling to find bottlenecks

17. **Testing**: Test each stage individually by setting other intensities to 0. Verify:
    - Rainbow hue cycles over time
    - Kaleidoscope creates symmetric patterns
    - Spiral creates rotational motion
    - Breathing layers pulse
    - Pixel sort displaces pixels
    - Melt warps organically
    - Zoom creates tunnel effect
    - Block datamosh creates pixelated artifacts
    - Saturation boosts colors
    - Strobe flashes at correct frequency
    - Depth modulates all effects

18. **Future Extensions**:
    - Add audio reactivity
    - Add preset system (e.g., "mild_groove", "full_psychedelia")
    - Add ability to disable individual effects
    - Add depth-based effect selection (different effects at different depths)
    - Add performance metrics overlay

---
-

## References

- Kaleidoscope: https://en.wikipedia.org/wiki/Kaleidoscope
- Feedback: https://en.wikipedia.org/wiki/Feedback
- Pixel sorting: https://en.wikipedia.org/wiki/Glitch_art#Pixel_sorting
- Datamosh: https://en.wikipedia.org/wiki/Datamosh
- HSV color space: https://en.wikipedia.org/wiki/HSL_and_HSV
- VJLive legacy: `plugins/vdepth/depth_groovy_datamosh.py`

---

## Implementation Tips

1. **Full Shader Skeleton**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;          // Original frame
   uniform sampler2D depth_tex;     // Depth texture
   uniform sampler2D feedback_tex;  // Feedback texture
   uniform sampler2D noise_tex;     // Noise texture (for melt)
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   uniform float delta_time;
   
   // Parameters (0-10 range)
   uniform float rainbowIntensity;
   uniform float kaleidoscopeSegments;
   uniform float spiralStrength;
   uniform float breathSpeed;
   uniform float breathDepth;
   uniform float pixelSortAmount;
   uniform float meltStrength;
   uniform float zoomFactor;
   uniform float blockSize;
   uniform float blockIntensity;
   uniform float saturationBoost;
   uniform float strobeFlash;
   uniform float depthInfluence;
   
   // HSV conversion functions
   vec3 rgb2hsv(vec3 c) { ... }
   vec3 hsv2rgb(vec3 c) { ... }
   
   // Effect stages
   vec2 apply_kaleidoscope(vec2 uv, float depth) { ... }
   vec2 apply_spiral(vec2 uv, float depth, float time) { ... }
   vec3 apply_hue_cycle(vec3 color, float depth, float time) { ... }
   vec3 apply_breathing_layers(vec3 color, float depth, float time) { ... }
   vec3 apply_pixel_sort(vec3 color, float depth) { ... }
   vec3 apply_melt_warp(vec3 color, vec2 uv, float depth) { ... }
   vec4 apply_zoom_feedback(vec4 current, vec4 previous, float depth) { ... }
   vec3 apply_block_datamosh(vec3 color, vec2 uv, float depth) { ... }
   vec3 boost_saturation(vec3 color) { ... }
   vec3 apply_strobe(vec3 color, float time, float depth) { ... }
   
   void main() {
       vec4 original = texture(tex0, uv);
       float depth = texture(depth_tex, uv).r;
       
       // Apply depth influence
       float depth_mod = depth * depthInfluence * 0.1;
       
       // Stage 1: UV modification
       vec2 uv_mod = uv;
       if (kaleidoscopeSegments > 0.0) {
           uv_mod = apply_kaleidoscope(uv_mod, depth);
       }
       if (spiralStrength > 0.0) {
           uv_mod = apply_spiral(uv_mod, depth, time);
       }
       
       // Stage 2: Sample and modify color
       vec4 color = texture(tex0, uv_mod);
       
       if (rainbowIntensity > 0.0) {
           color.rgb = apply_hue_cycle(color.rgb, depth, time);
       }
       
       if (meltStrength > 0.0) {
           color.rgb = apply_melt_warp(color.rgb, uv, depth);
       }
       
       // Stage 3: Feedback and zoom
       vec4 feedback = texture(feedback_tex, uv);
       if (zoomFactor > 1.0 || spiralStrength > 0.0) {
           color = apply_zoom_feedback(color, feedback, depth);
       }
       
       // Stage 4: Pixel sort and block datamosh
       if (pixelSortAmount > 0.0) {
           color.rgb = apply_pixel_sort(color.rgb, depth);
       }
       if (blockIntensity > 0.0) {
           color.rgb = apply_block_datamosh(color.rgb, uv, depth);
       }
       
       // Stage 5: Saturation
       if (saturationBoost > 0.0) {
           color.rgb = boost_saturation(color.rgb);
       }
       
       // Stage 6: Strobe
       if (strobeFlash > 0.0) {
           color.rgb = apply_strobe(color.rgb, time, depth);
       }
       
       // Stage 7: Breathing layers
       if (breathSpeed > 0.0) {
           color.rgb = apply_breathing_layers(color.rgb, depth, time);
       }
       
       // Final mix
       fragColor = mix(original, color, u_mix);
   }
   ```

2. **Python Setup**:
   ```python
   def __init__(self):
       super().__init__("depth_groovy_datamosh", DEPTH_GROOVY_FRAGMENT)
       self.depth_source = None
       self.depth_frame = None
       self.depth_texture = 0
       self.parameters = {
           'rainbowIntensity': 5.0,
           'kaleidoscopeSegments': 6.0,
           'spiralStrength': 4.0,
           'breathSpeed': 2.0,
           'breathDepth': 3.0,
           'pixelSortAmount': 3.0,
           'meltStrength': 4.0,
           'zoomFactor': 1.02,
           'blockSize': 8.0,
           'blockIntensity': 5.0,
           'saturationBoost': 3.0,
           'strobeFlash': 0.0,
           'depthInfluence': 5.0,
       }
       self.shader = None
       self.feedback_tex = 0
       self.noise_tex = 0
       self.fbo = 0
       self.current_fb = 0
       
   def _ensure_resources(self, width, height):
       # Create feedback textures (ping-pong)
       if self.feedback_tex == 0:
           self.feedback_tex = glGenTextures(2)
           self.fb_A, self.fb_B = self.feedback_tex
           for tex in [self.fb_A, self.fb_B]:
               glBindTexture(GL_TEXTURE_2D, tex)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
               glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
           
           self.fbo = glGenFramebuffers(1)
           
       if self.noise_tex == 0:
           # Generate noise texture
           noise = generate_perlin_noise_2d((256, 256), res=(8, 8))
           noise_uint8 = (noise * 255).astype(np.uint8)
           self.noise_tex = glGenTextures(1)
           glBindTexture(GL_TEXTURE_2D, self.noise_tex)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
           glTexImage2D(GL_TEXTURE_2D, 0, GL_R8, 256, 256, 0, GL_RED, GL_UNSIGNED_BYTE, noise_uint8)
           
       if self.shader is None:
           self.shader = ShaderProgram(vertex_src, fragment_src)
   ```

3. **Process Frame**:
   ```python
   def process_frame(self, frame):
       h, w = frame.shape[:2]
       self._ensure_resources(w, h)
       
       # Upload depth
       self._upload_depth_texture()
       
       # Determine ping-pong
       read_tex = self.fb_A if self.current_fb == 0 else self.fb_B
       write_tex = self.fb_B if self.current_fb == 0 else self.fb_A
       
       # Render to framebuffer
       glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
       glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, write_tex, 0)
       
       self.shader.use()
       self._apply_uniforms(time, (w, h))
       
       # Bind textures
       glActiveTexture(GL_TEXTURE0)
       glBindTexture(GL_TEXTURE_2D, frame_tex)
       self.shader.set_uniform("tex0", 0)
       
       glActiveTexture(GL_TEXTURE1)
       glBindTexture(GL_TEXTURE_2D, self.depth_texture)
       self.shader.set_uniform("depth_tex", 1)
       
       glActiveTexture(GL_TEXTURE2)
       glBindTexture(GL_TEXTURE_2D, read_tex)
       self.shader.set_uniform("feedback_tex", 2)
       
       glActiveTexture(GL_TEXTURE3)
       glBindTexture(GL_TEXTURE_2D, self.noise_tex)
       self.shader.set_uniform("noise_tex", 3)
       
       # Draw fullscreen quad
       draw_fullscreen_quad()
       
       glBindFramebuffer(GL_FRAMEBUFFER, 0)
       
       # Read result
       result = glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE)
       
       # Swap
       self.current_fb = 1 - self.current_fb
       
       return result
   ```

4. **Parameter Clamping**:
   ```python
   def set_parameter(self, name, value):
       if name == 'rainbowIntensity':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'kaleidoscopeSegments':
           self.parameters[name] = max(3.0, min(12.0, value))
       elif name == 'spiralStrength':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'breathSpeed':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'breathDepth':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'pixelSortAmount':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'meltStrength':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'zoomFactor':
           self.parameters[name] = max(1.0, min(1.1, value))
       elif name == 'blockSize':
           self.parameters[name] = max(2.0, min(20.0, value))
       elif name == 'blockIntensity':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'saturationBoost':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'strobeFlash':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'depthInfluence':
           self.parameters[name] = max(0.0, min(10.0, value))
   ```

5. **PRESETS**: The legacy likely has presets. Define a few:
   ```python
   PRESETS = {
       "mild_groove": {
           "rainbowIntensity": 2.0, "kaleidoscopeSegments": 4.0, "spiralStrength": 2.0,
           "breathSpeed": 1.0, "breathDepth": 2.0, "pixelSortAmount": 1.0,
           "meltStrength": 2.0, "zoomFactor": 1.01, "blockSize": 12.0,
           "blockIntensity": 2.0, "saturationBoost": 2.0, "strobeFlash": 0.0,
           "depthInfluence": 3.0,
       },
       "full_psychedelia": {
           "rainbowIntensity": 8.0, "kaleidoscopeSegments": 8.0, "spiralStrength": 7.0,
           "breathSpeed": 5.0, "breathDepth": 6.0, "pixelSortAmount": 6.0,
           "meltStrength": 7.0, "zoomFactor": 1.05, "blockSize": 4.0,
           "blockIntensity": 8.0, "saturationBoost": 8.0, "strobeFlash": 5.0,
           "depthInfluence": 8.0,
       },
   }
   ```

6. **Shader Optimization**: The shader will be huge. Use:
   - Early exits: `if (rainbowIntensity <= 0.0) { /* skip */ }`
   - Precompute common terms outside branches
   - Use `const` where possible
   - Minimize texture fetches (cache results)

7. **Testing Strategy**: Test each effect in isolation by zeroing others. Then test combinations.

8. **Documentation**: Since this is a maximalist effect, document each stage clearly in the shader code with comments.

---

## Conclusion

The DepthGroovyDatamoshEffect is the ultimate psychedelic depth effect, combining a dozen visual techniques into one overwhelming experience. It uses depth data to modulate every aspect of the effect, creating trippy, depth-reactive visuals that are perfect for high-energy VJ performances. While complex and computationally intensive, it provides unparalleled visual impact when you need to "turn it up to 11."

---
