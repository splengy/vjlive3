# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT185_vhalvorsenplugin.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT185 — VHalvorsenPlugin

**What This Module Does**

The `VHalvorsenPlugin` implements the Halvorsen chaotic attractor, a three-dimensional dynamical system that generates complex, non-repeating trajectories with sensitive dependence on initial conditions. This attractor is used in VJLive3 for generating organic, evolving visual modulation patterns that respond to audio and user parameters in real-time.

The Halvorsen attractor is defined by the following system of differential equations:

```
dx/dt = -a*x - 4*y - 4*z - y^2

dy/dt = -a*y - 4*z - 4*x - z^2

dz/dt = -a*z - 4*x - 4*y - x^2
```

Where `a` is a control parameter that determines the system's behavior. The system exhibits chaotic behavior for typical values of `a` in the range 1.0-3.0, producing spiral-like trajectories that never repeat.

The module provides:
- Real-time simulation of the attractor's state (x, y, z)
- Parameter control for `a`, `b`, and `c` (with `b` and `c` as additional modulation controls)
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
- Does not implement attractor blending with other systems (e.g., Lorenz, Thomas)
- Does not provide GUI controls (UI is handled by ProgramPage)

---

## Detailed Behavior and Parameter Interactions

### Core Algorithm

The Halvorsen attractor is integrated using a fourth-order Runge-Kutta method for numerical stability. The state variables (x, y, z) are updated each frame based on the differential equations:

```python
def step(self, dt):
    # Runge-Kutta 4th order integration
    k1x = -self.a * self.x - 4 * self.y - 4 * self.z - self.y * self.y
    k1y = -self.a * self.y - 4 * self.z - 4 * self.x - self.z * self.z
    k1z = -self.a * self.z - 4 * self.x - 4 * self.y - self.x * self.x
    
    k2x = -self.a * (self.x + 0.5*dt*k1x) - 4 * (self.y + 0.5*dt*k1y) - 4 * (self.z + 0.5*dt*k1z) - (self.y + 0.5*dt*k1y)**2
    k2y = -self.a * (self.y + 0.5*dt*k1y) - 4 * (self.z + 0.5*dt*k1z) - 4 * (self.x + 0.5*dt*k1x) - (self.z + 0.5*dt*k1z)**2
    k2z = -self.a * (self.z + 0.5*dt*k1z) - 4 * (self.x + 0.5*dt*k1x) - 4 * (self.y + 0.5*dt*k1y) - (self.x + 0.5*dt*k1x)**2
    
    k3x = -self.a * (self.x + 0.5*dt*k2x) - 4 * (self.y + 0.5*dt*k2y) - 4 * (self.z + 0.5*dt*k2z) - (self.y + 0.5*dt*k2y)**2
    k3y = -self.a * (self.y + 0.5*dt*k2y) - 4 * (self.z + 0.5*dt*k2z) - 4 * (self.x + 0.5*dt*k2x) - (self.z + 0.5*dt*k2z)**2
    k3z = -self.a * (self.z + 0.5*dt*k2z) - 4 * (self.x + 0.5*dt*k2x) - 4 * (self.y + 0.5*dt*k2y) - (self.x + 0.5*dt*k2x)**2
    
    k4x = -self.a * (self.x + dt*k3x) - 4 * (self.y + dt*k3y) - 4 * (self.z + dt*k3z) - (self.y + dt*k3y)**2
    k4y = -self.a * (self.y + dt*k3y) - 4 * (self.z + dt*k3z) - 4 * (self.x + dt*k3x) - (self.z + dt*k3z)**2
    k4z = -self.a * (self.z + dt*k3z) - 4 * (self.x + dt*k3x) - 4 * (self.y + dt*k3y) - (self.x + dt*k3x)**2
    
    self.x += (dt/6) * (k1x + 2*k2x + 2*k3x + k4x)
    self.y += (dt/6) * (k1y + 2*k2y + 2*k3y + k4y)
    self.z += (dt/6) * (k1z + 2*k2z + 2*k3z + k4z)
    
    return self.x, self.y, self.z
```

### Parameter Roles

The three parameters `a`, `b`, and `c` have distinct roles:

