````markdown
# P6-QC13: Trails Effect

> **Task ID:** `P6-QC13`
> **Priority:** P0 (Critical)
> **Source:** VJlive (`plugins/vcore/trails.py`)
> **Class:** `TrailsEffect`
> **Phase:** Phase 6
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete, unambiguous Pass 2 specification for the `TrailsEffect`—
a visual effect that creates persistent motion trails by blending incoming video
with a decaying history buffer. The effect simulates long-exposure photography or
motion blur by accumulating and fading previous frames. The objective is to document
the exact feedback/decay math, parameter remaps, trail composition algorithms,
presets, CPU fallback, and comprehensive tests for feature parity with VJlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (processes input video)
- Maintain proper frame-to-frame persistence at 60 FPS (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful fallback to CPU-based frame accumulation when GPU unavailable (Safety Rail 7)
- No silent failures; handle edge cases (first frame, buffer initialization) correctly

## Implementation Notes / Porting Strategy
1. Implement history buffer management (texture or framebuffer object for accumulation).
2. Use shader-based blending (alpha compositing or additive mixing) to combine
   current frame with decayed history.
3. Provide deterministic NumPy-based CPU fallback (frame averaging).
4. Support multiple trail modes: exponential decay, linear fade, blur, etc.
5. Add optional masking and flow-based trail direction optimization.

## Public Interface
```python
class TrailsEffect(Effect):
    """
    Motion trail effect: persistent trails via frame accumulation.
    
    Renders incoming video with long-exposure trails by blending the current
    frame with a decaying history buffer. Creates visual motion blur and
    persistence effects.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 use_gpu: bool = True):
        """
        Initialize the trails effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU acceleration; else CPU-based blending.
        """
        super().__init__("Trails", TRAILS_VERTEX_SHADER, TRAILS_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "temporal"
        self.effect_tags = ["motion", "blur", "history", "feedback"]
        self.features = ["FRAME_ACCUMULATION", "TEMPORAL_FEEDBACK"]
        self.usage_tags = ["PROCESSES_VIDEO"]
        
        self.use_gpu = use_gpu
        self.history_buffer = None       # Framebuffer or texture for accumulation
        self.history_data = None         # CPU fallback: numpy array (H, W, 3)
        self.initialized = False         # First frame guard

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'trail_length': (0.0, 10.0),       # history persistence (frames)
            'decay_mode': (0.0, 10.0),         # decay function selection
            'blend_mode': (0.0, 10.0),         # compositing mode (alpha, add, max)
            'intensity': (0.0, 10.0),          # trail brightness
            'saturation': (0.0, 10.0),         # color intensity
            'blur_amount': (0.0, 10.0),        # optional blur on history
            'direction_bias': (0.0, 10.0),     # directional trail emphasis
            'feedback_strength': (0.0, 10.0),  # how much history to keep
            'glow': (0.0, 10.0),               # brightness bloom
            'contrast': (0.0, 10.0),           # trail high-pass sharpening
        }

        # Default parameter values
        self.parameters = {
            'trail_length': 5.0,
            'decay_mode': 3.0,                 # exponential (default)
            'blend_mode': 0.0,                 # alpha blend
            'intensity': 8.0,
            'saturation': 8.0,
            'blur_amount': 2.0,
            'direction_bias': 2.0,
            'feedback_strength': 7.0,
            'glow': 2.0,
            'contrast': 5.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'trail_length': "How long trails persist (0=no trails, 10=very long)",
            'decay_mode': "Decay type: 0=linear, 3=exponential, 6=logarithmic, 10=step",
            'blend_mode': "Compositing: 0=alpha, 3=additive, 6=screen, 10=multiply",
            'intensity': "Trail brightness multiplier (0=dark, 10=bright)",
            'saturation': "Trail color saturation (0=grayscale, 10=vibrant)",
            'blur_amount': "Blur applied to history buffer (0=sharp, 10=soft)",
            'direction_bias': "Directional emphasis (0=omni, 10=forward-only)",
            'feedback_strength': "History accumulation rate (0=no trails, 10=max)",
            'glow': "Bloom/glow effect on trails (0=none, 10=intense)",
            'contrast': "Trail sharpness via high-pass (0=flat, 10=crisp)"
        }

        # Sweet spot presets
        self._sweet_spots = {
            'trail_length': [2.0, 5.0, 8.0],
            'feedback_strength': [5.0, 7.0, 9.0],
            'decay_mode': [1.0, 3.0, 6.0]
        }

    def render(self, tex_in: int, extra_textures: list = None, 
              chain = None) -> int:
        """
        Apply trails effect to input texture.
        
        Args:
            tex_in: Input video texture handle.
            extra_textures: Optional (flow field for directional trails).
            chain: Rendering chain context.
            
        Returns:
            Output texture handle with trails applied.
        """
        # Initialize history buffer on first frame
        # Blend current frame with decayed history
        # Apply decay, blur, glow, contrast
        # Write result to output and update history buffer
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms and bind history buffer.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio for parameter modulation.
            semantic_layer: Optional semantic input.
        """
        # Map UI parameters to shader uniforms
        # Bind history texture to shader sampler
        # Compute decay factor based on trail_length
        pass

    def update_history(self, output_texture: int):
        """
        Update history buffer with current output.
        
        Args:
            output_texture: Current frame output to accumulate into history.
        """
        # Copy output to history for next frame
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `trail_length` (float, UI 0—10) → internal `L` = map_linear(x, 0,10, 0.0, 30.0)
  - Number of frames to accumulate (30 frames = 0.5 sec at 60 FPS)
- `decay_mode` (int, UI 0—10) → internal mode selection:
  - 0–2: Linear decay (simplest)
  - 3–5: Exponential decay (smooth, natural-looking)
  - 6–8: Logarithmic decay (slower falloff)
  - 9–10: Step function (distinct trails)
- `blend_mode` (int, UI 0—10) → internal blend type:
  - 0–3: Alpha blending (standard compositing)
  - 4–6: Additive blending (luminous trails)
  - 7–9: Screen blending (bright, glowy)
  - 10: Multiply (darkening trails)
- `intensity` (float, UI 0—10) → internal `I` = map_linear(x, 0,10, 0.5, 2.0)
  - Trail brightness scaling factor
- `saturation` (float, UI 0—10) → internal `Sat` = map_linear(x, 0,10, 0.0, 2.0)
  - Color channel amplification (0 = grayscale, 2 = double saturation)
- `blur_amount` (float, UI 0—10) → internal `B` = map_linear(x, 0,10, 0.0, 4.0)
  - Blur kernel radius (sigma) applied to history
- `direction_bias` (float, UI 0—10) → internal `D` = x / 10.0
  - Directional weighting (0 = isotropic, 1 = from flow field)
- `feedback_strength` (float, UI 0—10) → internal `F` = map_linear(x, 0,10, 0.0, 1.0)
  - History accumulation weight (0 = no history, 1 = full feedback)
- `glow` (float, UI 0—10) → internal `G` = map_linear(x, 0,10, 0.0, 1.0)
  - Bloom intensity (applies threshold + blur to highlights)
- `contrast` (float, UI 0—10) → internal `C` = map_linear(x, 0,10, 0.0, 2.0)
  - High-pass filter strength for sharpening trails

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float trail_length;`         // accumulation length
- `uniform int decay_mode;`            // decay type (0—10)
- `uniform int blend_mode;`            // compositing type (0—10)
- `uniform float intensity;`           // brightness scaling
- `uniform float saturation;`          // color amplification
- `uniform float blur_sigma;`          // blur kernel sigma
- `uniform float direction_bias;`      // flow-based weighting
- `uniform float feedback_strength;`   // history mix weight
- `uniform float glow;`                // bloom threshold & intensity
- `uniform float contrast;`            // high-pass filtering
- `uniform sampler2D tex_current;`     // input frame
- `uniform sampler2D tex_history;`     // accumulated history buffer
- `uniform sampler2D flow_texture;`    // optional optical flow field

## Effect Math (concise, GPU/CPU-consistent)

All math is written to be implementable identically in GLSL and NumPy.

### 1) Frame Accumulation and Decay

Each frame, compute a blended result of current and history:

a) **Decay factor** based on decay_mode:

