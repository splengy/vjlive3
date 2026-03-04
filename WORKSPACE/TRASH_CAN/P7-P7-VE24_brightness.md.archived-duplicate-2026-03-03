````markdown
# P7-VE24: Brightness Effect (Simple Exposure Control)

> **Task ID:** `P7-VE24`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/color.py`)
> **Class:** `BrightnessEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `BrightnessEffect`—a
minimal exposure/brightness adjustment plugin. Unlike `ContrastEffect`, this
effect only shifts luminance up or down without altering contrast or color. It
serves as a lightweight tool for quick video adjustments in live performance and
preprocessing pipelines. The objective is to document the exact brightness math,
parameter remaps, CPU fallback, and comprehensive tests for feature parity with
vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (single-parameter brightness shift)
- Sustain 60 FPS at 4K with simple per-pixel arithmetic (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Effect must degrade gracefully when disabled (Safety Rail 7)
- Provide a CPU fallback trivial implementation

## Implementation Notes / Porting Strategy
1. Accept a single brightness parameter in UI range 0–10.
2. Map to internal shift value [-1.0, 1.0].
3. Add shift to each channel of input color; clamp output.
4. Render with GPU fragment shader or CPU vectorized addition.

## Public Interface
```python
class BrightnessEffect(Effect):
    """
    Brightness Effect: Exposure adjustment.

    Simple per-pixel brightness shift. Useful for quick scene exposure tuning
    and as a building block in chains where more complex grading is unnecessary.
    """

    def __init__(self, width: int = 1920, height: int = 1080,
                 use_gpu: bool = True):
        """
        Initialize brightness effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU arithmetic; else CPU.
        """
        super().__init__("Brightness", BRIGHTNESS_VERTEX_SHADER,
                         BRIGHTNESS_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "color"
        self.effect_tags = ["brightness", "exposure", "luminance"]
        self.features = ["BRIGHTNESS"]
        self.usage_tags = ["LIVE", "PREPROCESS"]
        
        self.use_gpu = use_gpu

        # Parameter ranges (UI 0.0—10.0)
        self._parameter_ranges = {
            'brightness': (0.0, 10.0),    # exposure shift
            'opacity': (0.0, 10.0)        # effect opacity
        }

        # Defaults
        self.parameters = {
            'brightness': 5.0,  # neutral
            'opacity': 10.0
        }

        self._parameter_descriptions = {
            'brightness': "0=dark, 5=neutral, 10=bright",
            'opacity': "Effect opacity (0=off, 10=full)"
        }

        self._sweet_spots = {
            'brightness': [4.0, 5.0, 6.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None,
              chain = None) -> int:
        """
        Render brightness-shifted texture.
        """
        # sample tex_in
        # add brightness shift to each channel
        # clamp and return
        pass

    def apply_uniforms(self, time: float, resolution: tuple,
                      audio_reactor=None, semantic_layer=None):
        """
        Bind brightness and opacity uniforms.
        """
        # compute internal shift
        pass
```

### Exposed Parameters and Remaps
- `brightness` (float, UI 0—10) → internal `B` = map_linear(x, 0,10, -1.0, 1.0)
  - Shift added to each color channel
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Blend amount with original

Remap utility:
`map_linear(v,a,b,c,d) = c + (d-c)*((v-a)/(b-a))`

## Shader Uniforms
- `uniform float brightness;` // shift value
- `uniform float opacity;`    // effect opacity
- `uniform sampler2D tex_in;`

## Effect Math (GPU/CPU-consistent)

```
// GPU fragment pseudocode
vec3 color = texture(tex_in, uv).rgb;
color += vec3(brightness);
color = clamp(color, 0.0, 1.0);
return mix(texture(tex_in, uv).rgb, color, opacity);
```

CPU fallback (NumPy):
```python
def brightness_cpu(frame, shift, opacity):
    img = frame.astype(np.float32) / 255.0
    adjusted = np.clip(img + shift, 0, 1)
    return ((1-opacity)*img + opacity*adjusted)*255
```

## Presets
- `Neutral`: brightness=5, opacity=10
- `Dark`: brightness=3, opacity=10
- `Bright`: brightness=7, opacity=10
- `Half`: brightness=5, opacity=5

## Edge Cases
- `brightness` at extremes clamps to black/white
- `opacity=0` returns original exactly

## Test Plan
- `test_neutral_no_change`
- `test_brightness_darkens`
- `test_brightness_brightens`
- `test_opacity_blend`
- `test_cpu_gpu_parity`
- `test_60fps_performance`

## Verification Checkpoints
- [ ] Parameter mapping correct
- [ ] Uniforms bound properly
- [ ] GPU and CPU outputs match

````
