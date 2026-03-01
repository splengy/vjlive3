````markdown
# P7-VE18: Blend Modes (Compositing Operations)

> **Task ID:** `P7-VE18`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/blend_modes.py`)
> **Class:** `_BlendMode`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `_BlendMode`—a comprehensive
blend mode selector effect implementing 15+ standard compositing operations.
Supports frame-to-frame blending, input-to-input compositing, and parameter-
driven mode selection. The objective is to document exact compositing mathematics,
all blend mode operations, parameter remaps, CPU fallback, and comprehensive
tests for feature parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (applies blend operations to dual inputs)
- Sustain 60 FPS with real-time blending (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful fallback to passthrough if no secondary input (Safety Rail 7)
- CPU fallback implementation for compatibility testing

## Implementation Notes / Porting Strategy
1. Implement 15+ blend mode operations (Add, Multiply, Screen, Overlay, etc.).
2. Support per-blend mode opacity/intensity.
3. Optional tone mapping per blend mode.
4. Support dual-input compositing or frame-to-frame.
5. NumPy-based CPU fallback for all modes.
6. Organized mode enumeration for UI selection.

## Public Interface
```python
class _BlendMode(Effect):
    """
    Blend Mode Processor: Comprehensive compositing operations.
    
    Implements 15+ standard blend modes for pixel-level compositing.
    Supports switching between modes, per-mode opacity, and tone mapping.
    Essential for advanced color compositing, layer blending, and
    creative video mixing in VJ and post-production workflows.
    """

    # Blend mode enumeration
    BLEND_MODES = {
        0: "Normal",
        1: "Additive",
        2: "Multiply",
        3: "Screen",
        4: "Overlay",
        5: "Soft Light",
        6: "Hard Light",
        7: "Color Dodge",
        8: "Color Burn",
        9: "Darken",
        10: "Lighten",
        11: "Difference",
        12: "Exclusion",
        13: "Hue",
        14: "Saturation",
        15: "Color"
    }

    def __init__(self, width: int = 1920, height: int = 1080,
                 initial_mode: int = 1, use_gpu: bool = True):
        """
        Initialize blend mode processor.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            initial_mode: Default blend mode (0–15).
            use_gpu: If True, use GPU blending; else CPU.
        """
        super().__init__("Blend Modes", BLENDMODE_VERTEX_SHADER,
                         BLENDMODE_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "compositing"
        self.effect_tags = ["blend", "compositing", "mixing", "modes"]
        self.features = ["BLEND_MODES", "COMPOSITING"]
        self.usage_tags = ["POST_PRODUCTION", "COMPOSITING", "VJ"]
        
        self.use_gpu = use_gpu
        self.current_mode = clamp(initial_mode, 0, 15)

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'blend_mode': (0.0, 10.0),         # mode selector (0–15 mapped)
            'blend_opacity': (0.0, 10.0),      # blend strength
            'base_opacity': (0.0, 10.0),       # base color opacity
            'blend_opacity_alt': (0.0, 10.0),  # alternate opacity for some modes
            'tone_brightness': (0.0, 10.0),    # output brightness
            'tone_contrast': (0.0, 10.0),      # output contrast
            'tone_saturation': (0.0, 10.0),    # output saturation
            'color_tint_hue': (0.0, 10.0),     # optional color tint
            'clipping_mode': (0.0, 10.0),      # clamp, wrap, or soft clip
            'opacity': (0.0, 10.0),            # effect opacity
        }

        # Default parameter values
        self.parameters = {
            'blend_mode': 1.0,                 # Additive
            'blend_opacity': 5.0,
            'base_opacity': 5.0,
            'blend_opacity_alt': 3.0,
            'tone_brightness': 5.0,
            'tone_contrast': 5.0,
            'tone_saturation': 5.0,
            'color_tint_hue': 0.0,
            'clipping_mode': 0.0,              # Clamp
            'opacity': 10.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'blend_mode': "0–2=Normal/Add/Multiply, 3–5=Screen/Overlay/SoftLight, etc.",
            'blend_opacity': "Blend color strength (0=original only, 10=full blend)",
            'base_opacity': "Base layer visibility (0=hidden, 10=opaque)",
            'blend_opacity_alt': "Alternate opacity for Color/Saturation modes",
            'tone_brightness': "Output brightness adjustment",
            'tone_contrast': "Output contrast adjustment",
            'tone_saturation': "Output saturation (0=mono, 10=vivid)",
            'color_tint_hue': "Optional color tint hue (0–10 → 0–360°)",
            'clipping_mode': "0=clamp, 5=wrap, 10=soft clip",
            'opacity': "Effect opacity (0=original, 10=full blend)",
        }

        # Sweet spots
        self._sweet_spots = {
            'blend_mode': [0.0, 3.0, 6.0, 10.0],
            'blend_opacity': [3.0, 5.0, 7.0],
        }

    def render(self, tex_base: int = None, tex_blend: int = None,
              extra_textures: list = None, chain = None) -> int:
        """
        Render blended output using selected blend mode.
        
        Args:
            tex_base: Base texture (required).
            tex_blend: Blend texture (secondary input).
            extra_textures: Optional additional textures.
            chain: Rendering chain context.
            
        Returns:
            Output texture with blend mode applied.
        """
        # Fetch blend mode from parameter
        # Apply corresponding blend operation
        # Apply tone correction
        # Return output
        pass

    def blend_normal(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Normal blend (alpha compositing)."""
        return tuple(base[i] * (1 - alpha) + blend[i] * alpha for i in range(3))

    def blend_additive(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Additive blend (lighten)."""
        return tuple(min(base[i] + blend[i] * alpha, 1.0) for i in range(3))

    def blend_multiply(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Multiply blend (darken)."""
        blend_scaled = tuple(blend[i] * alpha for i in range(3))
        return tuple(base[i] * blend_scaled[i] for i in range(3))

    def blend_screen(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Screen blend (lighten, inverse of multiply)."""
        blend_scaled = tuple(1 - (1 - blend[i]) * alpha for i in range(3))
        return tuple(1 - (1 - base[i]) * (1 - blend_scaled[i]) for i in range(3))

    def blend_overlay(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Overlay blend (multiply if base < 0.5, screen if > 0.5)."""
        result = []
        for i in range(3):
            if base[i] < 0.5:
                result.append(2 * base[i] * (blend[i] * alpha))
            else:
                result.append(1 - 2 * (1 - base[i]) * (1 - blend[i] * alpha))
        return tuple(result)

    def blend_soft_light(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Soft light blend (subtle overlay)."""
        blend_scaled = tuple(blend[i] * alpha for i in range(3))
        result = []
        for i in range(3):
            if blend_scaled[i] < 0.5:
                result.append(base[i] * (1 - (1 - 2 * blend_scaled[i]) * (1 - base[i])))
            else:
                result.append(base[i] + (2 * blend_scaled[i] - 1) * (1 - base[i]))
        return tuple(result)

    def blend_hard_light(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Hard light blend (aggressive overlay)."""
        blend_scaled = tuple(blend[i] * alpha for i in range(3))
        result = []
        for i in range(3):
            if base[i] < 0.5:
                result.append(2 * base[i] * blend_scaled[i])
            else:
                result.append(1 - 2 * (1 - base[i]) * (1 - blend_scaled[i]))
        return tuple(result)

    def blend_color_dodge(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Color dodge blend (brighten, inverse of burn)."""
        blend_scaled = tuple(blend[i] * alpha for i in range(3))
        result = []
        for i in range(3):
            if blend_scaled[i] == 0:
                result.append(base[i])
            else:
                result.append(min(base[i] / (1 - blend_scaled[i]), 1.0))
        return tuple(result)

    def blend_color_burn(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Color burn blend (darken, inverse of dodge)."""
        blend_scaled = tuple(blend[i] * alpha for i in range(3))
        result = []
        for i in range(3):
            if blend_scaled[i] == 1.0:
                result.append(0.0)
            else:
                result.append(1.0 - min((1 - base[i]) / blend_scaled[i], 1.0))
        return tuple(result)

    def blend_darken(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Darken (select darker color per channel)."""
        blend_scaled = tuple(blend[i] * alpha for i in range(3))
        return tuple(min(base[i], blend_scaled[i]) for i in range(3))

    def blend_lighten(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Lighten (select lighter color per channel)."""
        blend_scaled = tuple(blend[i] * alpha for i in range(3))
        return tuple(max(base[i], blend_scaled[i]) for i in range(3))

    def blend_difference(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Difference blend (absolute difference)."""
        blend_scaled = tuple(blend[i] * alpha for i in range(3))
        return tuple(abs(base[i] - blend_scaled[i]) for i in range(3))

    def blend_exclusion(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Exclusion blend (similar to difference, lower contrast)."""
        blend_scaled = tuple(blend[i] * alpha for i in range(3))
        return tuple(base[i] + blend_scaled[i] - 2 * base[i] * blend_scaled[i] for i in range(3))

    def blend_hue(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Hue blend (keep base saturation/lightness, use blend hue)."""
        # Convert to HSL, replace hue
        base_hsl = rgb_to_hsl(base)
        blend_hsl = rgb_to_hsl(tuple(b * alpha for b in blend))
        result_hsl = (blend_hsl[0], base_hsl[1], base_hsl[2])
        return hsl_to_rgb(result_hsl)

    def blend_saturation(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Saturation blend (keep base hue/lightness, use blend saturation)."""
        base_hsl = rgb_to_hsl(base)
        blend_hsl = rgb_to_hsl(tuple(b * alpha for b in blend))
        result_hsl = (base_hsl[0], blend_hsl[1], base_hsl[2])
        return hsl_to_rgb(result_hsl)

    def blend_color(self, base: tuple, blend: tuple, alpha: float) -> tuple:
        """Color blend (keep base lightness, use blend hue/saturation)."""
        base_hsl = rgb_to_hsl(base)
        blend_hsl = rgb_to_hsl(tuple(b * alpha for b in blend))
        result_hsl = (blend_hsl[0], blend_hsl[1], base_hsl[2])
        return hsl_to_rgb(result_hsl)

    def apply_uniforms(self, time: float, resolution: tuple,
                      audio_reactor = None, semantic_layer = None):
        """Apply shader uniforms for blend mode parameters."""
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `blend_mode` (int, UI 0—10) → internal mode:
  - 0: Normal, 1: Additive, 2: Multiply, 3: Screen, 4: Overlay
  - 5: Soft Light, 6: Hard Light, 7: Color Dodge, 8: Color Burn
  - 9: Darken, 10: Lighten
  - (11–15 for modes beyond 10)
- `blend_opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Blend strength [0, 1.0]
- `base_opacity` (float, UI 0—10) → internal `base_α` = x / 10.0
  - Base layer opacity [0, 1.0]
- `tone_brightness` (float, UI 0—10) → internal `bright` = map_linear(x, 0,10, -0.3, 0.3)
  - Brightness adjustment [-0.3, 0.3]
- `tone_contrast` (float, UI 0—10) → internal `contrast` = map_linear(x, 0,10, 0.5, 2.0)
  - Contrast [0.5, 2.0]
- `tone_saturation` (float, UI 0—10) → internal `sat` = x / 10.0
  - Saturation [0 grayscale, 1.0 vivid]
- `color_tint_hue` (float, UI 0—10) → internal `hue` = x / 10.0 * 360.0
  - Hue tint [0, 360°]
- `clipping_mode` (int, UI 0—10) → internal mode:
  - 0–3: Clamp to [0, 1]
  - 4–6: Wrap (modulo)
  - 7–10: Soft clip (tanh-based)
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Effect opacity [0, 1]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`
- `rgb_to_hsl(rgb) → (h, s, l)` — standard conversion
- `hsl_to_rgb(hsl) → (r, g, b)` — standard conversion

## Shader uniforms
- `uniform int blend_mode;`            // selected mode
- `uniform float blend_opacity;`       // blend strength
- `uniform float base_opacity;`        // base visibility
- `uniform float tone_brightness;`     // brightness shift
- `uniform float tone_contrast;`       // contrast scale
- `uniform float tone_saturation;`     // saturation
- `uniform int clipping_mode;`         // clamp/wrap/soft
- `uniform float opacity;`             // effect opacity
- `uniform sampler2D tex_base;`        // base texture
- `uniform sampler2D tex_blend;`       // blend texture

## Effect Math (exact, GPU/CPU-consistent)

### All 16 Blend Modes

See method definitions above for exact pseudocode. Key operations:

```
// For each mode, apply formula to base and blend colors
if mode == 0:    result = mix(base, blend, alpha)      // Normal
if mode == 1:    result = base + blend * alpha         // Add
if mode == 2:    result = base * blend * alpha         // Multiply
if mode == 3:    result = 1 - (1-base) * (1-blend*α)   // Screen
if mode == 4:    result = overlay(base, blend, α)      // Overlay (see method)
if mode == 5:    result = soft_light(base, blend, α)   // Soft Light
...
if mode == 15:   result = color_blend(base, blend, α)  // Color

// Apply tone correction
result = result + tone_brightness
result = 0.5 + (result - 0.5) * tone_contrast
// Saturation and optional tint...

// Clipping
if clipping_mode == 0:    result = clamp(result, 0, 1)
if clipping_mode == 1:    result = fract(result)
if clipping_mode == 2:    result = soft_clip(result)   // tanh-based
```

## CPU Fallback (NumPy sketch)

```python
def blend_cpu(base_frame, blend_frame, mode, opacity, brightness, contrast):
    """Apply blend mode on CPU."""
    base = base_frame.astype(np.float32) / 255.0
    blend = blend_frame.astype(np.float32) / 255.0
    
    if mode == 0:       # Normal
        result = base * (1 - opacity) + blend * opacity
    elif mode == 1:     # Add
        result = base + blend * opacity
    elif mode == 2:     # Multiply
        result = base * (blend * opacity)
    elif mode == 3:     # Screen
        result = 1 - (1 - base) * (1 - blend * opacity)
    else:
        result = base  # Fallback
    
    # Tone
    result = np.clip(result + brightness, 0, 1)
    result = 0.5 + (result - 0.5) * contrast
    
    return (result * 255).astype(np.uint8)
```

## Presets (recommended)
- `Pure Additive`: mode=1, blend_opacity=5.0
- `Darkening Multiply`: mode=2, blend_opacity=6.0, tone_contrast=5.0
- `Screen Brighten`: mode=3, blend_opacity=5.0
- `Smooth Overlay`: mode=4, blend_opacity=4.0, tone_saturation=6.0
- `Difference Edge`: mode=11, blend_opacity=7.0, tone_contrast=8.0
- `Color Dodge Glow`: mode=7, blend_opacity=3.0, tone_brightness=2.0

## Edge Cases and Error Handling
- **blend_mode >= 16**: Clamp to 15 (max mode).
- **Both inputs unavailable**: Passthrough original.
- **NaN from division (Color Dodge/Burn)**: Use safe fallback (0.5).
- **Saturation blend with zero saturation**: Produce grayscale.
- **clipping_mode invalid**: Default to clamp mode.

## Test Plan (minimum ≥80% coverage)
- `test_normal_blend_alpha_compositing` — normal mode blends with alpha
- `test_additive_blend_brightens` — add mode lightens output
- `test_multiply_blend_darkens` — multiply mode darkens output
- `test_screen_blend_lighter` — screen mode lighter than add
- `test_overlay_blend_adaptive` — overlay adapts per pixel
- `test_soft_light_blend_subtle` — soft light non-destructive
- `test_hard_light_blend_aggressive` — hard light stronger
- `test_color_dodge_bright` — dodge mode brightens highlights
- `test_color_burn_dark` — burn mode darkens shadows
- `test_darken_blend_minimum` — darken selects darker per channel
- `test_lighten_blend_maximum` — lighten selects lighter
- `test_difference_blend_edge` — difference produces edge patterns
- `test_exclusion_blend_contrast` — exclusion lower contrast
- `test_tone_brightness_adjustment` — brightness shifts level
- `test_tone_contrast_separation` — contrast adjusts spread
- `test_cpu_vs_gpu_parity` — CPU and GPU outputs match
- `test_performance_60fps` — sustain ≥60 FPS
- `test_mode_transitions` — switching modes produces expected results

## Verification Checkpoints
- [ ] All 16 blend modes implemented and tested
- [ ] Mode selection parameter binds correctly (0–15)
- [ ] Opacity/transparency applied correctly
- [ ] Tone correction (brightness/contrast/saturation) works
- [ ] Color/Hue/Saturation modes convert RGB↔HSL properly
- [ ] CPU fallback produces matching output
- [ ] Presets render correctly
- [ ] Tests pass ≥80% coverage
- [ ] 60 FPS at 1080p with dual inputs
- [ ] No artifacts at blend boundaries

## Implementation Handoff Notes
- Mode implementation checklist: Each mode needs exact pseudocode
- Color space conversions: RGB ↔ HSL/HSV must match across GPU/CPU
- Clipping strategies: Soft clip uses tanh for smooth behavior
- Performance: Avoid conditional branches in inner loops (GPU)

## Resources
- Reference: Photoshop blend modes, standard compositing algorithms
- Math: All formulas above, RGB/HSL color conversions
- GPU: Fragment shader blend mode selection, texture sampling

````