```
if decay_mode in [0..2]:  // Linear
    decay = max(0.0, 1.0 - (1.0 / trail_length))
    
if decay_mode in [3..5]:  // Exponential
    decay = exp(-1.0 / trail_length)
    
if decay_mode in [6..8]:  // Logarithmic
    decay = (trail_length - 1.0) / trail_length
```

b) **Blend current with history**:

```
color_current = sample_texture(tex_current, uv)
color_history = sample_texture(tex_history, uv)
color_decayed = color_history * decay

// Apply feedback strength
color_blended = mix(color_current, color_decayed, feedback_strength)
```

c) **Blend mode selection**:

```
if blend_mode in [0..3]:  // Alpha blend
    color_out = color_current * (1.0 - alpha) + color_blended * alpha

if blend_mode in [4..6]:  // Additive
    color_out = color_current + color_blended * intensity

if blend_mode in [7..9]:  // Screen (1 - (1-A)*(1-B))
    color_out = 1.0 - (1.0 - color_current) * (1.0 - color_blended)

if blend_mode in [10]:    // Multiply
    color_out = color_current * color_blended
```

### 2) Optional Blur on History

If blur_amount > 0, apply Gaussian blur to history before mixing:

```
color_blurred = gaussian_blur(color_history, blur_sigma)
color_decayed = color_blurred * decay
```

