# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT014_bass_cannon_datamosh.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT014 — BassCannonDatamoshEffect

**What This Module Does**

The `BassCannonDatamoshEffect` is a real-time video distortion effect that simulates a "sonic weapon" triggered by audio bass. It processes dual video inputs (Video A and Video B) along with a depth map to generate radial shockwaves that distort, displace, and shatter pixels. The effect is centered on the screen (the cannon muzzle) and fires outward when the bass intensity exceeds a configurable threshold.

The effect combines multiple visual phenomena:
- **Shockwave distortion**: A radial wave that propagates from the center, warping the image based on depth
- **Recoil**: Screen shake/kickback that intensifies with bass power
- **Muzzle flash**: Brief whiteout/blind effect at the wavefront origin
- **Debris scatter**: Pixel-level glitch/shattering effect that radiates with the shockwave
- **Chroma blast**: Color separation (RGB shift) that intensifies near the blast
- **Thermal exhaust**: Heat distortion trails that persist after the wave passes
- **Impact ring**: Visible ring of fire/energy at the shockwave front

All effects are driven by a single time-based wavefront that expands from the center. The `audio_level` input controls the `cannon_power` - higher bass produces stronger, larger shockwaves. The effect uses a fragment shader that samples the input textures, applies the distortion, and outputs the result.

**What This Module Does NOT Do**

- Does NOT provide audio analysis or bass detection (relies on external audio input providing a normalized 0.0-1.0 level)
- Does NOT handle video capture or camera management (receives frames as textures)
- Does NOT implement physics simulation for debris (uses procedural shader noise)
- Does NOT support 3D rendering (operates on 2D textures with depth as a single channel)
- Does NOT include audio playback or sound synthesis
- Does NOT provide user interface for parameter adjustment (parameters are set via config dict)
- Does NOT implement network streaming or multi-device synchronization
- Does NOT accumulate state across frames (stateless per-frame shader, except for previous frame texture)

---

## Detailed Behavior and Parameter Interactions

### Core Shader Algorithm

The effect is implemented entirely in a GLSL fragment shader. The main algorithm:

1. **Input textures**:
   - `tex0`: Video A (primary input)
   - `tex1`: Video B (secondary input, used when `hasDual` is true)
   - `texPrev`: Previous frame (for thermal exhaust trails)
   - `depth_tex`: Depth map (single channel, typically 0.0-1.0)

2. **Shockwave wavefront**:
   - The wavefront position is computed as `waveDist = fract(time * u_shockwave_speed)`, giving a repeating 0.0-1.0 radial distance
   - The blast strength decays with distance: `blastStr = u_cannon_power * (1.0 - waveDist) * step(waveDist, u_depth_penetration)`
   - The `step` ensures the wave stops at `u_depth_penetration` (0.0-1.0)

3. **Shockwave distortion**:
   - A ring is created at the wavefront: `shock = smoothstep(0.0, 0.1, abs(r - waveDist))` then inverted and sharpened: `shock = pow(1.0 - shock, 8.0)`
   - The UV coordinates are pushed outward radially: `shockUV = p * (1.0 - shock * u_distortion * 0.1 * blastStr)`
   - This creates a bulging effect at the wavefront

4. **Recoil (screen shake)**:
   - When `blastStr > 0.1`, a random shake offset is computed: `shake = hash(vec2(time, 0.0)) - 0.5`
   - The offset is scaled by `u_recoil` and modulated by `(1.0 - waveDist)` so the shake is strongest near the muzzle
   - The final UV includes this offset: `finalUV = shockUV + 0.5 + recoil`

5. **Debris scatter (glitch)**:
   - Random noise based on UV and time: `debris = hash(uv * 50.0 + time)`
   - If `debris > 0.95` (5% chance), add a random offset to the UV: `finalUV += (random_vec2 - 0.5) * u_debris_scatter * 0.1 * blastStr`
   - This creates pixel shattering that radiates with the blast

6. **Chroma blast (RGB shift)**:
   - If `u_chroma_blast > 0`, sample the texture at slightly offset UVs for each channel:
     - Red: `finalUV + vec2(off, 0)`
     - Green: `finalUV` (no offset)
     - Blue: `finalUV - vec2(off, 0)`
   - The offset magnitude: `off = u_chroma_blast * 0.02 * blastStr`
   - If dual video is enabled (`hasDual`), sample from `tex1` instead of `tex0`

