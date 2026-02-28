# P5-DM02: Bad Trip Datamosh

## Overview

The `BadTripDatamosh` effect simulates a terrifying psychedelic crisis—a "nightmare flip" that transforms video into an aggressive, hostile, and unsettling visual experience. It uses depth information to identify subjects and distort them into demonic forms, while the environment breathes with a sickly pulse and insects crawl under the pixels. The effect supports dual video inputs: Video A (tex0) as the primary source and Video B (tex1) as the "other side" that leaks through reality tears.

The implementation is a GLSL fragment shader with 12 user-controllable parameters (all on 0.0-10.0 range) that modulate various distortion, color, glitch, and strobing effects. The shader samples depth maps to apply targeted distortions to foreground subjects, uses procedural noise for insect crawl effects, and implements a reality tear mechanism that reveals the alternate video stream. Audio reactivity is optional, with specific parameters mapped to high-frequency energy and bass bands.

**Key Features:**
- **Demon Face**: Depth-based facial distortion that warps near-field regions into skeletal/demonic shapes
- **Insect Crawl**: High-frequency noise that moves like bugs crawling under the screen
- **Paranoia Strobe**: Random, anxiety-inducing black flashes
- **Void Gaze**: Dark vignette that creates a staring void at the center
- **Reality Tear**: Screen tearing that reveals Video B from the "other side"
- **Breathing Walls**: UV warping that makes the environment pulse
- **Shadow People**: Darkening of distant (low-depth) background figures
- **Psychosis**: Color inversion and hue shifting
- **Sickness**: Green/purple sickly tinting
- **Doom**: Contrast crushing
- **Time Loop**: Feedback echo using previous frame

## Architecture

### Shader Structure

The Bad Trip Datamosh effect is implemented as a single-pass fragment shader that processes full-screen video frames. The shader follows this execution pipeline:

1. **Texture Binding Setup**: Four texture units are bound:
   - `tex0` (unit 0): Video A (primary input)
   - `texPrev` (unit 1): Previous frame for feedback effects
   - `depth_tex` (unit 2): Depth map for subject isolation
   - `tex1` (unit 3): Video B (secondary/"other side" input)

2. **Dual Video Detection**: At shader start, the effect samples `tex1` at UV (0.5, 0.5) to check if Video B is present. If the sum of RGB channels exceeds 0.001, dual mode is active; otherwise, fallback to Video A only.

3. **Depth Sampling**: The depth map is sampled at the current UV coordinate to obtain a normalized depth value (0.0 = far, 1.0 = near). This depth drives subject-specific effects like Demon Face and Shadow People.

4. **Breathing Walls UV Warp**: If `u_breathing_walls > 0`, a radial sinusoidal distortion is applied to the UV coordinates based on distance from center, creating a pulsing expansion/contraction effect.

5. **Demon Face Distortion**: For pixels where `depth > 0.2`, aggressive sinusoidal warping is applied to simulate facial elongation and skeletal transformation. A hollow-eye effect further distorts the central region.

6. **Insect Crawl Noise**: High-frequency hash-based noise displaces UV coordinates randomly for a small fraction of pixels, creating the illusion of bugs crawling.

7. **Base Color Sampling**: The (potentially warped) UV coordinates are used to sample either Video B (if dual mode) or Video A. The previous frame is also sampled for feedback.

8. **Time Loop Feedback**: The current color is mixed with the previous frame using `u_time_loop` as blend factor (0.0 = no feedback, 1.0 = full previous frame).

9. **Reality Tear Glitch**: Random horizontal tears occur based on `u_reality_tear`. When a tear triggers, the pixel samples from the alternate video stream (Video A if using Video B, or inverted color if single mode).

10. **Sickness Tint**: A sickly green/purple color tint is mixed in, oscillating over time.

11. **Shadow People Darkening**: If `u_shadow_people > 0` and `depth < 0.3` (background), the color is multiplied by `(1.0 - u_shadow_people * 0.8)` to create dark silhouettes.

12. **Psychosis Inversion**: Color channels are offset by `u_psychosis * 0.5` and absolute-valued, creating harsh inversion and hue shifts.

13. **Void Gaze Vignette**: A radial darkening from the center with falloff controlled by `u_void_gaze`.

14. **Doom Contrast**: Linear contrast adjustment: `color = (color - 0.5) * (1.0 + u_doom) + 0.5`.

15. **Paranoia Strobe**: Random black frames triggered by `u_paranoia` with ~10% probability per frame.

16. **Final Mix**: The processed color is mixed with the original (unwarped) video using `u_mix` (always 1.0 in current implementation, but provided for future blending control).

### Parameter Mapping

All user-facing parameters use a 0.0-10.0 range. The plugin's `_map_param()` method converts these to operational shader ranges:

| Parameter | 0-10 Range | Operational Range | Mapping Formula |
|-----------|------------|-------------------|-----------------|
| `anxiety` | 0-10 | 0.0-10.0 | `out_min + (val/10.0)*(out_max-out_min)` where out_min=0, out_max=10 |
| `demon_face` | 0-10 | 0.0-1.0 | `val/10.0` |
| `insect_crawl` | 0-10 | 0.0-1.0 | `val/10.0` |
| `void_gaze` | 0-10 | 0.0-1.0 | `val/10.0` |
| `reality_tear` | 0-10 | 0.0-1.0 | `val/10.0` |
| `sickness` | 0-10 | 0.0-1.0 | `val/10.0` |
| `time_loop` | 0-10 | 0.0-1.0 | `val/10.0` |
| `breathing_walls` | 0-10 | 0.0-1.0 | `val/10.0` |
| `paranoia` | 0-10 | 0.0-1.0 | `val/10.0` |
| `shadow_people` | 0-10 | 0.0-1.0 | `val/10.0` |
| `psychosis` | 0-10 | 0.0-1.0 | `val/10.0` |
| `doom` | 0-10 | 0.0-1.0 | `val/10.0` |

**Audio Reactivity**: When an `audio_reactor` is provided, two parameters are modulated by audio:
- `anxiety` multiplied by `(1.0 + audio_reactor.get_energy(0.5) * 0.5)`
- `demon_face` multiplied by `(1.0 + audio_reactor.get_band('bass', 0.0) * 0.5)`

### Shader Uniforms

The fragment shader declares the following uniforms:

```glsl
uniform sampler2D tex0;        // Video A
uniform sampler2D texPrev;     // Previous frame (feedback)
uniform sampler2D depth_tex;   // Depth map
uniform sampler2D tex1;        // Video B (other side)
uniform float time;            // Global time in seconds
uniform vec2 resolution;       // Frame resolution in pixels

// Effect parameters (all 0.0-1.0 after remapping)
uniform float u_anxiety;           // Speed/jitter intensity
uniform float u_demon_face;        // Facial distortion amount (0-1)
uniform float u_insect_crawl;      // Bug-like noise intensity (0-1)
uniform float u_void_gaze;         // Dark vignette/hole intensity (0-1)
uniform float u_reality_tear;      // Glitch tearing probability weight (0-1)
uniform float u_sickness;          // Green/purple tinting (0-1)
uniform float u_time_loop;         // Feedback delay echo amount (0-1)
uniform float u_breathing_walls;   // UV warping intensity (0-1)
uniform float u_paranoia;          // Random strobe/cuts probability weight (0-1)
uniform float u_shadow_people;     // Dark depth artifacts (0-1)
uniform float u_psychosis;         // Color inversion/hue shift (0-1)
uniform float u_doom;              // Contrast crush (0-1)
uniform float u_mix;               // Final blend with original (always 1.0)
```

### Helper Functions

**Hash Function** (pseudo-random):
```glsl
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
```

**Noise Function** (smooth value noise):
```glsl
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f*f*(3.0-2.0*f);
    return mix(mix(hash(i + vec2(0.0,0.0)), hash(i + vec2(1.0,0.0)), f.x),
               mix(hash(i + vec2(0.0,1.0)), hash(i + vec2(1.0,1.0)), f.x), f.y);
}
```

## Inputs and Outputs

### Inputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `signal_in` | video | Primary video stream (Video A) | Must be valid GPU texture, any resolution |
| `depth_in` | depth_map | Depth map corresponding to Video A | Normalized 0.0-1.0, same resolution as video |
| `signal_alt` (optional) | video | Secondary video stream (Video B/"other side") | If not connected, reality tears use inverted colors |

### Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `signal_out` | video | Processed video with bad trip effects | Same resolution as input |

### Parameters

| Name | Type | Default | Min | Max | Description |
|------|------|---------|-----|-----|-------------|
| `anxiety` | float | 6.0 | 0.0 | 10.0 | Speed/jitter intensity; also scales insect crawl speed |
| `demon_face` | float | 4.0 | 0.0 | 10.0 | Distorts facial depth to look skeletal/demonic |
| `insect_crawl` | float | 3.0 | 0.0 | 10.0 | High-frequency noise that moves like bugs |
| `void_gaze` | float | 5.0 | 0.0 | 10.0 | Dark vignette/hole at center of screen |
| `reality_tear` | float | 4.0 | 0.0 | 10.0 | Screen tearing that reveals Video B |
| `sickness` | float | 5.0 | 0.0 | 10.0 | Green/purple sickly tinting |
| `time_loop` | float | 5.0 | 0.0 | 10.0 | Feedback echo using previous frame |
| `breathing_walls` | float | 4.0 | 0.0 | 10.0 | UV warping that makes environment pulse |
| `paranoia` | float | 3.0 | 0.0 | 10.0 | Random black strobe flashes |
| `shadow_people` | float | 4.0 | 0.0 | 10.0 | Darkens background (low-depth) figures |
| `psychosis` | float | 2.0 | 0.0 | 10.0 | Color inversion and hue shifting |
| `doom` | float | 4.0 | 0.0 | 10.0 | Contrast crushing |

