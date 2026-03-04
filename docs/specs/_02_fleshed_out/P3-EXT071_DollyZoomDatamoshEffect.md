# P3-EXT071 DollyZoomDatamoshEffect

**File naming:** `docs/specs/P3-EXT071_DollyZoomDatamoshEffect.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT071 — DollyZoomDatamoshEffect

**What This Module Does**

DollyZoomDatamoshEffect simulates the classic "Vertigo" camera trick (dolly zoom) pioneered by Alfred Hitchcock. This cinematic effect creates a warping perspective where the foreground subject remains at a stable scale while the background dramatically zooms in or out, producing a disorienting sensation of space expanding and contracting. The effect uses depth data to isolate the subject and apply differential scaling based on depth, creating a true stereoscopic dolly zoom effect that would be impossible with simple 2D warping.

Key features:
- **Vertigo effect**: Foreground locked, background zooms inversely
- **Depth-based parallax**: Uses depth map to determine which pixels are "subject" vs "background"
- **Focus breath**: Rhythmic field-of-view oscillation
- **Lens distortion**: Barrel/pincushion distortion that pulses with the zoom
- **Film grain**: 3AM gritty texture overlay
- **Chromatic aberration**: Color fringing at edges intensifies with distortion
- **Dizzy spin**: Optional rotation for enhanced disorientation
- **Vignette**: Dark corners to focus attention
- **Focal instability**: Jitter in focus point for organic feel
- **Motion trails**: Feedback loop for ghostly persistence
- **Panic zoom**: Fast snap zooms for jump-scare effects
- **Dual video input**: Support for two video sources (tex0 = Video A, tex1 = Video B)

**What This Module Does NOT Do**

- True 3D camera projection (uses depth-based 2D warping approximation)
- Physical lens simulation (stylized approximation only)
- Multi-pass depth reconstruction (single-pass effect)
- Audio-reactive depth analysis (uses simple band mapping)
- Real-time subject tracking (relies on depth threshold)

---

## Detailed Behavior and Parameter Interactions

### Core Parameters

| Parameter | Range | Physical Range | Description |
|-----------|-------|----------------|-------------|
| `zoom_intensity` | 0-10 | 0.0 to 10.0 | How extreme the dolly zoom effect is. 0 = no zoom, 10 = maximum warping |
| `subject_dist` | 0-10 | 0.0 to 1.0 (normalized depth) | Depth threshold for subject isolation. Pixels at this depth remain scale 1.0 |
| `breath_speed` | 0-10 | 0.1 to 5.0 Hz | Speed of the zoom oscillation cycle |
| `lens_distort` | 0-10 | -2.0 to 2.0 | Barrel (positive) or pincushion (negative) distortion amount |
| `film_grain` | 0-10 | 0.0 to 1.0 | Film grain intensity |
| `chromatic_ab` | 0-10 | 0.0 to 1.0 | Chromatic aberration strength at edges |
| `dizzy_spin` | 0-10 | 0.0 to 1.0 | Rotation amplitude during zoom cycle |
| `vignette` | 0-10 | 0.0 to 1.0 | Vignette darkness |
| `focal_instability` | 0-10 | 0.0 to 1.0 | Jitter in focus point (random walk) |
| `depth_cut` | 0-10 | 0.0 to 1.0 | Sharpness of subject isolation (smoothstep width) |
| `motion_trails` | 0-10 | 0.0 to 1.0 | Feedback amount from previous frame |
| `panic_zoom` | 0-10 | 0.0 to 1.0 | Fast snap zoom intensity |

### Parameter Interactions

1. **Zoom Intensity + Subject Distance**: These parameters work together to control the vertigo effect. Higher `zoom_intensity` creates more dramatic warping. `subject_dist` determines which depth layer remains stable; setting it to match your subject's depth keeps them locked while the background warps.

2. **Breath Speed + Zoom Intensity**: The `breath_speed` controls how fast the zoom oscillates, while `zoom_intensity` controls the amplitude. Fast breath with high intensity creates a dizzying, nauseating effect; slow breath with moderate intensity creates a more subtle, cinematic vertigo.

3. **Lens Distortion + Chromatic Aberration**: These parameters are modulated by the `breath` cycle, meaning they pulse in sync with the zoom. Higher `lens_distort` creates more barrel/pincushion warping that intensifies at zoom extremes. `chromatic_ab` adds color fringing that scales with the distortion amount.

4. **Dizzy Spin + Focal Instability**: Both add rotational jitter. `dizzy_spin` creates a smooth sinusoidal rotation synced to the breath cycle; `focal_instability` adds random jitter to the UV coordinates, creating an unsteady, hand-held camera feel.

5. **Motion Trails + Panic Zoom**: `motion_trails` mixes in the previous frame, creating ghostly persistence. `panic_zoom` adds fast snap zooms on top of the smooth breath cycle. Combining them creates a chaotic, glitchy effect suitable for jump-scare moments.

6. **Depth Cut + Subject Distance**: `depth_cut` controls the transition width between subject and background. Low values create a sharp binary mask; high values create a soft gradient. This affects how smoothly the subject blends into the warped background.

7. **Film Grain + Vignette**: These are post-processing effects applied after the main dolly zoom. They add texture and darken corners, respectively, enhancing the cinematic, film-noir aesthetic.

### Audio Reactivity

The effect supports audio reactivity through the `audio_reactor` parameter:
- `zoom_intensity` modulated by bass frequencies
- `panic_zoom` modulated by kick drum energy
- `focal_instability` modulated by high frequencies
- `breath_speed` modulated by mid frequencies

Audio reactivity allows the dolly zoom to pulse in sync with music, creating dynamic visual responses to rhythm.

---

## Public Interface

### Constructor
```python
DollyZoomDatamoshEffect(name: str = 'dolly_zoom_datamosh')
```
Initializes the effect with default parameters and loads the FRAGMENT shader.

### Methods

#### `set_parameter(name: str, value: float)`
Sets a parameter value. Parameters are mapped from 0-10 UI range to shader-specific ranges using `_map_param()`.

#### `get_parameter(name: str) -> float`
Returns the current value of a parameter.

#### `apply_uniforms(time: float, resolution: tuple, audio_reactor=None, semantic_layer=None)`
Applies uniforms to the shader, including:
- Time-based breath cycle
- Resolution for texel calculations
- Audio reactor data (if provided) for reactive modulation
- All dolly zoom parameters

#### `get_state() -> Dict[str, Any]`
Returns the current state as a dictionary with name, enabled flag, and parameters.

---

## Inputs and Outputs

### Inputs
- **Texture0 (tex0)**: Video A (sampler2D)
- **Texture1 (tex1)**: Video B (sampler2D) - optional dual input
- **Texture2 (depth_tex)**: Depth map (sampler2D, single-channel)
- **TexturePrev (texPrev)**: Previous frame (sampler2D) - for motion trails
- **Time**: Current time (float)
- **Resolution**: Output resolution (vec2)
- **AudioReactor**: Audio analysis data (optional)

### Outputs
- **FragColor**: Dithered output color (vec4)

### Data Flow
```
Video A/B → Dolly Zoom Warp → Chromatic Aberration → Film Grain → Motion Trails → Vignette → Output
     ↓
  Depth Map → Subject Isolation → Parallax Scaling
     ↓
  Audio → Parameter Modulation
