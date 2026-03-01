# P7-VE38: Scale Effect (Geometry Scaling)

> **Task ID:** `P7-VE38`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/geometry.py`)
> **Class:** `ScaleEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Scaling the input image about an arbitrary pivot is a basic geometric
operation used in dance, zoom transitions, and layout adjustments. The old
`ScaleEffect` lives in `vjlive/plugins/vcore/geometry.py`; our goal is a
clean re‑implementation in VJLive3 with GPU and CPU fallbacks, full docs,
and the usual test battery.

## Technical Requirements
- Plugin must register via the central manifest/registry system
- Should subclass `Effect` and declare appropriate metadata
- Support both GPU (GLSL) and CPU (NumPy/OpenCV) paths
- Parameter remapping via `map_linear` for UI sliders 0–10
- Maintain 60 FPS on 1920×1080 frames (Safety Rail 1)
- ≥80 % unit/test coverage (Safety Rail 5)
- Spec document <750 lines (Safety Rail 4)
- Proper input validation (zoom ≠0, pivot inside bounds) and explicit errors
  on invalid values (Safety Rail 7)

## Public Interface
```python
class ScaleEffect(Effect):
    """Uniform scaling of source image with pivot control."""

    def __init__(self,width:int=1920,height:int=1080,use_gpu:bool=True):
        super().__init__("Scale", SCALE_VERTEX_SHADER,
                         SCALE_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["scale","zoom"]
        self.features=["AFFINE_TRANSFORM"]
        self.usage_tags=["TRANSITION","CHOREO"]
        self.use_gpu=use_gpu

        self._parameter_ranges={'zoom':(0.0,10.0),
                                 'pivot_x':(0.0,10.0),
                                 'pivot_y':(0.0,10.0),
                                 'opacity':(0.0,10.0)}
        self.parameters={'zoom':5.0,'pivot_x':5.0,'pivot_y':5.0,'opacity':10.0}
        self._parameter_descriptions={
            'zoom':'Zoom factor (0.1..5)',
            'pivot_x':'Pivot X fractional (0..1)',
            'pivot_y':'Pivot Y fractional',
            'opacity':'Opacity of scaled image'}
        self._sweet_spots={'zoom':[4,5,6]}

    def render(self,tex_in:int=None,extra_textures:list=None,chain=None)->int:
        # compute scaling matrix and apply
        pass

    def apply_uniforms(self,time:float,resolution:tuple,
                      audio_reactor=None,semantic_layer=None):
        # remap parameters and upload to GPU
        pass
```

### Parameter Remaps
- `zoom` (0–10) → Z = map_linear(x,0,10,0.1,5.0)
- `pivot_x`/`pivot_y` → (Px,Py) = (x/10, y/10) fractions of resolution
- `opacity` → α = x/10

## Shader Uniforms
- `uniform float zoom;`
- `uniform vec2 pivot;`
- `uniform float opacity;`
- `uniform vec2 resolution;`
- `uniform sampler2D tex_in;`

## Effect Math
```
vec2 uv = gl_FragCoord.xy / resolution;
vec2 c = pivot;
vec2 pos = uv - c;
vec2 scaled = pos / zoom;
vec2 warped = scaled + c;
vec3 color = texture(tex_in, warped).rgb;
vec3 orig = texture(tex_in, uv).rgb;
return mix(orig, color, opacity);
```
Scale factor less than 1 zooms in; >1 zooms out (inverse relationship).

## CPU Fallback
```python
import cv2
import numpy as np

def scale_cpu(frame, zoom, pivot, opacity):
    h,w = frame.shape[:2]
    center = (pivot[0]*w, pivot[1]*h)
    M = cv2.getRotationMatrix2D(center, 0, 1/zoom)
    warped = cv2.warpAffine(frame, M, (w,h),
                            borderMode=cv2.BORDER_REFLECT)
    return ((1-opacity)*frame + opacity*warped).astype(np.uint8)
```

## Presets
- `Zoom In`: zoom=6, center pivot
- `Zoom Out`: zoom=4, center pivot, opacity=5
- `Corner Scale`: pivot at (0,0), zoom=8

## Edge Cases and Validation
- `zoom<=0`: raise `ValueError` or clamp to 0.1
- `pivot` outside [0,1]: clamp and log warning
- `opacity` outside [0,1]: clamp
- Requesting GPU when unsupported defaults to CPU fallback

## Test Plan
- `test_zoom_linear_remap`
- `test_pivot_fractional`
- `test_opacity_blending`
- `test_gpu_cpu_equivalence`
- `test_invalid_parameters_raise`
- `test_performance_1920x1080`

## Verification Checklist
- [ ] Plugin registers with manifest and enumerates parameters
- [ ] Zoom math behaves as expected in unit vectors
- [ ] CPU fallback matches GPU output for sample frames
- [ ] Performance benchmark ≥60 FPS on CI test rig
- [ ] All parameters have descriptions and sweet spots

---

**Notes:**
The original code may have had additional features (per-axis scaling); if so,
adapt here and update parameters accordingly.