7. **Muzzle flash**:
   - Near the wavefront origin (`waveDist < 0.1`), blend toward white: `flash = (0.1 - waveDist) * 10.0 * u_muzzle_flash * u_cannon_power`
   - `color.rgb = mix(color.rgb, vec3(1.0), flash)`

8. **Thermal exhaust (trails)**:
   - Sample the previous frame at the final UV: `prev = texture(texPrev, finalUV)`
   - Blend the current color with the previous frame: `color = mix(color, prev, u_thermal_exhaust * 0.3 * (1.0 - blastStr))`
   - The `(1.0 - blastStr)` ensures trails only appear where there's no blast (so the blast itself doesn't smear)

9. **Impact ring**:
   - Add an orange/red ring at the shockwave front: `color.rgb += vec3(1.0, 0.5, 0.2) * shock * blastStr * 2.0`

10. **Final blend**:
    - Mix between original (unprocessed) and processed color: `fragColor = mix(original, color, u_mix)`

### Parameter Roles

All parameters are uniform floats (0.0-10.0 range unless noted):

| Parameter | Role | Visual Effect |
|-----------|------|---------------|
| `u_cannon_power` | Overall blast intensity | Bigger, stronger distortion, brighter flash, more debris |
| `u_shockwave_speed` | Speed of wavefront expansion | Faster waves feel more explosive; slower waves feel like rumbles |
| `u_recoil` | Screen shake magnitude | More violent camera kickback |
| `u_muzzle_flash` | Whiteout brightness at origin | Brighter blinding effect at the center |
| `u_debris_scatter` | Glitch/pixel shatter amount | More random pixel displacement |
| `u_bass_threshold` | Audio level needed to trigger | Higher = only very loud bass fires; lower = more frequent |
| `u_impact_radius` | Size of the cannon muzzle | Affects initial ring width (used in smoothstep) |
| `u_distortion` | UV warping strength | More bulging at shockwave front |
| `u_chroma_blast` | RGB shift amount | Color fringing around edges |
| `u_thermal_exhaust` | Trail persistence | Longer-lasting motion blur trails |
| `u_depth_penetration` | How far the wave travels (0-1) | Larger values let the wave reach screen edges |
| `u_decay` | How fast blast fades (not heavily used in current shader) | Could modulate `blastStr` decay over time |
| `u_mix` | Blend between original and effect (0-1) | 0 = no effect, 1 = full effect |

**Note**: The skeleton spec lists these parameters in `config`. The legacy shader uses them as uniforms. The `audio_level` input is separate and is used to set `u_cannon_power` dynamically (or the effect could internally map audio to power).

### Dual Video Input Handling

The shader checks if Video B (`tex1`) has any content by sampling the center pixel:
```glsl
bool hasDual = (texture(tex1, vec2(0.5)).r + texture(tex1, vec2(0.5)).g + texture(tex1, vec2(0.5)).b) > 0.001;
```
If `hasDual` is true, the effect uses `tex1` as the source for color sampling (instead of `tex0`). This allows switching between two video sources. The chroma blast also uses the active source.

### Time Handling

The shader uses a `time` uniform that increments each frame. The wavefront position is `fract(time * u_shockwave_speed)`, creating a repeating cycle. The `hash` function uses `time` to generate random values for recoil and debris.

**Important**: The shader is stateless per-frame except for the `texPrev` texture which holds the previous frame's output. This must be provided by the pipeline.

---

## Integration

### VJLive3 Pipeline Integration

The `BassCannonDatamoshEffect` is a **frame processor** that sits in the video effects chain. It requires:

- **Inputs**: Two video textures (tex0, tex1) and a depth texture, plus the previous frame texture
- **Output**: A single processed video texture
- **Uniforms**: All the `u_*` parameters plus `time`, `resolution`
- **Audio**: An `audio_level` float that modulates `u_cannon_power` (or is used directly as power)

**Typical pipeline**:

```
[Video Source A] → tex0
[Video Source B] → tex1 (optional)
[Depth Source] → depth_tex
[Previous Frame] → texPrev (ping-pong FBOs)
[Audio Analyzer] → audio_level (0.0-1.0)

BassCannonDatamoshEffect.process_frame({
    'tex0': tex0,
    'tex1': tex1,
    'depth_tex': depth_tex,
    'texPrev': texPrev,
    'resolution': (width, height)
}, audio_level) → output_texture
```

**Frame sequence**:

