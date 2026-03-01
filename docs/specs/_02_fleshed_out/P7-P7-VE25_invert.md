````markdown
# P7-VE25: Invert Effect (Color Negative)

> **Task ID:** `P7-VE25`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/color.py`)
> **Class:** `InvertEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `InvertEffect`—a simple
color inversion plugin that turns images into their negative counterpart. This
is frequently used for stylistic treatments, debugging, and visual variation in
VJ setups. Documentation includes exact inversion math, parameter remaps, CPU
fallback, and tests for parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (pixel-wise color inversion)
- Sustain 60 FPS even at high resolutions (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful bypass when effect disabled (Safety Rail 7)
- Provide CPU fallback performing same arithmetic

## Implementation Notes / Porting Strategy
1. Invert each RGB channel: `output = 1.0 - input`.
2. Support optional alpha preservation or inversion mode.
3. Provide opacity control.
4. CPU fallback uses NumPy subtraction.

## Public Interface
```python
class InvertEffect(Effect):
    """
    Invert Effect: Color negative transformation.
    
    Flips color channels to produce a negative image. Includes optional
    alpha inversion and opacity blend. Useful for creative effects and
    diagnostic visualizations.
    """

    def __init__(self, width: int = 1920, height: int = 1080,
                 use_gpu: bool = True):
        """
        Initialize invert effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU inversion; else CPU.
        """
        super().__init__("Invert", INVERT_VERTEX_SHADER,
                         INVERT_FRAGMENT_SHADER)
        
        self.effect_category = "color"
        self.effect_tags = ["invert", "negative", "color"
                           ]
        self.features = ["INVERT"]
        self.usage_tags = ["STYLIZE", "DEBUG"]
        
        self.use_gpu = use_gpu

        self._parameter_ranges = {
            'invert_alpha': (0.0, 10.0),  # whether to flip alpha
            'opacity': (0.0, 10.0)        # blend with original
        }

        self.parameters = {
            'invert_alpha': 0.0,
            'opacity': 10.0
        }

        self._parameter_descriptions = {
            'invert_alpha': "0=no alpha change, 10=invert alpha channel",
            'opacity': "Effect opacity (0=orig, 10=full invert)"
        }

        self._sweet_spots = {
            'opacity': [5.0, 8.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None,
              chain = None) -> int:
        """
        Render inverted image.
        """
        # sample input, compute inverted colors
        # handle alpha inversion if requested
        # blend with original using opacity
        pass

    def apply_uniforms(self, time: float, resolution: tuple,
                      audio_reactor=None, semantic_layer=None):
        """
        Bind inversion parameters.
        """
        pass
```

### Exposed Parameters and Remaps
- `invert_alpha` (float, UI 0—10) → internal `A` = x / 10.0
  - 0 = preserve alpha, 1 = invert alpha
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0

## Effect Math

```
// GPU pseudocode
vec4 src = texture(tex_in, uv);
vec4 inv = vec4(1.0) - src;
if (invert_alpha < 0.5) inv.a = src.a;
vec4 output = mix(src, inv, opacity);
```

CPU fallback:
```python
def invert_cpu(frame, invert_alpha, opacity):
    img = frame.astype(np.float32) / 255.0
    inv = 1.0 - img
    if invert_alpha < 0.5:
        inv[:, :, 3] = img[:, :, 3]
    return ((1-opacity)*img + opacity*inv) * 255
```

## Presets
- `Negative`: opacity=10, invert_alpha=0
- `Ghost`: opacity=5, invert_alpha=0
- `Alpha Negative`: opacity=10, invert_alpha=10
- `Subtle`: opacity=2, invert_alpha=0

## Edge Cases
- Input without alpha: treat alpha as 1.0
- opacity 0 passes through

## Test Plan
- `test_full_inversion`
- `test_partial_opacity`
- `test_alpha_preserve`
- `test_alpha_invert`
- `test_cpu_gpu_parity`
- `test_60fps_performance`

## Verification Points
- [ ] Parameters map correctly
- [ ] Alpha handling works
- [ ] CPU fallback parity

````
