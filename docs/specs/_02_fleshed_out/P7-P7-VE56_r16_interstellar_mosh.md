# P7-VE56: R16 Interstellar Mosh

> **Task ID:** `P7-VE56`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/vdepth/r16_interstellar_mosh.py`)
> **Class:** `R16InterstellarMosh`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
An otherworldly counterpart to the Deep Mosh Studio, the Interstellar Mosh
layered nebula‑like displacements with chromatic aberration and starfield
feedback. It was a signature effect in VJlive‑2's R16 collection and must be
ported for authenticity.

## Technical Requirements
- Manifest‑registered `Effect` subclass in `src/vjlive3/plugins/other`.
- Expose parameters: `warp`, `star_density`, `shift_speed`, `hue_variation`,
  `feedback_strength`, `opacity`.
- GPU multiple‑pass shader with noise and feedback; CPU fallback using NumPy.
- Maintain 60 FPS at 1080p with moderate settings.
- ≥80 % test coverage, with explicit tests for stateful feedback.
- Keep spec <750 lines; no silent exceptions.

## Public Interface
```python
class R16InterstellarMosh(Effect):
    """Space‑themed mosh with drifting stars and chroma warp."""

    def __init__(self,*args,**kwargs):
        super().__init__("R16InterstellarMosh",
                         vertex_shader=STAR_VERTEX_SHADER,
                         fragment_shader=INTERSTELLAR_FRAGMENT_SHADER)
        self.effect_category="mosh"
        self.effect_tags=["space","feedback","warp"]
        self.features=["FEEDBACK","CHROMA_WARP"]
        self.parameters={
            'warp':5.0,'star_density':5.0,'shift_speed':5.0,
            'hue_variation':5.0,'feedback_strength':5.0,'opacity':10.0}
        self._parameter_ranges={'warp':(0,10),'star_density':(0,10),
                                'shift_speed':(0,10),'hue_variation':(0,10),
                                'feedback_strength':(0,10),'opacity':(0,10)}
        self._param_desc={
            'warp':'Amount of spatial distortion',
            'star_density':'Density of drifting stars',
            'shift_speed':'Speed of starfield motion',
            'hue_variation':'Color shift intensity',
            'feedback_strength':'Feedback layer opacity',
            'opacity':'Overall blend to source'}
        self._state={'feedback_tex':None,'time':0}

    def render(self, tex_in, extra_textures=None, chain=None):
        # handle ping-pong feedback, update self._state['feedback_tex']
        pass

    def apply_uniforms(self, time, resolution, audio=None, semantic=None):
        # remap parameters, update time-based shifts
        pass
```

### Parameter Remaps
- `warp` → W = map_linear(x,0,10,0,1.5)
- `star_density` → S = map_linear(x,0,10,0,1)
- `shift_speed` → V = map_linear(x,0,10,0,2)
- `hue_variation` → H = map_linear(x,0,10,0,0.5)
- `feedback_strength` → F = map_linear(x,0,10,0,1)
- `opacity` → α = x/10

## Shader Uniforms
```
uniform float warp;
uniform float star_density;
uniform float shift_speed;
uniform float hue_variation;
uniform float feedback_strength;
uniform float opacity;
uniform sampler2D feedback_tex;
```

## Effect Math
```
vec2 uv = gl_FragCoord.xy / resolution;
vec3 src = texture(tex_in, uv).rgb;
vec3 stars = generate_starfield(uv, star_density, shift_speed * time);
vec3 warped = texture(tex_in, uv + (noise(uv*warp)-0.5)*0.1).rgb;
warp_hue(warped, hue_variation);
vec3 fb = texture(feedback_tex, uv).rgb * feedback_strength;
vec3 outcol = mix(warped + stars, fb, feedback_strength);
return mix(src, outcol, opacity);
```

## CPU Fallback
```python
import numpy as np

def interstellar_cpu(frame, params, feedback_buf, time):
    h,w = frame.shape[:2]
    warp,star_density,shift_speed,hue_var,fb_strength,opacity = params
    noise = np.random.rand(h,w,3)*warp
    warped = np.roll(frame, int(shift_speed*time)%h, axis=0)
    # quantize hue variation
    # ... simplified for tests
    stars = np.random.rand(h,w,3) * star_density
    if feedback_buf is None:
        fb = np.zeros_like(frame)
    else:
        fb = feedback_buf * fb_strength
    out = frame*(1-opacity) + (((warped+stars)*warp + fb)*opacity)
    return np.clip(out,0,255).astype(np.uint8)
```

## Presets
- `Galaxy Drift`: warp=3, star_density=7, shift_speed=2
- `Nebula Burst`: warp=8, feedback_strength=6, hue_variation=4
- `Dark Matter`: star_density=1, feedback_strength=9, opacity=5

## Edge Cases
- `star_density` clamp ≥0
- Missing `feedback_tex` → blank layer
- Large warp may sample outside; wrap coordinates

## Test Plan
- `test_parameter_remaps`
- `test_feedback_pingpong`
- `test_gpu_cpu_agreement`
- `test_performance_1080p`
- `test_invalid_values_clamp`

## Verification Checklist
- [ ] Starfield moves with time
- [ ] Hue variation component works
- [ ] Feedback layer behaves correctly

---

**Note:** Stateful plugin; tests must reset feedback texture between renders.


