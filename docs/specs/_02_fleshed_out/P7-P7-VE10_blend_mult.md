````markdown
# P7-VE10: Multiplicative Blend Effect (Darkening Compositor)

> **Task ID:** `P7-VE10`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/blend.py`)
> **Class:** `BlendMultEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `BlendMultEffect`—a compositing
effect that combines two video inputs using multiplicative blending. Each pixel
in the output is the product of the corresponding pixels from both inputs,
creating a darkening effect. The objective is to document exact multiplicative
blending mathematics, parameter remaps, color handling, CPU fallback, and
comprehensive tests for feature parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (processes two video inputs)
- Sustain 60 FPS with real-time blending (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Handle missing input gracefully (Safety Rail 7)
- CPU fallback implementation for compatibility testing

## Implementation Notes / Porting Strategy
1. Accept two input textures (primary and secondary).
2. Implement per-pixel multiplicative blending: `output = input1 * input2`.
3. Support opacity modulation on each input.
4. Support color space selection (RGB, HSL, HSV).
5. Expose blend strength and post-processing parameters.
6. Provide NumPy-based CPU fallback.

## Public Interface
```python
class BlendMultEffect(Effect):
    """
    Multiplicative Blend Effect: Darkening color compositing.
    
    Combines two video inputs using multiplicative color blending. Each output
    pixel is the product of the two input pixels, creating darkening effects.
    Used for masking, darkening, and selective blending operations.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 use_gpu: bool = True):
        """
        Initialize the multiplicative blend effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU blending; else CPU multiplication.
        """
        super().__init__("Multiplicative Blend Effect", MULT_VERTEX_SHADER, 
                         MULT_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "compositor"
        self.effect_tags = ["multiply", "blend", "darkening", "compositor"]
        self.features = ["MULTI_INPUT", "DARKENING_BLEND"]
        self.usage_tags = ["MASKING", "SELECTIVE", "MODULATION"]
        
        self.use_gpu = use_gpu
        self.tex_primary = None
        self.tex_secondary = None

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'input1_opacity': (0.0, 10.0),     # primary input strength
            'input2_opacity': (0.0, 10.0),     # secondary input strength
            'blend_intensity': (0.0, 10.0),    # multiply strength/factor
            'color_space': (0.0, 10.0),        # RGB, HSL, HSV selection
            'brightness': (0.0, 10.0),         # output scaling
            'contrast': (0.0, 10.0),           # output contrast
            'gamma': (0.0, 10.0),              # output gamma correction
            'invert_input2': (0.0, 10.0),      # invert secondary before blend
            'edge_detection': (0.0, 10.0),     # edge emphasis mode
            'opacity': (0.0, 10.0),            # composite opacity
        }

        # Default parameter values
        self.parameters = {
            'input1_opacity': 8.0,
            'input2_opacity': 8.0,
            'blend_intensity': 5.0,
            'color_space': 0.0,                # RGB by default
            'brightness': 5.0,
            'contrast': 5.0,
            'gamma': 5.0,
            'invert_input2': 0.0,
            'edge_detection': 0.0,
            'opacity': 10.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'input1_opacity': "Primary input strength (0=white, 10=full)",
            'input2_opacity': "Secondary input strength (0=white, 10=full)",
            'blend_intensity': "Multiply strength (0=no effect, 10=extreme)",
            'color_space': "0=RGB, 3=HSL, 6=HSV, 10=Luma",
            'brightness': "Output brightness (0=dark, 10=bright)",
            'contrast': "Output contrast (0=flat, 10=sharp)",
            'gamma': "Gamma correction (0=dark, 5=linear, 10=bright)",
            'invert_input2': "Invert input2 before blend (0=no, 10=yes)",
            'edge_detection': "Edge emphasis (0=none, 10=strong)",
            'opacity': "Blend with background (0=bg, 10=full blend)",
        }

        # Sweet spots
        self._sweet_spots = {
            'input1_opacity': [5.0, 8.0, 10.0],
            'input2_opacity': [5.0, 8.0, 10.0],
            'blend_intensity': [3.0, 5.0, 8.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None, 
              chain = None) -> int:
        """
        Render multiplicatively blended composition of two inputs.
        
        Args:
            tex_in: Primary input texture (required).
            extra_textures: [secondary_texture, optional background].
            chain: Rendering chain context.
            
        Returns:
            Output texture with multiplicative blend applied.
        """
        # Bind primary and secondary textures
        # Apply per-pixel multiplicative blending
        # Apply optional inversion on secondary input
        # Apply brightness/contrast/gamma post-processing
        # Return output texture
        pass

    def blend_multiplicative_rgb(self, color1: tuple, color2: tuple, 
                                opacity1: float, opacity2: float,
                                intensity: float) -> tuple:
        """
        Perform multiplicative RGB blend of two colors.
        
        Args:
            color1: RGB tuple (r1, g1, b1) each in [0, 1].
            color2: RGB tuple (r2, g2, b2) each in [0, 1].
            opacity1: Strength of first color [0, 1].
            opacity2: Strength of second color [0, 1].
            intensity: Multiply blend factor [0, 1].
            
        Returns:
            Blended RGB tuple (r, g, b) in [0, 1].
        """
        # Multiplicative: output = color1 * color2 * intensity
        # With opacity modulation on inputs
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
        # Update based on color_space and invert_input2
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `input1_opacity` (float, UI 0—10) → internal `α1` = 1.0 - (x / 10.0)
  - Primary input strength [0, 1.0] (inverted: white = 0, black = 1)
- `input2_opacity` (float, UI 0—10) → internal `α2` = 1.0 - (x / 10.0)
  - Secondary input strength [0, 1.0] (inverted)
- `blend_intensity` (float, UI 0—10) → internal `B` = map_linear(x, 0,10, 0.0, 2.0)
  - Blend factor [0, 2.0]
- `color_space` (int, UI 0—10) → internal space:
  - 0–2: RGB (no transformation)
  - 3–5: HSL (convert to/from HSL)
  - 6–8: HSV (convert to/from HSV)
  - 9–10: Luma (Y'CbCr)
- `brightness` (float, UI 0—10) → internal `Br` = map_linear(x, 0,10, 0.5, 1.5)
  - Brightness scale [0.5, 1.5]
- `contrast` (float, UI 0—10) → internal `C` = map_linear(x, 0,10, 0.5, 1.5)
  - Contrast scale [0.5, 1.5]
- `gamma` (float, UI 0—10) → internal `γ` = map_linear(x, 0,10, 0.5, 2.0)
  - Gamma exponent [0.5, 2.0]
- `invert_input2` (float, UI 0—10) → internal `inv` = x / 10.0
  - Inversion strength [0, 1.0]
- `edge_detection` (float, UI 0—10) → internal `edge` = x / 10.0
  - Edge emphasis strength [0, 1.0]
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Composite opacity [0, 1]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float input1_opacity;`     // primary strength
- `uniform float input2_opacity;`     // secondary strength
- `uniform float blend_intensity;`    // multiply factor
- `uniform int color_space;`          // RGB, HSL, HSV
- `uniform float brightness;`         // output brightness
- `uniform float contrast;`           // output contrast
- `uniform float gamma;`              // gamma correction
- `uniform float invert_input2;`      // invert secondary
- `uniform float edge_detection;`     // edge emphasis
- `uniform float opacity;`            // composite opacity
- `uniform sampler2D tex_primary;`    // input 1
- `uniform sampler2D tex_secondary;`  // input 2

## Effect Math (concise, GPU/CPU-consistent)

### 1) Multiplicative RGB Blending (Base Operation)

For each pixel, sample both inputs and multiply:

```
// Sample inputs
color1 = texture(tex_primary, uv)
color2 = texture(tex_secondary, uv)

// Opacity modulation (inverted: 0=white, 1=black)
color1_modulated = mix(vec3(1.0), color1, input1_opacity)
color2_modulated = mix(vec3(1.0), color2, input2_opacity)

// Optional inversion on input 2
if invert_input2 > 0:
    color2_modulated = mix(color2_modulated, vec3(1.0) - color2_modulated, invert_input2)

// Multiplicative blend
color_mult = color1_modulated * color2_modulated
color_mult = pow(color_mult, 1.0 / blend_intensity)  // apply intensity as exponent
```

### 2) Edge Detection (Optional Enhancement)

Compute edges and emphasize:

```
// Sobel-like edge detection
edge_h = texture(tex_secondary, uv + vec2(1.0/w, 0)) - texture(tex_secondary, uv - vec2(1.0/w, 0))
edge_v = texture(tex_secondary, uv + vec2(0, 1.0/h)) - texture(tex_secondary, uv - vec2(0, 1.0/h))
edge_strength = length(vec2(edge_h, edge_v))

// If edge_detection > 0, emphasize edges
if edge_detection > 0:
    color_mult = mix(color_mult, color_mult * (1.0 + edge_strength * 5.0), edge_detection)
```

### 3) Brightness and Contrast Adjustment

After blending, apply post-processing:

```
// Brightness scaling
color = color_mult * brightness

// Contrast (center around 0.5)
color = 0.5 + (color - 0.5) * contrast

// Gamma correction
color = pow(clamp(color, 0, 1), 1.0 / gamma)
```

### 4) Final Composite

Blend result with background:

```
// Alpha compositing
output = mix(background, color, opacity)
```

## CPU Fallback (NumPy sketch)

```python
def blend_mult_cpu(frame1, frame2, opacity1, opacity2, blend_intensity, 
                  brightness, contrast, gamma, invert_input2):
    """Perform multiplicative blend on CPU."""
    
    # Normalize inputs to [0, 1]
    img1 = frame1.astype(np.float32) / 255.0
    img2 = frame2.astype(np.float32) / 255.0
    
    # Opacity modulation (inverted)
    opacity1_inv = 1.0 - opacity1
    opacity2_inv = 1.0 - opacity2
    
    img1_mod = (1.0 - opacity1_inv) + opacity1_inv * img1
    img2_mod = (1.0 - opacity2_inv) + opacity2_inv * img2
    
    # Invert input2 if needed
    if invert_input2 > 0:
        img2_inv = 1.0 - img2_mod
        img2_mod = (1.0 - invert_input2) * img2_mod + invert_input2 * img2_inv
    
    # Multiplicative blend
    result = img1_mod * img2_mod
    result = np.power(result, 1.0 / blend_intensity)
    
    # Brightness
    result = result * brightness
    
    # Contrast
    result = 0.5 + (result - 0.5) * contrast
    
    # Gamma
    result = np.power(np.clip(result, 0, 1), 1.0 / gamma)
    
    # Convert back to [0, 255]
    return (np.clip(result, 0, 1) * 255).astype(np.uint8)
```

## Presets (recommended)
- `Soft Multiply`:
  - `input1_opacity` 7.0, `input2_opacity` 7.0, `blend_intensity` 4.0,
    `brightness` 5.0, `opacity` 10.0
- `Mask Mode`:
  - `input1_opacity` 10.0, `input2_opacity` 5.0, `blend_intensity` 5.0,
    `brightness` 6.0, `contrast` 5.0, `opacity` 10.0
- `Darkening Blend`:
  - `input1_opacity` 8.0, `input2_opacity` 8.0, `blend_intensity` 3.0,
    `brightness` 4.0, `contrast` 6.0, `opacity` 10.0
- `Inverted Multiply`:
  - `input1_opacity` 8.0, `input2_opacity` 8.0, `blend_intensity` 4.0,
    `invert_input2` 5.0, `brightness` 5.5, `opacity` 10.0

## Edge Cases and Error Handling
- **Missing secondary input**: Use white (1, 1, 1) as fallback (no darkening).
- **Zero opacity**: Mix input with white to preserve visibility.
- **NaN in gamma**: Clamp gamma to [0.1, 10.0].
- **Mismatched resolutions**: Force secondary to match primary.
- **Invalid color_space**: Default to RGB.
- **opacity = 0**: Output is background.

## Test Plan (minimum ≥80% coverage)
- `test_multiply_black_black` — (0,0,0) * (0,0,0) = (0,0,0)
- `test_multiply_white_white` — (1,1,1) * (1,1,1) = (1,1,1)
- `test_multiply_color_half` — (1,1,1) * (0.5,0.5,0.5) = (0.5,0.5,0.5)
- `test_opacity1_scales` — opacity1 modulates first input
- `test_opacity2_scales` — opacity2 modulates second input
- `test_blend_intensity_scaling` — intensity exponent applied correctly
- `test_invert_input2` — inversion flips secondary input
- `test_brightness_scaling` — brightness scales output
- `test_contrast_adjustment` — contrast changes steepness
- `test_gamma_correction` — gamma exponent applied
- `test_edge_detection_effect` — edge emphasis visible when enabled
- `test_missing_secondary_white` — graceful fallback to white
- `test_multiplication_associative` — (A*B)*C ≈ A*(B*C)
- `test_cpu_vs_gpu_parity` — CPU and GPU match within tolerance

## Verification Checkpoints
- [ ] `BlendMultEffect` registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly
- [ ] Multiplicative blending darkens correctly per-pixel
- [ ] Opacity modulation works on both inputs
- [ ] Input 2 inversion works as expected
- [ ] Brightness/contrast/gamma post-processing applies
- [ ] Edge detection mode emphasizes edges when enabled
- [ ] CPU fallback produces darkened output without crash
- [ ] Presets render at intended blending styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p
- [ ] Graceful handling of missing secondary input

## Implementation Handoff Notes
- Performance optimization:
  - Multiplicative blend is simple; focus on texture bandwidth
  - Cache edge detection results if mode is constant
  
- GPU optimization:
  - Fragment shader is lightweight; use bilinear filtering for quality
  - Avoid unnecessary edge detection when not enabled
  
- CPU optimization:
  - Vectorize all operations with NumPy
  - Use uint8 where possible for speed
  
- Numerical stability:
  - Clamp opacity to [0, 1] even though semantically inverted
  - Guard against pow(0, negative) in intensity exponent

## Resources
- Reference: vjlive blend operations, Photoshop multiply blend mode
- Math: Multiplicative color mixing, darkening effects
- GPU: GLSL texture sampling, pow() function

````
