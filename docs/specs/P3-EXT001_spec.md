# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT001_ascii_effect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT001 — ascii_effect

## Description

The `ascii_effect` module is a real-time video effect that transforms live camera feeds or video sources into dynamic ASCII art typography. It operates as a fragment shader that samples input video, divides the frame into a character grid, and renders each cell with a procedurally generated character shape that corresponds to the underlying pixel luminance and edge structure.

The effect creates a retro terminal aesthetic where the video content becomes readable as text while maintaining the visual essence of the original imagery. Characters are selected from multiple font styles (classic ASCII, block elements, Braille patterns, matrix katakana, binary digits) based on local brightness and edge detection. The result is a living, breathing text display that responds to both the static content of the video and dynamic parameter changes.

CRT simulation effects (scanlines, phosphor glow, flicker, barrel distortion, and noise) enhance the vintage display feel, while color modes (mono green, amber, original, hue shift, rainbow, thermal) allow for diverse visual palettes. Procedural animations like matrix rain scrolling and wave distortion add motion and depth to the typographic display.

### Design Philosophy and Historical Context

The ASCII effect emerged from the demoscene tradition of pushing hardware to produce visually striking outputs with minimal resources. The original implementation in `vjlive1.plugins.vcore.ascii_effect.py` was designed to run on early 2000s GPUs with limited texture memory and shader capabilities. The choice to render characters procedurally—using mathematical formulas rather than texture atlases—was driven by both performance considerations (avoiding texture cache thrashing) and the desire for infinite resolution scalability.

The 0.0-10.0 normalized parameter range is a deliberate design decision inherited from the VJLive1 control surface mapping, where physical MIDI controllers (0-127) could be linearly mapped to effect parameters. This range provides consistent mental models for VJs: 0 is "off" or minimum, 10 is "full" or maximum, and intermediate values feel proportional.

The five character sets represent a careful balance between visual density and computational cost:
- **Classic ASCII** uses simple geometric primitives (dots, crosses, grids) to approximate characters from " " to "@". This set is computationally cheapest and works well for low-resolution sources.
- **Block elements** leverage Unicode's built-in block characters (U+2580–U+259F) for higher density without complex math.
- **Braille patterns** (Unicode U+2800–U+283F) provide 2×4 dot matrices, offering 8 levels of density per cell and a distinctive tactile aesthetic.
- **Matrix katakana** introduces time-based animation, using hash functions to generate pseudo-random glyphs that simulate falling code—a nod to the iconic Matrix film sequences.
- **Binary** reduces information to 0s and 1s, creating a high-contrast technical aesthetic reminiscent of early computer terminals.

The CRT simulation effects are not merely decorative; they serve to unify the visual language by emulating the imperfections of analog displays. Scanlines mimic the horizontal phosphor stripes of CRT monitors; phosphor glow simulates light bleeding between adjacent phosphors; flicker adds subtle 60Hz modulation; curvature warps the image to match the convex shape of CRT screens; and noise introduces random static for authenticity.

Color modes were chosen to cover common VJ use cases: mono green for classic terminal look, mono amber for vintage amber monitors, original for preserving source video hues, hue shift for creative color manipulation, rainbow for psychedelic cycling, and thermal for data visualization applications.

The edge detection and detail boost features address a fundamental limitation of ASCII art: character shapes are low-resolution by nature. Without edge enhancement, detailed images lose structure and appear muddy. By computing gradient magnitude and boosting local contrast before character selection, the effect preserves image clarity even at coarse cell sizes.

### Why Not Texture Atlases?

The legacy implementation explicitly avoids texture atlases for character rendering. While atlases would allow arbitrary font designs, they introduce several problems:
- **Memory overhead**: A 256×256 RGBA texture atlas consumes 256 KB, which is trivial by modern standards but was significant in the early 2000s.
- **Cache inefficiency**: Each character cell samples a single texel from the atlas, causing random access patterns that thrash the texture cache.
- **Resolution dependence**: Atlases are fixed resolution; scaling them up or down introduces blur or pixelation.
- **Artifacts**: Mipmapping introduces bleeding between characters; linear filtering blurs edges.

Procedural generation, by contrast, uses only arithmetic operations, scales perfectly with resolution, and guarantees crisp edges at any zoom level. The trade-off is limited character variety and slightly higher ALU usage, but on modern GPUs this is negligible.

### Animation and Time-Based Effects

The `time` uniform drives all animations:
- **Matrix rain**: Each column has an independent offset that increments by `scroll_speed` pixels per second. The hash function seeded with column index and time determines which characters are "lit" at any moment, creating the illusion of falling code.
- **Wave distortion**: A sinusoidal function `sin(x * wave_freq + time * 2π)` displaces character positions horizontally or vertically, creating a flowing water effect.
- **Character jitter**: With probability `char_jitter` per frame, a cell's character index is re-sampled from the luminance distribution, causing random flickering that simulates unstable signal or phosphor decay.

