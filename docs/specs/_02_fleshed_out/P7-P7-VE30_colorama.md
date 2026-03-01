````markdown
# P7-VE30: Colorama Effect (Palette Remapping)

> **Task ID:** `P7-VE30`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/vcore/colorama.py`)
> **Class:** `ColoramaEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
`ColoramaEffect` was originally a vjlive‑2 palette remapper allowing artists to
tint video based on an arbitrary 1‑D color map. It samples the luma of the
input and uses it to look up a color from a user‑supplied gradient (the
"colorama"), optionally animating the gradient over time. Our spec reproduces
this functionality with GPU and CPU implementations, comprehensive parameter
controls, and tests ensuring parity.

## Technical Requirements
- Implement as a VJLive3 effect (per‑pixel lookup into gradient texture)
- Support custom 1‑D color ramp via extra texture slot
- Animate offset of gradient over time
- Maintain 60 FPS even with gradient lookups (Safety Rail 1)
- ≥80 % coverage with unit tests (Safety Rail 5)
- Code size < 750 lines (Safety Rail 4)
- Fallback to grayscale if no gradient provided (Safety Rail 7)

## Implementation Notes / Porting Strategy
1. Compute luma for each pixel.
2. Use luma as UV coordinate to sample 1‑D gradient texture (colorama).
3. Allow shift/rotation of lookup for animation.
4. Blend remapped color with original according to opacity.
5. CPU fallback can precompute a LUT from gradient image and apply.

## Public Interface
```python
class ColoramaEffect(Effect):
    """
    Colorama Effect: Gradient-based color remapping.
    """
    def __init__(self, width: int=1920, height: int=1080,
                 use_gpu: bool=True):
        super().__init__("Colorama", COLORAMA_VERTEX_SHADER,
                         COLORAMA_FRAGMENT_SHADER)
        self.effect_category = "color"
        self.effect_tags = ["colorama","palette","ramp"]
        self.features = ["GRADIENT_LOOKUP"]
        self.usage_tags = ["STYLIZE","ANIMATE"]
        
        self.use_gpu = use_gpu
        
        self._parameter_ranges = {
            'offset': (0.0,10.0),       # shift along ramp
            'saturation': (0.0,10.0),   # preserve RGB saturation
            'luma_mode': (0.0,10.0),    # luma/hue/value
            'opacity': (0.0,10.0)
        }
        self.parameters = {'offset':0.0,'saturation':5.0,'luma_mode':0.0,'opacity':10.0}
        self._parameter_descriptions = {
            'offset':"Ramp offset (0..1)",
            'saturation':"Blend between colorama and original saturation",
            'luma_mode':"0=luma,5=hue,10=value",
            'opacity':"Effect opacity"
        }
        self._sweet_spots={'offset':[2.0,5.0,8.0]}

    def render(self, tex_in:int=None, extra_textures:list=None, chain=None) -> int:
        # extra_textures[0] expected to be 1D gradient (colorama)
        # sample input, compute metric (luma/hue/value)
        # sample gradient with metric+offset
        # blend with original
        pass

    def compute_metric(self,color:tuple,mode:int)->float:
        # return value in [0,1] depending on mode
        pass

    def apply_uniforms(self,time:float,resolution:tuple,
                      audio_reactor=None,semantic_layer=None):
        # bind offset,saturation,luma_mode,opacity
        pass
```

### Parameter Remaps
- `offset` (UI 0–10) → `off` = map_linear(x,0,10,0,1)
- `saturation` (UI 0–10) → `sat_blend` = x/10
- `luma_mode` → 0–3=lum,4–6=hue,7–10=val
- `opacity` → α=x/10

## Shader Uniforms
- `uniform float offset;`
- `uniform float sat_blend;`
- `uniform int luma_mode;`
- `uniform float opacity;`
- `uniform sampler2D tex_in;`
- `uniform sampler2D colorama;`  // 1D ramp

## Effect Math

```
vec3 c = texture(tex_in,uv).rgb;
float metric;
if(luma_mode<3) metric = dot(c,vec3(0.2126,0.7152,0.0722));
else if(luma_mode<6) metric = rgb2hsv(c).x;
else metric = rgb2hsv(c).z;
metric = fract(metric + offset);
vec3 ramp = texture(colorama, vec2(metric,0)).rgb;
// preserve saturation
float orig_sat = rgb2hsv(c).y;
ramp = mix(ramp, hsv2rgb(vec3(rgb2hsv(ramp).x, orig_sat, rgb2hsv(ramp).z)), sat_blend);
vec3 outc = mix(c, ramp, opacity);
```

CPU fallback sketch:
```python
def colorama_cpu(frame, gradient, offset, sat_blend, mode, opacity):
    img = frame.astype(np.float32)/255.0
    h,w = img.shape[:2]
    hsv = cv2.cvtColor(img,cv2.COLOR_RGB2HSV)
    if mode<3: metric=hsv[:,:,2]
    elif mode<6: metric=hsv[:,:,0]/360.0
    else: metric=hsv[:,:,2]
    metric = np.mod(metric+offset,1.0)
    lut = cv2.resize(gradient,(256,1)) # assume gradient provided as 256x1
    ramp = cv2.cvtColor(lut,cv2.COLOR_RGB2HSV)/255.0
    ramp_vals = ramp[np.floor(metric*255).astype(int),0]
    # ... convert back etc.
    # omitted details for brevity
    return ((1-opacity)*img + opacity*ramp_rgb)*255
```

## Presets
- `Gray Ramp`: offset=0, sat=0
- `Hue Cycle`: luma_mode=5, offset animates
- `Vintage`: sat=0.3, offset=0.2
- `Selective`: sat=1, opacity=0.5

## Edge Cases
- No `colorama` texture: fall back to grayscale by using metric as output
- `offset` wraps
- `saturation` extremes maintain original color

## Test Plan
- `test_gradient_lookup`
- `test_offset_wrap`
- `test_saturation_blend`
- `test_luma_hue_value_modes`
- `test_cpu_gpu_parity`
- `test_performance_60fps`

## Verification
- [ ] Gradient texture binding
- [ ] Modes switch correctly
- [ ] CPU fallback grayscale

````
