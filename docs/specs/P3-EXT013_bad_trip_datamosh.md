# P3-EXT013: BadTripDatamoshEffect

**Priority:** P3-EXT (Missing Legacy Effects Parity)
**Status:** Spec Draft
**Assignee:** TBD
**Estimated Completion:** 3-4 days

---

## 📋 Task Overview

Port the legacy `BadTripDatamoshEffect` from VJLive-2 to VJLive3. This is an advanced datamosh effect that simulates a psychedelic crisis with aggressive distortion, paranoid strobes, insect-like noise, and demonic depth warping. It uses dual video inputs, depth maps, and temporal feedback to create a terrifying visual experience.

---

## 🎯 Core Concept

BadTripDatamoshEffect is a multi-layered horror/datamosh effect that combines:

- **Dual Video Inputs**: tex0 (primary) and tex1 (secondary/"other side")
- **Depth Integration**: Uses depth map to apply face distortion and shadow people effects
- **Temporal Feedback**: Previous frame feedback for echo/trail effects
- **12 Distortion Parameters**: anxiety, demon_face, insect_crawl, void_gaze, reality_tear, sickness, time_loop, breathing_walls, paranoia, shadow_people, psychosis, doom
- **Audio Reactivity**: anxiety (high), demon_face (bass), paranoia (energy), breathing_walls (mid)
- **Procedural Noise**: Hash-based noise for insect crawl and paranoia strobe
- **3 Presets**: arachnophobia, ego_death, schizoid (each with distinct parameter combinations)

The legacy implementation is ~248 lines with a 168-line fragment shader.

---

## 1. File Structure

```
src/vjlive3/plugins/bad_trip_datamosh.py
tests/plugins/test_bad_trip_datamosh.py
```

---

## 2. Class Hierarchy

```python
from vjlive3.plugins.base import Effect
from typing import Dict, Any

class BadTripDatamoshEffect(Effect):
    """Bad Trip Datamosh — The Nightmare Flip."""

    def __init__(self, name: str = 'bad_trip_datamosh'):
        # Initialize parameters (12 params)
        # Initialize audio mappings
        pass

    def _map_param(self, name: str, out_min: float, out_max: float) -> float:
        """Map 0-10 parameter to output range."""
        pass

    def apply_uniforms(self, time: float, resolution: Tuple[int, int],
                       audio_reactor=None, semantic_layer=None):
        """Apply all 12 uniforms + audio modulation."""
        pass

    def get_state(self) -> Dict[str, Any]:
        """Return effect state for serialization."""
        pass
```

---

## 3. Parameters (0.0-10.0)

All parameters use the standard 0.0-10.0 range from UI sliders. They are mapped to shader ranges (typically 0.0-1.0) via `_map_param()`.

| Parameter Name | Type | Default | Shader Range | Description |
|----------------|------|---------|--------------|-------------|
| `anxiety` | float | 6.0 | 0.0-10.0 | Speed/jitter intensity, also affects breathing |
| `demon_face` | float | 4.0 | 0.0-1.0 | Facial depth distortion amount |
| `insect_crawl` | float | 3.0 | 0.0-1.0 | Bug-like noise that moves across screen |
| `void_gaze` | float | 5.0 | 0.0-1.0 | Dark vignette/hole intensity |
| `reality_tear` | float | 4.0 | 0.0-1.0 | Glitch tearing probability |
| `sickness` | float | 5.0 | 0.0-1.0 | Green/purple tinting intensity |
| `time_loop` | float | 5.0 | 0.0-1.0 | Feedback delay echo amount |
| `breathing_walls` | float | 4.0 | 0.0-1.0 | UV warping intensity |
| `paranoia` | float | 3.0 | 0.0-1.0 | Random strobe/cuts probability |
| `shadow_people` | float | 4.0 | 0.0-1.0 | Dark depth artifacts in background |
| `psychosis` | float | 2.0 | 0.0-1.0 | Color inversion/hue shift amount |
| `doom` | float | 4.0 | 0.0-1.0 | Contrast crush multiplier |

**Audio Mappings** (applied in `apply_uniforms`):
- `anxiety` ← high frequency energy (×1.5)
- `demon_face` ← bass level (×1.5)
- `paranoia` ← overall energy (×1.5)
- `breathing_walls` ← mid frequency (×1.5)

---

## 4. Texture Unit Layout

The shader expects 4 textures bound to specific units:

| Texture Unit | Name | Type | Description |
|--------------|------|------|-------------|
| `GL_TEXTURE0` | `tex0` | Video A | Primary video input |
| `GL_TEXTURE1` | `texPrev` | Previous frame | Feedback buffer (same resolution as output) |
| `GL_TEXTURE2` | `depth_tex` | Depth map | Single-channel depth (0.0-1.0) |
| `GL_TEXTURE3` | `tex1` | Video B | Secondary video ("other side") |

**Note**: The `texPrev` texture must be managed by the effect or chain. It should be updated each frame with the previous output (ping-pong buffer or feedback mechanism).

---

## 5. GLSL Fragment Shader (168 lines)

```glsl
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform sampler2D tex1;
uniform float time;
uniform vec2 resolution;

uniform float u_anxiety;           // 0-10 (mapped)
uniform float u_demon_face;        // 0-1
uniform float u_insect_crawl;      // 0-1
uniform float u_void_gaze;         // 0-1
uniform float u_reality_tear;      // 0-1
uniform float u_sickness;          // 0-1
uniform float u_time_loop;         // 0-1
uniform float u_breathing_walls;   // 0-1
uniform float u_paranoia;          // 0-1
uniform float u_shadow_people;     // 0-1
uniform float u_psychosis;         // 0-1
uniform float u_doom;              // 0-1

uniform float u_mix;

// Hash function for procedural noise
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

// Simple noise (not used but present)
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

    // Check if Video B has any content
    bool hasDual = (texture(tex1, vec2(0.5)).r +
                    texture(tex1, vec2(0.5)).g +
                    texture(tex1, vec2(0.5)).b) > 0.001;

    float depth = texture(depth_tex, uv).r;

    // BREATHING WALLS: Radial UV warping
    if (u_breathing_walls > 0.0) {
        vec2 center = vec2(0.5);
        vec2 d = uv - center;
        float r = length(d);
        float a = atan(d.y, d.x);
        float breath = sin(time * u_anxiety + r * 10.0) * u_breathing_walls * 0.05;
        uv += d * breath;
    }

    // DEMON FACE: Depth-based facial distortion
    if (depth > 0.2 && u_demon_face > 0.0) {
        float faceWarp = sin(uv.y * 50.0 + time * 10.0) * u_demon_face * 0.02;
        uv.x += faceWarp * smoothstep(0.2, 0.5, depth);

        // Hollow eyes effect
        vec2 eyeUV = (uv - 0.5) * vec2(1.0, 2.0);
        if (length(eyeUV) < 0.1) {
            uv -= (uv - 0.5) * u_demon_face * 0.5;
        }
    }

    // INSECT CRAWL: High-frequency noise that moves
    if (u_insect_crawl > 0.0) {
        float bugs = hash(uv * 100.0 + vec2(time * 10.0, sin(time)));
        if (bugs > 0.95 - u_insect_crawl * 0.05) {
            uv += (vec2(hash(uv), hash(uv+1.0)) - 0.5) * 0.02;
        }
    }

    // Sample video (A or B depending on availability)
    vec4 color = hasDual ? texture(tex1, uv) : texture(tex0, uv);
    vec4 prev = texture(texPrev, uv);

    // TIME LOOP: Feedback echo
    color = mix(color, prev, u_time_loop * 0.5);

    // REALITY TEAR: Random glitch tearing
    if (u_reality_tear > 0.0) {
        float tear = step(0.98 - u_reality_tear * 0.1, hash(vec2(uv.y * 10.0, time)));
        if (tear > 0.5) {
            vec4 other = hasDual ? texture(tex0, uv) : vec4(1.0) - color;
            color = mix(color, other, 0.8);
        }
    }

    // SICKNESS: Green/Purple tint
    if (u_sickness > 0.0) {
        vec3 sickGreen = vec3(0.2, 0.5, 0.1);
        vec3 sickPurple = vec3(0.4, 0.0, 0.4);
        float sickMix = sin(time * 0.5) * 0.5 + 0.5;
        vec3 sickColor = mix(sickGreen, sickPurple, sickMix);
        color.rgb = mix(color.rgb, color.rgb * sickColor * 2.0, u_sickness * 0.5);
    }

    // SHADOW PEOPLE: Darken background (low depth)
    if (u_shadow_people > 0.0 && depth < 0.3) {
        color.rgb *= (1.0 - u_shadow_people * 0.8);
    }

    // PSYCHOSIS: Color inversion/hue shift
    if (u_psychosis > 0.0) {
        color.rgb = abs(color.rgb - vec3(u_psychosis * 0.5));
    }

    // VOID GAZE: Dark vignette
    if (u_void_gaze > 0.0) {
        float d = length(v_uv - 0.5);
        color.rgb *= smoothstep(0.8, 0.2, d * (1.0 + u_void_gaze));
    }

    // DOOM: Contrast crush
    color.rgb = (color.rgb - 0.5) * (1.0 + u_doom) + 0.5;

    // PARANOIA: Random strobe blackout
    if (u_paranoia > 0.0 && hash(vec2(time)) > 0.9) {
        color.rgb = vec3(0.0);
    }

    // Blend with original
    vec4 original = hasDual ? texture(tex1, v_uv) : texture(tex0, v_uv);
    fragColor = mix(original, color, u_mix);
}
```

