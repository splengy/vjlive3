````markdown
# P7-VE21: Contrast Effect (Tone Mapping & Color Grading)

> **Task ID:** `P7-VE21`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/color.py`)
> **Class:** `ContrastEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `ContrastEffect`—a tone mapping
and color grading effect that adjusts contrast, brightness, levels, and gamma.
Supports multiple tone mapping modes (linear, curve, auto-levels) and full
color channel control. The objective is to document exact tone mapping math,
gamma correction, levels computation, parameter remaps, CPU fallback, and
comprehensive tests for feature parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (tone mapping and color grading)
- Sustain 60 FPS with real-time curve computation (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful passthrough if disabled (Safety Rail 7)
- CPU fallback implementation for compatibility testing

## Implementation Notes / Porting Strategy
1. Implement contrast/brightness adjustment (linear gain).
2. Implement gamma correction (power mapping).
3. Support levels: (black point, white point, gamma).
4. Implement tone curves (linear, S-curve, custom).
5. Support per-channel adjustments (R, G, B).
6. Provide NumPy-based CPU fallback.

## Public Interface
```python
class ContrastEffect(Effect):
    """
    Contrast Effect: Tone mapping and color grading.
    
    Provides comprehensive tone adjustment tools including brightness,
    contrast, gamma, levels, and custom tone curves. Supports per-channel
    adjustment and multiple tone mapping modes. Essential for color
    grading, exposure correction, and creative tone manipulation.
    """

    # Tone curve presets
    TONE_MODES = {
        0: "Linear",
        1: "S-Curve",
        2: "Auto-Levels",
        3: "Sigmoid",
        4: "Power Law",
    }

    def __init__(self, width: int = 1920, height: int = 1080,
                 use_gpu: bool = True):
        """
        Initialize the contrast effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU tone curves; else CPU.
        """
        super().__init__("Contrast Effect", CONTRAST_VERTEX_SHADER,
                         CONTRAST_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "color_grading"
        self.effect_tags = ["contrast", "brightness", "gamma", "tone"]
        self.features = ["TONE_MAPPING", "GAMMA", "LEVELS"]
        self.usage_tags = ["GRADING", "EXPOSURE", "ARCHIVE"]
        
        self.use_gpu = use_gpu

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'brightness': (0.0, 10.0),         # overall brightness
            'contrast': (0.0, 10.0),           # slope around midtones
            'gamma': (0.0, 10.0),              # power mapping
            'black_level': (0.0, 10.0),        # input black point
            'white_level': (0.0, 10.0),        # input white point
            'tone_mode': (0.0, 10.0),          # tone curve type
            'shadows': (0.0, 10.0),            # lift shadows
            'midtones': (0.0, 10.0),           # adjust midtones
            'highlights': (0.0, 10.0),         # compress highlights
            'opacity': (0.0, 10.0),            # effect opacity
        }

        # Default parameter values
        self.parameters = {
            'brightness': 5.0,                 # neutral
            'contrast': 5.0,                   # neutral (1.0)
            'gamma': 5.0,                      # linear (1.0)
            'black_level': 0.0,
            'white_level': 10.0,
            'tone_mode': 0.0,                  # Linear
            'shadows': 5.0,
            'midtones': 5.0,
            'highlights': 5.0,
            'opacity': 10.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'brightness': "Overall luminance shift (0=dark, 10=bright)",
            'contrast': "Slope around midpoint (0=flat, 10=steep)",
            'gamma': "Power correction (0=lift shadows, 10=crush shadows)",
            'black_level': "Input black point (0=black, 10=bright)",
            'white_level': "Input white point (0=dark, 10=white)",
            'tone_mode': "0=linear, 2=S-curve, 4=sigmoid, 6=power, 10=custom",
            'shadows': "Lift/adjust dark areas (0=dark, 10=bright)",
            'midtones': "Adjust mid gray (0=dark, 10=bright)",
            'highlights': "Compress/expand bright areas (0=crush, 10=expand)",
            'opacity': "Effect opacity (0=original, 10=full adjustment)",
        }

        # Sweet spots
        self._sweet_spots = {
            'brightness': [4.0, 5.0, 6.0],
            'contrast': [4.0, 5.0, 6.0],
            'gamma': [4.0, 5.0, 6.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None,
              chain = None) -> int:
        """
        Render tone-mapped output.
        
        Args:
            tex_in: Input texture (required).
            extra_textures: Optional additional textures.
            chain: Rendering chain context.
            
        Returns:
            Output texture with tone mapping applied.
        """
        # Sample input color
        # Apply tone curve based on tone_mode
        # Apply brightness/contrast
        # Apply gamma
        # Apply per-channel adjustments
        # Return output
        pass

    def apply_tone_curve(self, value: float, tone_mode: int,
                        black_level: float, white_level: float,
                        gamma: float) -> float:
        """
        Apply tone curve to normalize input range.
        
        Args:
            value: Input pixel value [0, 1].
            tone_mode: Curve type (0=linear, 1=s-curve, etc).
            black_level: Input black point [0, 1].
            white_level: Input white point [0, 1].
            gamma: Gamma correction [0.1, 3.0].
            
        Returns:
            Tone-mapped value [0, 1].
        """
        # Normalize to black/white levels
        # Apply gamma
        # Apply tone curve
        # Return result
        pass

    def apply_contrast_brightness(self, value: float, brightness: float,
                                 contrast: float) -> float:
        """
        Apply brightness and contrast adjustments.
        
        Args:
            value: Input value [0, 1].
            brightness: Brightness shift [-1, 1].
            contrast: Contrast slope [0.5, 2.0].
            
        Returns:
            Adjusted value [0, 1].
        """
        # Adjust around 0.5 pivot
        # Apply contrast slope first, then brightness
        # Clamp to [0, 1]
        pass

    def apply_curves(self, value: float, shadows: float, midtones: float,
                    highlights: float) -> float:
        """
        Apply 3-point curve adjustment (shadows, midtones, highlights).
        
        Args:
            value: Input value [0, 1].
            shadows: Lift shadows [-1, 1] (dark areas).
            midtones: Adjust midtones [-1, 1].
            highlights: Compress highlights [-1, 1] (bright areas).
            
        Returns:
            Curve-adjusted value [0, 1].
        """
        # Apply piecewise curve adjustments
        # Smooth transitions between zones
        # Return result
        pass

    def apply_uniforms(self, time: float, resolution: tuple,
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms for tone mapping parameters.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input (unused).
            semantic_layer: Optional semantic input (unused).
        """
        # Bind brightness, contrast, gamma, levels to uniforms
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `brightness` (float, UI 0—10) → internal `bright` = map_linear(x, 0,10, -0.5, 0.5)
  - Brightness shift [-0.5, 0.5]
- `contrast` (float, UI 0—10) → internal `contrast` = map_linear(x, 0,10, 0.5, 2.0)
  - Contrast slope [0.5=flat, 2.0=steep]
- `gamma` (float, UI 0—10) → internal `gamma` = map_linear(x, 0,10, 0.4, 2.5)
  - Power mapping [0.4=lifted, 2.5=crushed]
- `black_level` (float, UI 0—10) → internal `black` = x / 10.0
  - Input black point [0, 1.0] (normalized)
- `white_level` (float, UI 0—10) → internal `white` = map_linear(x, 0,10, 0.0, 1.0)
  - Input white point [0, 1.0] (normalized)
- `tone_mode` (int, UI 0—10) → internal mode:
  - 0–2: Linear
  - 3–4: S-Curve
  - 5–6: Auto-Levels
  - 7–8: Sigmoid
  - 9–10: Power Law
- `shadows` (float, UI 0—10) → internal `shadow_lift` = map_linear(x, 0,10, -0.3, 0.3)
  - Shadow adjustment [-0.3, 0.3]
- `midtones` (float, UI 0—10) → internal `midtone_adj` = map_linear(x, 0,10, -0.3, 0.3)
  - Midtone adjustment [-0.3, 0.3]
- `highlights` (float, UI 0—10) → internal `highlight_comp` = map_linear(x, 0,10, -0.3, 0.3)
  - Highlight adjustment [-0.3, 0.3]
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Effect opacity [0, 1]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float brightness;`           // brightness shift
- `uniform float contrast;`             // contrast slope
- `uniform float gamma;`                // power mapping
- `uniform float black_level;`          // input black
- `uniform float white_level;`          // input white
- `uniform int tone_mode;`              // curve type
- `uniform float shadow_lift;`          // shadow adjust
- `uniform float midtone_adjust;`       // midtone adjust
- `uniform float highlight_compress;`  // highlight adjust
- `uniform float opacity;`              // effect opacity
- `uniform sampler2D tex_in;`           // input texture

## Effect Math (concise, GPU/CPU-consistent)

### 1) Levels / Black & White Point

Normalize input to black/white points:

```
// Map input range [black, white] to [0, 1]
normalized = (value - black_level) / (white_level - black_level)
normalized = clamp(normalized, 0, 1)
```

### 2) Gamma Correction

Apply power law mapping:

```
// Gamma curves: gamma < 1 = lift shadows, gamma > 1 = crush shadows
corrected = pow(normalized, 1.0 / gamma)
```

### 3) Contrast & Brightness

```
// Contrast: scale around 0.5 pivot
contrasted = 0.5 + (corrected - 0.5) * contrast

// Brightness: shift all values
brightened = contrasted + brightness

// Clamp
result = clamp(brightened, 0, 1)
```

### 4) S-Curve for Tone Mode

```
// Parametric S-curve
if tone_mode == 1:
    s_curve(v) = 0.5 + (v - 0.5) * (3 - 2 * v^2)  // Smoothstep-like
    result = s_curve(result)
```

### 5) Per-Zone Curve (Shadows/Midtones/Highlights)

```
if value < 0.333:
    // Shadows zone
    zone_value = value / 0.333
    adjustment = shadow_lift * zone_value
else if value < 0.666:
    // Midtones zone
    zone_value = (value - 0.333) / 0.333
    adjustment = midtone_adjust * zone_value
else:
    // Highlights zone
    zone_value = (value - 0.666) / 0.333
    adjustment = highlight_compress * zone_value

result = value + adjustment
result = clamp(result, 0, 1)
```

## CPU Fallback (NumPy sketch)

```python
def contrast_cpu(frame, brightness, contrast, gamma, black_level,
                white_level, shadow_lift, midtone_adj, highlight_comp):
    """Apply tone mapping on CPU."""
    
    img = frame.astype(np.float32) / 255.0
    
    # Levels
    img = (img - black_level) / max(white_level - black_level, 0.001)
    img = np.clip(img, 0, 1)
    
    # Gamma
    img = np.power(img, 1.0 / gamma)
    
    # Contrast/Brightness
    img = 0.5 + (img - 0.5) * contrast + brightness
    img = np.clip(img, 0, 1)
    
    # Zone curves
    shadows_mask = img < 0.333
    midtones_mask = (img >= 0.333) & (img < 0.666)
    highlights_mask = img >= 0.666
    
    img[shadows_mask] += shadow_lift * (img[shadows_mask] / 0.333)
    img[midtones_mask] += midtone_adj * ((img[midtones_mask] - 0.333) / 0.333)
    img[highlights_mask] += highlight_comp * ((img[highlights_mask] - 0.666) / 0.333)
    
    img = np.clip(img, 0, 1)
    return (img * 255).astype(np.uint8)
```

## Presets (recommended)
- `Neutral (No Change)`:
  - `brightness` 5.0, `contrast` 5.0, `gamma` 5.0, `black_level` 0.0, `white_level` 10.0
- `High Contrast`:
  - `brightness` 5.0, `contrast` 7.0, `gamma` 5.0, `black_level` 1.0, `white_level` 9.0
- `Lifted Shadows`:
  - `brightness` 5.0, `contrast` 5.0, `gamma` 3.0, `shadows` 7.0
- `Crushed Blacks`:
  - `brightness` 5.0, `contrast` 6.0, `gamma` 7.0, `highlights` 3.0
- `Cinematic Curve`:
  - `brightness` 5.0, `contrast` 5.5, `gamma` 4.5, `tone_mode` 3.0,
    `shadows` 6.0, `highlights` 4.0

## Edge Cases and Error Handling
- **white_level <= black_level**: Use fallback (passthrough).
- **gamma = 0**: Avoid division; use minimum 0.1.
- **brightness/contrast extreme**: Clamp to [0, 1] after mapping.
- **All zones inactive**: Passthrough original.
- **NaN from pow()**: Use safe fallback value (0.5).

## Test Plan (minimum ≥80% coverage)
- `test_neutral_no_change` — neutral params = input unchanged
- `test_brightness_increases_luminance` — brightness adds to all channels
- `test_contrast_increases_slope` — contrast increases delta from midpoint
- `test_gamma_lift_shadows` — gamma < 1 brightens dark areas
- `test_gamma_crush_shadows` — gamma > 1 darkens light areas
- `test_black_level_clipping` — black point clips dark values
- `test_white_level_scaling` — white point scales bright values
- `test_tone_curve_s_shape` — S-curve reduces contrast in shadows/highlights
- `test_shadow_zone_adjustment` — shadows parameter affects dark areas
- `test_midtone_zone_adjustment` — midtones parameter affects grays
- `test_highlight_zone_adjustment` — highlights parameter affects bright areas
- `test_cpu_vs_gpu_parity` — CPU and GPU outputs match within tolerance
- `test_performance_60fps` — sustain ≥60 FPS at 1080p
- `test_no_artifacts_transitions` — smooth transitions between zones

## Verification Checkpoints
- [ ] `ContrastEffect` registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly
- [ ] Brightness/contrast apply correctly
- [ ] Gamma correction works (lift/crush as expected)
- [ ] Levels (black/white points) normalize correctly
- [ ] Tone curves (S-curve, etc) apply
- [ ] Per-zone adjustments work
- [ ] CPU fallback produces tone-mapped output
- [ ] Presets render at intended tone styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p
- [ ] Smooth transitions, no banding artifacts

## Implementation Handoff Notes
- Tone curve rendering: Pre-compute LUT (256-entry 1D texture) for speed
- Zone transitions: Use smoothstep() for smooth blending between zones
- Gamma: Avoid pow(0, x) edge case; add epsilon
- Performance: Consider 1D lookup texture instead of compute each frame

## Resources
- Reference: Curves tool in Photoshop/GIMP, tone mapping algorithms
- Math: Gamma correction, piecewise curves, contrast formula
- GPU: Fragment shader curve lookups, texture-based LUTs

````
