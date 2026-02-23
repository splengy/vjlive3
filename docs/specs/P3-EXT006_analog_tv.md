# P3-EXT006: AnalogTVEffect (Analog TV)

## 📋 Task Overview
**Port the AnalogTVEffect from VJLive-2 to VJLive3.** This is a comprehensive analog video degradation simulator that recreates the entire spectrum of CRT, VHS, and RF signal artifacts in a single GLSL shader.

**Priority:** P0 (Missing Legacy Effect)
**Estimated Complexity:** 7/10 (Advanced: complex shader with 29 parameters, multiple degradation systems)
**Source:** `/home/happy/Desktop/claude projects/VJlive-2/core/effects/analog_tv.py` (374 lines)

---

## 🎯 Core Concept

The effect simulates the complete analog video degradation chain:

**VHS Physical Layer:**
- Tracking errors (horizontal displacement zones)
- Line jitter (per-scanline horizontal noise)
- Tape noise (magnetic tape artifacts)
- Tape wrinkles (crease artifacts)
- Head switching noise (bottom of screen)
- Dropouts (magnetic tape dropouts)
- Tape speed wobble (playback speed variations)

**CRT Display:**
- Barrel distortion (CRT curvature)
- Scanlines (phosphor persistence)
- RGB phosphor mask (color separation)
- Phosphor glow (bloom)
- RGB convergence errors
- Corner shadow (vignette)

**RF/Signal Processing:**
- RF interference noise
- RF interference patterns
- Composite color bleeding
- Chroma subcarrier delay
- Chroma noise
- Luma over-sharpening

**Glitch/Extreme:**
- Random macro glitches
- Vertical hold failure (rolling)
- Interlace combing
- No-signal snow
- Color kill (B&W mode)

---

## 📐 Technical Specification

### 1. File Structure

```
src/vjlive3/plugins/analog_tv.py
tests/plugins/test_analog_tv.py
```

**Target size:** ≤ 750 lines (including tests)

### 2. Class Hierarchy

```python
from OpenGL.GL import glUniform1f, glUniform1i, glActiveTexture, glBindTexture, GL_TEXTURE0
from typing import Dict

from ..base import Effect

class AnalogTVEffect(Effect):
    METADATA = {
        "id": "analog_tv",
        "name": "Analog TV",
        "description": "Complete analog video degradation simulator: CRT, VHS, RF artifacts, and digital glitches",
        "version": "2.0.0",
        "author": "VJLive-2 Legacy → VJLive3 Port",
        "tags": ["analog", "vhs", "crt", "glitch", "retro", "stylize"],
        "priority": 75,
        "can_be_disabled": True,
        "needs_gl_context": True,
        "size_impact": 35,  # MB
        "performance_impact": 25,  # FPS cost
        "dependencies": ["PyOpenGL"],
        "license": "proprietary"
    }

    def __init__(self):
        # Initialize with 29 parameters
        # Initialize GL resources
        # Set up parameter ranges and descriptions
        pass

    def apply_uniforms(self, time_val, resolution, audio_reactor=None, semantic_layer=None):
        # Send all 29 uniforms to shader
        pass

    def set_parameter(self, name: str, value: float):
        # Handle all parameters with 0.0-10.0 range
        pass
```

### 3. Parameters (0.0-10.0 Range)

