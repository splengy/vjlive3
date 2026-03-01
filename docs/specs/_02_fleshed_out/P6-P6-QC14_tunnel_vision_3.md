````markdown
# P6-QC14: Tunnel Vision Effect (Quantum Consciousness Singularity)

> **Task ID:** `P6-QC14`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/vdepth/tunnel_vision_3.py`)
> **Class:** `QuantumConsciousnessSingularityEffect`
> **Phase:** Phase 6
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete, unambiguous Pass 2 specification for the `QuantumConsciousnessSingularityEffect`—
a distortion-based visual effect that creates a tunnel or vortex by warping input coordinates
using polar/logarithmic space transformations and time-based animations. The effect simulates
a "tunnel toward consciousness" or singularity pull, often with swirling distortion and
recursive depth layering. The objective is to document the exact coordinate warping math,
animation equations, parameter remaps, presets, CPU fallback, and comprehensive tests for
feature parity with VJLive-2.

## Technical Requirements
- Implement as a VJLive3 effect plugin (processes input video)
- Sustain smooth 60 FPS distortion rendering (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful fallback to CPU-based coordinate remapping (Safety Rail 7)
- No silent failures; handle edge cases (center singularity, coordinate overflow) correctly

## Implementation Notes / Porting Strategy
1. Implement polar coordinate transformation (Cartesian → polar, then back).
2. Add logarithmic spiral warping for vortex effect.
3. Apply time-based rotation and scaling animations.
4. Support multiple distortion modes (tunnel, vortex, kaleidoscope, wormhole).
5. Provide deterministic NumPy-based CPU fallback (coordinate remapping + interpolation).
6. Include optional depth-based weighting if depth texture available.

## Public Interface
```python
class QuantumConsciousnessSingularityEffect(Effect):
    """
    Quantum consciousness singularity: tunnel/vortex distortion effect.
    
    Warps coordinates using polar space transformations, creating a tunnel
    or swirling vortex effect with recursive depth animation. Often used for
    transitions and consciousness-themed visualizations.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 use_gpu: bool = True):
        """
        Initialize the tunnel vision effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU distortion; else CPU remapping.
        """
        super().__init__("Tunnel Vision", TUNNEL_VERTEX_SHADER, 
                         TUNNEL_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "distortion"
        self.effect_tags = ["warp", "tunnel", "vortex", "singularity"]
        self.features = ["COORDINATE_TRANSFORMATION", "ANIMATED_DISTORTION"]
        self.usage_tags = ["PROCESSES_VIDEO", "DEPTH_AWARE"]
        
        self.use_gpu = use_gpu
        self.distortion_lut = None       # Optional pre-computed LUT for CPU path

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'tunnel_intensity': (0.0, 10.0),   # distortion strength
            'rotation_speed': (0.0, 10.0),     # spiral rotation rate
            'zoom_factor': (0.0, 10.0),        # center zoom depth
            'spiral_tightness': (0.0, 10.0),   # logarithmic spiral parameter
            'kaleidoscope_segments': (0.0, 10.0),  # number of symmetry folds
            'depth_influence': (0.0, 10.0),    # depth map weighting (if available)
            'glow_amount': (0.0, 10.0),        # center glow intensity
            'aberration': (0.0, 10.0),         # chromatic aberration
            'recursion_depth': (0.0, 10.0),    # nested tunnel iterations
            'edge_clamp': (0.0, 10.0),         # behavior at screen edges
        }

        # Default parameter values
        self.parameters = {
            'tunnel_intensity': 5.0,
            'rotation_speed': 3.0,
            'zoom_factor': 4.0,
            'spiral_tightness': 4.0,
            'kaleidoscope_segments': 0.0,     # disabled by default
            'depth_influence': 2.0,
            'glow_amount': 2.0,
            'aberration': 1.0,
            'recursion_depth': 2.0,
            'edge_clamp': 5.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'tunnel_intensity': "Distortion strength (0=no effect, 10=extreme warping)",
            'rotation_speed': "Spiral rotation rate (0=static, 10=fast spin)",
            'zoom_factor': "Inward zoom at center (0=no zoom, 10=deep tunnel)",
            'spiral_tightness': "Log spiral coil tightness (0=loose, 10=tight)",
            'kaleidoscope_segments': "Symmetry folds (0=disabled, 10=many folds)",
            'depth_influence': "How depth map weights distortion (0=ignores, 10=full)",
            'glow_amount': "Center glow bloom (0=none, 10=intense)",
            'aberration': "Chromatic aberration (0=none, 10=strong separation)",
            'recursion_depth': "Nested tunnel iterations (0=single, 10=deeply recursive)",
            'edge_clamp': "Edge behavior: 0=wrap, 5=clamp, 10=mirror"
        }

        # Sweet spots
        self._sweet_spots = {
            'tunnel_intensity': [2.0, 5.0, 8.0],
            'rotation_speed': [1.0, 3.0, 6.0],
            'zoom_factor': [2.0, 4.0, 7.0]
        }

    def render(self, tex_in: int, extra_textures: list = None, 
              chain = None) -> int:
        """
        Apply tunnel/vortex distortion to input texture.
        
        Args:
            tex_in: Input video texture handle.
            extra_textures: Optional (depth texture for depth-aware warping).
            chain: Rendering chain context.
            
        Returns:
            Output texture handle with tunnel effect applied.
        """
        # Compute per-fragment warped coordinates
        # Sample from input at warped location
        # Apply glow, aberration, optional depth influence
        # Return distorted result
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms and time-based animations.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio for parameter modulation.
            semantic_layer: Optional semantic input.
        """
        # Map UI parameters to internal values
        # Compute animated rotation and zoom
        # Bind uniforms to GPU
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `tunnel_intensity` (float, UI 0—10) → internal `I` = map_linear(x, 0,10, 0.0, 2.0)
  - Distortion strength multiplier (2.0 = strong warping)
