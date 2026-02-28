# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD49_Depth_Fracture_Datamosh.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD49 — DepthFractureDatamoshEffect

## Description

The DepthFractureDatamoshEffect detects depth discontinuities to create dynamic fracture maps where datamosh artifacts concentrate and violently bleed through. Depth edges physically become neon cracks in the image, forcing pixel data from adjacent frames to leak out, creating a shattered-glass-meets-datamosh aesthetic. Fractures accumulate over time with configurable decay, expanding into tectonic rifts while color channels completely separate prismatically along fracture boundaries. Audio reactivity drives bleed amount, glow intensity, and displacement strength.

This effect is ideal for creating intense, glitchy visual destruction where depth edges become fault lines. It's perfect for VJ performances that need high-impact, chaotic visuals that respond to both depth and audio. The effect combines edge detection, temporal persistence, chromatic aberration, and datamosh techniques into a cohesive, configurable package.

## What This Module Does

- Detects depth discontinuities (edges) to create fracture maps
- Generates datamosh artifacts that concentrate along fracture lines
- Implements chromatic separation (RGB channel splitting) along fractures
- Supports temporal persistence (fractures accumulate over time)
- Adds glow to fracture lines for neon effect
- Audio-reactive: responds to audio for bleed, glow, displacement
- GPU-accelerated with fragment shader

## What This Module Does NOT Do

- Does NOT create fractures from image edges (only depth edges)
- Does NOT provide CPU fallback (GPU required)
- Does NOT implement true 3D fracture simulation (2D screen-space)
- Does NOT store persistent state across sessions
- Does NOT handle audio analysis internally (expects audio_reactor)
- Does NOT support multiple fracture maps (single map)

---

## Detailed Behavior

### Fracture Detection Pipeline

1. **Compute depth gradient**: Detect edges in depth map:
   ```
   grad_x = Sobel(depth, axis=1)
   grad_y = Sobel(depth, axis=0)
   grad_mag = sqrt(grad_x² + grad_y²)
   ```

2. **Threshold to fracture map**: Create binary mask of fracture regions:
   ```
   fracture_map = grad_mag > edge_threshold
   ```

3. **Expand fractures**: Dilate fracture map to create wider cracks:
   ```
   fracture_map = dilate(fracture_map, kernel_size)
   ```

4. **Generate datamosh artifacts**: At fracture locations, introduce pixel displacement:
   ```
   displacement = random_direction() * bleed_amount * audio_reactivity
   ```

5. **Chromatic separation**: Split RGB channels along fractures:
   ```
   r_channel = shift(original.r, +chromatic_offset)
   g_channel = shift(original.g, 0)
   b_channel = shift(original.b, -chromatic_offset)
   ```

6. **Temporal persistence**: Blend current fractures with previous frame:
   ```
   fracture_map = mix(current_fracture, previous_fracture, fracture_decay)
   ```

7. **Glow**: Add neon glow to fracture lines:
   ```
   glow = blur(fracture_map, glow_radius) * glow_intensity
   ```

8. **Composite**: Combine original, displaced, and glow:
   ```
   result = original + displacement + glow
   ```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `edgeThreshold` | float | 0.1 | 0.0-10.0 | Depth gradient threshold for fracture detection |
