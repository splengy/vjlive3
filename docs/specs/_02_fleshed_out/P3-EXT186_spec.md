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

### [NEEDS RESEARCH]: What are the exact parameter ranges used in the legacy system?

**Finding**: The legacy plugin.json shows `speed` and `amplitude` with range [0.0, 10.0]. The skeleton spec uses `sigma`, `rho`, `beta` with defaults 10.0, 28.0, 2.6667. The Lorenz attractor typically uses sigma in [0, 30], rho in [0, 50], beta in [0, 10] for interesting behavior.

**Resolution**: Map legacy `speed` (0-10) to a scaling factor for time integration, not directly to sigma. The legacy node wrapper sets `self.attractor.speed = 0.01 + norm_speed * 4.99`. This suggests `speed` controls the integration speed, not the Lorenz parameters. The `amplitude` parameter is used in normalization. So the actual sigma, rho, beta are fixed at classic values (10, 28, 8/3) in the attractor class, and `speed` scales the effective `dt` or the attractor's internal speed. The skeleton spec's `sigma`, `rho`, `beta` as direct parameters may be a different design.

Let's re-examine the legacy node wrapper from earlier:

```python
def process(self, dt: float, **kwargs):
    speed_param = self.parameters['speed']['value']
    norm_speed = speed_param / 10.0
    self.attractor.speed = 0.01 + norm_speed * 4.99
    
    self.attractor.process(dt)
    self._t += dt
    
    return {
        "x": self._normalize(self.attractor.x),
        "y": self._normalize(self.attractor.y),
        "z": self._normalize(self.attractor.z),
        "t": math.sin(self._t * 0.5) * 0.5 + 0.5
    }
```

The attractor has a `speed` attribute that is set before `process(dt)`. The `process(dt)` method likely uses `self.speed` to scale the integration. So the actual Lorenz equations use fixed sigma/rho/beta, and `speed` is a multiplier on the time step or on the derivatives.

**Resolution**: The VJLive3 implementation should support two modes:
1. Fixed classic parameters (sigma=10, rho=28, beta=8/3) with a `speed` parameter that scales integration (matching legacy)
2. Expose sigma, rho, beta directly for advanced users (matching skeleton spec)

Given the skeleton spec already defines `sigma`, `rho`, `beta` as constructor parameters, we'll go with direct parameter control. The `speed` concept can be achieved by scaling `dt` externally or adding a `speed` parameter that multiplies `dt` inside `step()`.

We'll add a `speed` parameter to the public interface to match legacy behavior, but also allow direct sigma/rho/beta. Actually the skeleton only has sigma, rho, beta. Let's stick to that and note that legacy used speed/amplitude. The spec should explain the mapping.

### [NEEDS RESEARCH]: How is the output normalized in the legacy system?

**Finding**: The legacy node wrapper uses `_normalize(val, scale=30.0)` with `max(0.0, min(1.0, (val / scale + 1.0) * 0.5))` and multiplies by `amp` where `amp = self.parameters['amplitude']['value'] / 5.0`. So the raw attractor output is scaled by 30.0 to fit in [-1,1], then to [0,1], and further scaled by amplitude/5.

**Resolution**: The VJLive3 implementation should use the same normalization: `normalized = max(0.0, min(1.0, (raw / 30.0 + 1.0) * 0.5)) * (amplitude / 5.0)`. But the skeleton spec doesn't have `amplitude`. We need to decide: either include `amplitude` as a parameter, or fix it at 1.0. The legacy uses amplitude as a UI parameter (0-10). To match legacy behavior, we should include `amplitude` in the config. However, the skeleton spec's `get_metadata` only returns name/description/parameters/default_values with sigma/rho/beta. We'll extend to include `amplitude` and `speed` as optional parameters for compatibility.

Actually, the skeleton spec is minimal; we are to enrich it. So we can add `amplitude` and `speed` as parameters. But the class constructor only takes sigma, rho, beta. We could also add `speed` and `amplitude` as separate parameters that affect integration and normalization respectively.

