# CosmicTunnelDatamoshEffect — Recursive Fractal Tunnel with Datamosh

**Task ID:** P3-EXT035  
**Module:** `CosmicTunnelDatamoshEffect`  
**Phase:** Pass 2 Fleshing Out  
**Status:** Ready for Phase 3 Review  

---

## Overview

The [`CosmicTunnelDatamoshEffect`](docs/specs/_02_fleshed_out/P3-EXT035_CosmicTunnelDatamoshEffect.md:136) class implements a recursive fractal tunnel effect with datamosh-style pixel stretching and feedback. It transforms video into an infinite, fast-moving tunnel where the walls are fractalized versions of the video itself. The effect uses log-polar coordinates, depth mapping, and multi-pass recursion to create the illusion of eternal forward motion.

**What This Module Does**

- Maps Cartesian screen coordinates to log-polar tunnel space
- Applies fractal distortion to tunnel walls using iterative complex-plane-like operations
- Uses feedback from previous frame (`texPrev`) to create recursive depth
- Supports dual video inputs (tex0 and tex1) with automatic fallback
- Integrates with depth maps to modulate effect intensity per-pixel
- Provides 12 controllable parameters for speed, rotation, recursion, and visual effects
- Includes audio reactivity for tunnel speed, wall warp, aberration, and fractal depth
- Offers three preset configurations for different visual styles

**What This Module Does NOT Do**

- Does not include traditional datamosh compression artifacts (no motion vector displacement)
- Does not support 3D geometry or raymarching (uses 2D coordinate transforms)
- Does not include HDR color processing (operates in standard 8-bit RGB)
- Does not provide temporal smoothing or frame blending beyond the single `texPrev` feedback
- Does not include particle systems or volumetric effects

---

## Detailed Behavior and Parameter Interactions

### Texture Unit Layout

The effect uses multiple texture units:

| Unit | Name | Type | Purpose |
|------|------|------|---------|
| 0 | `tex0` | `sampler2D` | Primary video input (Video A) |
| 1 | `texPrev` | `sampler2D` | Previous frame feedback (recursion) |
| 2 | `depth_tex` | `sampler2D` | Depth map for per-pixel modulation |
| 3 | `tex1` | `sampler2D` | Secondary video input (Video B, optional) |

The effect automatically detects if `tex1` is valid by sampling its center pixel. If the sum of RGB channels is > 0.001, `tex1` is used; otherwise `tex0` is used.

### Core Algorithm: Log-Polar Tunnel Mapping

The effect transforms screen coordinates into a tunnel using log-polar coordinates:

```glsl
vec2 toTunnel(vec2 uv) {
    vec2 p = uv - 0.5;
    float r = length(p);
    float a = atan(p.y, p.x);
    return vec2(0.5 / r, a / 3.14159);
}
```

This maps:
- `r` (distance from center) → `0.5/r` (tunnel depth coordinate)
- `a` (angle) → `a/π` (tunnel azimuth, normalized to [-0.5, 0.5])

The tunnel coordinate `tunUV` is then animated:

```glsl
tunUV.x += time * u_tunnel_speed * 0.5;  // Move forward
tunUV.y += time * u_rotation * 0.1;      // Rotate tunnel
```

### Fractal Wall Distortion

The tunnel walls are distorted using a simplified fractal iteration:

```glsl
vec2 fracUV = tunUV;
for(int i=0; i<3; i++) {
    fracUV = abs(fracUV) / dot(fracUV, fracUV) - u_fractal_depth * 0.1;
}
```

This is reminiscent of a Mandelbrot-like iteration `z = |z|² / z - c`, creating intricate fractal patterns on the tunnel walls. The `u_fractal_depth` parameter controls the offset subtracted each iteration.

### Depth-Modulated Mix

The effect uses a depth map to blend between normal planar sampling and tunnel sampling:

```glsl
vec2 mixUV = mix(uv, fract(tunUV + fracUV * 0.05), u_depth_fov * depth);
mixUV = clamp(mixUV, 0.0, 1.0);
vec4 color = hasDual ? texture(tex1, mixUV) : texture(tex0, mixUV);
```

