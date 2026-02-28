# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT001_ASCII_Effect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT001 — ASCII Effect

## Description

The ASCII Effect transforms video into living typography, rendering frames as ASCII characters on a grid. It uses procedural character generation (no texture atlas needed) to map luminance values to character patterns, creating a retro terminal aesthetic. The effect supports multiple character sets, color modes, CRT phosphor simulation, and Matrix-style falling rain animation. This effect is perfect for VJ performances that want to evoke the visual language of early computers, terminals, or glitch art.

This effect is ideal for creating retro-futuristic visuals, hacker aesthetics, or simply adding a layer of digital texture to video. The procedural character rendering ensures crisp, scalable ASCII without font dependencies.

## What This Module Does

- Renders video as ASCII characters on a configurable grid
- Supports 6 character sets: classic ASCII, blocks, braille, matrix, binary, custom
- Maps luminance to character density/pattern
- Applies color modes: mono green, amber, original, hue shift, rainbow, thermal
- Simulates CRT effects: scanlines, phosphor glow, flicker, barrel distortion, noise
- Animates with Matrix rain, character jitter, wave distortion
- Uses procedural character rendering (no texture atlas)
- Fully GPU-accelerated with real-time performance

## What This Module Does NOT Do

- Does NOT use actual font textures (procedural only)
- Does NOT support custom character sets beyond the 6 built-in
- Does NOT provide accurate text rendering (artistic approximation)
- Does NOT include OCR or text recognition
- Does NOT output actual ASCII text files (visual effect only)
- Does NOT support variable-width fonts (fixed grid)

---

## Detailed Behavior

### ASCII Rendering Pipeline

1. **Grid setup**: Divide screen into cells based on `cell_size` and `aspect_correct`
2. **Sample source**: For each cell, sample the source video at cell center
3. **Compute luminance**: Convert to grayscale using Rec. 709 weights
4. **Apply edge detection** (optional): Enhance luminance with edge information
5. **Apply threshold curve**: Gamma-like adjustment to luminance mapping
6. **Apply detail boost**: Enhance local contrast for better character mapping
7. **Select character**: Map luminance (0-1) to character index (0-10) based on charset
8. **Render character**: Procedurally draw character pattern in cell
9. **Apply color**: Based on `color_mode` and source color
10. **Apply CRT effects**: Scanlines, glow, flicker, curvature, noise
11. **Apply animation**: Matrix rain, jitter, wave distortion
12. **Composite**: Blend foreground (character) with background

### Grid and Cell Structure

The screen is divided into a grid of cells. Each cell is `cell_size` pixels wide and `cell_size / aspect_correct` pixels tall. The aspect correction allows characters to be rendered with proper proportions (typically characters are taller than wide).

```glsl
float csize = mix(4.0, 32.0, cell_size / 10.0);  // 4-32 pixels per char
float aspect = mix(0.4, 1.0, aspect_correct / 10.0);  // 0.4-1.0 char aspect

vec2 cell_px = vec2(csize, csize / aspect);
vec2 grid_pos = floor(cuv * resolution / cell_px);
vec2 cell_uv = fract(cuv * resolution / cell_px);
vec2 cell_center = (grid_pos + 0.5) * cell_px / resolution;
```

### Character Selection

The luminance of the source pixel determines which character to render. The luminance is mapped to a character index (0-10) representing 10 density levels. Different charsets interpret these levels differently:

- **Charset 0 (classic)**: " .:-=+*#%@" — density from dot to full block
- **Charset 1 (blocks)**: Various block elements (quarter, half, full)
- **Charset 2 (braille)**: Braille patterns for high-resolution feel
- **Charset 3 (matrix)**: Katakana-like characters for Matrix effect
- **Charset 4 (binary)**: 0 and 1 based on threshold
- **Charset 5 (custom)**: User-defined patterns (future)

```glsl
int charset_id = int(charset / 10.0 * 4.0 + 0.5);
float char_idx = luma;  // 0-1 mapped to 0-10 levels

if (jitter > 0.0) {
    // Randomly replace character with random pattern
    float j = hash3(vec3(grid_pos, floor(time * 10.0)));
    if (j < jitter * 0.3) {
        char_idx = hash(grid_pos + floor(time * 5.0));
    }
}
```

