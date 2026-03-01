````markdown
# P7-VE08: Feedback/Blend Effect

> **Task ID:** `P7-VE08`
> **Priority:** P0 (Critical)
> **Source:** VJlive (`plugins/vcore/blend.py`)
> **Class:** `FeedbackEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete, unambiguous Pass 2 specification for the `FeedbackEffect`—
a flexible multi-input blending effect that combines two or more video signals
using parameterized blend modes (alpha blending, additive, screen, multiply, etc.).
The effect is essential for layer composition, transitions, and creative blending
within VJLive3's node graph. The objective is to document exact blend math,
parameter remaps, multiple blend mode implementations, presets, CPU fallback, and
comprehensive tests for feature parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (typically a mixer/compositor)
- Support ≥2 video inputs with independent blend mode per input (Safety Rail 1)
- Sustain 60 FPS blending at 1080p (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- No silent failures; handle missing or mismatched input resolutions (Safety Rail 7)

## Implementation Notes / Porting Strategy
1. Implement multi-input texture binding and blending.
2. Support 8+ standard blend modes (alpha, add, screen, overlay, etc.).
3. Provide per-input opacity and color modulation.
4. Add transitions between blend modes with smooth interpolation.
5. Provide deterministic NumPy-based CPU fallback (per-pixel blend operations).
6. Include audio reactivity for opacity modulation.

## Public Interface
```python
class FeedbackEffect(Effect):
    """
    Multi-input blend/feedback effect with parameterized mixing.
    
    Combines multiple video inputs using configurable blend modes,
    opacity, and color transforms. Essential for layer composition
    and creative effects within the node graph.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 num_inputs: int = 2, use_gpu: bool = True):
        """
        Initialize the feedback/blend effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            num_inputs: Number of simultaneous inputs (2—4 typical).
            use_gpu: If True, use GPU blending; else CPU per-pixel ops.
        """
        super().__init__("Feedback/Blend", BLEND_VERTEX_SHADER, 
                         BLEND_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "mixer"
        self.effect_tags = ["blend", "mix", "feedback", "compositor"]
        self.features = ["MULTI_INPUT", "PARAMETERIZED_BLENDING"]
        self.usage_tags = ["PROCESSES_VIDEO", "MULTIPLE_INPUTS"]
        
        self.num_inputs = min(num_inputs, 4)  # Cap at 4 for practical limits
        self.use_gpu = use_gpu
        self.active_input_count = 2  # Default to stereo

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'opacity_a': (0.0, 10.0),          # input A visibility
            'opacity_b': (0.0, 10.0),          # input B visibility
            'blend_mode': (0.0, 10.0),         # blend operation selection
            'mix_ratio': (0.0, 10.0),          # crossfade between A and B
            'soft_light': (0.0, 10.0),         # soft light blending strength
            'color_a_r': (0.0, 10.0),          # input A color modulation R
            'color_a_g': (0.0, 10.0),          # input A color modulation G
            'color_a_b': (0.0, 10.0),          # input A color modulation B
            'color_b_r': (0.0, 10.0),          # input B color modulation R
            'color_b_g': (0.0, 10.0),          # input B color modulation G
            'color_b_b': (0.0, 10.0),          # input B color modulation B
        }

        # Default parameter values
        self.parameters = {
            'opacity_a': 10.0,
            'opacity_b': 5.0,
            'blend_mode': 1.0,                 # Alpha blend (default)
            'mix_ratio': 5.0,                  # 50-50 mix
            'soft_light': 0.0,                 # disabled
            'color_a_r': 10.0,
            'color_a_g': 10.0,
            'color_a_b': 10.0,
            'color_b_r': 10.0,
            'color_b_g': 10.0,
            'color_b_b': 10.0,
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'opacity_a': "Input A visibility (0=transparent, 10=opaque)",
            'opacity_b': "Input B visibility (0=transparent, 10=opaque)",
            'blend_mode': "0=alpha, 1=add, 2=screen, 3=overlay, 4=multiply, 5=darken, 6=lighten, 7=difference, 8=exclusion, 9=hard_light, 10=color_dodge",
            'mix_ratio': "Crossfade: 0=all A, 5=equal, 10=all B",
            'soft_light': "Soft light blend strength (0=off, 10=full)",
            'color_a_r': "Input A red channel intensity",
            'color_a_g': "Input A green channel intensity",
            'color_a_b': "Input A blue channel intensity",
            'color_b_r': "Input B red channel intensity",
            'color_b_g': "Input B green channel intensity",
            'color_b_b': "Input B blue channel intensity",
        }

        # Sweet spots
        self._sweet_spots = {
            'opacity_a': [5.0, 8.0, 10.0],
            'opacity_b': [3.0, 5.0, 8.0],
            'blend_mode': [0.0, 2.0, 4.0, 8.0],
            'mix_ratio': [2.0, 5.0, 8.0]
        }

    def render(self, tex_in: int, extra_textures: list = None, 
              chain = None) -> int:
        """
        Blend multiple input textures together.
        
        Args:
            tex_in: Primary input texture (input A).
            extra_textures: List of additional inputs (tex_b, tex_c, tex_d).
                           Must contain at least tex_b for normal operation.
            chain: Rendering chain context.
            
        Returns:
            Blended output texture handle.
        """
        # Bind input textures
        # Apply per-input color modulation
        # Composite using selected blend mode
        # Return blended result
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms for blending parameters.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio for opacity modulation.
            semantic_layer: Optional semantic input.
        """
        # Map UI parameters to shader uniforms
        # Compute normalized opacities and blend factors
        # Bind input textures to samplers
        # Apply audio reactivity if enabled
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `opacity_a` (float, UI 0—10) → internal `α_a` = map_linear(x, 0,10, 0.0, 1.0)
  - Input A blending weight [0, 1]
