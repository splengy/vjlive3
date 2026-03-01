# P3-EXT016: BassTherapyDatamoshEffect

**Priority:** P3-EXT (Missing Legacy Effects Parity)
**Status:** Spec Draft
**Assignee:** Desktop Roo Worker
**Estimated Completion:** 3-4 days

---

## 📋 Task Overview

Port the legacy `BassTherapyDatamoshEffect` from VJLive-2 to VJLive3. This is an advanced audio-reactive datamosh effect that combines bass-driven distortion, psychedelic color therapy, and temporal feedback to create a therapeutic yet trippy visual experience. It uses dual video inputs, depth maps, and bass-reactive parameters to create a soothing yet dynamic visual journey.

---

## 🎯 Core Concept

BassTherapyDatamoshEffect is a multi-layered audio-reactive datamosh effect that combines:

- **Dual Video Inputs**: tex0 (primary) and tex1 (secondary/"other side")
- **Depth Integration**: Uses depth map to apply depth-aware distortion and color therapy
- **Bass Reactivity**: Audio-driven parameters that respond to bass frequencies
- **Temporal Feedback**: Previous frame feedback for echo/trail effects
- **Color Therapy**: Psychedelic color palettes and healing color schemes
- **8 Distortion Parameters**: bass_warp, color_healing, temporal_echo, psychedelic_shift, depth_aura, harmonic_blend, resonance_feedback, tranquility
- **Audio Mappings**: bass_warp (bass), color_healing (mid), resonance_feedback (high)
- **3 Presets**: bass_meditation, color_healing, harmonic_resonance

---

## 1. File Structure

```
src/vjlive3/plugins/bass_therapy_datamosh.py
tests/plugins/test_bass_therapy_datamosh.py
```

---

## 2. Class Hierarchy

```python
from vjlive3.plugins.base import Effect
from typing import Dict, Any

class BassTherapyDatamoshEffect(Effect):
    """Bass Therapy Datamosh — The Healing Flip."""

    def __init__(self, name: str = 'bass_therapy_datamosh'):
        # Initialize parameters (8 params)
        # Initialize audio mappings
        pass

    def _map_param(self, name: str, out_min: float, out_max: float) -> float:
        """Map 0-10 parameter to output range."""
        pass

    def apply_uniforms(self, time: float, resolution: Tuple[int, int],
                       audio_reactor=None, semantic_layer=None):
        """Apply all 8 uniforms + audio modulation."""
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
| `bass_warp` | float | 6.0 | 0.0-1.0 | Bass-driven UV distortion intensity |
| `color_healing` | float | 7.0 | 0.0-1.0 | Psychedelic color therapy intensity |
| `temporal_echo` | float | 5.0 | 0.0-1.0 | Feedback delay echo amount |
| `psychedelic_shift` | float | 4.0 | 0.0-1.0 | Color hue and saturation shift |
| `depth_aura` | float | 5.0 | 0.0-1.0 | Depth-aware glow and aura effects |
| `harmonic_blend` | float | 6.0 | 0.0-1.0 | Dual video blending intensity |
| `resonance_feedback` | float | 4.0 | 0.0-1.0 | High-frequency feedback intensity |
| `tranquility` | float | 7.0 | 0.0-1.0 | Overall calming intensity |

**Audio Mappings** (applied in `apply_uniforms`):
- `bass_warp` ← bass level (×1.5)
- `color_healing` ← mid frequency (×1.5)
- `resonance_feedback` ← high frequency energy (×1.5)

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

uniform float u_bass_warp;           // 0-1 (mapped)
uniform float u_color_healing;        // 0-1
uniform float u_temporal_echo;      // 0-1
uniform float u_psychedelic_shift;         // 0-1
uniform float u_depth_aura;         // 0-1
uniform float u_harmonic_blend;      // 0-1
uniform float u_resonance_feedback;      // 0-1
uniform float u_tranquility;              // 0-1

uniform float u_mix;

// Hash function for procedural noise
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

void main() {
    vec2 uv = v_uv;
    vec2 texel = 1.0 / resolution;

    // Check if Video B has any content
    bool hasDual = (texture(tex1, vec2(0.5)).r +
                    texture(tex1, vec2(0.5)).g +
                    texture(tex1, vec2(0.5)).b) > 0.001;

    float depth = texture(depth_tex, uv).r;

    // BASS WARP: Bass-driven UV distortion
    if (u_bass_warp > 0.0) {
        float bass = sin(time * 5.0 + uv.x * 20.0) * u_bass_warp * 0.05;
        uv.x += bass * smoothstep(0.2, 0.8, depth);
    }

    // COLOR HEALING: Psychedelic color therapy
    if (u_color_healing > 0.0) {
        vec3 healingColors[4];
        healingColors[0] = vec3(0.2, 0.8, 0.3); // Green (healing)
        healingColors[1] = vec3(0.8, 0.2, 0.8); // Purple (spiritual)
        healingColors[2] = vec3(0.3, 0.5, 1.0); // Blue (calm)
        healingColors[3] = vec3(1.0, 0.8, 0.2); // Yellow (energy)
        
        int colorIndex = int(mod(time * 0.5, 4.0));
        vec3 healingColor = healingColors[colorIndex];
        
        float healingMix = sin(time * 2.0) * 0.5 + 0.5;
        uv += (vec2(hash(uv * 10.0), hash(uv * 10.0 + 1.0)) - 0.5) * u_color_healing * 0.02;
    }

    // DEPTH AURA: Depth-aware glow
    if (u_depth_aura > 0.0 && depth > 0.1) {
        float auraRadius = 0.1 + u_depth_aura * 0.2;
        float auraIntensity = smoothstep(0.1, 0.3, depth) * u_depth_aura;
        vec2 center = vec2(0.5);
        float dist = length(uv - center);
        if (dist < auraRadius) {
            uv -= (uv - center) * auraIntensity * 0.1;
        }
    }

    // Sample video (A or B depending on availability)
    vec4 color = hasDual ? texture(tex1, uv) : texture(tex0, uv);
    vec4 prev = texture(texPrev, uv);

    // TEMPORAL ECHO: Feedback echo
    color = mix(color, prev, u_temporal_echo * 0.5);

    // PSYCHEDELIC SHIFT: Color hue and saturation
    if (u_psychedelic_shift > 0.0) {
        vec3 hsv = rgb2hsv(color.rgb);
        hsv.x += sin(time * 2.0) * u_psychedelic_shift * 0.5;
        hsv.y = mix(hsv.y, 1.0, u_psychedelic_shift * 0.5);
        color.rgb = hsv2rgb(hsv);
    }

    // HARMONIC BLEND: Dual video blending
    if (hasDual && u_harmonic_blend > 0.0) {
        vec4 other = texture(tex0, uv);
        color = mix(color, other, u_harmonic_blend * 0.5);
    }

    // RESONANCE FEEDBACK: High-frequency feedback
    if (u_resonance_feedback > 0.0) {
        float feedback = hash(uv * 50.0 + vec2(time * 10.0, sin(time)));
        if (feedback > 0.95 - u_resonance_feedback * 0.05) {
            color.rgb = vec3(1.0) - color.rgb;
        }
    }

    // TRANQUILITY: Overall calming effect
    if (u_tranquility > 0.0) {
        color.rgb = mix(color.rgb, vec3(0.8, 0.9, 1.0), u_tranquility * 0.3);
    }

    // Blend with original
    vec4 original = hasDual ? texture(tex1, v_uv) : texture(tex0, v_uv);
    fragColor = mix(original, color, u_mix);
}

// Helper functions for color conversion
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}
```

