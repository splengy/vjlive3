# P3-EXT001: ASCIIEffect — Specification

## What This Module Does

Transform video into living typography. The screen becomes a terminal from an alternate dimension where every pixel cluster maps to a character whose shape echoes the luminance and structure beneath. Multiple character sets (classic ASCII, blocks, braille, matrix katakana, binary), color modes (green terminal, amber, original, hue-shift, rainbow, thermal), and CRT phosphor simulation turn modern video into the visual language of machines.

**Core Innovation:** Procedural character rendering using pure math — no texture atlas required. Characters are generated algorithmically based on luminance thresholds, creating a unique aesthetic that feels both retro and alive.

## Public Interface

```python
class ASCIIEffect(Effect):
    """ASCII art — character-mapped video with CRT simulation."""

    METADATA = {
        "name": "ASCII Effect",
        "description": "Transform video into living typography with CRT simulation",
        "version": "1.0.0",
        "api_version": "2.0",
        "author": "VJLive Team",
        "category": "stylize",
        "tags": ["ascii", "text", "matrix", "retro", "code", "glitch"],
        "complexity": "high",
        "performance_impact": "medium"
    }

    def __init__(self) -> None:
        """Initialize effect with default parameters."""
        super().__init__("ascii_effect", ASCII_EFFECT_FRAGMENT)
        self.parameters: dict[str, float] = { ... }  # See Parameters section

    PRESETS: dict[str, dict[str, float]] = {
        "matrix_rain": {...},
        "classic_terminal": {...},
        "color_ascii": {...},
        "blocky_pixels": {...},
        "glitch_text": {...},
    }
```

## Inputs and Outputs

**Inputs:**
- `tex0` (sampler2D): Source video frame (RGBA, normalized 0-1)
- `time` (float): Elapsed time in seconds (for animation)
- `resolution` (vec2): Viewport resolution in pixels
- `u_mix` (float): Blend factor 0-1 (0 = original, 1 = full effect)

**Outputs:**
- `fragColor` (vec4): Processed RGBA color (premultiplied alpha)

**Parameters (all float 0.0-10.0 range):**

### Grid Controls
- `cell_size` (4.0): Character pixel size, maps to 4-32px
- `aspect_correct` (6.0): Character aspect ratio, maps to 0.4-1.0

### Character Mapping
- `charset` (0.0): Font set selector (0=classic, 2=blocks, 4=braille, 6=matrix, 8=binary)
- `threshold_curve` (5.0): Luminance gamma, maps to 0.3-3.0
- `edge_detect` (0.0): Edge detection mix, 0-1
- `detail_boost` (3.0): Local contrast enhancement, 0-3

### Color
- `color_mode` (0.0): Palette (0=green, 1=amber, 2=original, 3=hue_shift, 4=rainbow, 5=thermal)
- `fg_brightness` (6.0): Foreground intensity, 0.3-3.0
- `bg_brightness` (1.0): Background intensity, 0-0.5
- `saturation` (5.0): Color saturation, 0-2.0
- `hue_offset` (0.0): Hue rotation, 0-1

### CRT Simulation
- `scanlines` (3.0): Scanline intensity, 0-1
- `phosphor_glow` (2.0): Character glow radius, 0-2
- `flicker` (1.0): Brightness flicker amplitude, 0-0.1
- `curvature` (2.0): Barrel distortion strength, 0-0.3
- `noise_amount` (1.0): Static noise level, 0-0.15

### Animation
- `scroll_speed` (5.0): Matrix rain scroll, -5 to 5 (5=stopped)
- `rain_density` (0.0): Falling character density, 0-1
- `char_jitter` (0.0): Random character changes, 0-1
- `wave_amount` (0.0): Wave distortion amplitude, 0-0.5
- `wave_freq` (3.0): Wave frequency, 1-20

## What It Does NOT Do

- **NO texture atlas usage:** Characters are procedurally generated via math functions, not bitmap fonts.
- **NO external dependencies:** All color space conversions (RGB↔HSV) and noise functions are inline.
- **NO audio reactivity:** This is a pure visual effect; audio input is ignored.
- **NO multi-pass rendering:** Single fragment shader only.
- **NO depth buffer usage:** 2D effect only, no 3D geometry.
- **NO network or file I/O:** Completely self-contained.