```

---

## Edge Cases and Error Handling

### Depth Edge Cases

1. **Missing Depth Data**:
   - If `depth_tex` is not bound or returns 0, the effect falls back to uniform scaling (no parallax)
   - The shader checks `texture(depth_tex, uv).r` but doesn't validate; invalid depth yields undefined behavior
   - **Recommendation**: Add depth validation in `apply_uniforms()` and set a default depth (0.5) if missing

2. **Depth Range**:
   - Assumes depth in [0, 1] normalized range
   - `subject_dist` is also normalized [0, 1]
   - If depth values exceed 1.0, they are clamped implicitly by texture sampling
   - If depth values are inverted (far=0, near=1), the effect inverts (subject becomes background)

3. **Depth Cutoff**:
   - `depth_cut` maps to smoothstep width; if too small (0), creates hard binary mask with aliasing
   - If too large (>1.0), creates overly soft transition where subject is never fully locked

### Mathematical Edge Cases

1. **Division by Zero**:
   - No explicit divisions in shader, but `scale = 1.0 + depthDiff * (zoom - 1.0) * 2.0` can produce negative scales if `depthDiff` is negative and `zoom < 1.0`
   - Negative scale inverts the image; this is intentional for full zoom range but may produce unexpected results
   - **Mitigation**: Clamp `zoom` to [0.5, 2.0] before scaling, or clamp `scale` to positive values

2. **Lens Distortion**:
   - `scale *= 1.0 + rsq * u_lens_distort * breath` can produce extreme distortion at corners if `u_lens_distort` is large
   - `rsq` (radius squared) can exceed 1.0 at UV corners (max = 0.5 at corner (0,0) or (1,1))
   - No clamping; extreme values may cause texture coordinate overflow (warpUV outside [0,1])
   - **Mitigation**: Clamp `warpUV` after all transformations

3. **Chromatic Aberration**:
   - `off = u_chromatic_ab * 0.01 * length(p)` - if `u_chromatic_ab` is 10 (mapped to 1.0), offset = 0.01 * radius
   - At corner radius ≈ 0.707, offset ≈ 0.007 pixels - negligible
   - The mapping may be too conservative; consider scaling by resolution

4. **Focal Instability**:
   - `warpUV += (hash(...) - 0.5) * u_focal_instability * 0.01`
   - Hash returns [0,1], so offset range is [-0.005, 0.005] at max instability
   - Very subtle; may not be visible at typical resolutions

### Performance Edge Cases

1. **Dual Input**:
   - `hasDual` check samples tex1 at (0.5,0.5) to detect if texture is valid
   - This is a clever hack but may produce false negatives if tex1 is bound but contains black pixels
   - **Recommendation**: Use a proper uniform flag to indicate dual input availability

2. **Motion Trails**:
   - `texture(texPrev, uv)` reads previous frame; requires proper framebuffer management
   - If `texPrev` is not updated correctly, trails will show stale data
   - No cleanup on effect disable; previous frame persists

3. **High Resolution**:
   - 4K resolution with all effects enabled (chromatic ab, lens distort, film grain, motion trails) may drop below 60fps
   - Most expensive operations: hash function (film grain), texture samples (dual input + prev + depth)

### Memory Management

- No dynamic memory allocation in shader
- All state is uniform-based
- Previous frame texture must be managed externally (swap chain)

---

## Mathematical Formulations

### Dolly Zoom Scale Calculation

The core dolly zoom effect computes a depth-dependent scale factor:

```glsl
float breath = sin(time * u_breath_speed);  // [-1, 1]
float zoom = 1.0 + breath * u_zoom_intensity * 0.5;  // [0.5, 1.5] typically

