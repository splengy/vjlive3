# P7-VE45: Hyperspace Tunnel

> **Task ID:** `P7-VE45`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/core/hyperspace/hyperspace_tunnel.py`)
> **Class:** `HyperspaceTunnelEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
This effect simulates a starfield tunnel rushing past the viewer—classic
hyperspace visuals used in sci‑fi and VJ sets. The original draws concentric
rings and streaks with depth cues. We'll port logic for speed, density,
rotation, and color modulation.

## Technical Requirements
- Register plugin via manifest, subclassing `Effect`
- Parameters: `speed`, `star_density`, `rotation`, `depth`, `color_shift`,
  `opacity`
- Efficient GPU shader generating points with radial blur; CPU fallback using
  NumPy/Canvas drawing
- Maintain 60 FPS at 1080p (Safety Rail 1)
- ≥80 % test coverage (Safety Rail 5)
- Spec <750 lines (Safety Rail 4)
- Input validation for nonnegative parameters; cap depth to reasonable value
  (Safety Rail 7)

## Public Interface
```python
class HyperspaceTunnelEffect(Effect):
    """Generates a moving tunnel of stars with depth and rotation."""

    def __init__(self,width=1920,height=1080,use_gpu=True):
        super().__init__("HyperspaceTunnel", HYPERSPACE_VERTEX_SHADER,
                         HYPERSPACE_FRAGMENT_SHADER)
        self.effect_category="geometry"
        self.effect_tags=["tunnel","warp","stars"]
        self.features=["PARTICLE_FIELD","RADIAL_BLUR"]
        self.usage_tags=["STYLING","PERFORMANCE","BACKGROUND"]
        self.use_gpu=use_gpu

        self._parameter_ranges={'speed':(0.0,10.0),
                                 'star_density':(0.0,10.0),
                                 'rotation':(0.0,10.0),
                                 'depth':(0.0,10.0),
                                 'color_shift':(0.0,10.0),
                                 'opacity':(0.0,10.0)}
        self.parameters={'speed':5.0,'star_density':5.0,'rotation':5.0,
                         'depth':5.0,'color_shift':0.0,'opacity':10.0}
        self._parameter_descriptions={
            'speed':'Forward velocity',
            'star_density':'Number of stars per unit',
            'rotation':'Spin of tunnel',
            'depth':'Number of concentric rings',
            'color_shift':'Hue shift over depth',
            'opacity':'Blend to original'}
        self._sweet_spots={'speed':[3,5,7],'star_density':[4,6,8]}

    def render(self,tex_in,extra_textures=None,chain=None):
        # generate tunnel using fragment math, no texture input needed
        pass

    def apply_uniforms(self,time,resolution,audio_reactor=None,
                      semantic_layer=None):
        # remap parameters, incorporate time and maybe audio
        pass
```

### Parameter Remaps
- `speed` → V = map_linear(x,0,10,0.1,50.0) units/sec
- `star_density` → D = map_linear(x,0,10,0.0,1.0)
- `rotation` → R = map_linear(x,0,10,0,2π) rad/sec
- `depth` → H = int(map_linear(x,0,10,1,20)) rings
- `color_shift` → C = map_linear(x,0,10,0,1) fraction of hue cycle
- `opacity` → α = x/10

## Shader Uniforms
- `uniform float speed;`
- `uniform float star_density;`
- `uniform float rotation;`
- `uniform int depth;`
- `uniform float color_shift;`
- `uniform float time;`
- `uniform float opacity;`
- `uniform vec2 resolution;`

## Effect Math (GLSL outline)
```
vec2 uv = (gl_FragCoord.xy / resolution) - 0.5;
float angle = atan(uv.y, uv.x) + rotation * time;
float radius = length(uv);
float z = mod(time * speed - radius, 1.0);
vec3 col = vec3(0);
for (int i = 0; i < depth; ++i) {
    float ring = fract((radius + float(i)/float(depth)) * star_density - time*speed);
    float brightness = smoothstep(0.98,1.0,ring);
    float hue = fract(angle/(2.0*PI) + color_shift * float(i)/float(depth));
    col += hsv2rgb(vec3(hue,1,brightness));
    radius -= 1.0/float(depth);
}
return mix(texture(tex_in, uv+0.5).rgb, col, opacity);
```

## CPU Fallback
```python
import numpy as np

def hyperspace_cpu(frame, speed, star_density, rotation,
                   depth, color_shift, time, opacity):
    h,w = frame.shape[:2]
    yy,xx = np.indices((h,w))
    uvx = xx/w - 0.5
    uvy = yy/h - 0.5
    angle = np.arctan2(uvy,uvx) + rotation*time
    radius = np.hypot(uvx,uvy)
    col = np.zeros_like(frame, dtype=np.float32)
    for i in range(depth):
        ring = np.mod(radius*star_density - time*speed + i/float(depth),1.0)
        brightness = np.clip((ring-0.98)/0.02,0,1)
        hue = np.mod(angle/(2*np.pi) + color_shift*i/float(depth),1.0)
        rgb = hsv_to_rgb(np.stack([hue, np.ones_like(hue), brightness],axis=-1))
        col += rgb
        radius -= 1.0/float(depth)
    col = np.clip(col,0,1)
    return ((1-opacity)*frame + opacity*(col*255)).astype(np.uint8)
```

## Presets
- `Classic Tunnel`: speed=8, star_density=0.8, depth=10
- `Rainbow Spin`: color_shift=1, rotation=5, depth=15
- `Slow Drift`: speed=2, opacity=0.5

## Edge Cases
- `depth` <=0: clamp to 1
- `star_density` >1: wrap to 1
- `rotation` negative allowed
- Large `speed` may wrap input coordinates; use mod

## Test Plan
- `test_parameter_remaps`
- `test_depth_iterations`
- `test_color_shift_cycle`
- `test_cpu_gpu_parity`
- `test_performance_1080p`
- `test_invalid_params_clamp`

## Verification Checklist
- [ ] Tunnel appears with correct perspective
- [ ] Rotation and speed behave independently
- [ ] CPU fallback produces similar look
- [ ] Presets trigger expected styles

---

**Note:** Because this effect is primarily procedural, there's no texture
input—document that pipelines should feed a black frame or ignore input.