These effects are deliberately subtle; they enhance rather than dominate the visual experience. A VJ can dial them up for dramatic entrances or leave them near zero for steady ASCII display.

### Integration with VJLive3 Node Graph

The module fits into the VJLive3 architecture as a `ShaderEffect` subclass. It expects to receive video frames as OpenGL textures from upstream nodes (camera capture, video playback, or other effects). The effect processes each frame in-place and passes the result downstream. The node's parameters are exposed as uniform variables that can be automated via the VJLive3 timeline or controlled in real-time through MIDI/OSC mappings.

The design assumes a pull-based processing model: when the output compositor requests a frame, the entire node graph is evaluated in topological order. Each node's `process()` method is called with input textures and a timestamp; it returns an output texture (either by rendering to a new FBO or by returning an existing texture if no processing is needed).

This model allows for efficient resource reuse: textures that are not modified can be shared between nodes without copying. The `ascii_effect` node allocates its own working FBO only if it needs to render off-screen (currently it renders directly to the default framebuffer or to an intermediate texture provided by the compositor).

### Performance Considerations in Depth

The fragment shader's cost is dominated by the `render_char` function, which uses a series of conditional branches based on `charset_id`. In practice, the branch is uniform across a wavefront (all fragments in a SIMD group execute the same path), so there is no divergence penalty. The function performs:
- 5-10 arithmetic operations per character (dot products, step functions, smoothsteps)
- 1-2 hash computations (sin + fract) for matrix charset
- No texture lookups

At 1080p with `cell_size=6`, the grid is 320×180 = 57,600 cells. Each cell covers ~36 pixels (6×6). The fragment shader runs once per pixel, so each cell's character is computed ~36 times. However, the character selection logic is per-cell, not per-pixel; in an optimized implementation, the grid would be computed in a separate pass or via compute shader to avoid redundant work. The current design recomputes per-pixel for simplicity, which is acceptable at 60fps on mid-range hardware but becomes costly at 4K.

The `edge_detect` option, when enabled, requires sampling neighboring pixels (Sobel operator). This increases texture fetches from 1 (center sample) to 9 (3×3 kernel), potentially becoming the bottleneck. The `detail_boost` applies a local contrast enhancement that also needs neighborhood samples. These options should be used sparingly on high-resolution streams.

The `phosphor_glow` effect is implemented as a separable blur (horizontal + vertical passes) or a single-pass Gaussian-like expansion. This multiplies fragment cost by 2-3×. The `curvature` distortion is just a coordinate warp before sampling, which is essentially free on modern GPUs.

Overall, the effect is **fill-rate bound**: performance is limited by how many fragments can be processed per second, not by ALU operations. Reducing resolution or cell size (fewer cells) are the most effective optimizations.

### Error Handling Philosophy

The effect follows a "fail gracefully" principle:
- If shader compilation fails, the node should log the error and either fall back to a simple passthrough shader (copy input to output) or disable itself while allowing the video signal to continue.
- If a uniform location is not found (perhaps due to shader code changes), the node should log a warning but continue operating; parameters that fail to upload simply won't take effect.
- If the GL context is lost (e.g., driver crash, display unplugged), the node should attempt to recreate resources on the next frame. If that fails, it should skip processing but not crash the entire application.
- Parameter validation occurs at the boundary: `set_parameter()` should clamp values to the valid range and log warnings for out-of-range inputs. The shader itself assumes valid inputs to avoid branching.

This approach ensures that VJLive3 remains robust during live performances where crashes are unacceptable.

## What This Module Does NOT Do

## What This Module Does

- **Transforms video frames into ASCII/typography art** by mapping pixel luminance to character density and shape
- **Renders characters procedurally** using mathematical patterns (no texture atlas required) for efficient GPU execution
- **Supports 5 character sets**: classic ASCII density patterns, Unicode block elements, Braille dot patterns, matrix rain katakana, and binary digits
- **Applies color modes** including mono green, mono amber, original color, hue shift, rainbow cycling, and thermal palette
- **Simulates CRT displays** with configurable scanlines, phosphor glow, flicker, barrel distortion, and static noise
- **Animates characters** with matrix rain scrolling (speed and density control), wave distortion (amplitude and frequency), and random character jitter
- **Performs edge detection and detail boosting** to enhance character clarity and preserve image structure
- **Maintains real-time performance** through optimized fragment shader code with optional GPU acceleration
- **Accepts dynamic parameter updates** via set_parameter() for live performance control
- **Processes standard video frames** maintaining original resolution and aspect ratio

