# P7-VE49: Milkdrop Effect (Visualizer)

> **Task ID:** `P7-VE49`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/core/milkdrop/milkdrop.py`)
> **Class:** `MilkdropEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Milkdrop is a legendary Winamp visualization originally scripted in a custom
language; this VJLive port simulates its math to generate swirling, audio-
reactive geometry and color. We're porting the existing implementation from
VJlive-2 which already translates the original code into Python.

## Technical Requirements
- Plugin registration via manifest; subclass `Effect` with audio-reactive
  support
- Parameters: `mode` (choose preset), `speed`, `scale`, `color_shift`,
  `audio_sensitivity`, `opacity`
- GPU shader implementing the generated particle/point equations; CPU fallback
  using NumPy drawing routines
- 60 FPS at 1080p on reference hardware (Safety Rail 1)
- ≥80 % test coverage (Safety Rail 5)
- Spec <750 lines (Safety Rail 4)
- Validate mode selection; gracefully handle absent audio data
  (Safety Rail 7)

## Public Interface
```python
class MilkdropEffect(Effect):
    """Recreates classic Milkdrop visualizer patterns."""

    def __init__(self,width=1920,height=1080,use_gpu=True):
        super().__init__("Milkdrop", MILKDROP_VERTEX_SHADER,
                         MILKDROP_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["visualizer","audio-reactive","retro"]
        self.features=["AUDIO_REACTIVE","MATH_SCRIPT"]
        self.usage_tags=["STYLING","PERFORMANCE"]
        self.use_gpu=use_gpu

        self._parameter_ranges={'mode':(0.0,10.0),
                                 'speed':(0.0,10.0),
                                 'scale':(0.0,10.0),
                                 'color_shift':(0.0,10.0),
                                 'audio_sensitivity':(0.0,10.0),
                                 'opacity':(0.0,10.0)}
        self.parameters={'mode':0.0,'speed':5.0,'scale':5.0,
                         'color_shift':0.0,'audio_sensitivity':5.0,
                         'opacity':10.0}
        self._parameter_descriptions={
            'mode':'Pattern preset index',
            'speed':'Animation speed',
            'scale':'Spatial scaling',
            'color_shift':'Hue shift',
            'audio_sensitivity':'Response to audio levels',
            'opacity':'Blend amount'}
        self._sweet_spots={'mode':[0,1,2],'speed':[3,5,7]}

    def render(self,tex_in,extra_textures=None,chain=None):
        # sample audio data in shader and compute pattern
        pass

    def apply_uniforms(self,time,resolution,audio_reactor=None,
                      semantic_layer=None):
        # remap parameters, sample audio amplitude
        pass
```

### Parameter Remaps
- `mode` → M = int(map_linear(x,0,10,0,10)) // limited to available presets
- `speed` → S = map_linear(x,0,10,0.0,5.0)
- `scale` → Z = map_linear(x,0,10,0.1,10.0)
- `color_shift` → C = map_linear(x,0,10,0,1)
- `audio_sensitivity` → A = map_linear(x,0,10,0,1)
- `opacity` → α = x/10

## Shader Uniforms
- `uniform float speed;`
- `uniform float scale;`
- `uniform float color_shift;`
- `uniform float audio_amp;`
- `uniform int mode;`
- `uniform float opacity;`
- `uniform vec2 resolution;`

Shader implements a handful of precompiled equations selected by `mode`.
Audio amplitude modulates one or more variables.

## Effect Math
Pseudo-GLSL describing generic mode:
```
float t = time * speed;
vec2 uv = (gl_FragCoord.xy / resolution - 0.5) * scale;
float a = audio_amp * audio_sensitivity;
vec3 col;
if (mode==0) {
    col = vec3(sin(uv.x + t + a), sin(uv.y + t), sin(uv.x+uv.y+t));
} else if (mode==1) {
    // different formula...
}
// apply color shift
col = hsv2rgb(vec3(col.r+color_shift,1,1));
return mix(texture(tex_in, gl_FragCoord.xy/resolution).rgb, col, opacity);
```

The real implementation cycles through dozens of such formulas.

## CPU Fallback
```python
import numpy as np

def milkdrop_cpu(frame, mode, speed, scale,
                 color_shift, audio_amp, time, opacity):
    h,w=frame.shape[:2]
    yy,xx = np.indices((h,w))
    uvx = (xx/w - 0.5)*scale
    uvy = (yy/h - 0.5)*scale
    t = time*speed
    if mode==0:
        col = np.stack([np.sin(uvx + t + audio_amp),
                        np.sin(uvy + t),
                        np.sin(uvx+uvy+t)],axis=-1)
    else:
        col = np.zeros((h,w,3))
    # convert via color shift
    # for brevity omitted
    return ((1-opacity)*frame + opacity*(col*0.5+0.5*255)).astype(np.uint8)
```

## Presets
- `Starfield`: mode=0, speed=2, scale=3
- `Warp`: mode=1, color_shift=0.5
- `Audio Pulse`: audio_sensitivity=1, speed=1

## Edge Cases
- Unsupported mode index: wrap or clamp to max
- Audio data missing: treat audio_amp=0
- Scale <=0: clamp to 0.1

## Test Plan
- `test_mode_bounds`
- `test_audio_reactivity`
- `test_cpu_gpu_parity_for_mode0`
- `test_performance_1080p`
- `test_invalid_params_clamp`

## Verification Checklist
- [ ] Each mode renders a distinct pattern
- [ ] Audio volume modulates visuals when sensitivity >0
- [ ] CPU fallback approximates simple modes
- [ ] Presets correspond to labels

---

**Note:** Because full Milkdrop feature set is large, consider planning a
later expansion to support script parsing; the initial implementation may
just hardcode a handful of popular formulas.