---

## 6. Effect Layers (Order of Operations)

1. **Bass Warp**: Bass-driven UV distortion based on time and UV position
2. **Color Healing**: Psychedelic color therapy with healing color palettes
3. **Depth Aura**: Depth-aware glow and aura effects
4. **Video Sample**: Sample from tex1 if available, else tex0
5. **Temporal Echo**: Mix with previous frame (feedback)
6. **Psychedelic Shift**: Color hue and saturation adjustments
7. **Harmonic Blend**: Dual video blending when tex1 available
8. **Resonance Feedback**: High-frequency feedback effects
9. **Tranquility**: Overall calming color overlay
10. **Final Blend**: Mix original vs processed by `u_mix`

---

## 7. Audio Reactivity

In `apply_uniforms`, audio modulation is applied:

```python
if audio_reactor:
    try:
        # Bass warp boosted by bass level
        bass_warp *= (1.0 + audio_reactor.get_band('bass', 0.0) * 0.5)

        # Color healing boosted by mid frequencies
        color_healing *= (1.0 + audio_reactor.get_band('mid', 0.0) * 0.5)

        # Resonance feedback boosted by high frequency energy
        resonance_feedback *= (1.0 + audio_reactor.get_energy(0.5) * 0.5)
    except Exception:
        pass  # Silently ignore audio errors
```

**Note**: Audio boost is multiplicative on top of the base 0-10 parameter value after mapping.

---

## 8. Presets (3 Minimum)

The legacy code provides 3 presets. We need at least 5, so we'll add 2 more.

**Legacy Presets**:

1. **`bass_meditation`**: High bass_warp (8), tranquility (9), temporal_echo (6), color_healing (5)
2. **`color_healing`**: High color_healing (10), depth_aura (8), psychedelic_shift (7), tranquility (8)
3. **`harmonic_resonance`**: High harmonic_blend (9), resonance_feedback (7), bass_warp (6), color_healing (6)

**Additional Presets** (required 5 total):

4. **`deep_relaxation`**: High tranquility (10), low bass_warp (2), high temporal_echo (8), low psychedelic_shift (3)
5. **`spiritual_journey`**: High depth_aura (9), high psychedelic_shift (8), high color_healing (7), medium bass_warp (5)

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
- **tex1**: Secondary video ("other side") used in harmonic_blend and as alternative source

The shader checks if tex1 has content by sampling the center pixel and summing RGB channels. If sum > 0.001, it considers tex1 "available".

**Implementation**: Ensure tex1 is bound to texture unit 3 even if not used (can be a black texture or the same as tex0).

