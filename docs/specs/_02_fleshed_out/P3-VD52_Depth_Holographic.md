# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD52_Depth_Holographic.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD52 — DepthHolographicIridescenceEffect

## Description

The DepthHolographicIridescenceEffect simulates holographic and iridescent materials using physically-inspired thin-film interference and diffraction grating models. Depth gradients from the depth camera approximate surface normals, which are used to compute Fresnel effects, iridescence color shifts, and holographic shimmer. The effect creates rainbow-colored, angle-dependent reflections that mimic real-world holographic materials and soap bubbles.

This effect is ideal for creating futuristic, sci-fi visuals with rainbow sheens that shift as the camera or objects move. It's perfect for VJ performances that need ethereal, otherworldly aesthetics. The effect combines multiple optical phenomena: thin-film interference (like soap bubbles), diffraction gratings (like holographic stickers), and Fresnel reflections (angle-dependent brightness).

## What This Module Does

- Simulates thin-film interference for iridescent colors
- Implements diffraction grating effects for holographic shimmer
- Uses depth gradients as surface normals for Fresnel calculations
- Computes angle-dependent reflections and color shifts
- Supports multiple holographic blend modes (add, multiply, screen, overlay, replace)
- Configurable iridescence amount, film thickness, and diffraction strength
- GPU-accelerated fragment shader with complex optical calculations

## What This Module Does NOT Do

- Does NOT provide 3D ray tracing (approximates with screen-space)
- Does NOT simulate volumetric holography (surface-only)
- Does NOT include audio reactivity (may be added later)
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT handle multiple light sources (single viewpoint)

---

## Detailed Behavior

### Optical Simulation Pipeline

1. **Compute surface normal from depth gradient**:
   ```
   dx = dFdx(depth)
   dy = dFdy(depth)
   normal = normalize(vec3(-dx, -dy, 1.0))
   ```

2. **Compute view direction** (assuming orthographic from camera):
   ```
   view_dir = vec3(0, 0, 1)  # Looking along Z axis
   ```

3. **Fresnel effect**: Compute reflection amount based on angle:
   ```
   fresnel = pow(1.0 - dot(normal, view_dir), fresnel_power)
   ```

4. **Thin-film interference**: Calculate iridescent color from film thickness and angle:
   ```
   // Optical path difference
   OPD = 2 * film_thickness * cos(incident_angle) + phase_shift
   // Constructive/destructive interference
   iridescence = cos(OPD * wavelength_factors)
   ```

5. **Diffraction grating**: Add holographic sparkle based on viewing angle:
   ```
   diffraction = sin(angle * diffraction_frequency + time) * diffraction_strength
   ```

6. **Combine effects**: Mix iridescence and diffraction:
   ```
   holo_color = iridescence + diffraction
   ```

7. **Blend with source**: Use selected blend mode:
   ```
   result = blend(source, holo_color, blend_mode, iridescence_amount)
   ```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `iridescenceAmount` | float | 5.0 | 0.0-10.0 | Overall strength of holographic effect |