## Test Plan

### Unit Tests (pytest)

1. **`test_ascii_effect.py`** - Effect class validation
   - Effect registers correctly with plugin system
   - METADATA constant present and valid
   - All 21 parameters exist with correct default values
   - Parameter ranges set correctly (0-10)
   - PRESETS dictionary contains 5 presets with valid parameters
   - Effect tags include required categories

2. **`test_ascii_shader_compilation.py`** - GLSL validation
   - Shader fragment compiles without errors
   - All uniform locations resolve correctly
   - No undefined variables or type mismatches

3. **`test_ascii_rendering.py`** - Visual correctness
   - Character grid aligns with cell_size parameter
   - Color modes produce expected palettes (green, amber, thermal, etc.)
   - Matrix rain animation moves downward when scroll_speed < 5
   - Rain density controls number of active columns
   - CRT curvature produces barrel distortion
   - Scanlines modulate brightness sinusoidally
   - Phosphor glow samples adjacent cells correctly

4. **`test_ascii_performance.py`** - FPS impact
   - Effect maintains ≥58 FPS at 1920x1080 on reference hardware
   - Memory usage stable over 60-second run (no leaks)
   - Parameter changes do not cause frame drops

5. **`test_ascii_edge_cases.py`** - Robustness
   - Handles resolution changes gracefully
   - Zero cell_size (edge case) does not crash
   - Extreme curvature values clamp correctly
   - Time wrap-around (large time values) stable

### Integration Tests

- Load via plugin registry: `registry.load_plugin("ascii_effect")`
- Apply to node graph and verify parameter updates
- Hot-reload: modify shader code, trigger reload, verify new shader compiles
- Serialization: save/load effect state with all parameters

### Performance Benchmarks

Target: **60 FPS stable** at 1920x1080 on mid-range GPU (GTX 1060 / RX 580 equivalent).

Expected overhead: ~2-3ms per frame (medium impact per SAFETY_RAILS.md).

## Implementation Notes

### File Structure

```
src/vjlive3/plugins/ascii_effect.py  # Main plugin (single file, <300 lines)
tests/plugins/test_ascii_effect.py    # Comprehensive test suite
```

### Code Style

- Follow existing plugin patterns (see `depth_aware_compression.py` for reference)
- Use `Effect` base class from `src/vjlive3/plugins/plugin_runtime.py`
- Include `METADATA` constant at module level
- Preserve the GLSL fragment as a raw string constant
- Keep all helper functions (hash, rgb2hsv, render_char) inside the fragment

### Bespoke Treatment

This plugin is **unique** — do NOT batch-process. The GLSL shader contains artistic mathematical patterns (procedural character generation) that must be preserved exactly. The `render_char` function is the soul of this effect; any deviation will break the aesthetic.

### Safety Rails Compliance

- **Rail 1 (60 FPS):** Profile with `profile_engine.py`; optimize if >3ms overhead
- **Rail 3 (Plugin Integrity):** METADATA must match this spec exactly
- **Rail 4 (750 lines):** Current implementation ~320 lines total (shader + Python) — well under limit
- **Rail 5 (Test Coverage):** Target ≥80% on this module

## References

**Legacy Sources:**
- VJLive-2: `/home/happy/Desktop/claude projects/VJlive-2/plugins/core/ascii_effect/__init__.py` (canonical)
- VJLive-2: `/home/happy/Desktop/claude projects/VJlive-2/core/effects/ascii.py` (simpler variant)
- vjlive: `/home/happy/Desktop/claude projects/vjlive/plugins/vcore/ascii_effect.py` (identical to VJLive-2 plugin)

**Knowledge Base Concepts:**
- `vjlive-v2---home-happy-Desktop-claude-projects-VJlive-2-plugins-core-ascii-effect---init--`
- `vjlive-v1---home-happy-Desktop-claude-projects-vjlive-plugins-vcore-ascii-effect`

**Related:** BackgroundSubtractionEffect (P3-EXT011) — also text-mode effect, but different approach.

---

**Specification approved by:** Manager-Gemini-3.1
**Date:** 2026-02-23
**Priority:** P0 (Critical — Phase 3 EXT collection)
**Source:** vjlive (legacy) + VJLive-2 (clean architecture)
