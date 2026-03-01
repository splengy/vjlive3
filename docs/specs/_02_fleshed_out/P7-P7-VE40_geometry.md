# P7-VE40: Repeat Effect (Tiling / Mosaic)

> **Task ID:** `P7-VE40`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/geometry.py`)
> **Class:** `RepeatEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
The `RepeatEffect` tiles the input image into a grid, optionally offsetting or
mirroring each tile. It enables kaleidoscopic patterns, seamless loops, and
feedback tricks. Must be ported cleanly with parameterizable rows/columns and
animation support.

## Technical Requirements
- Register as a plugin subclassing `Effect` with metadata
- Parameters: `cols`, `rows`, `offset_x`, `offset_y`, `mirror`, `opacity`
- GPU implementation via UV modulo/flip; CPU fallback using NumPy slicing
- Maintain 60 FPS at 1080p (Safety Rail 1)
- ≥80 % unit/test coverage (Safety Rail 5)
- Spec document under 750 lines (Safety Rail 4)
- Validate integer counts ≥1; `mirror` boolean; clamp offsets (Safety Rail 7)

## Public Interface
```python
class RepeatEffect(Effect):
    """Tile the input image in a grid with optional mirroring."""

    def __init__(self,width=1920,height=1080,use_gpu=True):
        super().__init__("Repeat", REPEAT_VERTEX_SHADER,
                         REPEAT_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["tile","repeat","kaleidoscope"]
        self.features=["GRID_REPEAT"]
        self.usage_tags=["STYLING","TRANSITION","CHOREO"]
        self.use_gpu=use_gpu

        self._parameter_ranges={'cols':(0.0,10.0),
                                 'rows':(0.0,10.0),
                                 'offset_x':(0.0,10.0),
                                 'offset_y':(0.0,10.0),
                                 'mirror':(0.0,10.0),
                                 'opacity':(0.0,10.0)}
        self.parameters={'cols':5.0,'rows':5.0,'offset_x':5.0,
                         'offset_y':5.0,'mirror':0.0,'opacity':10.0}
        self._parameter_descriptions={
            'cols':'Number of columns (1..20)',
            'rows':'Number of rows (1..20)',
            'offset_x':'Horizontal offset fraction',
            'offset_y':'Vertical offset fraction',
            'mirror':'Mirror every other tile (0/1)',
            'opacity':'Blend amount'}
        self._sweet_spots={'cols':[3,5,8],'rows':[3,5,8]}

    def render(self,tex_in,extra_textures=None,chain=None):
        # compute tile uv using mod and mirror
        pass

    def apply_uniforms(self,time,resolution,audio_reactor=None,
                      semantic_layer=None):
        # remap and upload cols, rows, offsets, mirror, opacity
        pass
```

### Parameter Remaps
- `cols` → C = int(map_linear(x,0,10,1,20))
- `rows` → R = int(map_linear(x,0,10,1,20))
- `offset_x` → Ox = map_linear(x,0,10,0.0,1.0)
- `offset_y` → Oy = map_linear(x,0,10,0.0,1.0)
- `mirror` → M = round(map_linear(x,0,10,0,1))
- `opacity` → α = x/10

## Shader Uniforms
- `uniform float cols;`
- `uniform float rows;`
- `uniform vec2 offset;`
- `uniform float mirror;`
- `uniform float opacity;`
- `uniform vec2 resolution;`
- `uniform sampler2D tex_in;`

## Effect Math
```
vec2 uv = gl_FragCoord.xy / resolution;
vec2 grid = vec2(cols, rows);
vec2 t = fract(uv * grid + offset);
if (mirror > 0.5) {
    if (mod(floor(uv.x * cols) + floor(uv.y * rows), 2.0) > 0.5) {
        t.x = 1.0 - t.x;
    }
}
vec3 color = texture(tex_in, t).rgb;
vec3 orig = texture(tex_in, uv).rgb;
return mix(orig, color, opacity);
```

## CPU Fallback
```python
import numpy as np

def repeat_cpu(frame, cols, rows, offset, mirror, opacity):
    h,w = frame.shape[:2]
    out = np.zeros_like(frame)
    ch = h//rows
    cw = w//cols
    for r in range(rows):
        for c in range(cols):
            y = r*ch
            x = c*cw
            tile = frame[y:y+ch, x:x+cw]
            if mirror and ((r+c)%2==1):
                tile = tile[:, ::-1]
            out[y:y+ch, x:x+cw] = tile
    return ((1-opacity)*frame + opacity*out).astype(np.uint8)
```

## Presets
- `4x4 Grid`: cols=4, rows=4, mirror=1
- `Horizontal Strip`: cols=10, rows=1, offset_x animates
- `Kaleidoscope`: cols=8, rows=8, mirror=1, opacity=0.7

## Edge Cases
- `cols` or `rows` <1: clamp to 1
- Offsets wrap (fract)
- Mirror noise if non‑binary; treat ≥0.5 as enabled

## Test Plan
- `test_grid_sizes`
- `test_mirror_pattern`
- `test_offset_animation`
- `test_cpu_gpu_equivalence`
- `test_performance_1080p`
- `test_invalid_counts_clamp`

## Verification Checklist
- [ ] Tiles align without seams
- [ ] Mirror toggles correctly
- [ ] CPU fallback matches GPU for sample images
- [ ] Offsets cause proper sliding

---

**Note:** Variation of offsets can drive animation easily; consider adding
`offset_rate` parameter if missing.

