````markdown
# P7-VE32: Chromatic Distortion Effect (RGB Warp)

> **Task ID:** `P7-VE32`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/distortion.py`)
> **Class:** `ChromaticDistortionEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
This effect extends simple RGB shift by applying separate spatial distortion
maps to each color channel. It creates psychedelic chromatic warps, heat‑haze
anomalies, or stereo 3D illusions by feeding the UV coordinates of each channel
through independent displacement fields. Our spec must capture per‑channel
wave distortion math, parameter remaps, CPU fallback, and tests to match vjlive
behaviour.

## Technical Requirements
- Implement as a VJLive3 effect plugin
- Accept six displacement parameters (rx, ry, gx, gy, bx, by) expressed as
  spatial offsets modulated by a distortion amount and frequency
- Maintain 60 FPS with three warped texture samples (Safety Rail 1)
- ≥80 % coverage in tests (Safety Rail 5)
- <750 lines of specification (Safety Rail 4)
- Provide graceful no‑distortion bypass and CPU fallback

## Implementation Notes / Porting Strategy
1. Parameterize each channel’s distortion as a sine‑wave field:
   `uv' = uv + amount * sin(uv*freq + phase)` with independent parameters.
2. Compute new UVs per channel, sample the input texture there.
3. Compose channels back into output.
4. CPU fallback uses NumPy and `np.sin` on meshgrid.

## Public Interface
```python
class ChromaticDistortionEffect(Effect):
    """
    Chromatic Distortion Effect: Per-channel UV warping.
    """

    def __init__(self, width: int=1920, height: int=1080,
                 use_gpu: bool=True):
        super().__init__("Chromatic Distortion", CDIST_VERTEX_SHADER,
                         CDIST_FRAGMENT_SHADER)
        self.effect_category = "distortion"
        self.effect_tags = ["chromatic","warp","displacement"]
        self.features = ["UV_WARP"]
        self.usage_tags = ["GLITCH","SURREAL"]

        self.use_gpu = use_gpu

        fields = ['r_amt','r_freq','g_amt','g_freq','b_amt','b_freq','opacity']
        self._parameter_ranges = {f:(0.0,10.0) for f in fields}
        self.parameters = {f:5.0 for f in fields}
        self._parameter_descriptions = {
            'r_amt':'Red channel distortion amount',
            'r_freq':'Red channel distortion frequency',
            'g_amt':'Green channel amount',
            'g_freq':'Green channel frequency',
            'b_amt':'Blue channel amount',
            'b_freq':'Blue channel frequency',
            'opacity':'Effect opacity'
        }
        self._sweet_spots={'r_amt':[4,5,6],'g_amt':[4,5,6],'b_amt':[4,5,6]}

    def render(self, tex_in:int=None, extra_textures:list=None, chain=None)->int:
        # compute uv
        # warp per-channel using sin fields
        # sample and recombine
        pass

    def apply_uniforms(self, time:float, resolution:tuple,
                      audio_reactor=None, semantic_layer=None):
        # remap amounts to pixels, freqs to cycles
        pass
```

### Parameter Remaps
- `*_amt` (UI 0–10) → `[0,0.1]` max displacement fraction of diagonal
- `*_freq` (UI 0–10) → `[0,10]` cycles per unit UV
- `opacity` → α=x/10

## Shader Uniforms
- `uniform vec2 r_dist;` // x=amount,y=freq
- `uniform vec2 g_dist;`
- `uniform vec2 b_dist;`
- `uniform float opacity;
- `uniform vec2 resolution;`
- `uniform sampler2D tex_in;`

## Effect Math

```
vec2 uv=gl_FragCoord.xy/resolution;
vec2 ruv = uv + r_dist.x * sin(uv * r_dist.y * 6.2831);
vec2 guv = uv + g_dist.x * sin(uv * g_dist.y * 6.2831 + 1.0);
vec2 buv = uv + b_dist.x * sin(uv * b_dist.y * 6.2831 + 2.0);
vec3 outc = vec3(
    texture(tex_in, ruv).r,
    texture(tex_in, guv).g,
    texture(tex_in, buv).b);
vec3 orig = texture(tex_in, uv).rgb;
return mix(orig, outc, opacity);
```

CPU fallback:
```python
import numpy as np

def chromatic_distort_cpu(frame, r_dist, g_dist, b_dist, opacity):
    h,w=frame.shape[:2]
    y,x=np.meshgrid(np.linspace(0,1,h),np.linspace(0,1,w),indexing='ij')
    def warp(channel, dist):
        amt,freq=dist
        u = x + amt*np.sin(x*freq*2*np.pi)
        v = y + amt*np.sin(y*freq*2*np.pi)
        return cv2.remap(channel,u.astype(np.float32),v.astype(np.float32),
                         interpolation=cv2.INTER_LINEAR)
    r=warp(frame[:,:,0],r_dist)
    g=warp(frame[:,:,1],g_dist)
    b=warp(frame[:,:,2],b_dist)
    out=np.dstack([r,g,b])
    return ((1-opacity)*frame + opacity*out).astype(np.uint8)
```

## Presets
- `Subtle Wave`: r_amt=2,g_amt=2,b_amt=2
- `RGB Ripple`: r_freq=5,g_freq=5,b_freq=5
- `Chaos`: all amt 8 freq 8
- `Static`: all amt0 (passthrough)

## Edge Cases
- amt=0 → no warp
- freq=0 → constant offset (no oscillation)
- Offsets exceed boundaries → use reflect or wrap sampling

## Test Plan
- `test_passthrough`
- `test_amount_effect`
- `test_frequency_effect`
- `test_opacity_blend`
- `test_cpu_gpu_parity`
- `test_60fps_performance`

## Verification
- [ ] Distortion mapping correct
- [ ] phasing per channel
- [ ] CPU fallback similar

````
