````markdown
# P7-VE05: Spiral Wave Effect (Logarithmic Spiral Distortion)

> **Task ID:** `P7-VE05`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/v_sws.py`)
> **Class:** `SpiralWaveEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `SpiralWaveEffect`—a 2D spatial
distortion effect that spirals image content outward from a center point using
logarithmic spiral geometry. The effect warps pixels along spiral trajectories,
creating vortex-like, whirling visual deformations. The objective is to document
exact spiral mathematics, parameter remaps, polar-to-Cartesian mapping, CPU
fallback, and comprehensive tests for feature parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (processes incoming video)
- Sustain 60 FPS with real-time spiral distortion (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful fallback without distortion if disabled (Safety Rail 7)
- CPU fallback implementation for compatibility testing

## Implementation Notes / Porting Strategy
1. Convert image to polar coordinates centered at spiral origin.
2. Apply logarithmic spiral transformation in polar space.
3. Apply rotation and scaling based on distance from spiral center.
4. Convert back to Cartesian coordinates for display.
5. Support multiple spiral modes (arithmetic, logarithmic, fermat).
6. Provide NumPy-based CPU fallback (frame remapping).

## Public Interface
```python
class SpiralWaveEffect(Effect):
    """
    Spiral Wave Effect: Logarithmic spiral spatial distortion.
    
    Distorts image content by warping pixels along logarithmic spiral
    trajectories emanating from a center point. Creates vortex, whirlpool,
    and tunnel-like visual effects. Common in VJ performance for dynamic
    and hypnotic visual transformations.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 use_gpu: bool = True):
        """
        Initialize the spiral wave effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU polar transforms; else CPU remapping.
        """
        super().__init__("Spiral Wave Effect", SPIRAL_VERTEX_SHADER, 
                         SPIRAL_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "distortion"
        self.effect_tags = ["spiral", "vortex", "polar", "distortion"]
        self.features = ["POLAR_DISTORTION", "SPIRAL_ANIMATION"]
        self.usage_tags = ["HYPNOTIC", "VORTEX", "KINETIC"]
        
        self.use_gpu = use_gpu
        self.spiral_center = [0.5, 0.5]  # normalized: (0—1, 0—1)

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'spiral_intensity': (0.0, 10.0),    # curvature factor
            'rotation_speed': (0.0, 10.0),      # angular velocity
            'expansion': (0.0, 10.0),           # radial growth rate
            'spiral_mode': (0.0, 10.0),         # arithmetic, log, fermat
            'center_x': (0.0, 10.0),            # spiral origin X
            'center_y': (0.0, 10.0),            # spiral origin Y
            'frequency': (0.0, 10.0),           # wave oscillation
            'phase': (0.0, 10.0),               # temporal phase
            'zoom': (0.0, 10.0),                # spiral magnification
            'opacity': (0.0, 10.0),             # blending with original
        }

        # Default parameter values
        self.parameters = {
            'spiral_intensity': 5.0,
            'rotation_speed': 3.0,
            'expansion': 2.0,
            'spiral_mode': 5.0,                 # logarithmic by default
            'center_x': 5.0,                    # screen center
            'center_y': 5.0,                    # screen center
            'frequency': 2.0,
            'phase': 0.0,
            'zoom': 5.0,
            'opacity': 8.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'spiral_intensity': "Spiral curvature (0=straight, 10=tight)",
            'rotation_speed': "Angular velocity (0=static, 10=fast)",
            'expansion': "Radial growth rate (0=none, 10=extreme)",
            'spiral_mode': "0=arithmetic, 5=logarithmic, 10=fermat",
            'center_x': "Spiral origin X (0=left, 10=right)",
            'center_y': "Spiral origin Y (0=top, 10=bottom)",
            'frequency': "Wave oscillation frequency (0=none, 10=fast)",
            'phase': "Temporal phase offset (0—360°)",
            'zoom': "Spiral magnification (0.1—2.0x)",
            'opacity': "Blend with original (0=original, 10=full spiral)",
        }

        # Sweet spots
        self._sweet_spots = {
            'spiral_intensity': [2.0, 5.0, 8.0],
            'rotation_speed': [1.0, 3.0, 6.0],
            'expansion': [1.0, 2.0, 4.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None, 
              chain = None) -> int:
        """
        Render spiral-distorted version of input texture.
        
        Args:
            tex_in: Input texture (required).
            extra_textures: Optional additional textures.
            chain: Rendering chain context.
            
        Returns:
            Output texture with spiral distortion applied.
        """
        # Update spiral center from parameters
        # Bind input texture
        # Apply polar→spiral→cartesian transform
        # Composite result with opacity blending
        # Return output texture
        pass

    def cartesian_to_polar(self, x: float, y: float, 
                          center_x: float, center_y: float) -> tuple:
        """
        Convert Cartesian coordinates to polar (angle, radius).
        
        Args:
            x, y: Cartesian pixel position.
            center_x, center_y: Spiral center.
            
        Returns:
            Tuple of (angle, radius) in polar space.
        """
        dx = x - center_x
        dy = y - center_y
        angle = atan2(dy, dx)
        radius = sqrt(dx**2 + dy**2)
        return angle, radius

    def apply_spiral_transform(self, angle: float, radius: float, 
                              intensity: float, rotation: float,
                              expansion: float) -> tuple:
        """
        Apply logarithmic spiral transformation in polar space.
        
        Args:
            angle: Current angle (radians).
            radius: Current radius (pixels).
            intensity: Spiral curvature factor.
            rotation: Angular rotation (radians/second * time).
            expansion: Radial growth rate.
            
        Returns:
            Transformed (angle, radius).
        """
        # Apply temporal rotation
        # Apply spiral curvature (spiral_angle = intensity * ln(radius))
        # Apply radial expansion
        # Return new (angle, radius)
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms for spiral animation.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input (unused).
            semantic_layer: Optional semantic input (unused).
        """
        # Update spiral center
        # Compute time-dependent rotation
        # Bind uniforms to shader
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `spiral_intensity` (float, UI 0—10) → internal `S` = map_linear(x, 0,10, 0.0, 2.0)
  - Spiral curvature factor [0, 2.0]
- `rotation_speed` (float, UI 0—10) → internal `ω` = map_linear(x, 0,10, 0.0, 5.0)
  - Angular velocity (radians/second) [0, 5π rad/s]
- `expansion` (float, UI 0—10) → internal `e` = map_linear(x, 0,10, 0.0, 0.5)
  - Radial growth rate per radian [0, 0.5]
- `spiral_mode` (int, UI 0—10) → internal mode:
  - 0–2: Arithmetic (radius = a*θ)
  - 3–7: Logarithmic (radius = a*ln(θ))
  - 8–10: Fermat (radius = a*√θ)
- `center_x` (float, UI 0—10) → internal `cx` = x / 10.0
  - Spiral center X [0, 1] (normalized)
- `center_y` (float, UI 0—10) → internal `cy` = x / 10.0
  - Spiral center Y [0, 1] (normalized)
- `frequency` (float, UI 0—10) → internal `f` = map_linear(x, 0,10, 0.0, 5.0)
  - Wave frequency (Hz) [0, 5]
- `phase` (float, UI 0—10) → internal `φ` = (x / 10.0) * 2π
  - Phase offset [0, 2π]
- `zoom` (float, UI 0—10) → internal `z` = map_linear(x, 0,10, 0.1, 2.0)
  - Spiral magnification [0.1, 2.0]
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Blend factor [0, 1]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float spiral_intensity;`   // curvature factor
- `uniform float rotation_speed;`     // angular velocity
- `uniform float expansion;`          // radial growth
- `uniform int spiral_mode;`          // transformation type
- `uniform vec2 center;`              // spiral origin (normalized)
- `uniform float frequency;`          // oscillation frequency
- `uniform float phase;`              // phase offset
- `uniform float zoom;`               // magnification
- `uniform float opacity;`            // blend factor
- `uniform float time;`               // elapsed time
- `uniform vec2 resolution;`          // screen size
- `uniform sampler2D tex_in;`         // input texture

## Effect Math (concise, GPU/CPU-consistent)

### 1) Cartesian to Polar Conversion

For each pixel at `(x, y)`, convert to polar around spiral center:

```
// Spiral center (normalized)
cx = center_x / 10
cy = center_y / 10

// Relative position
dx = x - cx
dy = y - cy

// Polar coordinates
angle = atan2(dy, dx)           // radians, [-π, π]
radius = sqrt(dx^2 + dy^2)

// Normalize radius by screen diagonal for scale independence
max_dist = sqrt(0.5^2 + 0.5^2)
radius_normalized = radius / max_dist
```

### 2) Spiral Transformation (Polar Space)

Apply spiral distortion based on mode:

```
// Temporal rotation
angle_rotated = angle + rotation_speed * time

// Spiral curvature (different modes)
if spiral_mode == 0:            // ARITHMETIC SPIRAL
    theta_sp = spiral_intensity * radius_normalized
elif spiral_mode == 1:          // LOGARITHMIC SPIRAL
    // Logarithmic: r = a * e^(θ*b)
    theta_sp = spiral_intensity * ln(radius_normalized + 1.0)
else:                           // FERMAT SPIRAL
    // Fermat: r = a * sqrt(θ)
    theta_sp = spiral_intensity * sqrt(radius_normalized)

// Apply expansion (radial growth)
radius_expanded = radius_normalized * (1.0 + expansion * angle_rotated)

// Oscillation (optional)
oscillation = 1.0 + 0.2 * sin(frequency * time * 2π + phase)
radius_final = radius_expanded * oscillation

// Apply zoom
radius_final = radius_final * zoom
```

### 3) Anomaly Angle Computation

In logarithmic spiral, the anomaly angle differs from the geometric angle:

```
// Logarithmic anomaly angle
if spiral_mode == 1:
    // θ' = θ + arctan(1 / spiral_intensity)
    anomaly_offset = atan(1.0 / max(spiral_intensity, 0.01))
    angle_final = angle_rotated + theta_sp + anomaly_offset
else:
    angle_final = angle_rotated + theta_sp
```

### 4) Polar to Cartesian Conversion

Convert back to Cartesian, clamping to valid bounds:

```
// Cartesian from polar
x_new = cx + radius_final * cos(angle_final)
y_new = cy + radius_final * sin(angle_final)

// Clamp to texture bounds
x_new = clamp(x_new, 0, 1)
y_new = clamp(y_new, 0, 1)
```

### 5) Texture Sampling

Sample from input at transformed coordinates:

```
// Bilinear interpolation for smoothness
color = texture_bilinear(tex_in, x_new, y_new)

// Blend with original
color_out = mix(color_original, color, opacity)
```

## CPU Fallback (NumPy sketch)

```python
def spiral_cpu(frame, time, spiral_intensity, rotation_speed, 
              expansion, spiral_mode, center_x, center_y, zoom):
    """Apply spiral distortion on CPU."""
    
    h, w = frame.shape[:2]
    output = np.zeros_like(frame)
    
    # Normalized center
    cy = center_y / 10.0
    cx = center_x / 10.0
    
    # Build meshgrid
    yy = np.arange(h) / h
    xx = np.arange(w) / w
    YY, XX = np.meshgrid(yy, xx, indexing='ij')
    
    # Convert to polar
    dx = XX - cx
    dy = YY - cy
    angles = np.arctan2(dy, dx)
    radii = np.sqrt(dx**2 + dy**2)
    max_dist = np.sqrt(0.5**2 + 0.5**2)
    radii_norm = radii / max_dist
    
    # Temporal rotation
    angles_rot = angles + rotation_speed * time
    
    # Spiral transformation
    if spiral_mode == 0:  # Arithmetic
        theta_sp = spiral_intensity * radii_norm
    else:  # Logarithmic
        theta_sp = spiral_intensity * np.log(radii_norm + 1.0)
    
    # Expansion
    radii_exp = radii_norm * (1.0 + expansion * angles_rot)
    
    # Zoom
    radii_final = radii_exp * zoom
    
    # Back to Cartesian
    angles_final = angles_rot + theta_sp
    xx_new = cx + radii_final * np.cos(angles_final)
    yy_new = cy + radii_final * np.sin(angles_final)
    
    # Clamp and convert to indices
    xx_new = np.clip(xx_new, 0, 1) * (w - 1)
    yy_new = np.clip(yy_new, 0, 1) * (h - 1)
    
    xx_idx = np.clip(xx_new.astype(int), 0, w - 1)
    yy_idx = np.clip(yy_new.astype(int), 0, h - 1)
    
    output = frame[yy_idx, xx_idx]
    return output.astype(np.uint8)
```

## Presets (recommended)
- `Gentle Swirl`:
  - `spiral_intensity` 2.0, `rotation_speed` 1.0, `expansion` 1.0,
    `spiral_mode` 5.0 (logarithmic), `center_x` 5.0, `center_y` 5.0, `opacity` 6.0
- `Fast Vortex`:
  - `spiral_intensity` 5.0, `rotation_speed` 4.0, `expansion` 2.0,
    `spiral_mode` 5.0 (logarithmic), `opacity` 8.0, `zoom` 6.0
- `Hypnotic Tunnel`:
  - `spiral_intensity` 4.0, `rotation_speed` 2.0, `expansion` 3.0,
    `spiral_mode` 5.0 (logarithmic), `frequency` 2.0, `opacity` 10.0
- `Arithmetic Spiral`:
  - `spiral_intensity` 3.0, `rotation_speed` 2.0, `expansion` 1.0,
    `spiral_mode` 0.0 (arithmetic), `opacity` 7.0

## Edge Cases and Error Handling
- **Radius = 0 (at center)**: Use default angle to avoid atan2(0,0) NaN.
- **Negative spiral_intensity**: Use absolute value.
- **Rotation_speed = 0**: No animation; static spiral.
- **Expansion = 0**: Spiral doesn't grow; simple rotation.
- **Off-center spiral**: Allow center anywhere on- or off-screen.
- **Invalid spiral_mode**: Default to logarithmic.

## Test Plan (minimum ≥80% coverage)
- `test_cartesian_to_polar` — coordinate conversion correct
- `test_polar_to_cartesian` — inverse conversion correct
- `test_arithmetic_spiral` — arithmetic spiral geometry correct
- `test_logarithmic_spiral` — logarithmic spiral geometry correct
- `test_fermat_spiral` — Fermat spiral geometry correct
- `test_rotation_speed` — angular rotation animates correctly
- `test_expansion_growth` — radial growth increases with expansion
- `test_zoom_scaling` — zoom parameter scales spiral correctly
- `test_center_positioning` — spiral origin positions correctly
- `test_frequency_oscillation` — frequency modulates radius
- `test_opacity_blending` — opacity blends with original
- `test_cpu_vs_gpu_parity` — CPU and GPU match within tolerance
- `test_performance_60fps` — sustain ≥60 FPS at 1080p
- `test_no_nan_inf` — no NaN/Inf output artifacts

## Verification Checkpoints
- [ ] `SpiralWaveEffect` registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly
- [ ] Spiral center positioning works (center_x, center_y)
- [ ] Spiral modes render distinctly (arithmetic, log, Fermat)
- [ ] Rotation animates spiral correctly over time
- [ ] Expansion causes radius growth with angle
- [ ] Frequency and phase modulate spiral correctly
- [ ] CPU fallback produces spiral output without crash
- [ ] Presets render at intended visual styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p
- [ ] Output matches vjlive reference

## Implementation Handoff Notes
- Performance optimization:
  - Pre-compute logarithms for radii (use lookup table if possible)
  - Cache atan2 results for common angles
  
- GPU optimization:
  - Use GLSL atan() and log() built-ins (highly optimized)
  - Consider separating polar→spiral and spiral→Cartesian into separate passes
  
- CPU optimization:
  - Vectorize all operations with NumPy
  - Use scipy bilinear interpolation for sampling
  
- Numerical stability:
  - Clamp radius to avoid log(0)
  - Guard against division by zero in atan2

## Resources
- Reference: vjlive, Resolume, TouchDesigner spiral/vortex effects
- Math: Logarithmic spirals (Bernoulli), polar coordinates, anomaly angles
- GPU: GLSL log(), pow(), atan2(), trigonometric functions

````