### Presets

The effect includes three curated presets:

**Arachnophobia** (spider-focused):
```python
{
    "anxiety": 8.0, "demon_face": 2.0, "insect_crawl": 10.0,
    "void_gaze": 4.0, "reality_tear": 3.0, "sickness": 4.0,
    "time_loop": 6.0, "breathing_walls": 2.0, "paranoia": 5.0,
    "shadow_people": 8.0, "psychosis": 3.0, "doom": 4.0,
}
```

**Ego Death** (existential breakdown):
```python
{
    "anxiety": 2.0, "demon_face": 6.0, "insect_crawl": 2.0,
    "void_gaze": 10.0, "reality_tear": 8.0, "sickness": 2.0,
    "time_loop": 10.0, "breathing_walls": 8.0, "paranoia": 2.0,
    "shadow_people": 0.0, "psychosis": 10.0, "doom": 8.0,
}
```

**Schizoid** (maximum chaos):
```python
{
    "anxiety": 10.0, "demon_face": 8.0, "insect_crawl": 5.0,
    "void_gaze": 2.0, "reality_tear": 10.0, "sickness": 8.0,
    "time_loop": 2.0, "breathing_walls": 10.0, "paranoia": 10.0,
    "shadow_people": 10.0, "psychosis": 8.0, "doom": 6.0,
}
```

## Edge Cases and Error Handling

### Missing Depth Texture

If the depth texture is not provided or is invalid (all zeros or uninitialized), the effect should:
- Log a warning at most once per activation (not per frame)
- Continue rendering with `depth = 0.5` (mid-depth) for all pixels
- Disable depth-dependent effects (Demon Face, Shadow People) by effectively setting their contributions to zero
- The shader should not crash; it should treat missing depth as uniform 0.5

**Implementation**: In the Python wrapper's `apply_uniforms()`, check if depth texture is valid. If not, bind a 1x1 pixel texture with value 0.5 or set a uniform flag to use constant depth.

### Missing Previous Frame Buffer

The `texPrev` texture is required for time loop feedback. If not provided:
- The effect should set `u_time_loop = 0` automatically (disable feedback)
- Log a debug message (not an error) indicating feedback disabled
- The shader already handles this gracefully: `color = mix(color, prev, u_time_loop * 0.5)` with `prev` sampling as black if texture missing

### Dual Video Mode

The shader detects Video B presence by sampling at UV (0.5, 0.5). Edge cases:
- If Video B is connected but all-black (sum < 0.001), it's treated as absent
- If Video B resolution differs from Video A, the texture sampler will handle scaling/letterboxing automatically per OpenGL rules (GL_REPEAT, GL_CLAMP_TO_EDGE)
- Reality tears in single-video mode use `vec4(1.0) - color` as the "other side"

### Parameter Clamping

All parameters must be clamped to the 0.0-10.0 range before mapping. The base `Effect` class should enforce this in `set_parameter()`:
- Values < 0.0 are set to 0.0
- Values > 10.0 are set to 10.0
- Non-numeric values raise `TypeError`
- Unknown parameter names raise `KeyError`

### Performance Under Load

**High Resolution (4K+)**:
- The shader is fill-rate bound due to multiple texture reads per fragment:
  - 1 read for color (tex0 or tex1)
  - 1 read for previous frame (texPrev)
  - 1 read for depth (depth_tex)
  - Plus occasional extra reads for insect crawl hash (procedural, no texture)
- At 4K (3840×2160 = 8.3M fragments), this can exceed 30 FPS on mid-tier GPUs
- **Mitigation**: The plugin should support optional half-resolution rendering via a `render_scale` parameter (not exposed to user, set by engine based on performance monitoring)

**Extreme Parameter Values**:
- `u_breathing_walls > 0.8` can cause UV coordinates to wrap or clamp, creating edge artifacts
- `u_void_gaze > 0.9` can make the entire screen nearly black except the very center
- `u_doom > 0.9` can cause severe contrast clipping, losing all shadow/highlight detail
- `u_paranoia > 0.8` can trigger strobing on nearly every frame, potentially causing seizures
- The shader does not explicitly clamp these internally; it relies on the Python wrapper to clamp user input to 0-10, which maps to safe operational ranges.

**Depth Map Edge Cases**:
- Depth values outside 0.0-1.0 range should be clamped in the shader: `depth = clamp(depth, 0.0, 1.0)`
- If depth map is noisy (common with real-time depth sensors), the Demon Face effect may flicker on/off. A simple temporal smoothing (not implemented) could help but is out of scope for parity.

### Resource Cleanup

The effect inherits from `Effect` base class which manages OpenGL resources:
- `__del__()` or explicit `close()` should delete the shader program and release texture units
- No persistent CPU-side buffers are allocated; all state is in uniform values
- The plugin should implement `get_state()` for serialization (already present in legacy code)

