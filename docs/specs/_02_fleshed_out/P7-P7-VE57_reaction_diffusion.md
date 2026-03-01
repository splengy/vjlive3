# P7-VE57: Reaction Diffusion Effect

> **Task ID:** `P7-VE57`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/core/reaction_diffusion/reaction_diffusion.py`)
> **Class:** `ReactionDiffusionEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Reaction–diffusion systems model the interaction of chemical or wave properties
across a domain. In VJL, this creates organic, growing patterns (Turing patterns,
waves, branching structures). This classic procedural effect was central to
VJlive-2's abstract library and must be ported intact.

## Technical Requirements
- Manifest-registered `Effect` subclass with dual-texture ping-pong feedback.
- Parameters: `feed_rate`, `kill_rate`, `diffusion_a`, `diffusion_b`, `sim_speed`,
  `opacity`.
- GPU implementation with multi-pass shader loop simulating Gray–Scott model;
  CPU fallback using NumPy convolution.
- Maintain 60 FPS at 1080p at moderate diffusion scales.
- ≥80 % test coverage; explicit error handling for parameter bounds.
- Keep spec <750 lines.

## Public Interface
```python
class ReactionDiffusionEffect(Effect):
    """Procedural Reaction-Diffusion (Gray-Scott) pattern generator."""

    def __init__(self, width=1920, height=1080, use_gpu=True):
        super().__init__("ReactionDiffusion",
                         vertex_shader=DIFFUSION_VERT,
                         fragment_shader=DIFFUSION_FRAG)
        self.effect_category = "procedural"
        self.effect_tags = ["organic", "procedural", "feedback"]
        self.features = ["MULTI_PASS", "STATEFUL"]
        self.parameters = {
            'feed_rate': 5.0,
            'kill_rate': 5.0,
            'diffusion_a': 5.0,
            'diffusion_b': 5.0,
            'sim_speed': 5.0,
            'opacity': 10.0
        }
        self._parameter_ranges = {
            'feed_rate': (0.0, 10.0),
            'kill_rate': (0.0, 10.0),
            'diffusion_a': (0.0, 10.0),
            'diffusion_b': (0.0, 10.0),
            'sim_speed': (0.0, 10.0),
            'opacity': (0.0, 10.0)
        }
        self._param_desc = {
            'feed_rate': 'Chemical feed rate (f).',
            'kill_rate': 'Chemical kill rate (k).',
            'diffusion_a': 'Diffusion of A component.',
            'diffusion_b': 'Diffusion of B component.',
            'sim_speed': 'Integration time steps per frame.',
            'opacity': 'Blend factor to source frame.'
        }
        self._state = {'buffer_a': None, 'buffer_b': None}
        self.use_gpu = use_gpu

    def render(self, tex_in, extra_textures=None, chain=None):
        # Ping-pong through simulation steps, return blended result
        pass

    def apply_uniforms(self, time, resolution, audio=None, semantic=None):
        # Map parameters and update simulation state
        pass
```

### Parameter Remaps
- `feed_rate` → F = map_linear(x, 0, 10, 0.02, 0.08)
- `kill_rate` → K = map_linear(x, 0, 10, 0.02, 0.08)
- `diffusion_a` → Da = map_linear(x, 0, 10, 0.2, 1.0)
- `diffusion_b` → Db = map_linear(x, 0, 10, 0.1, 0.5)
- `sim_speed` → steps = int(map_linear(x, 0, 10, 1, 16))
- `opacity` → α = x / 10

## Shader Uniforms
```glsl
uniform float feed_rate;
uniform float kill_rate;
uniform float dA;
uniform float dB;
uniform int steps;
uniform sampler2D tex_A;  // u (activator)
uniform sampler2D tex_B;  // v (inhibitor)
```

## Effect Math
**Gray–Scott Reaction–Diffusion:**
```
∂u/∂t = dA·∇²u - u·v² + f·(1 - u)
∂v/∂t = dB·∇²v + u·v² - (f + k)·v
```

Where u is activator, v is inhibitor; ∇² is discrete Laplacian:
```
∇²X ≈ (X_left + X_right + X_above + X_below - 4·X_center) / scale
```

## CPU Fallback
```python
import numpy as np
from scipy.ndimage import convolve

def reaction_diffusion_step(u, v, dA, dB, f, k, dt=0.1):
    # Laplacian kernel
    kernel = np.array([[0.05, 0.2, 0.05],
                       [0.2, -1.0, 0.2],
                       [0.05, 0.2, 0.05]])
    lap_u = convolve(u, kernel, mode='wrap')
    lap_v = convolve(v, kernel, mode='wrap')
    
    uvv = u * v * v
    du = dA * lap_u - uvv + f * (1 - u)
    dv = dB * lap_v + uvv - (f + k) * v
    
    u_new = u + du * dt
    v_new = v + dv * dt
    return np.clip(u_new, 0, 1), np.clip(v_new, 0, 1)
```

## Presets
- `Classic Mitosis`: f=0.025, k=0.06
- `Spirals`: f=0.03, k=0.062
- `Spots`: f=0.015, k=0.055
- `Waves`: f=0.04, k=0.062

## Edge Cases
- Boundary conditions wrap (toroidal topology).
- f + k must not exceed safe range (numerical stability).
- Uninitialized buffers seeded with small random perturbations.

## Test Plan
- `test_gray_scott_step`
- `test_buffer_init_and_evolution`
- `test_cpu_gpu_consistency`
- `test_performance_large_grid`
- `test_parameter_bounds_clamp`

## Verification Checklist
- [ ] Patterns emerge from random initial state
- [ ] Simulation remains numerically stable
- [ ] CPU/GPU outputs match within tolerance

---

**Note:** Stateful; initialize u with 1.0 everywhere, v with sparse random seeds.