- **`a` (Sensitivity)**: Primary control parameter for chaos. Higher values increase system sensitivity and chaotic behavior. Range: 0.5-5.0 (legacy uses 0-10 mapped to 0.5-5.0). Default: 1.0
- **`b` (Oscillation Frequency)**: Secondary modulation parameter that scales the output amplitude. Higher values increase the frequency of oscillations. Range: 0.5-5.0. Default: 2.0
- **`c` (Stability/Chaos Level)**: Tertiary control that affects the attractor's stability. Higher values increase the complexity of the trajectory. Range: 0.5-5.0. Default: 3.0

In the legacy system, these parameters were mapped to `speed` and `amplitude` in the UI:
- `speed` (0-10) → `a` (0.5-5.0)
- `amplitude` (0-10) → `b` and `c` (0.5-5.0)

The VJLive3 implementation uses direct parameter control for clarity.

### State Initialization

The attractor starts with initial conditions:
- `x = 0.1`
- `y = 0.0`
- `z = 0.0`

These values are chosen to be near the attractor's basin of attraction. The system is deterministic, so identical initial conditions always produce identical trajectories.

### Output Normalization

The raw attractor output (x, y, z) can range from approximately -10 to +10. For use in VJLive3's modulation system, these values are normalized to a 0-1 range:

```
normalized_value = max(0.0, min(1.0, (raw_value + 10.0) / 20.0))
```

This ensures compatibility with other VJLive3 modules that expect normalized modulation signals.

### Reset Behavior

The `reset()` method sets the state back to initial conditions:
- `x = 0.1`
- `y = 0.0`
- `z = 0.0`

This allows for deterministic behavior when restarting a performance or changing parameters.

---

## Integration

### VJLive3 Modulation Ecosystem

The `VHalvorsenPlugin` is a **modulation source** that integrates into the VJLive3 plugin ecosystem as follows:

```
[User Parameters] → [VHalvorsenPlugin] → [Modulation Output] → [Other Plugins]
```

**Position in pipeline**:
- The plugin is instantiated as a modulation source in the ProgramPage UI
- It receives `dt` (delta time) from the VJLive3 time manager
- It outputs normalized (x, y, z) values to other plugins via the `step(dt)` method
- Other plugins can query these values to modulate parameters like color, position, scale, or opacity

**Typical usage**:

```python
# Initialize
halvorsen = VHalvorsenPlugin(a=1.5, b=2.5, c=3.5)

# In the main loop (called once per frame)
x, y, z = halvorsen.step(delta_time)

# Use output to modulate other effects
effect.color = (x, y, z)  # Color modulation
effect.scale = y * 2.0    # Scale modulation
effect.position = (x, y, 0)  # Position modulation
```

**Metadata Integration**:

The `get_metadata()` method returns a dictionary that the ProgramPage UI uses to generate controls:

```python
{
    "name": "Halvorsen Attractor",
    "description": "Halvorsen chaotic attractor — spiral modulation",
    "parameters": [
        {"id": "a", "name": "Sensitivity", "min": 0.5, "max": 5.0, "default": 1.0},
        {"id": "b", "name": "Frequency", "min": 0.5, "max": 5.0, "default": 2.0},
        {"id": "c", "name": "Chaos Level", "min": 0.5, "max": 5.0, "default": 3.0}
    ],
    "default_values": {"a": 1.0, "b": 2.0, "c": 3.0}
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
- 18 multiplications
- 12 additions/subtractions
- 6 square operations
- 6 comparisons for normalization

On any modern CPU, this is negligible (< 0.01 ms per call). The module can be updated every frame (60-120 Hz) without impact.

### Memory Usage

- **Minimal**: Stores 3 floats for state (x, y, z) and 3 floats for parameters (a, b, c)
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
| `test_error_handling` | Invalid parameter values (e.g., negative a, b, or c) raise appropriate exceptions |
| `test_reset_state` | reset() method sets internal state to initial conditions and produces consistent output on next step |
| `test_metadata_consistency` | get_metadata() returns correct field names, descriptions, and default values matching legacy VHalvorsenPlugin |
| `test_parameter_ranges` | Parameters outside valid range (0.5-5.0) are clamped or raise ValueError |
| `test_deterministic_behavior` | Identical initial conditions and parameters produce identical trajectories |
| `test_step_consistency` | Multiple calls with same dt produce consistent state progression |
| `test_cleanup` | No resource leaks; can be destroyed cleanly |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

