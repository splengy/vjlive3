# P7-VE55: R16 Deep Mosh Studio

> **Task ID:** `P7-VE55`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/vdepth/r16_deep_mosh_studio.py`)
> **Class:** `R16DeepMoshStudio`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
This effect produces a heavyweight, high‑depth mosh distortion designed for
R16-era video feedback hardware. It blends multiple displacement maps,
scatter noise, and color quantization to achieve a deep, organic mosh look.
Porting ensures the classic R16 style remains available in VJLive3.

## Technical Requirements
- Register plugin via manifest and subclass `Effect` (or `FeedbackEffect`)
- Parameters: `intensity`, `noise_scale`, `color_steps`, `feedback_decay`,
  `opacity`
- GPU implementation using multiple passes or shader loops; CPU fallback with
  NumPy pipelines
- Must run at 60 FPS at 1080p with moderate parameter values
- ≥80 % test coverage
- Spec <750 lines and explicit error handling
- Validate nonnegative parameters, quantization steps ≥1

## Public Interface
```python
class R16DeepMoshStudio(Effect):
    """Deep, multi-layer mosh distortion with feedback."""

    def __init__(self,width=1920,height=1080,use_gpu=True):
        super().__init__("R16DeepMosh", R16_VERTEX_SHADER,
                         R16_FRAGMENT_SHADER)
        self.effect_category="morph"
        self.effect_tags=["mosh","feedback","retro"]
        self.features=["MULTI_PASS"]
        self.usage_tags=["STYLING","PERFORMANCE"]
        self.use_gpu=use_gpu

        self._parameter_ranges={'intensity':(0.0,10.0),
                                 'noise_scale':(0.0,10.0),
                                 'color_steps':(0.0,10.0),
                                 'feedback_decay':(0.0,10.0),
                                 'opacity':(0.0,10.0)}
        self.parameters={'intensity':5.0,'noise_scale':5.0,
                         'color_steps':4.0,'feedback_decay':5.0,'opacity':10.0}
        self._parameter_descriptions={
            'intensity':'Overall mosh strength',
            'noise_scale':'Scale of noise displacement',
            'color_steps':'Quantization levels (1..32)',
            'feedback_decay':'How quickly feedback fades',
            'opacity':'Blend with original'}
        self._sweet_spots={'intensity':[4,5,6],'color_steps':[2,4,8]}
        self._state={'feedback_tex':None}

    def render(self,tex_in,extra_textures=None,chain=None):
        # apply displacement and feedback, possibly ping-pong textures
        pass

    def apply_uniforms(self,time,resolution,audio_reactor=None,
                      semantic_layer=None):
        # remap params and manage feedback texture state
        pass
```

### Parameter Remaps
- `intensity` → I = map_linear(x,0,10,0,1)
- `noise_scale` → N = map_linear(x,0,10,0.1,10)
- `color_steps` → C = int(map_linear(x,0,10,1,32))
- `feedback_decay` → D = map_linear(x,0,10,0,1)
- `opacity` → α = x/10

## Shader Uniforms
- `uniform float intensity;`
- `uniform float noise_scale;`
- `uniform int color_steps;`
- `uniform float feedback_decay;`
- `uniform float opacity;`
- `uniform sampler2D feedback_tex;`

## Effect Math
```
vec2 uv = gl_FragCoord.xy / resolution;
vec3 src = texture(tex_in, uv).rgb;
vec3 fb = texture(feedback_tex, uv).rgb * feedback_decay;
vec3 noise = hash(uv * noise_scale);
vec3 warped = texture(tex_in, uv + (noise-0.5)*intensity*0.1).rgb;
vec3 quant = floor(warped * float(color_steps)) / float(color_steps);
vec3 out = mix(src, quant + fb, intensity);
return mix(src, out, opacity);
```

## CPU Fallback
```python
import numpy as np

def r16_cpu(frame, intensity, noise_scale, color_steps,
            feedback_decay, opacity, feedback_buf):
    h,w = frame.shape[:2]
    noise = np.random.rand(h,w,3) * noise_scale
    warped = np.roll(frame, shift=(int(noise_scale),0), axis=(0,1))
    quant = np.floor(warped * color_steps) / color_steps
    if feedback_buf is None:
        fb = np.zeros_like(frame)
    else:
        fb = feedback_buf * feedback_decay
    out = frame * (1-intensity) + (quant+fb) * intensity
    return ((1-opacity)*frame + opacity*out).astype(np.uint8)
```

## Presets
- `Classic R16`: intensity=0.8, color_steps=4
- `Soft Feedback`: feedback_decay=0.2, intensity=0.4
- `Noise Storm`: noise_scale=10, intensity=1

## Edge Cases
- `color_steps <1`: clamp to 1
- `feedback_tex` missing: treat as zeros
- Large noise_scale may alias; wrap values

## Test Plan
- `test_color_quantization`
- `test_feedback_decay`
- `test_cpu_gpu_consistency`
- `test_performance_1080p`
- `test_invalid_params_clamp`

## Verification Checklist
- [ ] Feedback appears and decays properly
- [ ] Noise generates warping relative to intensity
- [ ] CPU fallback approximate enough for tests

---

**Note:** This effect is stateful (feedback); ensure tests reset state between
frames.

