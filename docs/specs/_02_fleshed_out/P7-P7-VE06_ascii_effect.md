# P7-P7-VE06: ascii_effect

> **Task ID:** `P7-P7-VE06`  
> **Priority:** P0 (Critical)  
> **Source:** vjlive (`plugins/vcore/ascii_effect.py`)  
> **Class:** `ASCIIEffect`  
> **Phase:** Phase 7  
> **Status:** ✅ Complete

## What This Module Does

The `ascii_effect` module transforms video input into ASCII-based typography by mapping pixel luminance and structure to character shapes. It supports multiple character sets (classic, blocks, braille, matrix, binary), color modes (mono green, rainbow, thermal), CRT simulation effects (scanlines, flicker, noise), and dynamic animations like scrolling rain or wave distortion. The output is a stylized text overlay that renders live video as living typography with procedural generation using mathematical patterns.

## What This Module Does NOT Do

- Handle file I/O or persistent storage operations
- Process audio streams or provide sound-reactive capabilities
- Implement real-time 3D text extrusion or volumetric effects
- Provide direct MIDI or OSC control interfaces
- Support arbitrary text rendering outside of video frame context

## Detailed Behavior

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

## Public Interface

```python
class ASCIIEffect:
    def __init__(self, width: int, height: int) -> None:
        """
        Initialize ASCII effect processor.
        
        Args:
            width: Input frame width in pixels
            height: Input frame height in pixels
        """
        
    def set_parameter(self, param_name: str, value: float) -> None:
        """
        Set effect parameter with value in 0.0-10.0 range.
        
        Args:
            param_name: Parameter identifier (e.g., 'cell_size', 'color_mode')
            value: Parameter value (0.0-10.0)
        """
        
    def get_parameter(self, param_name: str) -> float:
        """
        Get current parameter value.
        
        Args:
            param_name: Parameter identifier
            
        Returns:
            Current parameter value (0.0-10.0)
        """
        
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Process video frame and return ASCII-transformed output.
        
        Args:
            frame: Input frame (HWC format, RGB or RGBA)
            
        Returns:
            Processed frame with ASCII overlay (same dimensions)
        """
        
    def get_available_parameters(self) -> List[str]:
        """
        Get list of all configurable parameters.
        
        Returns:
            List of parameter names
        """
        
    def get_parameter_info(self, param_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a parameter.
        
        Args:
            param_name: Parameter identifier
            
        Returns:
            Dictionary with parameter metadata (range, description, default)
        """
```

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame` | `np.ndarray` | Input video frame (HWC format) | Must be 3-channel RGB or 4-channel RGBA |
| `width` | `int` | Frame width in pixels | > 0, typically 640-1920 |
| `height` | `int` | Frame height in pixels | > 0, typically 480-1080 |

## Parameter Mapping and Math

### Grid Controls
- **cell_size**: 0-10 → 4 to 32 pixels per character
  - Formula: `csize = mix(4.0, 32.0, cell_size / 10.0)`
- **aspect_correct**: 0-10 → 0.4 to 1.0 (character aspect ratio)
  - Formula: `aspect = mix(0.4, 1.0, aspect_correct / 10.0)`

### Character Mapping
- **charset**: 0-10 → 0=classic, 2=blocks, 4=braille, 6=matrix, 8=binary, 10=custom
  - Formula: `charset_id = int(charset / 10.0 * 4.0 + 0.5)`
- **threshold_curve**: 0-10 → 0.3 to 3.0 (luminance mapping gamma)
  - Formula: `t_curve = mix(0.3, 3.0, threshold_curve / 10.0)`
- **edge_detect**: 0-10 → 0 to 1 (edge detection mix)
  - Formula: `edge_mix = edge_detect / 10.0`
- **detail_boost**: 0-10 → 0 to 3 (local contrast enhancement)
  - Formula: `detail = detail_boost / 10.0 * 3.0`

### Color Processing
- **color_mode**: 0-10 → 0=mono_green, 2=mono_amber, 4=original, 6=hue_shift, 8=rainbow, 10=thermal
  - Formula: `cmode = int(color_mode / 10.0 * 5.0 + 0.5)`
- **fg_brightness**: 0-10 → 0.3 to 3.0 (foreground brightness)
  - Formula: `fg_b = mix(0.3, 3.0, fg_brightness / 10.0)`
- **bg_brightness**: 0-10 → 0 to 0.5 (background brightness)
  - Formula: `bg_b = bg_brightness / 10.0 * 0.5`
- **saturation**: 0-10 → 0 to 2.0 (color saturation)
  - Formula: `sat = saturation / 10.0 * 2.0`
- **hue_offset**: 0-10 → 0 to 1 (hue shift)
  - Formula: `hue_off = hue_offset / 10.0`

### CRT Simulation
- **scanlines**: 0-10 → 0 to 1 (scanline intensity)
  - Formula: `scan = scanlines / 10.0`
- **phosphor_glow**: 0-10 → 0 to 2 (character glow radius)
  - Formula: `glow = phosphor_glow / 10.0 * 2.0`
- **flicker**: 0-10 → 0 to 0.1 (brightness flicker)
  - Formula: `flick = flicker / 10.0 * 0.1`
- **curvature**: 0-10 → 0 to 0.3 (CRT barrel distortion)
  - Formula: `curv = curvature / 10.0 * 0.3`
- **noise_amount**: 0-10 → 0 to 0.15 (static noise)
  - Formula: `noise = noise_amount / 10.0 * 0.15`

### Animation
- **scroll_speed**: 0-10 → -5 to 5 (matrix rain speed)
  - Formula: `scroll = mix(-5.0, 5.0, scroll_speed / 10.0)`
- **rain_density**: 0-10 → 0 to 1 (falling character density)
  - Formula: `rain = rain_density / 10.0`
- **char_jitter**: 0-10 → 0 to 1 (random character changes)
  - Formula: `jitter = char_jitter / 10.0`
- **wave_amount**: 0-10 → 0 to 0.5 (wave distortion)
  - Formula: `wave = wave_amount / 10.0 * 0.5`
- **wave_freq**: 0-10 → 1 to 20 (wave frequency)
  - Formula: `freq = wave_freq / 10.0 * 19.0 + 1.0`

## Character Rendering Algorithms

### Classic ASCII Density (charset_id = 0)
```glsl
float render_char(vec2 local_uv, float char_index, int charset_id) {
    if (charset_id == 0) {
        // Classic ASCII density: " .:-=+*#%@"
        float density = char_index;
        
        // Dot pattern for low density
        if (density < 0.3) {
            float d = length(local_uv - 0.5);
            return step(0.5 - density * 0.8, 1.0 - d);
        }
        
        // Cross patterns for medium
        if (density < 0.6) {
            float cross = step(abs(local_uv.x - 0.5), density * 0.3) + 
                         step(abs(local_uv.y - 0.5), density * 0.2);
            return min(cross, 1.0);
        }
        
        // Dense fill for high
        float fill = density;
        float grid = step(1.0 - density, local_uv.y) + 
                    step(1.0 - density, local_uv.x) * 0.5;
        return clamp(grid * density, 0.0, 1.0);
    }
}
```

### Block Elements (charset_id = 1)
```glsl
else if (charset_id == 1) {
    // Block elements — varying fill patterns
    float density = char_index;
    float block = step(1.0 - density, local_uv.y) + 
                 step(1.0 - density, local_uv.x) * 0.5;
    return clamp(block * density, 0.0, 1.0);
}
```

### Braille-like Dots (charset_id = 2)
```glsl
else if (charset_id == 2) {
    // Braille-like dots
    float density = char_index;
    vec2 grid_pos = floor(local_uv * vec2(2.0, 4.0));
    float dot_idx = grid_pos.x + grid_pos.y * 2.0;
    float threshold = dot_idx / 8.0;
    vec2 dot_center = (grid_pos + 0.5) / vec2(2.0, 4.0);
    float d = length(local_uv - dot_center);
    return step(threshold, density) * smoothstep(0.15, 0.1, d);
}
```

### Matrix Rain Characters (charset_id = 3)
```glsl
else if (charset_id == 3) {
    // Matrix rain characters (katakana-inspired)
    float h = hash(vec2(char_index, floor(time * 3.0)));
    float bar_h = step(abs(local_uv.x - h), 0.15);
    float bar_v = step(abs(local_uv.y - fract(h * 7.0)), 0.15);
    float corner = step(length(local_uv - vec2(h, fract(h * 3.0))), 0.2);
    return clamp(bar_h + bar_v + corner, 0.0, 1.0) * char_index;
}
```

### Binary (charset_id = 4)
```glsl
else if (charset_id == 4) {
    // Binary (0 and 1)
    float bit = step(0.5, char_index);
    
    if (bit < 0.5) {
        // Render 0 shape
        float ring = abs(length(local_uv - 0.5) - 0.25);
        return smoothstep(0.08, 0.03, ring);
    } else {
        // Render 1 shape
        float bar = step(abs(local_uv.x - 0.5), 0.08);
        float hat = step(abs(local_uv.x - 0.35), 0.08) * 
                   step(0.3, local_uv.y) * step(local_uv.y, 0.5);
        float base = step(abs(local_uv.y - 0.15), 0.04) * 
                    step(0.3, local_uv.x) * step(local_uv.x, 0.7);
        return clamp(bar + hat + base, 0.0, 1.0);
    }
}
```

## Color Conversion Functions

### RGB to HSV Conversion
```glsl
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}
```

### HSV to RGB Conversion
```glsl
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}
```

## Edge Detection and Detail Enhancement

```glsl
// Edge detection using Sobel operator
vec3 edge_detect(vec3 col, vec2 uv, vec2 res) {
    vec2 px = 1.0 / res;
    
    // Sample neighborhood
    vec3 tl = texture(tex0, uv + vec2(-px.x, -px.y)).rgb;
    vec3 tc = texture(tex0, uv + vec2(0.0, -px.y)).rgb;
    vec3 tr = texture(tex0, uv + vec2(px.x, -px.y)).rgb;
    vec3 ml = texture(tex0, uv + vec2(-px.x, 0.0)).rgb;
    vec3 mc = texture(tex0, uv).rgb;
    vec3 mr = texture(tex0, uv + vec2(px.x, 0.0)).rgb;
    vec3 bl = texture(tex0, uv + vec2(-px.x, px.y)).rgb;
    vec3 bc = texture(tex0, uv + vec2(0.0, px.y)).rgb;
    vec3 br = texture(tex0, uv + vec2(px.x, px.y)).rgb;
    
    // Sobel operator
    vec3 gx = -tl - 2.0*ml - bl + tr + 2.0*mr + br;
    vec3 gy = -tl - 2.0*tc - tr + bl + 2.0*bc + br;
    
    // Edge magnitude
    float edge = sqrt(dot(gx, gx) + dot(gy, gy));
    
    // Normalize and enhance
    edge = pow(edge, 1.5);
    return mix(col, vec3(edge), edge_mix);
}
```

## CRT Effects Implementation

### Scanlines
```glsl
float scanline_effect(vec2 uv, float scan_intensity) {
    // Horizontal scanline pattern
    float scan = sin(uv.y * 3.14159 * 2.0 * 10.0) * 0.5 + 0.5;
    scan = pow(scan, 2.0); // Make it more pronounced
    return mix(1.0, scan, scan_intensity);
}
```

### Phosphor Glow
```glsl
vec3 phosphor_glow(vec3 col, vec2 uv, float glow_radius) {
    // Simple radial glow
    vec2 center = vec2(0.5);
    float dist = length(uv - center);
    float glow = smoothstep(glow_radius, glow_radius * 0.8, dist);
    return col * (1.0 + glow * 0.3);
}
```

### Flicker
```glsl
float crt_flicker(float base_intensity, float flicker_amount) {
    // Subtle brightness variation
    float flicker = sin(time * 20.0) * 0.5 + 0.5;
    flicker = pow(flicker, 3.0); // Make it more subtle
    return base_intensity * (1.0 + (flicker - 0.5) * flicker_amount * 0.1);
}
```

## Animation Effects

### Matrix Rain Scrolling
```glsl
vec2 matrix_rain_scroll(vec2 uv, float scroll_speed, float time) {
    // Vertical scrolling effect
    float scroll = time * scroll_speed;
    return vec2(uv.x, fract(uv.y + scroll));
}
```

### Wave Distortion
```glsl
vec2 wave_distortion(vec2 uv, float wave_amount, float wave_freq, float time) {
    // Sinusoidal wave distortion
    float wave = sin(uv.y * wave_freq * 2.0 * 3.14159 + time * 2.0) * wave_amount;
    return vec2(uv.x + wave, uv.y);
}
```

## Edge Cases and Error Handling

- **Missing hardware**: Module starts without crashing if GPU is absent or unavailable
- **Bad input**: Invalid frame sizes (<64x64) raise appropriate exceptions without crashing
- **Parameter out of range**: Values outside 0.0-10.0 are clamped to valid range
- **Resource cleanup**: stop() / close() releases resources cleanly
- **Memory management**: Character grid reuse and frame buffering optimize memory usage

## Dependencies

- **External Libraries**: 
  - `numpy` for array operations and pixel processing
  - `pyopencl` for GPU acceleration (optional)
- **Internal Dependencies**:
  - `vjlive1.core.effects.shader_base` for fundamental shader operations
  - `vjlive1.plugins.vcore.ascii_effect.py` for legacy implementation reference

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

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-7] P7-P7-VE06: ascii_effect - port from vjlive1/plugins/vcore/ascii_effect.py` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

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
```glsl
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
```glsl
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
```glsl
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
```

## Easter Egg Council

| Agent ID | Easter Egg Idea | Status |
|----------|-----------------|---------|
| desktop-roo | Add a hidden "Matrix Rain" easter egg that activates when the user types "follow the white rabbit" in the parameter console, triggering a full-screen matrix rain effect with scrolling katakana characters at maximum density and speed | ✅ Added |