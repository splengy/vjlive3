# P7-VE48: LUT Grading Effect

> **Task ID:** `P7-VE48`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/lut_grading.py`)
> **Class:** `LUTGradingEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
This effect applies a 3D color lookup table (LUT) to the input image, allowing
complex color grading in a compact form. The original plugin loaded LUTs from
files and interpolated across RGB space. Our port must handle arbitrary LUT
images (e.g., 16×16×16 cube), support intensity blending, and optionally
animate the LUT.

## Technical Requirements
- Plugin registration via manifest; subclass `Effect`
- Parameters: `lut_texture` (user‑supplied), `intensity`, `blend_mode`
- GPU shader performs trilinear interpolation in LUT; CPU fallback using
  NumPy or OpenCV remapping
- Maintain 60 FPS at 1080p with LUT sizes up to 64^3 (Safety Rail 1)
- ≥80 % test coverage (Safety Rail 5)
- Spec <750 lines (Safety Rail 4)
- Validate that LUT texture is square N×N×N or reject with error
  (Safety Rail 7)

## Public Interface
```python
class LUTGradingEffect(Effect):
    """Applies a 3D LUT for color grading."""

    def __init__(self,width=1920,height=1080,use_gpu=True):
        super().__init__("LUTGrading", LUT_VERTEX_SHADER,
                         LUT_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["lut","grading","color"]
        self.features=["COLOR_LUT"]
        self.usage_tags=["COLOR","CORRECTION"]
        self.use_gpu=use_gpu

        self._parameter_ranges={'intensity':(0.0,10.0),
                                 'blend_mode':(0.0,10.0)}
        self.parameters={'intensity':10.0,'blend_mode':0.0}
        self._parameter_descriptions={
            'intensity':'Strength of LUT (0..1)',
            'blend_mode':'Blend mode (0=normal,1=add,2=mul)'}
        self._sweet_spots={'intensity':[3,5,8]}
        self._state={'lut_texture':None}

    def set_lut(self, image):
        # load user texture as 3D LUT into GPU or store for CPU path
        pass

    def render(self,tex_in,extra_textures=None,chain=None):
        # sample tex_in, then apply LUT by indexing
        pass

    def apply_uniforms(self,time,resolution,audio_reactor=None,
                      semantic_layer=None):
        # remap intensity and blend mode, upload LUT if changed
        pass
```

### Parameter Remaps
- `intensity` → α = x/10
- `blend_mode` → B = round(map_linear(x,0,10,0,2))

## Shader Uniforms
- `uniform sampler2D tex_in;`
- `uniform sampler3D lut;` // 3D texture containing color cube
- `uniform float intensity;`
- `uniform int blend_mode;`

LUT lookup performed via `texture(lut, rgb)` after converting input color to
[0,1] range.

## Effect Math
```
vec3 src = texture(tex_in, uv).rgb;
vec3 graded = texture(lut, src).rgb;
vec3 out;
if (blend_mode==1) out = src + graded;
else if (blend_mode==2) out = src * graded;
else out = mix(src, graded, intensity);
return out;
```

## CPU Fallback
```python
import numpy as np

def lut_cpu(frame, lut_array, intensity, blend_mode):
    # lut_array shape (N,N,N,3)
    lut = lut_array
    h,w=frame.shape[:2]
    rgb = frame.astype(np.float32)/255.0
    idx = np.clip((rgb*(lut.shape[0]-1)).astype(int),0,lut.shape[0]-1)
    graded = lut[idx[:,:,0], idx[:,:,1], idx[:,:,2]]
    if blend_mode==1:
        out = rgb + graded
    elif blend_mode==2:
        out = rgb * graded
    else:
        out = rgb*(1-intensity) + graded*intensity
    return np.clip(out,0,1)*255
```

## Presets
- `Neutral`: intensity=0
- `Cinematic`: intensity=0.7, blend_mode=0
- `Additive Glow`: intensity=0.5, blend_mode=1

## Edge Cases
- Missing LUT texture: warn and pass-through
- LUT dimension not cubic: raise `ValueError`
- Intensity outside [0,1]: clamp

## Test Plan
- `test_lut_loading`
- `test_intensity_blend`
- `test_blend_modes`
- `test_cpu_gpu_equivalence` using random LUT
- `test_performance_large_lut`

## Verification Checklist
- [ ] LUT applies correctly for known cube (e.g. invert LUT)
- [ ] Blend modes operate as documented
- [ ] CPU fallback produces same output for small LUT

---

**Note:** Users should be able to animate the LUT texture (hot‑swap) for
creative effects; ensure `set_lut` handles texture replacement efficiently.