Can use separable convolution (horizontal + vertical passes) for efficiency.

### 3) Color Processing (Saturation, Intensity, Contrast)

```
// Desaturate to luminance, then resat
y = 0.2126 * R + 0.7152 * G + 0.0722 * B
color_desat = vec3(y)
color_sat = mix(color_desat, color_out, saturation)

// Intensity scaling
color_out = color_sat * intensity

// High-pass sharpening (optional)
if contrast > 0:
    color_blur = gaussian_blur(color_out, 2.0)
    color_highpass = color_out - color_blur
    color_out += color_highpass * contrast
```

### 4) Glow / Bloom (Optional)

If glow > 0:

```
// Extract bright areas
y = luminance(color_out)
threshold = 0.7    // adjustable
bright = y > threshold ? color_out : vec3(0)

// Blur bright areas
bright_blurred = gaussian_blur(bright, 4.0)

// Combine
color_out += bright_blurred * glow
```

### 5) Directional Bias (Optional)

If direction_bias > 0 and flow texture available:

```
flow = sample_texture(flow_texture, uv)
flow_direction = normalize(flow)

// Weight history based on backward flow
flow_weight = dot(flow_direction, sample_direction) * direction_bias
color_out *= (1.0 + flow_weight)
```

### 6) History Buffer Update

After computing output, copy to history for next frame:

```
history_buffer = color_out    // for next frame's feedback
```

## CPU Fallback (NumPy sketch)

```python
def trails_cpu(frame_current, history_data, trail_length, decay_mode, 
               blend_mode, intensity, saturation, contrast, feedback_strength):
    """Apply trails effect on CPU using frame accumulation."""
    
    # Initialize history on first frame
    if history_data is None:
        history_data = frame_current.copy().astype(np.float32)
    
    # Compute decay factor
    if decay_mode < 3:
        decay = max(0.0, 1.0 - (1.0 / trail_length))
    elif decay_mode < 6:
        decay = np.exp(-1.0 / trail_length)
    else:
        decay = (trail_length - 1.0) / trail_length
    
    # Decay history
    history_decayed = history_data * decay
    
    # Blend with feedback strength
    frame_current_f = frame_current.astype(np.float32)
    frame_blended = frame_current_f * (1.0 - feedback_strength) + \
                    history_decayed * feedback_strength
    
    # Apply blend mode (simplified alpha for CPU)
    if blend_mode < 5:  # alpha
        frame_out = frame_current_f * 0.5 + frame_blended * 0.5
    else:  # additive
        frame_out = np.clip(frame_current_f + frame_blended, 0, 255)
    
    # Apply saturation & intensity
    frame_out = frame_out * intensity
    
    # Apply contrast via high-pass
    if contrast > 0:
        blur = cv2.GaussianBlur(frame_out, (5, 5), 2.0)
        highpass = frame_out - blur
        frame_out = np.clip(frame_out + highpass * contrast, 0, 255)
    
    # Update history for next frame
    history_data = frame_out.copy()
    
    return frame_out.astype(np.uint8), history_data
```