### Procedural Character Rendering

Characters are rendered using mathematical patterns, not textures. The `render_char()` function draws shapes based on the character index and charset:

```glsl
float render_char(vec2 local_uv, float char_index, int charset_id) {
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;  // 0-1 within cell

    if (charset_id == 0) {
        // Classic ASCII density
        float density = ci / 10.0;
        if (density < 0.1) return 0.0;  // space
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);  // dot
        }
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) +
                          step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);  // cross
        }
        // Grid pattern for high density
        float fill = density;
        float grid = step(fract(p.x * 3.0), fill) * step(fract(p.y * 3.0), fill);
        return grid * density;
    }
    // ... other charsets
}
```

### Color Modes

The effect supports multiple color schemes:

- **Mode 0 (mono_green)**: Classic terminal green on black
- **Mode 1 (mono_amber)**: Old terminal amber on black
- **Mode 2 (original)**: Source color with saturation/brightness control
- **Mode 3 (hue_shift)**: Source hue shifted by `hue_offset`
- **Mode 4 (rainbow)**: Position-based rainbow gradient
- **Mode 5 (thermal)**: Heatmap-style (blue→red) based on luminance

```glsl
if (cmode == 0) {
    fg_color = vec3(0.1, 1.0, 0.3) * fg_b;
    bg_color = vec3(0.0, bg_b * 0.3, 0.0);
} else if (cmode == 1) {
    fg_color = vec3(1.0, 0.7, 0.1) * fg_b;
    bg_color = vec3(bg_b * 0.3, bg_b * 0.2, 0.0);
} else if (cmode == 2) {
    vec3 hsv = rgb2hsv(src.rgb);
    hsv.y *= sat;
    hsv.z = fg_b;
    fg_color = hsv2rgb(hsv);
} else if (cmode == 3) {
    vec3 hsv = rgb2hsv(src.rgb);
    hsv.x = fract(hsv.x + hue_off);
    hsv.y = min(hsv.y * sat, 1.0);
    hsv.z = fg_b;
    fg_color = hsv2rgb(hsv);
} else if (cmode == 4) {
    float rainbow_hue = fract(hue_off + grid_pos.x / 40.0 + grid_pos.y / 60.0 + time * 0.05);
    fg_color = hsv2rgb(vec3(rainbow_hue, 0.9, fg_b));
} else {
    // Thermal mode
    float temp = luma;
    fg_color = vec3(
        smoothstep(0.3, 0.7, temp) * 2.0,
        smoothstep(0.5, 0.8, temp),
        smoothstep(0.0, 0.3, temp) * (1.0 - smoothstep(0.5, 0.9, temp))
    ) * fg_b;
}
```

### CRT Simulation

The effect includes several CRT monitor effects:

- **Scanlines**: Horizontal lines alternating brightness
- **Phosphor glow**: Bloom around characters
- **Flicker**: Random brightness variation
- **Curvature**: Barrel distortion to simulate curved CRT screen
- **Noise**: Static noise overlay

```glsl
// Curvature (barrel distortion)
if (curve > 0.0) {
    vec2 cc = cuv * 2.0 - 1.0;
    cc *= 1.0 + dot(cc, cc) * curve;
    cuv = cc * 0.5 + 0.5;
    if (cuv.x < 0.0 || cuv.x > 1.0 || cuv.y < 0.0 || cuv.y > 1.0) {
        fragColor = vec4(0.0);
        return;
    }
}

// Scanlines
if (scan > 0.0) {
    float sl = sin(cuv.y * resolution.y * 3.14159) * 0.5 + 0.5;
    color *= 1.0 - scan * (1.0 - sl) * 0.5;
}

// Phosphor glow
if (glow > 0.0) {
    vec2 tx = 1.0 / resolution;
    float glow_sum = 0.0;
    for (float dx = -1.0; dx <= 1.0; dx += 1.0) {
        for (float dy = -1.0; dy <= 1.0; dy += 1.0) {
            if (dx == 0.0 && dy == 0.0) continue;
            vec2 neighbor_center = cell_center + vec2(dx, dy) * cell_px / resolution;
            float n_luma = dot(texture(tex0, neighbor_center).rgb, vec3(0.299, 0.587, 0.114));
            glow_sum += pow(n_luma, t_curve) * 0.1;
        }
    }
    color += fg_color * glow_sum * glow;
}

// Flicker
if (flick > 0.0) {
    color *= 1.0 + (hash(vec2(time * 100.0, grid_pos.x)) - 0.5) * flick;
}

// Noise
if (noise_amt > 0.0) {
    float n = hash(cuv * resolution + time * 1000.0);
    color += (n - 0.5) * noise_amt;
}
```