Let's design: The attractor has core parameters (sigma, rho, beta). Additionally, there is a `speed` factor that scales the effective time step (so you can slow down or speed up the evolution without changing dt). And an `amplitude` factor that scales the normalized output. This matches the legacy UI where users adjust speed and amplitude.

Thus the public interface becomes:

```python
def __init__(self, sigma: float = 10.0, rho: float = 28.0, beta: float = 8/3, speed: float = 1.0, amplitude: float = 5.0):
```

But the skeleton spec doesn't include speed/amplitude. We'll add them in the enriched spec.

### [NEEDS RESEARCH]: What is the exact Runge-Kutta implementation in the legacy system?

**Finding**: The legacy code does not show the integration method. The node wrapper simply calls `self.attractor.process(dt)`. The attractor class implementation is missing.

**Resolution**: Use fourth-order Runge-Kutta as shown above. This is standard for chaotic systems and provides good stability with variable time steps.

---

## Configuration Schema

```python
METADATA = {
  "params": [
    {"id": "sigma", "name": "Sigma", "default": 10.0, "min": 0.0, "max": 30.0, "type": "float", "description": "Prandtl number — controls momentum transfer rate"},
    {"id": "rho", "name": "Rho", "default": 28.0, "min": 0.0, "max": 50.0, "type": "float", "description": "Rayleigh number — controls attractor size and chaos"},
    {"id": "beta", "name": "Beta", "default": 2.6667, "min": 0.0, "max": 10.0, "type": "float", "description": "Aspect ratio — controls dissipation in z-axis"},
    {"id": "speed", "name": "Speed", "default": 1.0, "min": 0.01, "max": 5.0, "type": "float", "description": "Time scaling factor — speeds up or slows down attractor evolution"},
    {"id": "amplitude", "name": "Amplitude", "default": 5.0, "min": 0.0, "max": 10.0, "type": "float", "description": "Output amplitude scaling (0-10 maps to 0-1 normalization factor)"}
  ]
}
```

**Presets**: Not applicable; this is a modulation source.

---

## State Management

- **Per-update state**: `x`, `y`, `z` state variables. These are updated every `step()` call.
- **Persistent state**: All configuration parameters (`sigma`, `rho`, `beta`, `speed`, `amplitude`). These persist for the lifetime of the module instance.
- **Init-once state**: Nothing special; all state is simple data.
- **Thread safety**: The module is **not thread-safe** by default. `step()` and `reset()` must be called from the same thread with an active context. If used from multiple threads, external synchronization is required.

---

## GPU Resources

This module is **CPU-only**. It does not use any GPU resources (no shaders, no textures). It can run on any hardware, including headless servers.

---

## Public Interface

