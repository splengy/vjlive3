# P7-VE44: Hyperion (Complex Warp)

> **Task ID:** `P7-VE44`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/core/vimana/hyperion.py`)
> **Class:** `VimanaHyperion`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Hyperion is one of the signature Vimana effects—a swirling, multi‑layered
warp that reacts to audio and time. It produces psychedelic tunnels, fractal
vortices, and complex kaleidoscopes. Our port must capture its parameters
(e.g. twist, scale, color cycles) while fitting into the new architecture.

## Technical Requirements
- Plugin registration via manifest; subclass `Effect` with audio-reactive
  capabilities
- Parameters: `twist`, `radius`, `speed`, `depth`, `opacity`, `audio_reactive`
- GPU shader implementing iterative coordinate transforms; CPU fallback using
  vectorized NumPy loops
- Maintain 60 FPS at 1080p (Safety Rail 1)
- ≥80 % test coverage (Safety Rail 5)
- Spec <750 lines (Safety Rail 4)
- Validate parameter ranges; audio-reactive toggles (Safety Rail 7)

## Public Interface
```python
class VimanaHyperion(Effect):
    """Complex generative warp with audio reactivity."""

    def __init__(self,width=1920,height=1080,use_gpu=True):
        super().__init__("Hyperion", HYPERION_VERTEX_SHADER,
                         HYPERION_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["warp","audio-reactive","fractal"]
        self.features=["ITERATIVE_WARP","AUDIO_REACTIVE"]
        self.usage_tags=["STYLING","PERFORMANCE"]
        self.use_gpu=use_gpu

        self._parameter_ranges={'twist':(0.0,10.0),
                                 'radius':(0.0,10.0),
                                 'speed':(0.0,10.0),
                                 'depth':(0.0,10.0),
                                 'opacity':(0.0,10.0),
                                 'audio_reactive':(0.0,10.0)}
        self.parameters={'twist':5.0,'radius':5.0,'speed':5.0,
                         'depth':5.0,'opacity':10.0,'audio_reactive':0.0}
        self._parameter_descriptions={
            'twist':'Angular distortion intensity',
            'radius':'Radius of effect influence',
            'speed':'Animation speed',
            'depth':'Number of iterations',
            'opacity':'Blend to original',
            'audio_reactive':'Enable audio reactivity'}
        self._sweet_spots={'twist':[3,5,7],'depth':[2,4,6]}

    def render(self,tex_in,extra_textures=None,chain=None):
        # iterative warp using uniforms computed below
        pass

    def apply_uniforms(self,time,resolution,audio_reactor=None,
                      semantic_layer=None):
        # remap basic parameters and optionally modulate by audio band
        pass
```

### Parameter Remaps
- `twist` → T = map_linear(x,0,10,0,10) radians per iteration
- `radius` → R = map_linear(x,0,10,0.0,1.0) fraction of min(resolution)
- `speed` → S = map_linear(x,0,10,0.0,5.0) rotations per second
- `depth` → D = int(map_linear(x,0,10,1,10)) iterations
- `opacity` → α = x/10
- `audio_reactive` → A = round(map_linear(x,0,10,0,1))

Audio reactor if enabled will modulate `twist` and/or `radius` based on
low-frequency energy.

## Shader Uniforms
- `uniform float twist;`
- `uniform float radius;`
- `uniform float speed;`
- `uniform int depth;`
- `uniform float time;`
- `uniform float opacity;`
- `uniform float audio_amt;` // 0..1
- `uniform sampler2D tex_in;`
- `uniform vec2 resolution;`

## Effect Math (pseudo-GLSL)
```
vec2 uv = gl_FragCoord.xy / resolution - 0.5;
float angle = atan(uv.y, uv.x);
float r = length(uv);
for (int i = 0; i < depth; ++i) {
    angle += twist + speed * time + audio_amt;
    uv = vec2(cos(angle), sin(angle)) * r;
    r *= radius;
}
vec2 warped = uv + 0.5;
vec3 color = texture(tex_in, warped).rgb;
vec3 orig = texture(tex_in, gl_FragCoord.xy/resolution).rgb;
return mix(orig, color, opacity);
```

## CPU Fallback
```python
import numpy as np

def hyperion_cpu(frame, twist, radius, speed, depth, time,
                 audio_amt, opacity):
    h,w=frame.shape[:2]
    yy,xx = np.indices((h,w))
    uvx = (xx/w - 0.5)
    uvy = (yy/h - 0.5)
    ang = np.arctan2(uvy,uvx)
    r = np.hypot(uvx,uvy)
    for i in range(depth):
        ang += twist + speed*time + audio_amt
        uvx = np.cos(ang) * r
        uvy = np.sin(ang) * r
        r *= radius
    warped_x = ((uvx + 0.5)*w).astype(int) % w
    warped_y = ((uvy + 0.5)*h).astype(int) % h
    warped = frame[warped_y,warped_x]
    return ((1-opacity)*frame + opacity*warped).astype(np.uint8)
```

## Presets
- `Classic Hyperion`: twist=5, radius=0.8, speed=2, depth=5
- `Deep Tunnel`: radius=0.95, depth=9, opacity=0.8
- `Audio Reactive`: audio_reactive=1, twist=2, speed=1

## Edge Cases
- depth <1: clamp to 1
- radius ≤0: clamp to 0.01
- angle overflow: use mod2π to avoid precision loss
- audio reactor unavailable: treat audio_amt=0

## Test Plan
- `test_parameter_remaps`
- `test_iteration_count`
- `test_audio_reactive_mode`
- `test_cpu_gpu_parity`
- `test_performance_1080p`
- `test_invalid_params_clamp`

## Verification Checklist
- [ ] Warp arises symmetrically around center
- [ ] Audio reactivity toggles correctly
- [ ] CPU fallback approximates GPU output within tolerance
- [ ] Presets produce recognizably named patterns

---

**Note:** This effect is computationally intensive; caching of precomputed
constants (e.g. sin/cos tables) may help in CPU path.

