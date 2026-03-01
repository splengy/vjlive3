````markdown
# P7-VE35: Fluid Simulation Effect (Navier–Stokes Dye)

> **Task ID:** `P7-VE35`
> **Priority:** P0 (Critical)
> **Source:** VJlive‑2 (`plugins/core/fluid_sim/fluid_sim.py`)
> **Class:** `FluidSimEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
This effect integrates a 2‑D fluid solver (sourced from VJlive‑2) into
VJLive3 as a generative visual tool. It models incompressible Navier–Stokes
flow on a grid, advecting velocity and dye fields, and allows parameterized
sources, viscosity, and boundary conditions. The resulting velocity field can
warp input video or supply colorful dye patterns. The spec covers solver math,
parameter remaps, GPU/CPU kernels, performance considerations, and an extensive
test suite.

## Technical Requirements
- Effect must maintain ≥60 FPS at 512×512 simulation grid (Safety Rail 1)
- Provide parameters: viscosity, diffusion, force, dye injection, grid size
- Implement semi‑Lagrangian advection, Jacobi pressure solve with divergence
- <750 lines spec (Safety Rail 4)
- ≥80 % coverage with unit tests (Safety Rail 5)
- CPU fallback using NumPy + simple loops for verification

## Implementation Notes
1. Use dual‑FBO ping‑pong for velocity and dye textures.
2. Advect velocity with itself; apply forces and viscosity.
3. Project step: compute divergence, solve Poisson for pressure (Jacobi),
   subtract gradient to make velocity divergence‑free.
4. Advect dye field through velocity; apply diffusion.
5. Provide optional external velocity injection by user input (mouse/audio).

## Public Interface
```python
class FluidSimEffect(Effect):
    """
    FluidSim Effect: 2D incompressible fluid solver.
    """

    def __init__(self, width:int=512, height:int=512,
                 use_gpu:bool=True):
        super().__init__("FluidSim", FLUID_VERTEX_SHADER,
                         FLUID_FRAGMENT_SHADER)
        self.effect_category = "simulation"
        self.effect_tags = ["fluid","navierstokes","dye"]
        self.features = ["FLUID_SIM"]
        self.usage_tags = ["GENERATIVE","PHYSICS"]

        self.use_gpu = use_gpu

        self._parameter_ranges = {
            'viscosity':(0.0,10.0),
            'diffusion':(0.0,10.0),
            'force_strength':(0.0,10.0),
            'dye_amount':(0.0,10.0),
            'decay':(0.0,10.0),
            'opacity':(0.0,10.0)
        }
        self.parameters={'viscosity':5.0,'diffusion':5.0,'force_strength':5.0,
                         'dye_amount':5.0,'decay':5.0,'opacity':10.0}
        self._parameter_descriptions={
            'viscosity':'Resistance (0=free,smooth;10=thick)',
            'diffusion':'Dye spread rate',
            'force_strength':'Amount of velocity added per input',
            'dye_amount':'Amount of dye injected per input',
            'decay':'Dye fade rate',
            'opacity':'Final compositing opacity'
        }
        self._sweet_spots={'viscosity':[4,5,6],'diffusion':[4,5,6]}

    def render(self, tex_in:int=None, extra_textures:list=None, chain=None)->int:
        # perform solver step (advect/project/diffuse/inject)
        # output dyed velocity as color or warp input
        pass

    # Below are pseudocode helper functions representing GPU kernels
    def advect(self, field, velocity, dt, dissipation):
        """Semi-Lagrangian advection of a scalar/vector field."""
        pass

    def project(self, velocity):
        """Make velocity divergence-free via pressure solve."""
        pass

    def apply_uniforms(self, time:float,resolution:tuple,
                      audio_reactor=None,semantic_layer=None):
        # compute internal parameters (viscosity=map_linear, etc.)
        pass
```

### Parameter Remaps
- `viscosity` → ν = map_linear(x,0,10, 0.0, 0.1)
- `diffusion` → κ = map_linear(x,0,10, 0.0, 0.1)
- `force_strength` → F = map_linear(x,0,10, 0.0, 100.0)
- `dye_amount` → D = map_linear(x,0,10, 0.0, 1.0)
- `decay` → δ = map_linear(x,0,10, 0.0, 0.99)
- `opacity` → α = x/10

## Simulation Math (GPU / CPU consistency)

```
# grid spacing h = 1/N (normalized)
dt = 0.016  # assume 60fps

# Advect velocity:
vel = advect(vel, vel, dt, 1.0)

# add viscosity via diffusion term (implicit)
vel = vel + ν * laplacian(vel) * dt

# project step
vel = project(vel)

# advect dye field through velocity
dye = advect(dye, vel, dt, δ)

# apply diffusion to dye
dye = dye + κ * laplacian(dye) * dt

# apply decay
dye *= δ

# optional external injection
if input():
    vel += F * input_force
    dye += D * input_color
```

Projection details:
```
div = ∂x vel.x + ∂y vel.y
p = 0
for i in range(20):
    p = (div + laplacian(p)) / 4
vel.x -= ∂x p
vel.y -= ∂y p
```

## CPU Fallback (NumPy sketch)

```python
def fluid_step_cpu(vel, dye, params, input_force=None, input_color=None):
    h,w=vel.shape[:2]
    # simple finite differences for laplacian/divergence
    # advection: backtrace and sample
    # use loops or vectorized np.roll for derivatives
    # omitted for brevity, see standard stable fluid implementations
    return vel_new,dye_new
```

## Presets
- `Smoke`: viscosity=7,diffusion=2,decay=0.95
- `Ink`: viscosity=2,diffusion=8,decay=0.99
- `Plasma`: viscosity=1,diffusion=1,decay=0.9
- `Still`: force_strength=0,dye_amount=0

## Edge Cases
- zero grid size (use fallback)
- solver divergence (cap iterations)

## Test Plan
- `test_pass_through_zero_force`
- `test_viscosity_effect`
- `test_dye_diffusion`
- `test_projection_div_free`
- `test_cpu_gpu_parity_limited_resolution`
- `test_60fps_performance` (profile)

## Verification
- [ ] Velocity field remains divergence-free
- [ ] Dye advection follows flow lines
- [ ] Parameter remaps produce expected behaviour

````