- `depth` is sampled from `depth_tex` (red channel)
- `u_depth_fov` scales the depth influence
- When `depth` is high (near), `mixUV` stays closer to `uv` (planar)
- When `depth` is low (far), `mixUV` wraps into the tunnel space

### Recursive Feedback

The effect samples the previous frame (`texPrev`) with a slight zoom and rotation toward the center:

```glsl
vec2 prevUV = (uv - 0.5) * (0.99 - u_center_pull * 0.02) + 0.5;
float s = sin(u_rotation * 0.01);
float c = cos(u_rotation * 0.01);
prevUV -= 0.5;
prevUV = vec2(prevUV.x * c - prevUV.y * s, prevUV.x * s + prevUV.y * c);
prevUV += 0.5;
vec4 prev = texture(texPrev, prevUV);
```

The feedback is then blended with the current frame:

```glsl
color = mix(color, prev, u_recursion * 0.1 + depth * 0.5);
```

The recursion factor combines the `u_recursion` parameter (scaled by 0.1) with depth (scaled by 0.5). This means deeper pixels (further into the tunnel) get more feedback, enhancing the infinite tunnel illusion.

### Chromatic Aberration

If `u_aberration > 0.0`, the effect adds chromatic aberration at the periphery:

```glsl
float r_off = u_aberration * 0.01 * length(uv - 0.5);
color.r = texture(..., mixUV + vec2(r_off, 0)).r;
color.b = texture(..., mixUV - vec2(r_off, 0)).b;
```

The red channel samples offset to the right, blue to the left, by an amount proportional to distance from center and the `u_aberration` parameter.

### Grid Lines

If `u_grid_lines > 0.5`, a grid pattern is overlaid on the tunnel:

```glsl
float grid = sin(tunUV.x * 20.0) * sin(tunUV.y * 20.0);
color.rgb += vec3(smoothstep(0.9, 1.0, grid)) * 0.3 * u_grid_lines;
```

The grid is drawn in tunnel UV space, creating a geometric grid that wraps around the tunnel walls.

### Color Shift

A simple color tint is applied, scaled by depth:

```glsl
vec3 shift = vec3(u_color_shift * 0.1, u_color_shift * 0.05, 0.0);
color.rgb += shift * depth;
```

This adds red and green (yellow-ish tint) proportional to `u_color_shift` and depth.

### Eternity Fade

The center of the tunnel can fade to white or black based on `u_eternity`:

```glsl
color.rgb = mix(color.rgb, vec3(u_eternity > 5.0 ? 1.0 : 0.0),
                smoothstep(0.0, 0.2, length(uv-0.5)) * abs(u_eternity - 5.0) * 0.1);
```

- If `u_eternity > 5.0`, the center fades to white; else to black.
- The fade amount is proportional to `abs(u_eternity - 5.0)` (distance from neutral)
- The fade is applied within a radius of 0.2 from the center, smoothly blended.

### Final Mix

The effect blends the transformed result with the original (untransformed) input:

```glsl
vec4 original = hasDual ? texture(tex1, uv) : texture(tex0, uv);
fragColor = mix(original, color, u_mix);
```

### Parameter Space and UI Mapping

All user-facing parameters use a normalized `0.0` to `10.0` range. The class uses a `_map_param()` method to convert these to shader-specific ranges:

| Parameter | UI Range | Shader Uniform | Internal Range | Purpose |
|-----------|----------|----------------|----------------|---------|
| `tunnel_speed` | 0.0-10.0 | `u_tunnel_speed` | 0.0-5.0 | Forward movement speed |
| `rotation` | 0.0-10.0 | `u_rotation` | -3.0 to +3.0 | Tunnel rotation (radians?) |
| `fractal_depth` | 0.0-10.0 | `u_fractal_depth` | 0.0-1.0 | Fractal distortion intensity |
| `recursion` | 0.0-10.0 | `u_recursion` | 0.0-1.0 | Feedback blend factor |
| `center_pull` | 0.0-10.0 | `u_center_pull` | 0.0-2.0 | Zoom toward center in feedback |
| `wall_warp` | 0.0-10.0 | `u_wall_warp` | 0.0-5.0 (with audio boost) | Wall undulation amplitude |
| `color_shift` | 0.0-10.0 | `u_color_shift` | 0.0-5.0 | Color tint intensity |
| `depth_fov` | 0.0-10.0 | `u_depth_fov` | 0.0-1.0 | Depth influence on planar/tunnel mix |
| `mosh_stretch` | 0.0-10.0 | `u_mosh_stretch` | 0.0-1.0 | Pixel stretching along tunnel |
| `grid_lines` | 0.0-10.0 | `u_grid_lines` | 0.0-1.0 | Grid overlay intensity |
| `aberration` | 0.0-10.0 | `u_aberration` | 0.0-5.0 | Chromatic aberration strength |
| `eternity` | 0.0-10.0 | `u_eternity` | 0.0-10.0 | Center fade to white/black |

