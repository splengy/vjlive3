# P3-EXT017: BenDayDotsEffect

**Task ID:** P3-EXT017  
**Plugin:** BenDayDotsEffect (Ben-Day Dots)  
**Priority:** P0  
**Status:** ⬜ Todo  
**Source:** vjlive (core/vstyle/pop_art_effects.py)  
**Target:** `src/vjlive3/plugins/ben_day_dots.py`

---

## 📋 Task Overview

Port the **BenDayDotsEffect** from VJLive-2 to VJLive3. This is a Pop Art style halftone dot effect inspired by Roy Lichtenstein's comic book aesthetic. It converts the video into a grid of dots whose size is determined by brightness, creating an authentic CMYK printing simulation.

**Key Features:**
- Halftone dot grid with configurable density
- Dot size scales with image luminance (brighter = smaller dots)
- Authentic Pop Art color palette (Primary Red, Metallic Yellow)
- Audio reactivity via `adrenaline` parameter (dots expand with energy)
- Simple, performant shader (~106 lines)
- 4 user parameters + 2 color uniforms

---

## 🎯 Core Concept

> "Ben-Day Dots Effect (Roy Lichtenstein Style)"

The effect transforms any video into a Pop Art masterpiece:
- Image is divided into a regular grid (density determines cell size)
- Each cell contains a circular dot
- Dot radius is inversely proportional to pixel brightness (darker = larger dots)
- Two-color palette: primary color for dots, secondary color for background
- Adrenaline parameter expands dots for high-energy moments
- Mix control blends effect with original video

This is a classic comic book printing technique recreated in real-time GLSL.

---

## 📁 File Structure

```
src/vjlive3/plugins/ben_day_dots.py
tests/plugins/test_ben_day_dots.py
```

---

## 1. Class Hierarchy

```python
from core.effects.shader_base import Effect
from core.audio_reactor import AudioReactor
import logging

logger = logging.getLogger(__name__)

class BenDayDotsEffect(Effect):
    """Ben-Day Dots Effect (Roy Lichtenstein Style)."""

    def __init__(self):
        # Inline shader (106 lines)
        fragment_source = self._get_fragment_shader()
        super().__init__("ben_day_dots", fragment_source)

        self.description = "Comic book halftone dots in Pop Art style"
        self.category = "Style"

        # Color palette (Pop Art colors)
        self.primary_color = [0.996, 0.0, 0.0]      # Primary Red #FE0000
        self.secondary_color = [0.996, 0.839, 0.082] # Metallic Yellow #FED715

        # Parameters (0.0-10.0)
        self.parameters = {
            'dot_scale': 1.0,      # Overall dot size multiplier
            'grid_density': 80.0,  # Number of dots per width (cells)
            'mix': 1.0,            # Effect blend amount (0=original, 1=full dots)
            'adrenaline_boost': 0.0  # Audio-driven expansion (set dynamically)
        }

        self.audio_reactor = None

    def _get_fragment_shader(self) -> str:
        """Return the 106-line GLSL shader."""
        return """#version 330 core
        // Full shader below
        """

    def set_audio_reactor(self, audio_reactor: AudioReactor):
        """Set audio reactor for adrenaline parameter."""
        self.audio_reactor = audio_reactor

    def apply_uniforms(self, time: float, resolution: tuple,
                       audio_reactor=None, semantic_layer=None):
        """Apply all uniforms including colors and audio-derived adrenaline."""
        super().apply_uniforms(time, resolution, audio_reactor, semantic_layer)

        # Set Pop Art colors
        self.shader.set_uniform("u_primary_color", self.primary_color)
        self.shader.set_uniform("u_secondary_color", self.secondary_color)

        # Get adrenaline from audio reactor or use 0
        adrenaline = 0.0
        if audio_reactor:
            # Try multiple methods for compatibility
            if hasattr(audio_reactor, 'get_adrenaline_level'):
                adrenaline = audio_reactor.get_adrenaline_level()
            elif hasattr(audio_reactor, 'audio_energy'):
                adrenaline = getattr(audio_reactor, 'audio_energy', 0.0)
            elif hasattr(audio_reactor, 'get_feature_level'):
                # Use bass as proxy for adrenaline
                try:
                    from core.audio_analyzer import AudioFeature
                    adrenaline = audio_reactor.get_feature_level(AudioFeature.BASS)
                except:
                    adrenaline = 0.0

        self.shader.set_uniform("u_adrenaline", adrenaline)

        # Set other parameters
        self.shader.set_uniform("u_dot_scale", self.parameters['dot_scale'])
        self.shader.set_uniform("u_grid_density", self.parameters['grid_density'])
        self.shader.set_uniform("u_mix", self.parameters['mix'])

    def __del__(self):
        """Cleanup if needed."""
        try:
            if hasattr(super(), '__del__'): super().__del__()
        except: pass

def create_ben_day_dots():
    return BenDayDotsEffect()
```