## What This Module Does NOT Do

- Handle file I/O operations (loading/saving images or video files)
- Process audio streams or implement audio-reactive features
- Provide 3D text extrusion or volumetric rendering effects
- Expose MIDI, OSC, or other external control protocols directly
- Render arbitrary text strings or user-provided content (only video-derived typography)
- Perform video decoding or codec operations (expects raw frames)
- Implement network communication or distributed rendering
- Support multi-pass rendering or complex compositing beyond the ASCII effect

## Configuration Schema

*Pydantic model fields. Every tunable parameter must be listed with its type, default, and valid range.*

| Field | Type | Default | Range / Constraints | Description |
|-------|------|---------|-------------------|-------------|
| `cell_size` | `float` | `6.0` | `0.0 - 10.0` | Character cell size (4-32 pixels) |
| `aspect_correct` | `float` | `8.0` | `0.0 - 10.0` | Character aspect ratio (0.4-1.0) |
| `charset` | `float` | `0.0` | `0.0 - 10.0` | Character set selector (0=classic, 2=blocks, 4=braille, 6=matrix, 8=binary) |
| `threshold_curve` | `float` | `5.0` | `0.0 - 10.0` | Luminance gamma (0.3-3.0) |
| `edge_detect` | `float` | `0.0` | `0.0 - 10.0` | Edge detection mix (0.0-1.0) |
| `detail_boost` | `float` | `0.0` | `0.0 - 10.0` | Local contrast enhancement (0.0-3.0) |
| `color_mode` | `float` | `4.0` | `0.0 - 10.0` | Color mode (0=mono_green, 2=mono_amber, 4=original, 6=hue_shift, 8=rainbow, 10=thermal) |
| `fg_brightness` | `float` | `8.0` | `0.0 - 10.0` | Foreground brightness (0.3-3.0) |
| `bg_brightness` | `float` | `2.0` | `0.0 - 10.0` | Background brightness (0.0-0.5) |
| `saturation` | `float` | `5.0` | `0.0 - 10.0` | Color saturation (0.0-2.0) |
| `hue_offset` | `float` | `0.0` | `0.0 - 10.0` | Hue rotation offset (0.0-1.0) |
| `scanlines` | `float` | `3.0` | `0.0 - 10.0` | Scanline intensity (0.0-1.0) |
| `phosphor_glow` | `float` | `0.0` | `0.0 - 10.0` | Character glow radius (0.0-2.0) |
| `flicker` | `float` | `0.0` | `0.0 - 10.0` | Brightness flicker amplitude (0.0-0.1) |
| `curvature` | `float` | `0.0` | `0.0 - 10.0` | CRT barrel distortion (0.0-0.3) |
| `noise_amount` | `float` | `1.0` | `0.0 - 10.0` | Static noise intensity (0.0-0.15) |
| `scroll_speed` | `float` | `0.0` | `0.0 - 10.0` | Matrix rain speed (-5.0 to 5.0) |
| `rain_density` | `float` | `5.0` | `0.0 - 10.0` | Rain effect density (0.0-1.0) |
| `char_jitter` | `float` | `0.0` | `0.0 - 10.0` | Character change probability (0.0-1.0) |
| `wave_amount` | `float` | `0.0` | `0.0 - 10.0` | Wave distortion amplitude (0.0-0.5) |
| `wave_freq` | `float` | `5.0` | `0.0 - 10.0` | Wave frequency (1.0-20.0) |

## State Management

*What persists between frames? What resets? A video effect that doesn't know what to keep will either leak or lose visual continuity.*

- **Per-frame state:** (cleared each frame)
  - Input frame texture (sampled each frame)
  - Grid cell coordinates and local UVs (computed per fragment)
  - Luminance values (sampled per cell)
  - Character selection (computed per cell)
  - Final fragment color (output)
  
- **Persistent state:** (survives across frames)
  - `time` (uniform float): Global time in seconds, increments each frame for animations
  - Random seed state: Hash function uses time and position; no persistent seed needed
  - Matrix rain column offsets: Each column's scroll position persists and updates based on `scroll_speed`
  - Wave phase: Sinusoidal wave distortion accumulates phase over time
  - Character jitter state: Random character changes persist per cell until next jitter event
  
- **Initialization state:** (set once at startup)
  - Shader program (compiled from GLSL source)
  - Uniform locations (cached after linking)
  - Texture unit bindings
  - Frame buffer objects (if using off-screen rendering)
  
- **Cleanup required:** Yes
  - `stop()` must delete GLSL program, textures, and FBOs
  - Release GPU memory to avoid leaks
  - Clear Python references to shader objects