- `opacity_b` (float, UI 0—10) → internal `α_b` = map_linear(x, 0,10, 0.0, 1.0)
  - Input B blending weight [0, 1]
- `blend_mode` (int, UI 0—10) → internal mode selection:
  - 0: Alpha blending (standard composite)
  - 1: Additive (luminous sum)
  - 2: Screen (inverse multiply)
  - 3: Overlay (soft multiply with screen)
  - 4: Multiply (darkening)
  - 5: Darken (per-channel minimum)
  - 6: Lighten (per-channel maximum)
  - 7: Difference (absolute difference)
  - 8: Exclusion (inverse difference)
  - 9: Hard light (aggressive overlay)
  - 10: Color dodge (brightens highlights)
- `mix_ratio` (float, UI 0—10) → internal `M` = x / 10.0 [0, 1]
  - Blend between A and B: `result = A * (1-M) + B * M`
- `soft_light` (float, UI 0—10) → internal `SL` = map_linear(x, 0,10, 0.0, 1.0)
  - Soft light overlay strength [0, 1]
- `color_a_r`, `color_a_g`, `color_a_b` (float, UI 0—10 each):
  - Input A color modulation channels: map_linear(x, 0,10, 0.0, 2.0) each
  - 10 = full intensity, 5 = half intensity, 0 = off
- `color_b_r`, `color_b_g`, `color_b_b` (float, UI 0—10 each):
  - Input B color modulation channels: map_linear(x, 0,10, 0.0, 2.0) each

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float opacity_a;`            // input A alpha [0,1]
- `uniform float opacity_b;`            // input B alpha [0,1]
- `uniform int blend_mode;`             // blend type (0—10)
- `uniform float mix_ratio;`            // crossfade parameter [0,1]
- `uniform float soft_light;`           // soft light strength
- `uniform vec3 color_mod_a;`           // input A RGB modulation
- `uniform vec3 color_mod_b;`           // input B RGB modulation
- `uniform sampler2D tex_a;`            // input A texture
- `uniform sampler2D tex_b;`            // input B texture
- `uniform sampler2D tex_c;`            // input C (optional)
- `uniform sampler2D tex_d;`            // input D (optional)

## Effect Math (concise, GPU/CPU-consistent)

All blend operations are written to be implementable identically in GLSL and NumPy.

### 1) Color Modulation per Input

Apply RGB scaling to each input:

```
color_a = sample_texture(tex_a, uv) * color_mod_a
color_b = sample_texture(tex_b, uv) * color_mod_b
```

### 2) Blend Mode Selection

a) **Alpha blending**:
```
result = color_a + (color_b - color_a) * opacity_b
```

b) **Additive**:
```
result = color_a * opacity_a + color_b * opacity_b
```

c) **Screen**:
```
result = 1.0 - (1.0 - color_a) * (1.0 - color_b)
```

d) **Overlay**:
```
// If color_a < 0.5: darken with multiply
// If color_a >= 0.5: brighten with screen
overlay_a = mix(color_a * color_b * 2.0,
                 1.0 - 2.0 * (1.0 - color_a) * (1.0 - color_b),
                 step(0.5, color_a))
result = mix(color_a, overlay_a, opacity_b)
```

e) **Multiply**:
```
result = color_a * color_b
```

f) **Darken** (per-channel min):
```
result = min(color_a, color_b)
```

g) **Lighten** (per-channel max):
```
result = max(color_a, color_b)
```

h) **Difference**:
```
result = abs(color_a - color_b)
```

i) **Exclusion**:
```
result = color_a + color_b - 2.0 * color_a * color_b
```

j) **Hard Light**:
```
// Inverted overlay: use color_b as blending layer
hard_light = mix(color_b * color_a * 2.0,
                 1.0 - 2.0 * (1.0 - color_b) * (1.0 - color_a),
                 step(0.5, color_b))
result = hard_light
```

k) **Color Dodge**:
```
result = color_a / (1.0 - color_b + 1e-6)  // guard against division
```

### 3) Crossfade (mix_ratio)

Blend between two mode results:

```
if blend_mode selects single operation:
    result = blend_operation(color_a, color_b, opacity_a, opacity_b)
else:
    result = mix(color_a, color_b, mix_ratio)
