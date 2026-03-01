# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT186_vattractors.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT186 — vattractors (VLorenzPlugin)

**What This Module Does**

The `VLorenzPlugin` implements the Lorenz chaotic attractor, a three-dimensional dynamical system that produces the famous "butterfly" pattern. This attractor is used in VJLive3 for generating organic, evolving visual modulation patterns that respond to audio and user parameters in real-time.

The Lorenz attractor is defined by the following system of differential equations:

```
dx/dt = sigma * (y - x)
dy/dt = x * (rho - z) - y
dz/dt = x * y - beta * z
```

Where `sigma`, `rho`, and `beta` are control parameters. The system exhibits chaotic behavior for the classic parameter set (sigma=10, rho=28, beta=8/3), producing a non-repeating trajectory that resembles a butterfly.

The module provides:
- Real-time simulation of the attractor's state (x, y, z)
- Parameter control for `sigma`, `rho`, and `beta`
- Integration with the VJLive3 modulation ecosystem
- Metadata-driven configuration for UI integration
- State reset capability for deterministic behavior

The output (x, y, z) values are normalized to a 0-1 range for use as modulation signals in other VJLive3 plugins.

**What This Module Does NOT Do**

- Does not render visual output directly (it's a modulation source)
- Does not handle audio input or synchronization
- Does not implement 3D rendering or point cloud visualization
- Does not provide audio output
- Does not store or replay attractor trajectories
- Does not implement attractor blending with other systems (e.g., Halvorsen, Thomas)
- Does not provide GUI controls (UI is handled by ProgramPage)

---

## Detailed Behavior and Parameter Interactions

### Core Algorithm

The Lorenz attractor is integrated using a fourth-order Runge-Kutta method for numerical stability. The state variables (x, y, z) are updated each frame based on the differential equations:

```python
def step(self, dt):
    # Runge-Kutta 4th order integration
    k1x = self.sigma * (self.y - self.x)
    k1y = self.x * (self.rho - self.z) - self.y
    k1z = self.x * self.y - self.beta * self.z
    
    k2x = self.sigma * ((self.y + 0.5*dt*k1y) - (self.x + 0.5*dt*k1x))
    k2y = (self.x + 0.5*dt*k1x) * (self.rho - (self.z + 0.5*dt*k1z)) - (self.y + 0.5*dt*k1y)
    k2z = (self.x + 0.5*dt*k1x) * (self.y + 0.5*dt*k1y) - self.beta * (self.z + 0.5*dt*k1z)
    
    k3x = self.sigma * ((self.y + 0.5*dt*k2y) - (self.x + 0.5*dt*k2x))
    k3y = (self.x + 0.5*dt*k2x) * (self.rho - (self.z + 0.5*dt*k2z)) - (self.y + 0.5*dt*k2y)
    k3z = (self.x + 0.5*dt*k2x) * (self.y + 0.5*dt*k2y) - self.beta * (self.z + 0.5*dt*k2z)
    
    k4x = self.sigma * ((self.y + dt*k3y) - (self.x + dt*k3x))
    k4y = (self.x + dt*k3x) * (self.rho - (self.z + dt*k3z)) - (self.y + dt*k3y)
    k4z = (self.x + dt*k3x) * (self.y + dt*k3y) - self.beta * (self.z + dt*k3z)
    
    self.x += (dt/6) * (k1x + 2*k2x + 2*k3x + k4x)
    self.y += (dt/6) * (k1y + 2*k2y + 2*k3y + k4y)
    self.z += (dt/6) * (k1z + 2*k2z + 2*k3z + k4z)
    
    return self.x, self.y, self.z
```

### Parameter Roles

The three parameters have distinct roles in controlling the attractor's behavior:

- **`sigma` (σ)**: The Prandtl number. Controls the rate of momentum transfer. Higher values increase the "stretch" in the x-y plane. Classic value: 10.0. Range: 0.0-30.0.
- **`rho` (ρ)**: The Rayleigh number. Controls the distance between the two lobes. Higher values increase the size of the attractor. Classic value: 28.0. Range: 0.0-50.0.
- **`beta` (β)**: The aspect ratio parameter. Controls the rate of dissipation in the z-direction. Classic value: 8/3 ≈ 2.6667. Range: 0.0-10.0.

In the legacy system, these were mapped to `speed` and `amplitude` UI controls (0-10 range). The VJLive3 implementation uses direct parameter control for clarity.

### State Initialization

The attractor starts with initial conditions:
- `x = 0.1`
- `y = 0.0`
- `z = 0.0`

These values are near the attractor's basin of attraction. The system is deterministic, so identical initial conditions produce identical trajectories.

### Output Normalization

The raw attractor output (x, y, z) can range from approximately -20 to +20. For use in VJLive3's modulation system, these values are normalized to a 0-1 range:

```python
def _normalize(self, val: float, scale: float = 30.0) -> float:
    """Normalize attractor output to 0-1 range."""
    amp = self.amplitude / 5.0  # if using amplitude scaling
    return max(0.0, min(1.0, (val / scale + 1.0) * 0.5)) * amp
```

The legacy node wrapper uses `scale=30.0` and an amplitude factor derived from the `amplitude` parameter. The VJLive3 implementation should follow this normalization to maintain compatibility.

### Reset Behavior

The `reset()` method sets the state back to initial conditions:
- `x = 0.1`
- `y = 0.0`
- `z = 0.0`

This allows for deterministic behavior when restarting a performance or changing parameters.

---

## Integration

### VJLive3 Modulation Ecosystem

The `VLorenzPlugin` is a **modulation source** that integrates into the VJLive3 plugin ecosystem as follows:

```
[User Parameters] → [VLorenzPlugin] → [Modulation Output] → [Other Plugins]
```

**Position in pipeline**:
- The plugin is instantiated as a modulation source in the ProgramPage UI
- It receives `dt` (delta time) from the VJLive3 time manager
- It outputs normalized (x, y, z) values to other plugins via the `step(dt)` method
- Other plugins can query these values to modulate parameters like color, position, scale, or opacity

**Typical usage**:

```python
# Initialize
lorenz = VLorenzPlugin(sigma=10.0, rho=28.0, beta=8/3)

# In the main loop (called once per frame)
x, y, z = lorenz.step(delta_time)

# Use output to modulate other effects
effect.color = (x, y, z)  # Color modulation
effect.scale = y * 2.0    # Scale modulation
effect.position = (x, y, 0)  # Position modulation
```

**Metadata Integration**:

The `get_metadata()` method returns a dictionary that the ProgramPage UI uses to generate controls:

```python
{
    "name": "Lorenz Attractor",
    "description": "Lorenz chaotic attractor — butterfly-pattern modulation",
    "parameters": [
        {"id": "sigma", "name": "Sigma", "min": 0.0, "max": 30.0, "default": 10.0},
        {"id": "rho", "name": "Rho", "min": 0.0, "max": 50.0, "default": 28.0},
        {"id": "beta", "name": "Beta", "min": 0.0, "max": 10.0, "default": 2.6667}
    ],
    "default_values": {"sigma": 10.0, "rho": 28.0, "beta": 2.6667}
}
```

### Time Management

The module relies on the VJLive3 `TimeManager` to provide accurate `delta_time` values. The `TimeManager` should:
- Use a high-resolution timer
- Account for pauses or frame drops
- Provide consistent time deltas even if frame rate varies

The Runge-Kutta integration is stable with variable `delta_time`, but smaller values (e.g., 1/60s) provide more accurate trajectories.

---

## Performance

### Computational Cost

The module is **CPU-bound** but extremely lightweight. Each `step(dt)` call performs:
- 27 multiplications
- 18 additions/subtractions
- 6 comparisons for normalization

On any modern CPU, this is negligible (< 0.01 ms per call). The module can be updated every frame (60-120 Hz) without impact.

### Memory Usage

- **Minimal**: Stores 3 floats for state (x, y, z) and 3 floats for parameters (sigma, rho, beta)
- **No dynamic allocation** after initialization
- **No GPU resources** required

### Optimization Strategies

None needed. The module is already optimal.

### Platform-Specific Considerations

- **Desktop**: No issues
- **Embedded (Raspberry Pi)**: Still negligible CPU usage
- **Real-time audio contexts**: If used with audio processing, ensure `step()` is called from a real-time thread if needed (but likely not critical)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware absent (no external devices) |
| `test_basic_operation` | Core step() method returns valid (x, y, z) values for reasonable dt inputs |
| `test_error_handling` | Invalid parameter values (e.g., negative sigma, rho, or beta) raise appropriate exceptions |
| `test_reset_state` | reset() method sets internal state to initial conditions and produces consistent output on next step |
| `test_metadata_consistency` | get_metadata() returns correct field names, descriptions, and default values matching legacy VLorenzPlugin |
| `test_parameter_ranges` | Parameters outside valid range are clamped or raise ValueError |
| `test_deterministic_behavior` | Identical initial conditions and parameters produce identical trajectories |
| `test_step_consistency` | Multiple calls with same dt produce consistent state progression |
| `test_cleanup` | No resource leaks; can be destroyed cleanly |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