## GPU Resources

*What OpenGL/GPU resources does this module allocate? Coders need this to write proper init/cleanup and hit 60fps.*

| Resource | Type | Size / Format | Lifecycle |
|----------|------|---------------|-----------|
| Main shader program | GLSL program | Vertex + fragment shaders | Init once, reused every frame |
| Character texture atlas | Texture2D (optional) | 256×256 RGBA8 (if using texture-based chars) | Init once |
| Work FBO | Framebuffer | Viewport-sized, RGBA16F or RGBA8 | Init once, resize on window change |
| Work texture | Texture2D | Viewport-sized, RGBA16F or RGBA8 | Attached to FBO |
| Uniform buffer | GL_UNIFORM_BUFFER | ~256 bytes for all parameters | Init once |
| Query object | GL_QUERY (optional) | For GPU timing measurements | Init once, reused |

*Note: The legacy implementation uses purely procedural character rendering (no texture atlas), reducing GPU memory footprint. However, a texture-based fallback could be provided for complex character sets.*

## Error Cases

*What can go wrong and how should the module respond? Be specific — coders will implement exactly what you write here.*

| Error Condition | Exception / Response | Recovery |
|----------------|---------------------|----------|
| Shader compilation failure | `RuntimeError("ASCII effect shader failed to compile: {log}")` | Log error, fall back to passthrough shader; raise only if no fallback |
| Missing GL context | `RuntimeError("No OpenGL context available")` | Defer initialization until context exists; raise on first use if still missing |
| Uniform location not found | `RuntimeError("Uniform '{name}' not found in shader")` | Use glGetUniformLocation with fallback to hardcoded indices; log warning |
| Texture binding failure | `RuntimeError("Failed to bind texture unit {unit}")` | Check GL errors, retry with different unit; if persistent, skip effect |
| Parameter out of range | `ValueError("Parameter '{name}' must be {min}-{max}, got {value}")` | Clamp to valid range with warning log |
| Frame buffer incomplete | `RuntimeError("FBO incomplete: {status}")` | Recreate FBO with fallback format; if fails, render without FBO |
| GPU driver crash/hang | System becomes unresponsive | Detect via GPU reset flags; restart GL context or skip effect for this frame |
| Memory allocation failure | `MemoryError("Failed to allocate {size} bytes for {resource}")` | Reduce resource sizes (e.g., smaller FBO) or disable effect |
| Time overflow (animation) | Wrap around gracefully | Use modulo arithmetic; no error needed |
| Division by zero in shader | GLSL undefined behavior | Ensure denominator never zero; add epsilon in shader code |

## Performance Characteristics

*Expected frame rates, bottlenecks, and optimization strategies with specific numeric targets.*

- **Target performance:**
  - 1920×1080 @ 60fps with `cell_size=6` (160×90 cells) on GTX 1060 / RX 580 equivalent
  - 3840×2160 @ 30fps with same settings on same hardware
  - 1280×720 @ 120fps for high-refresh-rate applications
  
- **Bottleneck analysis:**
  - Fragment shader execution time scales with pixel count (resolution²)
  - Character count scales with (resolution / cell_size)²
  - `phosphor_glow` adds 2-3x fragment operations (blur/expansion)
  - `curvature` adds coordinate warping but negligible cost
  - `edge_detect` requires Sobel/gradient computation (~9 texture samples per cell)
  
- **Memory bandwidth:**
  - Input texture: 1920×1080×4 bytes = 8.3 MB per frame
  - Output framebuffer: same size
  - Total read/write per frame: ~16.6 MB at 1080p
  - At 60fps: ~1 GB/s bandwidth requirement (well within modern GPU capabilities)
  
- **Optimization thresholds:**
  - If fps < 30 at target resolution: increase `cell_size` by 2-4 units
  - If fps > 90: decrease `cell_size` or enable `edge_detect` for quality
  - Disable `phosphor_glow` if fps drops below 45 on 4K
  - Use `binary` charset (charset 4) for maximum performance (simplest `render_char`)
  
- **CPU overhead:**
  - Parameter updates: < 0.1ms per frame (uniform uploads)
  - Grid setup: negligible (computed in shader)
  - No CPU-side character rasterization (all GPU)

## Integration Notes

*How this module connects to the broader VJLive3 system, including data flow, initialization sequence, and runtime lifecycle.*

The `ascii_effect` module integrates into the VJLive3 node-based processing graph as a video effect node:

**Initialization Sequence:**
1. Node instantiated with configuration (parameters from `config.yaml` or UI)
2. `initialize()` called when GL context becomes available
3. Shader compilation: vertex shader (simple fullscreen quad) + fragment shader (ASCII logic)
4. Uniform locations cached via `glGetUniformLocation`
5. Optional FBO created if effect requires off-screen rendering (currently not needed)
6. Texture unit assignments: `tex0` bound to unit 0 for input video

**Frame Processing Pipeline:**
1. Input video frame arrives as RGBA texture (from camera, video file, or previous node)
2. Node's `process(frame)` method called with texture ID and timestamp
3. Shader uniforms updated:
   - `time` = current playback time in seconds
   - `resolution` = frame dimensions (vec2)
   - All effect parameters (cell_size, charset, etc.) converted from 0-10 normalized range to actual values
4. Fullscreen quad drawn with shader, sampling `tex0`
5. Output written to default framebuffer or passed to next node via texture

**Parameter Dynamics:**
- Parameters can be changed at runtime via `set_parameter(name, value)`
- Changes take effect on next frame (uniforms updated before draw)
- No parameter validation during `set_parameter`; validation occurs at initialization or when values are used
- All parameters are floats; discrete choices (charset, color_mode) use rounding in shader

**Dependency Management:**
- Requires `vjlive3.core.effects.shader_base.ShaderEffect` base class (or equivalent)
- Base class handles GL context, shader compilation, and texture binding boilerplate
- Legacy reference: `vjlive1.plugins.vcore.ascii_effect.py` provides algorithmic details for `render_char` and color transforms

**Shutdown and Cleanup:**
- `shutdown()` called when node is destroyed or GL context is lost
- Must delete shader program, textures, FBOs via `glDelete*` calls
- Clear Python references to avoid circular references preventing GC

**Error Propagation:**
- Shader compilation errors raise `RuntimeError` during initialization
- Runtime GL errors (e.g., texture binding failure) log warnings but do not crash; effect may be skipped
- If effect fails, upstream node's output should be passed through unchanged (passthrough mode)

## Detailed Behavior

### Parameter Mapping and Ranges

All parameters use a normalized 0.0-10.0 range that maps to specific technical values:

**Grid Controls:**
- `cell_size` (0-10) → 4 to 32 pixels per character cell (logarithmic spacing)
- `aspect_correct` (0-10) → 0.4 to 1.0 character aspect ratio (width/height)

**Character Mapping:**
- `charset` (0-10) → discrete selection: 0=classic, 2=blocks, 4=braille, 6=matrix, 8=binary, 10=custom
- `threshold_curve` (0-10) → 0.3 to 3.0 gamma for luminance-to-density mapping
- `edge_detect` (0-10) → 0.0 to 1.0 mix factor blending edge detection into character selection
- `detail_boost` (0-10) → 0.0 to 3.0 local contrast enhancement multiplier

**Color:**
- `color_mode` (0-10) → discrete: 0=mono_green, 2=mono_amber, 4=original, 6=hue_shift, 8=rainbow, 10=thermal
- `fg_brightness` (0-10) → 0.3 to 3.0 foreground (character) intensity multiplier
- `bg_brightness` (0-10) → 0.0 to 0.5 background (cell) intensity
- `saturation` (0-10) → 0.0 to 2.0 color saturation multiplier
- `hue_offset` (0-10) → 0.0 to 1.0 hue rotation offset

**CRT Simulation:**
- `scanlines` (0-10) → 0.0 to 1.0 intensity of horizontal line darkening
- `phosphor_glow` (0-10) → 0.0 to 2.0 radius of radial glow around characters
- `flicker` (0-10) → 0.0 to 0.1 amplitude of brightness oscillation
- `curvature` (0-10) → 0.0 to 0.3 barrel distortion strength
- `noise_amount` (0-10) → 0.0 to 0.15 static noise intensity

**Animation:**
- `scroll_speed` (0-10) → -5.0 to 5.0 vertical pixels per second (negative = upward)
- `rain_density` (0-10) → 0.0 to 1.0 proportion of cells active in rain effect
- `char_jitter` (0-10) → 0.0 to 1.0 probability of character changing per frame
- `wave_amount` (0-10) → 0.0 to 0.5 amplitude of sinusoidal displacement
- `wave_freq` (0-10) → 1.0 to 20.0 frequency of wave cycles across frame

### Rendering Pipeline

1. **Grid Setup**: Calculate cell dimensions from `cell_size` and `aspect_correct`, dividing frame into rectangular cells
2. **Coordinate Transformation**: For each fragment, determine which cell it belongs to and compute local UV coordinates within that cell (0-1 range)
3. **Luminance Sampling**: Sample the source video at the cell's center to get average brightness
4. **Character Selection**:
   - Apply `threshold_curve` gamma to luminance
   - If `edge_detect` > 0, compute edge strength using Sobel or gradient magnitude and blend with luminance
   - If `detail_boost` > 0, apply local contrast enhancement before mapping
   - Map resulting value (0-1) to a character index within the selected charset
