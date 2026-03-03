# ChromaticDistortionEffect — Advanced Color Separation with Pattern Distortion

**Task ID:** P3-EXT028  
**Module:** `ChromaticDistortionEffect`  
**Phase:** Pass 2 Fleshing Out  
**Status:** Ready for Phase 3 Review  

---

## Overview

The [`ChromaticDistortionEffect`](docs/specs/_02_fleshed_out/P3-EXT028_ChromaticDistortionEffect.md:97) class implements an advanced chromatic aberration (color separation) effect with multiple distortion patterns and audio reactivity. It belongs to the `distortion` effect category and provides sophisticated control over how RGB channels are spatially separated.

**What This Module Does**

- Separates red, green, and blue color channels with independent offset controls
- Supports four aberration types: radial, horizontal, vertical, and circular
- Applies radial falloff for natural vignette-style color fringing
- Provides four preset configurations for common visual styles
- Integrates with audio reactor for volume-driven aberration modulation
- Uses a custom vertex shader for fullscreen quad rendering

**What This Module Does NOT Do**

- Does not include pattern distortion effects (those are in a separate `PatternDistortionEffect` class in the same file)
- Does not support temporal coherence or frame-to-frame smoothing (per-frame only)
- Does not handle HDR color spaces (operates in standard 8-bit RGB)
- Does not include edge wrapping or mirroring (samples outside viewport return black)
- Does not provide chromatic aberration correction (only artistic distortion)

---

## Detailed Behavior and Parameter Interactions

### Parameter Space and UI Mapping

All user-facing parameters use a normalized `0.0` to `10.0` range from UI sliders. The shader internally remaps these to appropriate mathematical ranges:

| Parameter | UI Range | Internal Range | Purpose |
|-----------|----------|----------------|---------|
| `red_offset` | 0.0-10.0 | 0.0-3.0 | Multiplier for red channel offset |
| `green_offset` | 0.0-10.0 | 0.0-3.0 | Multiplier for green channel offset |
| `blue_offset` | 0.0-10.0 | 0.0-3.0 | Multiplier for blue channel offset |
| `aberration_strength` | 0.0-10.0 | 0.0-0.2 | Base offset magnitude in UV space |
| `center_point` | (0.0-10.0, 0.0-10.0) | (0.0-1.0, 0.0-1.0) | Center of radial/circular patterns |
| `radial_falloff` | 0.0-10.0 | 0.0-2.0 | Distance over which radial effect fades |
| `aberration_type` | 0.0-10.0 | 0, 1, 2, or 3 | 0=radial, 1=horizontal, 2=vertical, 3=circular |

**Note:** `aberration_type` is an integer derived from the UI float: `int(value / 10.0 * 3.0)` maps 0-10 to 0-3.

### Core Algorithm: Channel-Specific Offset Sampling

The effect samples the input texture three times per pixel, once for each color channel, with different UV offsets:

```glsl
float ro = red_offset / 10.0 * 3.0;                // 0-3
float go = green_offset / 10.0 * 3.0;              // 0-3
float bo = blue_offset / 10.0 * 3.0;               // 0-3
float strength = aberration_strength / 10.0 * 0.2;  // 0-0.2

vec2 base_offset = get_aberration_offset(uv, strength, aberration_type, cp, rf);

float r = texture(tex0, uv + base_offset * ro).r;
float g = texture(tex0, uv + base_offset * go).g;
float b = texture(tex0, uv + base_offset * bo).b;
```

Each channel's offset is `base_offset * channel_multiplier`, allowing independent control over how much each color separates.

### Aberration Types

The `get_aberration_offset()` function computes a base offset vector based on the selected pattern:

1. **Radial (type 0)**: Offset radiates from `center_point`. Direction is `normalize(uv - cp)`. Magnitude scales with distance from center, attenuated by `smoothstep(0.0, rf, dist)`:
   ```glsl
   vec2 dir = uv - cp;
   float dist = length(dir);
   float falloff = 1.0 - smoothstep(0.0, rf, dist);
   offset = normalize(dir) * strength * falloff;
   ```

2. **Horizontal (type 1)**: Offset varies horizontally based on distance from centerline:
   ```glsl
   offset.x = strength * (uv.x - 0.5) * 2.0;  // -strength to +strength across screen
   offset.y = 0.0;
   ```

3. **Vertical (type 2)**: Offset varies vertically:
   ```glsl
   offset.y = strength * (uv.y - 0.5) * 2.0;
   offset.x = 0.0;
   ```

4. **Circular (type 3)**: Offset is tangential to the circle around `center_point`:
   ```glsl
   vec2 dir = uv - cp;
   float angle = atan(dir.y, dir.x);
   offset = vec2(cos(angle), sin(angle)) * strength;
   ```

### Preset Configurations

The class provides four preset parameter sets:

- **`subtle_fringe`**: `{red_offset: 2.0, green_offset: 3.3, blue_offset: 4.0, aberration_strength: 1.0, radial_falloff: 3.0}` — gentle color fringe, suitable for background depth enhancement.
- **`rgb_split`**: `{red_offset: 8.0, green_offset: 0.0, blue_offset: 8.0, aberration_strength: 4.0, radial_falloff: 5.0}` — extreme red/blue separation with green locked, creating a dramatic 3D anaglyph effect.
- **`circular_rainbow`**: `{red_offset: 5.0, green_offset: 3.0, blue_offset: 7.0, aberration_strength: 5.0, radial_falloff: 2.0}` — circular pattern with varying channel offsets for rainbow halo.
- **`glitch_shift`**: `{red_offset: 10.0, green_offset: 0.0, blue_offset: 10.0, aberration_strength: 8.0, radial_falloff: 8.0}` — maximum offset with no falloff, simulating a severe digital glitch.

### Audio Reactivity

When an [`AudioAnalyzer`](docs/specs/_02_fleshed_out/P3-EXT028_ChromaticDistortionEffect.md:128) is attached via `set_audio_analyzer()`, the effect creates an [`AudioReactor`](docs/specs/_02_fleshed_out/P3-EXT028_ChromaticDistortionEffect.md:126) that modulates `aberration_strength` based on audio volume:

```python
self.audio_reactor.assign_audio_feature("chromatic_distortion", "aberration_strength", AudioFeature.VOLUME, 0.0, 10.0)
```

During `render()`, the modulated strength is computed:

```python
modulated_strength = self.aberration_strength
if self.audio_reactor:
    modulated_strength = self.audio_reactor.get_audio_modulation("chromatic_distortion", "aberration_strength", self.aberration_strength)
```

The audio modulation scales the base `aberration_strength` parameter (0-10) based on real-time audio volume, creating a pulsating color separation effect that reacts to music.

---

## Public Interface

### Class: `ChromaticDistortionEffect`

**Inheritance:** [`Effect`](docs/specs/_02_fleshed_out/P3-EXT028_ChromaticDistortionEffect.md:97) (from `core.effects.shader_base`)

**Constructor:** `__init__(self)`

Initializes the effect with default parameters:

```python
self.red_offset = 3.3
self.green_offset = 3.3
self.blue_offset = 3.3
self.aberration_strength = 1.0
self.center_point = (5.0, 5.0)  # (x, y) in UI coordinates
self.radial_falloff = 2.5
self.aberration_type = 0  # radial
self.audio_reactor = None
```

**Properties:**

- `name = "chromatic_distortion"` — Effect identifier
- `fragment_shader = CHROMATIC_DISTORTION_FRAGMENT` — GLSL fragment shader
- `vertex_shader = CHROMATIC_DISTORTION_VERTEX` — GLSL vertex shader
- `effect_category = "distortion"`
- `effect_tags = ["chromatic", "aberration", "rgb", "distortion"]`
- `_chaos_rating = {...}` — Internal chaos potential metrics (0.0-1.0 per parameter)

**Methods:**

- `set_audio_analyzer(audio_analyzer)`: Attach an audio analyzer for volume reactivity. Pass `None` to disable.
- `set_parameter(name: str, value: float)`: Set a parameter in the 0-10 UI range. Parameters:
  - `"red_offset"`, `"green_offset"`, `"blue_offset"`: Clamped to [0.0, 10.0]
  - `"aberration_strength"`: Clamped to [0.0, 10.0]
  - `"radial_falloff"`: Clamped to [0.0, 10.0]
  - `"aberration_type"`: Mapped from 0-10 to integer 0-3 via `int(value / 10.0 * 3.0)`
  - `"center_x"`, `"center_y"`: Set individual components of `center_point` (clamped to [0.0, 10.0])
- `get_parameter(name: str) -> float`: Retrieve parameter value in 0-10 UI range. For `aberration_type`, returns `float(self.aberration_type) / 3.0 * 10.0`.
- `render(texture: int, extra_textures: list = None) -> int`: Render the effect to a framebuffer and return the output texture ID. Applies audio modulation if reactor is active.

**Class Attributes:**

- `PRESETS = {...}` — Dictionary of preset parameter configurations (see above).

---

## Inputs and Outputs

### Inputs

| Pin | Type | Description |
|-----|------|-------------|
| `tex0` | `sampler2D` | Input video texture |
| `u_mix` | `float` | Blend factor between original and distorted result (0.0-1.0) |
| `time` | `float` | Shader time in seconds (currently unused but required) |
| `resolution` | `vec2` | Viewport resolution in pixels |

### Uniforms (from Parameters)

All parameters are passed as separate uniforms:

- `red_offset`, `green_offset`, `blue_offset` (float)
- `aberration_strength` (float)
- `center_point` (vec2)
- `radial_falloff` (float)
- `aberration_type` (int)

### Outputs

| Pin | Type | Description |
|-----|------|-------------|
| `fragColor` | `vec4` | RGBA output with distorted color channels |

The output alpha is copied from the original texture's alpha (no modification).

---

## Edge Cases and Error Handling

### Edge Cases

1. **Zero aberration strength**: `aberration_strength = 0` produces `base_offset = 0`, so all channels sample the same UV → output equals input (no distortion).

2. **Extreme channel offsets**: `red_offset = 10.0` → `ro = 3.0`, meaning red channel samples at `uv + 3.0 * base_offset`. This can sample far outside the texture, returning black (0,0,0) for out-of-bounds regions. This is intentional and creates the "glitch" aesthetic.

3. **Center point outside [0,1]**: `center_point` is remapped from UI 0-10 to 0-1. If user sets center_x=10.0, `cp.x = 1.0` (right edge). This is valid but may produce asymmetric distortion.

4. **Radial falloff = 0**: `rf = 0` means `smoothstep(0.0, 0.0, dist)` returns 0 for all `dist > 0`, so `falloff = 1.0 - 0 = 1.0` only at `dist=0`. Practically, the radial effect becomes a point source with no falloff (full strength everywhere except exactly at center where it's 0). This creates an unusual but valid pattern.

5. **Aberration type out of range**: The shader uses `aberration_type` as an `int` in a switch. If the value is not 0-3 (e.g., due to bug), the behavior is undefined (likely falls through all cases and returns `offset = 0`). The Python setter clamps to [0, 3] to prevent this.

6. **Audio reactor not set**: `self.audio_reactor` is `None` by default. `render()` checks and uses base `aberration_strength` directly.

7. **Edge handling**: When `uv + offset` falls outside [0,1]×[0,1], the texture sampler returns black (0,0,0,1) by default (OpenGL behavior). This creates hard black edges at distortion boundaries. No special edge wrapping is implemented.

8. **Mix parameter**: The final `fragColor = mix(original, distorted, u_mix)` allows blending between original and distorted. If `u_mix = 0`, output is original; if `u_mix = 1`, output is fully distorted.

### Error Handling

- **No runtime errors** — all operations are safe GLSL; out-of-bounds texture access returns black, not a crash.
- **Division by zero**: `normalize(dir)` in radial case: if `dir = (0,0)` (pixel exactly at center), `normalize` returns (0,0) by GLSL spec (no division by zero error).
- **Parameter clamping**: Python `set_parameter()` methods clamp all values to valid ranges, preventing invalid uniform uploads.

---

## Mathematical Formulations

### Parameter Remapping

Let UI parameter `p_ui` ∈ [0, 10]. Internal mappings:

```
red/go/bo_offset = p_ui / 10.0 * 3.0        ∈ [0, 3]
aberration_strength = p_ui / 10.0 * 0.2      ∈ [0, 0.2]
center_point = (p_ui_x / 10.0, p_ui_y / 10.0) ∈ [0, 1]²
radial_falloff = p_ui / 10.0 * 2.0           ∈ [0, 2]
aberration_type = int(p_ui / 10.0 * 3.0)     ∈ {0, 1, 2, 3}
```

### Offset Calculation by Type

Given:
- `uv` ∈ [0,1]² normalized coordinates
- `cp` = center point ∈ [0,1]²
- `strength` ∈ [0, 0.2]
- `rf` = radial falloff ∈ [0, 2]

**Radial (type 0)**:
```
dir = uv - cp
dist = |dir|
falloff = 1 - smoothstep(0, rf, dist)
offset = normalize(dir) * strength * falloff
```

**Horizontal (type 1)**:
```
offset = (strength * (uv.x - 0.5) * 2, 0)
```

**Vertical (type 2)**:
```
offset = (0, strength * (uv.y - 0.5) * 2)
```

**Circular (type 3)**:
```
dir = uv - cp
angle = atan(dir.y, dir.x)
offset = (cos(angle), sin(angle)) * strength
```

### Final Color Composition

```
r = tex0(uv + offset * ro).r
g = tex0(uv + offset * go).g
b = tex0(uv + offset * bo).b
distorted = vec4(r, g, b, original.a)
output = mix(original, distorted, u_mix)
```

---

## Performance Characteristics

### Computational Complexity

- **Base cost**: 3 texture samples per pixel (red, green, blue channels separately) + 1 sample for original (for mix) = 4 total.
- **Offset calculation**: O(1) per pixel with simple arithmetic; `normalize()` and `atan()` are moderately expensive but acceptable.
- **No loops** in fragment shader — fully parallel.

### Memory Usage

- **Uniforms**: 7 floats + 1 vec2 + 1 int = 10 uniform values.
- **No framebuffer allocations** beyond the standard `render_to_texture()` call from base class.
- **Vertex shader**: Simple pass-through, no additional buffers.

### GPU Optimization Notes

- The triple texture sampling could be optimized by using a single sample and swizzling if the offset were uniform across channels, but here each channel has a different offset, so three samples are necessary.
- Consider using `textureGather` on GL 4.0+ to sample all four channels at once, then discard the unused alpha. This could reduce sampling to 2-3 taps if clever.
- The `normalize()` and `atan()` calls in the radial/circular types are the most expensive operations; could be approximated with lookup textures or fast math functions if needed for mobile.

---

## Test Plan

**Minimum coverage:** 80% before task is marked done.

### Unit Tests (Python)

1. **Parameter remapping**: Verify all UI→internal conversions are correct (e.g., `red_offset=5.0` → `1.5`).
2. **Aberration type mapping**: Test `aberration_type` setter: `value=0` → 0, `value=3.33` → 1, `value=6.66` → 2, `value=10.0` → 3.
3. **Parameter clamping**: Test that `set_parameter("red_offset", -1.0)` clamps to 0.0, `set_parameter("red_offset", 11.0)` clamps to 10.0.
4. **Center point setter**: Test `center_x` and `center_y` setters update only the respective component.
5. **Audio reactor attachment**: Test `set_audio_analyzer()` correctly creates `AudioReactor` and assigns feature mapping.
6. **Audio reactor None**: Test that passing `None` to `set_audio_analyzer()` sets `self.audio_reactor = None`.
7. **Get parameter symmetry**: For each parameter, verify `get_parameter(name)` returns the value set via `set_parameter(name, value)`.
8. **Preset values**: Verify each preset dictionary contains the expected keys and reasonable values (within 0-10).
9. **Chaos rating**: Verify `_chaos_rating` dictionary exists and all values are floats in [0,1].
10. **Effect metadata**: Verify `effect_category == "distortion"` and `effect_tags` contains expected strings.

### Integration Tests (Shader Rendering)

11. **Radial pattern test**: Render with `aberration_type=0` and verify color separation radiates from center point.
12. **Horizontal pattern test**: Render with `aberration_type=1` and verify separation varies horizontally only.
13. **Vertical pattern test**: Render with `aberration_type=2` and verify separation varies vertically only.
14. **Circular pattern test**: Render with `aberration_type=3` and verify separation follows tangential direction.
15. **Channel independence**: Test that setting only `red_offset` affects only the red channel, not green/blue.
16. **Mix blending**: Test `u_mix=0` produces original, `u_mix=1` produces fully distorted, intermediate values produce blend.
17. **Edge blackening**: Verify that when offset samples outside [0,1] range, those regions become black.
18. **Audio modulation test**: Attach mock audio analyzer and verify `render()` uses modulated strength instead of base.
19. **Preset rendering**: Render with each preset and verify visual distinctiveness (e.g., `rgb_split` should have strong red/blue separation, green intact).
20. **Center point control**: Test moving `center_point` changes distortion origin for radial/circular types.

### Performance Tests

21. **Benchmark 1080p**: Measure frame time with various aberration types; ensure all under 16ms for 60fps.
22. **Texture sample count**: Use GPU profiling to verify exactly 4 texture samples per pixel (3 offset + 1 original).

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass (80% coverage minimum)
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT028: ChromaticDistortionEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

This spec is derived from the following legacy implementations:

- [`core/effects/distortion.py`](home/happy/Desktop/claude projects/VJlive-2/core/effects/distortion.py:1) (VJlive Original) — Full implementation of both `ChromaticDistortionEffect` and `PatternDistortionEffect`. The chromatic distortion shader spans lines 16-80, and the class definition spans lines 97-201.
- [`plugins/vcore/distortion.py`](home/happy/Desktop/claude projects/VJlive-2/plugins/vcore/distortion.py:1) — Identical implementation in plugin format.

The legacy code validates the parameter ranges, default values, preset configurations, and audio reactivity described in this spec. Note that `PatternDistortionEffect` is a separate class in the same file and is **not** part of this task.

---

## Open Questions / [NEEDS RESEARCH]

- **Should aberration_type be an enum or separate parameters?** Currently it's a derived integer from 0-10. Would explicit boolean toggles or a dropdown be more user-friendly? [NEEDS RESEARCH]
- **Audio reactivity beyond volume**: Could we modulate individual channel offsets based on different audio features (bass, mid, treble)? [NEEDS RESEARCH]
- **Edge handling alternatives**: Should we implement edge wrapping or mirroring to avoid black borders? [NEEDS RESEARCH]
- **HDR support**: The current shader assumes 8-bit color. How should we handle floating-point HDR textures? [NEEDS RESEARCH]

---

*— desktop-roo, 2026-03-03*