## Dependencies

### External Libraries

- **PyOpenGL** (or VJLive3's OpenGL abstraction layer): For shader compilation, uniform setting, and texture binding. If OpenGL context is unavailable at init, the plugin should defer compilation until first use or raise a clear `RuntimeError` with message "OpenGL context required".
- **NumPy**: Not directly used by this effect (all operations in shader), but may be used by the base class for buffer management.
- **logging**: For debug/info/warning messages.

### Internal Dependencies

- **`vjlive3.core.effects.shader_base.Effect`**: Base class providing:
  - Shader program compilation and uniform caching
  - Texture unit management
  - `apply_uniforms()` hook for parameter remapping
  - `set_parameter()` / `get_parameter()` methods
  - `get_state()` serialization
- **`vjlive3.plugins.registry`**: Plugin manifest system that discovers and instantiates the effect class.
- **`vjlive3.render.framebuffer`**: Framebuffer management for full-screen pass rendering.
- **`vjlive3.audio.AudioReactor`** (optional): For audio reactivity; if not provided, audio-reactive parameters default to multiplicative factor 1.0.

### Texture Unit Requirements

The effect requires 4 texture units:
- Unit 0: `tex0` (Video A)
- Unit 1: `texPrev` (previous frame)
- Unit 2: `depth_tex` (depth map)
- Unit 3: `tex1` (Video B)

The base class should allocate these sequentially and ensure they are bound before drawing.

## Test Plan

### Unit Tests

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_without_opengl` | Plugin can be instantiated even if OpenGL context is not current; shader compilation deferred or fails gracefully |
| `test_shader_compilation` | The GLSL fragment shader compiles without errors or warnings |
| `test_parameter_defaults` | All 12 parameters have correct default values (6.0, 4.0, 3.0, 5.0, 4.0, 5.0, 5.0, 4.0, 3.0, 4.0, 2.0, 4.0) |
| `test_parameter_clamping` | Setting parameters below 0.0 clamps to 0.0; above 10.0 clamps to 10.0; within range preserved |
| `test_parameter_type_errors` | Setting non-numeric parameter raises `TypeError`; unknown parameter name raises `KeyError` |
| `test_uniform_locations_cached` | After first `apply_uniforms()`, uniform locations are cached and reused on subsequent frames |
| `test_audio_reactivity_scaling` | When `audio_reactor` provided, `anxiety` and `demon_face` are multiplied by audio factors |
| `test_audio_reactor_missing` | When `audio_reactor` is None, parameters use base values without scaling |
| `test_dual_video_detection` | Shader correctly detects presence of Video B by sampling at UV (0.5, 0.5) |
| `test_preset_loading` | All three presets (`arachnophobia`, `ego_death`, `schizoid`) load without errors and contain all 12 parameters |
| `test_state_serialization` | `get_state()` returns dict with `name`, `enabled`, and copy of `parameters` |
| `test_mix_parameter_always_one` | `u_mix` uniform is set to 1.0 (hardcoded in `apply_uniforms`) |

### Integration Tests

| Test Name | What It Verifies |
|-----------|------------------|
| `test_render_with_valid_textures` | Full render pass produces non-null framebuffer with reasonable pixel values (not all zero or NaN) |
| `test_depth_effect_visibility` | With `demon_face > 0` and a depth map having foreground >0.5, warping is visible in output |
| `test_reality_tear_swaps_video` | With dual video mode and `reality_tear > 0`, some pixels show Video A instead of Video B (or vice versa) |
| `test_paranoia_strobe` | With `paranoia > 0`, occasional frames are completely black (requires rendering multiple frames) |
| `test_void_gaze_darkens_center` | With `void_gaze > 0`, center region is brighter than edges (vignette inverted) |
| `test_time_loop_feedback` | With `time_loop > 0` and static input, output evolves over frames due to feedback accumulation |
| `test_breathing_walls_warp` | With `breathing_walls > 0`, UV distortion creates pulsating expansion/contraction over time |
| `test_sickness_tint` | With `sickness > 0`, color shifts toward green/purple oscillating mix |
| `test_shadow_people_darkens_background` | With `shadow_people > 0` and depth < 0.3, those regions are darker |
| `test_psychosis_inversion` | With `psychosis > 0`, colors are inverted and offset |
| `test_doom_contrast` | With `doom > 0`, midtones are pushed toward black or white |
| `test_insect_crawl_displacement` | With `insect_crawl > 0`, UV coordinates jitter randomly, creating shimmering effect |

### Performance Tests

| Test Name | What It Verifies |
|-----------|------------------|
| `test_1080p_60fps` | Rendering 1920×1080 frames maintains ≥60 FPS on reference hardware (GTX 1060 or equivalent) |
| `test_4k_30fps` | Rendering 3840×2160 frames maintains ≥30 FPS on reference hardware |
| `test_memory_stability` | No memory leaks after 10,000 frames (OpenGL objects not increasing) |
| `test_uniform_update_overhead` | Updating all 12 parameters per frame adds <0.1ms latency |

### Regression Tests

- Compare output frames against golden images from VJLive-2 implementation for a set of canonical parameter combinations (e.g., default, arachnophobia, ego_death).
- Ensure that parameter changes do not cause shader recompilation (uniform updates only).

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-5] P5-DM02: bad_trip_datamosh - port from VJLive-2` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### VJLive-2: `plugins/vdatamosh/bad_trip_datamosh.py` (Full File)

```python
"""
Bad Trip Datamosh — The Nightmare Flip

DUAL VIDEO INPUT: tex0 = Video A, tex1 = Video B

"IT WON'T STOP."

This effect simulates a psychedelic crisis. The visuals are aggressive,
hostile, and unsettling. It uses depth to identify the subject and
turn them into a monster. The environment breathes with a sickly
pulse. Spiders crawl under the pixels.

Features:
- Demon Face: Distorts facial depth to look skeletal or demonic.
- Insect Crawl: High-frequency noise that moves like bugs.
- Paranoia Strobe: Random, anxiety-inducing flashes.
- Void Gaze: The center of the screen stares back at you.
- Reality Tear: Screen tearing that reveals the "other side" (Video B).

Metadata:
- Tags: horror, nightmare, bad-trip, paranoia, demons, glitch
- Mood: terrifying, anxious, sick, dark, overwhelming
- Visual Style: psychological-horror, deep-fried, cursed-image, void

Texture unit layout:
  Unit 0: tex0 (Video A)
  Unit 1: texPrev (previous frame)
  Unit 2: depth_tex (depth map)
  Unit 3: tex1 (Video B)
"""

from core.effects.shader_base import Effect
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform sampler2D tex1;
uniform float time;
uniform vec2 resolution;

uniform float u_anxiety;           // Speed/Jitter intensity
uniform float u_demon_face;        // Facial distortion amount
uniform float u_insect_crawl;      // Bug-like noise
uniform float u_void_gaze;         // Dark vignette/hole
uniform float u_reality_tear;      // Glitch tearing
uniform float u_sickness;          // Green/Purple tinting
uniform float u_time_loop;         // Feedback delay echo
uniform float u_breathing_walls;   // UV warping
uniform float u_paranoia;          // Random strobe/cuts
uniform float u_shadow_people;     // Dark depth artifacts
uniform float u_psychosis;         // Color inversion/hue shift
uniform float u_doom;              // Contrast crush

uniform float u_mix;

float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f*f*(3.0-2.0*f);
    return mix(mix(hash(i + vec2(0.0,0.0)), hash(i + vec2(1.0,0.0)), f.x),
               mix(hash(i + vec2(0.0,1.0)), hash(i + vec2(1.0,1.0)), f.x), f.y);
}

void main() {
    vec2 uv = v_uv;
    vec2 texel = 1.0 / resolution;
    bool hasDual = (texture(tex1, vec2(0.5)).r + texture(tex1, vec2(0.5)).g + texture(tex1, vec2(0.5)).b) > 0.001;
    float depth = texture(depth_tex, uv).r;

    // BREATHING WALLS
    if (u_breathing_walls > 0.0) {
        vec2 center = vec2(0.5);
        vec2 d = uv - center;
        float r = length(d);
        float a = atan(d.y, d.x);
        float breath = sin(time * u_anxiety + r * 10.0) * u_breathing_walls * 0.05;
        uv += d * breath;
    }

    // DEMON FACE (Depth Distortion)
    // If depth is near (face), warp it aggressively
    if (depth > 0.2 && u_demon_face > 0.0) {
        float faceWarp = sin(uv.y * 50.0 + time * 10.0) * u_demon_face * 0.02;
        uv.x += faceWarp * smoothstep(0.2, 0.5, depth);
        
        // Hollow eyes effect
        vec2 eyeUV = (uv - 0.5) * vec2(1.0, 2.0); // Rough approximation
        if (length(eyeUV) < 0.1) {
            uv -= (uv - 0.5) * u_demon_face * 0.5;
        }
    }
    
    // INSECT CRAWL
    if (u_insect_crawl > 0.0) {
        float bugs = hash(uv * 100.0 + vec2(time * 10.0, sin(time)));
        if (bugs > 0.95 - u_insect_crawl * 0.05) {
            uv += (vec2(hash(uv), hash(uv+1.0)) - 0.5) * 0.02;
        }
    }

    vec4 color = hasDual ? texture(tex1, uv) : texture(tex0, uv);
    vec4 prev = texture(texPrev, uv);

    // TIME LOOP (Feedback)
    color = mix(color, prev, u_time_loop * 0.5);

    // REALITY TEAR (Glitch)
    if (u_reality_tear > 0.0) {
        float tear = step(0.98 - u_reality_tear * 0.1, hash(vec2(uv.y * 10.0, time)));
        if (tear > 0.5) {
            // Sample the "Other Side" or just invert
            vec4 other = hasDual ? texture(tex0, uv) : vec4(1.0) - color;
            color = mix(color, other, 0.8);
        }
    }

    // SICKNESS (Tint)
    if (u_sickness > 0.0) {
        vec3 sickGreen = vec3(0.2, 0.5, 0.1);
        vec3 sickPurple = vec3(0.4, 0.0, 0.4);
        float sickMix = sin(time * 0.5) * 0.5 + 0.5;
        vec3 sickColor = mix(sickGreen, sickPurple, sickMix);
        color.rgb = mix(color.rgb, color.rgb * sickColor * 2.0, u_sickness * 0.5);
    }
    
    // SHADOW PEOPLE
    if (u_shadow_people > 0.0 && depth < 0.3) {
        // Darken background figures
        color.rgb *= (1.0 - u_shadow_people * 0.8);
    }
    
    // PSYCHOSIS (Hue Shift/Inversion)
    if (u_psychosis > 0.0) {
        color.rgb = abs(color.rgb - vec3(u_psychosis * 0.5));
    }

    // VOID GAZE (Vignette)
    if (u_void_gaze > 0.0) {
        float d = length(v_uv - 0.5);
        color.rgb *= smoothstep(0.8, 0.2, d * (1.0 + u_void_gaze));
    }
    
    // DOOM (Contrast)
    color.rgb = (color.rgb - 0.5) * (1.0 + u_doom) + 0.5;
    
    // PARANOIA (Strobe)
    if (u_paranoia > 0.0 && hash(vec2(time)) > 0.9) {
        color.rgb = vec3(0.0);
    }

    vec4 original = hasDual ? texture(tex1, v_uv) : texture(tex0, v_uv);
    fragColor = mix(original, color, u_mix);
}
"""

class BadTripDatamoshEffect(Effect):
    """
    Bad Trip Datamosh — The Nightmare Flip.
    
    Simulates a terrifying psychedelic experience.
    Features heavy distortion, paranoid strobing, insect-like noise,
    and demonic depth warping. Not for the faint of heart.
    """
    
    PRESETS = {
        "arachnophobia": {
            "anxiety": 8.0, "demon_face": 2.0, "insect_crawl": 10.0,
            "void_gaze": 4.0, "reality_tear": 3.0, "sickness": 4.0,
            "time_loop": 6.0, "breathing_walls": 2.0, "paranoia": 5.0,
            "shadow_people": 8.0, "psychosis": 3.0, "doom": 4.0,
        },
        "ego_death": {
            "anxiety": 2.0, "demon_face": 6.0, "insect_crawl": 2.0,
            "void_gaze": 10.0, "reality_tear": 8.0, "sickness": 2.0,
            "time_loop": 10.0, "breathing_walls": 8.0, "paranoia": 2.0,
            "shadow_people": 0.0, "psychosis": 10.0, "doom": 8.0,
        },
        "schizoid": {
            "anxiety": 10.0, "demon_face": 8.0, "insect_crawl": 5.0,
            "void_gaze": 2.0, "reality_tear": 10.0, "sickness": 8.0,
            "time_loop": 2.0, "breathing_walls": 10.0, "paranoia": 10.0,
            "shadow_people": 10.0, "psychosis": 8.0, "doom": 6.0,
        },
    }

    def __init__(self, name: str = 'bad_trip_datamosh'):
        super().__init__(name, FRAGMENT)
        self.parameters = {
            'anxiety': 6.0, 'demon_face': 4.0, 'insect_crawl': 3.0,
            'void_gaze': 5.0, 'reality_tear': 4.0, 'sickness': 5.0,
            'time_loop': 5.0, 'breathing_walls': 4.0, 'paranoia': 3.0,
            'shadow_people': 4.0, 'psychosis': 2.0, 'doom': 4.0,
        }
        self.audio_mappings = {
            'anxiety': 'high', 'demon_face': 'bass',
            'paranoia': 'energy', 'breathing_walls': 'mid',
        }

    def _map_param(self, name, out_min, out_max):
        val = self.parameters.get(name, 5.0)
        return out_min + (val / 10.0) * (out_max - out_min)

    def apply_uniforms(self, time, resolution, audio_reactor=None, semantic_layer=None):
        super().apply_uniforms(time, resolution, audio_reactor, semantic_layer)
        anxiety = self._map_param('anxiety', 0.0, 10.0)
        demon = self._map_param('demon_face', 0.0, 1.0)
        
        if audio_reactor is not None:
             try:
                anxiety *= (1.0 + audio_reactor.get_energy(0.5) * 0.5)
                demon *= (1.0 + audio_reactor.get_band('bass', 0.0) * 0.5)
             except Exception:
                 pass

        self.shader.set_uniform('u_anxiety', anxiety)
        self.shader.set_uniform('u_demon_face', demon)
        self.shader.set_uniform('u_insect_crawl', self._map_param('insect_crawl', 0.0, 1.0))
        self.shader.set_uniform('u_void_gaze', self._map_param('void_gaze', 0.0, 1.0))
        self.shader.set_uniform('u_reality_tear', self._map_param('reality_tear', 0.0, 1.0))
        self.shader.set_uniform('u_sickness', self._map_param('sickness', 0.0, 1.0))
        self.shader.set_uniform('u_time_loop', self._map_param('time_loop', 0.0, 1.0))
        self.shader.set_uniform('u_breathing_walls', self._map_param('breathing_walls', 0.0, 1.0))
        self.shader.set_uniform('u_paranoia', self._map_param('paranoia', 0.0, 1.0))
        self.shader.set_uniform('u_shadow_people', self._map_param('shadow_people', 0.0, 1.0))
        self.shader.set_uniform('u_psychosis', self._map_param('psychosis', 0.0, 1.0))
        self.shader.set_uniform('u_doom', self._map_param('doom', 0.0, 1.0))
        self.shader.set_uniform('u_mix', 1.0)
        self.shader.set_uniform('depth_tex', 2)
        self.shader.set_uniform('tex1', 3)

    def get_state(self) -> Dict[str, Any]:
        return {'name': self.name, 'enabled': self.enabled, 'parameters': dict(self.parameters)}
```

### VJLive-2: `plugins/core/bad_trip_datamosh/plugin.json` (Manifest)

```json
{
  "id": "bad_trip_datamosh",
  "name": "Bad Trip Datamosh",
  "version": "1.0.0",
  "author": "VJLive",
  "description": "The Nightmare Flip. Simulates a terrifying psychedelic crisis where depth maps turn into demons and insects crawl under the screen. Features 'Paranoia' strobing and 'Reality Tear' glitching. Use Case: Trigger 'Anxiety' and 'Void Gaze' during intense horror sections or chaotic breakdowns.",
  "category": "Datamosh",
  "tags": [
    "datamosh",
    "glitch",
    "effect"
  ],
  "gpu_tier": "MEDIUM",
  "module_path": "plugins.core.bad_trip_datamosh",
  "class_name": "BadTripDatamoshEffect",
  "modules": [
    {
      "id": "bad_trip_datamosh",
      "name": "Bad Trip Datamosh",
      "type": "EFFECT",
      "description": "Bad Trip Datamosh — The Nightmare Flip DUAL VIDEO INPUT: tex0 = Video A, tex1 = Video B \"IT WON'T ST...",
      "module_path": "plugins.core.bad_trip_datamosh",
      "class_name": "BadTripDatamoshEffect",
      "category": "Datamosh",
      "inputs": [
        {
          "name": "signal_in",
          "type": "video"
        }
      ],
      "outputs": [
        {
          "name": "signal_out",
          "type": "video"
        }
      ],
      "parameters": [
        { "name": "anxiety", "label": "Anxiety", "type": "float", "min": 0.0, "max": 10.0, "default": 6.0 },
        { "name": "void_gaze", "label": "Void Gaze", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0 },
        { "name": "time_loop", "label": "Time Loop", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0 },
        { "name": "shadow_people", "label": "Shadow People", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0 }
      ]
    }
  ],
  "parameters": [
    { "name": "anxiety", "label": "Anxiety", "type": "float", "min": 0.0, "max": 10.0, "default": 6.0 },
    { "name": "breathing_walls", "label": "Breathing Walls", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0 },
    { "name": "demon_face", "label": "Demon Face", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0 },
    { "name": "doom", "label": "Doom", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0 },
    { "name": "insect_crawl", "label": "Insect Crawl", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0 },
    { "name": "paranoia", "label": "Paranoia", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0 },
    { "name": "psychosis", "label": "Psychosis", "type": "float", "min": 0.0, "max": 10.0, "default": 2.0 },
    { "name": "reality_tear", "label": "Reality Tear", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0 },
    { "name": "shadow_people", "label": "Shadow People", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0 },
    { "name": "sickness", "label": "Sickness", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0 },
    { "name": "time_loop", "label": "Time Loop", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0 },
    { "name": "void_gaze", "label": "Void Gaze", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0 }
  ]
}
```

---

## Implementation Notes for VJLive3

### Base Class Integration

The effect should inherit from `vjlive3.core.effects.shader_base.Effect` (or the VJLive3 equivalent). The base class provides:

- `__init__(self, name: str, fragment_source: str)`: Compiles the shader program, sets up uniform caching.
- `set_parameter(name: str, value: float)`: Validates and sets parameter values (0-10 range).
- `get_parameter(name: str) -> float`: Retrieves current parameter value.
- `apply_uniforms(time, resolution, audio_reactor=None)`: Called each frame to update uniform values. Override this to perform parameter mapping and set custom uniforms.
- `render(texture_units: dict)`: Called to draw the full-screen pass. The base class binds the vertex array, sets view uniforms, and calls `glDrawArrays`.
- `get_state() -> dict`: Serialize effect state for saving/loading presets.

The `shader` attribute is an instance of `ShaderProgram` (from `shader_base`) which handles uniform location caching via `set_uniform(name, value)`.

### Vertex Shader

The effect uses the standard VJLive3 base vertex shader (from `shader_base.BASE_VERTEX_SHADER`) which provides:
- `in vec2 position` and `in vec2 texCoord`
- `out vec2 v_uv` (local UV)
- Uniforms `u_ViewOffset`, `u_ViewResolution`, `u_TotalResolution` for multi-node stitching

No custom vertex shader is needed.

### Texture Unit Binding Order

The plugin must ensure the following texture bindings before rendering:
```python
self.shader.set_uniform('tex0', 0)      # Video A (bound by engine to unit 0)
self.shader.set_uniform('texPrev', 1)   # Previous frame (unit 1)
self.shader.set_uniform('depth_tex', 2) # Depth (unit 2)
self.shader.set_uniform('tex1', 3)      # Video B (unit 3)
```

The engine's node graph should provide these textures based on the node's inputs:
- `signal_in` → `tex0`
- `depth_in` (optional depth input) → `depth_tex`
- `signal_alt` (optional second video) → `tex1`
- The previous frame is managed by the engine's feedback buffer system and bound to unit 1 automatically.

### Handling Missing Inputs

If the depth input is not connected, the effect should:
- Not crash
- Use a uniform constant depth of 0.5 (mid-depth) by either:
  - Binding a 1×1 texture with value 0.5 to unit 2, OR
  - Setting a uniform `u_use_constant_depth = true` and `u_constant_depth = 0.5` (requires shader modification)
For parity, the first approach (binding a default texture) is simpler and keeps the shader unchanged.

If the alternate video input is not connected, the shader's dual detection will automatically treat it as absent (black), and reality tears will use inverted colors.

### Audio Reactivity

The `audio_reactor` object (if provided) has methods:
- `get_energy(band: float) -> float`: Returns energy in 0.0-1.0 range for frequency band (0.0=bass, 0.5=mid, 1.0=treble)
- `get_band(name: str, time: float) -> float`: Returns current amplitude of named band ('bass', 'mid', 'high', etc.)

The effect multiplies `anxiety` by `(1.0 + energy * 0.5)` and `demon_face` by `(1.0 + bass * 0.5)`. This is a simple linear scaling; more complex audio mapping can be added later.

### Thread Safety

The `Effect` base class is not thread-safe. All `set_parameter()` calls and `render()` invocations must happen on the same thread that owns the OpenGL context (typically the main thread or a dedicated render thread). The plugin should not spawn threads.

### Memory Layout

No special memory layout is required. The effect operates entirely on the GPU. CPU-side state is minimal:
- `parameters`: dict of 12 floats
- `audio_mappings`: dict (constant)
- `name`: str
- `enabled`: bool (from base class)
- `shader`: ShaderProgram object (holds GL program ID, uniform cache)

Total CPU memory per instance: < 2 KB.

## Performance Characteristics

### GPU Load

The fragment shader performs:
- 4 texture samples (color, prev, depth, alt) per fragment
- Several arithmetic operations and conditional branches
- Hash function calls (procedural, no texture)
- No loops (fully parallel per fragment)

**Fill-rate bound**: On modern GPUs, the limiting factor is memory bandwidth for texture reads. At 1080p (2M fragments) and 60 FPS, that's 120M texture fet/sec, which is trivial for any GPU from 2016 onward. At 4K (8.3M fragments), that's 500M fet/sec, requiring ~50 GB/s bandwidth—well within GDDR5/6 capabilities.

**ALU load**: The hash function and simple math are negligible compared to texture fetch latency.

### Optimization Opportunities

If performance is insufficient:
1. **Reduce texture sample count**: In single-video mode, `tex1` could be omitted, but the shader still samples it for dual detection. Could use a uniform flag to skip sampling when not needed.
2. **Half-resolution feedback**: Render `texPrev` at half resolution and upscale, reducing bandwidth for the feedback pass.
3. **Depth skipping**: If no depth-dependent effects are active (`demon_face == 0` and `shadow_people == 0`), the depth texture could be unbound and sampling skipped via uniform flag.

These optimizations are out of scope for initial port but can be added later if profiling indicates need.

## Easter Egg Council

**Idea**: "The Bad Trip Within a Bad Trip" — If all 12 parameters are set exactly to their maximum value (10.0), the shader enters a hidden "overdose" mode where an additional effect triggers: the screen gradually inverts to negative, then to grayscale, then back to color in a cycle that accelerates over time, while a faint but growing heartbeat sound (if audio output is available) syncs to the paranoia strobe. This acknowledges that even the nightmare can be worse. Signed: desktop-roo.

---

**Spec Version**: 1.0-final  
**Last Updated**: 2026-02-28  
**Agent**: desktop-roo  
**Status**: Ready for Review
