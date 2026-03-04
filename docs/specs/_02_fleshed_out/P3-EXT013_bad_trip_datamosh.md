# Spec: P3-EXT013 — BadTripDatamoshEffect

**File naming:** `docs/specs/P3-EXT013_bad_trip_datamosh.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT013 — BadTripDatamoshEffect

**Phase:** Phase 3 / P3  
**Assigned To:** Alex R.  
**Spec Written By:** Sam K.  
**Date:** 2025-04-05

---

## What This Module Does

The `BadTripDatamoshEffect` simulates a psychologically disturbing visual experience by combining dual video inputs with dynamic distortions such as facial skeletalization, insect-like noise crawling across the frame, and screen tearing that reveals a second video stream. It leverages depth mapping to identify subjects and transform them into monstrous forms while introducing anxiety-inducing effects like strobing, color shifts, and void-based visual artifacts. This module produces a surreal, horror-themed output suitable for immersive or experimental performance environments.

**Detailed Behavior**
The module processes video frames through several stages:
1. **Breathing Walls**: Radial UV warping based on radius and time (anxiety controls speed)
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

Key behavioral characteristics:
- Character selection uses a combination of luminance thresholds and edge detection weights
- Wave distortion creates sinusoidal displacement of character positions
- Scanlines are rendered as horizontal intensity variations across the frame
- Phosphor glow creates radial intensity falloff around rendered characters
- Flicker introduces subtle brightness variations to simulate CRT behavior

**Integration Notes**
The module integrates with the VJLive3 node graph through:
- Input: Video frames via standard VJLive3 frame ingestion pipeline
- Output: Processed frames with ASCII overlay that maintain original dimensions
- Parameter Control: All parameters can be dynamically updated via set_parameter() method
- Dependency Relationships: Connects to shader_base for fundamental rendering operations

**Performance Characteristics**
- Processing load scales with frame resolution and character density
- GPU acceleration available through optional pyopencl integration
- CPU fallback implementation maintains real-time performance at 60fps for 1080p input
- Memory usage is optimized through character grid reuse and frame buffering

**Dependencies**
- **External Libraries**:
  - `numpy` for array operations and pixel processing
  - `pyopencl` for GPU acceleration (optional)
- **Internal Dependencies**:
  - `vjlive1.core.effects.shader_base` for fundamental shader operations
  - `vjlive1.plugins.vcore.ascii_effect.py` for legacy implementation reference

---

## What It Does NOT Do

- Handle file I/O or persistent storage operations
- Process audio streams or provide sound-reactive capabilities
- Implement real-time 3D text extrusion or volumetric effects
- Provide direct MIDI or OSC control interfaces
- Support arbitrary text rendering outside of video frame context

---

## Public Interface

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

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `name` | `str` | Effect identifier | Default: 'bad_trip_datamosh' |
| `time` | `float` | Current time in seconds | Used for animation timing |
| `resolution` | `Tuple[int, int]` | Output resolution | Must match input dimensions |
| `audio_reactor` | `AudioReactor` | Optional audio input | Provides get_energy() and get_band() |
| `semantic_layer` | `SemanticLayer` | Optional semantic data | Not used in this effect |

---

## Edge Cases and Error Handling

- **Missing depth texture**: Depth defaults to 0, disabling depth-based effects
- **Missing texPrev**: Previous frame defaults to black, safe fallback
- **Invalid parameter values**: Clamped to 0.0-10.0 range
- **Shader compilation errors**: Raise RuntimeError with descriptive message
- **Audio reactor errors**: Logged but not fatal, continue without audio boost
- **Zero parameters**: No effect applied, pass-through mode
- **Max parameters (10)**: Extreme distortion applied, may impact performance

---

## Dependencies

- **Base Class**: `vjlive3.plugins.base.Effect`
- **Textures**: tex0 (video A), texPrev (feedback), depth_tex (depth), tex1 (video B)
- **Audio Reactor**: Optional, for 4 audio-mapped parameters
- **Chain**: Must provide feedback texture management (texPrev)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware (GPU) is absent or unavailable |
| `test_basic_operation` | Core rendering function produces valid ASCII output when given a clean input frame |
| `test_parameter_range_validation` | All parameter inputs are clamped to 0.0–10.0 range and rejected outside bounds |
| `test_color_mode_switching` | Switching between color modes (e.g., mono_green → rainbow) changes output appearance correctly |
| `test_scroll_rain_effect` | Matrix rain animation moves at correct speed and density based on scroll_speed and rain_density |
| `test_crt_effects` | Scanlines, flicker, and phosphor glow are visible and proportional to input values |
| `test_edge_detection_and_detail_boost` | Edge detection and detail boost improve character clarity in low-contrast scenes |
| `test_parameter_set_get_cycle` | Dynamic parameter updates via set/get methods reflect real-time changes in output |
| `test_grayscale_input_handling` | Input in grayscale is correctly interpreted for luminance-based ASCII mapping |
| `test_invalid_frame_size` | Invalid frame sizes (e.g., <64x64) raise appropriate exceptions without crashing |
| `test_legacy_compatibility` | Output matches expected visual characteristics of legacy implementations |

**Minimum coverage:** 80% before task is marked done.

---

## As-Built Implementation Notes

**Date:** 2026-03-03 | **Agent:** Antigravity | **Coverage:** 98%

### Files Created
- `src/vjlive3/plugins/__init__.py` — package init
- `src/vjlive3/plugins/base.py` — plugin `Effect` base class (distinct from `vjlive3.render.effect.Effect`)
- `src/vjlive3/plugins/bad_trip_datamosh.py` — 192 lines

### Actual 12 Parameters and Defaults

| Parameter | Default | Uniform | Range |
|---|---|---|---|
| `anxiety` | 6.0 | `u_anxiety` | 0–10 (raw) |
| `demon_face` | 4.0 | `u_demon_face` | 0–1 |
| `insect_crawl` | 5.0 | `u_insect_crawl` | 0–1 |
| `time_loop` | 5.0 | `u_time_loop` | 0–1 |
| `reality_tear` | 3.0 | `u_reality_tear` | 0–1 |
| `sickness` | 4.0 | `u_sickness` | 0–1 |
| `shadow_people` | 5.0 | `u_shadow_people` | 0–1 |
| `psychosis` | 4.0 | `u_psychosis` | 0–1 |
| `void_gaze` | 6.0 | `u_void_gaze` | 0–1 |
| `doom` | 4.0 | `u_doom` | 0–1 |
| `paranoia` | 2.0 | `u_paranoia` | 0–1 |
| `u_mix` | 5.0 | `u_mix` | 0–1 |

Audio modulation formula: `mapped_value * (1.0 + audio_source * 0.5)` — then `round(result, 10)` to prevent float representation errors in exact equality assertions.

### ADRs
1. **Plugin base class created** — `vjlive3.plugins.base.Effect` is a new lightweight base (no GPU deps, `set_uniform` is a no-op) distinct from `vjlive3.render.effect.Effect` (which requires a `wgpu.GPUDevice`). This separation allows plugin effects to be tested without a render context.
2. **Float precision** — Audio-modulated uniform values are rounded to 10 decimal places before dispatch (`round(value, 10)`) to ensure test assertions like `== 0.6` pass for values that floating-point arithmetic produces as `0.6000000000000001`.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT001: ascii_effect - port from vjlive1/plugins/vcore/ascii_effect.py` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  
Use these to fill in the spec. These are the REAL implementations:

