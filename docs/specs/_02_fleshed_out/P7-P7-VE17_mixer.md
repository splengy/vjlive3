````markdown
# P7-VE17: Mixer Effect (Multi-Input Blending)

> **Task ID:** `P7-VE17`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/blend.py`)
> **Class:** `MixerEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `MixerEffect`—a multi-input
blending effect that combines multiple video streams with flexible mixing
strategies. Supports up to 4 simultaneous inputs with per-input gain,
blend modes, and crossfading. The objective is to document exact mixing
mathematics, blend mode operations, parameter remaps, CPU fallback, and
comprehensive tests for feature parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (processes 1–4 input textures)
- Sustain 60 FPS with multi-input blending (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful fallback if inputs unavailable (Safety Rail 7)
- CPU fallback implementation for compatibility testing

## Implementation Notes / Porting Strategy
1. Accept up to 4 input textures simultaneously.
2. Per-input gain/level control.
3. Multiple blend mode options (add, multiply, screen, overlay, etc.).
4. Crossfade transitions between inputs.
5. Optional master gain and tone control.
6. NumPy-based CPU mixing fallback.

## Public Interface
```python
class MixerEffect(Effect):
    """
    Mixer Effect: Multi-input video blending.
    
    Combines multiple video streams with flexible mixing strategies.
    Supports up to 4 simultaneous inputs, per-input gain, multiple
    blend modes, and crossfading. Essential for live mixing, VJ
    performances, and multi-layer video composition.
    """

    def __init__(self, width: int = 1920, height: int = 1080,
                 num_inputs: int = 2, use_gpu: bool = True):
        """
        Initialize the mixer effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            num_inputs: Number of simultaneous inputs (1–4).
            use_gpu: If True, use GPU blending; else CPU.
        """
        super().__init__("Mixer Effect", MIXER_VERTEX_SHADER,
                         MIXER_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "mixing"
        self.effect_tags = ["mixer", "blend", "multi-input", "crossfade"]
        self.features = ["MULTI_INPUT", "BLEND_MODES", "CROSSFADE"]
        self.usage_tags = ["LIVE", "VJ", "COMPOSITION"]
        
        self.use_gpu = use_gpu
        self.num_inputs = clamp(num_inputs, 1, 4)

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'input_1_gain': (0.0, 10.0),       # input 1 level
            'input_2_gain': (0.0, 10.0),       # input 2 level
            'input_3_gain': (0.0, 10.0),       # input 3 level
            'input_4_gain': (0.0, 10.0),       # input 4 level
            'blend_mode': (0.0, 10.0),         # blending strategy
            'master_gain': (0.0, 10.0),        # overall output level
            'crossfade': (0.0, 10.0),          # transition between inputs
            'tone_brightness': (0.0, 10.0),    # output brightness
            'tone_contrast': (0.0, 10.0),      # output contrast
            'opacity': (0.0, 10.0),            # effect opacity
        }

        # Default parameter values
        self.parameters = {
            'input_1_gain': 5.0,
            'input_2_gain': 5.0,
            'input_3_gain': 5.0,
            'input_4_gain': 5.0,
            'blend_mode': 0.0,                 # additive
            'master_gain': 5.0,
            'crossfade': 5.0,                  # 50/50 mix
            'tone_brightness': 5.0,
            'tone_contrast': 5.0,
            'opacity': 10.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'input_1_gain': "Input 1 level (0=silent, 10=full volume)",
            'input_2_gain': "Input 2 level (0=silent, 10=full volume)",
            'input_3_gain': "Input 3 level (0=silent, 10=full volume)",
            'input_4_gain': "Input 4 level (0=silent, 10=full volume)",
            'blend_mode': "0=add, 2=multiply, 4=screen, 6=overlay, 8=soft-light",
            'master_gain': "Output level (0=silent, 10=very bright)",
            'crossfade': "Transition between inputs (0=1 only, 10=4 only)",
            'tone_brightness': "Add/subtract from all channels",
            'tone_contrast': "Increase/decrease channel separation",
            'opacity': "Effect opacity (0=original, 10=full mixed)",
        }

        # Sweet spots
        self._sweet_spots = {
            'input_1_gain': [3.0, 5.0, 7.0],
            'input_2_gain': [3.0, 5.0, 7.0],
            'blend_mode': [0.0, 4.0, 8.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None,
              chain = None) -> int:
        """
        Render mixed output from multiple inputs.
        
        Args:
            tex_in: Primary input texture (input 1).
            extra_textures: List of additional textures (inputs 2–4).
            chain: Rendering chain context.
            
        Returns:
            Output texture with mixed audio-video applied.
        """
        # Sample all input textures
        # Apply per-input gain
        # Blend according to blend_mode
        # Apply master gain and tone
        # Return output
        pass

    def mix_inputs(self, colors: list, gains: list, blend_mode: int,
                  master_gain: float, tone_brightness: float,
                  tone_contrast: float) -> tuple:
        """
        Mix multiple input colors with blend mode.
        
        Args:
            colors: List of RGB colors [(r,g,b), ...] in [0, 1].
            gains: Per-input gain levels [0, 1].
            blend_mode: Blending mode (0=add, 1=multiply, etc).
            master_gain: Output gain [0, 2].
            tone_brightness: Brightness adjustment [-0.5, 0.5].
            tone_contrast: Contrast adjustment [0.5, 2.0].
            
        Returns:
            Mixed RGB color in [0, 1].
        """
        # Apply per-input gain
        # Blend according to mode
        # Apply tone correction
        # Apply master gain
        # Return result
        pass

    def blend_multiply(self, c1: tuple, c2: tuple) -> tuple:
        """Multiply blend two colors (darken)."""
        return (c1[0]*c2[0], c1[1]*c2[1], c1[2]*c2[2])

    def blend_screen(self, c1: tuple, c2: tuple) -> tuple:
        """Screen blend two colors (lighten)."""
        return (1-(1-c1[0])*(1-c2[0]), 1-(1-c1[1])*(1-c2[1]), 1-(1-c1[2])*(1-c2[2]))

    def blend_overlay(self, c1: tuple, c2: tuple) -> tuple:
        """Overlay blend (multiply if c1 < 0.5, screen if > 0.5)."""
        r = c1[0] < 0.5 and 2*c1[0]*c2[0] or 1-2*(1-c1[0])*(1-c2[0])
        g = c1[1] < 0.5 and 2*c1[1]*c2[1] or 1-2*(1-c1[1])*(1-c2[1])
        b = c1[2] < 0.5 and 2*c1[2]*c2[2] or 1-2*(1-c1[2])*(1-c2[2])
        return (r, g, b)

    def apply_uniforms(self, time: float, resolution: tuple,
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms for mixer parameters.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input (unused).
            semantic_layer: Optional semantic input (unused).
        """
        # Bind input gain and blend parameters to uniforms
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `input_1_gain` (float, UI 0—10) → internal `g1` = x / 10.0
  - Input 1 gain [0, 1.0]
- `input_2_gain` (float, UI 0—10) → internal `g2` = x / 10.0
  - Input 2 gain [0, 1.0]
- `input_3_gain` (float, UI 0—10) → internal `g3` = x / 10.0
  - Input 3 gain [0, 1.0]
- `input_4_gain` (float, UI 0—10) → internal `g4` = x / 10.0
  - Input 4 gain [0, 1.0]
- `blend_mode` (int, UI 0—10) → internal mode:
  - 0–1: Additive (brighten)
  - 2–3: Multiply (darken)
  - 4–5: Screen (lighter)
  - 6–7: Overlay (adaptive)
  - 8–10: Soft light (subtle)
- `master_gain` (float, UI 0—10) → internal `master` = map_linear(x, 0,10, 0.5, 2.0)
  - Master output level [0.5, 2.0]
- `crossfade` (float, UI 0—10) → internal `fade` = x / 10.0
  - Crossfade factor [0 input1, 1 input4] (interpolates between inputs)
- `tone_brightness` (float, UI 0—10) → internal `bright` = map_linear(x, 0,10, -0.3, 0.3)
  - Brightness adjustment [-0.3, 0.3]
- `tone_contrast` (float, UI 0—10) → internal `contrast` = map_linear(x, 0,10, 0.5, 2.0)
  - Contrast [0.5=low, 2.0=high]
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Effect opacity [0, 1]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float input_1_gain;`        // input 1 level
- `uniform float input_2_gain;`        // input 2 level
- `uniform float input_3_gain;`        // input 3 level
- `uniform float input_4_gain;`        // input 4 level
- `uniform int blend_mode;`            // blending strategy
- `uniform float crossfade;`           // transition between inputs
- `uniform float master_gain;`         // output level
- `uniform float tone_brightness;`     // brightness adjustment
- `uniform float tone_contrast;`       // contrast adjustment
- `uniform float opacity;`             // effect opacity
- `uniform vec2 resolution;`           // screen size
- `uniform sampler2D tex_1;`           // input texture 1
- `uniform sampler2D tex_2;`           // input texture 2 (optional)
- `uniform sampler2D tex_3;`           // input texture 3 (optional)
- `uniform sampler2D tex_4;`           // input texture 4 (optional)

## Effect Math (concise, GPU/CPU-consistent)

### 1) Per-Input Gain Application

For each input, scale color by gain:

```
color_1 = texture(tex_1, uv) * input_1_gain
color_2 = texture(tex_2, uv) * input_2_gain
color_3 = texture(tex_3, uv) * input_3_gain
color_4 = texture(tex_4, uv) * input_4_gain
```

### 2) Crossfading Between Inputs

Smooth transition between available inputs:

```
// Crossfade blends between inputs based on fade parameter [0, 1]
if num_inputs == 2:
    blended = mix(color_1, color_2, crossfade)
elif num_inputs == 3:
    if crossfade < 0.5:
        blended = mix(color_1, color_2, crossfade * 2.0)
    else:
        blended = mix(color_2, color_3, (crossfade - 0.5) * 2.0)
elif num_inputs == 4:
    if crossfade < 0.333:
        blended = mix(color_1, color_2, crossfade * 3.0)
    else if crossfade < 0.666:
        blended = mix(color_2, color_3, (crossfade - 0.333) * 3.0)
    else:
        blended = mix(color_3, color_4, (crossfade - 0.666) * 3.0)
```

### 3) Blend Mode Operations

```
if blend_mode == 0:                  // ADDITIVE
    result = color_1 + color_2 + ...

elif blend_mode == 1:                // MULTIPLY
    result = color_1 * color_2 * ...

elif blend_mode == 2:                // SCREEN
    result = 1.0 - (1.0 - color_1) * (1.0 - color_2) * ...

elif blend_mode == 3:                // OVERLAY
    // Adaptive blend: multiply if base < 0.5, screen if > 0.5
    for each channel:
        if base < 0.5:
            result = 2 * base * blend
        else:
            result = 1 - 2 * (1 - base) * (1 - blend)

elif blend_mode == 4:                // SOFT LIGHT
    blend_factor = 0.5
    result = mix(2 * base * blend, 1 - 2 * (1 - base) * (1 - blend), blend_factor)

// Clamp to valid range
result = clamp(result, 0, 1)
```

### 4) Tone Correction

Apply brightness and contrast adjustments:

```
// Brightness: shift all channels
result = result + tone_brightness

// Contrast: scale around 0.5 pivot
result = 0.5 + (result - 0.5) * tone_contrast

// Master gain: scale overall level
result = result * master_gain

// Clamp again
result = clamp(result, 0, 1)

// Final opacity blend
final = mix(original, result, opacity)
```

## CPU Fallback (NumPy sketch)

```python
def mixer_cpu(inputs, gains, blend_mode, master_gain, 
             tone_brightness, tone_contrast, crossfade):
    """Mix multiple input frames."""
    
    # Normalize inputs to [0, 1]
    frames = [inp.astype(np.float32) / 255.0 for inp in inputs]
    h, w = frames[0].shape[:2]
    
    # Apply per-input gain
    gained = [frame * gains[i] for i, frame in enumerate(frames)]
    
    if blend_mode == 0:  # Additive
        result = np.zeros((h, w, 3))
        for frame in gained:
            result += frame
    elif blend_mode == 1:  # Multiply
        result = np.ones((h, w, 3))
        for frame in gained:
            result *= frame
    elif blend_mode == 2:  # Screen
        result = np.ones((h, w, 3))
        for frame in gained:
            result = 1.0 - (1.0 - result) * (1.0 - frame)
    else:  # Default to additive
        result = sum(gained)
    
    # Apply tone
    result = result + tone_brightness
    result = 0.5 + (result - 0.5) * tone_contrast
    result = result * master_gain
    result = np.clip(result, 0, 1)
    
    return (result * 255).astype(np.uint8)
```

## Presets (recommended)
- `Simple Mix (50/50)`:
  - `input_1_gain` 5.0, `input_2_gain` 5.0, `blend_mode` 0.0 (add),
    `master_gain` 5.0, `opacity` 10.0
- `Fade to Dark (Multiply)`:
  - `input_1_gain` 7.0, `input_2_gain` 3.0, `blend_mode` 2.0 (multiply),
    `master_gain` 6.0, `opacity` 9.0
- `Bright Overlay`:
  - `input_1_gain` 5.0, `input_2_gain` 7.0, `blend_mode` 4.0 (screen),
    `tone_brightness` 2.0, `master_gain` 5.0, `opacity` 10.0
- `Smooth Crossfade`:
  - `input_1_gain` 5.0, `input_2_gain` 5.0, `crossfade` 5.0,
    `blend_mode` 1.0 (soft), `tone_contrast` 5.0, `opacity` 10.0

## Edge Cases and Error Handling
- **num_inputs = 0**: Revert to passthrough (original texture).
- **All gains = 0**: Return black frame (or passthrough if opacity = 0).
- **No secondary input available**: Use primary input only.
- **Crossfade outside [0, 1]**: Clamp to valid range.
- **NaN from blend operation**: Use safe fallback (additive).
- **Master gain = 0**: Output black; don't underflow.

## Test Plan (minimum ≥80% coverage)
- `test_single_input_passthrough` — 1 input, all others zero
- `test_per_input_gain_scaling` — gain parameter scales each input
- `test_additive_blend_brightens` — additive mode increases brightness
- `test_multiply_blend_darkens` — multiply mode decreases brightness
- `test_screen_blend_lighter` — screen mode produces lighter output
- `test_overlay_blend_adaptive` — overlay adapts per channel brightness
- `test_soft_light_blend_subtle` — soft light is subtle, non-destructive
- `test_crossfade_transitions` — crossfade smoothly transitions between inputs
- `test_tone_brightness_adjustment` — brightness parameter shifts overall level
- `test_tone_contrast_separation` — contrast adjusts channel separation
- `test_master_gain_output_level` — master gain scales final output
- `test_cpu_vs_gpu_parity` — CPU and GPU outputs match within tolerance
- `test_performance_60fps` — sustain ≥60 FPS with 2 inputs at 1080p
- `test_opacity_parameter` — opacity blends with original

## Verification Checkpoints
- [ ] `MixerEffect` registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly
- [ ] Per-input gain applies correctly
- [ ] All blend modes produce distinct outputs
- [ ] Crossfade transitions smoothly between inputs
- [ ] Tone brightness/contrast adjust output correctly
- [ ] Master gain scales output level
- [ ] CPU fallback produces mixed output without crash
- [ ] Presets render at intended mixing styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p with 2+ inputs
- [ ] No visual artifacts from blend boundaries

## Implementation Handoff Notes
- Performance optimization:
  - GPU: Use texture sampling and hardware blending
  - CPU: Vectorize all operations with NumPy
  - Consider multi-threaded input sampling
  
- Blending considerations:
  - Additive mode can cause overexposure; cap with master_gain
  - Multiply mode can over-darken; use moderate gains
  - Screen mode lighter overall; may need lower gains
  - Overlay/Soft light best for subtle mixing
  
- Crossfading strategy:
  - 2 inputs: Linear interpolation [0, 1]
  - 3 inputs: Two segments [0, 0.5] and [0.5, 1]
  - 4 inputs: Three segments [0, 0.33], [0.33, 0.67], [0.67, 1]
  - Use mix() for smooth transitions
  
- Tone correction:
  - Brightness shift: clip to [0, 1] after adjustment
  - Contrast: maintain median by pivoting at 0.5
  - Watch for clipping artifacts with extreme settings

## Resources
- Reference: vjlive mixer, multi-input compositing, blend mode operations
- Math: RGB blending formulas, color theory, crossfading techniques
- GPU: Multi-texture sampling, fragment shaders, hardware blending

````