| `filmThickness` | float | 500.0 | 100.0-2000.0 | Thin film thickness (nm) |
| `diffractionStrength` | float | 3.0 | 0.0-10.0 | Intensity of diffraction grating sparkle |
| `diffractionFrequency` | float | 100.0 | 10.0-500.0 | Spatial frequency of diffraction (lines/mm) |
| `fresnelPower` | float | 2.0 | 0.5-10.0 | Fresnel falloff (higher = sharper falloff) |
| `blendMode` | int | 0 | 0-4 | 0=add, 1=multiply, 2=screen, 3=overlay, 4=replace |
| `colorShift` | float | 0.0 | 0.0-10.0 | Additional hue shift for iridescence |
| `shimmerSpeed` | float | 1.0 | 0.0-10.0 | Animation speed for diffraction |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class DepthHolographicIridescenceEffect(Effect):
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
| **Output** | `np.ndarray` | Holographic iridescence frame (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Latest depth frame
- `_depth_texture: int` — GL texture for depth data
- `_parameters: dict` — Holographic parameters
- `_shader: ShaderProgram` — Compiled shader

**Per-Frame:**
- Update depth data from source
- Upload depth texture
- Apply uniforms (including time for animation)
- Render holographic effect
- Return result

**Initialization:**
- Create depth texture (lazy)
- Compile shader
- Default parameters: iridescenceAmount=5.0, filmThickness=500.0, diffractionStrength=3.0, diffractionFrequency=100.0, fresnelPower=2.0, blendMode=0, colorShift=0.0, shimmerSpeed=1.0

**Cleanup:**
- Delete depth texture
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_RED, GL_UNSIGNED_BYTE | depth_frame size | Updated each frame |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Depth texture: 307,200 bytes
- Shader: ~20-50 KB (complex optical calculations)
- Total: ~0.3-0.4 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | Use flat normal (0,0,1) | Normal operation |
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
- Shader execution (optical calculations): ~4-8 ms
- Total: ~4.5-9 ms on GPU

**Optimization Strategies:**
- Reduce shader precision (use mediump floats)
- Precompute wavelength factors
- Use simpler Fresnel approximation
- Reduce diffraction calculations (lower frequency)
- Cache depth gradient if depth hasn't changed
- Use compute shader for parallel processing

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Holographic parameters configured (iridescence, film, diffraction, fresnel)
- [ ] Blend mode selected
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | Parameters can be set and clamped |
| `test_get_parameter` | Parameters can be retrieved |
| `test_depth_gradient` | Surface normals computed correctly from depth |
| `test_fresnel` | Fresnel effect increases at grazing angles |
| `test_thin_film_interference` | Iridescence colors appear based on film thickness |
| `test_diffraction` | Diffraction adds shimmering sparkles |
| `test_blend_modes` | Each blend mode produces correct mixing |
| `test_color_shift` | Additional hue shift modifies iridescence |
| `test_shimmer_animation` | Diffraction animates over time |
| `test_process_frame_no_depth` | Falls back to flat normal |
| `test_process_frame_with_depth` | Depth gradients drive effect |
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
- [ ] Git commit with `[Phase-3] P3-VD52: depth_holographic_iridescence_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_holographic.py` — VJLive Original implementation
- `plugins/core/depth_holographic/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_holographic/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthHolographicIridescenceEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_holographic`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for gradient-based normal approximation
- Parameters: `iridescenceAmount`, `filmThickness`, `diffractionStrength`, `diffractionFrequency`, `fresnelPower`, `blendMode`, `colorShift`, `shimmerSpeed`
- Allocates GL resources: depth texture
- Shader implements thin-film interference, diffraction grating, Fresnel effect
- Supports multiple blend modes

---

## Notes for Implementers

1. **Thin-Film Interference Physics**:
   - Light reflects from both top and bottom surfaces of a thin film
   - Optical path difference (OPD) causes constructive/destructive interference
   - OPD = 2 * n * d * cos(θ) + phase shifts
   - Where n = refractive index, d = thickness, θ = angle inside film
   - Result: colors shift with viewing angle and film thickness

2. **Simplified Implementation**:
   Instead of full physical simulation, use an approximate model:
   ```glsl
   // Compute incident angle from normal and view direction
   float cos_theta = dot(normal, view_dir);
   float theta = acos(cos_theta);
   
   // Effective film thickness varies with angle
   float effective_thickness = filmThickness * cos(theta);
   
   // Phase shift (in wavelengths)
   float phase = effective_thickness * 0.001;  // Simplified
   
   // Iridescence color from interference
   vec3 iridescence = vec3(
       sin(phase * 2.0 + colorShift),
       sin(phase * 2.0 + 2.094 + colorShift),  // +120° offset
       sin(phase * 2.0 + 4.188 + colorShift)   // +240° offset
   );
   iridescence = iridescence * 0.5 + 0.5;  // Remap to 0-1
   ```

3. **Diffraction Grating**:
   - Holographic surfaces have microscopic grooves that diffract light
   - Diffraction angle depends on wavelength and groove spacing
   - Simulate with sine wave based on viewing angle and time:
   ```glsl
   float diffraction = sin(
       (uv.x + uv.y) * diffractionFrequency * 0.01 +
       time * shimmerSpeed
   ) * diffractionStrength;
   ```

4. **Fresnel Effect**:
   - Reflection increases at grazing angles
   - Use Schlick's approximation or power function:
   ```glsl
   float fresnel = pow(1.0 - max(dot(normal, view_dir), 0.0), fresnelPower);
   ```

5. **Surface Normals from Depth**:
   - Depth gradient approximates surface normal
   - In screen space, compute derivatives:
   ```glsl
   float depth = texture(depth_tex, uv).r;
   float dx = dFdx(depth);
   float dy = dFdy(depth);
   vec3 normal = normalize(vec3(-dx, -dy, 1.0));
   ```
   - May need to scale dx, dy by depth range and focal length

6. **Blend Modes**:
   Implement 5 blend modes:
   ```glsl
   vec3 blend_add(vec3 a, vec3 b) { return a + b; }
   vec3 blend_multiply(vec3 a, vec3 b) { return a * b; }
   vec3 blend_screen(vec3 a, vec3 b) { return 1.0 - (1.0-a)*(1.0-b); }
   vec3 blend_overlay(vec3 a, vec3 b) {
       return a < 0.5 ? 2.0*a*b : 1.0 - 2.0*(1.0-a)*(1.0-b);
   }
   vec3 blend_replace(vec3 a, vec3 b) { return b; }
   ```

7. **Shader Uniforms**:
   ```glsl
   uniform sampler2D tex0;        // Source frame
   uniform sampler2D depth_tex;   // Depth texture
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float iridescenceAmount; // 0-10
   uniform float filmThickness;     // 100-2000 nm
   uniform float diffractionStrength; // 0-10
   uniform float diffractionFrequency; // 10-500 lines/mm
   uniform float fresnelPower;      // 0.5-10
   uniform int blendMode;           // 0-4
   uniform float colorShift;        // 0-10 (radians or hue shift)
   uniform float shimmerSpeed;      // 0-10
   ```

8. **Parameter Mapping**:
   - `iridescenceAmount`: 0-10 → 0.0-1.0 blend factor
   - `filmThickness`: 100-2000 → use directly (nm)
   - `diffractionStrength`: 0-10 → 0.0-1.0 multiplier
   - `diffractionFrequency`: 10-500 → scale appropriately
   - `fresnelPower`: 0.5-10 → use directly
   - `colorShift`: 0-10 → radians (0-10 rad ≈ 0-573°)
   - `shimmerSpeed`: 0-10 → Hz or multiplier

9. **Performance**: The shader does:
   - Depth gradient (dFdx/dFdy)
   - Normal normalization
   - Fresnel calculation
   - Thin-film interference (sin/cos)
   - Diffraction (sin with time)
   - Blend mode
   All are relatively fast; main cost is trig functions.

10. **Testing**: Create a depth ramp (smooth gradient) and verify:
    - Iridescence colors shift across depth
    - Fresnel makes edges brighter
    - Diffraction adds animated sparkle
    - Film thickness changes color palette
    - Blend modes mix correctly

11. **Future Extensions**:
    - Add multiple light sources
    - Add volumetric holography (ray marching)
    - Add audio reactivity to shimmer
    - Add custom holographic patterns (textures)
    - Add chromatic aberration to holographic effect

---
-

## References

- Thin-film interference: https://en.wikipedia.org/wiki/Thin-film_interference
- Diffraction grating: https://en.wikipedia.org/wiki/Diffraction_grating
- Fresnel equations: https://en.wikipedia.org/wiki/Fresnel_equations
- Holography: https://en.wikipedia.org/wiki/Holography
- Iridescence: https://en.wikipedia.org/wiki/Iridescence
- VJLive legacy: `plugins/vdepth/depth_holographic.py`

---

## Implementation Tips

1. **Full Shader**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;        // Source image
   uniform sampler2D depth_tex;   // Depth texture
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float iridescenceAmount;
   uniform float filmThickness;     // nm
   uniform float diffractionStrength;
   uniform float diffractionFrequency; // lines/mm
   uniform float fresnelPower;
   uniform int blendMode;           // 0=add,1=mult,2=screen,3=overlay,4=replace
   uniform float colorShift;        // radians
   uniform float shimmerSpeed;
   
   // Blend functions
   vec3 blend_add(vec3 a, vec3 b) { return a + b; }
   vec3 blend_multiply(vec3 a, vec3 b) { return a * b; }
   vec3 blend_screen(vec3 a, vec3 b) { return 1.0 - (1.0-a)*(1.0-b); }
   vec3 blend_overlay(vec3 a, vec3 b) {
       return a < 0.5 ? 2.0*a*b : 1.0 - 2.0*(1.0-a)*(1.0-b);
   }
   vec3 blend_replace(vec3 a, vec3 b) { return b; }
   
   void main() {
       vec4 source = texture(tex0, uv);
       float depth = texture(depth_tex, uv).r;
       
       // Compute surface normal from depth gradient
       float dx = dFdx(depth);
       float dy = dFdy(depth);
       vec3 normal = normalize(vec3(-dx, -dy, 1.0));
       
       // View direction (assuming orthographic camera looking along -Z)
       vec3 view_dir = vec3(0.0, 0.0, 1.0);
       
       // Fresnel effect
       float NdotV = max(dot(normal, view_dir), 0.0);
       float fresnel = pow(1.0 - NdotV, fresnelPower);
       
       // Thin-film interference
       // Effective thickness depends on angle
       float cos_theta = NdotV;
       float effective_thickness = filmThickness * cos_theta;
       
       // Phase shift (simplified: use wavelength factors for RGB)
       // Wavelengths: R~700nm, G~550nm, B~450nm
       float phase_r = effective_thickness * 0.01 + colorShift;
       float phase_g = effective_thickness * 0.01 + 2.094 + colorShift;  // 120° offset
       float phase_b = effective_thickness * 0.01 + 4.188 + colorShift;  // 240° offset
       
       vec3 iridescence = vec3(
           sin(phase_r) * 0.5 + 0.5,
           sin(phase_g) * 0.5 + 0.5,
           sin(phase_b) * 0.5 + 0.5
       );
       
       // Diffraction grating shimmer
       float diffraction = sin(
           (uv.x + uv.y) * diffractionFrequency * 0.1 +
           time * shimmerSpeed
       ) * diffractionStrength;
       
       // Combine iridescence and diffraction
       vec3 holo_color = iridescence + diffraction * 0.1;
       holo_color = clamp(holo_color, 0.0, 1.0);
       
       // Apply Fresnel as intensity mask
       holo_color *= fresnel;
       
       // Blend with source
       float amount = iridescenceAmount / 10.0;
       vec3 result;
       if (blendMode == 0) result = blend_add(source.rgb, holo_color);
       else if (blendMode == 1) result = blend_multiply(source.rgb, holo_color);
       else if (blendMode == 2) result = blend_screen(source.rgb, holo_color);
       else if (blendMode == 3) result = blend_overlay(source.rgb, holo_color);
       else result = blend_replace(source.rgb, holo_color);
       
       result = mix(source.rgb, result, amount);
       
       fragColor = vec4(clamp(result, 0.0, 1.0), source.a);
   }
   ```

2. **Depth Gradient Scaling**: The raw depth gradient may need scaling based on depth range and camera intrinsics. Consider:
   ```glsl
   float depth_scale = 100.0; // Adjust based on your depth units
   float dx = dFdx(depth) * depth_scale;
   float dy = dFdy(depth) * depth_scale;
   ```

3. **Film Thickness**: Typical thin-film interference occurs at thicknesses of 100-1000 nm. Map UI range (100-2000) directly.

4. **Diffraction Frequency**: Typical holographic gratings have 500-1000 lines/mm. Map UI range (10-500) appropriately.

5. **Color Shift**: The `colorShift` parameter can offset the phase to change the color palette. Use radians.

6. **Fresnel Power**: Lower values (0.5-2) give broad falloff; higher values (5-10) give sharp edge-only reflections.

7. **Blend Mode**: The `replace` mode completely replaces source with holographic color (most intense). `add` mode adds brightness (glowing). `multiply` darkens. `screen` lightens. `overlay` increases contrast.

8. **Performance**: The shader uses trig functions (sin) which can be expensive. Consider:
   - Using precomputed lookup texture for interference colors
   - Reducing `diffractionFrequency` to lower sin frequency
   - Using `mediump` precision

9. **Testing**: Create a depth gradient (e.g., a slanted plane) and verify:
   - Iridescence colors shift smoothly across the gradient
   - Fresnel makes edges (steeper angles) brighter
   - Diffraction adds animated sparkle pattern
   - Changing film thickness changes base colors

10. **PRESETS**:
    ```python
    PRESETS = {
        "soap_bubble": {
            "iridescenceAmount": 6.0, "filmThickness": 300.0,
            "diffractionStrength": 1.0, "diffractionFrequency": 200.0,
            "fresnelPower": 2.0, "blendMode": 2, "colorShift": 0.0,
            "shimmerSpeed": 1.0,
        },
        "holographic_sticker": {
            "iridescenceAmount": 8.0, "filmThickness": 800.0,
            "diffractionStrength": 6.0, "diffractionFrequency": 100.0,
            "fresnelPower": 3.0, "blendMode": 0, "colorShift": 1.0,
            "shimmerSpeed": 3.0,
        },
        "subtle_iridescence": {
            "iridescenceAmount": 3.0, "filmThickness": 500.0,
            "diffractionStrength": 2.0, "diffractionFrequency": 150.0,
            "fresnelPower": 2.5, "blendMode": 3, "colorShift": 0.5,
            "shimmerSpeed": 0.5,
        },
    }
    ```

11. **Depth Normal Quality**: The quality of the normal map from depth is crucial. If depth is noisy, consider:
    - Pre-smoothing depth texture
    - Using larger kernel for gradient
    - Using bilateral filter to preserve edges

12. **View Direction**: The current implementation assumes orthographic projection from fixed camera. For perspective, you'd need actual 3D position. This is a simplification suitable for VJ use.

---

## Conclusion

The DepthHolographicIridescenceEffect brings the magic of holographic materials and thin-film interference to VJ performances. By leveraging depth data to approximate surface normals, it creates angle-dependent iridescent colors that shift with camera movement and object geometry. Combined with diffraction grating sparkle and multiple blend modes, this effect adds a touch of futuristic, otherworldly beauty to any visual composition.

---
