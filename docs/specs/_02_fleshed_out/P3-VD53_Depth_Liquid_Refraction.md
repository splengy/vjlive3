# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD53_Depth_Liquid_Refraction.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD53 — DepthLiquidRefractionEffect

## Description

The DepthLiquidRefractionEffect creates depth-driven glass/water distortion by using the depth map as a 2D displacement field. Depth gradients—edges between near and far objects—create the strongest warping, producing caustic highlights around the performer's silhouette. The effect simulates looking through a refractive medium like water, glass, or a transparent material with liquid properties. It includes chromatic aberration (color fringing), animated ripples, frosted glass noise, and depth-proportional blur.

This effect is ideal for creating underwater scenes, glass distortion, heat haze, and other refractive phenomena. The depth-based displacement ensures that distortion is strongest at depth edges, creating natural-looking caustics around objects. It's perfect for VJ performances that need organic, fluid distortion effects.

## What This Module Does

- Uses depth map as a 2D displacement field
- Distorts image based on depth gradients
- Creates caustic highlights at depth edges
- Implements chromatic aberration (RGB channel separation)
- Adds animated ripple effects
- Supports frosted glass noise texture
- Applies depth-proportional blur
- Can invert depth for alternative effects
- GPU-accelerated fragment shader

## What This Module Does NOT Do

- Does NOT provide 3D ray tracing (2D screen-space only)
- Does NOT simulate volumetric refraction (surface-only)
- Does NOT include audio reactivity (may be added later)
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT handle multiple refraction layers (single pass)

---

## Detailed Behavior

### Refraction Pipeline

1. **Compute depth gradient**: Find edges in depth map:
   ```
   grad_x = dFdx(depth)
   grad_y = dFdy(depth)
   grad_mag = length(vec2(grad_x, grad_y))
   ```

2. **Generate displacement vector**: From depth gradient:
   ```
   displacement = vec2(grad_x, grad_y) * refraction_strength
   ```

3. **Apply chromatic aberration**: Offset RGB channels differently:
   ```
   r_offset = displacement * (1.0 + chromatic_spread)
   g_offset = displacement
   b_offset = displacement * (1.0 - chromatic_spread)
   ```

4. **Add animated ripples**: Time-based sinusoidal displacement:
   ```
   ripple = sin(uv * ripple_scale + time * ripple_speed) * ripple_strength
   displacement += ripple
   ```

5. **Apply frosted glass** (if enabled): Add noise-based distortion:
   ```
   noise = texture(noise_tex, uv).r
   displacement += (noise - 0.5) * frosted_strength
   ```

6. **Sample distorted coordinates**: Remap UV with displacement:
   ```
   uv_r = uv + r_offset
   uv_g = uv + g_offset
   uv_b = uv + b_offset
   ```

7. **Depth-proportional blur** (if enabled): Blur more at greater depths:
   ```
   blur_radius = depth * depth_blur_strength
   color = gaussian_blur(color, blur_radius)
   ```

8. **Edge glow** (optional): Add glow at depth edges:
   ```
   glow = grad_mag * edge_glow_strength
   color += glow_color * glow
   ```

9. **Final mix**: Blend with original:
   ```
   result = mix(original, color, u_mix)
   ```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `refractionStrength` | float | 5.0 | 0.0-10.0 | Overall strength of refraction distortion |
