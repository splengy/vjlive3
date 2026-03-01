# P7-VE47: Luma/Chroma Mask Effect

> **Task ID:** `P7-VE47`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/luma_chroma_mask.py`)
> **Class:** `LumaChromaMaskEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
This effect uses separate luminance and chroma thresholds to create a mask
from the input image. Useful for isolating bright/dark regions or particular
colors. The mask can be inverted and feathered. Porting ensures existing VJ
graphics can be replicated precisely.

## Technical Requirements
- Register as plugin subclassing `Effect`
- Parameters: `luma_low`, `luma_high`, `chroma_low`, `chroma_high`,
  `invert`, `feather`, `opacity`
- GPU shader performing YUV conversion, thresholding and mask blending; CPU
  fallback with NumPy/OpenCV
- Support optional chroma key saturation/angle criteria
- 60 FPS at 1080p (Safety Rail 1)
- ≥80 % test coverage (Safety Rail 5)
- Spec <750 lines (Safety Rail 4)
- Validate that low ≤ high, clamp values; booleans for invert (Safety Rail 7)

## Public Interface
```python
class LumaChromaMaskEffect(Effect):
    """Generates a binary mask based on luma and chroma thresholds."""

    def __init__(self,width=1920,height=1080,use_gpu=True):
        super().__init__("LumaChromaMask", MASK_VERTEX_SHADER,
                         MASK_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["mask","luma","chroma"]
        self.features=["MASKING"]
        self.usage_tags=["KEYING","STYLING","COMPOSITING"]
        self.use_gpu=use_gpu

        self._parameter_ranges={'luma_low':(0.0,10.0),
                                 'luma_high':(0.0,10.0),
                                 'chroma_low':(0.0,10.0),
                                 'chroma_high':(0.0,10.0),
                                 'invert':(0.0,10.0),
                                 'feather':(0.0,10.0),
                                 'opacity':(0.0,10.0)}
        self.parameters={'luma_low':0.0,'luma_high':10.0,
                         'chroma_low':0.0,'chroma_high':10.0,
                         'invert':0.0,'feather':0.0,'opacity':10.0}
        self._parameter_descriptions={
            'luma_low':'Minimum luma threshold',
            'luma_high':'Maximum luma threshold',
            'chroma_low':'Minimum chroma magnitude',
            'chroma_high':'Maximum chroma magnitude',
            'invert':'Invert mask (0/1)',
            'feather':'Feather amount (0..0.5)',
            'opacity':'Mask blend amount'}
        self._sweet_spots={'luma_low':[0,2,4],'luma_high':[6,8,10]}

    def render(self,tex_in,extra_textures=None,chain=None):
        # mask computed in fragment shader, blend with original
        pass

    def apply_uniforms(self,time,resolution,audio_reactor=None,
                      semantic_layer=None):
        # remap thresholds and upload
        pass
```

### Parameter Remaps
- `luma_low`/`luma_high` → map_linear(x,0,10,0,1)
- `chroma_low`/`chroma_high` → map_linear(x,0,10,0,1)
- `invert` → I = round(map_linear(x,0,10,0,1))
- `feather` → F = map_linear(x,0,10,0,0.5)
- `opacity` → α = x/10

## Shader Uniforms
- `uniform float luma_low;`
- `uniform float luma_high;`
- `uniform float chroma_low;`
- `uniform float chroma_high;`
- `uniform float invert;`
- `uniform float feather;`
- `uniform float opacity;`
- `uniform sampler2D tex_in;`

Fragment shader converts RGB→YUV, computes mask, then lerps with original.

## Effect Math
```
vec3 rgb = texture(tex_in, uv).rgb;
float y = dot(rgb, vec3(0.299,0.587,0.114));
float u = rgb.b - y;
float v = rgb.r - y;
float chroma = length(vec2(u,v));
float mask = step(luma_low, y) * step(y, luma_high) *
             step(chroma_low, chroma) * step(chroma, chroma_high);
if (invert > 0.5) mask = 1.0 - mask;
if (feather > 0.0) {
    mask = smoothstep(feather, 0.0, abs(y - (luma_low+luma_high)/2.0));
}
vec3 outc = mix(rgb, vec3(0), 1.0 - mask);
return mix(rgb, outc, opacity);
```

## CPU Fallback
```python
import cv2
import numpy as np

def lcm_cpu(frame, luma_low, luma_high,
            chroma_low, chroma_high, invert, feather, opacity):
    yuv = cv2.cvtColor(frame, cv2.COLOR_RGB2YUV).astype(np.float32)/255.0
    y = yuv[:,:,0]
    u = yuv[:,:,1]-0.5
    v = yuv[:,:,2]-0.5
    chroma = np.hypot(u,v)
    mask = ((y>=luma_low)&(y<=luma_high)&
            (chroma>=chroma_low)&(chroma<=chroma_high)).astype(np.float32)
    if invert:
        mask = 1.0 - mask
    if feather>0:
        mask = cv2.GaussianBlur(mask,(0,0),feather*100)
    mask = np.clip(mask,0,1)[:,:,None]
    out = frame * mask + frame * (1-mask)
    return ((1-opacity)*frame + opacity*out).astype(np.uint8)
```

## Presets
- `Luma Key`: luma_low=3, luma_high=7
- `Chroma Key`: chroma_low=4, chroma_high=8
- `Soft Mask`: feather=2, opacity=0.8

## Edge Cases
- `luma_low > luma_high`: swap values
- `chroma_low > chroma_high`: swap
- Thresholds outside [0,1]: clamp

## Test Plan
- `test_threshold_remaps`
- `test_invert_flag`
- `test_feather_blur`
- `test_cpu_gpu_parity`
- `test_opacity_blend`
- `test_performance_1080p`

## Verification Checklist
- [ ] Mask follows luma/chroma ranges
- [ ] Inversion and feathering behave correctly
- [ ] CPU fallback approximates shader

---

**Note:** Could be combined with other masks (e.g. luminance key,
chroma key) in user pipelines; document composition.