float depthDiff = depth - u_subject_dist;
float scale = 1.0 + depthDiff * (zoom - 1.0) * 2.0;
```

**Derivation**:
- We want pixels at `depth == subject_dist` to have `scale == 1.0` (no change)
- Pixels farther than subject (`depth > subject_dist`) should scale with `zoom`
- Pixels closer than subject (`depth < subject_dist`) should scale inversely
- The factor `(zoom - 1.0)` is the deviation from neutral zoom
- Multiplying by `depthDiff * 2.0` creates a linear ramp: at `depthDiff = 0.5`, scale = `1.0 + 0.5 * (zoom-1) * 2 = zoom`

This is a simplified approximation of the true dolly zoom where camera translation and focal length are inversely related.

### Lens Distortion

Barrel/pincushion distortion applied as radial scale modification:

```glsl
vec2 p = uv - 0.5;
float rsq = dot(p, p);  // radius squared
scale *= 1.0 + rsq * u_lens_distort * breath;
```

- `rsq` ranges from 0 at center to 0.5 at corners
- Positive `u_lens_distort` creates barrel distortion (magnifies center, compresses edges)
- Negative creates pincushion (compresses center, magnifies edges)
- Modulated by `breath` to pulse with zoom cycle

### Chromatic Aberration

Simulates lens chromatic aberration by offsetting RGB channels radially:

```glsl
float off = u_chromatic_ab * 0.01 * length(p);
float rCol = texture(tex, warpUV + vec2(off, 0)).r;
float gCol = texture(tex, warpUV).g;
float bCol = texture(tex, warpUV - vec2(off, 0)).b;
```

- Red channel samples to the right, blue to the left, green stays centered
- Offset magnitude proportional to distance from center (`length(p)`)
- Creates color fringing at edges, intensifying with `u_chromatic_ab`

### Film Grain

Procedural hash-based noise:

```glsl
float noise = hash(warpUV * 100.0 + time);
color.rgb = mix(color.rgb, vec3(noise), u_film_grain * 0.1);
```

- `hash()` is a simple pseudo-random function based on dot product with primes
- Noise is animated by adding `time` to the hash input
- Mixed at up to 10% strength (`u_film_grain * 0.1`)

### Motion Trails

Exponential decay feedback:

```glsl
vec4 prev = texture(texPrev, uv);  // Sample at UNWARPED uv
color = mix(color, prev, u_motion_trails * 0.5);
```

- Previous frame is sampled at the original (unwarped) UV to avoid compounding warp artifacts
- Mix factor is `u_motion_trails * 0.5`, so max 50% persistence
- Creates ghostly trails that fade over time as `texPrev` updates

### Vignette

Radial darkening:

```glsl
float vig = smoothstep(1.0, 0.4, length(p) * (1.0 + u_vignette));
color.rgb *= vig;
```

- `length(p)` is distance from center (0 at center, 0.5 at corners)
- `smoothstep(1.0, 0.4, x)` returns 1 when `x < 0.4`, 0 when `x > 1.0`, smooth interpolation between
- Multiplying by `(1.0 + u_vignette)` expands the vignette radius; higher vignette = darker corners
- At `u_vignette=0`, `length(p)` max=0.5, so `smoothstep(1.0,0.4,0.5)=1` (no vignette)
- At `u_vignette=1`, max=1.0, so corners at `smoothstep(1.0,0.4,1.0)=0` (fully dark)

### Focal Instability

Random jitter added to UV coordinates:

```glsl
warpUV += (vec2(hash(vec2(time)), hash(vec2(time+1.0))) - 0.5) * u_focal_instability * 0.01;
```

- Two hash calls generate random offset in X and Y
- Offset range: [-0.005, 0.005] at max instability
- Very subtle; simulates slight camera shake or focus breathing

### Panic Zoom

Fast snap zoom superimposed on smooth breath:

```glsl
if (u_panic_zoom > 0.0) {
    float snap = sign(sin(time * 10.0)) * u_panic_zoom * 0.2;
    breath += snap;
}
```

- `sin(time * 10.0)` oscillates at 10Hz (fast)
- `sign()` yields ±1, creating square wave
- Amplitude `u_panic_zoom * 0.2` adds sudden zoom jumps
- Creates jump-scare effect when combined with high `zoom_intensity`

---

## Performance Characteristics

### Computational Complexity
- **Fragment shader**: Medium complexity (~100 operations per pixel)
- **Texture samples**: 3-4 per pixel (tex0/tex1, depth_tex, texPrev)
- **Hash function**: Called 2-3 times per pixel (film grain, focal instability, chromatic ab offset)

### Memory Bandwidth
- **Read**: 4 textures × 4 channels × 4 bytes = 64 bytes per pixel (theoretical max)
- **Actual**: Depth is single-channel, so ~48 bytes/pixel
- **Write**: 1 output × 4 channels = 16 bytes/pixel
- **Total**: ~64 MB/s at 1080p60 (assuming 1920×1080 × 60fps × 64 bytes ≈ 8 GB/s theoretical, but texture compression and caching reduce actual)

### GPU Utilization
- **Arithmetic intensity**: Medium (balance of math and texture fetch)
- **Texture-bound**: Likely texture fetch limited due to 3-4 samples per pixel
- **Branching**: Minimal (if statements for feature toggles)

### Performance Bottlenecks
1. **Multiple texture samples**: Dual input + depth + previous frame = 4 texture units active
2. **Hash function**: Called multiple times; relatively expensive
3. **High resolution**: 4K may drop below 60fps with all effects enabled

### Optimization Opportunities
- **Early depth rejection**: If depth_cut is high and pixel is clearly subject/background, skip expensive distortion calculations
- **Reduce hash calls**: Cache hash values or use cheaper noise
- **Motion trails**: Use lower resolution previous frame buffer

---

## Test Plan

### Unit Tests (Python)
1. **Parameter Mapping**: Test `_map_param()` with edge values (0, 5, 10) and verify correct shader range
2. **State Serialization**: Test `get_state()` returns correct dictionary structure
3. **Preset Loading**: Test all presets (hitchcock_classic, bad_hangover, jumpscare) load correct parameter values
4. **Audio Reactivity**: Test that audio_reactor is passed correctly and audio mappings are applied

### Integration Tests (Python)
1. **Basic Dolly Zoom**: Render with simple depth gradient (black to white) and verify foreground (dark) remains stable while background warps
2. **Subject Lock**: Set `subject_dist` to match a specific depth value; verify that depth layer remains scale 1.0
3. **Breath Cycle**: Animate `breath_speed` and verify zoom oscillates at correct frequency
4. **Lens Distortion**: Enable `lens_distort` and verify barrel/pincushion effect
5. **Chromatic Aberration**: Enable and verify color fringing at edges
6. **Motion Trails**: Enable and verify previous frame persistence
7. **Dual Input**: Bind tex1 and verify `hasDual` detection switches source
8. **Audio Reactivity**: Provide mock audio_reactor and verify parameter modulation

### Visual Regression Tests (Python)
1. **Reference Frames**: Capture output at key frames (t=0, T/4, T/2, 3T/4) for standard parameters and compare against golden images
2. **Depth Gradient**: Use linear depth ramp and verify scale mapping is linear
3. **Edge Cases**: Test with extreme parameter values (zoom_intensity=0, zoom_intensity=10, subject_dist=0, subject_dist=1)
4. **Performance**: Measure frame time at 1080p and 4K with all effects enabled; ensure 60fps at 1080p

### Shader Tests (GLSL)
1. **Scale Calculation**: Test `scale = 1.0 + depthDiff * (zoom - 1.0) * 2.0` with various depth/zoom values
2. **UV Clamping**: Verify `warpUV` stays in [0,1] after all transformations (or document that out-of-bounds is acceptable)
3. **Depth Cut Smoothing**: Test smoothstep behavior with `depth_cut` parameter
4. **Hash Function**: Verify hash returns [0,1] and is deterministic for same input

### Coverage Requirements
- **Python Code**: 85% line coverage
- **GLSL Shader**: 80% line coverage (manual testing for visual effects)
- **Integration**: 80% scenario coverage

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT071: DollyZoomDatamoshEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

- **File**: `/home/happy/Desktop/claude projects/vjlive/plugins/vdatamosh/dolly_zoom_datamosh.py`
- **Class**: `DollyZoomDatamoshEffect` (full implementation)
- **Shader**: `FRAGMENT` string (full GLSL 330 core shader)
- **Presets**: 3 predefined configurations (hitchcock_classic, bad_hangover, jumpscare)
- **Dependencies**: `core.effects.shader_base.Effect` base class
- **Audio Mappings**: bass → zoom_intensity, kick → panic_zoom, high → focal_instability, mid → breath_speed

---

## Technical Notes

### Shader Architecture
- **Version**: GLSL 330 core
- **Inputs**: `v_uv`, `tex0`, `tex1`, `depth_tex`, `texPrev`, `time`, `resolution`
- **Uniforms**: 12 parameters + `u_mix`
- **Output**: `fragColor`
- **Dual Input**: Detected by sampling tex1 at (0.5,0.5) and checking if any channel > 0.001

### Depth-Based Warping Strategy
The effect uses a simplified model: instead of true 3D camera projection, it applies a depth-dependent scale factor. This is computationally cheaper and produces a stylized but convincing vertigo effect. The key insight: if you scale UV coordinates around the center by a factor that depends on depth, you simulate the perspective change of a dolly zoom.

### Audio Reactivity Implementation
Audio reactivity is applied in `apply_uniforms()` by scaling uniform values based on audio bands:
```python
if audio_reactor is not None:
    zoom *= (1.0 + audio_reactor.get_band('bass', 0.0) * 0.5)
    panic *= (1.0 + audio_reactor.get_energy(0.8) * 0.8)