---

## 6. Effect Layers (Order of Operations)

1. **Breathing Walls**: UV warping based on radius and time (anxiety controls speed)
2. **Demon Face**: Depth-triggered facial distortion (only if depth > 0.2)
3. **Insect Crawl**: Random UV offsets from hash noise
4. **Video Sample**: Sample from tex1 if available, else tex0
5. **Time Loop**: Mix with previous frame (feedback)
6. **Reality Tear**: Random glitch that swaps to other video or inverted
7. **Sickness**: Green/purple tint overlay
8. **Shadow People**: Darken background (depth < 0.3)
9. **Psychosis**: Color inversion via `abs(color - threshold)`
10. **Void Gaze**: Radial vignette darkening
11. **Doom**: Contrast adjustment (multiply around 0.5)
12. **Paranoia**: Random full blackout (10% chance when paranoia > 0)
13. **Final Blend**: Mix original vs processed by `u_mix`

---

## 7. Audio Reactivity

In `apply_uniforms`, audio modulation is applied:

```python
if audio_reactor:
    try:
        # Anxiety boosted by high-frequency energy
        anxiety *= (1.0 + audio_reactor.get_energy(0.5) * 0.5)

        # Demon face boosted by bass
        demon *= (1.0 + audio_reactor.get_band('bass', 0.0) * 0.5)

        # Paranoia boosted by overall energy
        paranoia *= (1.0 + audio_reactor.get_energy(0.5) * 0.5)

        # Breathing walls boosted by mid frequencies
        breathing_walls *= (1.0 + audio_reactor.get_band('mid', 0.0) * 0.5)
    except Exception:
        pass  # Silently ignore audio errors
```

**Note**: Audio boost is multiplicative on top of the base 0-10 parameter value after mapping.

---

## 8. Presets (3 Minimum)

The legacy code provides 3 presets. We need at least 5, so we'll add 2 more.

**Legacy Presets**:

1. **`arachnophobia`**: High insect_crawl (10), shadow_people (8), anxiety (8), demon_face (2)
2. **`ego_death`**: High void_gaze (10), reality_tear (8), time_loop (10), psychosis (10), breathing_walls (8)
3. **`schizoid`**: High anxiety (10), paranoia (10), breathing_walls (10), reality_tear (10), shadow_people (10)

**Additional Presets** (required 5 total):

4. **`demon_worship`**: High demon_face (9), doom (8), sickness (7), void_gaze (6)
5. **`mild_trip`**: All parameters around 3-4, low paranoia (1), low reality_tear (2) — for subtle effect

---

## 9. Texture Feedback Management

The `texPrev` texture requires careful management:

- **Creation**: Create a texture with same dimensions as output (resolution)
- **Format**: GL_RGBA16F or GL_RGBA8 (depending on quality needs)
- **Update**: After rendering the effect, the output framebuffer should be copied to `texPrev` for the next frame
- **Chain Integration**: The effect itself does not manage `texPrev`; the rendering chain must provide it

**Implementation Note**: The effect's `apply_uniforms` only binds the texture. The chain must ensure `texPrev` is updated each frame. This is typically done with a ping-pong framebuffer pair.

---

## 10. Dual Video Support

The effect supports two video inputs:

- **tex0**: Primary video (always provided)
- **tex1**: Secondary video ("other side") used in reality_tear and as alternative source

The shader checks if tex1 has content by sampling the center pixel and summing RGB channels. If sum > 0.001, it considers tex1 "available".

**Implementation**: Ensure tex1 is bound to texture unit 3 even if not used (can be a black texture or the same as tex0).

---

## 11. Unit Tests (≥ 80% coverage)

**Test File**: `tests/plugins/test_bad_trip_datamosh.py`

### Critical Tests:

1. **Parameter validation**:
   - All 12 parameters accept 0.0-10.0 values
   - `_map_param()` correctly maps to shader ranges
   - Default values match legacy

2. **Shader compilation**:
   - Fragment shader compiles without errors
   - All 13 uniforms locate correctly (12 params + u_mix)
   - All 4 texture uniforms locate

