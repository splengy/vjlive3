````markdown
# P7-VE13: Vignette Effect (Edge Darkening)

> **Task ID:** `P7-VE13`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/blend.py`)
> **Class:** `VignetteEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `VignetteEffect`—a compositing
effect that darkens or blurs the edges and corners of video frames, creating
cinematic vignetting. The effect gradually reduces brightness/saturation towards
screen boundaries. The objective is to document exact vignette mathematics,
parameter remaps, falloff curves, post-processing, CPU fallback, and comprehensive
tests for feature parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (processes incoming video)
- Sustain 60 FPS with real-time edge darkening (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful fallback without vignetting if disabled (Safety Rail 7)
- CPU fallback implementation for compatibility testing

## Implementation Notes / Porting Strategy
1. Compute distance from screen center to each pixel.
2. Apply radial falloff based on distance: `falloff = 1 - (distance / max_dist)^exponent`.
3. Darken or desaturate pixels based on falloff.
4. Support falloff curve types (linear, quadratic, smooth).
5. Support vignette color (black, color tint, blur).
6. Provide NumPy-based CPU fallback.

## Public Interface
```python
class VignetteEffect(Effect):
    """
    Vignette Effect: Cinematic edge darkening and desaturation.
    
    Darkens or blurs the edges and corners of video frames, creating a
    cinematic vignetting effect. Applies radial falloff from screen center
    to edges. Common in cinematography for focus and mood enhancement.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 use_gpu: bool = True):
        """
        Initialize the vignette effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU vignetting; else CPU falloff.
        """
        super().__init__("Vignette Effect", VIG_VERTEX_SHADER, 
                         VIG_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "post_processing"
        self.effect_tags = ["vignette", "edge", "darkening", "cinematic"]
        self.features = ["RADIAL_FALLOFF", "EDGE_EFFECTS"]
        self.usage_tags = ["CINEMATIC", "FOCUS", "MOOD"]
        
        self.use_gpu = use_gpu

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'vignette_intensity': (0.0, 10.0), # darkening strength
            'vignette_radius': (0.0, 10.0),    # falloff start distance
            'falloff_curve': (0.0, 10.0),      # curve shape
            'falloff_smoothness': (0.0, 10.0), # smooth gradient
            'vignette_color': (0.0, 10.0),     # color tint (black, color)
            'saturation_falloff': (0.0, 10.0), # desaturate edges
            'shape_aspect': (0.0, 10.0),       # elliptical vs circular
            'edge_blur': (0.0, 10.0),          # gaussian blur at edges
            'center_x': (0.0, 10.0),           # vignette center X
            'opacity': (0.0, 10.0),            # effect opacity
        }

        # Default parameter values
        self.parameters = {
            'vignette_intensity': 5.0,
            'vignette_radius': 6.0,
            'falloff_curve': 2.0,              # quadratic
            'falloff_smoothness': 5.0,
            'vignette_color': 0.0,             # black
            'saturation_falloff': 3.0,
            'shape_aspect': 5.0,               # circular
            'edge_blur': 0.0,
            'center_x': 5.0,                   # screen center
            'opacity': 8.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'vignette_intensity': "Darkening strength (0=none, 10=extreme)",
            'vignette_radius': "Falloff start distance (0=small, 10=large)",
            'falloff_curve': "0=linear, 2=quadratic, 5=cubic, 10=exponential",
            'falloff_smoothness': "Gradient smoothness (0=hard, 10=soft)",
            'vignette_color': "0=black, 3=dark blue, 6=dark red, 10=custom",
            'saturation_falloff': "Desaturate edges (0=none, 10=full gray)",
            'shape_aspect': "0=vertical ellipse, 5=circle, 10=horizontal ellipse",
            'edge_blur': "Gaussian blur at edges (0=none, 10=heavy)",
            'center_x': "Vignette center position (0=left, 5=center, 10=right)",
            'opacity': "Effect opacity (0=invisible, 10=full vignette)",
        }

        # Sweet spots
        self._sweet_spots = {
            'vignette_intensity': [3.0, 5.0, 7.0],
            'vignette_radius': [5.0, 6.0, 8.0],
            'falloff_curve': [1.0, 2.0, 3.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None, 
              chain = None) -> int:
        """
        Render vignette-darkened version of input texture.
        
        Args:
            tex_in: Input texture (required).
            extra_textures: Optional additional textures.
            chain: Rendering chain context.
            
        Returns:
            Output texture with vignette applied.
        """
        # Compute radial distance from center
        # Apply falloff curve
        # Darken or desaturate based on falloff
        # Apply optional edge blur
        # Return output texture
        pass

    def compute_vignette_falloff(self, distance: float, max_distance: float,
                                radius: float, curve_exp: float) -> float:
        """
        Compute vignette falloff at distance from center.
        
        Args:
            distance: Distance from vignette center.
            max_distance: Maximum screen distance.
            radius: Falloff start radius.
            curve_exp: Curve exponent (1=linear, 2=quadratic).
            
        Returns:
            Falloff factor [0, 1] (1=full visibility, 0=full vignette).
        """
        # Compute normalized distance
        # Clamp to radius
        # Apply curve exponent
        # Return falloff value
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms for vignette parameters.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input (unused).
            semantic_layer: Optional semantic input (unused).
        """
        # Compute vignette center from center_x
        # Bind falloff parameters to uniforms
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `vignette_intensity` (float, UI 0—10) → internal `I` = x / 10.0
  - Darkening strength [0, 1.0]
- `vignette_radius` (float, UI 0—10) → internal `r` = map_linear(x, 0,10, 0.2, 1.0)
  - Falloff start distance (normalized) [0.2, 1.0]
- `falloff_curve` (float, UI 0—10) → internal `c` = map_linear(x, 0,10, 1.0, 4.0)
  - Curve exponent [1.0 linear, 4.0 steep fall]
- `falloff_smoothness` (float, UI 0—10) → internal `smooth` = map_linear(x, 0,10, 0.0, 0.3)
  - Smoothstep range [0, 0.3]
- `vignette_color` (int, UI 0—10) → internal color:
  - 0–2: Black (0, 0, 0)
  - 3–5: Dark blue (0, 0, 0.3)
  - 6–8: Dark red (0.3, 0, 0)
  - 9–10: Custom color input
- `saturation_falloff` (float, UI 0—10) → internal `sat_f` = x / 10.0
  - Desaturation factor [0, 1.0]
- `shape_aspect` (float, UI 0—10) → internal `aspect` = map_linear(x, 0,10, 0.5, 2.0)
  - Aspect ratio for elliptical vignette [0.5, 2.0]
- `edge_blur` (float, UI 0—10) → internal `blur` = map_linear(x, 0,10, 0.0, 10.0)
  - Gaussian blur sigma [0, 10]
- `center_x` (float, UI 0—10) → internal `cx` = x / 10.0
  - Vignette center X (normalized) [0, 1.0]
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Effect opacity [0, 1]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float vignette_intensity;`   // darkening strength
- `uniform float vignette_radius;`      // falloff start
- `uniform float falloff_curve;`        // curve exponent
- `uniform float falloff_smoothness;`   // gradient smoothness
- `uniform vec3 vignette_color;`        // darkening color
- `uniform float saturation_falloff;`   // desaturation factor
- `uniform float shape_aspect;`         // aspect ratio
- `uniform float edge_blur;`            // blur sigma
- `uniform float center_x;`             // center x position
- `uniform float opacity;`              // effect opacity
- `uniform vec2 resolution;`            // screen size
- `uniform sampler2D tex_in;`           // input texture

## Effect Math (concise, GPU/CPU-consistent)

### 1) Distance Computation

For each pixel at normalized coordinates `(x, y)`:

```
// Vignette center (parametric X, fixed Y at center)
center_x = center_x  // from parameter
center_y = 0.5

// Screen aspect ratio
aspect = resolution.x / resolution.y

// Distance with aspect correction
dx = (x - center_x) * aspect
dy = (y - center_y)

distance = sqrt(dx^2 + dy^2)
max_distance = sqrt((0.5*aspect)^2 + 0.5^2)
distance_normalized = distance / max_distance
```

### 2) Falloff Computation

Compute vignette falloff based on curve:

```
// Normalize distance to [0, 1] range
t = distance_normalized

// Clamp to radius
if shape_aspect != 1.0:
    // Elliptical vignette
    t = t * (1.0 + (shape_aspect - 1.0) * abs(dx) / (0.5 * aspect))

// Apply falloff curve
if t < vignette_radius:
    falloff = 1.0
else:
    falloff_range = 1.0 - vignette_radius
    falloff_t = (t - vignette_radius) / falloff_range
    falloff = pow(1.0 - falloff_t, falloff_curve)
    
    // Smooth transition
    if falloff_smoothness > 0:
        falloff = smoothstep(vignette_radius + falloff_smoothness, 
                           vignette_radius, distance_normalized)
```

### 3) Darkening and Desaturation

Apply vignette effect based on falloff:

```
// Sample original color
color = texture(tex_in, uv)

// Darken edges
color_darkened = mix(vignette_color, color, falloff)

// Apply intensity modulation
color_darkened = color_darkened * (1.0 - vignette_intensity * (1.0 - falloff))

// Desaturate edges
if saturation_falloff > 0:
    gray = dot(color_darkened, vec3(0.299, 0.587, 0.114))
    color_darkened = mix(vec3(gray), color_darkened, 
                        falloff + (1.0 - falloff) * (1.0 - saturation_falloff))
```

### 4) Edge Blur (Optional)

Apply Gaussian blur at edges:

```
if edge_blur > 0:
    // Blur radius based on falloff
    blur_amount = edge_blur * (1.0 - falloff)
    
    // Sample neighboring pixels and blend
    blur_samples = 4
    blurred = texture(tex_in, uv)
    for i in range(blur_samples):
        offset = blur_amount * vec2(cos(2π*i/blur_samples), sin(2π*i/blur_samples))
        blurred += texture(tex_in, uv + offset)
    
    blurred /= (blur_samples + 1)
    color_darkened = mix(color_darkened, blurred, edge_blur * 0.1)
```

### 5) Final Composite

```
// Alpha compositing
output = mix(color, color_darkened, opacity)
```

## CPU Fallback (NumPy sketch)

```python
def vignette_cpu(frame, vignette_intensity, vignette_radius, 
                falloff_curve, saturation_falloff, shape_aspect):
    """Apply vignette darkening on CPU."""
    
    h, w = frame.shape[:2]
    img = frame.astype(np.float32) / 255.0
    output = img.copy()
    
    # Create vignette mask
    yy, xx = np.meshgrid(np.arange(h) / h, np.arange(w) / w, indexing='ij')
    
    # Normalized distance from center
    aspect = w / h
    dx = (xx - 0.5) * aspect
    dy = yy - 0.5
    distance = np.sqrt(dx**2 + dy**2)
    max_dist = np.sqrt((0.5*aspect)**2 + 0.5**2)
    distance_norm = distance / max_dist
    
    # Falloff curve
    falloff = np.ones_like(distance_norm)
    mask = distance_norm >= vignette_radius
    falloff[mask] = np.power(1.0 - (distance_norm[mask] - vignette_radius) / 
                            (1.0 - vignette_radius), falloff_curve)
    
    # Apply darkening
    for c in range(3):
        output[:, :, c] = output[:, :, c] * (1.0 - vignette_intensity * (1.0 - falloff))
    
    # Desaturate edges
    if saturation_falloff > 0:
        gray = 0.299 * output[:,:,0] + 0.587 * output[:,:,1] + 0.114 * output[:,:,2]
        for c in range(3):
            output[:,:,c] = gray * (1 - falloff * saturation_falloff) + \
                          output[:,:,c] * falloff * saturation_falloff
    
    return (np.clip(output, 0, 1) * 255).astype(np.uint8)
```

## Presets (recommended)
- `Subtle Cinema`:
  - `vignette_intensity` 3.0, `vignette_radius` 7.0, `falloff_curve` 2.0,
    `falloff_smoothness` 5.0, `opacity` 5.0
- `Classic Dark`:
  - `vignette_intensity` 5.0, `vignette_radius` 6.0, `falloff_curve` 2.0,
    `opacity` 8.0
- `Dramatic Focus`:
  - `vignette_intensity` 7.0, `vignette_radius` 5.0, `falloff_curve` 3.0,
    `saturation_falloff` 5.0, `opacity` 10.0
- `Soft Elliptical`:
  - `vignette_intensity` 4.0, `vignette_radius` 7.0, `falloff_curve` 1.5,
    `shape_aspect` 7.0 (horizontal), `opacity` 6.0

## Edge Cases and Error Handling
- **Falloff_curve = 0**: Use falloff_curve = 1.0 (linear fallback).
- **Vignette_radius > 1**: Clamp to 1.0 (no falloff needed).
- **Very small falloff_smoothness**: May cause harsh transitions; clamp to ≥0.
- **Center outside [0, 1]**: Still compute vignette; allow off-screen center.
- **opacity = 0**: Output is original image.

## Test Plan (minimum ≥80% coverage)
- `test_vignette_center_darkening` — center is brightest, edges darkest
- `test_vignette_radius_control` — radius parameter controls falloff start
- `test_falloff_curve_linear` — linear curve produces straight falloff
- `test_falloff_curve_quadratic` — quadratic curve steepens falloff
- `test_vignette_intensity_scaling` — intensity parameter scales darkening
- `test_saturation_falloff_desaturates` — edges desaturate with parameter
- `test_shape_aspect_ratio` — aspect parameter creates elliptical vignette
- `test_edge_blur_smooths` — blur parameter blurs edges
- `test_falloff_smoothness` — smoothness parameter softens transitions
- `test_vignette_color_tint` — color parameter affects edge color
- `test_center_positioning` — center_x shifts vignette center
- `test_cpu_vs_gpu_parity` — CPU and GPU outputs match within tolerance
- `test_performance_60fps` — sustain ≥60 FPS at 1080p
- `test_zero_intensity_pass_through` — zero intensity shows original

## Verification Checkpoints
- [ ] `VignetteEffect` registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly
- [ ] Radial falloff darkens edges correctly
- [ ] All falloff curves work (linear, quadratic, cubic, exponential)
- [ ] Vignette color tinting works
- [ ] Saturation falloff desaturates edges
- [ ] Shape aspect ratio creates elliptical vignette
- [ ] Edge blur smooths transitions
- [ ] CPU fallback produces vignette darkening without crash
- [ ] Presets render at intended cinematic styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p
- [ ] Visual output matches vjlive reference

## Implementation Handoff Notes
- Performance optimization:
  - Pre-compute vignette mask texture (expensive distance field)
  - Update mask only when parameters change
  
- GPU optimization:
  - Fragment shader is simple; most cost is texture sampling
  - Use built-in smoothstep() for smooth transitioning
  
- CPU optimization:
  - Vectorize distance field computation with NumPy meshgrid
  - Use scipy for Gaussian blur if edge_blur > 0
  
- Numerical stability:
  - Clamp falloff_curve to avoid negative exponents
  - Guard against division by zero in distance computation

## Resources
- Reference: vjlive, Resolume, standard film vignetting
- Math: Radial distance, power functions, falloff curves
- GPU: GLSL smoothstep(), pow(), mix() functions

````