---

## 11. Unit Tests (≥ 80% coverage)

**Test File**: `tests/plugins/test_bass_therapy_datamosh.py`

### Critical Tests:

1. **Parameter validation**:
   - All 8 parameters accept 0.0-10.0 values
   - `_map_param()` correctly maps to shader ranges
   - Default values match legacy

2. **Shader compilation**:
   - Fragment shader compiles without errors
   - All 9 uniforms locate correctly (8 params + u_mix)
   - All 4 texture uniforms locate

3. **Effect layer isolation** (unit test each effect by setting one parameter to 1.0, others 0):
   - Bass warp: UV offset proportional to time and bass
   - Color healing: Psychedelic color therapy applied
   - Depth aura: Glow effects only on depth > 0.1
   - Temporal echo: Mix with previous frame
   - Psychedelic shift: Color hue/saturation changes
   - Harmonic blend: Dual video mixing
   - Resonance feedback: High-frequency effects
   - Tranquility: Calming color overlay

4. **Audio modulation**:
   - Bass warp multiplied by bass level
   - Color healing multiplied by mid frequencies
   - Resonance feedback multiplied by high frequency energy
   - Audio boost only applied if audio_reactor present

5. **Dual video detection**:
   - `hasDual` true when tex1 center pixel sum > 0.001
   - When hasDual, uses tex1 as primary sample
   - When not hasDual, falls back to tex0

6. **Depth integration**:
   - Depth aura only active when depth > 0.1
   - Depth sampled correctly from depth_tex

7. **Preset loading**:
   - All 3 legacy presets load correctly
   - 2 new presets (deep_relaxation, spiritual_journey) have valid parameters
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
- Implement parameter definitions (8 parameters)
- Implement `_map_param()` helper
- Implement fragment shader (168 lines)
- Basic `apply_uniforms` structure

### Phase 2: Audio & State (Day 2)
- Implement audio reactivity (3 mappings)
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

## 🔐 Safety Rails Compliance

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

**Source File**: `/home/happy/Desktop/claude projects/VJlive-2/plugins/vdatamosh/bass_therapy_datamosh.py` (248 lines)

**Key Implementation Details**:
- Class: `BassTherapyDatamoshEffect(Effect)`
- Parameters: 8 parameters (bass_warp, color_healing, temporal_echo, psychedelic_shift, depth_aura, harmonic_blend, resonance_feedback, tranquility)
- Audio mappings: bass_warp (bass), color_healing (mid), resonance_feedback (high)
- Fragment shader: 168 lines (lines 38-169)
- Texture units: tex0 (0), texPrev (1), depth_tex (2), tex1 (3)
- Dual video detection: samples center of tex1, checks sum > 0.001
- Effect order: bass → color → depth → sample → echo → shift → blend → feedback → tranquility → blend
- Presets: 3 (bass_meditation, color_healing, harmonic_resonance)

**Porting Notes**:
- Copy shader verbatim (complex but self-contained)
- Preserve parameter mapping: `_map_param(name, out_min, out_max)` uses `val/10.0 * (out_max-out_min) + out_min`
- Audio boost: multiply mapped value by `(1.0 + audio_factor * 0.5)`
- `texPrev` is NOT managed by the effect; the chain must provide and update it
- Dual video check uses `texture(tex1, vec2(0.5))` — ensure tex1 is bound even if unused
- The `u_mix` uniform is set to 1.0 in legacy code; we should respect base class `u_mix` instead (override if needed)
- Depth aura effect only applies when depth > 0.1; ensure depth map is available

---

## ✅ Acceptance Criteria

1. **Functional**:
   - All 8 distortion parameters work independently
   - Dual video switching works (tex1 used when available)
   - Depth map integration correct (depth aura, bass warp)
   - Feedback loop (texPrev) updates correctly
   - Audio reactivity modulates 3 parameters
   - All 5 presets produce distinct therapeutic styles

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
- **Audio Reactor**: Optional, for 3 audio-mapped parameters
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

5. **Parameter Mapping**: The `_map_param()` function is crucial. It maps 0-10 to arbitrary ranges. For example, `bass_warp` maps to 0.0-1.0, but `color_healing` maps to 0.0-1.0. Check the legacy code for each parameter's target range.

6. **Presets**: The legacy presets use values like 8.0, 10.0, etc. These are the raw 0-10 parameter values, not mapped. Store presets as raw parameter dicts.

7. **Testing Strategy**: Because the shader is complex, write unit tests that:
   - Test each effect layer in isolation (set one param to 10, others to 0)
   - Mock the shader to capture uniform values
   - Test texture unit binding order
   - Test audio boost math separately

8. **Performance**: The shader has many conditionals. Modern GPUs handle this well, but on integrated GPUs, consider advising users to disable expensive effects (resonance_feedback, psychedelic_shift) for better FPS.

9. **Safety**: The effect is designed to be therapeutic. Consider adding a "safe mode" preset that limits extreme effects.

10. **Documentation**: This effect is intentionally soothing. Document its therapeutic benefits and warn users about potential visual intensity.

---

**Ready for Implementation after Approval**