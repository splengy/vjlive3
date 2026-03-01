````markdown
# P7-VE76: Rio Aesthetic Effect (Retro Style Compositor)

> **Task ID:** `P7-VE76`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/vstyle/vibrant_retro_styles.py`)
> **Class:** `RioAestheticEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `RioAestheticEffect`—a comprehensive
style effect that applies retro and vintage visual transformations to video. The
effect emulates CRT displays, VHS artifacts, scanlines, color grading, and retro
gaming aesthetics. The objective is to document exact visual transformations,
parameter remaps, style modes, CPU fallback, and comprehensive tests for feature
parity with VJlive-2.

## Technical Requirements
- Implement as a VJLive3 effect plugin (processes incoming video)
- Sustain 60 FPS with real-time retro styling (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful fallback without styling if disabled (Safety Rail 7)
- CPU fallback implementation for compatibility testing

## Implementation Notes / Porting Strategy
1. Implement color grading / LUT (lookup table) transformations.
2. Add scanline effect (horizontal lines, customizable spacing).
3. Add CRT distortion (barrel/pincushion warping).
4. Add noise layers (film grain, VHS artifacts).
5. Support multiple style modes (80s neon, 90s VHS, arcade, cyberpunk).
6. Provide NumPy-based CPU fallback.

## Public Interface
```python
class RioAestheticEffect(Effect):
    """
    Rio Aesthetic Effect: Vibrant retro visual styling.
    
    Applies comprehensive retro and vintage visual transformations including
    color grading, scanlines, CRT distortion, and VHS artifacts. Emulates
    classic gaming and television aesthetics for nostalgic visual effects.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 use_gpu: bool = True):
        """
        Initialize the retro aesthetic effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU styling; else CPU transformations.
        """
        super().__init__("Rio Aesthetic Effect", RETRO_VERTEX_SHADER, 
                         RETRO_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "styling"
        self.effect_tags = ["retro", "vintage", "aesthetic", "grading"]
        self.features = ["COLOR_GRADING", "RETRO_STYLING", "SCANLINES"]
        self.usage_tags = ["NOSTALGIC", "ARCADE", "CYBERPUNK", "VHS"]
        
        self.use_gpu = use_gpu
        self.lut_texture = None  # Color lookup table

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'style_mode': (0.0, 10.0),         # 80s, 90s, arcade, cyberpunk
            'color_grade': (0.0, 10.0),        # saturation/hue/warmth
            'scanline_intensity': (0.0, 10.0), # scanline darkness
            'scanline_spacing': (0.0, 10.0),   # pixel gap between lines
            'crt_distortion': (0.0, 10.0),     # barrel warp
            'vhs_noise': (0.0, 10.0),          # tape artifacts/jitter
            'film_grain': (0.0, 10.0),         # noise particles
            'color_aberration': (0.0, 10.0),   # RGB channel shift
            'brightness': (0.0, 10.0),         # output brightness
            'opacity': (0.0, 10.0),            # blending with original
        }

        # Default parameter values
        self.parameters = {
            'style_mode': 2.0,                 # 80s neon
            'color_grade': 5.0,
            'scanline_intensity': 5.0,
            'scanline_spacing': 3.0,
            'crt_distortion': 2.0,
            'vhs_noise': 2.0,
            'film_grain': 3.0,
            'color_aberration': 0.0,
            'brightness': 5.0,
            'opacity': 8.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'style_mode': "0=80s neon, 2=classic arcade, 5=90s VHS, 7=cyberpunk, 10=synthwave",
            'color_grade': "Color tone (0=blue/cool, 5=neutral, 10=orange/warm)",
            'scanline_intensity': "Scanline darkness (0=none, 10=heavy)",
            'scanline_spacing': "Pixel spacing between lines (1—20 pixels)",
            'crt_distortion': "Barrel warp effect (0=none, 10=extreme)",
            'vhs_noise': "VHS tape artifacts (0=none, 10=heavy glitch)",
            'film_grain': "Noise particles (0=none, 10=heavy grain)",
            'color_aberration': "RGB channel offset (0=none, 10=heavy separation)",
            'brightness': "Output brightness (0=dark, 10=bright)",
            'opacity': "Blend with original (0=original, 10=full effect)",
        }

        # Sweet spots
        self._sweet_spots = {
            'scanline_intensity': [3.0, 5.0, 8.0],
            'style_mode': [2.0, 5.0, 7.0],
            'vhs_noise': [1.0, 2.0, 4.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None, 
              chain = None) -> int:
        """
        Render retro-styled version of input texture.
        
        Args:
            tex_in: Input texture (required).
            extra_textures: Optional additional textures (precomputed LUT).
            chain: Rendering chain context.
            
        Returns:
            Output texture with retro styling applied.
        """
        # Apply color grading based on style_mode
        # Add scanlines
        # Apply CRT distortion
        # Add VHS noise and film grain
        # Apply color aberration
        # Composite with opacity blending
        # Return output texture
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms for retro styling.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input (unused).
            semantic_layer: Optional semantic input (unused).
        """
        # Select color grading based on style_mode
        # Bind LUT texture if available
        # Compute animation-based noise for time variance
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `style_mode` (int, UI 0—10) → internal mode:
  - 0–1: 80s Neon (bright, saturated, pink/cyan)
  - 2–3: Classic Arcade (warm, saturated, overscan)
  - 4–6: 90s VHS (desaturated, warm cast, jitter)
  - 7–8: Cyberpunk (cool, high contrast, neon accents)
  - 9–10: Synthwave (magenta/cyan, retrowave aesthetic)
- `color_grade` (float, UI 0—10) → internal `grade` = map_linear(x, 0,10, -1.0, 1.0)
  - Color tone shift [-1.0 cool, 0 neutral, 1.0 warm]
- `scanline_intensity` (float, UI 0—10) → internal `scan_I` = x / 10.0
  - Scanline opacity [0, 1.0]
- `scanline_spacing` (int, UI 0—10) → internal `scan_S` = clamp(round(x * 2), 1, 20)
  - Pixel spacing [1, 20]
- `crt_distortion` (float, UI 0—10) → internal `crt` = map_linear(x, 0,10, 0.0, 0.3)
  - Barrel warp factor [0, 0.3]
- `vhs_noise` (float, UI 0—10) → internal `vhs` = x / 10.0
  - Glitch/jitter amount [0, 1.0]
- `film_grain` (float, UI 0—10) → internal `grain` = x / 10.0
  - Grain opacity [0, 1.0]
- `color_aberration` (float, UI 0—10) → internal `aberr` = map_linear(x, 0,10, 0.0, 20.0)
  - Channel offset in pixels [0, 20]
- `brightness` (float, UI 0—10) → internal `Br` = map_linear(x, 0,10, 0.5, 1.5)
  - Brightness scale [0.5, 1.5]
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Blend factor [0, 1]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform int style_mode;`           // aesthetic selection
- `uniform float color_grade;`        // tone shift
- `uniform float scanline_intensity;` // line darkness
- `uniform int scanline_spacing;`     // pixel spacing
- `uniform float crt_distortion;`     // warp factor
- `uniform float vhs_noise;`          // artifact amount
- `uniform float film_grain;`         // grain opacity
- `uniform float color_aberration;`   // channel offset
- `uniform float brightness;`         // output brightness
- `uniform float opacity;`            // blend factor
- `uniform float time;`               // elapsed time
- `uniform vec2 resolution;`          // screen size
- `uniform sampler2D tex_in;`         // input texture
- `uniform sampler3D lut;`            // optional color LUT

## Effect Math (concise, GPU/CPU-consistent)

### 1) Color Grading via LUT

If LUT available, use 3D color lookup:

```
// Sample color from input
color = texture(tex_in, uv)

// Convert RGB [0,1] to LUT coordinates [0,255]
lut_coord = color * 255.0

// Sample 3D LUT (cubic interpolation ideal)
color_graded = texture(lut, lut_coord / 256.0)

// Otherwise, apply color shift directly
if style_mode == 0:          // 80s NEON
    // Boost magenta and cyan
    color.r = color.r * 1.2
    color.b = color.b * 1.1
    color.g = color.g * 0.9
elif style_mode == 1:        // ARCADE
    // Warm, saturated
    color += vec3(0.1, 0.05, 0)
    saturation *= 1.2
else:                        // VHS
    // Desaturated, warm
    saturation *= 0.8
    color += vec3(0.08, 0.02, 0)
```

### 2) Scanline Effect

Overlay horizontal lines:

```
// Scanline based on Y coordinate
y_pixel = uv.y * resolution.y
line_phase = mod(y_pixel, scanline_spacing)

// Create line pattern
scanline_value = (line_phase < 1.0) ? 1.0 : 0.5

// Darken pixels on scanlines
color = color * mix(1.0, scanline_value, scanline_intensity)
```

### 3) CRT Barrel Distortion

Apply pincushion/barrel warp:

```
// Center coordinates
center = vec2(0.5, 0.5)
uv_centered = uv - center

// Barrel distortion via polynomial
// radius^2 = (distance from center)^2
r2 = dot(uv_centered, uv_centered)

// Apply distortion
distortion = 1.0 + crt_distortion * r2

// Warp coordinates
uv_distorted = center + uv_centered * distortion

// Sample with clamping
color = texture(tex_in, clamp(uv_distorted, 0, 1))
```

### 4) VHS Glitch / Jitter

Add temporal artifacts:

```
// Time-based jitter
jitter_x = sin(time * 3.0 + uv.y * 10.0) * vhs_noise * 0.01
jitter_y = cos(time * 2.7 + uv.x * 7.0) * vhs_noise * 0.005

// Apply jitter to sampling coordinates
uv_jittered = uv + vec2(jitter_x, jitter_y)

// Occasional dislocation (every ~0.5 seconds)
if fract(time) < 0.1:
    uv_jittered.x += (rand(time) - 0.5) * vhs_noise * 0.05

color = texture(tex_in, clamp(uv_jittered, 0, 1))
```

### 5) Film Grain

Add noise particles:

```
// Pseudo-random noise seed based on UV and time
random_seed = uv + time * 0.1

// Generate noise value
grain_noise = fract(sin(dot(random_seed, vec2(12.9898, 78.233))) * 43758.5453)

// Normalize noise to [-0.5, 0.5] for brightness variation
grain_noise = grain_noise - 0.5

// Add grain to color
color = color + grain_noise * film_grain * 0.1
```

### 6) Chromatic Aberration

Shift RGB channels:

```
// Offset each channel by color_aberration amount
offset = color_aberration / resolution.x  // normalize to screen

uv_r = uv + vec2(offset, 0)
uv_g = uv
uv_b = uv - vec2(offset, 0)

// Sample each channel separately
r = texture(tex_in, uv_r).r
g = texture(tex_in, uv_g).g
b = texture(tex_in, uv_b).b

color = vec3(r, g, b)
```

### 7) Final Composite

```
// Brightness scaling
color = color * brightness

// Clamp to valid range
color = clamp(color, 0, 1)

// Blend with original
color_out = mix(original_color, color, opacity)
```

## CPU Fallback (NumPy sketch)

```python
def retro_aesthetic_cpu(frame, time, style_mode, color_grade, 
                       scanline_intensity, scanline_spacing,
                       crt_distortion, vhs_noise, film_grain):
    """Apply retro aesthetic on CPU."""
    
    img = frame.astype(np.float32) / 255.0
    h, w = img.shape[:2]
    output = img.copy()
    
    # Color grading
    if style_mode == 0:  # 80s NEON
        output[:,:,0] *= 1.2  # red boost
        output[:,:,2] *= 1.1  # blue boost
        output[:,:,1] *= 0.9  # green reduce
    elif style_mode == 5:  # VHS
        output *= 0.9  # desaturate
        output[:,:,0] += 0.08  # warm cast
        output[:,:,2] -= 0.02
    
    # Scanlines
    for y in range(h):
        if y % scanline_spacing == 0:
            output[y, :] *= (1.0 - scanline_intensity * 0.5)
    
    # Film grain
    if film_grain > 0:
        grain = np.random.randn(h, w, 3) * 0.1 * film_grain
        output = output + grain
    
    # VHS jitter (every few pixels)
    if vhs_noise > 0:
        jitter = np.random.randint(-2, 2, (h, w)) * vhs_noise
        for x in range(w - 1):
            offset = int(jitter[0, x])
            if 0 <= x + offset < w:
                output[:, x] = np.roll(output[:, x], offset, axis=0)
    
    return np.clip(output, 0, 1) * 255.0
```

## Presets (recommended)
- `80s Neon`:
  - `style_mode` 0.0, `scanline_intensity` 6.0, `scanline_spacing` 3.0,
    `color_aberration` 2.0, `vhs_noise` 1.0, `film_grain` 2.0, `opacity` 8.0
- `Arcade Classic`:
  - `style_mode` 2.0, `scanline_intensity` 5.0, `scanline_spacing` 2.0,
    `color_grade` 6.0, `crt_distortion` 3.0, `film_grain` 3.0, `opacity` 7.0
- `VHS Decay`:
  - `style_mode` 5.0, `scanline_intensity` 4.0, `vhs_noise` 4.0,
    `film_grain` 5.0, `color_grade` 3.0, `opacity` 9.0
- `Cyberpunk Neon`:
  - `style_mode` 7.0, `color_aberration` 5.0, `color_grade` 2.0,
    `scanline_intensity` 3.0, `brightness` 6.0, `opacity` 10.0

## Edge Cases and Error Handling
- **Missing LUT texture**: Fall back to direct color shift.
- **Invalid style_mode**: Clamp to valid range [0, 10].
- **Scanline_spacing = 0**: Clamp to minimum 1.
- **NaN in noise generation**: Use deterministic fallback.
- **Out-of-bounds distortion**: Clamp coordinates to [0, 1].
- **opacity = 0**: Output is original image.

## Test Plan (minimum ≥80% coverage)
- `test_color_grade_80s_neon` — magenta/cyan boost visible
- `test_color_grade_arcade` — warm saturation boost visible
- `test_color_grade_vhs` — desaturation and warm cast visible
- `test_scanline_darkness` — lines darken with intensity
- `test_scanline_spacing` — correct pixel line spacing
- `test_crt_distortion_barrel` — barrel warp applied
- `test_vhs_jitter_temporal` — jitter changes over time
- `test_film_grain_noise` — grain visible at high settings
- `test_color_aberration_separation` — RGB channels offset
- `test_brightness_scaling` — brightness control works
- `test_all_style_modes` — all 5+ style modes render distinctly
- `test_cpu_vs_gpu_parity` — CPU and GPU match within tolerance
- `test_performance_60fps` — sustain ≥60 FPS at 1080p
- `test_presets_visual_distinct` — presets produce distinct looks

## Verification Checkpoints
- [ ] `RioAestheticEffect` registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly
- [ ] Color grading applies per style_mode
- [ ] Scanlines render correctly with adjustable spacing
- [ ] CRT distortion warps image accurately
- [ ] VHS jitter animates over time with noise
- [ ] Film grain adds natural noise texture
- [ ] Chromatic aberration shifts RGB channels
- [ ] CPU fallback produces styled output without crash
- [ ] Presets render at intended retro aesthetic styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p
- [ ] Visual output matches VJlive-2 reference

## Implementation Handoff Notes
- LUT optimization:
  - Pre-load color LUT from 3D texture (if available)
  - Fallback to procedural color shifts if no LUT
  - Cache LUT texture between frames
  
- GPU optimization:
  - Use fragment shader with built-in noise functions
  - Pre-compute scanline pattern in texture if possible
  
- CPU optimization:
  - Vectorize scanline application with NumPy slicing
  - Use scipy perlin noise for grain (smoother than random)
  
- Numerical stability:
  - Clamp all colors to [0, 1] before output
  - Ensure jitter offsets don't exceed texture bounds

## Resources
- Reference: VJlive-2, Resolume, RetroFX plugins
- Math: Color grading, barrel distortion, perlin noise
- GPU: GLSL fragment shaders, texture sampling, per-channel operations

````
