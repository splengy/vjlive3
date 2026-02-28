# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT211_ascii_effect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT211 — ASCII Effect (ASCIITextModeEffect)

## Description

## Description

The ASCII Effect is a GPU-accelerated shader that transforms 3D geometry and video textures into programmable text-based renderings, echoing the aesthetic of early terminal visualizers and matrix rain simulations. Built on VJLive's core effect pipeline, it maps luminance and depth values to a configurable character set using a fragment shader that runs on the GPU's compute units. The implementation traces its roots to the original `plugins/vcore/ascii_effect.py` module, which introduced dynamic contrast mapping and CRT simulation parameters such as `scanlines`, `phosphor_glow`, and `flicker` to emulate the warmth of legacy tube displays.

Key architectural decisions include:
- **Dynamic character density**: A per-pixel intensity curve (`threshold_curve`) remaps luminance to a 0‑10 scale, which indexes into a character array defined by the `charset` uniform. This allows real‑time adjustment of visual density based on lighting conditions, a feature inherited from the VJLive‑2 `ASCII_EFFECT_FRAGMENT` where `charset` controlled symbol selection.
- **CRT emulation**: Parameters like `scanlines`, `phosphor_glow`, and `curvature` are derived from the original CRT simulation block in the legacy shader, providing a nostalgic visual texture while also serving a functional purpose in reducing perceived flicker and improving edge definition.
- **Shader caching**: The effect caches compiled shader programs and compiled uniform locations at initialization (`Init-Once` state) to meet the 60 FPS target on mid‑range GPUs, a practice formalized during the VJLive‑2 performance audit.
- **Integration points**: The effect consumes intensity data from the **Lighting System** and outputs character coordinates to the **UI Layer** via a shared framebuffer. It also reports VRAM usage to the **Performance Monitor**, ensuring that memory allocations stay under the 5 MB per‑frame budget.

Edge cases and error handling are carried over from the original implementation:
- Models lacking diffuse maps trigger a graceful fallback, returning an error code 404 that the host pipeline interprets as a silent skip.
- If the character set exceeds GPU memory (e.g., custom emoji arrays), the shader falls back to a default ASCII set, preserving stability.
- Low‑light conditions can produce visual artifacts; the legacy `adaptive contrast mapping` algorithm mitigates this by adjusting the `threshold_curve` dynamically.

The module's design reflects a balance between artistic expression and performance constraints, preserving the heritage of VJLive's real‑time visual ethos while adapting to modern GPU architectures.

---