**Note:** The `_map_param(name, out_min, out_max)` function computes: `out_min + (val / 10.0) * (out_max - out_min)`.

### Audio Reactivity

The effect includes audio reactivity via the `apply_uniforms` method:

```python
if audio_reactor is not None:
    try:
        speed *= (1.0 + audio_reactor.get_energy(0.5) * 0.5)
        warp *= (1.0 + audio_reactor.get_band('bass', 0.0) * 0.8)
    except Exception:
        pass
```

- `tunnel_speed` is modulated by overall audio energy (0.5 weight) → speed increases up to 50%
- `wall_warp` is modulated by bass frequency (0.0 weight) → warp increases up to 80%

The `audio_mappings` dictionary documents these connections:

```python
self.audio_mappings = {
    'tunnel_speed': 'energy',
    'wall_warp': 'bass',
    'aberration': 'high',
    'fractal_depth': 'mid',
}
```

Note: The code only applies audio modulation to `speed` and `warp`; the mappings for `aberration` and `fractal_depth` are declared but not implemented in the `apply_uniforms` method (this may be a bug or incomplete feature).

### Preset Configurations

The class provides three preset parameter sets:

- **`black_hole`**: `{tunnel_speed: 8.0, rotation: 5.0, fractal_depth: 3.0, recursion: 8.0, center_pull: 9.0, wall_warp: 2.0, color_shift: 2.0, depth_fov: 8.0, mosh_stretch: 7.0, grid_lines: 1.0, aberration: 8.0, eternity: 0.0}` — high speed, strong center pull, moderate warp, strong aberration, no eternity fade. Creates a intense, fast-moving black hole effect.

- **`kaleido_tube`**: `{tunnel_speed: 3.0, rotation: 8.0, fractal_depth: 7.0, recursion: 6.0, center_pull: 2.0, wall_warp: 6.0, color_shift: 8.0, depth_fov: 5.0, mosh_stretch: 4.0, grid_lines: 5.0, aberration: 3.0, eternity: 5.0}` — slower, high rotation, high fractal depth, strong color shift, grid lines visible, eternity at neutral. Creates a kaleidoscopic tube with geometric patterns.

- **`hyperspace`**: `{tunnel_speed: 10.0, rotation: 0.0, fractal_depth: 0.0, recursion: 9.0, center_pull: 5.0, wall_warp: 0.0, color_shift: 1.0, depth_fov: 10.0, mosh_stretch: 10.0, grid_lines: 0.0, aberration: 10.0, eternity: 10.0}` — maximum speed, no rotation, no fractal, high recursion, full depth_fov, max mosh stretch, max aberration, full eternity fade to white. Creates a classic hyperspace jump effect.

---

## Public Interface

### Class: `CosmicTunnelDatamoshEffect`

**Inheritance:** [`Effect`](docs/specs/_02_fleshed_out/P3-EXT035_CosmicTunnelDatamoshEffect.md:136) (from `core.effects.shader_base`)

**Constructor:** `__init__(self, name: str = 'cosmic_tunnel_datamosh')`

Initializes the effect with default parameters:

```python
self.parameters = {
    'tunnel_speed': 4.0,
    'rotation': 2.0,
    'fractal_depth': 3.0,
    'recursion': 5.0,
    'center_pull': 4.0,
    'wall_warp': 3.0,
    'color_shift': 2.0,
    'depth_fov': 5.0,
    'mosh_stretch': 4.0,
    'grid_lines': 2.0,
    'aberration': 3.0,
    'eternity': 5.0,
}
self.audio_mappings = {
    'tunnel_speed': 'energy',
    'wall_warp': 'bass',
    'aberration': 'high',
    'fractal_depth': 'mid',
}
```

