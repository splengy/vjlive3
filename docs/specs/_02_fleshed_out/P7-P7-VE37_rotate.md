````markdown
# P7-VE37: Rotate Effect (Image Rotation)

> **Task ID:** `P7-VE37`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/geometry.py`)
> **Class:** `RotateEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Simple rotation of the input image around its center, with optional zoom and
opacity. Although trivial, it’s widely used in choreography and transition
chains; thus must be part of the spec set. Documentation covers rotation math,
parameter remaps, GPU/CPU fallback, and testing.

## Technical Requirements
- Implement as plugin performing affine UV transform
- Parameters: angle, zoom, pivot offset, opacity
- Maintain 60 FPS (Safety Rail 1)
- ≥80 % unit/test coverage (Safety Rail 5)
- <750 lines spec (Safety Rail 4)
- Normalize for pivot shifts gracefully (Safety Rail 7)

## Implementation Notes
1. Compute rotation matrix using angle parameter.
2. Apply zoom scaling about center (or pivot offset).
3. Sample texture with transformed coords
t
## Public Interface
```python
class RotateEffect(Effect):
    """
    Rotate Effect: simple rotation/zoom of input.
    """
    def __init__(self,width:int=1920,height:int=1080,use_gpu:bool=True):
        super().__init__("Rotate", ROTATE_VERTEX_SHADER,
                         ROTATE_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["rotate","transform"]
        self.features=["AFFINE_TRANSFORM"]
        self.usage_tags=["TRANSITION","CHOREO"]
        self.use_gpu=use_gpu
        self._parameter_ranges={'angle':(0.0,10.0),
                                 'zoom':(0.0,10.0),
                                 'pivot_x':(0.0,10.0),
                                 'pivot_y':(0.0,10.0),
                                 'opacity':(0.0,10.0)}
        self.parameters={'angle':0.0,'zoom':5.0,'pivot_x':5.0,'pivot_y':5.0,'opacity':10.0}
        self._parameter_descriptions={
            'angle':'Rotation angle (degrees)',
            'zoom':'Zoom factor (0.1..5)',
            'pivot_x':'Pivot X fraction (0..1)',
            'pivot_y':'Pivot Y fraction',
            'opacity':'Effect opacity'}
        self._sweet_spots={'angle':[0,5,10],'zoom':[4,5,6]}

    def render(self,tex_in:int=None,extra_textures:list=None,chain=None)->int:
        # compute affine matrix, apply to uv coords
        # sample, blend
        pass

    def apply_uniforms(self,time:float,resolution:tuple,
                      audio_reactor=None,semantic_layer=None):
        # remap angle->radians, zoom linear, pivot fraction
        pass
```

### Parameter Remaps
- `angle` (0–10) → θ = map_linear(x,0,10,0,360) degrees → radians in shader
- `zoom` → Z = map_linear(x,0,10,0.1,5.0)
- `pivot_x`/`pivot_y` → Px = x/10, Py = y/10 (fraction of width/height)
- `opacity` → α = x/10

## Shader Uniforms
- `uniform float angle;`
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
float ca = cos(angle);
float sa = sin(angle);
vec2 rotated = vec2(pos.x*ca - pos.y*sa, pos.x*sa + pos.y*ca) / zoom;
vec2 warped = rotated + c;
vec3 outc = texture(tex_in, warped).rgb;
vec3 orig = texture(tex_in, uv).rgb;
return mix(orig, outc, opacity);
```

## CPU Fallback
```python
def rotate_cpu(frame, angle, zoom, pivot, opacity):
    h,w=frame.shape[:2]
    M = cv2.getRotationMatrix2D((pivot[0]*w,pivot[1]*h),angle*180/np.pi,1/zoom)
    warped = cv2.warpAffine(frame,M,(w,h),borderMode=cv2.BORDER_REFLECT)
    return ((1-opacity)*frame + opacity*warped).astype(np.uint8)
```

## Presets
- `Clockwise`: angle=2.5 (90°), zoom=5
- `Slow Spin`: angle=1, pivot center
- `Zoom Out`: zoom=1, angle=0

## Edge Cases
- Zoom≤0: clamp to 0.1
- Pivot outside [0,1]: clamp

## Test Plan
- `test_rotation_90deg`
- `test_zoom_factors`
- `test_pivot_offsets`
- `test_opacity_blend`
- `test_cpu_gpu_parity`
- `test_60fps_performance`

## Verification
- [ ] Matrix computed correctly
- [ ] Pivot respected
- [ ] CPU fallback matches

````
