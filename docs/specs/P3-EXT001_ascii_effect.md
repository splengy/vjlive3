# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT001_ascii_effect.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT001 — ascii_effect

**What This Module Does**  
The `ascii_effect` module transforms video input into ASCII-based typography by mapping pixel luminance and structure to character shapes. It supports multiple character sets (classic, blocks, braille, matrix, binary), color modes (mono green, rainbow, thermal), CRT simulation effects (scanlines, flicker, noise), and dynamic animations like scrolling rain or wave distortion. The output is a stylized text overlay that renders live video as living typography with procedural generation using mathematical patterns.

The module draws inspiration from legacy implementations in both vjlive v1 and vjlive-2, which used fragment shaders to map pixel data to character grids. The core algorithm analyzes luminance gradients and edge detection to determine optimal character placement, while procedural animations create dynamic text patterns that respond to video content.

**What This Module Does NOT Do**  
- Handle file I/O or persistent storage operations
- Process audio streams or provide sound-reactive capabilities
- Implement real-time 3D text extrusion or volumetric effects
- Provide direct MIDI or OSC control interfaces
- Support arbitrary text rendering outside of video frame context

**Detailed Behavior**  
The module processes video frames through several stages:
1. **Luminance Analysis**: Converts RGB input to grayscale and calculates luminance gradients
2. **Character Mapping**: Uses threshold curves and edge detection to select appropriate characters from configured character sets
3. **Procedural Animation**: Applies wave distortions, scrolling effects, and dynamic positioning based on parameters
4. **CRT Simulation**: Adds scanlines, phosphor glow, and flicker effects to emulate vintage display behavior
5. **Color Processing**: Applies color modes through HSV transformations or palette mapping

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

**Test Plan**  
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

### vjlive1/plugins/vcore/ascii_effect.py (L49-68)  
```

// --- Animation ---
uniform float scroll_speed;      // 0-10 → -5 to 5 (matrix rain speed)
uniform float rain_density;      // 0-10 → 0 to 1 (falling character density)
uniform float char_jitter;       // 0-10 → 0 to 1 (random character changes)
uniform float wave_amount;      // 0-10 → 0 to 0.5 (wave distortion)
uniform float wave_freq;         // 0-10 → 1 to 20 (wave frequency)

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

// Procedural character rendering using math (no texture atlas needed)
float render_char(vec2 local_uv, float char_index, int charset_id) {
    // Map character index (0-1) to patterns rendered procedurally
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;

    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = ci / 10.0;
        // Generate pattern based on density
        float pattern = 0.0;
        if (density < 0.1) return 0.0; // space

        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(p - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(p.x - 0.5), density * 0.3) + step(abs(p.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }

    else if (charset_id == 1) {
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
        // Render 0 or 1 shape
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

    // Procedural character rendering using math (no texture atlas needed)
    float ci = floor(char_index * 10.0);
    vec2