1. Bind input textures to appropriate texture units
2. Set all uniform values (including `time` which increments each frame)
3. Render a full-screen quad with the shader
4. The shader writes to an FBO or directly to the screen
5. The output becomes the `texPrev` for the next frame (ping-pong)

**Audio integration**: The `audio_level` should be derived from the audio pipeline's bass detection (e.g., RMS of low frequencies). It can be mapped to `u_cannon_power` directly or via a scaling factor.

**Depth map**: The depth texture is sampled but not heavily used in the current shader (only to check `hasDual`? Actually the shader reads `float depth = texture(depth_tex, uv).r;` but doesn't use it further. This is likely a placeholder for future depth-based distortion. The spec should note that depth is currently unused but reserved.

### Shader Management

The effect inherits from `Effect` base class which handles:
- Shader compilation (vertex + fragment)
- Uniform location caching
- Texture unit binding
- Rendering full-screen quad

The vertex shader is standard pass-through (not shown in legacy but implied).

---

## Performance

### Computational Cost

The effect is **GPU-bound** due to the fragment shader running at full screen resolution.

**Shader operations per fragment**:
- 5 texture samples (tex0, tex1, depth_tex, texPrev, plus potential extra for chroma)
- Several arithmetic operations (add, mul, smoothstep, pow, sin, atan, length)
- Hash function (few operations)
- Conditional branches (hasDual, blastStr > 0.1, debris random, etc.)

**Expected performance**:
- 1080p (1920x1080): ~2-4 ms on modern GPU (NVIDIA GTX 1060+)
- 4K (3840x2160): ~8-12 ms
- Integrated graphics: may struggle at 1080p

The effect is relatively heavy due to multiple texture fetches and complex math. Optimizations:
- Reduce texture samples when `hasDual` is false (already done)
- Early-out if `blastStr` is very small (skip heavy calculations)
- Use lower precision where possible

### Memory Usage

- **GPU memory**: 
  - 4 input textures (full resolution, typically RGBA or RGBA+depth)
  - 1 output texture (ping-pong)
  - Shader program: < 50 KB
- **CPU memory**: Minimal (uniforms, state)

### Optimization Strategies

1. **Texture format**: Use `GL_RGBA8` or `GL_RGBA16F` for HDR; depth can be `GL_R8` or `GL_R16F`
2. **Ping-pong FBOs**: Use two FBOs and swap to avoid read-write hazards
3. **Uniform buffering**: Batch uniform updates; use UBO if many effects
4. **Shader simplification**: If performance is critical, disable some features (e.g., thermal exhaust, debris) via compile-time flags or runtime uniform toggles
5. **Resolution scaling**: Render at lower internal resolution and upscale

### Platform-Specific Considerations

- **Desktop**: No issues; requires OpenGL 3.3+
- **Embedded (Raspberry Pi)**: Likely too heavy for 1080p; consider reducing resolution or simplifying shader
- **Mobile**: May need significant optimization; consider using Vulkan/Metal for better performance

---

## State Management

### Per-Frame State
- `audio_level` (float): Current audio input level, varies each frame
- `time` (float): Global time counter, increments continuously
- `blastStr` (float, computed): Current blast strength based on time and parameters
- `waveDist` (float, computed): Current wavefront radial position (0.0-1.0)

### Persistent State
- None (the effect is stateless between frames except for the previous frame texture)

### Initialization State
- Shader program compiled and linked
- Uniform locations cached
- Texture units bound (tex0, tex1, depth_tex, texPrev)
- FBOs created for ping-pong rendering

---

## GPU Resources

### Shaders
- **Vertex Shader**: Simple pass-through rendering full-screen quad with UV coordinates
- **Fragment Shader**: Complex shader implementing shockwave, distortion, recoil, debris, chroma blast, muzzle flash, thermal exhaust, and impact ring

### Textures
- `tex0` (sampler2D): Primary video input (RGBA)
- `tex1` (sampler2D): Secondary video input (RGBA), used when `hasDual` is true
- `depth_tex` (sampler2D): Depth map (single channel, typically R8 or R16F)
- `texPrev` (sampler2D): Previous frame output for thermal exhaust trails

### Framebuffers
- **Ping-pong FBOs**: Two framebuffers used to alternate between reading previous frame and writing current frame
- **Default Framebuffer**: Optional direct rendering to screen

### Uniforms
- All `u_*` parameters (13 floats)
- `time` (float)
- `resolution` (vec2)

---

## Error Cases

### Configuration Errors
- **Missing required parameters**: Should raise `KeyError` with message indicating which parameter is missing
- **Invalid parameter types**: Should raise `TypeError` if parameter is not a number
- **Out-of-range values**: Should clamp to valid range and log warning (e.g., `u_cannon_power` clamped to [0.0, 10.0])

### Runtime Errors
- **Missing textures**: If any required texture (tex0, depth_tex, texPrev) is None or invalid, should raise `RuntimeError` with texture name
- **Shader compilation failure**: Should raise `RuntimeError` with shader compilation log
- **GPU memory exhaustion**: Should raise `MemoryError` when FBO or texture allocation fails
- **Invalid resolution**: If resolution is (0, 0) or negative, should raise `ValueError`

### Input Errors
- **Invalid audio_level**: Should be clamped to [0.0, 1.0] with warning if outside range
- **Missing previous frame**: If `texPrev` is not provided, thermal exhaust will not work but effect should still render (with warning)
- **Dual video not available**: If `tex1` is None, effect should fall back to `tex0` without error

---

## Configuration Schema (Pydantic-style)

```python
from pydantic import BaseModel, Field, validator
from typing import Dict, Any

class BassCannonConfig(BaseModel):
    u_cannon_power: float = Field(default=5.0, ge=0.0, le=10.0, description="Intensity of the shockwave distortion")
    u_shockwave_speed: float = Field(default=5.0, ge=0.0, le=10.0, description="Speed of the blast wavefront expansion")
    u_recoil: float = Field(default=3.0, ge=0.0, le=10.0, description="Screen kickback intensity")
    u_muzzle_flash: float = Field(default=4.0, ge=0.0, le=10.0, description="Whiteout intensity at impact origin")
    u_debris_scatter: float = Field(default=3.0, ge=0.0, le=10.0, description="Pixel shattering/glitch amount")
    u_bass_threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="Audio level (0.0-1.0) needed to trigger fire")
    u_impact_radius: float = Field(default=5.0, ge=0.0, le=10.0, description="Size of the cannon muzzle (affects ring width)")
    u_distortion: float = Field(default=4.0, ge=0.0, le=10.0, description="UV warping amount at shockwave front")
    u_chroma_blast: float = Field(default=2.0, ge=0.0, le=10.0, description="Color separation (RGB shift) intensity")
    u_thermal_exhaust: float = Field(default=3.0, ge=0.0, le=10.0, description="Heat distortion trail persistence")
    u_depth_penetration: float = Field(default=4.0, ge=0.0, le=10.0, description="How far the blast travels (0=center only, 1=full screen)")
    u_decay: float = Field(default=3.0, ge=0.0, le=10.0, description="How fast the blast fades (currently unused)")
    u_mix: float = Field(default=0.5, ge=0.0, le=1.0, description="Blend ratio between original and effect (0=original, 1=full)")

    @validator('u_bass_threshold')
    def check_bass_threshold(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('u_bass_threshold must be between 0.0 and 1.0')
        return v

    @validator('u_mix')
    def check_mix(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('u_mix must be between 0.0 and 1.0')
        return v
```

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect initializes without crashing if textures are None or OpenGL context missing |
| `test_basic_operation` | Effect applies distortion when audio_level > threshold; output differs from input |
| `test_dual_video_switch` | When tex1 has content, effect uses tex1 instead of tex0 |
| `test_shockwave_visual` | Shockwave ring appears and propagates from center over time |
| `test_recoil_effect` | Screen shake offset is applied and varies with time |
| `test_muzzle_flash` | Whiteout effect appears near wavefront origin when u_muzzle_flash > 0 |
| `test_debris_scatter` | Random pixel offsets appear when u_debris_scatter > 0 |
| `test_chroma_blast` | RGB channels are offset differently, creating color fringing |
| `test_thermal_exhaust` | Previous frame trails persist in output when u_thermal_exhaust > 0 |
| `test_impact_ring` | Orange/red ring is visible at shockwave front |
| `test_parameter_validation` | All uniform parameters are clamped to [0,10] or appropriate range |
| `test_audio_threshold` | When audio_level < u_bass_threshold, cannon_power is effectively 0 (no effect) |
| `test_depth_penetration` | Wavefront stops at radius = u_depth_penetration |
| `test_mix_control` | u_mix=0 returns original; u_mix=1 returns full effect |
| `test_cleanup` | OpenGL resources (FBOs, textures, shader) are released properly |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

