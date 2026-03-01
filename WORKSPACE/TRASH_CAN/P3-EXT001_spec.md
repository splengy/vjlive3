# P3-EXT001: ASCII Effect (ASCIIEffect)

## Overview

The ASCII Effect transforms video frames into living typography by mapping pixel luminance and structural patterns to character glyphs, creating a terminal-like visual experience from an alternate dimension. This effect renders video as ASCII characters with full control over character sets, color modes, and CRT phosphor simulation. The implementation uses a purely procedural approach—no texture atlas required—rendering characters mathematically through GLSL shader code.

The effect operates on a 0.0-10.0 parameter range throughout, providing consistent control mapping across all effect parameters. The core algorithm divides the screen into a grid of cells, samples the source image luminance within each cell, selects an appropriate character based on that luminance, and renders the character shape procedurally. Additional layers include color mapping, CRT scanline simulation, phosphor glow, flicker effects, barrel distortion, and optional matrix-style rain animation with falling characters.

## Architecture

### Shader Structure

The ASCII effect is implemented entirely in GLSL fragment shader code. The shader follows this execution pipeline:

1. **Parameter Normalization**: All 0-10 input parameters are remapped to their operational ranges at the start of `main()`.
2. **Grid Computation**: The screen is divided into a grid where each cell corresponds to one ASCII character. Cell size is controlled by `cell_size` (4-32 pixels).
3. **Luminance Sampling**: For each grid cell, the source texture is sampled at multiple points to compute average luminance, optionally with edge detection mixed in.
4. **Character Selection**: The luminance value determines which character from the chosen charset to render. The `threshold_curve` parameter applies gamma correction to the luminance mapping.
5. **Character Rendering**: The selected character index is passed to `render_char()`, which procedurally draws the character shape using signed distance functions, step functions, and hash-based patterns specific to the chosen charset.
6. **Color Application**: The character's color is computed based on `color_mode`, with options for monochrome (green/amber), original source colors, hue-shifted, rainbow, or thermal palettes. Saturation, brightness, and hue offset are applied.
7. **CRT Effects**: Optional scanlines, phosphor glow, flicker, and barrel distortion are layered on top.
8. **Matrix Animation**: If `scroll_speed` is non-zero, characters scroll vertically like matrix rain, with density controlled by `rain_density` and random character changes driven by `char_jitter`.

### Character Sets

The effect supports six distinct character sets, selected via `charset` parameter:

- **Charset 0 (Classic)**: Density-based characters `" .:-=+*#%@"` rendered procedurally as dots, crosses, and filled grids.
- **Charset 1 (Blocks)**: Varying fill patterns using block elements.
- **Charset 2 (Braille-like)**: 2×4 dot grid patterns mimicking Braille characters.
- **Charset 3 (Matrix)**: Katakana-inspired geometric shapes with time-based animation.
- **Charset 4 (Binary)**: Only "0" and "1" characters with precise vector shapes.
- **Charset 5 (Custom)**: Reserved for future custom texture atlas support.

Each charset uses mathematical functions to render character shapes without external textures, ensuring the effect remains self-contained and performant.

### CRT Simulation

The CRT effects are implemented as post-processing passes:

- **Scanlines**: Horizontal lines with intensity controlled by `scanlines`.
- **Phosphor Glow**: A blur-like effect that makes characters appear to glow, radius controlled by `phosphor_glow`.
- **Flicker**: Random brightness modulation at high frequency (`flicker`).
- **Barrel Distortion**: A radial distortion that bends the image outward from center (`curvature`).
- **Noise**: Static noise overlay (`noise_amount`).

### Matrix Rain Mode

When `scroll_speed` is non-zero, the effect enters "matrix rain" mode where characters fall vertically. The speed is controlled by `scroll_speed` (negative for upward, positive for downward). The `rain_density` parameter controls what fraction of cells contain active falling characters. The `char_jitter` parameter causes characters to randomly change as they fall, creating the classic digital rain aesthetic. The `wave_amount` and `wave_freq` parameters add sinusoidal distortion to the character positions.

## Methods

### Core Shader Functions

#### `render_char(vec2 local_uv, float char_index, int charset_id) -> float`

Renders a single ASCII character procedurally. `local_uv` is the UV coordinate within the character cell (0-1). `char_index` is a normalized value (0-1) selecting which character to draw from the charset. `charset_id` selects the character set (0-5).

