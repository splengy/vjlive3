````markdown
# P7-VE09: Additive Blend Effect (Simple Compositor)

> **Task ID:** `P7-VE09`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/blend.py`)
> **Class:** `BlendAddEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `BlendAddEffect`—a simple
compositing effect that combines two video inputs using additive blending.
Each pixel in the output is the sum of the corresponding pixels from both
inputs, creating a brightening effect. The objective is to document exact
blending mathematics, parameter remaps, color handling (RGB, HSL), clipping
strategies, CPU fallback, and comprehensive tests for feature parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (processes two video inputs)
- Sustain 60 FPS with real-time blending (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Handle missing input gracefully (Safety Rail 7)
- CPU fallback implementation for compatibility testing

## Implementation Notes / Porting Strategy
1. Accept two input textures (primary and secondary).
2. Implement per-pixel additive blending: `output = input1 + input2`.
3. Support color space selection (RGB, HSL, HSV).
4. Support clipping modes (clamp, wrap, saturate).
5. Expose blend strength and mixing parameters.
6. Provide NumPy-based CPU fallback.

## Public Interface
```python
class BlendAddEffect(Effect):
    """
    Additive Blend Effect: Simple additive color compositing.
    
    Combines two video inputs using additive color blending. Each output
    pixel is the sum of the two input pixels, creating brightening effects.
    Used for layering, accumulation, and multi-source composition.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 use_gpu: bool = True):
        """
        Initialize the additive blend effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU blending; else CPU addition.
        """
        super().__init__("Additive Blend Effect", BLEND_VERTEX_SHADER, 
                         BLEND_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "compositor"
        self.effect_tags = ["blend", "additive", "compositor", "mixing"]
        self.features = ["MULTI_INPUT", "COLOR_COMPOSITING"]
        self.usage_tags = ["LAYERING", "ACCUMULATION", "MIXING"]
        
        self.use_gpu = use_gpu
        self.tex_primary = None
        self.tex_secondary = None

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'input1_opacity': (0.0, 10.0),     # primary input strength
            'input2_opacity': (0.0, 10.0),     # secondary input strength
            'color_space': (0.0, 10.0),        # RGB, HSL, HSV selection
            'clipping_mode': (0.0, 10.0),      # clamp, wrap, saturate
            'brightness': (0.0, 10.0),         # output scaling
            'saturation': (0.0, 10.0),         # color intensity (HSL mode)
            'contrast': (0.0, 10.0),           # output contrast
            'gamma': (0.0, 10.0),              # output gamma correction
            'channel_invert': (0.0, 10.0),     # invert channels 0-none, 10=all
            'opacity': (0.0, 10.0),            # composite opacity
        }

        # Default parameter values
        self.parameters = {
            'input1_opacity': 8.0,
            'input2_opacity': 8.0,
            'color_space': 0.0,                # RGB by default
            'clipping_mode': 0.0,              # clamp by default
            'brightness': 5.0,
            'saturation': 5.0,
            'contrast': 5.0,
            'gamma': 5.0,
            'channel_invert': 0.0,
            'opacity': 10.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'input1_opacity': "Primary input strength (0=invisible, 10=full)",
            'input2_opacity': "Secondary input strength (0=invisible, 10=full)",
            'color_space': "0=RGB, 3=HSL, 6=HSV, 10=Luma",
            'clipping_mode': "0=clamp, 3=wrap, 6=saturate, 10=soften",
            'brightness': "Output brightness (0=dark, 10=bright)",
            'saturation': "Color intensity (0=mono, 10=vivid)",
            'contrast': "Output contrast (0=flat, 10=sharp)",
            'gamma': "Gamma correction (0=dark, 5=linear, 10=bright)",
            'channel_invert': "Invert color channels (0=none, 10=all)",
            'opacity': "Blend with background (0=bg, 10=full blend)",
        }

        # Sweet spots
        self._sweet_spots = {
            'input1_opacity': [5.0, 8.0, 10.0],
            'input2_opacity': [5.0, 8.0, 10.0],
            'brightness': [4.0, 5.0, 6.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None, 
              chain = None) -> int:
        """
        Render additively blended composition of two inputs.
        
        Args:
            tex_in: Primary input texture (required).
            extra_textures: [secondary_texture, optional background].
            chain: Rendering chain context.
            
        Returns:
            Output texture with additive blend applied.
        """
        # Bind primary and secondary textures
        # Apply per-pixel additive blending
        # Apply color space transformation (if HSL/HSV)
        # Apply clipping
        # Apply brightness/contrast/gamma
        # Return output texture
        pass

    def blend_additive_rgb(self, color1: tuple, color2: tuple, 
                          opacity1: float, opacity2: float) -> tuple:
        """
        Perform additive RGB blend of two colors.
        
        Args:
            color1: RGB tuple (r1, g1, b1) each in [0, 1].
            color2: RGB tuple (r2, g2, b2) each in [0, 1].
            opacity1: Strength of first color [0, 1].
            opacity2: Strength of second color [0, 1].
            
        Returns:
            Blended RGB tuple (r, g, b) in [0, 1].
        """
        # Add colors: output = input1 * opacity1 + input2 * opacity2
        # Clip to [0, 1]
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms for blending parameters.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input (unused).
            semantic_layer: Optional semantic input (unused).
        """
        # Bind blend parameters to uniforms
        # Update based on color_space and clipping_mode
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `input1_opacity` (float, UI 0—10) → internal `α1` = x / 10.0
  - Primary input strength [0, 1.0]
- `input2_opacity` (float, UI 0—10) → internal `α2` = x / 10.0
  - Secondary input strength [0, 1.0]
- `color_space` (int, UI 0—10) → internal space:
  - 0–2: RGB (no transformation)
  - 3–5: HSL (convert to/from HSL)
  - 6–8: HSV (convert to/from HSV)
  - 9–10: Luma (Y'CbCr or grayscale)
- `clipping_mode` (int, UI 0—10) → internal mode:
  - 0–2: Clamp (clip to [0, 1])
  - 3–5: Wrap (modulo wrapping)
  - 6–8: Saturate (soft clipping via tanh)
  - 9–10: Soften (attenuate overly bright)
- `brightness` (float, UI 0—10) → internal `B` = map_linear(x, 0,10, 0.5, 1.5)
  - Brightness scale [0.5, 1.5]
- `saturation` (float, UI 0—10) → internal `Sat` = x / 10.0
  - Saturation factor [0, 1.0]
- `contrast` (float, UI 0—10) → internal `C` = map_linear(x, 0,10, 0.5, 1.5)
  - Contrast scale [0.5, 1.5]
- `gamma` (float, UI 0—10) → internal `γ` = map_linear(x, 0,10, 0.5, 2.0)
  - Gamma exponent [0.5, 2.0]
- `channel_invert` (float, UI 0—10) → internal `inv` = x / 10.0
  - Invert strength [0, 1.0]
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Composite opacity [0, 1]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float input1_opacity;`     // primary strength
- `uniform float input2_opacity;`     // secondary strength
- `uniform int color_space;`          // RGB, HSL, HSV
- `uniform int clipping_mode;`        // clamp, wrap, saturate
- `uniform float brightness;`         // output brightness
- `uniform float saturation;`         // color saturation
- `uniform float contrast;`           // output contrast
- `uniform float gamma;`              // gamma correction
- `uniform float channel_invert;`     // channel inversion
- `uniform float opacity;`            // composite opacity
- `uniform sampler2D tex_primary;`    // input 1
- `uniform sampler2D tex_secondary;`  // input 2

## Effect Math (concise, GPU/CPU-consistent)

### 1) Additive RGB Blending (Base Operation)

For each pixel, sample both inputs and add:

```
// Sample inputs
color1 = texture(tex_primary, uv)
color2 = texture(tex_secondary, uv)

// Additive blend (simple addition)
color_add = color1 * input1_opacity + color2 * input2_opacity
```

### 2) Clipping Strategies

Handle overflow based on clipping_mode:

```
if clipping_mode == 0:              // CLAMP
    color_clipped = clamp(color_add, 0, 1)
elif clipping_mode == 1:            // WRAP
    color_clipped = fract(color_add)  // modulo [0, 1]
elif clipping_mode == 2:            // SATURATE
    // Soft clipping via tanh
    color_clipped = 0.5 * (1.0 + tanh(2.0 * (color_add - 0.5)))
else:                               // SOFTEN
    // Attenuate overbright
    color_clipped = clamp(color_add, 0, 1)
    // Add slight reduction for very bright values
    color_clipped = color_clipped * (1.0 - 0.1 * max(0, color_add - 1.0))
```

### 3) Color Space Transformations

a) **RGB to HSL**:
```
max_c = max(r, g, b)
min_c = min(r, g, b)
l = (max_c + min_c) / 2

if max_c == min_c:
    h = s = 0
else:
    delta = max_c - min_c
    s = l < 0.5 ? delta / (max_c + min_c) : delta / (2 - max_c - min_c)
    
    if max_c == r:
        h = (g - b) / delta + (g < b ? 6 : 0)
    else if max_c == g:
        h = (b - r) / delta + 2
    else:
        h = (r - g) / delta + 4
    h /= 6
```