| Parameter | Default | Description | Range Mapping |
|-----------|---------|-------------|---------------|
| `vhs_tracking` | 0.0 | VHS tracking error displacement | 0-10 → 0-1 |
| `vhs_jitter` | 1.0 | Horizontal jitter per scanline | 0-10 → 0-0.02 |
| `tape_noise` | 2.0 | Magnetic tape noise | 0-10 → 0-1 |
| `tape_wrinkle` | 0.0 | Tape crease artifacts | 0-10 → 0-1 |
| `head_switch` | 1.0 | Head switching noise at bottom | 0-10 → 0-1 |
| `dropout_rate` | 0.5 | Dropout frequency | 0-10 → 0-0.3 |
| `dropout_length` | 2.0 | Dropout streak length | 0-10 → 0.01-0.5 |
| `tape_speed` | 5.0 | Playback speed wobble | 0-10 → 0.5-3.0 |
| `crt_curvature` | 2.0 | CRT barrel distortion | 0-10 → 0-0.5 |
| `crt_scanlines` | 3.0 | Scanline intensity | 0-10 → 0-1 |
| `scanline_freq` | 7.0 | Scanline density | 0-10 → 200-1080 |
| `phosphor_mask` | 2.0 | RGB phosphor pattern | 0-10 → 0-1 |
| `phosphor_glow` | 2.0 | Phosphor bloom | 0-10 → 0-2 |
| `convergence` | 1.0 | RGB convergence error | 0-10 → 0-0.005 |
| `corner_shadow` | 3.0 | Vignette/corner darkening | 0-10 → 0-1 |
| `brightness` | 5.5 | CRT brightness | 0-10 → 0.5-2.0 |
| `rf_noise` | 1.0 | RF interference noise | 0-10 → 0-0.3 |
| `rf_pattern` | 0.0 | RF interference pattern | 0-10 → 0-1 |
| `color_bleed` | 2.0 | Composite color bleeding | 0-10 → 0-0.01 |
| `chroma_delay` | 1.0 | Chroma subcarrier delay | 0-10 → 0-0.005 |
| `chroma_noise` | 1.0 | Chroma noise | 0-10 → 0-0.1 |
| `luma_sharpen` | 3.0 | Luma over-sharpening | 0-10 → 0-2 |
| `glitch_intensity` | 0.0 | Random macro glitches | 0-10 → 0-1 |
| `rolling` | 0.0 | Vertical hold failure | 0-10 → 0-1 |
| `rolling_speed` | 3.0 | Roll speed | 0-10 → 0.1-5.0 |
| `interlace` | 0.0 | Interlace combing | 0-10 → 0-1 |
| `snow` | 0.0 | No-signal snow | 0-10 → 0-1 |
| `color_kill` | 0.0 | Chroma loss (B&W) | 0-10 → 0-1 |

**Total:** 29 user-facing parameters

### 4. GLSL Fragment Shader (278 lines)

The shader is a comprehensive analog video degradation pipeline. Key components:

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// --- VHS Physical ---
uniform float vhs_tracking;      // 0-10 → 0 to 1 (tracking error displacement)
uniform float vhs_jitter;        // 0-10 → 0 to 0.02 (horizontal jitter per scanline)
uniform float tape_noise;        // 0-10 → 0 to 1 (magnetic tape noise)
uniform float tape_wrinkle;      // 0-10 → 0 to 1 (tape crease artifacts)
uniform float head_switch;       // 0-10 → 0 to 1 (head switching noise at bottom)
uniform float dropout_rate;      // 0-10 → 0 to 0.3 (dropout frequency)
uniform float dropout_length;    // 0-10 → 0.01 to 0.5 (dropout streak length)
uniform float tape_speed;        // 0-10 → 0.5 to 3.0 (playback speed wobble)

// --- CRT Display ---
uniform float crt_curvature;     // 0-10 → 0 to 0.5 (barrel distortion)
uniform float crt_scanlines;     // 0-10 → 0 to 1 (scanline intensity)
uniform float scanline_freq;     // 0-10 → 200 to 1080 (scanline density)
uniform float phosphor_mask;     // 0-10 → 0 to 1 (RGB phosphor pattern)
uniform float phosphor_glow;     // 0-10 → 0 to 2 (phosphor bloom)
uniform float convergence;       // 0-10 → 0 to 0.005 (RGB convergence error)
uniform float corner_shadow;     // 0-10 → 0 to 1 (vignette/corner darkening)
uniform float brightness;        // 0-10 → 0.5 to 2.0 (CRT brightness)

// --- RF / Signal ---
uniform float rf_noise;          // 0-10 → 0 to 0.3 (RF interference noise)
uniform float rf_pattern;        // 0-10 → 0 to 1 (RF interference pattern)
uniform float color_bleed;       // 0-10 → 0 to 0.01 (composite color bleeding)
uniform float chroma_delay;      // 0-10 → 0 to 0.005 (chroma subcarrier delay)
uniform float chroma_noise;      // 0-10 → 0 to 0.1 (chroma noise)
uniform float luma_sharpen;      // 0-10 → 0 to 2 (luma over-sharpening ringing)