**Implementation Details**:
- Uses `hash()` functions for pseudo-random patterns.
- For charset 0: Maps `char_index` to one of 10 density levels and renders appropriate pattern (dot, cross, grid).
- For charset 2: Creates a 2×4 dot grid where each dot's presence is determined by comparing `char_index` to a threshold derived from dot position.
- For charset 3: Generates bar and corner shapes with time-based variation using `hash()` and `time`.
- For charset 4: Draws precise vector shapes for "0" (ring) and "1" (bars).
- Returns a float in 0.0-1.0 representing character opacity at that UV coordinate.

#### `hash(vec2 p) -> float` and `hash3(vec3 p) -> float`

Pseudo-random hash functions using a sine-based dot product with prime numbers. Used for procedural texture generation and matrix rain character selection.

#### `rgb2hsv(vec3 c) -> vec3` and `hsv2rgb(vec3 c) -> vec3`

Color space conversion utilities for hue manipulation in color modes.

### Parameter Mapping

All user-facing parameters use 0-10 range and are remapped as follows:

| Parameter | Range (0-10) | Operational Range |
|-----------|--------------|-------------------|
| `cell_size` | 0-10 | 4-32 pixels |
| `aspect_correct` | 0-10 | 0.4-1.0 (character aspect ratio) |
| `charset` | 0-10 | 0-5 (integer charset ID) |
| `threshold_curve` | 0-10 | 0.3-3.0 (gamma) |
| `edge_detect` | 0-10 | 0-1 (mix factor) |
| `detail_boost` | 0-10 | 0-3 (contrast enhancement) |
| `color_mode` | 0-10 | 0-5 (integer mode ID) |
| `fg_brightness` | 0-10 | 0.3-3.0 |
| `bg_brightness` | 0-10 | 0-0.5 |
| `saturation` | 0-10 | 0-2.0 |
| `hue_offset` | 0-10 | 0-1.0 |
| `scanlines` | 0-10 | 0-1 |
| `phosphor_glow` | 0-10 | 0-2 |
| `flicker` | 0-10 | 0-0.1 |
| `curvature` | 0-10 | 0-0.3 |
| `noise_amount` | 0-10 | 0-0.15 |
| `scroll_speed` | 0-10 | -5 to 5 |
| `rain_density` | 0-10 | 0-1 |
| `char_jitter` | 0-10 | 0-1 |
| `wave_amount` | 0-10 | 0-0.5 |
| `wave_freq` | 0-10 | 1-20 |

## Edge Cases

### Performance Considerations

- **High Resolution**: At high resolutions with small `cell_size` (large character grid), the shader may become fill-rate bound due to multiple texture samples per cell. The effect samples the source texture at the center of each cell, plus optionally for edge detection. On 4K output, a cell size of 4 pixels creates a 960×540 grid (518,400 cells), which can stress GPU fill rate.
- **Large Cell Size**: Very large cells (cell_size > 20) may cause visible blockiness and loss of detail, as each character covers many source pixels. This is expected behavior but can be artistically useful.
- **Aspect Ratio**: The `aspect_correct` parameter adjusts character cell aspect ratio to prevent character distortion on non-square pixels. Incorrect settings can make characters appear stretched or squished.

### Matrix Rain Mode

- **Scroll Speed**: Negative `scroll_speed` values cause characters to rise rather than fall. Extreme values (>5 or <-5) can cause visual artifacts due to time wrapping.
- **Rain Density**: Setting `rain_density` too high (>0.8) can make the screen mostly solid characters, losing the background. Too low (<0.1) makes the effect subtle.
- **Char Jitter**: High `char_jitter` causes characters to change every frame, creating a chaotic "glitch" aesthetic. Zero jitter makes characters static as they scroll.

### CRT Effects

- **Barrel Distortion**: High `curvature` (>0.2) can cause visible image stretching at corners and may interact poorly with other post-processing effects that expect linear coordinates.
- **Phosphor Glow**: High values (>1.5) can cause significant blur and reduce readability of characters. The glow is implemented as a simple radial blur in screen space.
- **Flicker**: Even small `flicker` values can cause eye strain during extended viewing. Recommended to keep below 0.05.

### Color Modes

- **Thermal Mode (color_mode=10)**: Maps luminance to black→red→yellow→white heatmap. May clip bright whites if `fg_brightness` is too high.
- **Rainbow Mode (color_mode=8)**: Uses full HSV spectrum. High `saturation` can cause color banding in gradients.
- **Original Mode (color_mode=4)**: Preserves source colors but applies brightness and saturation adjustments. Can produce unexpected color combinations if source image has strong color casts.

### Edge Cases in Character Rendering

