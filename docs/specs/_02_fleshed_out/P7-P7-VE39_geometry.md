# P7-VE39: Pixelate Effect (Blocky Pixelation)

> **Task ID:** `P7-VE39`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/geometry.py`)
> **Class:** `PixelateEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
A pixelate/"mosaic" effect reduces resolution by grouping pixels into larger
blocks. It’s a staple for censorship, retro aesthetics, or transitional
flare. The older implementation lives in `vjlive/plugins/vcore/geometry.py`.
We'll re‑implement in VJLive3 with precise control over block size,
density, and color mode.

## Technical Requirements
- Register as plugin, subclassing `Effect`
- Parameters: `block_size`, `density`, `mode` (`avg`/`nearest`), `opacity`
- Efficient GPU shader using UV quantization; CPU fallback via NumPy
- Maintain 60 FPS at 1080p (Safety Rail 1)
- ≥80 % test coverage (Safety Rail 5)
- Spec <750 lines (Safety Rail 4)
- Validate non‑zero block size, log/correct invalid modes (Safety Rail 7)

## Public Interface
```python
class PixelateEffect(Effect):
    """Reduce image resolution by grouping pixels into blocks."""
    def __init__(self,width=1920,height=1080,use_gpu=True):
        super().__init__("Pixelate", PIXELATE_VERTEX_SHADER,
                         PIXELATE_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["pixelate","mosaic"]
        self.features=["PIXELATE"]
        self.usage_tags=["TRANSITION","CHOREO","STYLING"]
        self.use_gpu=use_gpu

        self._parameter_ranges={'block_size':(0.0,10.0),
                                 'density':(0.0,10.0),
                                 'opacity':(0.0,10.0)}
        self.parameters={'block_size':5.0,'density':5.0,'opacity':10.0}
        self._parameter_descriptions={
            'block_size':'Size of each pixel block (1..100)',
            'density':'How densely the blocks cover the frame',
            'opacity':'Blend between original and pixelated'}
        self._sweet_spots={'block_size':[2,5,8],'density':[3,5,7]}

    def render(self,tex_in,extra_textures=None,chain=None):
        # quantize uv coords by block size and sample
        pass

    def apply_uniforms(self,time,resolution,audio_reactor=None,
                      semantic_layer=None):
        # remap block_size,density,opacity and send to shader
        pass
```

### Parameter Remaps
- `block_size` (0–10) → S = map_linear(x,0,10,1,100) pixels
- `density` (0–10) → D = map_linear(x,0,10,0.0,1.0) fraction of pixels kept
- `opacity` → α = x/10

Edge note: density controls probability that a block is applied; randomize by
hash or noise to allow flicker.

## Shader Uniforms
- `uniform float block_size;`
- `uniform float density;`
- `uniform float opacity;`
- `uniform vec2 resolution;`
- `uniform sampler2D tex_in;`

## Effect Math
```
vec2 uv = gl_FragCoord.xy/resolution;
vec2 grid = floor(uv * resolution / block_size) * block_size / resolution;
vec3 pix = texture(tex_in, grid).rgb;
vec3 orig = texture(tex_in, uv).rgb;
if (fract(sin(dot(grid,vec2(12.9898,78.233)))*43758.5453) > density) {
    pix = orig;
}
return mix(orig, pix, opacity);
```

## CPU Fallback
```python
import numpy as np

def pixelate_cpu(frame, block_size, density, opacity):
    h,w=frame.shape[:2]
    out = frame.copy()
    bs = int(block_size)
    for y in range(0,h,bs):
        for x in range(0,w,bs):
            if np.random.rand() > density:
                continue
            block = frame[y:y+bs,x:x+bs]
            avg = block.mean(axis=(0,1),dtype=np.uint8)
            out[y:y+bs,x:x+bs] = avg
    return ((1-opacity)*frame + opacity*out).astype(np.uint8)
```

## Presets
- `Censor`: block_size=80, density=1.0, opacity=1.0
- `Retro`: block_size=10, density=0.5, opacity=1.0
- `Sparse`: block_size=20, density=0.3, opacity=0.8

## Edge Cases
- `block_size <1`: clamp to 1
- `density` outside [0,1]: clamp
- random generator seed should be controllable for deterministic tests

## Test Plan
- `test_block_size_remap`
- `test_density_effect`
- `test_opacity_blend`
- `test_cpu_gpu_parity` (fixed seed)
- `test_zero_block_size_clamps`
- `test_performance_1080p`

## Verification Checklist
- [ ] Blocks align with pixel grid
- [ ] Density behaves statistically
- [ ] Presets produce expected visuals
- [ ] CPU fallback produces same result when seeded


---

**Note:** Quality of randomness influences look; use hashing in shader for
reproducibility across frames when density<1.

