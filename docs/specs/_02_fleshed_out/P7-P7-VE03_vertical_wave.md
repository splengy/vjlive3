````markdown
# P7-VE03: Vertical Wave Effect (Sinusoidal Distortion)

> **Task ID:** `P7-VE03`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/v_sws.py`)
> **Class:** `VerticalWaveEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `VerticalWaveEffect`—a spatial
distortion effect that displaces image pixels vertically using sinusoidal wave patterns.
The effect creates undulating, ripple-like visual deformations synchronized to
parameters (wavelength, amplitude, frequency, phase). The objective is to document
exact distortion mathematics, parameter remaps, rendering approach, CPU fallback,
and comprehensive tests for feature parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (processes incoming video)
- Sustain 60 FPS with real-time distortion (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful fallback without distortion if disabled (Safety Rail 7)
- CPU fallback implementation for compatibility testing

## Implementation Notes / Porting Strategy
1. Implement vertex displacement via vertex shader (GPU-accelerated).
2. Compute vertical offsets using sinusoidal wave equation: `y_offset = amplitude * sin(frequency * x + phase + time)`.
3. Clamp displaced pixels to valid bounds; extrapolate or clamp at edges.
4. Support multiple wave modes (sine, cosine, sawtooth, square).
5. Provide NumPy-based CPU fallback (frame remapping).
6. Cache wave lookups for performance.

## Public Interface
```python
class VerticalWaveEffect(Effect):
    """
    Vertical Wave Effect: Sinusoidal vertical displacement distortion.
    
    Displaces image pixels vertically using sinusoidal or periodic wave patterns.
    Creates undulating, ripple-like visual deformations. Common in VJ performance
    for motion blur and fluid-like video effects.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 use_gpu: bool = True):
        """
        Initialize the vertical wave effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU vertex displacement; else CPU remapping.
        """
        super().__init__("Vertical Wave Effect", WAVE_VERTEX_SHADER, 
                         WAVE_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "distortion"
        self.effect_tags = ["wave", "distortion", "ripple", "vertical"]
        self.features = ["SPATIAL_DISTORTION", "WAVE_ANIMATION"]
        self.usage_tags = ["MOTION_BLUR", "FLUID", "KINETIC"]
        
        self.use_gpu = use_gpu
        self.wave_cache = {}  # Cache wave lookups for performance

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'amplitude': (0.0, 10.0),          # wave height
            'wavelength': (0.0, 10.0),         # distance between peaks
            'frequency': (0.0, 10.0),          # wave oscillation speed
            'phase': (0.0, 10.0),              # wave offset
            'wave_mode': (0.0, 10.0),          # sine, cosine, sawtooth, etc.
            'edge_behavior': (0.0, 10.0),      # clamp, wrap, mirror
            'horizontal_offset': (0.0, 10.0),  # shift wave horizontally
            'vertical_scale': (0.0, 10.0),     # scale input vertically
            'smoothness': (0.0, 10.0),         # interpolation quality
            'opacity': (0.0, 10.0),            # blending with original
        }

        # Default parameter values
        self.parameters = {
            'amplitude': 5.0,
            'wavelength': 5.0,
            'frequency': 3.0,
            'phase': 0.0,
            'wave_mode': 2.0,                 # sine by default
            'edge_behavior': 0.0,             # clamp by default
            'horizontal_offset': 0.0,
            'vertical_scale': 5.0,
            'smoothness': 8.0,
            'opacity': 10.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'amplitude': "Wave displacement height (0=none, 10=extreme)",
            'wavelength': "Distance between peaks (0=tight, 10=loose)",
            'frequency': "Oscillation speed (0=static, 10=fast)",
            'phase': "Wave offset (0–360°)",
            'wave_mode': "0=sine, 2=cosine, 5=sawtooth, 8=square, 10=triangle",
            'edge_behavior': "0=clamp, 3=wrap, 7=mirror, 10=extrapolate",
            'horizontal_offset': "Shift wave left/right (0—10)",
            'vertical_scale': "Stretch input vertically (0.1—2.0)",
            'smoothness': "Interpolation quality (0=blocky, 10=smooth)",
            'opacity': "Blend with original (0=fully original, 10=full effect)",
        }

        # Sweet spots
        self._sweet_spots = {
            'amplitude': [2.0, 5.0, 8.0],
            'wavelength': [3.0, 5.0, 7.0],
            'frequency': [1.0, 3.0, 6.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None, 
              chain = None) -> int:
        """
        Render wave-distorted version of input texture.
        
        Args:
            tex_in: Input texture (required).
            extra_textures: Optional additional textures.
            chain: Rendering chain context.
            
        Returns:
            Output texture with wave distortion applied.
        """
        # Bind input texture
        # Apply wave displacement via vertex shader
        # Composite result with opacity blending
        # Return output texture
        pass

    def compute_wave_offset(self, x: float, time: float, 
                           frequency: float, phase: float, 
                           amplitude: float) -> float:
        """
        Compute vertical offset at horizontal position x.
        
        Args:
            x: Horizontal coordinate (normalized 0—1).
            time: Current time (seconds).
            frequency: Oscillation frequency.
            phase: Wave phase offset (radians).
            amplitude: Displacement magnitude (pixels).
            
        Returns:
            Vertical offset in pixels.
        """
        # Compute wave value based on mode
        # Apply time-based animation
        # Scale by amplitude
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms for wave animation.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input (unused for this effect).
            semantic_layer: Optional semantic input (unused).
        """
        # Compute time-dependent phase
        # Bind wave parameters to uniforms
        # Update cache for CPU path
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `amplitude` (float, UI 0—10) → internal `A` = map_linear(x, 0,10, 0.0, 100.0)
  - Wave displacement height in pixels [0, 100]
- `wavelength` (float, UI 0—10) → internal `λ` = map_linear(x, 0,10, 10.0, 1000.0)
  - Distance between peaks in pixels [10, 1000]
- `frequency` (float, UI 0—10) → internal `f` = map_linear(x, 0,10, 0.1, 5.0)
  - Oscillation frequency (Hz) [0.1, 5.0]
- `phase` (float, UI 0—10) → internal `φ` = (x / 10.0) * 2π
  - Phase offset in radians [0, 2π]
- `wave_mode` (int, UI 0—10) → internal mode:
  - 0–1: Sine (smooth oscillation)
  - 2–3: Cosine (phase-shifted sine)
  - 4–5: Sawtooth (linear ramp, sharp reset)
  - 6–7: Square (binary on/off)
  - 8–9: Triangle (linear up/down)
  - 10: Custom/hybrid
- `edge_behavior` (int, UI 0—10) → internal behavior:
  - 0–2: Clamp (repeat edge pixels)
  - 3–5: Wrap (tile input)
  - 6–8: Mirror (reflect input)
  - 9–10: Extrapolate (blend to background)
- `horizontal_offset` (float, UI 0—10) → internal `h_offset` = map_linear(x, 0,10, -100.0, 100.0)
  - Shift wave left/right in pixels [-100, 100]
- `vertical_scale` (float, UI 0—10) → internal `v_scale` = map_linear(x, 0,10, 0.1, 2.0)
  - Vertical zoom factor [0.1, 2.0]
- `smoothness` (float, UI 0—10) → internal `smooth` = map_linear(x, 0,10, 0.0, 1.0)
  - Interpolation coefficient for bilinear sampling [0, 1]
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Blend factor [0, 1.0]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float amplitude;`        // wave height
- `uniform float wavelength;`       // peak-to-peak distance
- `uniform float frequency;`        // oscillation frequency
- `uniform float phase;`            // phase offset (radians)
- `uniform int wave_mode;`          // style selection
- `uniform int edge_behavior;`      // boundary handling
- `uniform float horizontal_offset;`// wave shift
- `uniform float vertical_scale;`   // input scaling
- `uniform float smoothness;`       // interpolation quality
- `uniform float opacity;`          // blend factor
- `uniform float time;`             // elapsed time
- `uniform sampler2D tex_in;`       // input texture

## Effect Math (concise, GPU/CPU-consistent)

### 1) Wave Function (Base Computation)

For a horizontal position `x` (0—1 normalized) and time `t`:

```
// Unnormalized wave argument
arg = frequency * time + phase + horizontal_offset

// Base wave value (waveform selection)
if wave_mode == 0:        // SINE
    wave = sin(x / wavelength * 2π + arg)
elif wave_mode == 1:      // COSINE
    wave = cos(x / wavelength * 2π + arg)
elif wave_mode == 2:      // SAWTOOTH
    wave = 2 * ((x / wavelength + arg / 2π) % 1) - 1
elif wave_mode == 3:      // SQUARE
    wave = sign(sin(x / wavelength * 2π + arg))
elif wave_mode == 4:      // TRIANGLE
    wave = 1 - 2 * abs((x / wavelength + arg / 2π) % 1 - 0.5)
else:
    wave = 0.0  // invalid mode

// Amplitude scaling
y_offset = amplitude * wave
```

### 2) Vertical Displacement

For each pixel at `(x, y)` in normalized coordinates:

```
// Compute wave offset at this x position
offset = compute_wave(x, time, wavelength, frequency, phase, amplitude)

// Apply vertical scaling
scaled_offset = offset * vertical_scale

// New sampling position (with boundary handling)
y_new = y + scaled_offset / height  // convert pixels to normalized

// Clamp or wrap based on edge_behavior
if edge_behavior == 0:      // CLAMP
    y_new = clamp(y_new, 0, 1)
elif edge_behavior == 1:    // WRAP
    y_new = y_new % 1
elif edge_behavior == 2:    // MIRROR
    y_new = abs(sin(π * y_new / 2))  // fold at boundaries
else:
    y_new = clamp(y_new, 0, 1)       // default: clamp
```

### 3) Texture Sampling

Sample from input texture at perturbed coordinates with interpolation:

```
// Bilinear interpolation for smoothness
if smoothness > 0.5:
    // Use texture filtering (GPU) or bilinear (CPU)
    color = sample_bilinear(tex_in, (x, y_new))
else:
    // Use nearest neighbor (fast, blocky)
    color = texture(tex_in, (x, y_new))

// Alpha blending with original
color_out = mix(original_color, color, opacity)
```

### 4) Optimization (Cache Wave Lookups)

Pre-compute wave values in 1D lookup table:

```
// Build wave table at start of frame
wave_table = []
for i in range(width):
    x_norm = i / width
    wave_value = compute_wave(x_norm, time)
    wave_table.append(wave_value)

// In shader, index directly into table
y_offset = wave_table[x_pixel]
```

## CPU Fallback (NumPy sketch)

```python
def vertical_wave_cpu(frame, time, amplitude, wavelength, frequency, 
                     phase, wave_mode, edge_behavior, opacity):
    """Apply vertical wave distortion on CPU."""
    
    h, w = frame.shape[:2]
    output = np.zeros_like(frame)
    
    # Build wave lookup
    x_vals = np.arange(w) / w
    wave_arg = frequency * time + phase
    
    if wave_mode == 0:  # SINE
        waves = np.sin(x_vals / wavelength * 2 * np.pi + wave_arg)
    elif wave_mode == 1:  # COSINE
        waves = np.cos(x_vals / wavelength * 2 * np.pi + wave_arg)
    elif wave_mode == 2:  # SAWTOOTH
        waves = 2 * ((x_vals / wavelength + wave_arg / (2*np.pi)) % 1) - 1
    else:
        waves = np.zeros_like(x_vals)
    
    y_offsets = amplitude * waves  # in pixels
    
    # Apply distortion per column
    for x in range(w):
        offset = int(y_offsets[x])
        
        if edge_behavior == 0:  # CLAMP
            y_src = np.arange(h) + offset
            y_src = np.clip(y_src, 0, h - 1)
        elif edge_behavior == 1:  # WRAP
            y_src = (np.arange(h) + offset) % h
        else:
            y_src = np.arange(h) + offset
            y_src = np.clip(y_src, 0, h - 1)
        
        output[:, x] = frame[y_src, x]
    
    # Alpha blend
    result = (1 - opacity) * frame + opacity * output
    return result.astype(np.uint8)
```

## Presets (recommended)
- `Gentle Ripple`:
  - `amplitude` 3.0, `wavelength` 7.0, `frequency` 1.0, `phase` 0.0,
    `wave_mode` 0.0 (sine), `edge_behavior` 0.0 (clamp), `opacity` 5.0
- `Fast Oscillation`:
  - `amplitude` 4.0, `wavelength` 5.0, `frequency` 4.0, `phase` 0.0,
    `wave_mode` 0.0 (sine), `edge_behavior` 0.0 (clamp), `opacity` 8.0
- `Sharp Sawtooth`:
  - `amplitude` 6.0, `wavelength` 3.0, `frequency` 2.0, `phase` 0.0,
    `wave_mode` 2.0 (sawtooth), `edge_behavior` 1.0 (wrap), `opacity` 10.0
- `Mirrored Morphing`:
  - `amplitude` 5.0, `wavelength` 6.0, `frequency` 1.5, `phase` 0.0,
    `wave_mode` 4.0 (triangle), `edge_behavior` 2.0 (mirror), 
    `opacity` 7.0, `vertical_scale` 8.0

## Edge Cases and Error Handling
- **Wavelength = 0**: Clamp to minimum (10 pixels) to avoid division by zero.
- **Frequency = 0**: No animation; static wave pattern.
- **Amplitude = 0**: No distortion; pass through original.
- **Off-screen sampling**: Use clamp/wrap/mirror based on edge_behavior.
- **Invalid wave_mode**: Default to sine.
- **Missing input texture**: Render transparent or black.

## Test Plan (minimum ≥80% coverage)
- `test_wave_function_sine` — sine wave computes correctly
- `test_wave_function_cosine` — cosine wave phase-shifts correctly
- `test_wave_function_sawtooth` — sawtooth ramps and resets correctly
- `test_wave_function_square` — square wave toggles at peaks
- `test_vertical_displacement` — pixels shift vertically by amplitude
- `test_amplitude_scaling` — displacement scales linearly with amplitude
- `test_wavelength_period` — wavelength controls peak-to-peak distance
- `test_frequency_animation` — frequency controls oscillation speed
- `test_phase_offset` — phase shifts wave horizontally
- `test_edge_clamp` — out-of-bounds pixels clamped to edges
- `test_edge_wrap` — out-of-bounds pixels wrap around
- `test_edge_mirror` — out-of-bounds pixels reflected
- `test_opacity_blending` — opacity correctly blends with original
- `test_cpu_vs_gpu_parity` — CPU and GPU outputs match within tolerance
- `test_performance_60fps` — sustain ≥60 FPS at 1080p with default settings

## Verification Checkpoints
- [ ] `VerticalWaveEffect` class registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly to shader uniforms
- [ ] Wave function mode selection works (sine, cosine, sawtooth, square, triangle)
- [ ] Vertical displacement applies and animates correctly
- [ ] Edge behaviors (clamp, wrap, mirror) work as expected
- [ ] CPU fallback produces distorted output without crashing
- [ ] Presets render at intended visual distortion styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p with typical settings
- [ ] Visual output matches vjlive reference implementation

## Implementation Handoff Notes
- Wave lookup optimization:
  - Pre-allocate and reuse wave_table array
  - Update table only when parameters change (not every frame)
  
- GPU optimization:
  - Use vertex shader for displacement (efficient)
  - Alternative: fragment shader with texture lookups (slightly slower)
  
- CPU optimization:
  - Use NumPy vectorization for loop-heavy operations
  - Cache wave computation results across frames
  
- Numerical stability:
  - Normalize inputs to reasonable ranges
  - Check for division by zero in wavelength computation
  - Handle NaN/Inf gracefully

## Resources
- Reference: vjlive, Resolume, TouchDesigner wave effects
- Math: Sinusoidal oscillation, interpolation theory, texture sampling
- GPU: GLSL vertex/fragment shaders, texture wrapping modes

````