- **Charset 2 (Braille)**: The 2×4 dot grid has 8 dots. The `char_index` determines which dots are lit based on a threshold pattern. At extreme `char_index` values (near 0 or 1), all dots may be off or on, reducing variety.
- **Charset 3 (Matrix)**: Uses `time` to animate characters. If `time` is not updated (frozen), the characters become static. The hash function may produce visible patterns at certain resolutions due to aliasing.
- **Charset 4 (Binary)**: The "0" is rendered as a ring using `smoothstep`. At very high resolutions, the ring may appear thin or broken if `local_uv` sampling is not precise.

### Parameter Boundary Conditions

- **Zero Values**: `cell_size=0` would theoretically produce infinite grid resolution but is clamped to minimum 4 pixels. `scroll_speed=0` disables matrix animation. `edge_detect=0` disables edge detection entirely.
- **Maximum Values**: `cell_size=10` maps to 32 pixels, which may be too coarse for detailed source material. `curvature=10` maps to 0.3, which is already quite strong; higher values would be visually overwhelming.
- **Aspect Ratio**: `aspect_correct=0` yields 0.4 (narrow characters), `aspect_correct=10` yields 1.0 (square characters). Values outside this range are not supported.

## Legacy Context

The ASCII effect originates from the VJlive codebase at `plugins/vcore/ascii_effect.py`. The original implementation was a fully-featured effect with 21 parameters covering grid control, character mapping, color, CRT simulation, and animation. The code is written in GLSL and embedded within a Python plugin class that integrates with the VJLive effect system.

**Key Legacy Characteristics**:
- The effect uses a **procedural character rendering** approach, avoiding texture atlas lookups entirely. This keeps memory footprint low and allows infinite resolution scaling.
- The **matrix rain mode** is a distinctive feature that transforms the effect from a static ASCII filter into an animated display reminiscent of the "Matrix" film trilogy.
- The **CRT simulation** includes multiple layers (scanlines, glow, flicker, curvature) that together create an authentic retro terminal look.
- The **parameter range** of 0-10 is consistent with VJLive's convention of using normalized 0-10 ranges for all effect parameters, mapped to meaningful operational ranges internally.
- The **charset selection** is implemented as a series of `if-else` branches in the shader, each containing a self-contained character rendering routine. This is efficient because only one charset is active per frame, and the branch is taken once per character cell, not per pixel.

**Legacy Code Structure** (from Qdrant snippets):
```glsl
// Uniforms (excerpt)
uniform float cell_size;
uniform float aspect_correct;
uniform float charset;
uniform float threshold_curve;
uniform float edge_detect;
uniform float detail_boost;
uniform float color_mode;
uniform float fg_brightness;
uniform float bg_brightness;
uniform float saturation;
uniform float hue_offset;
uniform float scanlines;
uniform float phosphor_glow;
uniform float flicker;
uniform float curvature;
uniform float noise_amount;
uniform float scroll_speed;
uniform float rain_density;
uniform float char_jitter;
uniform float wave_amount;
uniform float wave_freq;
```

The Python plugin wrapper (not shown in snippets) would inherit from a base `Effect` class, declare these parameters with their 0-10 ranges and human-readable names, and compile the fragment shader at initialization.

## Implementation Notes

### Porting Considerations

When implementing this effect in VJLive3, the following architectural decisions should be noted:

1. **Shader Compilation**: The entire fragment shader must be compiled as a single string. The `render_char()` function is large but necessary for procedural character generation. No external textures are required.
2. **Uniform Management**: All 21 parameters must be exposed as uniform variables with appropriate types (`float` for most, `int` for charset and color_mode after remapping). The plugin system should handle automatic uniform location caching.
3. **Time Uniform**: The shader uses `time` for matrix rain animation and character jitter. This must be provided by the rendering engine as a global uniform or effect-specific parameter.
4. **Resolution Handling**: The shader expects `resolution` uniform to compute grid cell positions. This is standard for full-screen effects.
5. **Performance Optimization**: The inner loop over grid cells is implicit in the fragment shader—each fragment corresponds to one character cell. The shader does **not** iterate over multiple samples per cell except for optional edge detection (which would require additional texture reads). The legacy code snippet shows edge detection is mixed in but the exact implementation detail is truncated; likely it involves sampling neighboring cells or using a Sobel filter on the source texture before character selection.
6. **Edge Detection**: The `edge_detect` parameter suggests the effect can enhance character selection based on image edges. The full implementation likely computes a simple gradient magnitude from the source texture and uses it to bias the character index toward higher-density characters at edges. This enhances readability of outlines.
7. **Detail Boost**: The `detail_boost` parameter probably applies a local contrast enhancement before sampling luminance, making subtle textures more visible in the ASCII representation.
8. **Aspect Correction**: The `aspect_correct` parameter adjusts the character cell's width-to-height ratio to compensate for non-square pixels in the source or output. This is important because ASCII characters are inherently taller than wide in most fonts; the procedural rendering must account for this to avoid stretched characters.

