# P7-VE51: Oscilloscope Effect

> **Task ID:** `P7-VE51`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/oscilloscope.py`)
> **Class:** `OscilloscopeEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Renders a real‑time waveform on screen based on audio input or derived from
frame luminance. Useful for audio-reactive visuals and debugging signals.
We're porting the existing VJlive implementation which supported polar and
linear displays with variable thickness, fade, and color.

## Technical Requirements
- Register plugin via manifest; subclass `Effect` with audio-reactive
  requirement
- Parameters: `mode` (linear/polar), `thickness`, `fade`, `color_mode`,
  `opacity`
- GPU shader draws line by reading an audio buffer texture (passed via
  `extra_textures`) or computing from luminosity of input frame
- CPU fallback renders line using matplotlib or PIL drawing
- Maintain 60 FPS at 1080p sampling 1024 audio points (Safety Rail 1)
- ≥80 % test coverage (Safety Rail 5)
- Spec <750 lines (Safety Rail 4)
- Validate audio buffer availability; default to black if missing
  (Safety Rail 7)

## Public Interface
```python
class OscilloscopeEffect(Effect):
    """Displays waveform from audio or frame brightness."""

    def __init__(self,width=1920,height=1080,use_gpu=True):
        super().__init__("Oscilloscope", OSC_VERTEX_SHADER,
                         OSC_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["oscilloscope","audio-reactive"]
        self.features=["AUDIO_SAMPLING"]
        self.usage_tags=["STYLING","DEBUG"]
        self.use_gpu=use_gpu

        self._parameter_ranges={'mode':(0.0,10.0),
                                 'thickness':(0.0,10.0),
                                 'fade':(0.0,10.0),
                                 'color_mode':(0.0,10.0),
                                 'opacity':(0.0,10.0)}
        self.parameters={'mode':0.0,'thickness':5.0,'fade':5.0,
                         'color_mode':0.0,'opacity':10.0}
        self._parameter_descriptions={
            'mode':'0=linear,1=polar',
            'thickness':'Line thickness',
            'fade':'Trail fade amount',
            'color_mode':'0=monochrome,1=rainbow',
            'opacity':'Blend amount'}
        self._sweet_spots={'thickness':[1,3,5],'fade':[2,5,8]}

    def render(self,tex_in,extra_textures=None,chain=None):
        # sample audio buffer texture if provided and draw waveform
        pass

    def apply_uniforms(self,time,resolution,audio_reactor=None,
                      semantic_layer=None):
        # remap parameters, optionally get audio data
        pass
```

### Parameter Remaps
- `mode` → M = int(map_linear(x,0,10,0,1))
- `thickness` → T = map_linear(x,0,10,1,20) pixels
- `fade` → F = map_linear(x,0,10,0,1)
- `color_mode` → C = int(map_linear(x,0,10,0,1))
- `opacity` → α = x/10

## Shader Uniforms
- `uniform float thickness;`
- `uniform float fade;`
- `uniform int mode;`
- `uniform int color_mode;`
- `uniform float opacity;`
- `uniform sampler2D audio_buf;` // 1D texture containing waveform

## Effect Math
```
vec2 uv = gl_FragCoord.xy / resolution;
float sample = texture(audio_buf, vec2(uv.x,0)).r;
float y = (sample + 1.0) * 0.5;
if (mode==1) {
    // polar coordinate transform
    float angle = uv.x * 2.0*PI;
    float radius = y;
    vec2 pos = vec2(cos(angle), sin(angle)) * radius * 0.5 + 0.5;
    uv = pos;
}
vec3 color = (color_mode==1) ? hsv2rgb(vec3(uv.x,1,1)) : vec3(1);
float alpha = smoothstep(thickness, thickness-1.0, abs(uv.y - y));
alpha *= opacity;
return vec4(color, alpha);
```
Fade implemented by blending current frame with previous using F.

## CPU Fallback
```python
import numpy as np
from PIL import Image, ImageDraw

def osc_cpu(frame, audio_buf, mode, thickness, fade, color_mode, opacity):
    h,w = frame.shape[:2]
    img = Image.new('RGBA',(w,h))
    draw = ImageDraw.Draw(img)
    samples = np.interp(np.linspace(0,1,w), np.linspace(0,1,len(audio_buf)), audio_buf)
    if mode==0:
        points = [(x, (s+1)*0.5*h) for x,s in enumerate(samples)]
    else:
        points = []
        for x,s in enumerate(samples):
            angle = x/w*2*np.pi
            r = (s+1)*0.5*min(w,h)/2
            points.append((w/2 + r*np.cos(angle), h/2 + r*np.sin(angle)))
    draw.line(points, fill=(255,255,255,int(255*opacity)), width=int(thickness))
    return np.array(img)
```

## Presets
- `Basic`: mode=0, thickness=2
- `Circle`: mode=1, thickness=3, color_mode=1
- `Rainbow Line`: color_mode=1, fade=0.5

## Edge Cases
- audio_buf missing: sample = 0 waveform
- thickness <1: clamp to 1
- fade <0 or >1: clamp

## Test Plan
- `test_waveform_linear`
- `test_waveform_polar`
- `test_color_modes`
- `test_cpu_gpu_equivalence`
- `test_performance_1080p`

## Verification Checklist
- [ ] Wave reacts to provided audio array
- [ ] Fade persists previous frames correctly
- [ ] CPU fallback shows same line positions

---

**Note:** Provide an API for external code to supply a custom audio buffer
(e.g., from file or network) for testing.