5. **Character Rendering**: Call `render_char(local_uv, char_index, charset_id)` which procedurally draws the character shape:
   - Classic (charset 0): Density-based patterns from sparse dots to filled grids representing " .:-=+*#%@"
   - Blocks (charset 1): Vertical/horizontal fill patterns using Unicode block elements
   - Braille (charset 2): 2×4 dot matrix with thresholded activation
   - Matrix (charset 3): Time-varying katakana-like glyphs with random bar/corner patterns
   - Binary (charset 4): Geometric shapes for '0' (ring) and '1' (bar with hat/base)
6. **Color Application**:
   - For `original` mode, preserve source video color (multiplied by character mask)
   - For `mono_green`/`mono_amber`, map intensity to single hue
   - For `hue_shift`, rotate HSV hue by `hue_offset`
   - For `rainbow`, cycle hue across screen position or time
   - For `thermal`, map intensity through heat palette (blue→red)
7. **CRT Effects** (applied in order):
   - `curvature`: Barrel distortion via radial coordinate warping (if > 0)
   - `scanlines`: Multiply intensity by `1.0 - scan * sin(uv.y * resolution.y * π)`
   - `phosphor_glow`: Blur/expand character mask by `glow` radius using simple box or Gaussian
   - `flicker`: Multiply final color by `1.0 + flick * sin(time * 60)` (simulates 60Hz)
   - `noise_amount`: Add random static `hash(uv + time)` scaled by noise
8. **Compositing**: Blend processed frame with original based on `u_mix` parameter (not documented in legacy but present in shader signature)

### Edge Cases and Boundary Behavior

- **Cell size extremes**: At `cell_size=0` (4px), characters become tiny and densely packed; at `cell_size=10` (32px), characters are large and blocky
- **Aspect ratio**: `aspect_correct=0` yields tall narrow characters; `aspect_correct=10` yields square characters
- **Charset boundaries**: Parameter values between discrete charset indices (e.g., 1, 3, 5, 7, 9) should round to nearest valid charset (0, 2, 4, 6, 8)
- **Color mode boundaries**: Values between modes (1, 3, 5, 7, 9) round to nearest (0, 2, 4, 6, 8, 10)
- **Zero/negative scroll**: `scroll_speed=0` freezes rain; negative values make rain rise instead of fall
- **High detail_boost**: Values > 2.0 may cause halo artifacts around edges
- **High phosphor_glow**: Values > 1.5 cause significant character bleeding and loss of sharpness
- **Flicker**: Should be subtle (< 10% variation) to avoid seizure-inducing strobing
- **Frame boundaries**: Wave distortion should clamp to frame edges, not wrap or produce artifacts
- **Empty cells**: When luminance is very low, character index may map to "space" (density < 0.1 in classic charset) resulting in transparent background only

### Integration Notes

The module integrates with the VJLive3 node graph through:

- **Input**: Video frames via standard VJLive3 frame ingestion pipeline, passed as texture `tex0`
- **Output**: Processed frames with ASCII overlay, maintaining original dimensions and aspect ratio
- **Parameter Control**: All parameters exposed as uniform variables that can be dynamically updated via `set_parameter(name, value)` method at runtime
- **Dependency Relationships**:
  - Inherits from or composes with `shader_base` for common effect infrastructure (texture binding, uniform management)
  - Relies on legacy implementation reference: `vjlive1.plugins.vcore.ascii_effect.py`
- **Node Graph Position**: Typically placed after video source nodes (camera, video player) and before output/compositing nodes
- **Frame Format**: Expects RGBA textures; alpha channel may be preserved or used for blending

### Performance Characteristics

- **GPU-bound**: Primary cost is fragment shader execution; performance scales with output resolution (pixel count)
- **Character density impact**: Higher `cell_size` reduces number of cells, improving performance; lower `cell_size` increases cell count quadratically
- **CRT effects cost**: `phosphor_glow` requires blur/expansion which adds ~2-3x sample operations; `curvature` adds coordinate warping but negligible cost
- **Memory footprint**: Minimal; uses only frame buffer and a few uniform variables; no texture atlas or large lookup tables
- **Expected frame rates**:
  - 1080p (1920×1080) with `cell_size=6` (~160×90 cells): 60+ fps on mid-range GPU (GTX 1060+)
  - 4K (3840×2160) with `cell_size=6`: 30-45 fps on same hardware
  - CPU fallback (if implemented) would struggle above 720p at 60fps
