````markdown
# P7-VE16: Bloom Shadertoy Effect (Procedural Glow)

> **Task ID:** `P7-VE16`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/blend.py`)
> **Class:** `BloomShadertoyEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `BloomShadertoyEffect`—a
procedurally-generated bloom effect inspired by Shadertoy-style shaders.
Unlike standard bloom, this creates artistic, animated glow patterns using
procedural noise, distortion, and shader-based generation. The objective
is to document exact Shadertoy bloom mathematics, procedural patterns,
parameter remaps, CPU approximation, and comprehensive tests for feature
parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (post-processes incoming video)
- Sustain 60 FPS with procedural bloom generation (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful fallback to simple bloom if procedural disabled (Safety Rail 7)
- CPU fallback implementation for compatibility testing

## Implementation Notes / Porting Strategy
1. Use Shadertoy-style procedural generation (fbm, turbulence, etc).
2. Apply animated distortion to bloom pattern.
3. Create artistic, fractal-like glow shapes.
4. Blend procedural bloom with original video.
5. Support multiple procedural patterns (fbm, voronoi, cellular).
6. Provide NumPy-based CPU approximation.

## Public Interface
```python
class BloomShadertoyEffect(Effect):
    """
    Bloom Shadertoy Effect: Procedural artistic glow.
    
    Creates animated, procedurally-generated glow patterns inspired by
    Shadertoy shaders. Combines noise, distortion, and mathematical
    patterns to produce artistic, animated bloom effects rather than
    simple highlight glow. Popular in VJ and generative art contexts.
    """

    def __init__(self, width: int = 1920, height: int = 1080,
                 use_gpu: bool = True):
        """
        Initialize the procedural bloom effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU procedural generation; else CPU.
        """
        super().__init__("Bloom Shadertoy", SHADERTOY_BLOOM_VERTEX,
                         SHADERTOY_BLOOM_FRAGMENT)
        
        # Agent Metadata
        self.effect_category = "post_processing"
        self.effect_tags = ["bloom", "procedural", "artistic", "animated"]
        self.features = ["PROCEDURAL_GENERATION", "FRACTAL_NOISE"]
        self.usage_tags = ["ARTISTIC", "ANIMATED", "VJ"]
        
        self.use_gpu = use_gpu
        self.noise_seed = 0.0  # Animated seed

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'bloom_intensity': (0.0, 10.0),    # glow strength
            'bloom_scale': (0.0, 10.0),        # pattern size
            'bloom_speed': (0.0, 10.0),        # animation speed
            'pattern_type': (0.0, 10.0),       # fbm, voronoi, cellular, etc.
            'distortion_amount': (0.0, 10.0),  # procedural distortion
            'color_hue_shift': (0.0, 10.0),    # bloom hue
            'color_saturation': (0.0, 10.0),   # color intensity
            'octave_count': (0.0, 10.0),       # fbm octave layers
            'fractal_roughness': (0.0, 10.0),  # noise lacunarity
            'opacity': (0.0, 10.0),            # effect opacity
        }

        # Default parameter values
        self.parameters = {
            'bloom_intensity': 5.0,
            'bloom_scale': 5.0,
            'bloom_speed': 3.0,
            'pattern_type': 3.0,               # fbm
            'distortion_amount': 4.0,
            'color_hue_shift': 5.0,
            'color_saturation': 6.0,
            'octave_count': 4.0,
            'fractal_roughness': 5.0,
            'opacity': 7.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'bloom_intensity': "Glow strength (0=none, 10=intense)",
            'bloom_scale': "Pattern size (0=fine, 10=large scale)",
            'bloom_speed': "Animation speed (0=static, 10=very fast)",
            'pattern_type': "0–3=FBM, 4–6=Voronoi, 7–10=Cellular",
            'distortion_amount': "Procedural distortion (0=none, 10=extreme)",
            'color_hue_shift': "Bloom hue (0=red, 5=green, 10=blue)",
            'color_saturation': "Color intensity (0=mono, 10=vivid)",
            'octave_count': "FBM layers (0=simple, 10=complex)",
            'fractal_roughness': "Noise lacunarity (0=smooth, 10=rough)",
            'opacity': "Effect opacity (0=original, 10=full bloom)",
        }

        # Sweet spots
        self._sweet_spots = {
            'bloom_intensity': [4.0, 5.0, 7.0],
            'bloom_scale': [3.0, 5.0, 8.0],
            'bloom_speed': [2.0, 5.0, 8.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None,
              chain = None) -> int:
        """
        Render procedural bloom effect.
        
        Args:
            tex_in: Input texture (required).
            extra_textures: Optional additional textures.
            chain: Rendering chain context.
            
        Returns:
            Output texture with procedural bloom applied.
        """
        # Generate procedural bloom pattern based on time/parameters
        # Distort and color the pattern
        # Blend with input texture
        # Return output
        pass

    def generate_procedural_bloom(self, uv: tuple, time: float,
                                 pattern: int, intensity: float,
                                 scale: float, roughness: float) -> tuple:
        """
        Generate procedural bloom RGB at given UV.
        
        Args:
            uv: UV coordinate (x, y) in [0, 1].
            time: Animation time (seconds).
            pattern: Pattern type (0=fbm, 1=voronoi, 2=cellular).
            intensity: Glow intensity [0, 1].
            scale: Pattern size [0.1, 10.0].
            roughness: Lacunarity [0.1, 3.0].
            
        Returns:
            Procedural bloom color (r, g, b) in [0, 1].
        """
        # Generate noise pattern (fbm, voronoi, etc.)
        # Apply distortion
        # Color and return
        pass

    def fbm_pattern(self, uv: tuple, time: float, scale: float,
                   octaves: int, roughness: float) -> float:
        """
        Fractional Brownian Motion (FBM) noise pattern.
        
        Args:
            uv: UV coordinate (x, y).
            time: Animation time.
            scale: Base pattern size.
            octaves: Number of noise layers.
            roughness: Frequency multiplier per octave.
            
        Returns:
            FBM value in [0, 1].
        """
        # Initialize
        # Accumulate octaves with decreasing amplitude
        # Return normalized value
        pass

    def apply_uniforms(self, time: float, resolution: tuple,
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms for procedural bloom.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input (unused).
            semantic_layer: Optional semantic input (unused).
        """
        # Bind procedural bloom parameters to uniforms
        # Update animated noise seed
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `bloom_intensity` (float, UI 0—10) → internal `I` = x / 10.0
  - Glow strength [0, 1.0]
- `bloom_scale` (float, UI 0—10) → internal `scale` = map_linear(x, 0,10, 0.5, 5.0)
  - Pattern size [0.5=fine, 5.0=large]
- `bloom_speed` (float, UI 0—10) → internal `speed` = map_linear(x, 0,10, 0.0, 3.0)
  - Animation speed [0.0=static, 3.0=fast]
- `pattern_type` (int, UI 0—10) → internal type:
  - 0–3: FBM (Fractional Brownian Motion)
  - 4–6: Voronoi (cell-based)
  - 7–10: Cellular (random voronoi cells)
- `distortion_amount` (float, UI 0—10) → internal `dist` = x / 10.0
  - Procedural distortion [0, 1.0]
- `color_hue_shift` (float, UI 0—10) → internal `hue` = x / 10.0 * 360.0
  - Bloom hue angle [0, 360°]
- `color_saturation` (float, UI 0—10) → internal `sat` = x / 10.0
  - Color saturation [0 grayscale, 1 vivid]
- `octave_count` (int, UI 0—10) → internal `octaves` = clamp(round(x / 2.0), 1, 8)
  - FBM octave layers [1, 8]
- `fractal_roughness` (float, UI 0—10) → internal `roughness` = map_linear(x, 0,10, 1.5, 3.0)
  - Noise lacunarity [1.5=smooth, 3.0=rough]
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Effect opacity [0, 1]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float bloom_intensity;`      // glow strength
- `uniform float bloom_scale;`          // pattern size
- `uniform float bloom_speed;`          // animation speed
- `uniform int pattern_type;`           // fbm, voronoi, cellular
- `uniform float distortion_amount;`    // procedural distortion
- `uniform float color_hue_shift;`      // bloom hue (degrees)
- `uniform float color_saturation;`     // color intensity
- `uniform int octave_count;`           // fbm layers
- `uniform float fractal_roughness;`    // lacunarity
- `uniform float opacity;`              // effect opacity
- `uniform float time;`                 // animation time
- `uniform vec2 resolution;`            // screen size
- `uniform sampler2D tex_in;`           // input texture

## Effect Math (concise, GPU/CPU-consistent)

### 1) FBM (Fractional Brownian Motion) Pattern

Generate multi-octave Perlin-like noise:

```
float fbm(vec2 uv, float time, int octaves, float scale, float roughness):
    float value = 0.0
    float amplitude = 1.0
    float frequency = 1.0
    float max_value = 0.0
    
    for i in [0, octaves):
        // Sample noise at this octave
        value += amplitude * noise(uv * frequency * scale + time)
        
        // Update for next octave
        max_value += amplitude
        amplitude *= 0.5                    // Amplitude decreases
        frequency *= roughness              // Frequency increases (lacunarity)
    
    return value / max_value                // Normalize
```

### 2) Voronoi Pattern

Generate cell-based voronoi bloom:

```
float voronoi(vec2 uv, float scale):
    uv *= scale
    vec2 grid_uv = floor(uv)
    vec2 local_uv = fract(uv)
    
    float min_dist = 1.0
    
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            vec2 neighbor = grid_uv + vec2(dx, dy)
            // Pseudo-random cell point
            vec2 point = fract(sin(neighbor * vec2(43.14, 12.77)) * 43758.5453)
            
            float dist = length(local_uv - (point + vec2(dx, dy)))
            min_dist = min(min_dist, dist)
    
    // Invert distance for bloom effect
    return 1.0 - min_dist
```

### 3) Procedural Distortion

Apply animated distortion to UV:

```
vec2 distort_uv(vec2 uv, float time, float amount, float scale):
    // Sample distortion field
    float dist_x = fbm(uv * scale, time, 2, 1.0, 2.0) - 0.5
    float dist_y = fbm(uv * scale + 10.0, time, 2, 1.0, 2.0) - 0.5
    
    // Apply offset
    return uv + vec2(dist_x, dist_y) * amount * 0.1
```

### 4) Procedural Bloom Coloring

Apply hue and saturation to bloom:

```
vec3 bloom_color(float bloom, float hue, float saturation):
    // HSV to RGB conversion
    vec3 hsv = vec3(hue / 360.0, saturation, bloom)
    
    // HSV → RGB
    float c = bloom * saturation
    float x = c * (1.0 - abs(mod(hue / 60.0, 2.0) - 1.0))
    
    vec3 rgb = vec3(0)
    if hue < 60:      rgb = vec3(c, x, 0)
    else if hue < 120: rgb = vec3(x, c, 0)
    else if hue < 180: rgb = vec3(0, c, x)
    else if hue < 240: rgb = vec3(0, x, c)
    else if hue < 300: rgb = vec3(x, 0, c)
    else:             rgb = vec3(c, 0, x)
    
    return rgb
```

### 5) Composite Bloom with Input

```
vec3 color_original = texture(tex_in, uv)
vec3 bloom = bloom_color(fbm_value, hue, saturation)

// Additive composite
vec3 output = color_original + bloom * bloom_intensity

// With opacity
output = mix(color_original, output, opacity)
return output
```

## CPU Fallback (NumPy sketch)

```python
def fbm_pattern_cpu(uv, time, octaves, scale, roughness):
    """Compute FBM pattern."""
    value = np.zeros_like(uv[..., 0])
    amplitude = 1.0
    frequency = 1.0
    max_amp = 0.0
    
    for octave in range(octaves):
        # Pseudo-random noise via sine
        noise = np.sin((uv[:,0] * frequency * scale + time) * 43.14) * 
               np.sin((uv[:,1] * frequency * scale + time) * 12.77) * 43758.5453
        value += amplitude * np.fract(noise)
        
        max_amp += amplitude
        amplitude *= 0.5
        frequency *= roughness
    
    return value / max(max_amp, 0.001)

def bloom_shadertoy_cpu(frame, pattern_type, bloom_intensity, scale,
                       speed, octaves, roughness, hue, saturation):
    """Apply procedural bloom."""
    
    img = frame.astype(np.float32) / 255.0
    h, w = img.shape[:2]
    
    # Generate UV coordinates
    y, x = np.meshgrid(np.linspace(0, 1, h), np.linspace(0, 1, w))
    uv = np.stack([x, y], axis=-1)
    
    if pattern_type == 0:  # FBM
        bloom = fbm_pattern_cpu(uv, speed, octaves, scale, roughness)
    elif pattern_type == 1:  # Voronoi
        bloom = voronoi_pattern_cpu(uv, scale)
    else:  # Cellular
        bloom = cellular_pattern_cpu(uv, scale)
    
    # Color bloom
    bloom_rgb = hsv_to_rgb(np.stack([hue, saturation, bloom], axis=-1))
    
    # Composite
    result = img + bloom_rgb * bloom_intensity
    result = np.clip(result, 0, 1)
    
    return (result * 255).astype(np.uint8)
```

## Presets (recommended)
- `Gentle FBM Glow`:
  - `bloom_intensity` 4.0, `bloom_scale` 3.0, `bloom_speed` 1.0,
    `pattern_type` 2.0, `octave_count` 3.0, `opacity` 5.0
- `Fast Voronoi Bloom`:
  - `bloom_intensity` 5.0, `bloom_scale` 4.0, `bloom_speed` 6.0,
    `pattern_type` 5.0, `fractal_roughness` 6.0, `opacity` 7.0
- `Chaotic Distortion`:
  - `bloom_intensity` 6.0, `bloom_scale` 5.0, `bloom_speed` 8.0,
    `distortion_amount` 8.0, `pattern_type` 2.0, `opacity` 8.0
- `Colored Cellular Matter`:
  - `bloom_intensity` 7.0, `bloom_scale` 6.0, `bloom_speed` 4.0,
    `pattern_type` 8.0, `color_hue_shift` 3.0, `color_saturation` 9.0,
    `opacity` 9.0

## Edge Cases and Error Handling
- **octave_count = 0**: Use minimum 1 octave fallback.
- **bloom_scale = 0**: Use minimum scale 0.5.
- **fractal_roughness < 1.0**: Clamp to 1.0 (no amplitude growth).
- **bloom_speed = 0**: Static pattern (no animation).
- **pattern_type invalid**: Default to FBM (type 0).
- **NaN in noise**: Use safe default value (0.5).

## Test Plan (minimum ≥80% coverage)
- `test_zero_intensity_pass_through` — zero intensity = input only
- `test_fbm_pattern_generation` — FBM produces varied noise pattern
- `test_voronoi_pattern_generation` — Voronoi generates cell pattern
- `test_cellular_pattern_generation` — Cellular produces random cells
- `test_animation_time_changes_pattern` — Pattern animates with time
- `test_scale_affects_pattern_size` — Scale changes pattern frequency
- `test_octave_count_complexity` — More octaves = more complex pattern
- `test_roughness_affects_lacunarity` — Roughness controls frequency growth
- `test_distortion_warps_pattern` — Distortion amount deforms bloom
- `test_hue_shift_colors_bloom` — Hue parameter colors output
- `test_saturation_modulates_color` — Saturation affects color intensity
- `test_cpu_vs_gpu_parity` — CPU and GPU outputs match within tolerance
- `test_performance_60fps` — sustain ≥60 FPS at 1080p
- `test_pattern_transitions` — Pattern type changes produce distinct outputs

## Verification Checkpoints
- [ ] `BloomShadertoyEffect` registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly
- [ ] FBM pattern generates multi-octave noise
- [ ] Voronoi pattern generates cell-based bloom
- [ ] Cellular pattern generates random cells
- [ ] Time parameter animates patterns
- [ ] Scale parameter controls pattern frequency
- [ ] Distortion applies procedural warping
- [ ] Hue shift colors bloom correctly
- [ ] Saturation modulates color intensity
- [ ] CPU fallback produces procedural bloom without crash
- [ ] Presets render at intended styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p with procedural generation
- [ ] No visual artifacts from pattern boundaries

## Implementation Handoff Notes
- GPU techniques:
  - Implement Perlin-like noise via 2D sine/pseudorandom functions
  - Use texture-based noise (classic Perlin or Simplex) for quality
  - Consider noise texture atlases for performance
  - Multi-pass rendering for complex procedural patterns
  
- Procedural generation tips:
  - FBM: Start with amplitude=1, halve per octave, multiply frequency
  - Voronoi: Use fract(sin()) for pseudo-random cell points
  - Cellular: Similar to Voronoi but with different distance metrics
  
- Performance optimization:
  - Cache noise function results when possible
  - Use integer coordinates in modular arithmetic to avoid float errors
  - Consider low-res procedural generation + upsampling
  
- CPU fallback strategy:
  - Use NumPy fract() and sin() for fast pseudo-random numbers
  - Pre-compute patterns if static (cache between frames)
  - For animation, only recompute affected pixels

## Resources
- Reference: Shadertoy popular bloom effects, procedural generation tutorials
- Math: FBM, Voronoi, Perlin noise, HSV color conversion
- GPU: GLSL noise functions, multi-pass rendering

````
