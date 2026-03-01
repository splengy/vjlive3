````markdown
# P7-VE26: Threshold Effect (Binary Posterize)

> **Task ID:** `P7-VE26`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/color.py`)
> **Class:** `ThreshEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `ThreshEffect`—a simple
binary thresholding and posterization effect. It converts each pixel to either
black or white (or two chosen colors) based on brightness threshold, optionally
in RGB or luma mode. Frequently used for high-contrast, stylized visuals or
edge detection enhancement in VJ performances. The specification includes
exact math, parameter remaps, CPU fallback, and tests for parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (brightness thresholding)
- Sustain 60 FPS with per-pixel comparisons (Safety Rail 1)
- ≥80% unit/test coverage (Safety Rail 5)
- Code size <750 lines (Safety Rail 4)
- Provide graceful pass-through if threshold disabled (Safety Rail 7)
- Allow CPU fallback

## Implementation Notes / Porting Strategy
1. Compute grayscale or luma per pixel.
2. Compare to threshold parameter.
3. Output chosen high or low color.
4. Support hue thresholding optionally.

## Public Interface
```python
class ThreshEffect(Effect):
    """
    Thresh Effect: Binary threshold / posterize.

    Converts video to a two-tone image based on brightness or hue
    threshold. Useful for stylized high-contrast visuals and mid-ground
    detection.
    """

    def __init__(self, width: int = 1920, height: int = 1080,
                 use_gpu: bool = True):
        super().__init__("Threshold", THRESH_VERTEX_SHADER,
                         THRESH_FRAGMENT_SHADER)
        
        self.effect_category = "color"
        self.effect_tags = ["threshold", "binary", "posterize"]
        self.features = ["THRESHOLD"]
        self.usage_tags = ["STYLIZE", "EDGE"]
        
        self.use_gpu = use_gpu

        self._parameter_ranges = {
            'threshold': (0.0, 10.0),    # cutoff
            'mode': (0.0, 10.0),         # brightness or hue
            'low_color': (0.0, 10.0),    # choose presets
            'high_color': (0.0, 10.0),
            'opacity': (0.0, 10.0)
        }

        self.parameters = {
            'threshold': 5.0,
            'mode': 0.0,
            'low_color': 0.0,   # black
            'high_color': 10.0, # white
            'opacity': 10.0
        }

        self._parameter_descriptions = {
            'threshold': "0=all low, 5=midpoint, 10=all high",
            'mode': "0=brightness, 5=luma, 10=hue",
            'low_color': "0=black, 5=mid, 10=white",
            'high_color': "0=black, 5=mid, 10=white",
            'opacity': "Effect opacity"
        }

        self._sweet_spots = {
            'threshold': [4.0, 5.0, 6.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None,
              chain = None) -> int:
        # sample color
        # compute metric depending on mode
        # compare to threshold
        # choose low/high color
        # blend with original
        pass

    def compute_metric(self, color: tuple, mode: int) -> float:
        # brightness = (r+g+b)/3
        # luma = dot(color, vec3(0.2126,0.7152,0.0722))
        # hue = rgb2hsv(color).x
        pass

    def select_color(self, low: tuple, high: tuple, t: bool) -> tuple:
        return high if t else low

    def apply_uniforms(self, time: float, resolution: tuple,
                      audio_reactor=None, semantic_layer=None):
        pass
```

### Parameters and Remaps
- `threshold` (float, 0–10) → `T` = map_linear(x,0,10,0,1)
- `mode` (int, 0–10) → 0=brightness, 5=luma, 10=hue
- `low_color`/`high_color` choose among presets black, gray, white
  convert to RGB internally
- `opacity` → α = x/10

## Shader Uniforms
- `uniform float threshold;`
- `uniform int mode;`
- `uniform vec3 low_color;`
- `uniform vec3 high_color;`
- `uniform float opacity;`
- `uniform sampler2D tex_in;`

## Effect Math

```
vec3 c = texture(tex_in, uv).rgb;
float metric = 0.0;
if(mode < 3) metric = (c.r+c.g+c.b)/3.0;
else if(mode < 7) metric = dot(c, vec3(0.2126,0.7152,0.0722));
else metric = rgb2hsv(c).x;
bool hi = metric > threshold;
vec3 outc = hi ? high_color : low_color;
return mix(c, outc, opacity);
```

CPU fallback:
```python
def thresh_cpu(frame, threshold, mode, low_color, high_color, opacity):
    img = frame.astype(np.float32)/255.0
    if mode < 3:
        metric = img.mean(axis=2)
    elif mode < 7:
        metric = 0.2126*img[:,:,0] + 0.7152*img[:,:,1] + 0.0722*img[:,:,2]
    else:
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        metric = hsv[:,:,0]
    mask = metric > threshold
    out = np.zeros_like(img)
    out[mask] = high_color
    out[~mask] = low_color
    return ((1-opacity)*img + opacity*out)*255
```

## Presets
- `Classic B/W`: threshold=5, low=black, high=white
- `Bright Map`: threshold=7, low=gray, high=white
- `Hue Split`: mode=10, threshold=0.5, low=blue, high=red
- `Subtle`: threshold=4, low=darkgray, high=lightgray

## Edge Cases
- `threshold 0` → all pixels high
- `threshold 1` → all pixels low
- `mode between ranges` → segmented as above
- `opacity 0` → passthrough

## Test Plan
- `test_binary_conversion`
- `test_mode_brightness_luma_hue`
- `test_color_choice`
- `test_opacity_blend`
- `test_cpu_gpu_parity`
- `test_performance_60fps`

## Verification
- [ ] Mode switching correct
- [ ] Low/high colors applied
- [ ] CPU fallback same

````
