````markdown
# P7-VE36: Mandalascope Effect (Symmetric Kaleidoscope)

> **Task ID:** `P7-VE36`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/geometry.py`)
> **Class:** `MandalascopeEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
A mandalascope replicates and mirrors portions of an image around a central
origin to create radial symmetry. This effect takes an input texture, applies
polar transformations combined with rotational symmetry, and outputs a
kaleidoscopic view. Our spec details modular symmetry counts, rotation,
zoom, and spiral options, along with CPU fallback and verification steps.

## Technical Requirements
- Implement as plugin using fragment shader geometry warping
- Allow parameters: segment count, rotation, zoom, spiral twist
- Maintain 60 FPS (Safety Rail 1)
- ≥80 % test coverage (Safety Rail 5)
- <750 lines spec (Safety Rail 4)
- Fall back to pass-through for segment=1 (Safety Rail 7)

## Implementation Notes
1. Convert uv to polar coords (r, θ).
2. Multiply θ by segment count to create repeated wedges.
3. Apply modulo π/segment to mirror.
4. Optionally add twist: θ += twist * r.
5. Convert back to cartesian, sample texture.

## Public Interface
```python
class MandalascopeEffect(Effect):
    """
    Mandalascope Effect: radial symmetry warping.
    """
    def __init__(self,width:int=1920,height:int=1080,use_gpu:bool=True):
        super().__init__("Mandalascope", MANDALA_VERTEX_SHADER,
                         MANDALA_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["mandala","kaleidoscope","symmetry"]
        self.features=["SYMMETRY"]
        self.usage_tags=["GEOMETRY","PSYCHEDELIC"]
        self.use_gpu=use_gpu
        self._parameter_ranges={'segments':(0.0,10.0),
                                 'rotation':(0.0,10.0),
                                 'zoom':(0.0,10.0),
                                 'twist':(0.0,10.0),
                                 'opacity':(0.0,10.0)}
        self.parameters={'segments':5.0,'rotation':5.0,'zoom':5.0,'twist':0.0,'opacity':10.0}
        self._parameter_descriptions={
            'segments':'Number of radial segments (1..20)',
            'rotation':'Global rotation of pattern',
            'zoom':'Zoom factor',
            'twist':'Spiral twist amount',
            'opacity':'Effect opacity'}
        self._sweet_spots={'segments':[3,6,12]}

    def render(self,tex_in:int=None,extra_textures:list=None,chain=None)->int:
        # convert uv to polar
        # apply symmetry and twist
        # sample texture
        # blend with original
        pass

    def apply_uniforms(self,time:float,resolution:tuple,
                      audio_reactor=None,semantic_layer=None):
        # remap segments to int, rotation to radians, zoom linear, twist factor
        pass
```

### Parameter Remaps
- `segments` (UI 0–10) → N = clamp(int(map_linear(x,0,10,1,20)),1,20)
- `rotation` → θ0 = map_linear(x,0,10,0,2π)
- `zoom` → Z = map_linear(x,0,10,0.5,3.0)
- `twist` → T = map_linear(x,0,10,0,5)  # radians per unit radius
- `opacity` → α = x/10

## Shader Uniforms
- `uniform int segments;`
- `uniform float rotation;`
- `uniform float zoom;`
- `uniform float twist;`
- `uniform float opacity;`
- `uniform vec2 resolution;`
- `uniform sampler2D tex_in;`

## Effect Math

```
vec2 uv = (gl_FragCoord.xy/resolution - 0.5) * zoom;
float r = length(uv);
float theta = atan(uv.y, uv.x);
theta += rotation;
float wedge = 2.0 * 3.14159265 / float(segments);
theta = mod(theta, wedge);
if(theta > wedge/2.0) theta = wedge - theta; // mirror
theta += twist * r;
vec2 warped = vec2(r * cos(theta), r * sin(theta));
warped = warped / zoom + 0.5;
vec3 outc = texture(tex_in, warped).rgb;
vec3 orig = texture(tex_in, (gl_FragCoord.xy/resolution)).rgb;
return mix(orig, outc, opacity);
```

## CPU Fallback
```python
def mandala_cpu(frame, segments, rotation, zoom, twist, opacity):
    h,w=frame.shape[:2]
    y,x=np.meshgrid(np.linspace(0,1,h),np.linspace(0,1,w),indexing='ij')
    u=(x-0.5)*zoom; v=(y-0.5)*zoom
    r=np.sqrt(u**2+v**2)
    theta=np.arctan2(v,u)
    theta+=rotation
    wedge=2*np.pi/segments
    theta=np.mod(theta,wedge)
    mask=theta>wedge/2
    theta[mask]=wedge-theta[mask]
    theta+=twist*r
    warped_x = r*np.cos(theta)/zoom + 0.5
    warped_y = r*np.sin(theta)/zoom + 0.5
    warped = cv2.remap(frame, warped_x.astype(np.float32), warped_y.astype(np.float32), 
                       interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return ((1-opacity)*frame + opacity*warped).astype(np.uint8)
```

## Presets
- `Simple Star`: segments=6, twist=0
- `Spiral Mandala`: segments=8, twist=2
- `Zoomed In`: zoom=2, rotation=1
- `Subtle`: segments=3, opacity=5

## Edge Cases
- segments=1 -> identity
- twist large -> heavy spiral

## Test Plan
- `test_segments_symmetry`
- `test_rotation_applied`
- `test_zoom_effect`
- `test_twist_spiral`
- `test_cpu_gpu_parity`
- `test_60fps_performance`

## Verification
- [ ] Symmetry count correct
- [ ] Warp invertible
- [ ] CPU fallback accurate

````