---

## 2. Parameters (0.0-10.0)

All parameters are in the standard 0.0-10.0 range and are mapped to appropriate GLSL ranges.

| Parameter | Shader Uniform | Default | GLSL Range | Description |
|-----------|----------------|---------|------------|-------------|
| `dot_scale` | `u_dot_scale` | 1.0 | 0.0-10.0 (multiplier) | Overall dot size multiplier. 1.0 = base size, >1.0 larger dots, <1.0 smaller dots |
| `grid_density` | `u_grid_density` | 80.0 | 10.0-200.0 (cells) | Number of dot cells across the screen width. Higher = smaller, more numerous dots |
| `mix` | `u_mix` | 1.0 | 0.0-1.0 | Blend factor: 0.0 = original video, 1.0 = full dot effect |
| `adrenaline_boost` | `u_adrenaline` | 0.0 | 0.0-1.0 (set dynamically) | Audio-driven dot expansion. Not user-controlled; set via `apply_uniforms` from audio reactor |

**Note:** `adrenaline_boost` is not a user parameter; it's computed each frame from audio.

---

## 3. GLSL Fragment Shader (106 lines)

```glsl
#version 330 core
in vec2 v_texcoord;
out vec4 fragColor;

uniform sampler2D tex0;
uniform float u_adrenaline;
uniform float u_dot_scale;
uniform float u_grid_density;
uniform vec3 u_primary_color;
uniform vec3 u_secondary_color;
uniform float u_mix;

void main() {
    // Sample original video
    vec4 tex = texture(tex0, v_texcoord);

    // Convert to grayscale (luminance)
    float gray = dot(tex.rgb, vec3(0.299, 0.587, 0.114));

    // Calculate grid cell coordinates
    vec2 grid = fract(v_texcoord * u_grid_density);

    // Distance from cell center (0,0) to cell pixel
    float dist = distance(grid, vec2(0.5));

    // Base radius: darker pixels = larger dots
    // gray=0 (black) → radius=0.5, gray=1 (white) → radius=0
    float base_radius = 0.5 * (1.0 - gray);

    // Adrenaline boost: audio energy expands dots
    float adrenaline_boost = u_adrenaline * 0.2;

    // Final radius with scale and adrenaline
    float radius = base_radius * u_dot_scale + adrenaline_boost;

    // Create circular mask: 1 inside dot, 0 outside
    float mask = step(radius, dist);

    // Color: interpolate between primary and secondary based on gray
    vec3 color = mix(u_primary_color, u_secondary_color, gray);

    // Apply mask: dot color where mask=0, background where mask=1
    vec3 final_color = color * mask;

    // Blend with original video based on u_mix
    final_color = mix(tex.rgb, final_color, u_mix);

    fragColor = vec4(final_color, tex.a);
}
```

**Line Count:** 42 lines (compact). The legacy inline shader is 42 lines; we'll keep it concise.

**Uniforms:**
- `tex0` - input video
- `u_adrenaline` - audio-driven expansion (0-1)
- `u_dot_scale` - dot size multiplier (0-10)
- `u_grid_density` - number of cells (10-200)
- `u_primary_color` - RGB vec3 for dots
- `u_secondary_color` - RGB vec3 for background
- `u_mix` - blend amount (0-1)

---

## 4. Audio Reactivity

The effect responds to audio via the `adrenaline` uniform:

**Source:** `audio_reactor` (passed to `apply_uniforms` or set via `set_audio_reactor`)

**Mapping:**
- Try `audio_reactor.get_adrenaline_level()` (preferred)
- Fallback: `audio_reactor.audio_energy`
- Fallback: `audio_reactor.get_feature_level(AudioFeature.BASS)`
- Default: 0.0 if no audio reactor or methods fail

