# P7-VE54: Warhol Quad Effect

> **Task ID:** `P7-VE54`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/vstyle/pop_art_effects.py`)
> **Class:** `WarholQuadEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
This variant of the pop-art plugin splits the frame into four quadrants,
applying distinct color transforms to each (à la Andy Warhol’s silkscreens).
Parameters control the color palettes, border thickness, and spacing. We'll
port from VJlive-2's implementation which used a simple grid and hue offsets.

## Technical Requirements
- Register as plugin and subclass `Effect`
- Parameters: `colors` (4 hues), `border`, `padding`, `grayscale`, `opacity`
- GPU shader slices the image into quads, applies color overlays; CPU fallback
  uses PIL operations
- Maintain 60 FPS at 1080p with realtime parameter updates
- ≥80 % test coverage
- Spec <750 lines
- Validate color values in [0,1], border and padding non‑negative

## Public Interface
```python
class WarholQuadEffect(Effect):
    """Divides frame into four colored quadrants Warhol-style."""

    def __init__(self,width=1920,height=1080,use_gpu=True):
        super().__init__("WarholQuad", WARHOL_VERTEX_SHADER,
                         WARHOL_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["pop-art","quad","color"]
        self.features=["QUAD_SPLIT"]
        self.usage_tags=["STYLING"]
        self.use_gpu=use_gpu

        self._parameter_ranges={
            'color0':(0.0,10.0),'color1':(0.0,10.0),
            'color2':(0.0,10.0),'color3':(0.0,10.0),
            'border':(0.0,10.0),'padding':(0.0,10.0),
            'grayscale':(0.0,10.0),'opacity':(0.0,10.0)}
        self.parameters={
            'color0':0.0,'color1':2.5,'color2':5.0,'color3':7.5,
            'border':1.0,'padding':0.0,'grayscale':0.0,'opacity':10.0}
        self._parameter_descriptions={
            'color0':'Hue for quadrant 0',
            'color1':'Hue for quadrant 1',
            'color2':'Hue for quadrant 2',
            'color3':'Hue for quadrant 3',
            'border':'Border thickness between quads (px)',
            'padding':'Padding inside each quad (px)',
            'grayscale':'Desaturate original before coloring',
            'opacity':'Blend amount'}
        self._sweet_spots={'border':[1,5,10]}

    def render(self,tex_in,extra_textures=None,chain=None):
        # sample each quadrant, tint by hue and composite
        pass

    def apply_uniforms(self,time,resolution,audio_reactor=None,
                      semantic_layer=None):
        # convert hues back to 0..1, upload any scalars
        pass
```

### Parameter Remaps
- `colorN` → HN = map_linear(x,0,10,0,1)
- `border` → B = map_linear(x,0,10,0,50) pixels
- `padding` → P = map_linear(x,0,10,0,50) pixels
- `grayscale` → G = round(map_linear(x,0,10,0,1))
- `opacity` → α = x/10

## Shader Uniforms
- `uniform float hues[4];`
- `uniform float border;`
- `uniform float padding;`
- `uniform int grayscale;`
- `uniform float opacity;`
- `uniform vec2 resolution;`

## Effect Math
```
vec2 uv = gl_FragCoord.xy / resolution;
vec2 half = vec2(0.5,0.5);
vec3 src = texture(tex_in, uv).rgb;
if (grayscale>0) src = vec3(dot(src, vec3(0.299,0.587,0.114)));
vec3 out = src;
if (uv.x<0.5 && uv.y<0.5) out *= hsv2rgb(vec3(hues[0],1,1));
else if (uv.x>=0.5 && uv.y<0.5) out *= hsv2rgb(vec3(hues[1],1,1));
else if (uv.x<0.5 && uv.y>=0.5) out *= hsv2rgb(vec3(hues[2],1,1));
else out *= hsv2rgb(vec3(hues[3],1,1));
// apply borders/padding by masking if within threshold
return mix(src, out, opacity);
```

## CPU Fallback
```python
from PIL import Image, ImageDraw
import numpy as np

def warhol_cpu(frame, hues, border, padding, grayscale, opacity):
    h,w=frame.shape[:2]
    img = Image.fromarray(frame)
    if grayscale:
        img = img.convert('L').convert('RGB')
    out = np.array(img).astype(np.float32)/255.0
    quads = [out[:h//2,:w//2], out[:h//2,w//2:],
             out[h//2:,:w//2], out[h//2:,w//2:]]
    for i,q in enumerate(quads):
        color = hsv_to_rgb((hues[i],1,1))
        quads[i] = q * color
    arranged = np.vstack([np.hstack([quads[0],quads[1]]),
                           np.hstack([quads[2],quads[3]])])
    return ((1-opacity)*out + opacity*arranged*255).astype(np.uint8)
```

## Presets
- `Classic Warhol`: hues=[0,0.25,0.5,0.75]
- `Monochrome`: grayscale=1
- `Padded`: padding=10

## Edge Cases
- hues wrap seamlessly
- border/padding clamped to prevent overlap

## Test Plan
- `test_quadrant_hues`
- `test_grayscale_toggle`
- `test_border_padding`
- `test_cpu_gpu_parity`
- `test_performance_1080p`

## Verification Checklist
- [ ] Four quadrants show distinct tints
- [ ] Grayscale desaturates input correctly
- [ ] Borders appear and respect padding

---

**Note:** This effect is straightforward combinatorials; future improvements
could allow arbitrary grid sizes.

