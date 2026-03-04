# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-P3-VD72_displacement_map_effect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD72 — DisplacementMapEffect

## Description

The DisplacementMapEffect is a fundamental image warping technique where one signal (the displacement map) controls how another signal (the source image) is warped through space. This effect is the basis for many visual distortions, from subtle texture deformations to dramatic spatial transformations. It's essential for creating effects like water ripples, heat distortion, lens effects, and complex spatial manipulations.

This effect is ideal for VJ performances that want to create organic, fluid distortions, simulate physical phenomena, or create complex spatial transformations. The effect is highly configurable with 21 parameters controlling source modes, channel mappings, and feedback iteration.

## What This Module Does

- Warps one image using another as a displacement map
- Supports 6 source modes (self-luma, self-RG, noise, radial, edge, curl flow)
- Supports 5 channel mappings (XY, R→XY, radial, twist, zoom)
- Provides feedback iteration for complex distortions
- Includes edge darkening for displaced areas
- GPU-accelerated with real-time performance
- Configurable with 21 parameters

## What This Module Does NOT Do

- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT include audio reactivity in base implementation
- Does NOT produce 3D effects (2D only)
- Does NOT include color correction (only displacement)
- Does NOT support multiple displacement layers (single layer)

---

## Detailed Behavior

### Displacement Mapping Pipeline

1. **Capture source frame**: `source_frame` (HxWxC, RGB)
2. **Capture displacement map**: `map_frame` (HxWxC, RGB) — provides displacement vectors
3. **Compute displacement vectors**: Based on source mode and channel mapping
4. **Apply displacement**: Warp source pixels according to displacement vectors
5. **Feedback iteration**: Apply displacement multiple times for complex effects
6. **Edge darkening**: Darken areas with high displacement
7. **Composite**: Blend result with original via `u_mix`

### Core Displacement Concept

The displacement map provides offset vectors for each pixel. For each output pixel at coordinate (x, y):

```glsl
vec2 displacement = get_displacement(uv);  // From displacement map
vec2 source_uv = uv + displacement;        // Sample source at displaced position
vec3 color = texture(source_texture, source_uv).rgb;
```

### Source Modes

| Mode | Description | Implementation |
|------|-------------|-----------------|
| **Self-Luma** | Use source image luminance as displacement | `displacement = vec2(luma, luma) * strength` |
| **Self-RG** | Use source image red/green channels as displacement | `displacement = vec2(red, green) * strength` |
| **Noise** | Use procedural noise as displacement | `displacement = noise(uv) * strength` |
| **Radial** | Radial displacement from center | `displacement = normalize(uv - center) * radius * strength` |
| **Edge** | Edge detection as displacement | `displacement = edge_detect(source) * strength` |
| **Curl Flow** | Curl noise flow field | `displacement = curl_noise(uv) * strength` |

### Channel Mappings

| Mapping | Description | Implementation |
|---------|-------------|-----------------|
| **XY** | Direct XY displacement | `displacement = vec2(x, y)` |
| **R→XY** | Red channel to XY | `displacement = vec2(red, red)` |
| **Radial** | Radial displacement | `displacement = normalize(uv - center) * red` |
| **Twist** | Twisting displacement | `displacement = vec2(cos(angle), sin(angle)) * red` |
| **Zoom** | Zooming displacement | `displacement = normalize(uv - center) * red * zoom` |

### Feedback Iteration

Multiple passes of displacement create complex, organic distortions:

```glsl
vec2 uv = initial_uv;
for (int i = 0; i < iterations; i++) {
    vec2 disp = get_displacement(uv);
    uv = uv + disp * feedback_strength;
}
```

### Edge Darkening

Highly displaced areas are darkened to create depth:

```glsl
float disp_mag = length(final_disp) / strength;
color *= 1.0 - disp_mag * edge_darken;
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `sourceMode` | int | 0 | 0-5 | Source mode (0=Self-Luma, 1=Self-RG, 2=Noise, 3=Radial, 4=Edge, 5=Curl Flow) |
| `channelMapping` | int | 0 | 0-4 | Channel mapping (0=XY, 1=R→XY, 2=Radial, 3=Twist, 4=Zoom) |
| `strength` | float | 5.0 | 0.0-10.0 | Overall displacement strength |
| `iterations` | int | 3 | 1-10 | Number of feedback iterations |
| `feedbackStrength` | float | 3.0 | 0.0-10.0 | Strength of feedback iteration |
| `edgeDarken` | float | 2.0 | 0.0-10.0 | Edge darkening intensity |
| `noiseScale` | float | 4.0 | 0.0-10.0 | Noise scale (for Noise mode) |
| `noiseOctaves` | int | 3 | 1-8 | Noise octaves (for Noise mode) |
| `radialCenter` | vec2 | (0.5, 0.5) | 0.0-1.0 | Radial center (for Radial mode) |
| `radialRadius` | float | 0.5 | 0.0-10.0 | Radial radius (for Radial mode) |
| `edgeThreshold` | float | 0.3 | 0.0-1.0 | Edge detection threshold (for Edge mode) |
| `curlScale` | float | 2.0 | 0.0-10.0 | Curl noise scale (for Curl Flow mode) |
| `antialias` | float | 0.0 | 0.0-10.0 | Antialiasing strength |
| `chromaticDisplace` | float | 0.0 | 0.0-10.0 | Chromatic aberration |
| `distortRotate` | float | 0.0 | 0.0-10.0 | Rotation of displacement field |
| `pixelate` | float | 0.0 | 0.0-10.0 | Pixelation effect |
| `u_mix` | float | 0.5 | 0.0-1.0 | Mix with original |
| `time` | float | 0.0 | N/A | Time for animation |
| `resolution` | vec2 | (640, 480) | N/A | Output resolution |

**Inherited from Effect**: `u_mix`

---

## Public Interface

```python
class DisplacementMapEffect(Effect):
    def __init__(self) -> None: ...
    def set_source(self, source) -> None: ...
    def set_displacement_map(self, map) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int]) -> None: ...
    def process_frame(self, source_frame: np.ndarray, map_frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `source_frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| `map_frame` | `np.ndarray` | Displacement map frame (HxWxC, RGB) |
| **Output** | `np.ndarray` | Displaced output (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_source: Optional[np.ndarray]` — Current source frame
- `_map: Optional[np.ndarray]` — Current displacement map
- `_parameters: dict` — Displacement parameters
- `_shader: ShaderProgram` — Compiled shader
- `_temp_texture: int` — For intermediate rendering

**Per-Frame:**
- Update source and map frames
- Compute displacement vectors based on source mode and channel mapping
- Apply displacement with feedback iteration
- Apply edge darkening
- Return result

**Initialization:**
- Compile shader
- Create temporary textures
- Default parameters: sourceMode=0, channelMapping=0, strength=5.0, iterations=3, feedbackStrength=3.0, edgeDarken=2.0, noiseScale=4.0, noiseOctaves=3, radialCenter=(0.5, 0.5), radialRadius=0.5, edgeThreshold=0.3, curlScale=2.0, antialias=0.0, chromaticDisplace=0.0, distortRotate=0.0, pixelate=0.0
- Initialize `_shader`

**Cleanup:**
- Delete temporary textures
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Shader program | GLSL | vertex + fragment | N/A | Init once |
| Temporary textures (optional) | GL_TEXTURE_2D | GL_RGBA8 | frame size | For intermediate renders |

**Memory Budget (640×480):**
- Shader: ~30-40 KB
- Temporary textures: ~1.8 MB (if used)
- Total: ~1.9 MB (moderate)

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| No source frame | Use black frame | Normal operation |
| No displacement map | Use uniform displacement (0,0) | Normal operation |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Invalid source mode | Clamp to 0-5 or raise `ValueError` | Document valid modes |
| Invalid channel mapping | Clamp to 0-4 or raise `ValueError` | Document valid mappings |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations, texture updates, and shader operations must occur on the thread with the OpenGL context. The effect updates state each frame; concurrent `process_frame()` calls will cause race conditions and corrupted rendering. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Shader execution (displacement, feedback, edge darkening): ~8-15 ms
- Total: ~8-15 ms on GPU (moderate to heavy)

**Optimization Strategies:**
- Reduce iterations (fewer feedback passes)
- Use simpler source modes (Self-Luma vs Curl Flow)
- Disable edge darkening
- Use lower resolution for displacement map
- Simplify channel mapping

---

## Integration Checklist

- [ ] Source frame set and providing video
- [ ] Displacement map frame set and providing map
- [ ] Displacement parameters configured
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_self_luma` | Self-luma mode displaces based on luminance |
| `test_self_rg` | Self-RG mode displaces based on red/green channels |
| `test_noise` | Noise mode creates random displacement |
| `test_radial` | Radial mode displaces from center |
| `test_edge` | Edge mode detects edges and displaces |
| `test_curl_flow` | Curl flow mode creates fluid-like displacement |
| `test_xy_mapping` | XY mapping uses direct coordinates |
| `test_r_to_xy` | R→XY mapping uses red channel |
| `test_radial_mapping` | Radial mapping creates circular displacement |
| `test_twist_mapping` | Twist mapping creates rotational displacement |
| `test_zoom_mapping` | Zoom mapping creates scaling displacement |
| `test_feedback_iteration` | Multiple iterations create complex effects |
| `test_edge_darken` | Edge darkening works on displaced areas |
| `test_strength` | Strength controls displacement magnitude |
| `test_iterations` | Iterations control complexity |
| `test_feedback_strength` | Feedback strength controls iteration intensity |
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
- [ ] Git commit with `[Phase-3] P3-VD72: displacement_map_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vcore/displacement_map.py` — VJLive Original implementation
- `plugins/core/displacement_map/__init__.py` — VJLive-2 implementation
- `plugins/core/displacement_map/plugin.json` — Effect manifest
- `core/effects/__init__.py` — Effect registry

Design decisions inherited:
- Effect name: `displacement_map`
- Inherits from `Effect` (not `DepthEffect`)
- Uses two textures: source and displacement map
- Parameters: `sourceMode`, `channelMapping`, `strength`, `iterations`, `feedbackStrength`, `edgeDarken`, `noiseScale`, `noiseOctaves`, `radialCenter`, `radialRadius`, `edgeThreshold`, `curlScale`, `antialias`, `chromaticDisplace`, `distortRotate`, `pixelate`
- Allocates GL resources: temporary textures for intermediate rendering
- Shader implements displacement mapping with 6 source modes and 5 channel mappings
- Method `_ensure_textures()` creates GPU resources
- Presets: "water_ripple", "heat_distortion", "lens_effect", "flow_field", "edge_warp"

---

## Notes for Implementers

1. **Core Concept**: This effect warps one image using another as a displacement map. The displacement map provides offset vectors for each pixel, creating effects like water ripples, heat distortion, lens effects, and complex spatial transformations.

2. **Source Modes**: The effect supports 6 different ways to generate displacement vectors:
   - **Self-Luma**: Use the source image's luminance as displacement
   - **Self-RG**: Use the source image's red/green channels as displacement
   - **Noise**: Use procedural noise as displacement
   - **Radial**: Create radial displacement from a center point
   - **Edge**: Use edge detection as displacement
   - **Curl Flow**: Use curl noise for fluid-like displacement

3. **Channel Mappings**: The displacement vectors can be mapped in 5 different ways:
   - **XY**: Direct XY coordinates
   - **R→XY**: Red channel to XY displacement
   - **Radial**: Radial displacement based on red channel
   - **Twist**: Twisting displacement based on red channel
   - **Zoom**: Zooming displacement based on red channel

4. **Feedback Iteration**: Multiple passes of displacement create complex, organic effects. Each iteration uses the result of the previous iteration as input.

5. **Edge Darkening**: Areas with high displacement are darkened to create depth and prevent bright artifacts.

6. **Shader Uniforms**:
   ```glsl
   uniform sampler2D tex0;           // Source texture
   uniform sampler2D tex1;           // Displacement map texture
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform int sourceMode;           // 0-5
   uniform int channelMapping;        // 0-4
   uniform float strength;            // 0-10
   uniform int iterations;            // 1-10
   uniform float feedbackStrength;    // 0-10
   uniform float edgeDarken;          // 0-10
   uniform float noiseScale;          // 0-10
   uniform int noiseOctaves;          // 1-8
   uniform vec2 radialCenter;         // 0-1
   uniform float radialRadius;        // 0-10
   uniform float edgeThreshold;       // 0-1
   uniform float curlScale;           // 0-10
   uniform float antialias;           // 0-10
   uniform float chromaticDisplace;   // 0-10
   uniform float distortRotate;       // 0-10
   uniform float pixelate;            // 0-10
   ```

7. **Parameter Mapping** (0-10 → actual):
   - `strength`: 0-10 → 0-1 (divide by 10)
   - `feedbackStrength`: 0-10 → 0-1 (divide by 10)
   - `edgeDarken`: 0-10 → 0-1 (divide by 10)
   - `noiseScale`: 0-10 → scale factor
   - `radialRadius`: 0-10 → radius in pixels
   - `edgeThreshold`: 0-10 → 0-1 (divide by 10)
   - `curlScale`: 0-10 → scale factor
   - `antialias`: 0-10 → 0-1 (divide by 10)
   - `chromaticDisplace`: 0-10 → 0-1 (divide by 10)
   - `distortRotate`: 0-10 → degrees (multiply by 3.6)
   - `pixelate`: 0-10 → pixel size (multiply by 10)

8. **PRESETS**:
   ```python
   PRESETS = {
       "water_ripple": {
           "sourceMode": 0, "channelMapping": 0, "strength": 3.0,
           "iterations": 2, "feedbackStrength": 2.0, "edgeDarken": 1.0,
           "noiseScale": 5.0, "noiseOctaves": 2, "radialCenter": (0.5, 0.5),
           "radialRadius": 2.0, "edgeThreshold": 0.2, "curlScale": 1.0,
           "antialias": 3.0, "chromaticDisplace": 0.0, "distortRotate": 0.0,
           "pixelate": 0.0,
       },
       "heat_distortion": {
           "sourceMode": 2, "channelMapping": 0, "strength": 6.0,
           "iterations": 3, "feedbackStrength": 4.0, "edgeDarken": 3.0,
           "noiseScale": 8.0, "noiseOctaves": 3, "radialCenter": (0.5, 0.5),
           "radialRadius": 3.0, "edgeThreshold": 0.3, "curlScale": 2.0,
           "antialias": 2.0, "chromaticDisplace": 2.0, "distortRotate": 0.0,
           "pixelate": 0.0,
       },
       "lens_effect": {
           "sourceMode": 3, "channelMapping": 4, "strength": 8.0,
           "iterations": 1, "feedbackStrength": 1.0, "edgeDarken": 5.0,
           "noiseScale": 3.0, "noiseOctaves": 1, "radialCenter": (0.5, 0.5),
           "radialRadius": 5.0, "edgeThreshold": 0.1, "curlScale": 0.5,
           "antialias": 4.0, "chromaticDisplace": 5.0, "distortRotate": 0.0,
           "pixelate": 0.0,
       },
       "flow_field": {
           "sourceMode": 5, "channelMapping": 0, "strength": 4.0,
           "iterations": 4, "feedbackStrength": 3.0, "edgeDarken": 2.0,
           "noiseScale": 6.0, "noiseOctaves": 2, "radialCenter": (0.5, 0.5),
           "radialRadius": 2.0, "edgeThreshold": 0.2, "curlScale": 3.0,
           "antialias": 3.0, "chromaticDisplace": 1.0, "distortRotate": 0.0,
           "pixelate": 0.0,
       },
       "edge_warp": {
           "sourceMode": 4, "channelMapping": 0, "strength": 7.0,
           "iterations": 2, "feedbackStrength": 2.5, "edgeDarken": 4.0,
           "noiseScale": 4.0, "noiseOctaves": 2, "radialCenter": (0.5, 0.5),
           "radialRadius": 3.0, "edgeThreshold": 0.4, "curlScale": 1.5,
           "antialias": 3.0, "chromaticDisplace": 0.0, "distortRotate": 0.0,
           "pixelate": 0.0,
       },
   }
   ```

9. **Testing Strategy**:
    - Test with uniform displacement map: should create uniform distortion
    - Test with gradient displacement map: should create smooth distortion
    - Test source modes: each should produce distinct displacement patterns
    - Test channel mappings: each should produce different displacement behaviors
    - Test strength: higher = more distortion
    - Test iterations: more = more complex distortion
    - Test feedback strength: higher = stronger iteration effect
    - Test edge darkening: displaced areas should be darker
    - Test noise scale/octaves: affects noise quality
    - Test radial parameters: affects radial displacement
    - Test edge threshold: affects edge detection sensitivity
    - Test curl scale: affects curl flow quality

10. **Performance**: Moderate — multiple texture fetches and computations. Optimize by reducing iterations and simplifying source modes.

11. **Memory**: Light — only needs two textures (source and map).

12. **Debug Mode**: Visualize displacement vectors, intermediate results, edge detection, etc.

---
-

## References

- Displacement mapping: https://en.wikipedia.org/wiki/Displacement_mapping
- Texture warping: https://en.wikipedia.org/wiki/Warping
- GLSL displacement: https://www.shaderific.com/glsl-functions
- VJLive legacy: `plugins/vcore/displacement_map.py`

---

## Implementation Tips

1. **Full Shader**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;           // Source texture
   uniform sampler2D tex1;           // Displacement map texture
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform int sourceMode;           // 0-5
   uniform int channelMapping;        // 0-4
   uniform float strength;            // 0-10
   uniform int iterations;            // 1-10
   uniform float feedbackStrength;    // 0-10
   uniform float edgeDarken;          // 0-10
   uniform float noiseScale;          // 0-10
   uniform int noiseOctaves;          // 1-8
   uniform vec2 radialCenter;         // 0-1
   uniform float radialRadius;        // 0-10
   uniform float edgeThreshold;       // 0-1
   uniform float curlScale;           // 0-10
   uniform float antialias;           // 0-10
   uniform float chromaticDisplace;   // 0-10
   uniform float distortRotate;       // 0-10
   uniform float pixelate;            // 0-10
   
   // Pseudo-random
   float random(vec2 uv) {
       return fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453);
   }
   
   // Noise (simple)
   float noise(vec2 uv) {
       return random(uv * noiseScale);
   }
   
   // Edge detection (simple Sobel)
   float edge_detect(sampler2D tex, vec2 uv) {
       vec2 texel = 1.0 / resolution;
       float gx = -texture(tex, uv + vec2(-texel.x, -texel.y)).r
                 -2.0*texture(tex, uv + vec2(-texel.x, 0.0)).r
                 -texture(tex, uv + vec2(-texel.x, texel.y)).r
                 +texture(tex, uv + vec2(texel.x, -texel.y)).r
                 +2.0*texture(tex, uv + vec2(texel.x, 0.0)).r
                 +texture(tex, uv + vec2(texel.x, texel.y)).r;
       
       float gy = -texture(tex, uv + vec2(-texel.x, -texel.y)).r
                 -2.0*texture(tex, uv + vec2(0.0, -texel.y)).r
                 -texture(tex, uv + vec2(texel.x, -texel.y)).r
                 +texture(tex, uv + vec2(-texel.x, texel.y)).r
                 +2.0*texture(tex, uv + vec2(0.0, texel.y)).r
                 +texture(tex, uv + vec2(texel.x, texel.y)).r;
       
       return length(vec2(gx, gy));
   }
   
   // Curl noise (simplified)
   vec2 curl_noise(vec2 uv) {
       vec2 p = uv * curlScale;
       float n1 = noise(p);
       float n2 = noise(p + vec2(1.0, 0.0));
       float n3 = noise(p + vec2(0.0, 1.0));
       return vec2(n2 - n1, n3 - n1);
   }
   
   void main() {
       vec2 uv = gl_FragCoord.xy / resolution;
       
       // Get displacement from map
       vec3 disp_map = texture(tex1, uv).rgb;
       
       // Compute displacement based on source mode
       vec2 displacement = vec2(0.0);
       
       if (sourceMode == 0) { // Self-Luma
           vec3 source = texture(tex0, uv).rgb;
           float luma = dot(source, vec3(0.299, 0.587, 0.114));
           displacement = vec2(luma, luma) * strength * 0.1;
       }
       else if (sourceMode == 1) { // Self-RG
           vec3 source = texture(tex0, uv).rgb;
           displacement = vec2(source.r, source.g) * strength * 0.1;
       }
       else if (sourceMode == 2) { // Noise
           displacement = vec2(noise(uv), noise(uv + vec2(123.45, 67.89))) * strength * 0.1;
       }
       else if (sourceMode == 3) { // Radial
           vec2 to_center = uv - radialCenter;
           float dist = length(to_center);
           if (dist > 0.0) {
               vec2 dir = to_center / dist;
               displacement = dir * dist * radialRadius * strength * 0.1;
           }
       }
       else if (sourceMode == 4) { // Edge
           float edge = edge_detect(tex0, uv);
           if (edge > edgeThreshold) {
               displacement = vec2(edge, edge) * strength * 0.1;
           }
       }
       else if (sourceMode == 5) { // Curl Flow
           displacement = curl_noise(uv) * strength * 0.1;
       }
       
       // Apply channel mapping
       if (channelMapping == 1) { // R→XY
           displacement = vec2(disp_map.r, disp_map.r) * strength * 0.1;
       }
       else if (channelMapping == 2) { // Radial
           vec2 to_center = uv - radialCenter;
           float dist = length(to_center);
           if (dist > 0.0) {
               vec2 dir = to_center / dist;
               displacement = dir * disp_map.r * radialRadius * strength * 0.1;
           }
       }
       else if (channelMapping == 3) { // Twist
           float angle = disp_map.r * 6.28; // 0-2π
           displacement = vec2(cos(angle), sin(angle)) * strength * 0.1;
       }
       else if (channelMapping == 4) { // Zoom
           vec2 to_center = uv - radialCenter;
           float dist = length(to_center);
           if (dist > 0.0) {
               vec2 dir = to_center / dist;
               displacement = dir * disp_map.r * radialRadius * strength * 0.1;
           }
       }
       
       // Apply feedback iteration
       vec2 final_uv = uv;
       for (int i = 0; i < iterations; i++) {
           vec2 disp = texture(tex1, final_uv).rg;
           final_uv = final_uv + disp * feedbackStrength * 0.1;
       }
       
       // Sample source with antialiasing
       vec3 color = texture(tex0, final_uv).rgb;
       
       // Edge darkening
       if (edgeDarken > 0.0) {
           float disp_mag = length(displacement) / strength;
           color *= 1.0 - disp_mag * edgeDarken * 0.1;
       }
       
       // Chromatic aberration
       if (chromaticDisplace > 0.0) {
           vec2 r_uv = final_uv + vec2(chromaticDisplace * 0.001, 0.0);
           vec2 b_uv = final_uv - vec2(chromaticDisplace * 0.001, 0.0);
           vec3 r = texture(tex0, r_uv).rgb;
           vec3 b = texture(tex0, b_uv).rgb;
           color.r = r.r;
           color.b = b.b;
       }
       
       // Pixelation
       if (pixelate > 0.0) {
           vec2 pixel_size = resolution / (pixelate * 10.0);
           vec2 pixel_uv = floor(final_uv * pixel_size) / pixel_size;
           color = texture(tex0, pixel_uv).rgb;
       }
       
       fragColor = mix(texture(tex0, uv), vec4(color, 1.0), u_mix);
   }
   ```

2. **Python Implementation**:
   ```python
   class DisplacementMapEffect(Effect):
       def __init__(self):
           super().__init__("displacement_map", DISPLACEMENT_VERTEX, DISPLACEMENT_FRAGMENT)
           
           self.source = None
           self.displacement_map = None
           
           self.parameters = {
               'sourceMode': 0,
               'channelMapping': 0,
               'strength': 5.0,
               'iterations': 3,
               'feedbackStrength': 3.0,
               'edgeDarken': 2.0,
               'noiseScale': 4.0,
               'noiseOctaves': 3,
               'radialCenter': (0.5, 0.5),
               'radialRadius': 0.5,
               'edgeThreshold': 0.3,
               'curlScale': 2.0,
               'antialias': 0.0,
               'chromaticDisplace': 0.0,
               'distortRotate': 0.0,
               'pixelate': 0.0,
           }
           
           self.shader = None
       
       def set_source(self, source):
           """Set source video frame."""
           self.source = source
       
       def set_displacement_map(self, map):
           """Set displacement map frame."""
           self.displacement_map = map
       
       def process_frame(self, source_frame, map_frame):
           h, w = source_frame.shape[:2]
           
           # Update textures
           glBindTexture(GL_TEXTURE_2D, self.source_texture)
           glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, source_frame)
           
           glBindTexture(GL_TEXTURE_2D, self.map_texture)
           glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, map_frame)
           
           # Render
           glBindFramebuffer(GL_FRAMEBUFFER, 0)
           
           self.shader.use()
           self._apply_uniforms(time, (w, h))
           
           glActiveTexture(GL_TEXTURE0)
           glBindTexture(GL_TEXTURE_2D, self.source_texture)
           glUniform1i(glGetUniformLocation(self.shader.program, "tex0"), 0)
           
           glActiveTexture(GL_TEXTURE1)
           glBindTexture(GL_TEXTURE_2D, self.map_texture)
           glUniform1i(glGetUniformLocation(self.shader.program, "tex1"), 1)
           
           draw_fullscreen_quad()
           
           result = self._read_pixels()
           return result
   ```

3. **Source Modes**: Each source mode generates displacement vectors differently:
   - **Self-Luma**: Uses the source image's brightness as displacement
   - **Self-RG**: Uses the source image's red/green channels as displacement
   - **Noise**: Uses procedural noise for random displacement
   - **Radial**: Creates displacement radiating from a center point
   - **Edge**: Uses edge detection to create displacement along edges
   - **Curl Flow**: Uses curl noise for fluid-like displacement

4. **Channel Mappings**: Each channel mapping interprets the displacement map differently:
   - **XY**: Direct XY coordinates from the map
   - **R→XY**: Red channel controls both X and Y displacement
   - **Radial**: Red channel controls radial displacement from center
   - **Twist**: Red channel controls rotational displacement
   - **Zoom**: Red channel controls scaling displacement

5. **Feedback Iteration**: Multiple passes of displacement create complex, organic effects. Each iteration uses the result of the previous iteration.

6. **Edge Darkening**: Areas with high displacement are darkened to create depth and prevent bright artifacts.

7. **Chromatic Aberration**: Simulates lens chromatic aberration by slightly displacing red and blue channels.

8. **Pixelation**: Simulates pixelation by sampling at lower resolution.

9. **Performance**: Moderate — multiple texture fetches and computations. Optimize by reducing iterations and simplifying source modes.

10. **Testing**: Use simple patterns (gradients, checkerboards) and displacement maps (gradients, noise). Verify:
    - Self-luma creates displacement based on brightness
    - Self-RG creates displacement based on color
    - Noise creates random displacement
    - Radial creates circular displacement
    - Edge creates displacement along edges
    - Channel mappings work correctly
    - Feedback iteration creates complex effects
    - Edge darkening works
    - Chromatic aberration works
    - Pixelation works

11. **Future Extensions**:
    - Add 3D displacement
    - Add audio reactivity
    - Add multiple displacement layers
    - Add displacement animation

---

## Conclusion

The DisplacementMapEffect is a fundamental image warping technique that uses one signal to control how another is warped through space. With 6 source modes, 5 channel mappings, and feedback iteration, it can create everything from subtle texture deformations to dramatic spatial transformations. Essential for creating effects like water ripples, heat distortion, lens effects, and complex spatial manipulations, this effect is a powerful tool for creating organic, fluid distortions in VJ performances.

---