| `chromaticSpread` | float | 3.0 | 0.0-10.0 | RGB channel separation amount |
| `rippleSpeed` | float | 4.0 | 0.0-10.0 | Speed of animated ripples |
| `rippleScale` | float | 5.0 | 0.0-10.0 | Spatial scale of ripple pattern |
| `edgeGlow` | float | 4.0 | 0.0-10.0 | Intensity of caustic edge glow |
| `depthBlur` | float | 2.0 | 0.0-10.0 | Depth-proportional blur amount |
| `frostedGlass` | float | 0.0 | 0.0-10.0 | Frosted glass noise strength |
| `invertDepth` | float | 0.0 | 0.0-10.0 | Invert depth gradient (0=off, >0=on) |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class DepthLiquidRefractionEffect(Effect):
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
| **Output** | `np.ndarray` | Liquid refraction frame (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Latest depth frame
- `_depth_texture: int` — GL texture for depth data
- `_parameters: dict` — Refraction parameters
- `_shader: ShaderProgram` — Compiled shader
- `_noise_texture: int` — Noise texture for frosted glass (if enabled)
- `_previous_frame_texture: int` — For blur if needed

**Per-Frame:**
- Update depth data from source
- Upload depth texture
- Set shader uniforms (including time for ripples)
- Render refraction effect
- Return result

**Initialization:**
- Create depth texture (lazy)
- Create noise texture (if frostedGlass > 0)
- Compile shader
- Default parameters: refractionStrength=5.0, chromaticSpread=3.0, rippleSpeed=4.0, rippleScale=5.0, edgeGlow=4.0, depthBlur=2.0, frostedGlass=0.0, invertDepth=0.0

**Cleanup:**
- Delete depth texture
- Delete noise texture (if created)
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_RED, GL_UNSIGNED_BYTE | depth_frame size | Updated each frame |
| Noise texture (optional) | GL_TEXTURE_2D | GL_R8 | 256×256 (typical) | Init once |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Depth texture: 307,200 bytes
- Noise texture: 256×256×1 = 65,536 bytes (if used)
- Shader: ~20-40 KB
- Total: ~0.4 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | Use zero gradient (no distortion) | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and texture updates must occur on the thread with the OpenGL context. The depth texture is updated each frame, and the shader is used for rendering, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth texture upload: ~0.5-1 ms
- Shader execution (distortion + chromatic + ripples): ~3-6 ms
- Optional blur: +2-4 ms
- Total: ~3.5-11 ms on GPU (depending on options)

**Optimization Strategies:**
- Disable `depthBlur` if not needed (expensive)
- Reduce `frostedGlass` noise resolution
- Use simpler ripple pattern (fewer sin/cos calls)
- Lower resolution for depth texture
- Cache depth gradient if depth hasn't changed
- Use compute shader for parallel processing

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Refraction parameters configured (strength, chromatic, ripples, etc.)
- [ ] Optional effects configured (glow, blur, frosted)
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | Parameters can be set and clamped |
| `test_get_parameter` | Parameters can be retrieved |
| `test_depth_gradient` | Gradient computed correctly from depth |
| `test_refraction_strength` | Displacement magnitude controlled by strength |
| `test_chromatic_aberration` | RGB channels separate by different amounts |
| `test_ripple_animation` | Ripples animate over time |
| `test_edge_glow` | Glow appears at depth edges |
| `test_depth_blur` | Blur amount proportional to depth |
| `test_frosted_glass` | Noise adds additional distortion |
| `test_invert_depth` | Inverting depth reverses distortion direction |
| `test_process_frame_no_depth` | No distortion when depth missing |
| `test_process_frame_with_depth` | Distortion follows depth gradients |
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
- [ ] Git commit with `[Phase-3] P3-VD53: depth_liquid_refraction_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_liquid_refraction.py` — VJLive Original implementation
- `plugins/core/depth_liquid_refraction/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_liquid_refraction/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthLiquidRefractionEffect` allocates `glGenTextures` and must free them
- `assets/gists/depth_liquid_refraction.json` — Gist documentation

Design decisions inherited:
- Effect name: `depth_liquid_refraction`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for gradient-based displacement
- Parameters: `refractionStrength`, `chromaticSpread`, `rippleSpeed`, `rippleScale`, `edgeGlow`, `depthBlur`, `frostedGlass`, `invertDepth`
- Allocates GL resources: depth texture (and optionally noise texture)
- Shader implements depth-driven distortion with chromatic aberration, ripples, glow, blur
- Auto-wires to DepthDataBus (legacy feature)

---

## Notes for Implementers

1. **Depth Gradient as Displacement**: The core idea is to use depth gradient (spatial rate of change) as a displacement vector. Steeper gradients (depth edges) cause more distortion:
   ```glsl
   float depth = texture(depth_tex, uv).r;
   float dx = dFdx(depth);
   float dy = dFdy(depth);
   vec2 displacement = vec2(dx, dy) * refractionStrength * 0.01;
   ```

2. **Chromatic Aberration**: Apply different displacements to each color channel to simulate lens refraction:
   ```glsl
   vec2 offset_r = displacement * (1.0 + chromaticSpread * 0.1);
   vec2 offset_g = displacement;
   vec2 offset_b = displacement * (1.0 - chromaticSpread * 0.1);
   
   float r = texture(tex0, uv + offset_r).r;
   float g = texture(tex0, uv + offset_g).g;
   float b = texture(tex0, uv + offset_b).b;
   ```

3. **Animated Ripples**: Add time-varying sinusoidal displacement:
   ```glsl
   float ripple = sin(uv.x * rippleScale * 0.1 + time * rippleSpeed) *
                  cos(uv.y * rippleScale * 0.1 + time * rippleSpeed * 0.7);
   displacement += ripple * refractionStrength * 0.02;
   ```

4. **Edge Glow**: Highlight depth edges with additive glow:
   ```glsl
   float edge = length(vec2(dx, dy));
   vec3 glow = vec3(0.0, 0.8, 1.0) * edge * edgeGlow * 0.1;  // Cyan glow
   color += glow;
   ```

5. **Depth-Proportional Blur**: Blur more at greater depths (simulating depth of field):
   ```glsl
   float blur_radius = depth * depthBlur * 2.0;
   if (blur_radius > 0.5) {
       color = gaussian_blur(color, uv, blur_radius);
   }
   ```
   Note: Gaussian blur in shader can be expensive. Consider simpler box blur or pre-blurred mipmaps.

6. **Frosted Glass**: Add noise-based distortion:
   ```glsl
   if (frostedGlass > 0.0) {
       float noise = texture(noise_tex, uv * 2.0).r;
       displacement += (noise - 0.5) * frostedGlass * 0.02;
   }
   ```

7. **Invert Depth**: Option to invert depth gradient direction:
   ```glsl
   if (invertDepth > 0.0) {
       displacement = -displacement;
   }
   ```

8. **Shader Uniforms**:
   ```glsl
   uniform sampler2D tex0;        // Source frame
   uniform sampler2D depth_tex;   // Depth texture
   uniform sampler2D noise_tex;   // Noise texture (optional)
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float refractionStrength; // 0-10
   uniform float chromaticSpread;    // 0-10
   uniform float rippleSpeed;        // 0-10
   uniform float rippleScale;        // 0-10
   uniform float edgeGlow;           // 0-10
   uniform float depthBlur;          // 0-10
   uniform float frostedGlass;       // 0-10
   uniform float invertDepth;        // 0-10 (0=off, >0=on)
   ```

9. **Parameter Mapping**: Map 0-10 UI ranges to shader values:
   - `refractionStrength`: 0-10 → multiply by 0.01
   - `chromaticSpread`: 0-10 → multiply by 0.1 (offset factor)
   - `rippleSpeed`: 0-10 → Hz or multiplier
   - `rippleScale`: 0-10 → spatial frequency multiplier
   - `edgeGlow`: 0-10 → multiply by 0.1
   - `depthBlur`: 0-10 → blur radius in pixels (max ~20)
   - `frostedGlass`: 0-10 → distortion strength
   - `invertDepth`: 0-10 → boolean (0 = false, >0 = true)

10. **Noise Texture**: For frosted glass, generate a small noise texture (e.g., 256×256) with Perlin or simplex noise. Upload once and reuse.

11. **Depth Gradient Scaling**: The raw depth gradient may need scaling based on depth resolution. Experiment with multipliers (e.g., 0.01) to get usable displacement.

12. **Performance**: The biggest cost is the optional blur. If `depthBlur` is 0, the shader is relatively fast. With blur, consider:
    - Using separable blur (horizontal + vertical passes)
    - Using lower resolution for blur
    - Using mipmap-based blur (cheaper but lower quality)

13. **PRESETS**:
    ```python
    PRESETS = {
        "gentle_water": {
            "refractionStrength": 3.0, "chromaticSpread": 2.0,
            "rippleSpeed": 2.0, "rippleScale": 3.0,
            "edgeGlow": 2.0, "depthBlur": 1.0,
            "frostedGlass": 0.0, "invertDepth": 0.0,
        },
        "thick_glass": {
            "refractionStrength": 7.0, "chromaticSpread": 5.0,
            "rippleSpeed": 1.0, "rippleScale": 2.0,
            "edgeGlow": 6.0, "depthBlur": 3.0,
            "frostedGlass": 0.0, "invertDepth": 0.0,
        },
        "frosted_pane": {
            "refractionStrength": 4.0, "chromaticSpread": 1.0,
            "rippleSpeed": 0.0, "rippleScale": 0.0,
            "edgeGlow": 3.0, "depthBlur": 0.0,
            "frostedGlass": 8.0, "invertDepth": 0.0,
        },
        "underwater": {
            "refractionStrength": 6.0, "chromaticSpread": 4.0,
            "rippleSpeed": 5.0, "rippleScale": 8.0,
            "edgeGlow": 5.0, "depthBlur": 4.0,
            "frostedGlass": 0.0, "invertDepth": 0.0,
        },
    }
    ```

14. **Testing**: Create a depth image with clear edges (e.g., a cube). Verify:
    - Distortion is strongest at depth edges
    - Chromatic aberration creates color fringing
    - Ripples animate smoothly
    - Edge glow highlights depth boundaries
    - Depth blur increases with depth
    - Frosted glass adds noise-based warping
    - Invert depth reverses distortion direction

15. **Future Extensions**:
    - Add audio reactivity to ripple speed/strength
    - Add multiple distortion layers
    - Add custom noise patterns (bubbles, waves)
    - Add depth-based refraction index variation
    - Add volumetric blur (not just depth-proportional)

---
-

## References

- Refraction: https://en.wikipedia.org/wiki/Refraction
- Chromatic aberration: https://en.wikipedia.org/wiki/Chromatic_aberration
- Caustics: https://en.wikipedia.org/wiki/Caustic_(optics)
- Depth of field: https://en.wikipedia.org/wiki/Depth_of_field
- VJLive legacy: `plugins/vdepth/depth_liquid_refraction.py`

---

## Implementation Tips

1. **Full Shader**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;        // Source image
   uniform sampler2D depth_tex;   // Depth texture
   uniform sampler2D noise_tex;   // Noise texture (optional)
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float refractionStrength; // 0-10
   uniform float chromaticSpread;    // 0-10
   uniform float rippleSpeed;        // 0-10
   uniform float rippleScale;        // 0-10
   uniform float edgeGlow;           // 0-10
   uniform float depthBlur;          // 0-10
   uniform float frostedGlass;       // 0-10
   uniform float invertDepth;        // 0-10 (0=off)
   
   // Simple Gaussian blur (separable would be better)
   vec3 gaussian_blur(sampler2D tex, vec2 uv, float radius) {
       vec2 texel = 1.0 / resolution;
       vec3 color = vec3(0.0);
       float total = 0.0;
       for (float x = -2.0; x <= 2.0; x += 1.0) {
           for (float y = -2.0; y <= 2.0; y += 1.0) {
               float weight = exp(-(x*x + y*y) / (2.0 * radius * radius));
               color += texture(tex, uv + vec2(x, y) * texel * radius).rgb * weight;
               total += weight;
           }
       }
       return color / total;
   }
   
   void main() {
       vec4 original = texture(tex0, uv);
       float depth = texture(depth_tex, uv).r;
       
       // Compute depth gradient
       float dx = dFdx(depth);
       float dy = dFdy(depth);
       vec2 grad = vec2(dx, dy);
       
       // Invert if requested
       if (invertDepth > 0.0) {
           grad = -grad;
       }
       
       // Base displacement from gradient
       vec2 displacement = grad * refractionStrength * 0.01;
       
       // Add ripples
       if (rippleSpeed > 0.0 && rippleScale > 0.0) {
           float ripple = sin(uv.x * rippleScale * 0.1 + time * rippleSpeed) *
                          cos(uv.y * rippleScale * 0.1 + time * rippleSpeed * 0.7);
           displacement += ripple * refractionStrength * 0.02;
       }
       
       // Add frosted glass noise
       if (frostedGlass > 0.0) {
           float noise = texture(noise_tex, uv * 2.0).r;
           displacement += (noise - 0.5) * frostedGlass * 0.02;
       }
       
       // Chromatic aberration: different offsets per channel
       vec2 offset_r = displacement * (1.0 + chromaticSpread * 0.1);
       vec2 offset_g = displacement;
       vec2 offset_b = displacement * (1.0 - chromaticSpread * 0.1);
       
       // Sample with offsets
       float r = texture(tex0, uv + offset_r).r;
       float g = texture(tex0, uv + offset_g).g;
       float b = texture(tex0, uv + offset_b).b;
       vec3 color = vec3(r, g, b);
       
       // Apply depth-proportional blur
       if (depthBlur > 0.0) {
           float blur_radius = depth * depthBlur * 2.0;
           if (blur_radius > 0.5) {
               color = gaussian_blur(tex0, uv, blur_radius);
           }
       }
       
       // Edge glow
       if (edgeGlow > 0.0) {
           float edge = length(grad);
           vec3 glow_color = vec3(0.0, 0.8, 1.0);  // Cyan
           color += glow_color * edge * edgeGlow * 0.1;
       }
       
       // Final mix
       color = clamp(color, 0.0, 1.0);
       vec3 result = mix(original.rgb, color, u_mix);
       
       fragColor = vec4(result, 1.0);
   }
   ```

2. **Python Implementation**:
   ```python
   class DepthLiquidRefractionEffect(Effect):
       def __init__(self):
           super().__init__("depth_liquid_refraction", DEPTH_LIQUID_REFRACTION_FRAGMENT)
           self.depth_source = None
           self.depth_frame = None
           self.depth_texture = 0
           self.parameters = {
               'refractionStrength': 5.0,
               'chromaticSpread': 3.0,
               'rippleSpeed': 4.0,
               'rippleScale': 5.0,
               'edgeGlow': 4.0,
               'depthBlur': 2.0,
               'frostedGlass': 0.0,
               'invertDepth': 0.0,
           }
           self.shader = None
           self.noise_texture = 0
           
       def _ensure_resources(self, width, height):
           if self.depth_texture == 0:
               self.depth_texture = glGenTextures(1)
               glBindTexture(GL_TEXTURE_2D, self.depth_texture)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
               
           if self.noise_texture == 0 and self.parameters['frostedGlass'] > 0:
               # Generate noise
               noise = generate_perlin_noise_2d((256, 256), res=(8, 8))
               noise_uint8 = (noise * 255).astype(np.uint8)
               self.noise_texture = glGenTextures(1)
               glBindTexture(GL_TEXTURE_2D, self.noise_texture)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
               glTexImage2D(GL_TEXTURE_2D, 0, GL_R8, 256, 256, 0, GL_RED, GL_UNSIGNED_BYTE, noise_uint8)
               
           if self.shader is None:
               self.shader = ShaderProgram(vertex_src, fragment_src)
   ```

3. **Parameter Clamping**:
   ```python
   def set_parameter(self, name, value):
       if name == 'refractionStrength':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'chromaticSpread':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'rippleSpeed':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'rippleScale':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'edgeGlow':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'depthBlur':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'frostedGlass':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'invertDepth':
           self.parameters[name] = max(0.0, min(10.0, value))
   ```

4. **Depth Texture Upload**: Standard procedure.

5. **Blur Implementation**: The Gaussian blur in the shader above is a simple 5×5 kernel. For better performance, use separable blur (two passes: horizontal then vertical) or use mipmaps.

6. **Auto-wiring to DepthDataBus**: The legacy mentions auto-wiring. If your system has a DepthDataBus, the effect should automatically connect to it if no explicit depth source is set. Document this behavior.

7. **Testing Strategy**: Test each parameter individually:
   - Set `refractionStrength` to 0 → no distortion
   - Increase `chromaticSpread` → color fringing appears
   - Animate `rippleSpeed` → ripples move
   - Increase `edgeGlow` → edges get brighter
   - Increase `depthBlur` → deeper areas blur more
   - Set `frostedGlass` > 0 → noise distortion appears

8. **Performance Tuning**: The effect can be heavy with blur enabled. Consider:
   - Making blur optional (only if `depthBlur > 0`)
   - Using a simpler blur (box or bilateral)
   - Downsampling for blur pass
   - Using compute shader for parallel blur

---

## Conclusion

The DepthLiquidRefractionEffect creates realistic, depth-driven distortion that simulates looking through refractive media like water or glass. By using depth gradients as displacement fields, it produces natural-looking caustics and chromatic aberration that respond to scene geometry. With additional features like animated ripples, frosted glass, and depth-proportional blur, it's a versatile tool for creating organic, fluid distortion effects in VJ performances.

---