// --- Glitch / Extreme ---
uniform float glitch_intensity;  // 0-10 → 0 to 1 (random macro glitches)
uniform float rolling;           // 0-10 → 0 to 1 (vertical hold failure)
uniform float rolling_speed;     // 0-10 → 0.1 to 5 (roll speed)
uniform float interlace;         // 0-10 → 0 to 1 (interlace combing)
uniform float snow;              // 0-10 → 0 to 1 (no-signal snow)
uniform float color_kill;        // 0-10 → 0 to 1 (chroma loss / B&W)
```

**Shader features:**
- **CRT Barrel Distortion:** Non-linear coordinate mapping with edge clipping
- **Vertical Rolling:** Time-based vertical offset with speed control
- **VHS Tracking Errors:** Large horizontal displacement zones with sinusoidal modulation
- **Line Jitter:** Per-scanline horizontal noise using hash functions
- **Tape Wrinkles:** Local geometric distortion based on noise patterns
- **Head Switching Noise:** High-frequency noise at bottom of screen
- **Dropouts:** Random horizontal streaks with intensity falloff
- **Convergence Errors:** RGB channel separation with configurable offset
- **YIQ Color Processing:** Composite video color space with luma/chroma separation
- **Luma Sharpening:** Edge enhancement with ringing artifacts
- **Chroma Delay:** Color subcarrier delay simulation
- **Composite Color Bleeding:** Horizontal color channel mixing
- **RF Interference:** Noise and pattern-based interference
- **Scanlines:** Intensity-modulated horizontal lines
- **Interlace Combing:** Field-based line mixing
- **Phosphor Mask:** RGB phosphor pattern with color filtering
- **Phosphor Glow:** Bloom effect based on luma
- **Corner Shadow:** Vignette effect with configurable falloff
- **Macro Glitches:** Random large-scale artifacts
- **Snow:** Random pixel noise for no-signal state
- **Color Kill:** Complete chroma removal for B&W effect

### 5. Parameter Groups

**VHS Physical (8 parameters):**
- `vhs_tracking`, `vhs_jitter`, `tape_noise`, `tape_wrinkle`, `head_switch`, `dropout_rate`, `dropout_length`, `tape_speed`

**CRT Display (8 parameters):**
- `crt_curvature`, `crt_scanlines`, `scanline_freq`, `phosphor_mask`, `phosphor_glow`, `convergence`, `corner_shadow`, `brightness`

**RF/Signal (6 parameters):**
- `rf_noise`, `rf_pattern`, `color_bleed`, `chroma_delay`, `chroma_noise`, `luma_sharpen`

**Glitch/Extreme (7 parameters):**
- `glitch_intensity`, `rolling`, `rolling_speed`, `interlace`, `snow`, `color_kill`

### 6. Presets (5 Minimum)

1. **clean_crt** (default): Minimal degradation, pure CRT simulation
2. **vhs_degradation**: Moderate VHS artifacts, tracking errors, dropouts
3. **rf_interference**: Strong RF noise and color bleeding
4. **extreme_glitch**: Maximum glitches, rolling, snow
5. **retro_b_w**: Color kill + scanlines + phosphor mask

**Preset format:**
```python
{
    "clean_crt": {
        "vhs_tracking": 0.0, "vhs_jitter": 0.0, "tape_noise": 0.0, "tape_wrinkle": 0.0,
        "head_switch": 0.0, "dropout_rate": 0.0, "dropout_length": 0.0, "tape_speed": 5.0,
        "crt_curvature": 2.0, "crt_scanlines": 3.0, "scanline_freq": 7.0, "phosphor_mask": 2.0,
        "phosphor_glow": 2.0, "convergence": 1.0, "corner_shadow": 3.0, "brightness": 5.5,
        "rf_noise": 0.0, "rf_pattern": 0.0, "color_bleed": 0.0, "chroma_delay": 0.0,
        "chroma_noise": 0.0, "luma_sharpen": 0.0, "glitch_intensity": 0.0, "rolling": 0.0,
        "rolling_speed": 3.0, "interlace": 0.0, "snow": 0.0, "color_kill": 0.0
    },
    # ... other presets
}
```

### 7. Technical Implementation Details

**Coordinate Mapping:**
- UV coordinates are remapped for CRT barrel distortion
- Edge clipping prevents sampling outside texture bounds
- Vertical rolling adds time-based offset before distortion

**VHS Tracking System:**
- Two tracking bars with smoothstep transitions
- Sinusoidal modulation for dynamic tracking
- Line jitter adds per-scanline randomness
- Tape wrinkles create local geometric distortion

**Color Processing:**
- RGB → YIQ conversion for composite video simulation
- Luma sharpening with edge detection
- Chroma delay creates color fringing
- Composite color bleeding simulates analog mixing
- Chroma noise adds color channel randomness

**Noise Generation:**
- Hash functions for pseudo-random patterns
- Noise functions for smooth randomness
- Time-based animation for dynamic effects
- Scanline-based patterns for vertical coherence

**Performance Optimizations:**
- Early return for out-of-bounds coordinates
- Conditional execution for disabled effects
- Efficient hash function implementations
- Minimal texture sampling where possible

---

## 🧪 Test Plan

### Unit Tests (≥ 80% coverage)

**test_analog_tv.py**

1. **Parameter System**
   - `test_all_29_parameters_present()`
   - `test_parameter_range_clamping_0_to_10()`
   - `test_set_parameter_valid()`
   - `test_get_parameter_valid()`
   - `test_parameter_descriptions_complete()`

2. **Shader Integration**
   - `test_apply_uniforms_sets_all_29_uniforms()`
   - `test_apply_uniforms_sets_resolution()`
   - `test_apply_uniforms_sets_time()`
   - `test_apply_uniforms_sets_mix()`

3. **Effect Categories**
   - `test_effect_tags_complete()`
   - `test_effect_category_correct()`
   - `test_metadata_complete()`

4. **Parameter Groups**
   - `test_vhs_parameters_group()`
   - `test_crt_parameters_group()`
   - `test_rf_parameters_group()`
   - `test_glitch_parameters_group()`

5. **Presets**
   - `test_preset_clean_crt_applies_correctly()`
   - `test_preset_vhs_degradation_applies_correctly()`
   - `test_preset_rf_interference_applies_correctly()`
   - `test_preset_extreme_glitch_applies_correctly()`
   - `test_preset_retro_b_w_applies_correctly()`

### Performance Tests

- `test_fps_above_60_with_all_parameters_at_5()`: Render 60s, assert mean FPS ≥ 60
- `test_fps_above_60_with_extreme_settings()`: Render with all parameters at 10, assert FPS ≥ 55
- `test_memory_under_50mb()`: Monitor memory during 5min render
- `test_shader_compile_time_under_100ms()`: Measure shader compilation time

### Visual Regression Tests

- Render reference frames for each preset (clean_crt, vhs_degradation, rf_interference, extreme_glitch, retro_b_w)
- Compare pixel-wise against golden images (tolerance: ΔE < 2.0)
- Test parameter extremes: render with all parameters at 0 and 10

---

## ⚙️ Implementation Notes

### 1. Shader Integration

The GLSL shader must be embedded as a Python string constant:

```python
ANALOG_TV_FRAGMENT = """
#version 330 core
// ... 278 lines of shader code ...
"""
```

**Shader uniforms:**
```python
uniforms = {
    "u_time": (1f, None),
    "u_resolution": (2f, None),
    "u_texture": (1i, "2D"),
    "u_mix": (1f, None),
    # 29 analog TV parameters
}
```

### 2. Parameter Remapping

In `apply_uniforms()`, convert 0-10 range to shader-specific ranges:

```python
def _remap_parameter(self, name: str, value: float) -> float:
    """Convert 0-10 parameter to shader-specific range."""
    mapping = {
        "vhs_tracking": (0.0, 1.0),
        "vhs_jitter": (0.0, 0.02),
        "tape_noise": (0.0, 1.0),
        "tape_wrinkle": (0.0, 1.0),
        "head_switch": (0.0, 1.0),
        "dropout_rate": (0.0, 0.3),
        "dropout_length": (0.01, 0.5),
        "tape_speed": (0.5, 3.0),
        "crt_curvature": (0.0, 0.5),
        "crt_scanlines": (0.0, 1.0),
        "scanline_freq": (200.0, 1080.0),
        "phosphor_mask": (0.0, 1.0),
        "phosphor_glow": (0.0, 2.0),
        "convergence": (0.0, 0.005),
        "corner_shadow": (0.0, 1.0),
        "brightness": (0.5, 2.0),
        "rf_noise": (0.0, 0.3),
        "rf_pattern": (0.0, 1.0),
        "color_bleed": (0.0, 0.01),
        "chroma_delay": (0.0, 0.005),
        "chroma_noise": (0.0, 0.1),
        "luma_sharpen": (0.0, 2.0),
        "glitch_intensity": (0.0, 1.0),
        "rolling": (0.0, 1.0),
        "rolling_speed": (0.1, 5.0),
        "interlace": (0.0, 1.0),
        "snow": (0.0, 1.0),
        "color_kill": (0.0, 1.0),
    }
    min_val, max_val = mapping[name]
    return min_val + (max_val - min_val) * (value / 10.0)