b) **HSL to RGB** (reverse transformation):
```
if s == 0:
    r = g = b = l
else:
    q = l < 0.5 ? l * (1 + s) : l + s - l * s
    p = 2 * l - q
    r = hue2rgb(p, q, h + 1/3)
    g = hue2rgb(p, q, h)
    b = hue2rgb(p, q, h - 1/3)
```

### 4) Brightness and Contrast Adjustment

After blending, apply post-processing:

```
// Brightness scaling
color = color * brightness

// Contrast (center around 0.5)
color = 0.5 + (color - 0.5) * contrast

// Gamma correction
color = pow(clamp(color, 0, 1), 1.0 / gamma)

// Channel inversion
if channel_invert > 0:
    inverted = 1.0 - color
    color = mix(color, inverted, channel_invert)

// Saturation (if HSL mode, adjust S)
// Saturation: desaturate = mix(gray, color, saturation)
gray = dot(color, vec3(0.299, 0.587, 0.114))  // Luma
color = mix(vec3(gray), color, saturation)
```

### 5) Final Composite

Blend result with background (if opacity < 1):

```
// Alpha compositing
output = mix(background, color, opacity)
```

## CPU Fallback (NumPy sketch)

```python
def blend_add_cpu(frame1, frame2, opacity1, opacity2, brightness, 
                 contrast, gamma, saturation, clipping_mode):
    """Perform additive blend on CPU."""
    
    # Normalize inputs to [0, 1]
    img1 = frame1.astype(np.float32) / 255.0
    img2 = frame2.astype(np.float32) / 255.0
    
    # Additive blend
    result = img1 * opacity1 + img2 * opacity2
    
    # Clipping
    if clipping_mode == 0:  # CLAMP
        result = np.clip(result, 0, 1)
    elif clipping_mode == 1:  # WRAP
        result = np.fmod(result, 1.0)
    else:  # SATURATE
        result = 0.5 * (1.0 + np.tanh(2.0 * (result - 0.5)))
    
    # Brightness
    result = result * brightness
    
    # Contrast
    result = 0.5 + (result - 0.5) * contrast
    
    # Gamma
    result = np.power(np.clip(result, 0, 1), 1.0 / gamma)
    
    # Saturation
    gray = 0.299 * result[:,:,0] + 0.587 * result[:,:,1] + 0.114 * result[:,:,2]
    gray = np.stack([gray, gray, gray], axis=2)
    result = gray * (1 - saturation) + result * saturation
    
    # Convert back to [0, 255]
    return (np.clip(result, 0, 1) * 255).astype(np.uint8)
```