- `rotation_speed` (float, UI 0—10) → internal `ω` = map_linear(x, 0,10, 0.0, 6.28)
  - Spiral rotation rate in radians/sec (6.28 = 1 full rotation/sec)
- `zoom_factor` (float, UI 0—10) → internal `Z` = map_linear(x, 0,10, 1.0, 10.0)
  - Depth scaling toward center (1.0 = no zoom, 10.0 = extreme zoom)
- `spiral_tightness` (float, UI 0—10) → internal `τ` = map_linear(x, 0,10, 0.1, 2.0)
  - Logarithmic spiral coil parameter (higher = tighter spirals)
- `kaleidoscope_segments` (int, UI 0—10) → internal `K` = round(x * 1.6)
  - Number of symmetry folds (0=disabled, 16=many reflections)
- `depth_influence` (float, UI 0—10) → internal `D` = x / 10.0
  - Depth-based weighting [0, 1]
- `glow_amount` (float, UI 0—10) → internal `G` = map_linear(x, 0,10, 0.0, 1.0)
  - Center glow intensity [0, 1]
- `aberration` (float, UI 0—10) → internal `A` = map_linear(x, 0,10, 0.0, 0.05)
  - Chromatic aberration offset (normalized; 0.05 = 5% shift)
- `recursion_depth` (int, UI 0—10) → internal `R` = round(x)
  - Number of nested recursion iterations (0—10)
- `edge_clamp` (float, UI 0—10) → internal mode:
  - 0—3: Wrap (repeating texture)
  - 4—6: Clamp (edge pixels repeated)
  - 7—10: Mirror (reflected edges)

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float tunnel_intensity;`     // distortion strength
- `uniform float rotation_speed;`       // spiral rotation (rad/sec)
- `uniform float zoom_factor;`          // depth scaling
- `uniform float spiral_tightness;`     // log spiral coil
- `uniform int kaleidoscope_segments;`  // symmetry folds
- `uniform float depth_influence;`      // depth weighting
- `uniform float glow_amount;`          // center bloom
- `uniform float aberration;`           // chromatic offset
- `uniform int recursion_depth;`        // nested iterations
- `uniform int edge_mode;`              // wrap/clamp/mirror
- `uniform float time;`                 // elapsed time for animation
- `uniform sampler2D tex_input;`        // input video
- `uniform sampler2D tex_depth;`        // optional depth (if available)

## Effect Math (concise, GPU/CPU-consistent)

All math is written to be implementable identically in GLSL and NumPy via
bilinear interpolation for CPU path.

### 1) Coordinate Transformation: Cartesian to Polar

Convert screen coordinates to polar space for distortion:

```
// Normalize to [-1, 1] around center
coord_centered = (fragCoord / resolution) * 2.0 - 1.0

