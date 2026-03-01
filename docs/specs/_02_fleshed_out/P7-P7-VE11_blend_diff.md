````markdown
# P7-VE11: Difference Blend Effect (Subtractive Compositor)

> **Task ID:** `P7-VE11`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/blend.py`)
> **Class:** `BlendDiffEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `BlendDiffEffect`—a compositing
effect that combines two video inputs using difference blending. Each pixel in
the output is the absolute difference of the corresponding pixels from both
inputs, creating unique contour and edge-enhancement effects. The objective is
to document exact difference blending mathematics, parameter remaps, post-processing,
CPU fallback, and comprehensive tests for feature parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (processes two video inputs)
- Sustain 60 FPS with real-time difference blending (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Handle missing input gracefully (Safety Rail 7)
- CPU fallback implementation for compatibility testing

## Implementation Notes / Porting Strategy
1. Accept two input textures (primary and secondary).
2. Implement per-pixel difference blending: `output = |input1 - input2|`.
3. Support opacity modulation on each input.
4. Support post-processing (contrast, threshold, color mapping).
5. Expose blend strength and edge enhancement parameters.
6. Provide NumPy-based CPU fallback.

## Public Interface
```python
class BlendDiffEffect(Effect):
    """
    Difference Blend Effect: Edge-detecting difference compositing.
    
    Combines two video inputs using absolute difference blending. Emphasizes
    edges and contours where the two inputs diverge. Useful for motion
    detection, edge enhancement, and uncovering hidden visual information.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 use_gpu: bool = True):
        """
        Initialize the difference blend effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU blending; else CPU subtraction.
        """
        super().__init__("Difference Blend Effect", DIFF_VERTEX_SHADER, 
                         DIFF_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "compositor"
        self.effect_tags = ["difference", "edge", "subtraction", "motion"]
        self.features = ["EDGE_DETECTION", "MOTION_SENSING"]
        self.usage_tags = ["CONTOUR", "MOTION_DETECTION", "ARTISTIC"]
        
        self.use_gpu = use_gpu
        self.tex_primary = None
        self.tex_secondary = None

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'input1_opacity': (0.0, 10.0),     # primary input strength
            'input2_opacity': (0.0, 10.0),     # secondary input strength
            'blend_intensity': (0.0, 10.0),    # difference magnitude
            'contrast': (0.0, 10.0),           # output contrast
            'threshold': (0.0, 10.0),          # edge detection threshold
            'edge_inversion': (0.0, 10.0),     # invert dark/bright edges
            'colorize_mode': (0.0, 10.0),      # color mapping style
            'brightness': (0.0, 10.0),         # output brightness
            'saturation': (0.0, 10.0),         # color intensity
            'opacity': (0.0, 10.0),            # composite opacity
        }

        # Default parameter values
        self.parameters = {
            'input1_opacity': 6.0,
            'input2_opacity': 6.0,
            'blend_intensity': 5.0,
            'contrast': 5.0,
            'threshold': 0.0,
            'edge_inversion': 0.0,
            'colorize_mode': 0.0,              # grayscale by default
            'brightness': 5.0,
            'saturation': 5.0,
            'opacity': 8.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'input1_opacity': "Primary input strength (0=none, 10=full)",
            'input2_opacity': "Secondary input strength (0=none, 10=full)",
            'blend_intensity': "Difference magnitude (0=subtle, 10=extreme)",
            'contrast': "Output contrast (0=flat, 10=sharp)",
            'threshold': "Edge detection threshold (0=all, 10=sharp edges only)",
            'edge_inversion': "Invert bright/dark (0=normal, 10=inverted)",
            'colorize_mode': "0=grayscale, 3=spectrum, 6=hue-based, 10=custom",
            'brightness': "Output brightness (0=dark, 10=bright)",
            'saturation': "Color intensity (0=mono, 10=vivid)",
            'opacity': "Blend with background (0=bg, 10=full difference)",
        }

        # Sweet spots
        self._sweet_spots = {
            'input1_opacity': [5.0, 7.0, 10.0],
            'input2_opacity': [5.0, 7.0, 10.0],
            'threshold': [0.0, 2.0, 5.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None, 
              chain = None) -> int:
        """
        Render difference-blended composition of two inputs.
        
        Args:
            tex_in: Primary input texture (required).
            extra_textures: [secondary_texture, optional background].
            chain: Rendering chain context.
            
        Returns:
            Output texture with difference blend applied.
        """
        # Bind primary and secondary textures
        # Apply per-pixel absolute difference blending
        # Apply thresholding if enabled
        # Apply edge enhancement and post-processing
        # Return output texture
        pass

    def blend_difference_rgb(self, color1: tuple, color2: tuple, 
                            opacity1: float, opacity2: float,
                            intensity: float) -> tuple:
        """
        Perform difference RGB blend of two colors.
        
        Args:
            color1: RGB tuple (r1, g1, b1) each in [0, 1].
            color2: RGB tuple (r2, g2, b2) each in [0, 1].
            opacity1: Strength of first color [0, 1].
            opacity2: Strength of second color [0, 1].
            intensity: Difference blend factor [0, 1].
            
        Returns:
            Blended RGB tuple (r, g, b) in [0, 1].
        """
        # Difference: output = |input1 * opacity1 - input2 * opacity2|
        # Scale by intensity
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms for difference blending.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input (unused).
            semantic_layer: Optional semantic input (unused).
        """
        # Bind blend parameters to uniforms
        # Update threshold and colorization settings
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `input1_opacity` (float, UI 0—10) → internal `α1` = x / 10.0
  - Primary input strength [0, 1.0]
- `input2_opacity` (float, UI 0—10) → internal `α2` = x / 10.0
  - Secondary input strength [0, 1.0]
- `blend_intensity` (float, UI 0—10) → internal `B` = map_linear(x, 0,10, 0.0, 2.0)
  - Difference magnitude scale [0, 2.0]
- `contrast` (float, UI 0—10) → internal `C` = map_linear(x, 0,10, 0.5, 1.5)
  - Contrast scale [0.5, 1.5]
- `threshold` (float, UI 0—10) → internal `T` = x / 10.0
  - Threshold for edge detection [0, 1.0]
- `edge_inversion` (float, UI 0—10) → internal `inv` = x / 10.0
  - Inversion strength [0, 1.0]
- `colorize_mode` (int, UI 0—10) → internal mode:
  - 0–2: Grayscale (no color mapping)
  - 3–5: Spectrum (hot/cool colormap)
  - 6–8: Hue-based (edge direction colored)
  - 9–10: Custom gradient
- `brightness` (float, UI 0—10) → internal `Br` = map_linear(x, 0,10, 0.5, 1.5)
  - Brightness scale [0.5, 1.5]
- `saturation` (float, UI 0—10) → internal `Sat` = x / 10.0
  - Saturation factor [0, 1.0]
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Composite opacity [0, 1]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float input1_opacity;`     // primary strength
- `uniform float input2_opacity;`     // secondary strength
- `uniform float blend_intensity;`    // difference scale
- `uniform float contrast;`           // output contrast
- `uniform float threshold;`          // edge threshold
- `uniform float edge_inversion;`     // edge inversion
- `uniform int colorize_mode;`        // color mapping type
- `uniform float brightness;`         // output brightness
- `uniform float saturation;`         // color saturation
- `uniform float opacity;`            // composite opacity
- `uniform sampler2D tex_primary;`    // input 1
- `uniform sampler2D tex_secondary;`  // input 2

## Effect Math (concise, GPU/CPU-consistent)

### 1) Absolute Difference Blending

For each pixel, compute absolute difference:

```
// Sample inputs
color1 = texture(tex_primary, uv)
color2 = texture(tex_secondary, uv)

// Apply opacity
color1_mod = color1 * input1_opacity
color2_mod = color2 * input2_opacity

// Absolute difference
color_diff = abs(color1_mod - color2_mod)

// Scale by intensity
color_diff = color_diff * blend_intensity
```

### 2) Thresholding (Edge Detection)

Optionally threshold to isolate edges:

```
// Compute luminance of difference
luma_diff = dot(color_diff, vec3(0.299, 0.587, 0.114))

// Apply threshold
if threshold > 0:
    edge_mask = step(threshold, luma_diff)
    color_diff = color_diff * edge_mask

// Invert if requested
if edge_inversion > 0:
    color_diff = mix(color_diff, vec3(1.0) - color_diff, edge_inversion)
```

### 3) Contrast Adjustment

```
// Center around 0.5 and scale
color_diff = 0.5 + (color_diff - 0.5) * contrast

// Clamp to valid range
color_diff = clamp(color_diff, 0, 1)
```

### 4) Colorization

Map grayscale to color based on mode:

```
if colorize_mode == 0:          // GRAYSCALE
    // No color mapping; use as-is
    color_out = color_diff
elif colorize_mode == 1:        // SPECTRUM (hot colormap)
    // Remap luminance to hot colormap
    // Dark → blue, Mid → yellow, Bright → red
    luma = dot(color_diff, vec3(0.299, 0.587, 0.114))
    color_out = hot_colormap(luma)
elif colorize_mode == 2:        // HUE-BASED
    // Map luminance to hue
    luma = dot(color_diff, vec3(0.299, 0.587, 0.114))
    hue = luma * 6.283  // full hue rotation
    color_out = hsv_to_rgb(vec3(hue, saturation, 1.0))
else:
    color_out = color_diff
```

### 5) Brightness and Saturation

```
// Brightness scaling
color_out = color_out * brightness

// Saturation
gray = dot(color_out, vec3(0.299, 0.587, 0.114))
gray_vec = vec3(gray)
color_out = mix(gray_vec, color_out, saturation)
```

### 6) Final Composite

```
// Alpha compositing
output = mix(background, color_out, opacity)
```

## CPU Fallback (NumPy sketch)

```python
def blend_diff_cpu(frame1, frame2, opacity1, opacity2, blend_intensity,
                  contrast, threshold, edge_inversion, colorize_mode):
    """Perform difference blend on CPU."""
    
    # Normalize inputs to [0, 1]
    img1 = frame1.astype(np.float32) / 255.0
    img2 = frame2.astype(np.float32) / 255.0
    
    # Apply opacity
    img1_mod = img1 * opacity1
    img2_mod = img2 * opacity2
    
    # Absolute difference
    result = np.abs(img1_mod - img2_mod)
    result = result * blend_intensity
    
    # Thresholding
    if threshold > 0:
        luma = 0.299 * result[:,:,0] + 0.587 * result[:,:,1] + 0.114 * result[:,:,2]
        mask = (luma > threshold).astype(np.float32)
        for c in range(3):
            result[:,:,c] = result[:,:,c] * mask
    
    # Contrast
    result = 0.5 + (result - 0.5) * contrast
    
    # Colorize (grayscale fallback for CPU)
    if colorize_mode > 2:  # SPECTRUM or HUE
        luma = 0.299 * result[:,:,0] + 0.587 * result[:,:,1] + 0.114 * result[:,:,2]
        # Simple hot colormap: dark=blue, bright=red
        result[:,:,2] = luma  # blue channel as luminance
        result[:,:,0] = luma  # red channel as luminance
        result[:,:,1] = (1 - luma) * 0.5  # green inverted
    
    return np.clip(result, 0, 1) * 255.0
```

## Presets (recommended)
- `Simple Edge Detection`:
  - `input1_opacity` 5.0, `input2_opacity` 5.0, `blend_intensity` 5.0,
    `contrast` 6.0, `threshold` 0.0, `opacity` 8.0
- `Sharp Contour`:
  - `input1_opacity` 8.0, `input2_opacity` 8.0, `blend_intensity` 6.0,
    `contrast` 8.0, `threshold` 3.0, `opacity` 10.0
- `Motion Glow`:
  - `input1_opacity` 7.0, `input2_opacity` 7.0, `blend_intensity` 4.0,
    `contrast` 5.0, `colorize_mode` 3.0 (spectrum), `saturation` 7.0, `opacity` 7.0
- `Inverted Edges`:
  - `input1_opacity` 6.0, `input2_opacity` 6.0, `blend_intensity` 5.0,
    `contrast` 7.0, `edge_inversion` 8.0, `opacity` 9.0

## Edge Cases and Error Handling
- **Missing secondary input**: Use black (0, 0, 0) as fallback.
- **Threshold > 1**: Produces no edges; clamp to [0, 1].
- **Zero opacity**: Output is black (no signal).
- **Mismatched resolutions**: Force secondary to match primary.
- **Invalid colorize_mode**: Default to grayscale.
- **NaN from division**: Use safe fallback values.

## Test Plan (minimum ≥80% coverage)
- `test_difference_identical_black` — |0-0| = 0 (black)
- `test_difference_white_black` — |1-0| = 1 (white)
- `test_difference_color_subtraction` — color differences computed correctly
- `test_opacity1_scales` — opacity1 modulates first input
- `test_opacity2_scales` — opacity2 modulates second input
- `test_blend_intensity_magnification` — intensity scales difference
- `test_threshold_edge_isolation` — threshold removes low-difference pixels
- `test_edge_inversion` — inversion inverts bright/dark
- `test_contrast_adjustment` — contrast steepens difference gradient
- `test_colorize_grayscale` — grayscale mode preserves luminance
- `test_colorize_spectrum` — spectrum mode colors edges
- `test_brightness_scaling` — brightness scales output
- `test_cpu_vs_gpu_parity` — CPU and GPU match within tolerance
- `test_motion_detection` — moving objects produce high difference

## Verification Checkpoints
- [ ] `BlendDiffEffect` registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly
- [ ] Absolute difference blending computes correctly per-pixel
- [ ] Opacity modulation works on both inputs
- [ ] Thresholding isolates edges when enabled
- [ ] Edge inversion works as expected
- [ ] Colorization modes apply distinct color mappings
- [ ] Brightness/contrast/saturation post-processing applies
- [ ] CPU fallback produces difference output without crash
- [ ] Presets render at intended visual styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p
- [ ] Graceful handling of missing secondary input

## Implementation Handoff Notes
- Performance optimization:
  - Difference blend is simple; mostly texture bandwidth limited
  - Cache colormap lookups if colorize_mode is constant
  
- GPU optimization:
  - Fragment shader is straightforward
  - Use bilinear filtering for smooth color transitions
  
- CPU optimization:
  - Vectorize all operations with NumPy
  - Use uint8 arithmetic for speed when possible
  
- Numerical stability:
  - Clamp all values to prevent overflow
  - Guard against division by zero in threshold computation

## Resources
- Reference: vjlive difference blending, Photoshop difference blend mode
- Math: Absolute difference, color space conversions, colormaps
- GPU: GLSL abs() function, threshold operations

````