## Presets (recommended)
- `Simple Additive`:
  - `input1_opacity` 5.0, `input2_opacity` 5.0, `clipping_mode` 0.0 (clamp),
    `brightness` 5.0, `opacity` 10.0
- `Bright Accumulation`:
  - `input1_opacity` 8.0, `input2_opacity` 8.0, `clipping_mode` 0.0 (clamp),
    `brightness` 6.0, `contrast` 6.0, `opacity` 10.0
- `Soft Blend`:
  - `input1_opacity` 6.0, `input2_opacity` 6.0, `clipping_mode` 2.0 (saturate),
    `brightness` 4.5, `opacity` 8.0
- `Saturated Mix`:
  - `input1_opacity` 7.0, `input2_opacity` 7.0, `clipping_mode` 0.0 (clamp),
    `saturation` 8.0, `brightness` 5.0, `opacity` 10.0

## Edge Cases and Error Handling
- **Missing secondary input**: Use black (0, 0, 0) as fallback.
- **NaN in gamma**: Clamp gamma to [0.1, 10.0] to avoid issues.
- **Overflow in addition**: Handle via clipping_mode (clamp, wrap, or saturate).
- **Mismatched resolutions**: Force secondary texture to match primary.
- **Invalid color_space**: Default to RGB.
- **opacity = 0**: Output is fully background.