| `bleedAmount` | float | 5.0 | 0.0-10.0 | How far pixels bleed along fractures |
| `chromaticOffset` | float | 3.0 | 0.0-10.0 | RGB channel separation distance |
| `fractureDecay` | float | 0.9 | 0.0-10.0 | Temporal decay (lower = fractures persist longer) |
| `glowIntensity` | float | 5.0 | 0.0-10.0 | Brightness of fracture glow |
| `glowRadius` | float | 2.0 | 1.0-10.0 | Blur radius for glow effect |
| `displacementMode` | int | 0 | 0-2 | 0=random, 1=directional, 2=spiral |
| `audioReactivity` | float | 5.0 | 0.0-10.0 | How strongly audio affects effect |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class DepthFractureDatamoshEffect(Effect):
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
| `audio_reactor` | AudioReactor (optional) | Audio analysis object for reactivity |
| **Output** | `np.ndarray` | Fracture datamosh frame (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Latest depth frame
- `_depth_texture: int` — GL texture for depth data
- `_parameters: dict` — Effect parameters
- `_shader: ShaderProgram` — Compiled shader
- `_previous_fracture_map: Optional[np.ndarray]` — For temporal persistence
- `_fracture_texture: int` — GL texture for fracture map (optional)

**Per-Frame:**
- Update depth data from source
- Compute depth gradient and fracture map
- Apply temporal decay (blend with previous)
- Generate displacement vectors
- Apply chromatic separation
- Add glow
- Composite with original frame
- Store current fracture map for next frame

**Initialization:**
- Create depth texture (lazy)
- Create fracture texture (if needed)
- Compile shader
- Default parameters from PRESETS (e.g., "hairline_cracks")

**Cleanup:**
- Delete depth texture
- Delete fracture texture (if created)
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_RED, GL_UNSIGNED_BYTE | depth_frame size | Updated each frame |
| Fracture texture (optional) | GL_TEXTURE_2D | GL_R8 | frame size | Updated each frame |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Depth texture: 307,200 bytes
- Fracture texture: 640×480×1 = 307,200 bytes (if used)
- Shader: ~10-50 KB
- Total: ~0.5-1 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | Skip fracture detection, render original | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Previous frame missing | Use current fracture map only | Normal first frame |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and buffer updates must occur on the thread with the OpenGL context. The depth texture and fracture map are updated each frame, and the shader is used for rendering, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth gradient computation (CPU): ~2-4 ms
- Fracture map generation: ~1-2 ms
- Displacement and chromatic separation (GPU): ~2-4 ms
- Glow blur (GPU): ~1-2 ms
- Total: ~6-12 ms on CPU+GPU

**Optimization Strategies:**
- Compute depth gradient on GPU (in shader)
- Reduce fracture map resolution
- Use simpler blur for glow (separable)
- Cache depth gradient if depth hasn't changed
- Reduce `glowRadius` for faster blur
- Implement in compute shader for better parallelism

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Fracture parameters configured (threshold, bleed, chromatic, decay)
- [ ] Glow parameters tuned (intensity, radius)
- [ ] Displacement mode selected
- [ ] Audio reactivity configured (if used)
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | Parameters can be set and clamped |
| `test_get_parameter` | Parameters can be retrieved |
| `test_depth_gradient` | Gradient correctly detects depth edges |
| `test_fracture_map` | Threshold creates binary fracture mask |
| `test_bleed_amount` | Displacement magnitude controlled by bleed |
| `test_chromatic_separation` | RGB channels split along fractures |
| `test_temporal_decay` | Fractures persist/decay over time |
| `test_glow` | Glow adds brightness to fractures |
| `test_displacement_modes` | Different modes produce distinct patterns |
| `test_audio_reactivity` | Audio influences bleed/glow/displacement |
| `test_process_frame_no_depth` | Renders original when no depth |
| `test_process_frame_with_depth` | Fractures appear at depth edges |
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
- [ ] Git commit with `[Phase-3] P3-VD49: depth_fracture_datamosh_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_fracture_datamosh.py` — VJLive Original implementation
- `plugins/core/depth_fracture_datamosh/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthFractureDatamoshEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_fracture_datamosh`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for fracture detection
- Parameters: `edgeThreshold`, `bleedAmount`, `chromaticOffset`, `fractureDecay`, `glowIntensity`, `glowRadius`, `displacementMode`, `audioReactivity`
- Allocates GL resources: depth texture (and optionally fracture texture)
- Shader implements fracture detection, displacement, chromatic separation, glow
- Supports temporal persistence via previous frame blending

---

## Notes for Implementers

1. **Depth Edge Detection**: Compute gradient on CPU or GPU:
   ```python
   # CPU approach (OpenCV)
   grad_x = cv2.Sobel(depth, cv2.CV_32F, 1, 0, ksize=3)
   grad_y = cv2.Sobel(depth, cv2.CV_32F, 0, 1, ksize=3)
   grad_mag = np.sqrt(grad_x**2 + grad_y**2)
   fracture_map = (grad_mag > edge_threshold).astype(np.float32)
   ```

2. **Fracture Expansion**: Dilate the fracture map to make cracks wider:
   ```python
   kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
   fracture_map = cv2.dilate(fracture_map, kernel)
   ```

3. **Temporal Persistence**: Blend with previous frame:
   ```python
   if self._previous_fracture is not None:
       fracture_map = cv2.addWeighted(fracture_map, 1.0 - fracture_decay,
                                      self._previous_fracture, fracture_decay, 0)
   self._previous_fracture = fracture_map
   ```

4. **Displacement Vectors**: Generate random or structured displacement:
   ```python
   # Random displacement
   displacement = np.random.randn(h, w, 2) * bleed_amount
   
   # Directional (e.g., outward from center)
   center = np.array([w/2, h/2])
   grid = np.indices((h, w)).transpose(1,2,0)[..., ::-1]  # (y,x) -> (x,y)
   direction = grid - center
   direction = direction / (np.linalg.norm(direction, axis=2, keepdims=True) + 1e-6)
   displacement = direction * bleed_amount
   
   # Spiral displacement
   angle = np.arctan2(grid[...,1] - h/2, grid[...,0] - w/2)
   spiral = np.stack([np.cos(angle + np.pi/2), np.sin(angle + np.pi/2)], axis=2)
   displacement = spiral * bleed_amount
   ```

5. **Chromatic Separation**: Apply different displacements to each channel:
   ```python
   r_offset = displacement * chromatic_offset
   g_offset = displacement * 0.0
   b_offset = displacement * (-chromatic_offset)
   
   # Remap image with offsets
   r_channel = remap(frame[...,0], r_offset)
   g_channel = remap(frame[...,1], g_offset)
   b_channel = remap(frame[...,2], b_offset)
   ```

6. **Glow**: Blur the fracture map and add to image:
   ```python
   glow = cv2.GaussianBlur(fracture_map, (glow_radius*2+1, glow_radius*2+1), 0)
   glow_color = np.array([0.0, 1.0, 0.0])  # Green neon, for example
   result = frame + glow[..., np.newaxis] * glow_color * glow_intensity
   ```

7. **Shader Integration**: The shader should:
   - Sample depth texture
   - Compute gradient (or receive fracture map from CPU)
   - Apply displacement with chromatic separation
   - Add glow
   - Mix with original

8. **Audio Reactivity**: If `audio_reactor` provided, modulate parameters:
   ```python
   if audio_reactor:
       bass = audio_reactor.get_low_freq()
       treble = audio_reactor.get_high_freq()
       bleed = base_bleed * (1.0 + bass * audio_reactivity)
       glow = base_glow * (1.0 + treble * audio_reactivity)
   ```

9. **PRESETS**: Define useful configurations:
   ```python
   PRESETS = {
       "hairline_cracks": {
           "edgeThreshold": 0.1, "bleedAmount": 2.0, "chromaticOffset": 1.0,
           "fractureDecay": 0.9, "glowIntensity": 3.0, "glowRadius": 1.0,
           "displacementMode": 0, "audioReactivity": 2.0,
       },
       "shattered_glass": {
           "edgeThreshold": 0.05, "bleedAmount": 8.0, "chromaticOffset": 5.0,
           "fractureDecay": 0.7, "glowIntensity": 8.0, "glowRadius": 3.0,
           "displacementMode": 0, "audioReactivity": 7.0,
       },
       "tectonic_rifts": {
           "edgeThreshold": 0.2, "bleedAmount": 5.0, "chromaticOffset": 2.0,
           "fractureDecay": 0.5, "glowIntensity": 6.0, "glowRadius": 2.0,
           "displacementMode": 1, "audioReactivity": 5.0,
       },
   }
   ```

10. **Performance**: The effect is computationally intensive. Consider:
    - Computing gradient on GPU (in shader) to avoid CPU-GPU transfer
    - Using lower resolution for fracture map
    - Reducing `glowRadius` for faster blur
    - Caching fracture map if depth unchanged
    - Using compute shader for parallel processing

11. **Testing**: Create depth with sharp edges (e.g., cube, steps) and verify:
    - Fractures appear at depth discontinuities
    - Bleed amount controls displacement magnitude
    - Chromatic offset splits RGB channels
    - Temporal decay causes fractures to fade over time
    - Glow adds colored outline to fractures
    - Audio reactivity modulates effect intensity

12. **Future Extensions**:
    - Add depth-based fracture strength (deeper edges = bigger fractures)
    - Add multiple fracture layers
    - Add fracture propagation (fractures grow over time)
    - Add sound-triggered fracture events
    - Add export/import of fracture maps

---

## Easter Egg Idea

When `edgeThreshold` is set exactly to 6.66, `bleedAmount` to exactly 6.66, `chromaticOffset` to exactly 6.66, `fractureDecay` to exactly 0.666, and `glowIntensity` to exactly 6.66, and the depth map contains a perfect dodecahedron, the fractures spontaneously arrange themselves into a "sacred geometry" pattern where the cracks form a perfect pentagram for exactly 6.66 seconds, causing the datamosh to follow a golden ratio spiral. VJs can feel this as a "harmonic fracture" that resonates with the underlying structure of reality.

---

## References

- Edge detection: https://en.wikipedia.org/wiki/Edge_detection
- Datamosh: https://en.wikipedia.org/wiki/Datamosh
- Chromatic aberration: https://en.wikipedia.org/wiki/Chromatic_aberration
- VJLive legacy: `plugins/vdepth/depth_fracture_datamosh.py`

---

## Implementation Tips

1. **Shader Structure**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;        // Current frame
   uniform sampler2D depth_tex;   // Depth texture
   uniform sampler2D texPrev;     // Previous frame (for temporal)
   uniform vec2 resolution;
   uniform float u_mix;
   
   uniform float edgeThreshold;
   uniform float bleedAmount;
   uniform float chromaticOffset;
   uniform float fractureDecay;
   uniform float glowIntensity;
   uniform float glowRadius;
   uniform int displacementMode;
   uniform float audioReactivity;
   uniform float time;
   
   // Random function
   float random(vec2 st) {
       return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
   }
   
   void main() {
       vec4 current = texture(tex0, uv);
       float depth = texture(depth_tex, uv).r;
       
       // Compute gradient (simple Sobel)
       vec2 texel = 1.0 / resolution;
       float d00 = texture(depth_tex, uv + vec2(-texel.x, -texel.y)).r;
       float d01 = texture(depth_tex, uv + vec2(0.0, -texel.y)).r;
       float d02 = texture(depth_tex, uv + vec2(texel.x, -texel.y)).r;
       float d10 = texture(depth_tex, uv + vec2(-texel.x, 0.0)).r;
       float d12 = texture(depth_tex, uv + vec2(texel.x, 0.0)).r;
       float d20 = texture(depth_tex, uv + vec2(-texel.x, texel.y)).r;
       float d21 = texture(depth_tex, uv + vec2(0.0, texel.y)).r;
       float d22 = texture(depth_tex, uv + vec2(texel.x, texel.y)).r;
       
       float gx = -d00 - 2.0*d10 - d20 + d02 + 2.0*d12 + d22;
       float gy = -d00 - 2.0*d01 - d02 + d20 + 2.0*d21 + d22;
       float grad_mag = sqrt(gx*gx + gy*gy);
       
       // Fracture map
       float fracture = step(edgeThreshold, grad_mag);
       
       // Temporal persistence
       vec4 prev = texture(texPrev, uv);
       fracture = mix(fracture, prev.r, fractureDecay);
       
       // Displacement
       vec2 offset = vec2(0.0);
       if (displacementMode == 0) {
           // Random
           float rand = random(uv + time);
           angle = rand * 6.28318;
           offset = bleedAmount * vec2(cos(angle), sin(angle)) / resolution;
       } else if (displacementMode == 1) {
           // Directional (outward from center)
           vec2 center = resolution * 0.5;
           vec2 dir = normalize(uv * resolution - center);
           offset = dir * bleedAmount / resolution;
       } else if (displacementMode == 2) {
           // Spiral
           vec2 center = resolution * 0.5;
           vec2 pos = uv * resolution - center;
           float angle = atan(pos.y, pos.x) + 1.5708;  // +90°
           vec2 dir = vec2(cos(angle), sin(angle));
           offset = dir * bleedAmount / resolution;
       }
       
       // Chromatic separation
       float r = texture(tex0, uv + offset * chromaticOffset).r;
       float g = texture(tex0, uv).g;
       float b = texture(tex0, uv - offset * chromaticOffset).b;
       vec4 displaced = vec4(r, g, b, 1.0);
       
       // Glow
       float glow = 0.0;
       if (glowRadius > 0.0) {
           // Simple box blur for glow
           int samples = int(glowRadius);
           for (int i = -samples; i <= samples; i++) {
               for (int j = -samples; j <= samples; j++) {
                   vec2 off = vec2(float(i), float(j)) / resolution;
                   glow += texture(depth_tex, uv + off).r;
               }
           }
           glow /= float((2*samples+1)*(2*samples+1));
           glow = step(edgeThreshold, glow) * glowIntensity;
       }
       
       vec3 glow_color = vec3(0.0, 1.0, 1.0);  // Cyan neon
       vec3 result = mix(current.rgb, displaced.rgb, fracture);
       result += glow * glow_color;
       
       fragColor = mix(current, vec4(result, 1.0), u_mix);
   }
   ```

2. **CPU vs GPU**: The legacy likely computes fracture on CPU and passes as texture. Consider:
   - CPU: More flexible, easier to debug, but slower due to transfer
   - GPU: Faster, but more complex shader
   Choose based on performance needs.

3. **Fracture Texture**: If computing on CPU, upload fracture map as texture:
   ```python
   fracture_uint8 = (fracture_map * 255).astype(np.uint8)
   glTexImage2D(GL_TEXTURE_2D, 0, GL_R8, w, h, 0, GL_RED, GL_UNSIGNED_BYTE, fracture_uint8)
   ```

4. **Audio Reactivity**: The `audioReactivity` parameter scales how much audio affects:
   - `bleedAmount` *= (1 + audio_level * audioReactivity / 10.0)
   - `glowIntensity` *= (1 + audio_level * audioReactivity / 10.0)
   - `displacement` magnitude *= (1 + audio_level * audioReactivity / 10.0)

5. **Temporal Decay**: The `fractureDecay` parameter controls how fast fractures fade:
   - 0.0 = immediate fade (no persistence)
   - 1.0 = infinite persistence (fractures never fade)
   - Typical: 0.7-0.95

6. **Displacement Modes**:
   - **Random (0)**: Fractures bleed in random directions (chaotic)
   - **Directional (1)**: Fractures bleed outward from center (expanding)
   - **Spiral (2)**: Fractures bleed in spiral pattern (vortex)

7. **Glow Implementation**: The glow should be applied to fracture lines only. Use the fracture map as mask:
   ```glsl
   float glow = blur(fracture_map, glowRadius) * glowIntensity;
   result += glow * glow_color;
   ```

8. **Performance**: The biggest cost is depth gradient computation. If doing on CPU, consider:
   - Using Sobel with smaller kernel (3×3 is typical)
   - Downsampling depth before gradient
   - Computing gradient every N frames if depth stable

9. **Testing**: Use a depth image with clear edges (e.g., a step function). Verify:
   - Edges are detected correctly
   - Fractures follow depth discontinuities
   - Bleed creates displacement along fractures
   - Chromatic offset splits colors
   - Temporal decay causes fractures to fade

10. **Shader Optimization**: If doing gradient in shader, use derivatives:
    ```glsl
    float d = texture(depth_tex, uv).r;
    float dx = dFdx(d);
    float dy = dFdy(d);
    float grad_mag = sqrt(dx*dx + dy*dy);
    ```

---

## Conclusion

The DepthFractureDatamoshEffect creates intense, chaotic visual destruction by detecting depth edges and using them as fault lines for datamosh artifacts. With chromatic separation, temporal persistence, neon glow, and audio reactivity, it produces a shattered-glass aesthetic that is both visually striking and highly configurable. This effect is a powerful tool for creating high-impact, glitchy visuals in VJ performances.

---
>>>>>>> REPLACE