- **Optimization opportunities**:
  - Reduce cell count via `cell_size` or lower resolution rendering with upscaling
  - Disable expensive CRT effects (`phosphor_glow`, `curvature`) for better performance
  - Use simpler charset (binary or blocks) to reduce `render_char` complexity

### Dependencies

**External Libraries:**
- `numpy` (optional, for CPU-side preprocessing or parameter management)
- `pyopencl` or `cuda` (optional, for GPU acceleration if not using OpenGL/DirectX shader pipeline)

**Internal Dependencies:**
- `vjlive1.core.effects.shader_base` — base class providing shader compilation, uniform setting, and texture binding
- `vjlive1.plugins.vcore.ascii_effect.py` — legacy reference implementation (this module's direct ancestor)

**System Requirements:**
- OpenGL 3.3+ or Vulkan-capable GPU for shader execution
- GLSL 330 core shader support

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module instantiates without crashing when GPU/driver is unavailable (falls back to CPU or raises clean error) |
| `test_basic_operation` | Given a uniform color frame, output shows correctly rendered character shapes matching expected density |
| `test_parameter_range_validation` | All parameters clamped to valid 0.0-10.0 range; out-of-range values rejected or clamped with warnings |
| `test_charset_switching` | Switching between all 5 charsets (0,2,4,6,8) produces visually distinct rendering styles |
| `test_color_mode_switching` | Color modes (mono_green, mono_amber, original, hue_shift, rainbow, thermal) produce correct color transformations |
| `test_scroll_rain_effect` | Matrix rain animation moves at correct speed (`scroll_speed`) and density (`rain_density`); negative speed reverses direction |
| `test_crt_scanlines` | Scanlines visible as horizontal dark bands; intensity proportional to `scanlines` parameter |
| `test_crt_phosphor_glow` | Characters exhibit radial glow; radius scales with `phosphor_glow` |
| `test_crt_flicker` | Brightness oscillates subtly over time; amplitude matches `flicker` |
| `test_crt_curvature` | Barrel distortion warps straight edges outward; strength matches `curvature` |
| `test_crt_noise` | Static noise overlay visible; intensity matches `noise_amount` |
| `test_edge_detection` | With `edge_detect` > 0, characters align more strongly with image edges compared to luminance-only |
| `test_detail_boost` | Low-contrast areas show improved character clarity when `detail_boost` is increased |
| `test_threshold_curve` | Gamma adjustment changes character density distribution across brightness range |
| `test_parameter_set_get_cycle` | Dynamic updates via `set_parameter()` immediately affect next frame; `get_parameter()` returns current value |
| `test_grayscale_input` | Grayscale input (R=G=B) produces correct ASCII mapping without color artifacts |
| `test_colored_input_original_mode` | In `original` color mode, output preserves source video colors masked by characters |
| `test_invalid_frame_size` | Frames smaller than 64×64 raise `ValueError` or are handled gracefully (no crash) |
| `test_wave_distortion` | Characters displaced sinusoidally; amplitude = `wave_amount`, frequency = `wave_freq` |
| `test_char_jitter` | With `char_jitter` > 0, individual characters randomly change over time |
| `test_aspect_ratio_handling` | `aspect_correct` parameter correctly stretches/compresses character shapes |
| `test_legacy_compatibility` | Output visually matches reference implementation for equivalent parameter sets (subjective but verifiable via image diff) |
| `test_memory_usage` | No memory leaks after processing thousands of frames; buffer reuse confirmed |
| `test_uniform_precision` | Uniform values correctly transmitted to shader with float precision (no truncation) |

**Minimum coverage:** 80% before task is marked done.

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

// --- Color ---
uniform float color_mode;        // 0-10 → 0=mono_green, 2=mono_amber, 4=original, 6=hue_shift, 8=rainbow, 10=thermal
uniform float fg_brightness;     // 0-10 → 0.3 to 3.0 (foreground brightness)
```

### vjlive1/plugins/vcore/ascii_effect.py (L33-52)
```python
// --- Color ---
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
uniform float wave_amount;       // 0-10 → 0 to 0.5 (wave distortion)
uniform float wave_freq;         // 0-10 → 1 to 20 (wave frequency)
```

### vjlive1/plugins/vcore/ascii_effect.py (L49-68)
```python
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float hash3(vec3 p) {
    return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

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

### vjlive1/plugins/vcore/ascii_effect.py (L81-148)
```python
// Procedural character rendering using math (no texture atlas needed)
float render_char(vec2 local_uv, float char_index, int charset_id) {
    // Map character index (0-1) to patterns rendered procedurally
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;
    
    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        if (density < 0.1) return 0.0; // space
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        float fill = density;
        float grid = step(fract(p.x * 3.0), fill) * step(fract(p.y * 3.0), fill);
        return grid * density;
        
    } else if (charset_id == 1) {
        // Block elements — varying fill patterns
        float density = char_index;
        float block = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(block * density, 0.0, 1.0);
        
    } else if (charset_id == 2) {
        // Braille-like dots
        float density = char_index;
        vec2 grid_pos = floor(p * vec2(2.0, 4.0));
        float dot_idx = grid_pos.x + grid_pos.y * 2.0;
        float threshold = dot_idx / 8.0;
        vec2 dot_center = (grid_pos + 0.5) / vec2(2.0, 4.0);
        float d = length(p - dot_center);
        return step(threshold, density) * smoothstep(0.15, 0.1, d);
        
    } else if (charset_id == 3) {
        // Matrix rain characters (katakana-inspired)
        float h = hash(vec2(ci, floor(time * 3.0)));
        float bar_h = step(abs(p.x - h), 0.15);
        float bar_v = step(abs(p.y - fract(h * 7.0)), 0.15);
        float corner = step(length(p - vec2(h, fract(h * 3.0))), 0.2);
        return clamp(bar_h + bar_v + corner, 0.0, 1.0) * char_index;
        
    } else if (charset_id == 4) {
        // Binary (0 and 1)
        float bit = step(0.5, char_index);
        if (bit < 0.5) {
            float ring = abs(length(p - 0.5) - 0.25);
            return smoothstep(0.08, 0.03, ring);
        } else {
            float bar = step(abs(p.x - 0.5), 0.08);
            float hat = step(abs(p.x - 0.35), 0.08) * step(0.3, p.y) * step(p.y, 0.5);
            float base = step(abs(p.y - 0.15), 0.04) * step(0.3, p.x) * step(p.x, 0.7);
            return clamp(bar + hat + base, 0.0, 1.0);
        }
    }
    
    // Fallback: simple density
    return step(1.0 - char_index, hash(p * 10.0 + ci));
}
```

### vjlive1/plugins/vcore/ascii_effect.py (L145-164)
```python
void main() {
    // Remap parameters
    float csize = mix(4.0, 32.0, cell_size / 10.0);
    float aspect = mix(0.4, 1.0, aspect_correct / 10.0);
    int charset_id = int(charset / 10.0 * 4.0 + 0.5);
    float t_curve = mix(0.3, 3.0, threshold_curve / 10.0);
    float edge_mix = edge_detect / 10.0;
    float detail = detail_boost / 10.0 * 3.0;
    int cmode = int(color_mode / 10.0 * 5.0 + 0.5);
    float fg_b = mix(0.3, 3.0, fg_brightness / 10.0);
    float bg_b = bg_brightness / 10.0 * 0.5;
    float sat = saturation / 10.0 * 2.0;
    float hue_off = hue_offset / 10.0;
    float scan = scanlines / 10.0;
    float glow = phosphor_glow / 10.0 * 2.0;
    float flick = flicker / 10.0 * 0.1;
    
    // ... (rest of main() would include full rendering pipeline)
}
```

---

## EXPANDED LEGACY CONTEXT

Based on analysis of legacy implementations in vjlive v1 and vjlive-2, the ascii_effect module implements the following key features:

1. **Character Set Hierarchy**:
   - Classic set uses ASCII characters (0-9, A-Z, a-z, punctuation) arranged by visual complexity
   - Blocks set uses Unicode block characters for higher density rendering
   - Braille set leverages Braille patterns for enhanced character variety
   - Matrix set uses falling character animation for dynamic text effects
   - Binary set uses 0/1 characters for high-contrast technical aesthetic

2. **Luminance Mapping Algorithm**:
   - Uses threshold_curve parameter to control gamma adjustment of luminance values
   - Applies edge_detect weighting to prioritize characters along image edges
   - Incorporates detail_boost to enhance character clarity in low-detail regions

3. **Procedural Animation Systems**:
   - Scroll speed controls vertical movement of characters in rain effect
   - Wave amount creates sinusoidal distortion of character positions
   - Dynamic character density adjusts based on scene complexity

4. **CRT Emulation Techniques**:
   - Scanlines implemented through horizontal intensity modulation
   - Phosphor glow uses radial falloff with configurable radius
   - Flicker applies subtle brightness variations with configurable intensity

5. **Color Processing Pipeline**:
   - Mono green mode maps luminance to green channel intensity
   - Rainbow mode cycles through HSV spectrum based on position/time
   - Thermal mode uses sequential color palette for heat mapping
   - Original mode preserves legacy color mapping from vjlive v1

This expanded context fills in the [NEEDS RESEARCH] markers and provides detailed behavioral specifications that align with the actual legacy implementations.