3. **Effect layer isolation** (unit test each effect by setting one parameter to 1.0, others 0):
   - Breathing walls: UV offset proportional to radius and time
   - Demon face: Only affects depth > 0.2, warps UV.x
   - Insect crawl: Random UV jitter when hash threshold exceeded
   - Time loop: Mix with previous frame
   - Reality tear: Random frame replacement based on hash
   - Sickness: Green/purple tint applied
   - Shadow people: Darkens when depth < 0.3
   - Psychosis: Color inversion
   - Void gaze: Radial vignette
   - Doom: Contrast adjustment
   - Paranoia: Random black frames

4. **Audio modulation**:
   - Anxiety multiplied by high-frequency energy
   - Demon face multiplied by bass
   - Paranoia multiplied by energy
   - Breathing walls multiplied by mid
   - Audio boost only applied if audio_reactor present

5. **Dual video detection**:
   - `hasDual` true when tex1 center pixel sum > 0.001
   - When hasDual, uses tex1 as primary sample
   - When not hasDual, falls back to tex0

6. **Depth integration**:
   - Demon face only active when depth > 0.2
   - Shadow people only active when depth < 0.3
   - Depth sampled correctly from depth_tex

7. **Preset loading**:
   - All 3 legacy presets load correctly
   - 2 new presets (demon_worship, mild_trip) have valid parameters
   - Preset parameters within 0-10 range

8. **Texture unit binding**:
   - tex0 → unit 0
   - texPrev → unit 1
   - depth_tex → unit 2
   - tex1 → unit 3

9. **Edge cases**:
   - Zero parameters → no effect
   - Max parameters (10) → extreme distortion
   - Missing depth texture → depth = 0 (safe)
   - Missing texPrev → prev = black (safe)

---

## 12. Performance Tests

- **Shader Compile**: < 30ms (complex shader with many conditionals)
- **Texture Uploads**: 4 textures bound per frame
- **FPS Impact**: < 15% on integrated GPU (many effects are conditional)
- **Memory**: 1 feedback texture (same size as output) ≈ 8-16 MB

---

## 13. Visual Regression Tests

Capture reference frames with:
- Static scene with depth map
- Moving subject (depth changes)
- Dual video inputs (tex1 different from tex0)
- All 5 presets
- Audio reactivity (with/without audio)
- Extreme parameter values (all 10.0)

---

## 14. Implementation Phases

### Phase 1: Foundation (Day 1)
- Create plugin file with class skeleton
- Implement parameter definitions (12 parameters)
- Implement `_map_param()` helper
- Implement fragment shader (168 lines)
- Basic `apply_uniforms` structure

### Phase 2: Audio & State (Day 2)
- Implement audio reactivity (4 mappings)
- Implement `get_state()` serialization
- Test texture unit binding
- Test dual video detection

### Phase 3: Feedback Integration (Day 3)
- Document `texPrev` management requirements
- Create helper for chain to allocate feedback texture
- Test with ping-pong framebuffer

### Phase 4: Testing & Validation (Day 4)
- Write unit tests (target 85% coverage)
- Performance testing
- Visual regression captures
- Safety rails verification

---

## 🔒 Safety Rails Compliance

| Rail | Compliance Strategy |
|------|---------------------|
| **60 FPS Sacred** | Many effects are conditional (only run if param > 0); feedback texture doubles memory but not compute |
| **Offline-First** | No network calls; all local |
| **Plugin Integrity** | `METADATA` constant with name, version, description, author, license |
| **750-Line Limit** | Expected ~300 lines total (well under limit) |
| **80% Test Coverage** | Unit tests targeting 85%+ (parameters, audio, texture units, effect layers) |
| **No Silent Failures** | Shader compilation errors raise `RuntimeError`; audio errors logged but not fatal |
| **Resource Leak Prevention** | No GL resources allocated by effect itself (textures provided by chain); `texPrev` managed by chain |
| **Backward Compatibility** | New plugin, no compatibility concerns |
| **Security** | No user input in shader strings; all uniforms validated |

---

## 🎨 Legacy Reference Analysis

**Source File**: `/home/happy/Desktop/claude projects/VJlive-2/plugins/vdatamosh/bad_trip_datamosh.py` (248 lines)

**Key Implementation Details**:
- Class: `BadTripDatamoshEffect(Effect)`
- Parameters: 12 parameters (anxiety, demon_face, insect_crawl, void_gaze, reality_tear, sickness, time_loop, breathing_walls, paranoia, shadow_people, psychosis, doom)
- Audio mappings: anxiety (high), demon_face (bass), paranoia (energy), breathing_walls (mid)
- Fragment shader: 168 lines (lines 38-169)
- Texture units: tex0 (0), texPrev (1), depth_tex (2), tex1 (3)
- Dual video detection: samples center of tex1, checks sum > 0.001
- Effect order: breathing → demon → insect → sample → time_loop → tear → sickness → shadow → psychosis → void → doom → paranoia → blend
- Presets: 3 (arachnophobia, ego_death, schizoid)