**Properties:**

- `name = "cosmic_tunnel_datamosh"` (or custom name passed to constructor)
- `fragment_shader = FRAGMENT` — GLSL fragment shader (see full listing in legacy reference)
- `effect_category` — Not explicitly set in legacy; likely `"datamosh"` or `"distortion"`
- `effect_tags` — Not explicitly set; based on description: `["datamosh", "glitch", "tunnel", "fractal", "recursive", "psychedelic"]`
- `audio_mappings` — Dictionary mapping parameters to audio features

**Methods:**

- `apply_uniforms(time, resolution, audio_reactor=None, semantic_layer=None)`: Sets all shader uniforms, including parameter mapping and audio modulation. Overrides base class.
- `get_state() -> Dict[str, Any]`: Returns a dictionary with `{'name': self.name, 'enabled': self.enabled, 'parameters': dict(self.parameters)}`.
- `set_parameter(name: str, value: float)`: Likely inherited from base class; should clamp to [0.0, 10.0] (not shown in legacy snippet but expected).
- `get_parameter(name: str) -> float`: Likely inherited; returns parameter value in UI range.

**Class Attributes:**

- `PRESETS = {...}` — Dictionary of preset parameter configurations (see above).
- `FRAGMENT` — The full GLSL shader code (lines 29-134 in legacy file).

---

## Inputs and Outputs

### Inputs

| Pin | Type | Description |
|-----|------|-------------|
| `tex0` | `sampler2D` | Primary video input (Video A) |
| `texPrev` | `sampler2D` | Previous frame buffer (for recursion/feedback) |
| `depth_tex` | `sampler2D` | Depth map (single channel, typically red) |
| `tex1` | `sampler2D` | Secondary video input (Video B, optional) |
| `u_mix` | `float` | Blend factor between original and tunnel result (0.0-1.0) |
| `time` | `float` | Shader time in seconds (for animation) |
| `resolution` | `vec2` | Viewport resolution in pixels |
| `uv` | `vec2` | Normalized texture coordinates |

All parameters are passed as uniforms (see table above).

### Outputs

| Pin | Type | Description |
|-----|------|-------------|
| `fragColor` | `vec4` | RGBA output with tunnel effect applied (alpha unchanged) |

---

## Edge Cases and Error Handling

### Edge Cases

1. **No previous frame**: `texPrev` must be a valid texture containing the previous frame's output. If not provided or uninitialized, the recursion will sample undefined data (likely black or garbage). The effect expects the host to manage framebuffer ping-pong.

2. **No depth map**: `depth_tex` is required. If not provided or all zeros, the depth-modulated effects (depth_fov, wall_warp, recursion depth weighting, color shift, eternity fade) will be minimized, effectively flattening the tunnel. The effect will still render but may look flat.

3. **Dual input detection**: The code checks `hasDual` by sampling the center of `tex1`. If `tex1` is not bound or is black, `hasDual` is false and `tex0` is used. This is safe.

4. **Extreme recursion**: `u_recursion = 1.0` (max) combined with `u_center_pull = 2.0` (max) gives `prevUV` scale factor `0.99 - 2.0*0.02 = 0.95`, meaning the feedback zooms out by 5% per frame. This can cause rapid feedback decay or expansion. The `u_recursion` blend factor becomes `0.1 + depth*0.5`, so at max recursion and full depth, the blend is 0.6 (60% feedback). This is moderate.