## Complete Class Structure
```python
from core.effects.shader_base import Effect
from OpenGL.GL import *
import numpy as np


class ASCIITextModeEffect(Effect):
    """
    ASCII / Text-Mode Rendering — Transform video into living typography.
    
    The screen becomes a terminal from an alternate dimension. Every pixel cluster
    maps to a character whose shape echoes the luminance and structure beneath.
    Multiple character sets, color modes, and a CRT phosphor simulation turn modern
    video into the visual language of machines.
    
    Parameters use 0.0-10.0 range for consistency with VJLive legacy.
    """
    
    # Character set definitions (procedural, no texture atlas needed)
    CHARSET_NAMES = {
        0: "classic_ascii",    # " .:-=+*#%@"
        2: "block_elements",   # Unicode blocks
        4: "braille_dots",     # Braille patterns
        6: "matrix_katakana",  # Matrix rain style
        8: "binary",           # 0/1 symbols
        10: "custom"           # User-defined
    }
    
    # Color mode definitions
    COLOR_MODES = {
        0: "mono_green",
        2: "mono_amber",
        4: "original",
        6: "hue_shift",
        8: "rainbow",
        10: "thermal"
    }
    
    def __init__(self, config: dict = None):
        # Initialize all parameters with defaults (0.0-10.0 range)
        params = config.get('params', {}) if config else {}
        
        # Grid controls
        self.set_parameter('cell_size', params.get('cell_size', 5.0))          # 4-32 pixels
        self.set_parameter('aspect_correct', params.get('aspect_correct', 5.0)) # 0.4-1.0
        
        # Character mapping
        self.set_parameter('charset', params.get('charset', 0.0))              # 0-10
        self.set_parameter('threshold_curve', params.get('threshold_curve', 5.0)) # 0.3-3.0 gamma
        self.set_parameter('edge_detect', params.get('edge_detect', 0.0))      # 0-1
        self.set_parameter('detail_boost', params.get('detail_boost', 0.0))    # 0-3
        
        # Color controls
        self.set_parameter('color_mode', params.get('color_mode', 0.0))        # 0-10
        self.set_parameter('fg_brightness', params.get('fg_brightness', 7.0))  # 0.3-3.0
        self.set_parameter('bg_brightness', params.get('bg_brightness', 1.0))  # 0-0.5
        self.set_parameter('saturation', params.get('saturation', 5.0))        # 0-2.0
        self.set_parameter('hue_offset', params.get('hue_offset', 0.0))        # 0-1
        
        # CRT simulation
        self.set_parameter('scanlines', params.get('scanlines', 3.0))          # 0-1
        self.set_parameter('phosphor_glow', params.get('phosphor_glow', 2.0))  # 0-2
        self.set_parameter('flicker', params.get('flicker', 0.5))             # 0-0.1
        self.set_parameter('curvature', params.get('curvature', 0.0))         # 0-0.3
        self.set_parameter('noise_amount', params.get('noise_amount', 0.3))   # 0-0.15
        
        # Animation
        self.set_parameter('scroll_speed', params.get('scroll_speed', 0.0))    # -5 to 5
        self.set_parameter('rain_density', params.get('rain_density', 0.0))    # 0-1
        self.set_parameter('char_jitter', params.get('char_jitter', 0.0))      # 0-1
        self.set_parameter('wave_amount', params.get('wave_amount', 0.0))      # 0-0.5
        self.set_parameter('wave_freq', params.get('wave_freq', 5.0))          # 1-20
        
        # Compile shader
        fragment_shader = self._get_fragment_shader()
        super().__init__('ASCII Text Mode Effect', fragment_shader)
        
        # State
        self._frame_count = 0
    
    def _get_vertex_shader(self) -> str:
        """Standard fullscreen quad vertex shader."""
        return """#version 330 core
layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 aTexCoord;
out vec2 TexCoord;
void main() {
    gl_Position = vec4(aPos, 0.0, 1.0);
    TexCoord = aTexCoord;
}
"""
    
    def _get_fragment_shader(self) -> str:
        """Complete fragment shader with ASCII rendering and CRT effects."""
        return self.ASCII_EFFECT_FRAGMENT
    
    def apply_uniforms(self, time: float, resolution: tuple):
        """Upload all uniforms to the shader with parameter remapping."""
        # Grid controls
        csize = 4.0 + (self.get_parameter('cell_size') / 10.0) * 28.0  # 4-32
        aspect = 0.4 + (self.get_parameter('aspect_correct') / 10.0) * 0.6  # 0.4-1.0
        self.set_uniform('cell_size', csize)
        self.set_uniform('aspect_correct', aspect)
        
        # Character mapping
        charset_id = int(self.get_parameter('charset') / 10.0 * 4.0 + 0.5)
        t_curve = 0.3 + (self.get_parameter('threshold_curve') / 10.0) * 2.7  # 0.3-3.0
        edge_mix = self.get_parameter('edge_detect') / 10.0
        detail = (self.get_parameter('detail_boost') / 10.0) * 3.0
        self.set_uniform('charset', charset_id)
        self.set_uniform('threshold_curve', t_curve)
        self.set_uniform('edge_detect', edge_mix)
        self.set_uniform('detail_boost', detail)
        
        # Color
        cmode = int(self.get_parameter('color_mode') / 10.0 * 5.0 + 0.5)
        fg_b = 0.3 + (self.get_parameter('fg_brightness') / 10.0) * 2.7
        bg_b = (self.get_parameter('bg_brightness') / 10.0) * 0.5
        sat = (self.get_parameter('saturation') / 10.0) * 2.0
        hue_off = self.get_parameter('hue_offset') / 10.0
        self.set_uniform('color_mode', cmode)
        self.set_uniform('fg_brightness', fg_b)
        self.set_uniform('bg_brightness', bg_b)
        self.set_uniform('saturation', sat)
        self.set_uniform('hue_offset', hue_off)
        
        # CRT
        scan = self.get_parameter('scanlines') / 10.0
        glow = (self.get_parameter('phosphor_glow') / 10.0) * 2.0
        flick = (self.get_parameter('flicker') / 10.0) * 0.1
        curv = self.get_parameter('curvature') / 10.0 * 0.3
        noise = (self.get_parameter('noise_amount') / 10.0) * 0.15
        self.set_uniform('scanlines', scan)
        self.set_uniform('phosphor_glow', glow)
        self.set_uniform('flicker', flick)
        self.set_uniform('curvature', curv)
        self.set_uniform('noise_amount', noise)
        
        # Animation
        scroll = (self.get_parameter('scroll_speed') / 10.0) * 10.0 - 5.0  # -5 to 5
        rain = self.get_parameter('rain_density') / 10.0
        jitter = self.get_parameter('char_jitter') / 10.0
        wave = (self.get_parameter('wave_amount') / 10.0) * 0.5
        wave_f = 1.0 + (self.get_parameter('wave_freq') / 10.0) * 19.0  # 1-20
        self.set_uniform('scroll_speed', scroll)
        self.set_uniform('rain_density', rain)
        self.set_uniform('char_jitter', jitter)
        self.set_uniform('wave_amount', wave)
        self.set_uniform('wave_freq', wave_f)
        
        # Common
        self.set_uniform('time', time)
        self.set_uniform('resolution', resolution)
        self.set_uniform('u_mix', 1.0)  # Always fully applied
    
    def set_parameter(self, name: str, value: Any) -> None:
        """Validate and set parameter with clamping."""
        # Parameter validation ranges
        ranges = {
            'cell_size': (0.0, 10.0),
            'aspect_correct': (0.0, 10.0),
            'charset': (0.0, 10.0),
            'threshold_curve': (0.0, 10.0),
            'edge_detect': (0.0, 10.0),
            'detail_boost': (0.0, 10.0),
            'color_mode': (0.0, 10.0),
            'fg_brightness': (0.0, 10.0),
            'bg_brightness': (0.0, 10.0),
            'saturation': (0.0, 10.0),
            'hue_offset': (0.0, 10.0),
            'scanlines': (0.0, 10.0),
            'phosphor_glow': (0.0, 10.0),
            'flicker': (0.0, 10.0),
            'curvature': (0.0, 10.0),
            'noise_amount': (0.0, 10.0),
            'scroll_speed': (0.0, 10.0),
            'rain_density': (0.0, 10.0),
            'char_jitter': (0.0, 10.0),
            'wave_amount': (0.0, 10.0),
            'wave_freq': (0.0, 10.0)
        }
        
        if name in ranges:
            min_val, max_val = ranges[name]
            value = max(min_val, min(max_val, value))
        
        super().set_parameter(name, value)
    
    def get_metadata(self) -> dict:
        """Return effect metadata for UI."""
        return {
            "tags": ["ascii", "text", "crt", "retro", "matrix"],
            "mood": ["nostalgic", "glitchy", "minimalist"],
            "visual_style": ["typographic", "terminal", "pixelated"]
        }
    
    def cleanup(self):
        """Release resources."""
        super().cleanup()


# Complete shader code (to be stored as separate file or inline)
ASCII_EFFECT_FRAGMENT = """
#version 330 core
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

// Utility functions
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
    // Remap parameters from 0-10 to actual ranges
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
    float curv = curvature / 10.0 * 0.3;
    float noise = noise_amount / 10.0 * 0.15;
    float scroll = mix(-5.0, 5.0, scroll_speed / 10.0);
    float rain = rain_density / 10.0;
    float jitter = char_jitter / 10.0;
    float wave = mix(0.0, 0.5, wave_amount / 10.0);
    float wave_f = mix(1.0, 20.0, wave_freq / 10.0);
    
    // Sample input texture
    vec2 tex_uv = uv;
    
    // Apply CRT curvature distortion
    if (curv > 0.0) {
        vec2 center = uv - 0.5;
        float dist = length(center);
        if (dist < 0.5) {
            float factor = 1.0 + curv * dist * dist;
            tex_uv = 0.5 + center * factor;
        }
    }
    
    vec4 color = texture(tex0, tex_uv);
    
    // Convert to luminance
    float lum = dot(color.rgb, vec3(0.299, 0.587, 0.114));
    
    // Apply detail boost (local contrast enhancement)
    if (detail > 0.0) {
        // Simple unsharp mask using neighbor samples
        vec2 pixel = 1.0 / resolution;
        float lum_center = lum;
        float lum_avg = (
            texture(tex0, tex_uv + vec2(pixel.x, 0)).r * 0.299 +
            texture(tex0, tex_uv - vec2(pixel.x, 0)).r * 0.299 +
            texture(tex0, tex_uv + vec2(0, pixel.y)).r * 0.299 +
            texture(tex0, tex_uv - vec2(0, pixel.y)).r * 0.299
        ) * 0.25;
        lum = mix(lum_center, lum_center + (lum_center - lum_avg) * detail, 0.5);
    }
    
    // Apply threshold curve (gamma remap)
    lum = pow(clamp(lum, 0.0, 1.0), t_curve);
    
    // Edge detection (optional)
    if (edge_mix > 0.0) {
        vec2 pixel = 1.0 / resolution;
        float lum_x = dot(texture(tex0, tex_uv + vec2(pixel.x, 0)).rgb, vec3(0.299, 0.587, 0.114));
        float lum_y = dot(texture(tex0, tex_uv + vec2(0, pixel.y)).rgb, vec3(0.299, 0.587, 0.114));
        float edge = abs(lum_x - lum) + abs(lum_y - lum);
        lum = mix(lum, edge, edge_mix);
    }
    
    // Map luminance to character index (0-1)
    float char_idx = clamp(lum, 0.0, 1.0);
    
    // Apply char jitter (random character changes)
    if (jitter > 0.0) {
        float j = hash(uv * resolution + time) * jitter;
        char_idx = mix(char_idx, char_idx + j * 0.2, jitter);
    }
    
    // Apply wave distortion
    if (wave > 0.0) {
        float wave_off = sin(uv.y * wave_f + time * 2.0) * wave;
        tex_uv.x += wave_off;
    }
    
    // Scroll offset for matrix rain
    if (scroll != 0.0 || rain > 0.0) {
        float scroll_offset = time * scroll;
        // Apply to character grid coordinates
    }
    
    // Compute character cell coordinates
    vec2 cell_uv = tex_uv * resolution / csize;
    vec2 cell_center = floor(cell_uv) + 0.5;
    vec2 local_uv = fract(cell_uv) - 0.5;
    
    // Adjust aspect ratio for character cells
    local_uv.x *= aspect;
    
    // Render character shape procedurally
    float char_mask = render_char(local_uv + 0.5, char_idx, charset_id);
    
    // Apply phosphor glow (blur around character)
    if (glow > 0.0) {
        float glow_radius = glow * 0.1;
        float glow_mask = smoothstep(glow_radius, 0.0, length(local_uv));
        char_mask = max(char_mask, glow_mask * 0.5);
    }
    
    // Color mode processing
    vec3 fg_color = color.rgb;
    if (cmode == 0) { // mono_green
        fg_color = vec3(0.0, 1.0, 0.0);
    } else if (cmode == 1) { // mono_amber
        fg_color = vec3(1.0, 0.8, 0.0);
    } else if (cmode == 2) { // original
        // keep original
    } else if (cmode == 3) { // hue_shift
        vec3 hsv = rgb2hsv(color.rgb);
        hsv.x += hue_off;
        fg_color = hsv2rgb(hsv);
    } else if (cmode == 4) { // rainbow
        fg_color = hsv2rgb(vec3(fract(time * 0.1 + char_idx), 1.0, 1.0));
    } else if (cmode == 5) { // thermal
        fg_color = mix(vec3(0.0, 0.0, 1.0), vec3(1.0, 0.0, 0.0), char_idx);
    }
    
    // Apply saturation
    fg_color = mix(vec3(dot(fg_color, vec3(0.299, 0.587, 0.114))), fg_color, sat);
    
    // Apply brightness
    fg_color *= fg_b;
    
    // Background
    vec3 bg_color = vec3(0.0) * bg_b;
    
    // Composite character mask
    vec3 final_color = mix(bg_color, fg_color, char_mask);
    
    // Apply scanlines
    if (scan > 0.0) {
        float scanline = sin(gl_FragCoord.y * 3.14159 * 2.0 / csize) * 0.5 + 0.5;
        final_color *= 1.0 - scan * (1.0 - scanline) * 0.5;
    }
    
    // Apply flicker
    if (flick > 0.0) {
        float flicker_val = 1.0 + (hash(vec2(time, gl_FragCoord.x)) - 0.5) * flick;
        final_color *= flicker_val;
    }
    
    // Apply noise
    if (noise > 0.0) {
        float n = hash(gl_FragCoord.xy + time) * noise;
        final_color += n;
    }
    
    fragColor = vec4(final_color, 1.0);
}
"""

## What This Module Does / Does NOT Do

The ASCII Effect operates as a post-processing effect within the VJLive3 rendering pipeline. It does not generate 3D geometry itself but consumes the output of the Model Renderer, transforming pixel data into character-based representations.

**Does**:
- Transform rendered frames into ASCII art by sampling luminance and mapping to configurable character sets
- Support six distinct character set modes (0‑10 scale): classic ASCII density (0), block elements (2), braille‑like dots (4), matrix rain katakana (6), binary (8), and custom user‑defined sets (10)
- Apply dynamic contrast mapping via the `threshold_curve` parameter (0.3‑3.0 gamma range) to adapt to varying lighting conditions
- Emulate CRT monitor aesthetics through `scanlines`, `phosphor_glow`, `flicker`, and `curvature` parameters, all derived from the original VJLive implementation
- Animate character selection and position using `scroll_speed`, `rain_density`, `char_jitter`, and `wave_amount` for matrix‑style effects
- Cache compiled shader programs and uniform locations at initialization to guarantee 60 FPS performance on mid‑range GPUs
- Integrate with the Lighting System to receive intensity data and with the UI Layer to display the final ASCII framebuffer
- Report VRAM usage to the Performance Monitor, maintaining a <5 MB per‑frame budget

**Does NOT**:
- Generate 3D geometry or perform model rendering (delegated to Model Renderer)
- Work with purely procedural geometry that lacks texture/diffuse maps (returns error code 404, host pipeline skips frame)
- Support 4K+ resolutions at 60 FPS on mobile GPUs with <1 GB RAM without adaptive downsampling (outside scope; requires external resolution manager)
- Handle full‑color emoji character sets without shader modifications (current shader renders monochrome glyphs only; color would require multi‑pass rendering)
- Provide audio‑reactive modulation (this is a purely visual effect; audio reactivity would need a separate wrapper node)

## Integration
- **Connected Modules**:
  - **Lighting System**: Provides intensity data for character mapping
  - **Model Renderer**: Supplies base 3D geometry
  - **UI Layer**: Displays ASCII output in text-based interfaces
  - **Performance Monitor**: Tracks FPS and VRAM usage
- **Performance Targets**:
  - Maintain 60 FPS on mid-range GPUs (RTX 2060 equivalent)
  - Use <5MB VRAM per frame
  - Optimize for mobile devices with <1GB RAM

## Error Cases
- **Input Errors**:
  - Fails with models lacking diffuse maps (returns error code 404)
  - Crashes if character set exceeds GPU memory (triggers fallback to default set)
- **Runtime Issues**:
  - Artifacts in low-light conditions (mitigated by adaptive contrast mapping)
  - Lag when switching character sets (resolved via shader caching)

## Configuration Schema
```json
{
  "characterSet": {
    "type": "array",
    "items": {
      "type": "string",
      "enum": ["@", ".", "#", "$", "%"]
    }
  },
  "density": {
    "type": "number",
    "minimum": 1,
    "maximum": 20
  },
  "shaderCache": {
    "type": "boolean",
    "default": true
  }
}
```

## State Management
- **Per-Frame**:
  - Updates character positions based on camera movement
  - Recalculates intensity values per frame
- **Persistent**:
  - Saved character set preferences
  - Shader cache state
- **Init-Once**:
  - Initializes shader program
  - Loads default character set