**Porting Notes**:
- Copy shader verbatim (complex but self-contained)
- Preserve parameter mapping: `_map_param(name, out_min, out_max)` uses `val/10.0 * (out_max-out_min) + out_min`
- Audio boost: multiply mapped value by `(1.0 + audio_factor * 0.5)`
- `texPrev` is NOT managed by the effect; the chain must provide and update it
- Dual video check uses `texture(tex1, vec2(0.5))` — ensure tex1 is bound even if unused
- The `u_mix` uniform is set to 1.0 in legacy code; we should respect base class `u_mix` instead (override if needed)
- Shadow people effect only applies when `depth < 0.3`; ensure depth map is available

---

## ✅ Acceptance Criteria

1. **Functional**:
   - All 12 distortion parameters work independently
   - Dual video switching works (tex1 used when available)
   - Depth map integration correct (demon face, shadow people)
   - Feedback loop (texPrev) updates correctly
   - Audio reactivity modulates 4 parameters
   - All 5 presets produce distinct horror styles

2. **Performance**:
   - Shader compile < 30ms
   - FPS impact < 15% on integrated GPU
   - No texture allocation stalls

3. **Quality**:
   - No shader compilation warnings
   - Smooth animation (no jittering unless intended by parameters)
   - Clean feedback loop (no ghosting artifacts unless intended)

4. **Testing**:
   - Unit test coverage ≥ 80%
   - All tests pass
   - Visual regression baseline captured

5. **Safety**:
   - All safety rails satisfied
   - No GL texture leaks (chain-managed)
   - Proper error handling for missing depth/texPrev

---

## 🔗 Dependencies

- **Base Class**: `vjlive3.plugins.base.Effect`
- **Textures**: tex0 (video A), texPrev (feedback), depth_tex (depth), tex1 (video B)
- **Audio Reactor**: Optional, for 4 audio-mapped parameters
- **Chain**: Must provide feedback texture management (texPrev)

---

## 📊 Success Metrics

- FPS: ≥ 60 with moderate parameter levels
- Test Coverage: ≥ 80%
- Lines of Code: ≤ 300
- Shader Compile: < 30ms
- Memory: < 20 MB (including feedback texture)

---

## 📝 Notes for Implementation Engineer

1. **Feedback Texture**: The most critical integration point. The effect does NOT manage `texPrev`. You must document that the chain needs to:
   - Allocate a texture matching output resolution
   - Bind it to texture unit 1 before calling `apply_uniforms`
   - After rendering, copy the output to this texture for next frame (glCopyTexImage2D or FBO ping-pong)

2. **Depth Map**: The effect expects a single-channel depth texture (0.0-1.0). Ensure the chain provides it. If no depth, the effect should still work (depth defaults to 0, disabling depth-based effects).

3. **Dual Video**: The effect checks tex1 availability by sampling center pixel. If you want to force single-video mode, bind a black texture to tex1.

4. **Audio Reactivity**: The legacy code uses `audio_reactor.get_energy(0.5)` and `audio_reactor.get_band('bass', 0.0)`. Ensure your audio reactor implements these methods. If not, adapt to available API.

5. **Parameter Mapping**: The `_map_param()` function is crucial. It maps 0-10 to arbitrary ranges. For example, `demon_face` maps to 0.0-1.0, but `anxiety` maps to 0.0-10.0. Check the legacy code for each parameter's target range.

6. **Presets**: The legacy presets use values like 8.0, 10.0, etc. These are the raw 0-10 parameter values, not mapped. Store presets as raw parameter dicts.

7. **Testing Strategy**: Because the shader is complex, write unit tests that:
   - Test each effect layer in isolation (set one param to 10, others to 0)
   - Mock the shader to capture uniform values
   - Test texture unit binding order
   - Test audio boost math separately

8. **Performance**: The shader has many conditionals. Modern GPUs handle this well, but on integrated GPUs, consider advising users to disable expensive effects (insect_crawl, reality_tear, paranoia) for better FPS.

9. **Safety**: The effect can be quite extreme. Consider adding a "safe mode" preset that limits doom, psychosis, and paranoia to low values.

10. **Documentation**: This effect is intentionally disturbing. Document its psychological impact and warn users before enabling.

---

**Ready for Implementation after Approval**