### Missing Implementation Details

The provided legacy snippets are incomplete. The following sections of the shader were not captured in the Qdrant results and would need to be reconstructed from the full source:

- **Complete `main()` function**: After the parameter remapping, the main logic for grid traversal, texture sampling, luminance calculation, and final color composition is missing. The snippets show the beginning of `main()` but not the full body.
- **Edge detection implementation**: How exactly `edge_detect` is integrated is not shown.
- **Wave distortion**: The application of `wave_amount` and `wave_freq` to character positions is not visible in the snippets.
- **Noise generation**: The `noise_amount` parameter likely uses a hash function but the exact integration is missing.
- **Color mode implementations**: The mapping from `color_mode` integer to actual color palette logic is not fully shown. The snippets mention modes but not the complete `if` chain for each mode.
- **Background handling**: How `bg_brightness` is applied (likely as a base color behind characters) is not explicit.

These gaps are marked with `[NEEDS RESEARCH]` in the spec and should be filled by consulting the full legacy source file or by reverse-engineering from the existing partial code and test suite.

### Integration with VJLive3

The effect should integrate as a standard VJLive3 plugin:

- **Plugin Class**: `ASCIIEffect` inheriting from `BaseEffect` or `ShaderEffect`.
- **Parameter Declaration**: Use the plugin system's parameter registration to expose all 21 parameters with their 0-10 ranges and user-friendly names.
- **Shader Source**: Store the GLSL fragment shader as a multi-line string in the plugin or load from an external `.glsl` file if the architecture supports it.
- **Uniform Updates**: In the plugin's `render()` method, update all uniform values each frame before drawing. The `time` uniform should come from the engine's global time or effect-specific timing.
- **Texture Input**: The source texture (`tex0`) is provided by the node graph. The effect should sample from its input texture.
- **Output**: The effect writes to the framebuffer as a full-screen pass.

## Testing

### Unit Tests

The legacy test suite for `ascii_effect` contains 14 tests that verify:

- Parameter range validation (all parameters accept 0-10 values and clamp appropriately)
- Shader compilation success (the GLSL code compiles without errors)
- Uniform location caching (uniforms are found and set correctly)
- Basic rendering output (non-null framebuffer, reasonable pixel values)
- Character grid alignment (cells align to grid based on `cell_size`)
- Color mode switching (different color modes produce visibly different outputs)
- Matrix animation (when `scroll_speed` non-zero, characters move over time)
- CRT effects (scanlines, glow, flicker produce visible changes)
- Edge detection (when enabled, characters change at edges)
- Performance benchmarks (rendering time under threshold for various resolutions)

These tests should be ported or adapted to VJLive3's testing framework, which likely uses headless OpenGL context and pixel-readback comparisons.

### Integration Tests

- Load the plugin in a node graph with a test video source (e.g., color bars, moving gradient).
- Verify that changing parameters produces smooth, continuous output changes without artifacts.
- Test with various output resolutions (1080p, 4K) to ensure performance remains acceptable.
- Test with different aspect ratios (16:9, 4:3) to verify `aspect_correct` works correctly.
- Test matrix rain mode with different `scroll_speed` values to ensure smooth animation.

### Regression Tests

- Compare output frames against golden images from the legacy implementation for a set of known parameter combinations. This ensures visual parity during porting.
- Test that parameter changes do not cause shader recompilation (should be uniform updates only).

## Documentation Status

This spec is **incomplete**. The following items require further investigation:

- [ ] Full `main()` function body from legacy source
- [ ] Exact edge detection algorithm
- [ ] Wave distortion implementation details
- [ ] Complete color mode palette definitions
- [ ] Noise generation method
- [ ] Performance characteristics on various hardware
- [ ] Memory usage profile (no dynamic allocations in shader)
- [ ] Interaction with other effects in a node chain (does it require specific input formats?)

## Easter Egg Council

**Idea**: "The Turing Terminal" — When `charset` is set to exactly 7.0 (a value not normally accessible via UI), the effect switches to a special mode where characters form a simulation of Conway's Game of Life running atop the ASCII rendering. The Game of Life patterns are computed in a separate shader pass and influence character selection, creating evolving organic patterns that interact with the underlying video luminance. This easter egg pays homage to Alan Turing and the intersection of computation, artificial life, and retro computing aesthetics.

---

**Spec Version**: 1.0-draft  
**Last Updated**: 2026-02-27  
**Agent**: maxx-roo  
**Status**: Needs Research (partial legacy context retrieved)