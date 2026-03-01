# P7-VE46: Living Fractal Consciousness

> **Task ID:** `P7-VE46`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/living_fractal_consciousness.py`)
> **Class:** `LivingFractalConsciousness`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
This mystical effect generates a constantly morphing fractal pattern that
appears to "think" or breathe, hence the name. The core is an iterated
complex function (e.g. Julia set) whose parameters oscillate over time and may
respond to audio. We'll capture the living behavior, color cycling, zoom and
rotation.

## Technical Requirements
- Plugin registration via manifest; subclass `Effect` with optional audio
  support
- Parameters: `zoom`, `rotation`, `iter_count`, `color_offset`, `audio_amp`,
  `opacity`
- GPU shader computing fractal iterations per pixel; CPU fallback via NumPy
  loops optimized with vectorization
- Maintain 60 FPS at 1080p (Safety Rail 1)
- ≥80 % test coverage (Safety Rail 5)
- Spec <750 lines (Safety Rail 4)
- Input validation for iter_count positive integer; clamp zoom range
  (Safety Rail 7)

## Public Interface
```python
class LivingFractalConsciousness(Effect):
    """Animated fractal generator with living, breathing motion."""

    def __init__(self,width=1920,height=1080,use_gpu=True):
        super().__init__("LivingFractal", FRACTAL_VERTEX_SHADER,
                         FRACTAL_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["fractal","audio-reactive","psychedelic"]
        self.features=["FRACTAL_GENERATION","AUDIO_REACTIVE"]
        self.usage_tags=["STYLING","PERFORMANCE","EXPERIMENTAL"]
        self.use_gpu=use_gpu

        self._parameter_ranges={'zoom':(0.0,10.0),
                                 'rotation':(0.0,10.0),
                                 'iter_count':(0.0,10.0),
                                 'color_offset':(0.0,10.0),
                                 'audio_amp':(0.0,10.0),
                                 'opacity':(0.0,10.0)}
        self.parameters={'zoom':5.0,'rotation':0.0,'iter_count':5.0,
                         'color_offset':0.0,'audio_amp':0.0,'opacity':10.0}
        self._parameter_descriptions={
            'zoom':'Zoom level into the fractal',
            'rotation':'Rotate coordinate system',
            'iter_count':'Iteration depth (1..100)',
            'color_offset':'Hue offset per iteration',
            'audio_amp':'Amplitude of audio modulation',
            'opacity':'Blend to original'}
        self._sweet_spots={'zoom':[4,5,6],'iter_count':[10,20,30]}

    def render(self,tex_in,extra_textures=None,chain=None):
        # compute fractal color for each pixel
        pass

    def apply_uniforms(self,time,resolution,audio_reactor=None,
                      semantic_layer=None):
        # remap parameters and compute audio_amt
        pass
```

### Parameter Remaps
- `zoom` → Z = map_linear(x,0,10,0.5,10.0)
- `rotation` → R = map_linear(x,0,10,0,2π)
- `iter_count` → I = int(map_linear(x,0,10,1,100))
- `color_offset` → C = map_linear(x,0,10,0,1)
- `audio_amp` → A = x/10
- `opacity` → α = x/10

`audio_amt` used to perturb zoom or rotation when audio_amp >0.

## Shader Uniforms
- `uniform float zoom;`
- `uniform float rotation;`
- `uniform int iter_count;`
- `uniform float color_offset;`
- `uniform float audio_amt;`
- `uniform float time;`
- `uniform float opacity;`
- `uniform vec2 resolution;`

## Effect Math (GLSL sketch)
```
vec2 uv = (gl_FragCoord.xy / resolution - 0.5) * zoom;
float angle = rotation + audio_amt * sin(time);
uv = mat2(cos(angle),-sin(angle),sin(angle),cos(angle)) * uv;
vec2 z = uv;
int i;
for (i = 0; i < iter_count; ++i) {
    z = vec2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + uv;
    if (dot(z,z) > 4.0) break;
}
float t = float(i) / float(iter_count);
float hue = fract(t + color_offset);
vec3 col = hsv2rgb(vec3(hue,1.0,1.0 - t));
vec3 orig = texture(tex_in, gl_FragCoord.xy/resolution).rgb;
return mix(orig, col, opacity);
```

## CPU Fallback
```python
import numpy as np

def lfc_cpu(frame, zoom, rotation, iter_count,
            color_offset, audio_amt, time, opacity):
    h,w=frame.shape[:2]
    yy,xx = np.indices((h,w))
    uvx = (xx/w - 0.5)*zoom
    uvy = (yy/h - 0.5)*zoom
    angle = rotation + audio_amt * np.sin(time)
    c = np.cos(angle); s = np.sin(angle)
    x = c*uvx - s*uvy
    y = s*uvx + c*uvy
    z_x = x.copy(); z_y = y.copy()
    col = np.zeros((h,w,3),dtype=np.float32)
    for i in range(iter_count):
        zx2 = z_x*z_x - z_y*z_y + x
        zy2 = 2*z_x*z_y + y
        z_x, z_y = zx2, zy2
        mask = z_x*z_x + z_y*z_y > 4.0
        t = i / float(iter_count)
        hue = np.mod(t + color_offset,1.0)
        rgb = hsv_to_rgb(np.stack([hue, np.ones_like(hue), 1-t],axis=-1))
        col += rgb * (~mask)[...,None]
    col = np.clip(col,0,1)
    return ((1-opacity)*frame + opacity*(col*255)).astype(np.uint8)
```

## Presets
- `Calm Mind`: zoom=3, iter_count=20, color_offset=0.1
- `Fractal Frenzy`: zoom=10, iter_count=80, audio_amp=1
- `Spinning Thoughts`: rotation=5, color_offset=0.5

## Edge Cases
- `iter_count` extremely large affects performance; clamp at 200
- Zoom <0.5 or >20 clamp
- Audio_amt may be noisy; low-pass filter recommended

## Test Plan
- `test_fractal_generation`
- `test_save_frame_consistency`
- `test_audio_modulation`
- `test_cpu_gpu_parity`
- `test_performance_1080p_iter50`
- `test_invalid_params_clamp`

## Verification Checklist
- [ ] Fractal colors cycle smoothly
- [ ] Audio modulation affects zoom/rotation when enabled
- [ ] CPU fallback matches GPU with tolerances
- [ ] Presets visually distinct

---

**Note:** Because iteration-heavy, this effect may not run on low-end GPUs.
Document in README with performance hints.

