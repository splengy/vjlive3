````markdown
# P7-VE33: Pattern Distortion Effect (Grid / Noise Warp)

> **Task ID:** `P7-VE33`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/distortion.py`)
> **Class:** `PatternDistortionEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
`PatternDistortionEffect` introduces structured warping using a repeating
geometric pattern (e.g. grid, hexagon, concentric circles) to distort UV
coordinates. The effect is often used to create kaleidoscopic or retro TV
patterns. This spec captures parameterized pattern selection/scale/amount,
detailed math for each pattern, CPU fallback, and thorough test plans to match
vjlive behaviour.

## Technical Requirements
- Implement as a VJLive3 plugin (pattern‑based UV warp)
- Support multiple pattern types selectable by UI (grid, circles, waves)
- Maintain 60 FPS with analytic UV transforms (Safety Rail 1)
- ≥80 % unit/test coverage (Safety Rail 5)
- <750 lines specification (Safety Rail 4)
- Fallback to passthrough if amount = 0 (Safety Rail 7)

## Implementation Notes / Porting Strategy
1. Parameterize warp amount and scale.
2. Provide pattern enumeration: grid, rings, diamond, etc.
3. For each pattern, compute displacement vector `D(uv)` and perturb coords:
   `uv' = uv + amount * D(uv)`. Patterns should tile seamlessly.
4. CPU fallback computes same with NumPy functions.

## Public Interface
```python
class PatternDistortionEffect(Effect):
    """
    Pattern Distortion: UV warping using geometric patterns.
    """
    PATTERN_MODES = {0: 'grid', 1: 'rings', 2: 'diamond', 3:'waves'}

    def __init__(self, width:int=1920, height:int=1080,
                 use_gpu:bool=True):
        super().__init__("Pattern Distortion", PATTERN_VERTEX_SHADER,
                         PATTERN_FRAGMENT_SHADER)
        self.effect_category = "distortion"
        self.effect_tags = ["pattern","warp","grid","rings"]
        self.features = ["PATTERN_DISTORTION"]
        self.usage_tags = ["KALIEDOSCOPE","RETRO"]

        self.use_gpu = use_gpu
        self._parameter_ranges = {
            'mode':(0.0,10.0),
            'amount':(0.0,10.0),
            'scale':(0.0,10.0),
            'opacity':(0.0,10.0)
        }
        self.parameters={'mode':0.0,'amount':5.0,'scale':5.0,'opacity':10.0}
        self._parameter_descriptions={
            'mode':'0=grid,3=rings,6=diamond,9=waves',
            'amount':'Distortion strength',
            'scale':'Pattern scale (size)',
            'opacity':'Effect opacity'
        }
        self._sweet_spots={'amount':[4,5,6],'scale':[4,5,6]}

    def render(self, tex_in:int=None, extra_textures:list=None, chain=None)->int:
        # compute uv
        # generate displacement based on selected mode
        # warp uv, sample
        # mix with original
        pass

    def pattern_displacement(self, uv:tuple, mode:int, scale:float)->tuple:
        # grid: offset toward nearest grid line
        # rings: radial sine pattern
        # diamond: manhattan-distance distortion
        # waves: sin(x*scale), cos(y*scale)
        pass

    def apply_uniforms(self, time:float, resolution:tuple,
                      audio_reactor=None, semantic_layer=None):
        # remap amount->pixels, scale->frequency
        pass
```

### Parameter Remaps
- `mode` (0–10) → discrete {0,1,2,3}
- `amount` → `A = map_linear(x,0,10,0,0.2)` fraction of UV
- `scale` → `S = map_linear(x,0,10,1,20)` repetitions across UV space
- `opacity` → α=x/10

## Shader Uniforms
- `uniform int pattern_mode;`
- `uniform float amount;`
- `uniform float scale;`
- `uniform float opacity;`
- `uniform vec2 resolution;`
- `uniform sampler2D tex_in;`

## Effect Math

```
vec2 uv = gl_FragCoord.xy/resolution;
vec2 d;
if(pattern_mode==0){ // grid
    vec2 g = fract(uv*scale) - 0.5;
    d = normalize(g) * (1.0 - length(g));
}
else if(pattern_mode==1){ // rings
    float r = length(uv - 0.5)*scale;
    d = vec2(sin(r*6.2831),cos(r*6.2831))*0.5;
}
else if(pattern_mode==2){ // diamond
    vec2 g = abs(fract(uv*scale)-0.5);
    d = vec2(g.x - g.y, g.y - g.x);
}
else { // waves
    d = vec2(sin(uv.x*scale*6.2831), cos(uv.y*scale*6.2831));
}
vec2 warped = uv + amount * d;
vec3 outc = texture(tex_in, warped).rgb;
vec3 orig = texture(tex_in, uv).rgb;
return mix(orig, outc, opacity);
```

CPU fallback sketch:
```python
def pattern_distort_cpu(frame, mode, amount, scale, opacity):
    h,w=frame.shape[:2]
    y,x = np.meshgrid(np.linspace(0,1,h),np.linspace(0,1,w),indexing='ij')
    if mode==0:
        g = np.stack([np.mod(x*scale,1)-0.5, np.mod(y*scale,1)-0.5],axis=-1)
        d = g/ (np.linalg.norm(g,axis=-1,keepdims=True)+1e-6) * (1-np.linalg.norm(g,axis=-1,keepdims=True))
    elif mode==1:
        r = np.sqrt((x-0.5)**2+(y-0.5)**2)*scale
        d = np.stack([np.sin(r*2*np.pi), np.cos(r*2*np.pi)],axis=-1)*0.5
    elif mode==2:
        g = np.stack([np.abs(np.mod(x*scale,1)-0.5), np.abs(np.mod(y*scale,1)-0.5)],axis=-1)
        d = np.stack([g[:,:,0]-g[:,:,1], g[:,:,1]-g[:,:,0]],axis=-1)
    else:
        d = np.stack([np.sin(x*scale*2*np.pi), np.cos(y*scale*2*np.pi)],axis=-1)
    warped_x = np.clip(x + amount * d[:,:,0],0,1)
    warped_y = np.clip(y + amount * d[:,:,1],0,1)
    # remap sampling using cv2.remap or interpolation
    # ...
    # omitted for brevity
    return ((1-opacity)*frame + opacity*warped_frame).astype(np.uint8)
```

## Presets
- `Subtle Grid`: mode=0, amount=2, scale=5
- `Hypnotic Rings`: mode=1, amount=4, scale=10
- `Diamond Warp`: mode=2, amount=5, scale=8
- `Wave Portal`: mode=3, amount=6, scale=12

## Edge Cases
- amount 0 → passthrough
- scale 0 or 1 → negligible pattern

## Test Plan
- `test_grid_pattern`
- `test_rings_pattern`
- `test_amount_control`
- `test_scale_control`
- `test_opacity_blend`
- `test_cpu_gpu_parity`
- `test_60fps_performance`

## Verification
- [ ] Pattern math correct
- [ ] Warp seamless tile
- [ ] CPU fallback accurate

````
