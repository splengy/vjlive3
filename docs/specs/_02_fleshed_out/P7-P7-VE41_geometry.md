# P7-VE41: Scroll Effect (Texture Offset)

> **Task ID:** `P7-VE41`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/geometry.py`)
> **Class:** `ScrollEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
The ScrollEffect continuously shifts the UV coordinates of the input, giving a
seamless scrolling texture. Parameters control horizontal/vertical speed, loop
mode, and jitter. It's widely used for crawl texts, moving backgrounds, and
motion illusions.

## Technical Requirements
- Subclass `Effect` and register with manifest
- Parameters: `speed_x`, `speed_y`, `wrap` (boolean), `opacity`
- Support both GPU (simple UV offset) and CPU fallback (array roll)
- Maintain 60 FPS on 1080p (Safety Rail 1)
- ≥80 % test coverage (Safety Rail 5)
- Spec document concise (<750 lines, Safety Rail 4)
- Proper handling of floating point wrap-around; no NaNs (Safety Rail 7)

## Public Interface
```python
class ScrollEffect(Effect):
    """Continuously scrolls the texture by an offset accumulated from speed."""

    def __init__(self,width=1920,height=1080,use_gpu=True):
        super().__init__("Scroll", SCROLL_VERTEX_SHADER,
                         SCROLL_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["scroll","offset"]
        self.features=["UV_SCROLL"]
        self.usage_tags=["CHOREO","BACKGROUND"]
        self.use_gpu=use_gpu

        self._parameter_ranges={'speed_x':(0.0,10.0),
                                 'speed_y':(0.0,10.0),
                                 'wrap':(0.0,10.0),
                                 'opacity':(0.0,10.0)}
        self.parameters={'speed_x':5.0,'speed_y':5.0,'wrap':10.0,'opacity':10.0}
        self._parameter_descriptions={
            'speed_x':'Horizontal speed (pixels/sec)',
            'speed_y':'Vertical speed (pixels/sec)',
            'wrap':'Wrap when exceeding bounds (0/1)',
            'opacity':'Blend amount'}
        self._sweet_spots={'speed_x':[2,5,8],'speed_y':[2,5,8]}
        self._state={'offset':(0.0,0.0)}

    def render(self,tex_in,extra_textures=None,chain=None):
        # use current offset uniform to sample
        pass

    def apply_uniforms(self,time,resolution,audio_reactor=None,
                      semantic_layer=None):
        # update offset based on speed and time
        # store in self._state and upload
        pass
```

### Parameter Remaps
- `speed_x`/`speed_y` (0–10) → S = map_linear(x,0,10,-100,100) pixels/sec
- `wrap` → W = round(map_linear(x,0,10,0,1))
- `opacity` → α = x/10

Offsets accumulate as `offset += speed * delta_time`.

## Shader Uniforms
- `uniform vec2 offset;`
- `uniform float wrap;`
- `uniform float opacity;`
- `uniform sampler2D tex_in;`
- `uniform vec2 resolution;`

## Effect Math
```
vec2 uv = gl_FragCoord.xy/resolution;
vec2 shifted = uv + offset / resolution;
if (wrap > 0.5) {
    shifted = fract(shifted);
}
vec3 color = texture(tex_in, shifted).rgb;
vec3 orig = texture(tex_in, uv).rgb;
return mix(orig, color, opacity);
```

## CPU Fallback
```python
import numpy as np

def scroll_cpu(frame, offset, wrap, opacity):
    h,w = frame.shape[:2]
    dx,dy = int(offset[0]) % w, int(offset[1]) % h
    out = np.roll(frame, shift=(dy,dx), axis=(0,1))
    if not wrap:
        # zero padding for areas that rolled
        if dx>0:
            out[:,:dx] = 0
        elif dx<0:
            out[:,dx:] = 0
        if dy>0:
            out[:dy,:] = 0
        elif dy<0:
            out[dy:,:] = 0
    return ((1-opacity)*frame + opacity*out).astype(np.uint8)
```

## Presets
- `Right Scroll`: speed_x=8, speed_y=0, wrap=1
- `Diagonal`: speed_x=5, speed_y=5, wrap=1
- `Upward`: speed_x=0, speed_y=-10, wrap=0

## Edge Cases
- Speeds extremely large may overflow; wrap offsets via fract
- Negative speeds permitted
- Time discontinuities (seek) should not accumulate errant values;
  optionally reset when abs(dt)>1

## Test Plan
- `test_speed_remap`
- `test_offset_accumulation`
- `test_wrap_behavior`
- `test_cpu_gpu_comparison`
- `test_zero_wrap_clamp`
- `test_performance_1080p`

## Verification
- [ ] Offset increments correctly with time
- [ ] Wrap toggles between seamless and cut-off
- [ ] CPU fallback matches GPU for sample sequences
- [ ] Presets demonstrate expected movement

---

**Notes:**
Because scroll effects are stateful, be mindful of threading/serialization
when running multiple instances.