// Cartesian to polar
r = length(coord_centered)
theta = atan(coord_centered.y, coord_centered.x)
```

### 2) Polar-Space Distortion (Tunnel/Vortex)

In polar space, apply distortion:

a) **Basic tunnel (zoom)**:
```
r_distorted = r * zoom_factor + tunnel_intensity * sin(theta * 3.0)
```

b) **Logarithmic spiral (vortex)**:
```
theta_spiral = theta + spiral_tightness * log(r + 0.1)
theta_distorted = theta_spiral + rotation_speed * time
r_distorted = r * zoom_factor
```

c) **Kaleidoscope symmetry** (if enabled):
```
theta_reflected = fmod(theta, 2π / kaleidoscope_segments)
// Use reflected theta in distortion
```

### 3) Animation: Rotation

Rotate tunnel over time:

```
theta_animated = theta_distorted + rotation_speed * time
```

### 4) Back to Cartesian

Convert distorted polar coordinates back:

```
uv_warped = polar_to_cartesian(r_distorted, theta_animated)
uv_warped = (uv_warped + 1.0) / 2.0  // back to [0, 1]
```

### 5) Chromatic Aberration (Optional)

Sample R, G, B at slightly offset positions:

```
offset_r = vec2(+aberration, 0)
offset_g = vec2(0, 0)
offset_b = vec2(-aberration, 0)

color_r = sample_texture(tex_input, uv_warped + offset_r).r
color_g = sample_texture(tex_input, uv_warped + offset_g).g
color_b = sample_texture(tex_input, uv_warped + offset_b).b

color_out = vec3(color_r, color_g, color_b)
```

### 6) Center Glow

Add bloom at center:

```
if glow_amount > 0:
    center_distance = length(coord_centered)
    glow_factor = glow_amount / (center_distance + 0.1)
    color_out += color_out * glow_factor
```

### 7) Depth-Based Weighting (Optional)

If depth texture available:

```
depth = sample_texture(tex_depth, original_uv)
depth_weight = 1.0 + depth_influence * (depth - 0.5)
tunnel_intensity *= depth_weight
```

### 8) Recursion (Optional)

Apply coordinate transformation recursively:

```
for i in range(recursion_depth):
    r_distorted = apply_transform(r_distorted, theta_distorted, time * (i+1))
    theta_distorted = update_theta(theta_distorted, time)
```

## CPU Fallback (NumPy sketch)

```python
def tunnel_vision_cpu(frame, time, tunnel_intensity, rotation_speed, 
                      zoom_factor, spiral_tightness, aberration):
    """Apply tunnel distortion via coordinate remapping on CPU."""
    
    h, w = frame.shape[:2]
    center = np.array([w/2, h/2])
    
    # Create output
    output = np.zeros_like(frame)
    
    # Per-pixel coordinate remapping
    for y in range(h):
        for x in range(w):
            # Normalize to [-1, 1]
            coord = np.array([x, y]) - center
            coord = coord / (np.array([w, h]) / 2)
            
            # Cartesian to polar
            r = np.linalg.norm(coord)
            theta = np.arctan2(coord[1], coord[0])
            
            # Apply distortion
            theta_dist = theta + spiral_tightness * np.log(r + 0.1)
            theta_anim = theta_dist + rotation_speed * time
            r_dist = r * zoom_factor
            
            # Back to Cartesian
            uv_warped = np.array([r_dist * np.cos(theta_anim),
                                  r_dist * np.sin(theta_anim)])
            
            # Back to pixel coords
            uv_pixel = (uv_warped + 1.0) / 2.0 * np.array([w, h])
            
            # Bilinear interpolation
            if 0 <= uv_pixel[0] < w-1 and 0 <= uv_pixel[1] < h-1:
                output[y, x] = bilinear_sample(frame, uv_pixel)
    
    return output.astype(np.uint8)