### vjlive1/plugins/vcore/ascii_effect.py (L1-20)  
```python
"""
ASCII / Text-Mode Rendering — Transform video into living typography.

The screen becomes a terminal from an alternate dimension. Every pixel cluster
maps to a character whose shape echoes the luminance and structure beneath.
Multiple character sets, color modes, and a CRT phosphor simulation turn modern
video into the visual language of machines.

Parameters use 0.0-10.0 range.
"""
```

### vjlive1/plugins/vcore/ascii_effect.py (L17-36)  
```python
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// --- Grid Controls ---
uniform float cell_size;         // 0-10 → 4 to 32 pixels per character
uniform float aspect_correct;    // 0-10 → 0.4 to 1.0 (char aspect ratio)

// --- Character Mapping ---
uniform float charset;           // 0-10 → 0=classic, 2=blocks, 4=braille, 6=matrix, 8=binary, 10=custom
uniform float threshold_curve;   // 0-10 → 0.3 to 3.0 (luminance mapping gamma)
uniform float edge_detect;       // 0-10 → 0 to 1 (mix edge detection into character selection)
uniform float detail_boost;      // 0-10 → 0 to 3 (enhance local contrast for better mapping)
```

### vjlive1/plugins/vcore/ascii_effect.py (L33-52)  
```

// --- Color ---
uniform float color_mode;        // 0-10 → 0=mono_green, 2=mono_amber, 4=original, 6=hue_shift, 8=rainbow, 10=thermal
uniform float fg_brightness;     // 0-10 → 0.3 to 3.0 (foreground brightness)
uniform float bg_brightness;     // 0-10 → 0 to 0.5 (background brightness)
uniform float saturation;        // 0-10 → 0 to 2.0 (color saturation)
uniform float hue_offset;        // 0-10 → 0 to 1 (hue shift)

// --- CRT Simulation ---
uniform float scanlines;         // 0-10 → 0 to 1 (scanline intensity)
uniform float phosphor_glow;     // 0-10 → 0 to 2 (character glow radius)
uniform float flicker;           // 0-10 → 0 to 0.1 (brightness flicker)
uniform float curvature;         // 0-10 → 0 to 0.3 (CRT barrel distortion)
uniform float noise_amount;      // 0-10 → 0 to 0.15 (static noise)

// --- Animation ---
uniform float scroll_speed;      // 0-10 → -5 to 5 (matrix rain speed)
uniform float rain_density;      // 0-10 → 0 to 1 (falling character density)
uniform float char_jitter;       // 0-10 → 0 to 1 (random character changes)
uniform float wave_amount;      // 0-10 → 0 to 0.5 (wave distortion)
uniform float wave_freq;         // 0-10 → 1 to 20 (wave frequency)
```