5. **Fractal depth**: `u_fractal_depth = 1.0` (max) subtracts `0.1` each iteration. The iteration `fracUV = abs(fracUV) / dot(fracUV, fracUV) - 0.1` can produce large values or division by near-zero if `fracUV` approaches zero. However, the initial `fracUV = tunUV` is typically not zero (tunnel coordinates at screen center map to `r=0` → `tunUV.x = 0.5/0 = ∞`? Actually, at `uv=0.5`, `r=0` → `0.5/r` is infinity. This is a problem: the `toTunnel` function divides by `r`. At exact center, `r=0` → `tunUV.x = ∞`. This will produce NaNs or infinities in the shader, likely causing undefined behavior. The effect should avoid exact center sampling or add epsilon. This is a **critical edge case**.

6. **Aberration at edges**: `u_aberration` offsets are computed as `u_aberration * 0.01 * length(uv-0.5)`. At corners, `length(uv-0.5) ≈ 0.707`, so max offset ≈ `5.0 * 0.01 * 0.707 = 0.035`. This is safe. At center, offset is 0.

7. **Eternity fade**: `u_eternity = 5.0` is neutral (no fade). `u_eternity = 0.0` or `10.0` gives `abs(u_eternity-5.0)=5.0`, so fade factor = `smoothstep(0,0.2, r) * 5.0 * 0.1 = 0.5 * smoothstep(...)`. This can fade up to 50% to black/white within radius 0.2. That's moderate.

8. **Grid lines**: `u_grid_lines` scales the grid addition. At `u_grid_lines=1.0`, the grid adds up to `0.3 * 1.0 = 0.3` intensity. This can brighten the image but not clip.

9. **Mix parameter**: `u_mix` is set to `1.0` in `apply_uniforms` (hardcoded). The skeleton likely expects `u_mix` to be a parameter controlled by the host. The legacy code sets it to 1.0 always, which means the effect is always fully applied. This may be intentional for datamosh effects, but it's unusual. The final `fragColor = mix(original, color, u_mix)` uses this uniform.

10. **Audio modulation errors**: The `try/except` around audio modulation means if `audio_reactor` methods fail, the effect continues without audio reactivity. This is safe but may hide bugs.

### Error Handling

- **Division by zero in `toTunnel`**: Not handled. At `uv=0.5`, `r=0` → `0.5/r = ∞`. This will produce infinities in shader, likely resulting in black or undefined colors. This is a known limitation; the effect should be used with a small offset from center or the shader should add epsilon: `0.5 / max(r, 1e-6)`.
- **No parameter clamping**: The legacy `__init__` sets parameters directly without clamping. The base class `set_parameter` method (not shown) should clamp to [0,10]. If not, invalid values could break `_map_param`.
- **Shader compilation**: The GLSL code uses `#version 330 core` and standard functions; should compile on any GL 3.3+ context.
- **Texture completeness**: If `texPrev` is not the same size as the framebuffer, sampling may be stretched or misaligned. The host must ensure proper texture management.

---

## Mathematical Formulations

### Coordinate Transforms

**Log-polar mapping**:

Given `uv ∈ [0,1]²`, compute:

```
p = uv - 0.5
r = |p|
a = atan(p.y, p.x)  // range [-π, π]
tunUV = (0.5 / r, a / π)
```

**Tunnel animation**:

```
tunUV.x ← tunUV.x + time * speed * 0.5
tunUV.y ← tunUV.y + time * rotation * 0.1
```

**Wall warp**:

```
warp = sin(tunUV.y * 10.0 + time) * wall_warp * 0.01 * depth
tunUV.x ← tunUV.x + warp
```

**Fractal iteration** (3 iterations):

```
fracUV = tunUV
for i in 0..2:
    fracUV = |fracUV| / dot(fracUV, fracUV) - fractal_depth * 0.1
```

**Mix UV**:

```
mixUV = mix(uv, fract(tunUV + fracUV * 0.05), depth_fov * depth)
mixUV = clamp(mixUV, 0, 1)
```

**Feedback UV**:

```
scale = 0.99 - center_pull * 0.02
prevUV = (uv - 0.5) * scale + 0.5
// Apply rotation:
prevUV = prevUV - 0.5
prevUV = (prevUV.x * cos(rot) - prevUV.y * sin(rot), prevUV.x * sin(rot) + prevUV.y * cos(rot))
prevUV = prevUV + 0.5
```

where `rot = rotation * 0.01` (radians?).

**Color composition**:

```
color = sample(tex0 or tex1, mixUV)
prev = sample(texPrev, prevUV)
color = mix(color, prev, recursion * 0.1 + depth * 0.5)

// Chromatic aberration (if aberration > 0):
r_off = aberration * 0.01 * |uv-0.5|
color.r = sample(..., mixUV + (r_off, 0)).r
color.b = sample(..., mixUV - (r_off, 0)).b

// Grid lines (if grid_lines > 0.5):
grid = sin(tunUV.x * 20) * sin(tunUV.y * 20)
color.rgb += (smoothstep(0.9, 1.0, grid) * 0.3 * grid_lines)

// Color shift:
color.rgb += (color_shift * 0.1, color_shift * 0.05, 0) * depth

// Eternity fade:
fade_target = (eternity > 5.0) ? 1.0 : 0.0
fade_amount = smoothstep(0, 0.2, |uv-0.5|) * |eternity-5.0| * 0.1
color.rgb = mix(color.rgb, fade_target, fade_amount)

// Final mix:
original = sample(tex0 or tex1, uv)
output = mix(original, color, u_mix)
```

### Parameter Mapping

For any parameter `p` with UI value `p_ui ∈ [0,10]`, the shader uniform `u_p` is computed as:

```
u_p = p_min + (p_ui / 10.0) * (p_max - p_min)
```

where the `(p_min, p_max)` pairs are as listed in the table above.

---

## Performance Characteristics

### Computational Complexity

- **Base cost**: High. The shader performs:
  - 1-2 texture samples (primary + optional secondary) + 1 feedback sample + 1 depth sample = 3-4 samples per pixel
  - 3 iterations of fractal math (abs, dot, division) per pixel
  - Multiple trigonometric functions: `atan`, `sin`, `cos` (called multiple times)
  - Log-polar transform with division by `r` (potential division by zero)
  - Chromatic aberration adds 2 additional texture samples (red and blue offsets) when enabled
  - Grid lines add a few arithmetic ops
- **No loops** beyond the fixed 3-iteration fractal loop (unrolled by compiler)
- **Heavy GPU load**: This is a `MEDIUM` to `HIGH` tier effect as per plugin manifest. Expect 2-5ms per 1080p frame on modern GPU, possibly more with recursion and fractal depth.

### Memory Usage

- **Uniforms**: 12 floats + standard uniforms (time, resolution, u_mix) = ~14 uniforms.
- **Textures**: Requires 3-4 texture units bound simultaneously.
- **Framebuffer**: Requires a separate framebuffer for `texPrev` feedback (ping-pong). The host must manage this.

### GPU Optimization Notes

- The fractal iteration is the most expensive part (3 divisions per iteration). Could be optimized with lookup textures or simplified to fewer iterations.
- The `atan` and `sin/cos` calls are expensive; consider using approximations or precomputed lookup if performance is critical.
- The chromatic aberration adds 2 extra texture fetches; could be combined into a single gather if hardware supports it.
- The effect is not suitable for mobile or low-end GPUs at high resolutions. Consider reducing fractal iterations or disabling some features for lower tiers.

---

## Test Plan

**Minimum coverage:** 80% before task is marked done.

### Unit Tests (Python)

1. **Parameter remapping**: Verify `_map_param()` for all parameters produces correct ranges (e.g., `tunnel_speed=5.0` → 2.5).
2. **Parameter clamping**: If `set_parameter` exists, test clamping to [0.0, 10.0].
3. **Get/set symmetry**: For each parameter, verify `get_parameter` returns the value set.
4. **Preset values**: Verify each preset contains all 12 keys and values within 0-10.
5. **Audio mappings**: Verify `audio_mappings` dictionary contains expected keys.
6. **State retrieval**: Test `get_state()` returns correct dict structure.
7. **Default parameters**: Verify all 12 parameters have expected default values.
8. **Depth FOV mapping**: Test `depth_fov` maps to [0,1] correctly.
9. **Rotation mapping**: Test `rotation` maps to [-3, 3] correctly.
10. **Eternity neutral**: Test `eternity=5.0` produces no fade (fade_amount should be 0).
11. **Aberration zero**: Test `aberration=0.0` disables chromatic aberration.
12. **Grid lines threshold**: Test `grid_lines=0.5` is the activation threshold.

### Integration Tests (Shader Rendering)

13. **Tunnel transformation**: Render a test pattern and verify log-polar mapping creates tunnel effect.
14. **Fractal distortion**: Render with `fractal_depth > 0` and verify intricate wall patterns.
15. **Recursion feedback**: Render with `recursion > 0` and verify infinite tunnel illusion.
16. **Depth modulation**: Render with depth map and verify near/far regions respond differently.
17. **Dual input**: Test with both `tex0` and `tex1` valid; verify `tex1` is used.
18. **Single input fallback**: Test with `tex1` black; verify `tex0` is used.
19. **Rotation**: Test `rotation` parameter rotates the tunnel.
20. **Tunnel speed**: Test `tunnel_speed` controls forward movement speed.
21. **Center pull**: Test `center_pull` zooms feedback toward center.
22. **Wall warp**: Test `wall_warp` creates undulating tunnel walls.
23. **Color shift**: Test `color_shift` adds yellow tint proportional to depth.
24. **Aberration**: Test `aberration` adds red/blue fringing at edges.
25. **Grid lines**: Test `grid_lines` overlays a grid pattern.
26. **Eternity fade**: Test `eternity=0.0` fades center to black; `eternity=10.0` fades to white.
27. **Mix blending**: Test `u_mix` values (if made variable) blend between original and effect.
28. **Preset rendering**: Render each preset and verify visual character (e.g., `hyperspace` should be fast with white center, `kaleido_tube` should have grid and rotation).
29. **Audio reactivity**: Attach mock audio reactor and verify `tunnel_speed` and `wall_warp` are modulated.
30. **Edge case: center pixel**: Render exact center pixel and verify no NaN/infinity artifacts (may need to add epsilon in shader).

### Performance Tests

31. **Benchmark 1080p**: Measure frame time with default parameters; should be < 16ms for 60fps (likely 2-5ms).
32. **Benchmark with all effects**: Enable all features (aberration, grid, fractal) and measure worst-case.
33. **Texture sample count**: Use GPU profiling to verify 3-4 texture samples per pixel (more with aberration).

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass (80% coverage minimum)
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT035: CosmicTunnelDatamoshEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

This spec is derived from the following legacy implementations:

- [`plugins/vdatamosh/cosmic_tunnel_datamosh.py`](home/happy/Desktop/claude projects/VJlive-2/plugins/vdatamosh/cosmic_tunnel_datamosh.py:1) (VJlive Original) — Full implementation with shader code (lines 29-134) and class (lines 136-213).
- [`plugins/core/cosmic_tunnel_datamosh/__init__.py`](home/happy/Desktop/claude projects/VJlive-2/plugins/core/cosmic_tunnel_datamosh/__init__.py:1) (VJlive-2 Legacy) — Same implementation in a different plugin location.
- [`core/matrix/node_datamosh.py`](home/happy/Desktop/claude projects/VJlive-2/core/matrix/node_datamosh.py:1) — Registration of the effect in the datamosh node system.

The legacy code validates the parameter ranges, default values, preset configurations, and mathematical formulations described in this spec. The effect is a sophisticated recursive tunnel using log-polar coordinates, fractal distortion, and depth-modulated feedback.

---

## Open Questions / [NEEDS RESEARCH]

- **Center division by zero**: The `toTunnel` function divides by `r` which is zero at screen center. This needs a fix: `0.5 / max(r, 1e-6)`. Should this be handled in the spec or left to implementer? [NEEDS RESEARCH]
- **Audio mappings incomplete**: The `audio_mappings` dict includes `aberration` and `fractal_depth` but the code doesn't modulate them. Should these be implemented? [NEEDS RESEARCH]
- **Parameter `u_mix` hardcoded**: The `apply_uniforms` sets `u_mix` to 1.0 always. Should this be a parameter? Or is the effect meant to be always fully applied? [NEEDS RESEARCH]
- **Rotation units**: The `rotation` parameter maps to `-3.0 to 3.0` and is used as `sin(u_rotation * 0.01)`. This suggests the rotation angle in the feedback transform is `u_rotation * 0.01` radians? That's a very small range. Is this correct? [NEEDS RESEARCH]
- **Depth map channel**: The shader samples `depth_tex.r` only. Should we support other channels or combinations? [NEEDS RESEARCH]
- **Dual input blending**: The effect chooses either `tex0` or `tex1` based on whether `tex1` is "valid" (non-black center). Should there be a blend mode between the two inputs? [NEEDS RESEARCH]
- **Mosh stretch unused**: The parameter `mosh_stretch` is mapped to a uniform but never used in the shader. Is this a leftover or should it affect something? [NEEDS RESEARCH]

---

*— desktop-roo, 2026-03-03*