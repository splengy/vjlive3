````markdown
# P7-VE15: Bloom Effect (Highlights Glow)

> **Task ID:** `P7-VE15`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/blend.py`)
> **Class:** `BloomEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `BloomEffect`—a post-processing
effect that creates glowing highlights by extracting bright pixels, blurring them,
and compositing back to the original. The effect simulates lens flare and camera
bloom. The objective is to document exact bloom mathematics, parameter remaps,
threshold computation, CPU fallback, and comprehensive tests for feature parity
with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (post-processes incoming video)
- Sustain 60 FPS with real-time blur and compositing (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful fallback without glow if disabled (Safety Rail 7)
- CPU fallback implementation for compatibility testing

## Implementation Notes / Porting Strategy
1. Extract bright pixels above luminance threshold.
2. Apply Gaussian blur to bright pixels (large kernel).
3. Composite blurred bright pixels back to original.
4. Support threshold adjustment (isolate only very bright areas).
5. Support bloom radius (blur kernel size).
6. Provide NumPy-based CPU fallback.

## Public Interface
```python
class BloomEffect(Effect):
    """
    Bloom Effect: Cinematic highlights glow.
    
    Creates soft glowing highlights on bright areas of video. Extracts
    bright pixels, blurs them, and composites back to create a lens
    bloom effect. Common in cinematography for soft, dreamy aesthetics.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 use_gpu: bool = True):
        """
        Initialize the bloom effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU blur; else CPU scipy.
        """
        super().__init__("Bloom Effect", BLOOM_VERTEX_SHADER, 
                         BLOOM_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "post_processing"
        self.effect_tags = ["bloom", "glow", "highlight", "cinematic"]
        self.features = ["HIGHLIGHT_EXTRACTION", "GAUSSIAN_BLUR"]
        self.usage_tags = ["SOFT", "DREAMY", "CINEMATIC"]
        
        self.use_gpu = use_gpu
        self.bright_buffer = None  # Extracted bright pixels

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'bloom_intensity': (0.0, 10.0),    # glow strength
            'bloom_threshold': (0.0, 10.0),    # brightness cutoff
            'bloom_radius': (0.0, 10.0),       # blur kernel size
            'bloom_falloff': (0.0, 10.0),      # threshold softness
            'color_preserve': (0.0, 10.0),     # keep original colors
            'highlight_boost': (0.0, 10.0),    # amplify picked bright
            'tone_curve': (0.0, 10.0),         # tone mapping mode
            'blend_mode': (0.0, 10.0),         # additive, screen, soft light
            'saturation_boost': (0.0, 10.0),   # color intensity on bloom
            'opacity': (0.0, 10.0),            # effect opacity
        }

        # Default parameter values
        self.parameters = {
            'bloom_intensity': 5.0,
            'bloom_threshold': 6.0,
            'bloom_radius': 5.0,               # pixels
            'bloom_falloff': 3.0,
            'color_preserve': 5.0,
            'highlight_boost': 4.0,
            'tone_curve': 5.0,                 # linear
            'blend_mode': 0.0,                 # additive
            'saturation_boost': 5.0,
            'opacity': 7.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'bloom_intensity': "Glow strength (0=none, 10=intense)",
            'bloom_threshold': "Brightness cutoff (0=all pixels, 10=only very bright)",
            'bloom_radius': "Blur kernel size (0=sharp, 10=very soft)",
            'bloom_falloff': "Threshold softness (0=hard, 10=smooth)",
            'color_preserve': "Keep color tint (0=white glow, 10=colored glow)",
            'highlight_boost': "Amplify bright pixels (0=subtle, 10=extreme)",
            'tone_curve': "0=linear, 5=quadratic, 10=exponential",
            'blend_mode': "0=additive, 3=screen, 6=soft light, 10=multiply",
            'saturation_boost': "Bloom color intensity (0=mono, 10=vivid)",
            'opacity': "Effect opacity (0=original, 10=full bloom)",
        }

        # Sweet spots
        self._sweet_spots = {
            'bloom_intensity': [3.0, 5.0, 7.0],
            'bloom_threshold': [5.0, 6.0, 7.0],
            'bloom_radius': [3.0, 5.0, 8.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None, 
              chain = None) -> int:
        """
        Render bloom-glowed version of input texture.
        
        Args:
            tex_in: Input texture (required).
            extra_textures: Optional additional textures.
            chain: Rendering chain context.
            
        Returns:
            Output texture with bloom glow applied.
        """
        # Extract bright pixels above threshold
        # Apply Gaussian blur to bright pixels
        # Composite glow back to original
        # Apply blend mode and opacity
        # Return output texture
        pass

    def extract_bright_pixels(self, color: tuple, threshold: float,
                             falloff: float, boost: float) -> tuple:
        """
        Extract and boost bright pixels above threshold.
        
        Args:
            color: Original RGB color (r, g, b) in [0, 1].
            threshold: Brightness cutoff [0, 1].
            falloff: Threshold softness [0, 1].
            boost: Amplification factor [1, 3].
            
        Returns:
            Extracted bright color in [0, 1].
        """
        # Compute luminance
        # Apply threshold with falloff
        # Boost and return
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms for bloom parameters.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input (unused).
            semantic_layer: Optional semantic input (unused).
        """
        # Bind bloom parameters to uniforms
        # Setup blur kernel size based on radius
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `bloom_intensity` (float, UI 0—10) → internal `I` = x / 10.0
  - Glow strength [0, 1.0]
- `bloom_threshold` (float, UI 0—10) → internal `T` = map_linear(x, 0,10, 0.1, 0.95)
  - Brightness cutoff [0.1=more pixels, 0.95=only very bright]
- `bloom_radius` (int, UI 0—10) → internal `r` = clamp(round(x * 5), 1, 50)
  - Blur radius in pixels [1, 50]
- `bloom_falloff` (float, UI 0—10) → internal `falloff` = map_linear(x, 0,10, 0.01, 0.2)
  - Threshold softness [0.01=hard, 0.2=smooth]
- `color_preserve` (float, UI 0—10) → internal `preserve` = x / 10.0
  - Color preservation factor [0 white glow, 1 colored]
- `highlight_boost` (float, UI 0—10) → internal `boost` = map_linear(x, 0,10, 1.0, 3.0)
  - Bright pixel amplification [1.0=neutral, 3.0=3x brightness]
- `tone_curve` (int, UI 0—10) → internal curve:
  - 0–3: Linear
  - 4–6: Quadratic
  - 7–10: Exponential (steeper)
- `blend_mode` (int, UI 0—10) → internal mode:
  - 0–2: Additive (brighten)
  - 3–5: Screen (lighter)
  - 6–8: Soft light (subtle)
  - 9–10: Multiply (darken)
- `saturation_boost` (float, UI 0—10) → internal `sat` = x / 10.0
  - Saturation on bloom [0 grayscale, 1 vivid]
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Effect opacity [0, 1]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float bloom_intensity;`      // glow strength
- `uniform float bloom_threshold;`      // brightness cutoff
- `uniform int bloom_radius;`           // blur kernel size
- `uniform float bloom_falloff;`        // threshold softness
- `uniform float color_preserve;`       // color tint preservation
- `uniform float highlight_boost;`      // bright pixel amplification
- `uniform int tone_curve;`             // curve type
- `uniform int blend_mode;`             // compositing mode
- `uniform float saturation_boost;`     // bloom color intensity
- `uniform float opacity;`              // effect opacity
- `uniform vec2 resolution;`            // screen size
- `uniform sampler2D tex_in;`           // input texture

## Effect Math (concise, GPU/CPU-consistent)

### 1) Bright Pixel Extraction

For each pixel, compute luminance and extract bright values:

```
// Sample color
color = texture(tex_in, uv)

// Compute luminance (ITU-R BT.709)
luma = dot(color, vec3(0.2126, 0.7152, 0.0722))

// Threshold with falloff (smooth step)
if tone_curve == 0:              // LINEAR
    threshold_mask = smoothstep(bloom_threshold - bloom_falloff, 
                               bloom_threshold + bloom_falloff, luma)
elif tone_curve == 1:            // QUADRATIC
    threshold_mask = pow(max(luma - bloom_threshold, 0), 2.0) / 
                    max(bloom_falloff, 0.001)
else:                            // EXPONENTIAL
    threshold_mask = exp((luma - bloom_threshold) / max(bloom_falloff, 0.001))

// Extract bright color (preserve color or make white)
bright_color = color * threshold_mask * highlight_boost

// Optionally desaturate to white glow
if color_preserve < 1.0:
    gray = vec3(luma * highlight_boost)
    bright_color = mix(gray, bright_color, color_preserve)
```

### 2) Gaussian Blur

Apply Gaussian blur to extracted bright pixels:

```
// Gaussian blur kernel (separable: apply horizontal then vertical)
sigma = bloom_radius / 2.0
kernel_size = int(ceil(2.0 * sigma))

// Blur horizontally
for x_offset in range(-kernel_size, kernel_size):
    weight = exp(-(x_offset^2) / (2.0 * sigma^2))
    blurred += texture(bright_buffer, uv + vec2(x_offset/w, 0)) * weight

// Blur vertically (second pass)
for y_offset in range(-kernel_size, kernel_size):
    weight = exp(-(y_offset^2) / (2.0 * sigma^2))
    blurred += texture(bright_buffer, uv + vec2(0, y_offset/h)) * weight

// Normalize
blurred = blurred / total_weight
```

### 3) Color Treatment on Bloom

Apply saturation boost to bloom:

```
// Existing desaturation logic
if saturation_boost < 1.0:
    gray = dot(blurred, vec3(0.299, 0.587, 0.114))
    for channel:
        blurred[c] = gray * (1 - saturation_boost) + blurred[c] * saturation_boost

// Or: boost saturation
if saturation_boost > 1.0:
    gray = dot(blurred, vec3(0.299, 0.587, 0.114))
    for channel:
        blurred[c] = 0.5 + (blurred[c] - 0.5) * saturation_boost
```

### 4) Blend Modes

Composite bloom with original:

```
color_original = texture(tex_in, uv)

if blend_mode == 0:              // ADDITIVE
    color_out = color_original + blurred * bloom_intensity
elif blend_mode == 1:            // SCREEN
    color_out = 1.0 - (1.0 - color_original) * (1.0 - blurred * bloom_intensity)
elif blend_mode == 2:            // SOFT LIGHT
    base = color_original
    blend = blurred
    // SoftLight formula (from Photoshop)
    result = mix(2.0 * base * blend,
                1.0 - 2.0 * (1.0 - base) * (1.0 - blend),
                step(0.5, base))
    color_out = mix(color_original, result, bloom_intensity)
else:                            // MULTIPLY
    color_out = color_original * (1.0 - blurred * bloom_intensity)

// Clamp to valid range
color_out = clamp(color_out, 0, 1)

// Final opacity blend
output = mix(color_original, color_out, opacity)
```

## CPU Fallback (NumPy sketch)

```python
def bloom_cpu(frame, bloom_intensity, bloom_threshold, bloom_radius,
             bloom_falloff, highlight_boost, saturation_boost):
    """Apply bloom effect on CPU."""
    
    img = frame.astype(np.float32) / 255.0
    h, w = img.shape[:2]
    
    # Compute luminance
    luma = 0.2126 * img[:,:,0] + 0.7152 * img[:,:,1] + 0.0722 * img[:,:,2]
    
    # Extract bright pixels
    bright_mask = np.maximum(luma - bloom_threshold, 0) / max(bloom_falloff, 0.001)
    bright_mask = np.clip(bright_mask, 0, 1)
    
    bright = img.copy()
    for c in range(3):
        bright[:,:,c] = bright[:,:,c] * bright_mask * highlight_boost
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(bright, (bloom_radius*2+1, bloom_radius*2+1), 
                              bloom_radius / 2.0)
    
    # Composite: additive blend
    result = img + blurred * bloom_intensity
    result = np.clip(result, 0, 1)
    
    return (result * 255).astype(np.uint8)
```

## Presets (recommended)
- `Subtle Glow`:
  - `bloom_intensity` 3.0, `bloom_threshold` 7.0, `bloom_radius` 3.0,
    `highlight_boost` 2.0, `blend_mode` 0.0 (additive), `opacity` 4.0
- `Soft Cinema`:
  - `bloom_intensity` 5.0, `bloom_threshold` 6.0, `bloom_radius` 6.0,
    `color_preserve` 8.0, `highlight_boost` 3.0, `opacity` 7.0
- `Dreamy Light`:
  - `bloom_intensity` 6.0, `bloom_threshold` 5.0, `bloom_radius` 8.0,
    `bloom_falloff` 4.0, `blend_mode` 1.0 (screen), `opacity` 8.0
- `Neon Glow`:
  - `bloom_intensity` 7.0, `bloom_threshold` 7.5, `bloom_radius` 5.0,
    `highlight_boost` 4.0, `saturation_boost` 9.0, `color_preserve` 10.0, 
    `opacity` 10.0

## Edge Cases and Error Handling
- **bloom_radius = 0**: Use minimum radius 1 to prevent no-op.
- **bloom_threshold = 1.0**: Only pure white (1, 1, 1) blooms.
- **bloom_threshold = 0**: All pixels bloom (expensive).
- **bloom_intensity = 0**: No bloom; pass through original.
- **bloom_falloff = 0**: Hard transition; may cause aliasing.
- **NaN in blur**: Use safe fallback blur kernel.

## Test Plan (minimum ≥80% coverage)
- `test_no_bloom_pass_through` — zero intensity = input only
- `test_bright_pixel_extraction` — only bright pixels extracted
- `test_threshold_adjustment` — threshold isolates correct pixels
- `test_threshold_falloff_smoothness` — falloff softens transitions
- `test_bloom_radius_blur_size` — radius controls blur magnitude
- `test_highlight_boost_amplification` — boost brightens extracted pixels
- `test_color_preserve_tint` — preserve parameter keeps color or whitens
- `test_blend_additive` — additive blend brightens output
- `test_blend_screen` — screen blend is lighter
- `test_blend_soft_light` — soft light subtle blending
- `test_saturation_boost_color` — saturation modulates bloom color
- `test_cpu_vs_gpu_parity` — CPU and GPU outputs match within tolerance
- `test_performance_60fps` — sustain ≥60 FPS at 1080p with bloom
- `test_no_bloom_edge_pixels` — edge pixels don't cause artifacts

## Verification Checkpoints
- [ ] `BloomEffect` registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly
- [ ] Bright pixel extraction works per threshold
- [ ] Gaussian blur applies correctly to bright buffer
- [ ] All blend modes produce distinct compositing
- [ ] Color preservation tints bloom correctly
- [ ] CPU fallback produces glow output without crash
- [ ] Presets render at intended bloom styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p with typical bloom
- [ ] No visual artifacts from blur boundary

## Implementation Handoff Notes
- Performance optimization:
  - Two-pass Gaussian blur (separate H and V) is crucial for speed
  - Pre-allocate blur kernel to avoid per-frame computation
  - Use lower resolution intermediate buffer for bloom blur (downsampling)
  
- GPU optimization:
  - Implement separable Gaussian with fragment shader
  - Use hardware texture filtering for blur averaging
  - Consider multi-scale bloom (mipmap-based) for large radius
  
- CPU optimization:
  - Use OpenCV GaussianBlur for speed
  - Vectorize all operations with NumPy
  - Consider scipy.ndimage.gaussian_filter as fallback
  
- Numerical stability:
  - Clamp bloom_falloff to avoid division by zero
  - Normalize blur kernel weights properly
  - Watch for luminance computation overflow

## Resources
- Reference: vjlive bloom, standard post-processing bloom
- Math: Gaussian blur, luminance formulas, blend mode operations
- GPU: GLSL separable convolution, two-pass blur technique

````
