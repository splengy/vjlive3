# P3-EXT079_FluidSimEffect.md

# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT079 — FluidSimEffect

### What This Module Does
Implements a GPU-accelerated fluid simulation effect based on Navier-Stokes equations with dye injection and vorticity confinement. Can function as both a standalone generator (producing fluid patterns) or as an effect (blending fluid simulation with input video).

### What This Module Does NOT Do
Does not handle audio reactivity or advanced particle systems. Focuses solely on fluid dynamics simulation and rendering.

### Detailed Behavior and Parameter Interactions

#### Core Simulation
- **Navier-Stokes Solver**: Solves incompressible fluid dynamics on GPU
- **Dye Injection**: Injects colored dye into the fluid field
- **Vorticity Confinement**: Preserves small-scale vortices for visual detail
- **Advection**: Transports velocity and dye fields through the flow

#### Key Parameters
1. **viscosity** (float, 0.0-10.0): Fluid viscosity (higher = thicker, slower flow)
2. **vorticity** (float, 0.0-10.0): Vorticity confinement strength (preserves swirls)
3. **dissipation** (float, 0.0-10.0): Rate of velocity/dye decay over time
4. **velocity_decay** (float, 0.0-10.0): Specific velocity field decay rate
5. **turbulence** (float, 0.0-10.0): Amount of random turbulence injection
6. **inject_mode** (float, 0.0-1.0): Dye injection pattern type
7. **inject_radius** (float, 0.0-10.0): Radius of dye injection area
8. **inject_force** (float, 0.0-10.0): Force of dye injection
9. **render_mode** (float, 0.0-10.0): Visual rendering style (0=velocity, 10=dye)
10. **opacity** (float, 0.0-1.0): Overall effect opacity when used as effect
11. **inject_hue_speed** (float, 0.0-10.0): Rate of hue cycling for psychedelic effects

#### Presets
- **gentle_flow**: Low viscosity, moderate vorticity, slow dissipation
- **ink_in_water**: Medium viscosity, high vorticity, ink-like behavior
- **turbulent_storm**: Low viscosity, high vorticity, high turbulence
- **psychedelic_lava**: Medium viscosity, high vorticity, hue cycling

#### Dual Mode Operation
- **Generator Mode**: Outputs fluid simulation directly (no input required)
- **Effect Mode**: Blends fluid with input video using `u_mix` parameter

### Public Interface
```python
class FluidSimEffect(Effect):
    def __init__(self):
        # Initialize with default parameters
        # Set up shader program and FBOs

    def update(self, dt: float):
        # Step fluid simulation forward by dt seconds
        # Advection, force application, projection steps

    def render(self, texture: int, extra_textures: list = None) -> int:
        # If input texture provided, blend fluid with it
        # Otherwise output fluid directly

    def set_parameter(self, name: str, value: float):
        # Update simulation parameters in real-time

    def inject_dye(self, position: tuple, color: tuple, radius: float, force: float):
        # Inject dye at specified position with given properties
```

### Inputs and Outputs
- **Inputs**: 
  - Optional video texture (for effect mode)
  - Extra textures for advanced compositing
- **Outputs**: 
  - Fluid simulation result (RGBA velocity + dye)
  - When used as effect: blended result

### Edge Cases and Error Handling
- Invalid parameter ranges (clamp to valid ranges)
- Missing shader compilation (fallback to solid color)
- FBO allocation failures (graceful degradation)
- Extremely high viscosity causing simulation instability

### Mathematical Formulations

#### Navier-Stokes (Incompressible)
```
∂u/∂t = -(u·∇)u + ν∇²u - ∇p + f
∇·u = 0
```
Where:
- u = velocity field
- ν = viscosity (parameter)
- p = pressure
- f = external forces (turbulence, injection)

#### Advection
```
u_new = u_old - Δt * (u_old · ∇)u_old
dye_new = dye_old - Δt * (u_old · ∇)dye_old
```

#### Vorticity Confinement
```
ω = ∇ × u  // vorticity
F_vort = ε * (|ω| ∇|ω|) × ω / (|ω|² + ε)
```

#### Dissipation
```
velocity *= (1.0 - velocity_decay * dt)
dye *= (1.0 - dissipation * dt)
```

### Performance Characteristics
- **GPU-Bound**: Entirely shader-based, runs on GPU
- **Memory**: ~2-3 full-screen FBOs (velocity, pressure, dye)
- **Resolution Dependent**: O(N) where N = pixel count
- **Typical Performance**: 60+ FPS at 1080p on mid-range GPU
- **Multi-pass**: Requires 3-5 render passes per frame

### Test Plan
1. Verify shader compilation on different GPU vendors
2. Test parameter ranges and clamping behavior
3. Validate preset configurations produce expected visual results
4. Measure performance at various resolutions (720p, 1080p, 4K)
5. Test generator vs effect mode switching
6. Verify FBO cleanup on destruction

### Definition of Done
- [ ] Spec reviewed by Manager
- [ ] All test cases pass
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

## LEGACY CODE REFERENCES
- core/effects/fluid_sim.py (Main implementation)
- core/effects/generative/fluid_sim.py (Alternative location)
- plugins/vcore/fluid_sim.py (Plugin version)
- core/matrix/node_effect_fluid.py (Node wrapper)
- tests/test_legacy_migration.py (Test coverage)
- plugin.json (Parameter definitions)
