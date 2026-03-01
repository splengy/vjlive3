````markdown
# P7-VE04: Ripple Effect (Radial Water Distortion)

> **Task ID:** `P7-VE04`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/v_sws.py`)
> **Class:** `RippleEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `RippleEffect`—a 2D spatial
distortion effect that propagates concentric ripples outward from a center point,
similar to waves radiating from a stone dropped in water. The effect displaces
image pixels based on distance from the ripple center, creating realistic water-
like visual deformations. The objective is to document exact ripple mathematics,
parameter remaps, radial distortion approach, CPU fallback, and comprehensive
tests for feature parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (processes incoming video)
- Sustain 60 FPS with real-time radial distortion (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful fallback without ripple if disabled (Safety Rail 7)
- CPU fallback implementation for compatibility testing

## Implementation Notes / Porting Strategy
1. Implement radial distortion via fragment shader (GPU-accelerated).
2. Compute distance from ripple center to each pixel.
3. Apply periodic displacement based on distance: `displacement = amplitude * sin(frequency * (distance - time))`.
4. Support ripple source positioning (center, corner, custom).
5. Support ripple modes (expanding, contracting, pulsing).
6. Provide NumPy-based CPU fallback (frame remapping).

## Public Interface
```python
class RippleEffect(Effect):
    """
    Ripple Effect: Concentric water-like radial distortion.
    
    Propagates concentric ripples outward from a center point, displacing
    image pixels radially. Creates water-drop and impulse response effects.
    Common in VJ performance for dynamic, organic-looking video warping.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 use_gpu: bool = True):
        """
        Initialize the ripple effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU fragment distortion; else CPU remapping.
        """
        super().__init__("Ripple Effect", RIPPLE_VERTEX_SHADER, 
                         RIPPLE_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "distortion"
        self.effect_tags = ["ripple", "water", "radial", "distortion"]
        self.features = ["RADIAL_DISTORTION", "RIPPLE_ANIMATION"]
        self.usage_tags = ["ORGANIC", "WATER_LIKE", "IMPULSE"]
        
        self.use_gpu = use_gpu
        self.ripple_center = [0.5, 0.5]  # normalized: (0—1, 0—1)

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'amplitude': (0.0, 10.0),          # ripple height
            'wavelength': (0.0, 10.0),         # distance between peaks
            'frequency': (0.0, 10.0),          # ripple oscillation speed
            'ripple_mode': (0.0, 10.0),        # expanding, contracting, etc.
            'center_x': (0.0, 10.0),           # ripple source X (0=left, 10=right)
            'center_y': (0.0, 10.0),           # ripple source Y (0=top, 10=bottom)
            'dampening': (0.0, 10.0),          # ripple decay over distance
            'phase': (0.0, 10.0),              # temporal phase offset
            'edge_blend': (0.0, 10.0),         # smooth blend at edges
            'opacity': (0.0, 10.0),            # blending with original
        }

        # Default parameter values
        self.parameters = {
            'amplitude': 5.0,
            'wavelength': 4.0,
            'frequency': 2.0,
            'ripple_mode': 2.0,                # expanding by default
            'center_x': 5.0,                   # screen center
            'center_y': 5.0,                   # screen center
            'dampening': 3.0,
            'phase': 0.0,
            'edge_blend': 4.0,
            'opacity': 8.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'amplitude': "Ripple displacement magnitude (0=none, 10=extreme)",
            'wavelength': "Distance between ripple peaks (0=tight, 10=loose)",
            'frequency': "Ripple propagation speed (0=static, 10=fast)",
            'ripple_mode': "0=expanding, 5=pulsing, 10=contracting",
            'center_x': "Ripple source X position (0=left, 10=right)",
            'center_y': "Ripple source Y position (0=top, 10=bottom)",
            'dampening': "Ripple decay with distance (0=no decay, 10=rapid)",
            'phase': "Temporal phase offset (0—360°)",
            'edge_blend': "Smooth falloff at screen edges (0=hard, 10=smooth)",
            'opacity': "Blend with original (0=original, 10=full ripple)",
        }

        # Sweet spots
        self._sweet_spots = {
            'amplitude': [2.0, 5.0, 8.0],
            'wavelength': [3.0, 4.0, 6.0],
            'frequency': [1.0, 2.0, 4.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None, 
              chain = None) -> int:
        """
        Render ripple-distorted version of input texture.
        
        Args:
            tex_in: Input texture (required).
            extra_textures: Optional additional textures.
            chain: Rendering chain context.
            
        Returns:
            Output texture with ripple distortion applied.
        """
        # Update ripple center from parameters
        # Bind input texture
        # Apply radial distortion via fragment shader
        # Composite result with opacity blending
        # Return output texture
        pass

    def compute_ripple_displacement(self, distance: float, time: float,
                                   frequency: float, wavelength: float,
                                   amplitude: float, dampening: float) -> float:
        """
        Compute radial displacement at distance from ripple center.
        
        Args:
            distance: Distance from ripple center (pixels).
            time: Current time (seconds).
            frequency: Ripple propagation frequency.
            wavelength: Distance between peaks.
            amplitude: Displacement magnitude.
            dampening: Decay factor.
            
        Returns:
            Radial displacement in pixels.
        """
        # Compute ripple phase based on distance and time
        # Apply oscillation
        # Apply dampening decay
        # Return displacement
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms for ripple animation.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input (unused).
            semantic_layer: Optional semantic input (unused).
        """
        # Update ripple center from parameters
        # Bind ripple parameters to uniforms
        # Compute time-dependent animation
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `amplitude` (float, UI 0—10) → internal `A` = map_linear(x, 0,10, 0.0, 150.0)
  - Ripple displacement in pixels [0, 150]
- `wavelength` (float, UI 0—10) → internal `λ` = map_linear(x, 0,10, 20.0, 500.0)
  - Distance between ripple peaks in pixels [20, 500]
- `frequency` (float, UI 0—10) → internal `f` = map_linear(x, 0,10, 0.5, 10.0)
  - Ripple propagation frequency (Hz) [0.5, 10.0]
- `ripple_mode` (int, UI 0—10) → internal mode:
  - 0–2: Expanding (ripples move outward)
  - 3–7: Pulsing (ripples pulse at center)
  - 8–10: Contracting (ripples move inward)
- `center_x` (float, UI 0—10) → internal `cx` = x / 10.0
  - Ripple center X coordinate [0, 1] (normalized)
- `center_y` (float, UI 0—10) → internal `cy` = x / 10.0
  - Ripple center Y coordinate [0, 1] (normalized)
- `dampening` (float, UI 0—10) → internal `d` = map_linear(x, 0,10, 0.0, 0.05)
  - Decay factor per pixel [0, 0.05]
- `phase` (float, UI 0—10) → internal `φ` = (x / 10.0) * 2π
  - Phase offset in radians [0, 2π]
- `edge_blend` (float, UI 0—10) → internal `edge` = map_linear(x, 0,10, 0.0, 0.5)
  - Falloff smoothness [0, 0.5]
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Blend factor [0, 1.0]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float amplitude;`        // ripple height
- `uniform float wavelength;`       // peak distance
- `uniform float frequency;`        // propagation speed
- `uniform int ripple_mode;`        // style selection
- `uniform vec2 center;`            // ripple source (normalized)
- `uniform float dampening;`        // decay factor
- `uniform float phase;`            // phase offset
- `uniform float edge_blend;`       // smoothness at edges
- `uniform float opacity;`          // blend factor
- `uniform float time;`             // elapsed time
- `uniform vec2 resolution;`        // screen size
- `uniform sampler2D tex_in;`       // input texture

## Effect Math (concise, GPU/CPU-consistent)

### 1) Distance Computation

For each pixel at coordinates `(px, py)` (normalized 0—1):

```
// Ripple center (normalized, from parameters)
cx = center_x / 10
cy = center_y / 10

// Distance from pixel to ripple center (in normalized space)
dx = px - cx
dy = py - cy
distance = sqrt(dx^2 + dy^2)

// Convert to pixel distance for amplitude scaling
pixel_distance = distance * max(resolution.x, resolution.y)
```

### 2) Ripple Wave Function

Compute ripple phase and oscillation:

```
// Ripple wave: sin(frequency * time - wavelength * distance)
// Minus sign: expanding ripples
// Plus sign: contracting ripples

if ripple_mode == 0:          // EXPANDING
    wave_arg = frequency * time - pixel_distance / wavelength
elif ripple_mode == 1:        // PULSING
    wave_arg = frequency * time - pixel_distance / wavelength
    // Apply phase offset for pulsing effect
    wave_arg = wave_arg + sin(frequency * time)
else:                         // CONTRACTING
    wave_arg = frequency * time + pixel_distance / wavelength

ripple_wave = sin(wave_arg * 2π + phase)
```

### 3) Dampening and Falloff

Apply decay over distance:

```
// Exponential dampening
decay = exp(-dampening * pixel_distance)

// Edge falloff (smooth transition)
edge_factor = 1.0 - smoothstep(0.4, 1.0, distance)
// Adjust 0.4—1.0 range by edge_blend parameter

// Combined: wave modulated by decay and edge
modulated_wave = ripple_wave * decay * edge_factor
```

### 4) Displacement Vector

Convert wave value to displacement:

```
// Compute direction from center to pixel
dir = normalize(vec2(dx, dy))

// Displacement magnitude
displacement_magnitude = amplitude * modulated_wave

// Displacement vector (radial)
displacement = dir * displacement_magnitude

// Add refraction component (optional)
// Refraction bends ray towards/away from center
// refraction = refraction_strength * ripple_wave * dir
```

### 5) Texture Sampling at Displaced Position

Sample from input texture at perturbed coordinates:

```
// Original coordinates (pixel space)
uv_original = vec2(px, py)

// Perturbed coordinates (add displacement)
uv_displaced = uv_original + displacement

// Clamp or wrap
uv_displaced = clamp(uv_displaced, 0, 1)

// Sample with filtering
color = texture(tex_in, uv_displaced)

// Blend with original
color_out = mix(color_original, color, opacity)
```

## CPU Fallback (NumPy sketch)

```python
def ripple_cpu(frame, time, amplitude, wavelength, frequency, 
              center_x, center_y, dampening, opacity):
    """Apply ripple distortion on CPU."""
    
    h, w = frame.shape[:2]
    output = np.zeros_like(frame)
    
    # Normalized center
    cy = center_y / 10.0
    cx = center_x / 10.0
    
    # Build meshgrid
    yy = np.arange(h) / h  # normalized y
    xx = np.arange(w) / w  # normalized x
    YY, XX = np.meshgrid(yy, xx, indexing='ij')
    
    # Distance from center
    dx = XX - cx
    dy = YY - cy
    distances = np.sqrt(dx**2 + dy**2)
    pixel_distances = distances * max(h, w)
    
    # Ripple wave
    wave = np.sin(frequency * time * 2*np.pi - pixel_distances / wavelength * 2*np.pi)
    
    # Dampening
    decay = np.exp(-dampening * pixel_distances)
    
    # Combined wave
    modulated = wave * decay
    
    # Displacement
    magnitude = amplitude * modulated
    
    # Direction (avoid division by zero)
    with np.errstate(divide='ignore', invalid='ignore'):
        dir_norm = np.sqrt(dx**2 + dy**2)
        dir_norm[dir_norm == 0] = 1.0
        dir_x = dx / dir_norm
        dir_y = dy / dir_norm
    
    # Displace coordinates
    disp_x = (xx + dir_x * magnitude / w) * w
    disp_y = (yy + dir_y * magnitude / h) * h
    
    # Interpolate
    disp_x = np.clip(disp_x, 0, w - 1).astype(int)
    disp_y = np.clip(disp_y, 0, h - 1).astype(int)
    
    output = frame[disp_y, disp_x]
    
    # Blend
    result = (1 - opacity) * frame + opacity * output
    return result.astype(np.uint8)
```

## Presets (recommended)
- `Gentle Drop`:
  - `amplitude` 3.0, `wavelength` 6.0, `frequency` 1.0, `dampening` 4.0,
    `ripple_mode` 0.0 (expanding), `opacity` 5.0
- `Fast Pulse`:
  - `amplitude` 5.0, `wavelength` 4.0, `frequency` 3.0, `dampening` 2.0,
    `ripple_mode` 5.0 (pulsing), `center_x` 5.0, `center_y` 5.0, `opacity` 8.0
- `Turbulent Wave`:
  - `amplitude` 7.0, `wavelength` 3.0, `frequency` 4.0, `dampening` 1.0,
    `ripple_mode` 0.0 (expanding), `opacity` 10.0, `edge_blend` 2.0
- `Corner Source`:
  - `amplitude` 4.0, `wavelength` 5.0, `frequency` 2.0, `dampening` 3.0,
    `ripple_mode` 0.0 (expanding), `center_x` 1.0, `center_y` 1.0 (top-left),
    `opacity` 6.0

## Edge Cases and Error Handling
- **Wavelength = 0**: Clamp to minimum (20 pixels) to avoid division by zero.
- **Frequency = 0**: No animation; static wave pattern.
- **Amplitude = 0**: No distortion; pass through original.
- **Center outside bounds**: Still compute ripples; allow center to be off-screen.
- **Distance = 0**: Avoid NaN in direction vectorization; use default direction.
- **Invalid ripple_mode**: Default to expanding.

## Test Plan (minimum ≥80% coverage)
- `test_distance_computation` — distance from center computed correctly
- `test_ripple_wave_expanding` — expanding ripples move outward over time
- `test_ripple_wave_pulsing` — pulsing ripples oscillate at center
- `test_ripple_wave_contracting` — contracting ripples move inward
- `test_amplitude_scaling` — displacement scales with amplitude
- `test_wavelength_period` — wavelength controls peak spacing
- `test_frequency_animation` — frequency controls propagation speed
- `test_dampening_decay` — amplitude decays with distance
- `test_edge_blend_falloff` — ripple smooths at screen edges
- `test_center_positioning` — center_x/y control ripple source
- `test_opacity_blending` — opacity correctly blends with original
- `test_offset_center` — ripples work correctly from non-center sources
- `test_cpu_vs_gpu_parity` — CPU and GPU outputs match within tolerance
- `test_performance_60fps` — sustain ≥60 FPS at 1080p with default settings
- `test_no_artifacts` — no NaN or out-of-bounds artifacts

## Verification Checkpoints
- [ ] `RippleEffect` class registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly to shader uniforms
- [ ] Ripple center positioning works (center_x, center_y)
- [ ] Ripple modes work (expanding, pulsing, contracting)
- [ ] Ripple displacement applies and animates correctly
- [ ] Dampening causes ripples to fade with distance
- [ ] Edge blending smooths ripple falloff
- [ ] CPU fallback produces rippled output without crashing
- [ ] Presets render at intended visual styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p with typical settings
- [ ] Visual output matches vjlive reference implementation

## Implementation Handoff Notes
- Performance optimization:
  - Pre-compute distance field (distance from center per pixel)
  - Update only when center moves or resolution changes
  - Use 1D wave lookup table for wave computation
  
- GPU optimization:
  - Use fragment shader with built-in distance functions
  - Avoid expensive sqrt() operations; use squared distances where possible
  
- CPU optimization:
  - Vectorize with NumPy meshgrid for fast distance field
  - Use scipy.ndimage.map_coordinates for bilinear interpolation
  
- Numerical stability:
  - Guard against division by zero when distance = 0
  - Clamp pixel coordinates before indexing frame buffer

## Resources
- Reference: vjlive, Resolume, TouchDesigner ripple effects
- Math: Circular wave propagation, radial distance, exponential decay
- GPU: GLSL fragment shaders, normalize() function, smoothstep()

````