## Test Plan (minimum ≥80% coverage)
- `test_additive_rgb_white_white` — (1,1,1) + (1,1,1) clamps to (1,1,1)
- `test_additive_rgb_color_sum` — arbitrary colors sum correctly
- `test_opacity1_scales_input1` — opacity1 modulates first input
- `test_opacity2_scales_input2` — opacity2 modulates second input
- `test_clipping_clamp` — overflow clipped to [0, 1]
- `test_clipping_wrap` — overflow wraps modulo [0, 1]
- `test_clipping_saturate` — overflow softly clipped via tanh
- `test_brightness_scaling` — brightness parameter scales output
- `test_contrast_adjustment` — contrast changes midtone steepness
- `test_gamma_correction` — gamma exponent applied correctly
- `test_saturation_modulation` — saturation parameter affects color intensity
- `test_channel_inversion` — channel_invert inverts RGB values
- `test_hsl_conversion` — RGB→HSL→RGB round-trip lossless
- `test_missing_secondary_texture` — graceful fallback to black
- `test_cpu_vs_gpu_parity` — CPU and GPU outputs match within tolerance

## Verification Checkpoints
- [ ] `BlendAddEffect` registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly
- [ ] Additive blending performs correctly per-pixel
- [ ] All clipping modes work (clamp, wrap, saturate, soften)
- [ ] Color space transformation works (RGB, HSL, HSV)
- [ ] Post-processing (brightness, contrast, gamma) applies correctly
- [ ] CPU fallback produces blended output without crash
- [ ] Presets render at intended visual blending styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p with typical settings
- [ ] Graceful handling of missing secondary input

## Implementation Handoff Notes
- Optimization strategies:
  - Cache color space conversion results if switching modes infrequently
  - Use lookup tables for gamma correction (fast approximation)
  - Pre-compute HSL↔RGB conversion matrices if applicable
  
- GPU performance:
  - Fragment shader is simple; most cost is texture sampling
  - Use bilinear filtering for smooth color interpolation
  
- CPU performance:
  - Vectorize all operations with NumPy
  - Use uint8 arithmetic where possible (avoid float overhead)
  
- Numerical precision:
  - Clamp gamma exponent to avoid NaN from negative bases
  - Handle white/black edge cases in HSL conversion (undefined hue)

## Resources
- Reference: vjlive blend operations, standard compositing
- Math: Additive color mixing, RGB/HSL/HSV color spaces, gamma curves
- GPU: GLSL texture sampling, clamp/fract/mix functions

````