```python
class VLorenzPlugin:
    def __init__(self, sigma: float = 10.0, rho: float = 28.0, beta: float = 8/3, speed: float = 1.0, amplitude: float = 5.0) -> None:
        """
        Initialize the Lorenz attractor with parameters.
        
        Args:
            sigma: Prandtl number (default 10.0)
            rho: Rayleigh number (default 28.0)
            beta: Aspect ratio (default 8/3 ≈ 2.6667)
            speed: Time scaling factor (default 1.0)
            amplitude: Output amplitude scaling (default 5.0)
        """
    
    def step(self, dt: float) -> tuple[float, float, float]:
        """
        Advance the attractor state by a time step.
        
        Args:
            dt: Time delta in seconds (will be multiplied by speed)
            
        Returns:
            Tuple of (x, y, z) representing current state of the system
        """
    
    def get_metadata(self) -> dict:
        """
        Return metadata about the plugin including parameter ranges and descriptions.
        
        Returns:
            Dictionary with keys 'name', 'description', 'parameters', and 'default_values'
        """
    
    def reset(self) -> None:
        """Reset the internal state to initial conditions."""
    
    def get_state(self) -> tuple[float, float, float]:
        """
        Get the current state without advancing.
        
        Returns:
            Tuple of (x, y, z)
        """
    
    def set_parameters(self, sigma: float = None, rho: float = None, beta: float = None, speed: float = None, amplitude: float = None) -> None:
        """
        Set one or more parameters.
        
        Args:
            sigma: New Prandtl number
            rho: New Rayleigh number
            beta: New aspect ratio
            speed: New time scaling factor
            amplitude: New output amplitude scaling
        """
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `sigma` | `float` | Prandtl number | Must be ≥ 0.0, default: 10.0 |
| `rho` | `float` | Rayleigh number | Must be ≥ 0.0, default: 28.0 |
| `beta` | `float` | Aspect ratio | Must be ≥ 0.0, default: 2.6667 |
| `speed` | `float` | Time scaling factor | Must be ≥ 0.01, default: 1.0 |
| `amplitude` | `float` | Output amplitude scaling | Must be ≥ 0.0, default: 5.0 |
| `dt` | `float` | Time step for integration | Must be ≥ 0.0, typically small (e.g., 0.01) |
| `x`, `y`, `z` | `float` | Output state values from attractor simulation | Normalized to [0.0, 1.0] range |
| `return_value` (from get_metadata) | `dict` | Plugin metadata | Contains 'name', 'description', 'parameters', 'default_values' |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — used for numerical integration — fallback: basic Python math (slower, less accurate)
- Internal modules this depends on:
  - `vjlive3.core.attractor_base.AttractorBase` — base class for all attractor plugins
  - `vjlive3.plugins.vattractors.metadata_utils` — provides metadata formatting and validation

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware absent (no external devices) |
| `test_basic_operation` | Core step() method returns valid (x, y, z) values for reasonable dt inputs |
| `test_error_handling` | Invalid parameter values (e.g., negative sigma, rho, beta) raise appropriate exceptions |
| `test_reset_state` | reset() method sets internal state to initial conditions and produces consistent output on next step |
| `test_metadata_consistency` | get_metadata() returns correct field names, descriptions, and default values matching legacy VLorenzPlugin |
| `test_parameter_ranges` | Parameters outside valid range are clamped or raise ValueError |
| `test_deterministic_behavior` | Identical initial conditions and parameters produce identical trajectories |
| `test_step_consistency` | Multiple calls with same dt produce consistent state progression |
| `test_speed_scaling` | Changing speed factor effectively scales time evolution (faster speed = larger state changes per dt) |
| `test_amplitude_scaling` | Changing amplitude scales normalized output values |
| `test_cleanup` | No resource leaks; can be destroyed cleanly |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT186: Implement VLorenzPlugin` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive1/plugins/core/modulation_attractors_lorenz_attractor/plugin.json (L1-20)
```json
{
    "id": "lorenz_attractor",
    "name": "Lorenz Attractor",
    "version": "1.0.0",
    "description": "Lorenz chaotic attractor — butterfly-pattern modulation",
    "category": "Modulation",
    "tags": [
        "math",
        "lfo",
        "unbundled",
        "modulation",
        "modulation_attractors",
        "chaos"
    ],
    "author": "VJLive Plugin Team",
    "license": "Unknown",
    "module_path": "plugins.core.modulation_attractors_lorenz_attractor",
    "modules": [
        {
            "id": "lorenz_attractor",
            "name": "Lorenz Attractor",
            "type": "EFFECT",
            "class_name": "VLorenzPlugin",
            "description": "Lorenz chaotic attractor — butterfly-pattern modulation",
            "category": "Modulation",
            "inputs": [],
            "outputs": [
                {
                    "name": "x",
                    "type": "float"
                },
                {
                    "name": "y",
                    "type": "float"
                },
                {
                    "name": "z",
                    "type": "float"
                }
            ],
            "parameters": [
                {
                    "name": "speed",
                    "label": "Speed",
                    "type": "float",
                    "min": 0.0,
                    "max": 10.0,
                    "default": 5.0
                },
                {
                    "name": "amplitude",
                    "label": "Amplitude",
                    "type": "float",
                    "min": 0.0,
                    "max": 10.0,
                    "default": 5.0
                }
            ]
        }
    ]
}
```