## Presets (recommended)
- `Soft Bloom`:
  - `trail_length` 5.0, `decay_mode` 3.0 (exponential), `blend_mode` 0.0 (alpha),
    `intensity` 7.0, `feedback_strength` 6.0, `blur_amount` 3.0, `glow` 2.0
- `Bright Streaks`:
  - `trail_length` 8.0, `decay_mode` 1.0 (linear), `blend_mode` 4.0 (additive),
    `intensity` 9.0, `feedback_strength` 8.0, `blur_amount` 1.0, `glow` 4.0
- `Crisp Motion Blur`:
  - `trail_length` 3.0, `decay_mode` 5.0 (exponential), `blend_mode` 0.0,
    `intensity` 8.0, `feedback_strength` 5.0, `blur_amount` 0.5, `contrast` 6.0
- `Painterly`:
  - `trail_length` 6.0, `decay_mode` 6.0 (logarithmic), `blend_mode` 3.0,
    `intensity` 6.0, `feedback_strength` 9.0, `blur_amount` 4.0, `saturation` 9.0

## Edge Cases and Error Handling
- **First frame**: Initialize history buffer from input; no decay on frame 0.
- **Buffer size mismatch**: If resolution changes, reallocate history buffer
  (clear it to black or downsample old history).
- **Extremely high trail_length**: Clamp to reasonable max (60 frames).
- **NaN/Inf in math**: Guard exp() and division operations.
- **GPU memory exhaustion**: Fall back to CPU path with downsampled output.
- **Audio reactivity absence**: Render without audio modulation (silent fail).

## Test Plan (minimum ≥80% coverage)
- `test_decay_linear` — linear decay reduces values correctly per frame
- `test_decay_exponential` — exponential decay approaches asymptote
- `test_blend_alpha` — alpha blend produces correct weighted result
- `test_blend_additive` — additive mode adds brightness without clamping errors
- `test_history_update` — history buffer updates after each frame
- `test_first_frame_init` — first frame initializes history without crashing
- `test_blur_amount_effect` — blur_amount parameter softens trails
- `test_feedback_strength_bounds` — feedback_strength in [0,1] bounds
- `test_saturation_grayscale_conversion` — saturation=0 produces grayscale
- `test_glow_bright_areas` — glow highlights bright regions
- `test_contrast_sharpening` — contrast amplifies high frequencies
- `test_cpu_vs_gpu_parity` — CPU and GPU paths produce pixel-diff comparable output
- `test_performance_60fps` — sustain ≥60 FPS at 1080p
- `test_resolution_change` — handle resolution switch without artifacts

## Verification Checkpoints
- [ ] `TrailsEffect` class registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly to shader uniforms
- [ ] History buffer (GPU texture or CPU array) allocates and updates correctly
- [ ] Decay function produces expected exponential/linear curves
- [ ] CPU fallback produces trails without crashing (headless mode)
- [ ] Presets render trails at expected visual styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p with typical trail settings
- [ ] No safety rail violations

## Implementation Handoff Notes
- Choose GPU accumulation strategy:
  - **Ping-pong framebuffers**: Two FBOs, alternate read/write each frame
  - **Half-precision targets**: RGB16F or RGBA16F for history (sufficient precision)
  - **Texture fetch filtering**: Use LINEAR filtering for history sampling
  
- History buffer lifecycle:
  - Allocate on first render() call matching input resolution
  - Deallocate in destructor or on resolution change
  
- Decay factor precomputation: Store decay as `(exp(-dt / tau))^frame`
  for smooth per-frame exponential decay without expensive exp() calls.

## Resources
- Reference (trail effects): MilkdropWaveform, Resolume trails, TouchDesigner feedback TOP
- Math: Exponential/logarithmic curves, Gaussian blur (separable convolution)
- Performance: Framebuffer ping-pong patterns, half-precision texture formats

````