```
This allows the effect to pulse with music, making it suitable for live VJing.

### Known Limitations

1. **No True 3D**: The effect is a 2D warp with depth modulation, not a full 3D camera projection. True dolly zoom would require reconstructing a 3D point cloud and re-projecting with different focal length and camera position.

2. **Depth Quality**: The effect assumes a clean depth map. Noisy depth data produces warping artifacts. No depth preprocessing or filtering is applied.

3. **Subject Isolation**: The `subject_dist` parameter is a single depth value, not a range. Complex scenes with multiple subjects at different depths cannot be locked simultaneously.

4. **Dual Input Fallback**: The `hasDual` detection is heuristic and may fail if tex1 is bound but contains only black pixels.

5. **Motion Trails Artifacts**: Using `texPrev` at unwarped UV can create ghosting that doesn't align with the warped output, producing a "double vision" effect that may be undesirable.

### WebGPU Migration Notes

- GLSL to WGSL conversion required
- Bind group layout: 4 textures (tex0, tex1, depth_tex, texPrev) + uniforms
- Uniform buffer for 12 parameters + time + resolution + u_mix
- Hash function needs to be reimplemented in WGSL (same algorithm)
- Texture sampling coordinates need careful handling due to WGSL's different coordinate system (Y may be flipped)
- Consider using storage buffers for previous frame if multiple feedback passes are needed

### Performance Optimization Tips

1. **Disable unused features**: If chromatic aberration and film grain are off, the shader still computes hash; consider moving hash inside conditionals
2. **Lower resolution depth**: Depth map can be half-resolution without noticeable quality loss
3. **Reduce texture samples**: If dual input not needed, skip tex1 sampling entirely
4. **Motion trails**: Use every other frame for texPrev update to reduce bandwidth

---