```

## Presets (recommended)
- `Gentle Vortex`:
  - `tunnel_intensity` 2.0, `rotation_speed` 1.0, `zoom_factor` 2.0,
    `spiral_tightness` 2.0, `glow_amount` 1.0
- `Fast Spin`:
  - `tunnel_intensity` 4.0, `rotation_speed` 6.0, `zoom_factor` 3.0,
    `spiral_tightness` 3.0, `glow_amount` 2.0
- `Deep Tunnel`:
  - `tunnel_intensity` 6.0, `rotation_speed` 2.0, `zoom_factor` 7.0,
    `spiral_tightness` 5.0, `glow_amount` 3.0, `aberration` 2.0
- `Quantum Singularity`:
  - `tunnel_intensity` 8.0, `rotation_speed` 4.0, `zoom_factor` 9.0,
    `spiral_tightness` 6.0, `kaleidoscope_segments` 5.0, `glow_amount` 5.0,
    `recursion_depth` 4.0

## Edge Cases and Error Handling
- **Singularity at center** (division by zero in polar): Guard log(r) with `log(r + epsilon)`.
- **Wrap-around at theta = ±π**: Use `atan2()` correctly; handle wrapping explicitly.
- **Off-screen coordinates**: Apply edge_mode (clamp, wrap, mirror) at boundaries.
- **Invalid parameter values**: Clamp tunnel_intensity, zoom_factor to safe ranges.
- **Depth texture unavailable**: Render without depth-based weighting.
- **Kaleidoscope segments = 0**: Disable symmetry logic gracefully.

## Test Plan (minimum ≥80% coverage)
- `test_cartesian_to_polar` — coordinate conversion produces expected (r, theta)
- `test_polar_to_cartesian` — inverse transformation round-trips correctly
- `test_tunnel_intensity_zero` — zero intensity produces no distortion
- `test_rotation_animation` — rotation_speed parameter animates theta correctly
- `test_zoom_scaling` — zoom_factor scales r appropriately
- `test_spiral_tightness` — spiral_tightness affects log spiral shape
- `test_kaleidoscope_folds` — with segments=4, produces 4-fold symmetry
- `test_chromatic_aberration` — aberration parameter offsets RGB channels
- `test_glow_center` — glow_amount brightens center region
- `test_edge_clamp_modes` — wrap/clamp/mirror handle off-screen coordinates
- `test_cpu_vs_gpu_parity` — CPU and GPU outputs match within tolerance
- `test_performance_60fps` — sustain ≥60 FPS at 1080p
- `test_depth_weighting` — depth_influence modulates distortion with depth map

## Verification Checkpoints
- [ ] `QuantumConsciousnessSingularityEffect` class registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly to shader uniforms
- [ ] Coordinate transformations (polar/Cartesian) produce valid output
- [ ] Time-based rotation animation is smooth and continuous
- [ ] CPU fallback produces tunnel-like distortion without crashing
- [ ] Presets render distinctive tunnel/vortex visual styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p with typical tunnel settings
- [ ] No safety rail violations

## Implementation Handoff Notes
- Coordinate transformation precision:
  - Use double-precision in critical path (atan2, log)
  - Normalize coordinates carefully to avoid artifacts near edges
  
- Performance optimization:
  - Pre-compute rotation matrices where possible
  - Cache frequently-computed values (sin/cos of time)
  - Consider GLSL `fastlog()` approximations for mobile targets
  
- Recursion implementation:
  - Limit to recursion_depth ≤ 10 to prevent shader compilation bloat
  - Each recursion iteration applies full transform (expensive)
  
- Kaleidoscope symmetry:
  - For N segments, fold theta to range [0, 2π/N], then mirror/reflect

## Resources
- Reference (polar distortion effects): Pov-Ray, Shadertoy tunnels, GLSL Sandbox
- Math: Polar coordinates, logarithmic spirals, complex number transformations
- Performance: Shader optimization for transcendental functions

````