**Effect on Shader:**
```glsl
float adrenaline_boost = u_adrenaline * 0.2;
float radius = base_radius * u_dot_scale + adrenaline_boost;
```
When audio energy is high, dots expand by up to 0.2 units, making the halftone pattern more pronounced during bass hits.

---

## 5. Color Palette

The effect uses authentic Pop Art colors from the legacy `PopArtColorPalette` class:

**Default Palette:**
- **Primary Red:** `[0.996, 0.0, 0.0]` (#FE0000)
- **Metallic Yellow:** `[0.996, 0.839, 0.082]` (#FED715)

These are hardcoded in the plugin for simplicity. The legacy code loads from a JSON preset, but we'll use defaults directly.

**Future Extension:** Could add `set_color_palette(primary, secondary)` method for runtime changes.

---

## 6. Presets (5 Minimum)

Create 5 presets demonstrating different Pop Art styles:

### 1. `classic_lichtenstein` (Legacy)
- **Description:** Authentic Roy Lichtenstein comic book style
- **Parameters:**
  - `dot_scale`: 1.0
  - `grid_density`: 80.0
  - `mix`: 1.0
- **Colors:** Primary Red + Metallic Yellow (default)

### 2. `high_contrast` (Legacy)
- **Description:** More dramatic dots with higher contrast
- **Parameters:**
  - `dot_scale`: 1.5
  - `grid_density`: 60.0
  - `mix`: 1.0

### 3. `subtle_halftone` (Legacy)
- **Description:** Subtle newspaper printing effect
- **Parameters:**
  - `dot_scale`: 0.7
  - `grid_density`: 120.0
  - `mix`: 0.6 (blend more with original)

### 4. `adrenaline_punk` (New)
- **Description:** Audio-reactive expanding dots for high-energy sets
- **Parameters:**
  - `dot_scale`: 1.2
  - `grid_density`: 70.0
  - `mix`: 1.0
- **Audio:** Adrenaline boost prominent

### 5. `retro_comic` (New)
- **Description:** Bold, exaggerated Pop Art with large dots
- **Parameters:**
  - `dot_scale`: 2.0
  - `grid_density`: 50.0
  - `mix`: 1.0

**Preset Storage:** Store as dicts with parameter values. Colors are fixed (not part of presets).

---

## 7. Unit Tests (≥ 80% coverage)

**Test File:** `tests/plugins/test_ben_day_dots.py`

### Critical Tests:

#### Initialization
- [ ] `test_plugin_creates_with_correct_name()`
- [ ] `test_plugin_initializes_default_parameters()`
- [ ] `test_plugin_has_4_parameters()`
- [ ] `test_plugin_initializes_pop_art_colors()`
- [ ] `test_plugin_creates_shader_with_40_plus_lines()`

#### Parameter System
- [ ] `test_set_parameter_valid_range_0_to_10()`
- [ ] `test_set_parameter_rejects_negative()`
- [ ] `test_set_parameter_rejects_over_10()`
- [ ] `test_get_parameter_returns_current_value()`
- [ ] `test_parameters_persist_across_frames()`

#### Shader Compilation
- [ ] `test_shader_compiles_without_errors()`
- [ ] `test_shader_has_all_required_uniforms()`
- [ ] `test_shader_has_7_uniforms()`
- [ ] `test_shader_uses_correct_texture_unit_for_tex0()`

#### Halftone Math
- [ ] `test_gray_conversion_correct()`
- [ ] `test_grid_calculation_with_density_80()`
- [ ] `test_base_radius_inversely_proportional_to_gray()`
- [ ] `test_radius_includes_dot_scale_and_adrenaline()`
- [ ] `test_mask_step_function_creates_circle()`

#### Color & Blend
- [ ] `test_primary_and_secondary_colors_set_correctly()`
- [ ] `test_color_mix_interpolates_by_gray()`
- [ ] `test_final_color_blends_with_original_by_mix()`
- [ ] `test_mix_0_returns_original()`
- [ ] `test_mix_1_returns_full_dots()`

#### Audio Reactivity
- [ ] `test_audio_reactor_set_and_used()`
- [ ] `test_adrenaline_from_get_adrenaline_level()`
- [ ] `test_adrenaline_fallback_to_audio_energy()`
- [ ] `test_adrenaline_fallback_to_bass_feature()`
- [ ] `test_adrenaline_defaults_to_0_without_reactor()`
- [ ] `test_adrenaline_boost_in_radius_calculation()`

#### Uniform Application
- [ ] `test_apply_uniforms_sets_all_parameters()`
- [ ] `test_apply_uniforms_sets_colors()`
- [ ] `test_apply_uniforms_sets_adrenaline_from_audio()`
- [ ] `test_apply_uniforms_calls_super()`

#### Edge Cases
- [ ] `test_black_pixel_produces_large_dot()`
- [ ] `test_white_pixel_produces_no_dot()`
- [ ] `test_gray_mid_produces_medium_dot()`
- [ ] `test_extreme_grid_density_handled()`
- [ ] `test_zero_dot_scale_results_in_no_dots()`

#### Performance
- [ ] `test_frame_budget_under_1ms()`
- [ ] `test_shader_compile_time_under_20ms()`

**Target Coverage:** 85% (35+ tests)

---

## 8. Performance Tests

- **Frame Budget:** ≤ 1.0ms per frame (very simple shader)
- **Shader Compilation:** ≤ 20ms
- **Memory:** Minimal (no extra textures)
- **Texture Binds:** 1 (tex0 only)
- **GPU:** Should run easily on integrated GPUs at 4K resolution

---

## 9. Visual Regression Tests

Capture reference frames with:
1. **Original video** (mix=0) vs **full effect** (mix=1)
2. **Grid density variations:** 40, 80, 160
3. **Dot scale variations:** 0.5, 1.0, 2.0
4. **Brightness gradient:** Test black→white dot size progression
5. **Adrenaline boost:** No audio vs high bass (dots expand)
6. **Color palette:** Red/Yellow vs alternative colors
7. **Edge cases:** All-black frame, all-white frame, noise

Compare against legacy reference images.

---

## 10. Implementation Phases

### Phase 1: Foundation (Day 1)
- Create plugin file `src/vjlive3/plugins/ben_day_dots.py`
- Implement `__init__` with parameters and colors
- Implement `_get_fragment_shader()` with inline 106-line GLSL
- Write 10 initial unit tests

**Success:** Plugin loads, shader compiles, parameters accessible

### Phase 2: Audio Reactivity (Day 2)
- Implement `set_audio_reactor()`
- Implement `apply_uniforms()` with audio-derived adrenaline
- Write 10 audio reactivity tests

**Success:** Adrenaline uniform updates correctly from audio

### Phase 3: Testing & Validation (Day 2-3)
- Complete unit tests (reach 85% coverage)
- Performance testing
- Visual regression captures
- Create 5 presets
- Safety Rails compliance verification

**Success:** All tests pass, performance within budget, presets functional

---

## 🔒 Safety Rails Compliance

| Rail | Requirement | Compliance |
|------|-------------|------------|
| **60 FPS Sacred** | ≤ 16.67ms per frame | Target ≤ 1ms; extremely simple shader ✓ |
| **Offline-First** | No cloud dependencies | No network calls ✓ |
| **Plugin Integrity** | METADATA constant | Add to plugin ✓ |
| **750-Line Limit** | ≤ 750 lines of code | Estimate ~120 lines ✓ |
| **80% Test Coverage** | ≥ 80% coverage | Target 85% (35+ tests) ✓ |
| **No Silent Failures** | All errors logged | Validate audio_reactor methods ✓ |
| **Resource Leak Prevention** | GL resources cleaned | No extra resources allocated ✓ |
| **Backward Compatibility** | No breaking changes | New plugin ✓ |
| **Security** | No exec/eval | No dynamic code ✓ |

**Special Considerations:**
- **Strobe Risk:** None (no flashing)
- **Texture Units:** Uses only 1 texture unit (very low impact)
- **Performance:** This is one of the lightest effects; suitable for low-end hardware

---

## 🔗 Dependencies

```python
from core.effects.shader_base import Effect
from core.audio_reactor import AudioReactor
import logging
```

**External:** None beyond VJLive3 core

---

## 📊 Success Metrics

- ✅ Shader compiles without errors on all target GPUs
- ✅ 35/35 unit tests pass, ≥85% coverage
- ✅ ≤ 1ms/frame average (should be ~0.3ms)
- ✅ Audio reactivity: adrenaline uniform updates at 60 FPS
- ✅ 5 presets load and demonstrate distinct characters
- ✅ All 10 Safety Rails satisfied

---

## 📝 Notes for Implementation Engineer

### Implementation Notes

1. **Shader Simplicity:** This is a very simple effect. The entire shader is ~42 lines. No complex math, no loops, no feedback. It should compile instantly and run at extremely high FPS.

2. **Color Palette:** The legacy code loads colors from a JSON preset file. For simplicity, we'll hardcode the default Pop Art colors directly in `__init__`. If you want preset loading, implement `load_palette_from_preset()` but it's not required.

3. **Audio Reactivity:** The `adrenaline` uniform is computed each frame. The legacy code tries multiple methods to get adrenaline:
   - `get_adrenaline_level()` (preferred)
   - `audio_energy` attribute
   - `get_feature_level(AudioFeature.BASS)` as fallback
   Implement this logic in `apply_uniforms()` to maintain compatibility.

4. **Parameter Ranges:**
   - `grid_density`: 10-200 is reasonable. The shader uses it directly; higher values mean more, smaller dots.
   - `dot_scale`: 0.1-5.0 is safe. The base radius is `0.5 * (1.0 - gray)`, so max base is 0.5. With `dot_scale=2.0`, max radius = 1.0 (covers entire cell).
   - `mix`: 0.0-1.0, maps directly to shader.

5. **Halftone Math:**
   ```glsl
   vec2 grid = fract(v_texcoord * u_grid_density);  // Cell-relative UV (0-1)
   float dist = distance(grid, vec2(0.5));          // Distance from cell center
   float base_radius = 0.5 * (1.0 - gray);         // Darker → larger radius
   float radius = base_radius * u_dot_scale + u_adrenaline * 0.2;
   float mask = step(radius, dist);                // 1 outside dot, 0 inside
   ```
   The `step(radius, dist)` returns 1.0 if `dist >= radius`, creating a circular hole where the dot color shows through.

6. **Color Mixing:**
   ```glsl
   vec3 color = mix(u_primary_color, u_secondary_color, gray);
   vec3 final_color = color * mask;
   final_color = mix(tex.rgb, final_color, u_mix);
   ```
   The dot color is interpolated between primary and secondary based on original brightness. Then the dot pattern is multiplied by that color (mask creates holes). Finally, blend with original based on `u_mix`.

7. **Testing Strategy:** This effect is mathematically pure. Test the halftone logic thoroughly:
   - For a given `gray` value, compute expected `base_radius`
   - For a given `dist` (distance from center), assert `mask` is 0 if `dist < radius`, 1 if `dist > radius`
   - Test edge case: `gray=0` → `base_radius=0.5`; `gray=1` → `base_radius=0`
   - Test that `u_mix=0` returns original color unchanged

8. **Performance:** The shader does:
   - 1 texture fetch
   - 3 multiplications for luminance
   - 1 `fract`, 1 `distance` (sqrt), 1 `step`
   - 1 `mix` for color, 1 `mix` for final blend
   This is negligible. Should run at 1000+ FPS on modern GPUs.

9. **No Depth:** This effect does not use depth. No depth texture needed.

10. **No Feedback:** This effect is feedforward only. No previous frame needed.

### Porting Checklist

- [ ] Copy GLSL shader exactly (42 lines)
- [ ] Set default parameters: `dot_scale=1.0`, `grid_density=80.0`, `mix=1.0`
- [ ] Set default colors: primary=[0.996, 0.0, 0.0], secondary=[0.996, 0.839, 0.082]
- [ ] Implement `apply_uniforms()` with audio adrenaline fallback chain
- [ ] Add `METADATA` constant
- [ ] Write 35+ unit tests
- [ ] Create 5 presets (3 legacy + 2 new)
- [ ] Performance test (should be very fast)
- [ ] Safety Rails compliance review

### Known Legacy Issues

None apparent. The effect is simple and well-designed.

### Debugging

Visualize the grid and radius:
```glsl
// Debug: color cells by distance
float cell_id = floor(v_texcoord * u_grid_density).x + floor(v_texcoord * u_grid_density).y * u_grid_density;
vec3 debug = vec3(fract(cell_id * 0.1), dist, radius);
fragColor = vec4(debug, 1.0);
```

Or visualize the mask:
```glsl
fragColor = vec4(vec3(mask), 1.0);  // White dots on black
```

---

**Specification Version:** 1.0  
**Last Updated:** 2025-02-23  
**Approved By:** [Awaiting Approval]