```

### 4) Soft Light (Optional)

Additional soft blending:

```
if soft_light > 0:
    soft = soft_light / 2.0
    if color_a < 0.5:
        result = result - (1.0 - 2.0 * color_a) * color_b * (1.0 - soft)
    else:
        result = result + (2.0 * color_a - 1.0) * color_b * soft
```

### 5) Final Compositing

Combine multiple inputs if more than 2:

```
if active_input_count >= 3:
    color_c = sample_texture(tex_c, uv) * color_mod_c
    result = blend(result, color_c, opacity_c)
    
if active_input_count >= 4:
    color_d = sample_texture(tex_d, uv) * color_mod_d
    result = blend(result, color_d, opacity_d)
```

## CPU Fallback (NumPy sketch)

```python
def blend_cpu(frame_a, frame_b, opacity_a, opacity_b, blend_mode, 
              mix_ratio, color_mod_a, color_mod_b):
    """Apply blend operation on CPU via per-pixel operations."""
    
    # Normalize to [0, 1]
    fa = frame_a.astype(np.float32) / 255.0
    fb = frame_b.astype(np.float32) / 255.0
    
    # Apply color modulation
    fa = fa * color_mod_a
    fb = fb * color_mod_b
    
    # Apply blend mode
    if blend_mode == 0:  # alpha
        result = fa * (1.0 - opacity_b) + fb * opacity_b
    elif blend_mode == 1:  # additive
        result = fa * opacity_a + fb * opacity_b
    elif blend_mode == 2:  # screen
        result = 1.0 - (1.0 - fa) * (1.0 - fb)
    elif blend_mode == 4:  # multiply
        result = fa * fb
    # ... other modes ...
    
    # Clamp and convert back
    result = np.clip(result * 255.0, 0, 255).astype(np.uint8)
    return result
```

## Presets (recommended)
- `Smooth Crossfade`:
  - `blend_mode` 0 (alpha), `opacity_a` 10.0, `opacity_b` 0.0,
    `mix_ratio` 5.0, `color_a_r/g/b` 10.0, `color_b_r/g/b` 10.0
- `Additive Glow`:
  - `blend_mode` 1 (additive), `opacity_a` 8.0, `opacity_b` 6.0,
    `color_a_r/g/b` 10.0, `color_b_r/g/b` 10.0
- `Multiply Darken`:
  - `blend_mode` 4 (multiply), `opacity_a` 10.0, `opacity_b` 8.0,
    `mix_ratio` 5.0
- `Screen Bright`:
  - `blend_mode` 2 (screen), `opacity_a` 8.0, `opacity_b` 7.0,
    `mix_ratio` 5.0, `soft_light` 3.0

## Edge Cases and Error Handling
- **Missing input texture**: Use black (0,0,0,1) as fallback.
- **Mismatched resolutions**: Assume inputs will be pre-scaled by upstream nodes.
- **Invalid blend_mode**: Clamp to valid range [0, 10].
- **Color modulation out of bounds**: Clamp to [0, 2] to allow boosting.
- **Zero opacity input**: Effectively removes that input from blend.
- **Audio reactivity**: Optional; no-op if audio_reactor unavailable.

## Test Plan (minimum ≥80% coverage)
- `test_alpha_blend` — alpha mode produces correct weighted average
- `test_additive_blend` — additive mode sums without clamping errors
- `test_screen_blend` — screen mode brightens appropriately
- `test_multiply_blend` — multiply mode darkens appropriately
- `test_overlay_blend` — overlay toggles between multiply and screen at 0.5
- `test_color_modulation_a` — color_a_r/g/b scale input A channels
- `test_color_modulation_b` — color_b_r/g/b scale input B channels
- `test_mix_ratio_bounds` — mix_ratio [0,1] correctly crossfades A to B
- `test_opacity_bounds` — opacity [0,1] properly weights inputs
- `test_soft_light_effect` — soft_light parameter affects blend
- `test_missing_input_fallback` — missing input uses black color gracefully
- `test_cpu_vs_gpu_parity` — CPU and GPU outputs match within tolerance
- `test_performance_60fps` — sustain ≥60 FPS at 1080p

## Verification Checkpoints
- [ ] `FeedbackEffect` class registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly to shader uniforms
- [ ] Multiple input textures bind and render correctly
- [ ] All 10+ blend modes produce expected visual results
- [ ] CPU fallback produces blended output without crashing
- [ ] Presets render distinctive blend combinations
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p with 2+ inputs
- [ ] No safety rail violations

## Implementation Handoff Notes
- Multi-input architecture:
  - Plugin accepts 2+ inputs via `extra_textures` list
  - Each input gets independent opacity, color modulation, blend mode
  - Results composite sequentially (A → B → C → D)
  
- Blend mode performance:
  - GPU: All modes equally fast (texture blending is free)
  - CPU: Some modes (soft light, overlay) are expensive; cache results
  
- Missing inputs:
  - If extra_textures is empty or too short, substitute black texture
  - Log warning but continue gracefully

## Resources
- Reference (blend modes): Photoshop blend modes, SVG compositing spec
- Math: Per-channel RGB operations, gamma-correct blending considerations
- Performance: GPU blend state caching, framebuffer object reuse

````