### Matrix Rain Animation

The effect can simulate falling Matrix-style characters:

```glsl
float rain_alpha = 0.0;
if (rain > 0.0) {
    float column_hash = hash(vec2(grid_pos.x, 0.0));
    if (column_hash < rain) {
        float drop_pos = fract(time * scroll * 0.1 + column_hash * 10.0);
        float cell_y = grid_pos.y / (resolution.y / cell_px.y);
        float trail = smoothstep(drop_pos, drop_pos - 0.3, cell_y) * step(cell_y, drop_pos);
        rain_alpha = trail;
        char_idx = max(char_idx, hash3(vec3(grid_pos, floor(time * 8.0))) * trail);
    }
}

if (rain_alpha > 0.0) {
    fg_color = mix(fg_color, vec3(0.0, 1.0, 0.3) * fg_b, rain_alpha);
}
```

### Wave Distortion

The grid can be warped with sine waves:

```glsl
if (wave_a > 0.0) {
    cuv.x += sin(cuv.y * wave_f + time * 2.0) * wave_a;
    cuv.y += cos(cuv.x * wave_f * 0.7 + time * 1.5) * wave_a * 0.3;
}
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `cell_size` | float | 5.0 | 0-10 → 4-32 px | Character cell size (pixels) |
| `aspect_correct` | float | 7.0 | 0-10 → 0.4-1.0 | Character aspect ratio (1.0 = square) |
| `charset` | float | 0.0 | 0-10 → 0-5 | Character set ID (0=classic, 1=blocks, 2=braille, 3=matrix, 4=binary, 5=custom) |
| `threshold_curve` | float | 5.0 | 0-10 → 0.3-3.0 | Luminance gamma (lower = brighter chars) |
| `edge_detect` | float | 0.0 | 0-10 → 0-1 | Mix edge detection into luminance |
| `detail_boost` | float | 0.0 | 0-10 → 0-3 | Enhance local contrast |
| `color_mode` | float | 2.0 | 0-10 → 0-5 | Color mode (0=green, 1=amber, 2=original, 3=hue_shift, 4=rainbow, 5=thermal) |
| `fg_brightness` | float | 5.0 | 0-10 → 0.3-3.0 | Foreground (character) brightness |
| `bg_brightness` | float | 2.0 | 0-10 → 0-0.5 | Background brightness |
| `saturation` | float | 5.0 | 0-10 → 0-2.0 | Color saturation (for color modes) |
| `hue_offset` | float | 0.0 | 0-10 → 0-1 | Hue shift (for hue_shift mode) |
| `scanlines` | float | 3.0 | 0-10 → 0-1 | Scanline intensity |
| `phosphor_glow` | float | 2.0 | 0-10 → 0-2 | Character glow radius |
| `flicker` | float | 1.0 | 0-10 → 0-0.1 | Brightness flicker amount |
| `curvature` | float | 0.0 | 0-10 → 0-0.3 | CRT barrel distortion |
| `noise_amount` | float | 0.5 | 0-10 → 0-0.15 | Static noise intensity |
| `scroll_speed` | float | 0.0 | 0-10 → -5 to 5 | Matrix rain scroll speed |
| `rain_density` | float | 0.0 | 0-10 → 0-1 | Matrix rain density |
| `char_jitter` | float | 0.0 | 0-10 → 0-1 | Random character changes |
| `wave_amount` | float | 0.0 | 0-10 → 0-0.5 | Wave distortion amplitude |
| `wave_freq` | float | 5.0 | 0-10 → 1-20 | Wave distortion frequency |

**Inherited from Effect**: `u_mix`

---

## Public Interface

```python
class ASCIIEffect(Effect):
    def __init__(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input RGB frame (HxWxC, 0-255) |
| **Output** | `np.ndarray` | ASCII-rendered frame (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_parameters: dict` — Effect parameters (20+ controls)
- `_shader: ShaderProgram` — Compiled shader
- `_texture: int` — Input frame texture

**Per-Frame:**
- Upload input frame to texture
- Set all shader uniforms
- Render full-screen quad
- Read output or blit to screen

**Initialization:**
- Compile shader from `ASCII_EFFECT_FRAGMENT`
- Create input texture
- Initialize parameters to defaults
- Allocate texture at frame size

**Cleanup:**
- Delete texture
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Shader program | GLSL | vertex + fragment | N/A | Init once |
| Input texture | GL_TEXTURE_2D | GL_RGBA8 | frame size | Per-frame update |

**Memory Budget (1920×1080):**
- Shader: ~50-80 KB
- Texture: ~8.3 MB
- Total: ~8.4 MB (light)

**Memory Budget (640×480):**
- Texture: ~1.2 MB
- Total: ~1.3 MB (light)

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Shader compilation fails | `ShaderCompilationError` | Log error, abort |
| Texture creation fails | `RuntimeError` | Reduce resolution or abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Uniform not found | `KeyError` or ignore | Verify shader/parameter names match |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations must occur on the thread with the OpenGL context. The effect updates the input texture each frame; concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (1920×1080):**
- Texture upload: ~2-4 ms
- Shader execution (grid + char render): ~5-10 ms
- Total: ~7-14 ms (70-140 fps) on mid-range GPU

**Expected Frame Time (640×480):**
- Total: ~2-4 ms (250-500 fps)

**Optimization Strategies:**
- Increase `cell_size` (fewer cells = less work)
- Disable expensive effects (glow, scanlines, curvature)
- Reduce resolution
- Use simpler charset (binary is fastest)

---

## Integration Checklist

- [ ] Shader compiled successfully
- [ ] Input texture created
- [ ] Parameters configured
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_cell_size` | Cell size affects grid resolution |
| `test_aspect_ratio` | Aspect correction changes cell shape |
| `test_charset` | Different charsets render different patterns |
| `test_threshold_curve` | Gamma affects character density |
| `test_edge_detect` | Edge detection enhances edges |
| `test_color_modes` | All 6 color modes produce expected colors |
| `test_crt_scanlines` | Scanlines render correctly |
| `test_crt_glow` | Phosphor glow adds bloom |
| `test_crt_flicker` | Flicker adds noise |
| `test_crt_curvature` | Barrel distortion warps image |
| `test_matrix_rain` | Rain animation works |
| `test_char_jitter` | Jitter randomizes characters |
| `test_wave_distortion` | Wave distortion warps grid |
| `test_cleanup` | All resources released |
| `test_no_memory_leak` | Repeated init/cleanup cycles don't leak |

**Minimum coverage:** 85%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-EXT001: ascii_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `core/effects/ascii.py` — VJLive Original implementation
- `plugins/vcore/ascii_effect.py` — VJLive-2 implementation

Design decisions inherited:
- Effect name: `ascii` or `ASCII Effect`
- Procedural character rendering (no texture atlas)
- 6 character sets (classic, blocks, braille, matrix, binary, custom)
- 6 color modes (mono_green, mono_amber, original, hue_shift, rainbow, thermal)
- CRT effects: scanlines, phosphor_glow, flicker, curvature, noise
- Animation: scroll_speed, rain_density, char_jitter, wave_amount, wave_freq
- Parameters all use 0-10 range with internal mapping
- Shader uses `render_char()` function for each charset
- Presets: "terminal_green", "matrix_rain", "retro_amber", "binary_code", "thermal_vision", "crt_curved"

---

## Notes for Implementers

1. **Core Concept**: This effect converts video into ASCII art by dividing the screen into a grid, sampling the source color/luminance at each cell, and rendering a procedural character whose density matches the luminance.

2. **Procedural Characters**: Instead of using font textures, characters are drawn using mathematical patterns (circles, crosses, grids). This makes the effect resolution-independent and avoids font dependencies.

3. **Character Sets**: Each charset defines 10 density levels (0-9). The luminance of the source pixel selects which density level to use. The `render_char()` function draws the corresponding pattern.

4. **Color Modes**: The effect can color characters based on source color, fixed colors (green/amber), or position-based gradients (rainbow, thermal).

5. **CRT Simulation**: The effect includes several post-processing steps to simulate old CRT monitors: scanlines (horizontal lines), phosphor glow (bloom), flicker (random brightness), curvature (barrel distortion), and noise (static).

6. **Matrix Rain**: The `rain_density` and `scroll_speed` parameters create falling columns of characters, mimicking the Matrix movie's "digital rain" effect.

7. **Parameter Scaling**: Most parameters are 0-10 sliders that map to internal ranges. For example, `cell_size` maps 0-10 to 4-32 pixels. Check the spec table for exact mappings.

8. **Shader Uniforms**:
   ```glsl
   uniform sampler2D tex0;
   uniform float time;
   uniform vec2 resolution;
   uniform float u_mix;
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

9. **Performance**: The shader is relatively lightweight. The main cost is the per-cell texture sampling and character rendering. Increasing `cell_size` (fewer cells) improves performance.

10. **PRESETS**:
    ```python
    PRESETS = {
        "terminal_green": {
            "cell_size": 6.0, "aspect_correct": 7.0, "charset": 0,
            "color_mode": 0, "fg_brightness": 8.0, "bg_brightness": 2.0,
            "scanlines": 5.0, "phosphor_glow": 3.0,
        },
        "matrix_rain": {
            "cell_size": 5.0, "aspect_correct": 8.0, "charset": 3,
            "color_mode": 0, "fg_brightness": 9.0, "bg_brightness": 1.0,
            "rain_density": 7.0, "scroll_speed": 3.0, "char_jitter": 2.0,
        },
        "retro_amber": {
            "cell_size": 7.0, "aspect_correct": 6.0, "charset": 0,
            "color_mode": 1, "fg_brightness": 7.0, "bg_brightness": 2.0,
            "scanlines": 4.0, "phosphor_glow": 2.0, "flicker": 2.0,
        },
        "binary_code": {
            "cell_size": 8.0, "aspect_correct": 7.0, "charset": 4,
            "color_mode": 0, "fg_brightness": 8.0, "bg_brightness": 3.0,
            "char_jitter": 5.0,
        },
        "thermal_vision": {
            "cell_size": 6.0, "aspect_correct": 7.0, "charset": 0,
            "color_mode": 5, "fg_brightness": 8.0, "bg_brightness": 1.0,
            "threshold_curve": 3.0,
        },
        "crt_curved": {
            "cell_size": 5.0, "aspect_correct": 7.0, "charset": 1,
            "color_mode": 2, "curvature": 5.0, "scanlines": 7.0,
            "phosphor_glow": 4.0, "flicker": 3.0, "noise_amount": 2.0,
        },
    }
    ```

11. **Testing Strategy**:
    - Test with solid color frames: verify character density matches luminance
    - Test edge detection: edges should have more/different characters
    - Test all charsets: each should produce distinct patterns
    - Test all color modes: verify color output
    - Test CRT effects individually: scanlines, glow, flicker, curvature, noise
    - Test Matrix rain: characters should fall
    - Test wave distortion: grid should warp
    - Test performance: measure FPS at different resolutions and cell sizes

12. **Future Extensions**:
    - Add custom character set via texture atlas
    - Add dithering to simulate lower bit depth
    - Add character set animation (morphing between sets)
    - Add per-cell random seed for more variation
    - Add audio reactivity (character size/color reacts to audio)

---

## Easter Egg Idea

When `cell_size` is set exactly to 6.66, `aspect_correct` to exactly 6.66, `charset` to exactly 6.66 (which rounds to charset ID 4, binary), `threshold_curve` to exactly 6.66, `edge_detect` to exactly 6.66, `detail_boost` to exactly 6.66, `color_mode` to exactly 6.66 (which rounds to mode 4, rainbow), `fg_brightness` to exactly 6.66, `bg_brightness` to exactly 6.66, `saturation` to exactly 6.66, `hue_offset` to exactly 6.66, `scanlines` to exactly 6.66, `phosphor_glow` to exactly 6.66, `flicker` to exactly 6.66, `curvature` to exactly 6.66, `noise_amount` to exactly 6.66, `scroll_speed` to exactly 6.66, `rain_density` to exactly 6.66, `char_jitter` to exactly 6.66, `wave_amount` to exactly 6.66, and `wave_freq` to exactly 6.66, the ASCII effect enters a "sacred terminal" state where each character cell becomes exactly 6.66×6.66 pixels, the aspect ratio becomes exactly 6.66, the character density curve becomes exactly 666% more sensitive, the edge detection finds exactly 666 edges per frame, the detail boost creates exactly 666 levels of contrast, the rainbow hue cycles exactly 666 times per second, the scanlines appear exactly 666 times per character, the phosphor glow extends exactly 6.66 characters, the flicker oscillates at exactly 666 Hz, the barrel distortion creates exactly 6.66 units of curvature, the static noise contains exactly 666 random seeds per frame, the Matrix rain falls at exactly 666 characters per second, the character jitter randomizes exactly 666% of characters, the wave distortion has exactly 6.66 wavelengths across the screen, and the entire effect becomes a "digital prayer" where every pixel is exactly 666% more ASCII than normal, creating a perfect 666×666 grid of sacred typography that can only be read by achieving exactly 666 Hz brainwave resonance.

---

## References

- ASCII art: https://en.wikipedia.org/wiki/ASCII_art
- CRT simulation: https://en.wikipedia.org/wiki/Cathode-ray_tube
- Matrix digital rain: https://en.wikipedia.org/wiki/Matrix_digital_rain
- Procedural texture generation: https://en.wikipedia.org/wiki/Procedural_texture
- VJLive legacy: `core/effects/ascii.py`, `plugins/vcore/ascii_effect.py`

---

## Implementation Tips

1. **Full Shader**:
   The shader is already provided in the legacy code. It's ~300 lines. Key sections:
   - Uniform declarations (all parameters)
   - Helper functions: `hash()`, `hash3()`, `rgb2hsv()`, `hsv2rgb()`, `render_char()`
   - `main()`: grid setup, cell sampling, character selection, color application, CRT effects, animation

2. **Python Implementation**:
   ```python
   class ASCIIEffect(Effect):
       def __init__(self):
           super().__init__("ASCII", ASCII_EFFECT_FRAGMENT)
           
           self.parameters = {
               'cell_size': 5.0,
               'aspect_correct': 7.0,
               'charset': 0.0,
               'threshold_curve': 5.0,
               'edge_detect': 0.0,
               'detail_boost': 0.0,
               'color_mode': 2.0,
               'fg_brightness': 5.0,
               'bg_brightness': 2.0,
               'saturation': 5.0,
               'hue_offset': 0.0,
               'scanlines': 3.0,
               'phosphor_glow': 2.0,
               'flicker': 1.0,
               'curvature': 0.0,
               'noise_amount': 0.5,
               'scroll_speed': 0.0,
               'rain_density': 0.0,
               'char_jitter': 0.0,
               'wave_amount': 0.0,
               'wave_freq': 5.0,
           }
       
       def process_frame(self, frame):
           h, w = frame.shape[:2]
           
           # Upload frame to texture
           glActiveTexture(GL_TEXTURE0)
           glBindTexture(GL_TEXTURE_2D, self.texture)
           glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, frame)
           
           # Set uniforms
           self.apply_uniforms(time, (w, h))
           
           # Render
           self._render_fullscreen_quad()
           
           # Read result or return texture
           result = self._read_pixels(w, h)
           return result
       
       def apply_uniforms(self, time, resolution, audio_reactor=None):
           super().apply_uniforms(time, resolution, audio_reactor)
           
           # Set all parameters with scaling
           p = self.parameters
           self.shader.set_uniform('cell_size', p['cell_size'])
           self.shader.set_uniform('aspect_correct', p['aspect_correct'])
           self.shader.set_uniform('charset', p['charset'])
           self.shader.set_uniform('threshold_curve', mix(0.3, 3.0, p['threshold_curve'] / 10.0))
           self.shader.set_uniform('edge_detect', p['edge_detect'] / 10.0)
           self.shader.set_uniform('detail_boost', p['detail_boost'] / 10.0 * 3.0)
           self.shader.set_uniform('color_mode', p['color_mode'])
           self.shader.set_uniform('fg_brightness', mix(0.3, 3.0, p['fg_brightness'] / 10.0))
           self.shader.set_uniform('bg_brightness', p['bg_brightness'] / 10.0 * 0.5)
           self.shader.set_uniform('saturation', p['saturation'] / 10.0 * 2.0)
           self.shader.set_uniform('hue_offset', p['hue_offset'] / 10.0)
           self.shader.set_uniform('scanlines', p['scanlines'] / 10.0)
           self.shader.set_uniform('phosphor_glow', p['phosphor_glow'] / 10.0 * 2.0)
           self.shader.set_uniform('flicker', p['flicker'] / 10.0 * 0.1)
           self.shader.set_uniform('curvature', p['curvature'] / 10.0 * 0.3)
           self.shader.set_uniform('noise_amount', p['noise_amount'] / 10.0 * 0.15)
           self.shader.set_uniform('scroll_speed', (p['scroll_speed'] / 10.0 - 0.5) * 10.0)
           self.shader.set_uniform('rain_density', p['rain_density'] / 10.0)
           self.shader.set_uniform('char_jitter', p['char_jitter'] / 10.0)
           self.shader.set_uniform('wave_amount', p['wave_amount'] / 10.0 * 0.5)
           self.shader.set_uniform('wave_freq', mix(1.0, 20.0, p['wave_freq'] / 10.0))
   ```

3. **Helper Functions**: The shader uses `mix()` for range mapping. In Python, use:
   ```python
   def mix(a, b, t):
       return a + (b - a) * t
   ```

4. **Character Sets**: The legacy code implements charsets 0-4. Charset 5 (custom) is not implemented. You can either:
   - Implement charset 5 as a placeholder (returns 0)
   - Add a texture atlas parameter for custom characters
   - Use a procedural pattern based on a seed

5. **Edge Detection**: The shader computes simple Sobel-like edge detection by sampling neighboring cells. This is optional but adds detail to edges.

6. **CRT Curvature**: The barrel distortion can push UVs outside [0,1], which are then discarded (black border). Ensure your framebuffer has black background or handle edge clamping.

7. **Performance Tips**:
   - The shader does many texture fetches per cell (especially with edge detection, glow, etc.)
   - Consider reducing `cell_size` for performance (fewer cells = fewer fetches)
   - Glow effect samples 8 neighbors; disable if too expensive
   - Curvature adds minimal cost; scanlines and flicker are cheap

8. **Testing**: Use a gradient image to verify character density mapping. Use a checkerboard to verify edge detection. Use a solid color to test color modes.

9. **Audio Reactivity**: The effect doesn't currently use audio, but you could modulate parameters like `char_jitter`, `wave_amount`, or `rain_density` with audio features.

10. **Future Work**:
    - Add support for custom character textures
    - Add dithering to simulate lower bit depth
    - Add character set blending (morph between sets)
    - Add per-cell random seed for more organic variation

---

## Conclusion

The ASCII Effect is a classic retro visual that transforms video into living typography. With its procedural character rendering, multiple character sets and color modes, CRT simulation, and Matrix rain animation, it offers a wide range of stylized visuals perfect for VJ performances. The effect is lightweight, fully GPU-accelerated, and produces authentic-looking ASCII art without font dependencies.

---
>>>>>>> REPLACE