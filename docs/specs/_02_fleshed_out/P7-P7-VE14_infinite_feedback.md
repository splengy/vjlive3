````markdown
# P7-VE14: Infinite Feedback Effect (Recursive Video Loop)

> **Task ID:** `P7-VE14`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/blend.py`)
> **Class:** `InfiniteFeedbackEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `InfiniteFeedbackEffect`—a
recursive feedback effect that feeds the output back into the input, creating
infinite loop visuals. The effect can apply zoom, rotation, and color shifts
per feedback iteration. The objective is to document exact feedback mathematics,
parameter remaps, stability constraints, CPU fallback (simplified), and comprehensive
tests for feature parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (processes incoming video with feedback)
- Sustain 60 FPS with recursive rendering (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Prevent feedback explosion (stability rails) via dampening (Safety Rail 7)
- CPU fallback implementation (iterative, not real recursive)

## Implementation Notes / Porting Strategy
1. Maintain secondary framebuffer for feedback history.
2. Composite input with feedback buffer.
3. Apply transform (zoom, rotation, position shift) to feedback.
4. Apply color shift/grading per iteration.
5. Implement dampening to prevent explosion.
6. Provide NumPy-based CPU fallback (multi-iteration simulation).

## Public Interface
```python
class InfiniteFeedbackEffect(Effect):
    """
    Infinite Feedback Effect: Recursive recursive video loop.
    
    Creates recursive feedback loops by feeding the output back as input
    in subsequent frames. Supports zoom, rotation, color shifts, and
    position offsets per iteration. Creates hypnotic, kaleidoscopic
    visual patterns. Common in experimental and live VJ performance.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 use_gpu: bool = True):
        """
        Initialize the infinite feedback effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU feedback; else CPU iteration.
        """
        super().__init__("Infinite Feedback Effect", FB_VERTEX_SHADER, 
                         FB_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "recursive"
        self.effect_tags = ["feedback", "recursive", "infinite", "loop"]
        self.features = ["RECURSIVE_RENDERING", "FEEDBACK_LOOP"]
        self.usage_tags = ["HYPNOTIC", "EXPERIMENTAL", "KALEIDOSCOPE"]
        
        self.use_gpu = use_gpu
        self.feedback_buffer = None  # Previous frame buffer
        self.feedback_iterations = 1  # Number of feedback passes

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'feedback_amount': (0.0, 10.0),    # feedback strength
            'feedback_dampening': (0.0, 10.0), # decay per iteration
            'zoom_factor': (0.0, 10.0),        # radial magnification
            'rotation': (0.0, 10.0),           # angular rotation
            'position_x': (0.0, 10.0),         # x offset per iteration
            'position_y': (0.0, 10.0),         # y offset per iteration
            'color_shift': (0.0, 10.0),        # hue rotation per iteration
            'blur_feedback': (0.0, 10.0),      # gaussian blur on feedback
            'saturation': (0.0, 10.0),         # color intensity
            'opacity': (0.0, 10.0),            # effect opacity
        }

        # Default parameter values
        self.parameters = {
            'feedback_amount': 6.0,
            'feedback_dampening': 5.0,
            'zoom_factor': 5.0,                # 1.0x by default
            'rotation': 0.0,
            'position_x': 0.0,
            'position_y': 0.0,
            'color_shift': 0.0,
            'blur_feedback': 0.0,
            'saturation': 5.0,
            'opacity': 8.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'feedback_amount': "Feedback strength (0=none, 10=strong loop)",
            'feedback_dampening': "Decay per iteration (0=explosion, 5=stable, 10=fade)",
            'zoom_factor': "Magnification (0=shrink, 5=1x, 10=expand)",
            'rotation': "Angular rotation per iteration (0—360°)",
            'position_x': "Horizontal shift per iteration (pixels, -100—100)",
            'position_y': "Vertical shift per iteration (pixels, -100—100)",
            'color_shift': "Hue rotation per iteration (0—360°)",
            'blur_feedback': "Blur on feedback buffer (0=sharp, 10=heavy)",
            'saturation': "Color intensity (0=grayscale, 10=vivid)",
            'opacity': "Overall effect opacity (0=original, 10=full feedback)",
        }

        # Sweet spots
        self._sweet_spots = {
            'feedback_amount': [3.0, 6.0, 8.0],
            'feedback_dampening': [4.0, 5.0, 6.0],
            'zoom_factor': [4.0, 5.0, 6.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None, 
              chain = None) -> int:
        """
        Render recursive feedback composite of input and previous frame.
        
        Args:
            tex_in: Current input texture (required).
            extra_textures: Optional additional textures.
            chain: Rendering chain context.
            
        Returns:
            Output texture with feedback loop applied.
        """
        # Sample current input
        # Sample feedback buffer
        # Composite input with transformed feedback
        # Apply color shifts and dampening
        # Render to output and to feedback buffer for next frame
        # Return output texture
        pass

    def apply_feedback_iterations(self, color: tuple, iteration: int,
                                 color_shift: float, zoom: float) -> tuple:
        """
        Apply transformations based on feedback iteration count.
        
        Args:
            color: Current pixel color (r, g, b, a) in [0, 1].
            iteration: Iteration number (0, 1, 2, ...).
            color_shift: Hue rotation per iteration.
            zoom: Zoom factor per iteration.
            
        Returns:
            Transformed color.
        """
        # Apply color shift based on iteration
        # Apply zoom-based brightness modulation
        # Apply dampening to reduce amplitude
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms for feedback parameters.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input (unused).
            semantic_layer: Optional semantic input (unused).
        """
        # Bind feedback parameters to uniforms
        # Ensure dampening prevents explosion
        # Update feedback buffer texture
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `feedback_amount` (float, UI 0—10) → internal `F` = x / 10.0
  - Feedback strength [0, 1.0]
- `feedback_dampening` (float, UI 0—10) → internal `D` = map_linear(x, 0,10, 0.3, 1.0)
  - Decay per iteration [0.3=strong decay, 1.0=no decay]
- `zoom_factor` (float, UI 0—10) → internal `Z` = map_linear(x, 0,10, 0.5, 2.0)
  - Magnification [0.5=shrink, 1.0=neutral, 2.0=expand]
- `rotation` (float, UI 0—10) → internal `θ` = (x / 10.0) * 360.0
  - Rotation per iteration (degrees) [0, 360]
- `position_x` (float, UI 0—10) → internal `px` = map_linear(x, 0,10, -50.0, 50.0)
  - X offset per iteration (pixels) [-50, 50]
- `position_y` (float, UI 0—10) → internal `py` = map_linear(x, 0,10, -50.0, 50.0)
  - Y offset per iteration (pixels) [-50, 50]
- `color_shift` (float, UI 0—10) → internal `hue` = (x / 10.0) * 360.0
  - Hue rotation per iteration (degrees) [0, 360]
- `blur_feedback` (float, UI 0—10) → internal `blur_σ` = map_linear(x, 0,10, 0.0, 10.0)
  - Gaussian blur sigma [0, 10]
- `saturation` (float, UI 0—10) → internal `sat` = x / 10.0
  - Saturation factor [0, 1.0]
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Effect opacity [0, 1]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float feedback_amount;`      // feedback strength
- `uniform float feedback_dampening;`   // decay factor
- `uniform float zoom_factor;`          // zoom per iteration
- `uniform float rotation;`             // rotation per iteration
- `uniform vec2 position_offset;`       // (px, py) offset
- `uniform float color_shift;`          // hue rotation per iteration
- `uniform float blur_feedback;`        // blur on feedback
- `uniform float saturation;`           // color saturation
- `uniform float opacity;`              // effect opacity
- `uniform sampler2D tex_in;`           // current input
- `uniform sampler2D tex_feedback;`     // previous frame buffer

## Effect Math (concise, GPU/CPU-consistent)

### 1) Composite Input and Feedback

For each pixel:

```
// Sample current input
color_in = texture(tex_in, uv)

// Sample feedback
color_fb = texture(tex_feedback, uv)

// Apply dampening decay
color_fb = color_fb * feedback_dampening

// Composite: blend feedback with input
color_composite = mix(color_in, color_fb, feedback_amount)
```

### 2) Apply Transforms to Feedback

Before rendering to feedback buffer, apply transforms:

```
// Transform coordinates for next iteration
// Center around origin
uv_centered = uv - vec2(0.5)

// Apply rotation (matrix)
angle = rotation * π / 180.0
c = cos(angle)
s = sin(angle)
uv_rotated = vec2(c * uv_centered.x - s * uv_centered.y,
                  s * uv_centered.x + c * uv_centered.y)

// Apply zoom
uv_zoomed = uv_rotated / zoom_factor

// Apply position offset
uv_offset = uv_zoomed + position_offset / resolution

// Bring back to [0, 1]
uv_transformed = uv_offset + vec2(0.5)

// Clamp to valid bounds
uv_transformed = clamp(uv_transformed, 0, 1)
```

### 3) Color Shifts Per Iteration

Apply hue rotation and saturation:

```
// Convert RGB to HSV
hsv = rgb_to_hsv(color_fb)

// Rotate hue
hsv.x = fract(hsv.x + color_shift / 360.0)

// Modulate saturation
hsv.y = hsv.y * saturation

// Convert back to RGB
color_shifted = hsv_to_rgb(hsv)
```

### 4) Blur on Feedback

Optional Gaussian blur:

```
if blur_feedback > 0:
    // Apply Gaussian blur with sigma = blur_feedback
    blurred = gaussian_blur(tex_feedback, uv, blur_feedback)
    color_shifted = mix(color_shifted, blurred, min(blur_feedback / 5.0, 1.0))
```

### 5) Render to Both Output and Feedback Buffer

```
// Output: composite
out_color = mix(color_in, color_composite, opacity)

// Feedback buffer: transformed, shifted version (for next frame)
feedback_next = texture_at_transformed(color_shifted, uv_transformed)

// Write out_color to output framebuffer
// Write feedback_next to feedback buffer for next frame
```

## CPU Fallback (NumPy sketch)

```python
def infinite_feedback_cpu(frame, feedback_previous, feedback_amount, 
                         feedback_dampening, zoom_factor, rotation,
                         position_offset, color_shift):
    """Apply feedback effect via iterative simulation."""
    
    h, w = frame.shape[:2]
    frame_f = frame.astype(np.float32) / 255.0
    fb = feedback_previous.astype(np.float32) / 255.0
    
    # Generate mesh for coordinate transforms
    yy, xx = np.meshgrid(np.arange(h) / h, np.arange(w) / w, indexing='ij')
    
    # Apply feedback dampening
    fb = fb * feedback_dampening
    
    # Apply transforms to feedback
    # (Simplified: just scale and shift without full rotation)
    scale = 1.0 / zoom_factor
    fb_scaled = cv2.warpAffine(fb, 
        cv2.getRotationMatrix2D((w/2, h/2), rotation, zoom_factor), 
        (w, h))
    
    # Composite
    result = (1 - feedback_amount) * frame_f + feedback_amount * fb_scaled
    
    # Hue shift via HSV (optional simplified version)
    if color_shift > 0:
        hsv = cv2.cvtColor((result * 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
        hsv[:,:,0] = (hsv[:,:,0] + color_shift * 255 / 360) % 256
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB).astype(np.float32) / 255.0
    
    # For next frame
    feedback_next = result.copy()
    
    return (np.clip(result, 0, 1) * 255).astype(np.uint8), \
           (np.clip(feedback_next, 0, 1) * 255).astype(np.uint8)
```

## Presets (recommended)
- `Gentle Loop`:
  - `feedback_amount` 4.0, `feedback_dampening` 6.0, `zoom_factor` 5.0,
    `rotation` 0.0, `opacity` 6.0
- `Spinning Vortex`:
  - `feedback_amount` 6.0, `feedback_dampening` 5.0, `zoom_factor` 5.5,
    `rotation` 5.0, `color_shift` 10.0, `opacity` 8.0
- `Infinite Tunnel`:
  - `feedback_amount` 7.0, `feedback_dampening` 5.0, `zoom_factor` 6.0,
    `rotation` 0.0, `color_shift` 5.0, `opacity` 9.0
- `Chaotic Kaleidoscope`:
  - `feedback_amount` 8.0, `feedback_dampening` 4.0, `zoom_factor` 4.5,
    `rotation` 10.0, `position_x` 5.0, `position_y` 5.0, 
    `color_shift` 20.0, `opacity` 10.0

## Edge Cases and Error Handling
- **feedback_dampening < 0.3**: Feedback explodes; clamp to 0.3.
- **feedback_amount = 0**: No feedback; output is input only.
- **zoom_factor << 0.5**: Extreme shrinking; may lose visual content.
- **zoom_factor >> 2.0**: Extreme expansion; pixels may magnify beyond visible bounds.
- **Missing feedback buffer**: Initialize to black on first frame.
- **rotation = any value**: Wrap angle to [0, 360].

## Test Plan (minimum ≥80% coverage)
- `test_no_feedback_pass_through` — zero feedback = input only
- `test_feedback_accumulation` — feedback appears in subsequent frames
- `test_feedback_dampening_decay` — dampening reduces feedback strength
- `test_zoom_expansion` — zoom > 1.0 expands feedback
- `test_zoom_contraction` — zoom < 1.0 shrinks feedback
- `test_rotation_angular` — rotation rotates feedback per iteration
- `test_position_offset_movement` — position offset shifts feedback
- `test_color_shift_hue_rotation` — hue rotates per iteration
- `test_blur_smooths_feedback` — blur parameter blurs feedback buffer
- `test_stability_constraint` — dampening prevents explosion
- `test_feedback_explosion_prevented` — dampening >= 0.3 prevents blow-up
- `test_cpu_iterative_approximation` — CPU feedback approximates GPU recursive
- `test_performance_60fps` — sustain ≥60 FPS at 1080p with feedback
- `test_long_sequence_stability` — effect stable over 10+ seconds

## Verification Checkpoints
- [ ] `InfiniteFeedbackEffect` registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly
- [ ] Feedback buffer properly maintained across frames
- [ ] Composition of input and feedback works correctly
- [ ] Zoom factor scales feedback correctly
- [ ] Rotation transforms feedback coordinates correctly
- [ ] Position offset shifts feedback per iteration
- [ ] Color shift rotates hue per iteration
- [ ] Blur on feedback buffer works
- [ ] Dampening prevents feedback explosion
- [ ] CPU fallback produces feedback approximation without crash
- [ ] Presets render hypnotic/tunnel/kaleidoscope effects
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p with typical feedback settings
- [ ] No visual artifacts or aliasing from repeated feedback

## Implementation Handoff Notes
- Feedback buffer management:
  - Use ping-pong buffers (two framebuffers, swap each frame)
  - Clear buffer periodically to prevent DC offset buildup
  - Consider tone-mapping to prevent numerical issues
  
- GPU optimization:
  - Fragment shader handles all transformations
  - Use hardware-accelerated texture filtering for quality
  - Implement dampening in shader (avoid CPU loops)
  
- Stability critical:
  - Hard clamp dampening to [0.3, 1.0] to prevent explosion
  - Monitor luminance; if peak > 1.0, auto-reduce
  - Test with extreme parameter combinations
  
- CPU optimization:
  - Use OpenCV warpAffine for rotation/zoom
  - Vectorize with NumPy for iteration
  - Consider limiting iterations to 3–5 for speed

## Resources
- Reference: vjlive feedback loops, experimental VJ systems
- Math: Recursive geometric transforms, damped oscillation
- GPU: GLSL texture transforms, framebuffer ping-ponging

````