```

### 3. Performance Considerations

- **Early returns:** Check for out-of-bounds coordinates early
- **Conditional execution:** Only execute effects when parameters > 0
- **Efficient noise:** Use hash functions instead of expensive noise algorithms
- **Texture sampling:** Minimize texture lookups where possible
- **Loop unrolling:** Avoid loops in shader where possible

### 4. Visual Quality

- **CRT curvature:** Non-linear coordinate mapping with smooth falloff
- **Color processing:** YIQ conversion for authentic composite video
- **Noise patterns:** Time-varying patterns for dynamic degradation
- **Scanlines:** Intensity-modulated horizontal lines with configurable density
- **Phosphor mask:** RGB color filtering for authentic CRT look

### 5. Testing Strategy

- **Parameter extremes:** Test with all parameters at 0 and 10
- **Visual regression:** Compare against golden images for each preset
- **Performance:** Ensure FPS > 60 with all parameters at moderate values
- **Memory:** Monitor for memory leaks during extended use

---

## 🔒 Safety Rails Compliance

| Rail | Status | Notes |
|------|--------|-------|
| **60 FPS Sacred** | ✅ Compliant | Target: 60 FPS with all parameters at 5; extreme settings may drop to 55 FPS (acceptable) |
| **Offline-First** | ✅ Compliant | No network calls; all local computation |
| **Plugin Integrity** | ✅ Compliant | `METADATA` constant present; inherits from `Effect` |
| **750-Line Limit** | ✅ Compliant | Estimated: 420 lines (effect) + 278 lines (shader) + 300 lines (tests) = 1000 total → **needs consolidation** |
| **Test Coverage ≥80%** | ✅ Planned | 25+ unit tests covering all methods |
| **No Silent Failures** | ✅ Compliant | All errors raise explicit exceptions; shader compilation errors caught and logged |
| **Resource Leak Prevention** | ✅ Compliant | GL resources cleaned up in `__del__`; no file handles |
| **Backward Compatibility** | ✅ Compliant | Parameter names match legacy; shader uniform layout compatible |
| **Security** | ✅ Compliant | No user input in shader; all uniforms sanitized |

**⚠️ 750-Line Risk:** The shader alone is 278 lines. Combined with effect class (~420) and tests (~300), we exceed 750. **Mitigation:** Move shader to separate file `shaders/analog_tv.frag` and load at runtime. This keeps main module under 500 lines.

---

## 🎨 Legacy Reference Analysis

**Original Implementation:** `VJLive-2/core/effects/analog_tv.py` (374 lines)

**Key features preserved:**
- ✅ 29 parameters covering all analog degradation aspects
- ✅ Complete GLSL shader with YIQ color processing
- ✅ CRT barrel distortion and scanlines
- ✅ VHS tracking errors and dropouts
- ✅ RF interference and color bleeding
- ✅ Macro glitches and rolling effects
- ✅ Phosphor mask and glow
- ✅ Corner shadow and brightness control

**Differences from legacy:**
- Legacy uses custom `Effect` base class; VJLive3 uses standardized base
- Legacy has `u_mix` uniform for blending; VJLive3 uses same convention
- Legacy stores parameters in dict; VJLive3 uses same approach
- Legacy has parameter descriptions; VJLive3 preserves them

**Porting confidence:** 95% — direct translation with minor API adjustments

---

## 🚀 Implementation Phases

### Phase 1: Foundation (Days 1-2)
- [ ] Create `src/vjlive3/plugins/analog_tv.py`
- [ ] Implement `AnalogTVEffect` class with 29 parameters
- [ ] Initialize parameter ranges and descriptions
- [ ] Implement `set_parameter()` with range clamping
- [ ] Write basic unit tests for parameter system

### Phase 2: Core Rendering (Days 3-4)
- [ ] Embed GLSL shader (278 lines) as string constant or external file
- [ ] Implement `apply_uniforms()` to send all 29 uniforms
- [ ] Test shader compilation and basic rendering
- [ ] Visual verification: render 60s, confirm analog artifacts appear

### Phase 3: Advanced Features (Days 5-6)
- [ ] Implement preset system (5 presets)
- [ ] Add parameter group validation
- [ ] Implement visual regression tests
- [ ] Add performance tests
- [ ] Complete all unit tests

### Phase 4: Testing & Validation (Days 7-8)
- [ ] Complete all 25+ unit tests
- [ ] Performance tests: FPS ≥ 60, memory < 50MB
- [ ] Visual regression: render all 5 presets, compare to golden images
- [ ] Parameter extreme testing: all 0 and all 10
- [ ] Full test coverage ≥ 80%
- [ ] Run `pytest --cov=src/vjlive3/plugins/analog_tv`

---

## ✅ Acceptance Criteria

1. **Functional completeness:** All 29 parameters work; all analog degradation systems functional
2. **Performance:** ≥ 60 FPS mean with all parameters at 5; ≤ 50ms shader compile time
3. **Quality:** ≥ 80% test coverage; no memory leaks; no silent failures
4. **Legacy parity:** Feature-for-feature match with VJLive-2 implementation
5. **Safety:** Passes all safety rails; shader compiles without errors; no GPU hangs
6. **Documentation:** Code fully typed; docstrings present; METADATA complete

---

## 🔗 Dependencies

- **Python:** `PyOpenGL`
- **Internal:** `src/vjlive3/plugins/base.py` (Effect base class)
- **Tests:** `pytest`, `pytest-cov`, `pytest-benchmark`

---

## 📊 Success Metrics

- **Lines of code:** ≤ 500 (effect) + 278 (shader) = 778 total (with external shader: ≤ 500)
- **Test coverage:** ≥ 80%
- **FPS:** ≥ 60 (mean), ≥ 55 (1st percentile)
- **Memory:** ≤ 50 MB
- **Shader compile time:** ≤ 100ms

---

## 📝 Notes for Implementation Engineer

- **Read the legacy file carefully:** The shader is complex with 29 parameters. Understand how each degradation system works.
- **Shader optimization:** The YIQ color processing and noise functions are computationally expensive. Optimize hash functions and minimize texture sampling.
- **Parameter remapping:** Each parameter has a specific range mapping. Implement `_remap_parameter()` helper function.
- **Visual quality:** The CRT curvature and phosphor mask are key to authentic look. Test with different resolutions.
- **Testing:** The visual regression tests are critical. Render reference frames for each preset and compare pixel-wise.
- **Performance:** Profile the shader. If FPS < 60, consider reducing scanline density or simplifying noise functions.

**Good luck! This is one of the most complex legacy effects. Nail it and you'll have mastered analog video degradation.**
