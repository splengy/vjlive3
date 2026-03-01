# P7-VE42: Mirror Effect (Axis Reflection)

> **Task ID:** `P7-VE42`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/geometry.py`)
> **Class:** `MirrorEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
MirrorEffect reflects the input image over one or both axes, optionally
around a pivot point. It’s the basis for kaleidoscopes, symmetrical patterns,
and can also serve as a simple flip transition. We replicate the original code
from `vjlive/plugins/vcore/geometry.py` with a clean spec.

## Technical Requirements
- Implement as plugin subclassing `Effect`
- Parameters: `horizontal`, `vertical`, `pivot_x`, `pivot_y`, `opacity`
- GPU shader uses `abs` or coordinate flip; CPU fallback with array slicing
- Maintain 60 FPS on 1080p (Safety Rail 1)
- ≥80 % coverage (Safety Rail 5)
- Spec <750 lines (Safety Rail 4)
- Validate pivot within bounds; booleans for flips (Safety Rail 7)

## Public Interface
```python
class MirrorEffect(Effect):
    """Reflects the image over horizontal/vertical axes around a pivot."""
    def __init__(self,width=1920,height=1080,use_gpu=True):
        super().__init__("Mirror", MIRROR_VERTEX_SHADER,
                         MIRROR_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["mirror","flip","symmetry"]
        self.features=["AXIS_MIRROR"]
        self.usage_tags=["STYLING","TRANSITION","CHOREO"]
        self.use_gpu=use_gpu

        self._parameter_ranges={'horizontal':(0.0,10.0),
                                 'vertical':(0.0,10.0),
                                 'pivot_x':(0.0,10.0),
                                 'pivot_y':(0.0,10.0),
                                 'opacity':(0.0,10.0)}
        self.parameters={'horizontal':0.0,'vertical':0.0,
                         'pivot_x':5.0,'pivot_y':5.0,'opacity':10.0}
        self._parameter_descriptions={
            'horizontal':'Enable horizontal mirror (0/1)',
            'vertical':'Enable vertical mirror (0/1)',
            'pivot_x':'Pivot X fraction (0..1)',
            'pivot_y':'Pivot Y fraction',
            'opacity':'Blend amount'}
        self._sweet_spots={'horizontal':[0,10],'vertical':[0,10]}

    def render(self,tex_in,extra_textures=None,chain=None):
        # flip coordinates based on flags and pivot
        pass

    def apply_uniforms(self,time,resolution,audio_reactor=None,
                      semantic_layer=None):
        # compute bools, pivot fractions, opacity
        pass
```

### Parameter Remaps
- `horizontal` → H = round(map_linear(x,0,10,0,1))
- `vertical` → V = round(map_linear(x,0,10,0,1))
- `pivot_x` → Px = x/10
- `pivot_y` → Py = y/10
- `opacity` → α = x/10

## Shader Uniforms
- `uniform float horizontal;`
- `uniform float vertical;`
- `uniform vec2 pivot;`
- `uniform float opacity;`
- `uniform vec2 resolution;`
- `uniform sampler2D tex_in;`

## Effect Math
```
vec2 uv = gl_FragCoord.xy/resolution;
vec2 p = pivot;
vec2 d = uv - p;
if (horizontal > 0.5) {
    d.x = -d.x;
}
if (vertical > 0.5) {
    d.y = -d.y;
}
vec2 warped = d + p;
vec3 color = texture(tex_in, warped).rgb;
vec3 orig = texture(tex_in, uv).rgb;
return mix(orig, color, opacity);
```

## CPU Fallback
```python
import numpy as np

def mirror_cpu(frame, horizontal, vertical, pivot, opacity):
    h,w = frame.shape[:2]
    px = int(pivot[0]*w)
    py = int(pivot[1]*h)
    out = frame.copy()
    if horizontal:
        left = out[:,:px]
        out[:,:px] = np.fliplr(left)
    if vertical:
        top = out[:py,:]
        out[:py,:] = np.flipud(top)
    return ((1-opacity)*frame + opacity*out).astype(np.uint8)
```

## Presets
- `Flip Horizontal`: horizontal=1
- `Flip Vertical`: vertical=1
- `Cross`: horizontal=1, vertical=1

## Edge Cases
- No flips selected: output = original
- Pivot outside [0,1]: clamp and warn
- Both flips with pivot center yields 180° rotation

## Test Plan
- `test_horizontal_vertical_flags`
- `test_pivot_variations`
- `test_combined_flip`
- `test_cpu_gpu_equivalence`
- `test_opacity_blend`
- `test_performance_1080p`

## Verification Checklist
- [ ] Mirror axes align at pivot
- [ ] CPU output matches GPU for sample image
- [ ] Presets toggle correctly
- [ ] Invalid inputs are clamped

---

**Note:** This effect can be combined with Rotate/Scale for creative
compositions, consider documenting common usage combos.