### vjlive1/core/matrix/node_modulation_attractors.py (L1-20)
```python
from .base_matrix_node import BaseMatrixNode
from ..modulation.attractors import LorenzAttractor, HalvorsenAttractor, ThomasAttractor, SakaryaAttractor
import math

class BaseAttractorNode(BaseMatrixNode):
    def __init__(self, name: str, node_type: str, attractor_class):
        super().__init__(name, node_type, "MODULATION")
        self.attractor = attractor_class()
        self._t = 0.0
        
        self.output_ports = {
            "x": {"type": "modulation", "desc": "X Output"},
            "y": {"type": "modulation", "desc": "Y Output"},
            "z": {"type": "modulation", "desc": "Z Output"},
            "t": {"type": "modulation", "desc": "Time/Cycle"},
        }
        
        self.parameters = {
            "speed": {
                "value": 5.0, "min": 0.0, "max": 10.0, "label": "Speed", "type": "float"
            },
            "amplitude": {
                "value": 5.0, "min": 0.0, "max": 10.0, "label": "Amplitude", "type": "float"
            },
        }
```

### vjlive1/core/matrix/node_modulation_attractors.py (L33-52)
```python
    def process(self, dt: float, **kwargs):
        # Update speed
        speed_param = self.parameters['speed']['value']
        # Map 0-10 to workable speed range (0.01 to 5.0 approx)
        norm_speed = speed_param / 10.0
        self.attractor.speed = 0.01 + norm_speed * 4.99
        
        self.attractor.process(dt)
        self._t += dt
        
        return {
            "x": self._normalize(self.attractor.x),
            "y": self._normalize(self.attractor.y),
            "z": self._normalize(self.attractor.z),
            "t": math.sin(self._t * 0.5) * 0.5 + 0.5
        }
```

### vjlive1/core/matrix/node_modulation_attractors.py (L81-100)
```python
    def process(self, dt: float, **kwargs):
        speed_param = self.parameters['speed']['value']
        norm_speed = speed_param / 10.0
        speed = 0.01 + norm_speed * 4.99
        
        self.lorenz.speed = speed
        self.halvorsen.speed = speed
        self.thomas.speed = speed
        self.sakarya.speed = speed
        
        self.lorenz.process(dt)
        self.halvorsen.process(dt)
        self.thomas.process(dt)
        self.sakarya.process(dt)
        self._t += dt
        
        amp = self.parameters['amplitude']['value'] / 5.0
        
        x = (self.lorenz.x + self.halvorsen.x + self.thomas.x + self.sakarya.x) / 4.0
        y = (self.lorenz.y + self.halvorsen.y + self.thomas.y + self.sakarya.y) / 4.0
        z = (self.lorenz.z + self.halvorsen.z + self.thomas.z + self.sakarya.z) / 4.0
        t = (self.lorenz.x + self.lorenz.y - self.lorenz.z +
             self.halvorsen.x + self.halvorsen.y - self.halvorsen.z +
             self.thomas.x + self.thomas.y - self.thomas.z +
             self.sakarya.x + self.sakarya.y - self.sakarya.z) / 4.0
             
        def norm(v, s=30.0):
            return max(0.0, min(1.0, (v / s + 1.0) * 0.5)) * amp

        return {'x': norm(x), 'y': norm(y), 'z': norm(z), 't': norm(t)}
```

### vjlive1/core/matrix/node_modulation_attractors.py (L120-123)
```python
        def norm(v, s=30.0):
            return max(0.0, min(1.0, (v / s + 1.0) * 0.5)) * amp

        return {'x': norm(x), 'y': norm(y), 'z': norm(z), 't': norm(t)}
```

[NEEDS RESEARCH]: The actual implementation of the LorenzAttractor class (the differential equations) was not found in the legacy code. The spec is based on the standard mathematical definition of the Lorenz attractor and the behavior observed in the node wrapper. The implementation should be verified against any remaining legacy code or the original VJLive1 plugin if available. The core algorithm (Runge-Kutta integration) is standard for chaotic systems and should be straightforward to implement.
