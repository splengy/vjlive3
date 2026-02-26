# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT191_vThomasPlugin.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT191 — vThomasPlugin

**What This Module Does**

The `VThomasPlugin` implements the Thomas chaotic attractor, a three-dimensional dynamical system that produces cyclic, grid-like patterns. This attractor is used in VJLive3 for generating organic, evolving visual modulation patterns that respond to audio and user parameters in real-time.

The Thomas attractor is defined by the following system of differential equations:

```
dx/dt = sin(y) - b*x
dy/dt = sin(z) - b*y
dz/dt = sin(x) - b*z
```

Where `b` is a positive control parameter. The system exhibits chaotic behavior for typical values of `b` in the range 0.1-0.3, producing a swirling, toroidal pattern that resembles a twisted grid.

The module provides:
- Real-time simulation of the attractor's state (x, y, z)
- Parameter control for `b` (the nonlinearity/damping parameter)
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
- Does not implement attractor blending with other systems (e.g., Lorenz, Halvorsen)
- Does not provide GUI controls (UI is handled by ProgramPage)

---

## Detailed Behavior and Parameter Interactions

### Core Algorithm

The Thomas attractor is integrated using a fourth-order Runge-Kutta method for numerical stability. The state variables (x, y, z) are updated each frame based on the differential equations:

```python
def step(self, dt):
    # Runge-Kutta 4th order integration
    k1x = math.sin(self.y) - self.b * self.x
    k1y = math.sin(self.z) - self.b * self.y
    k1z = math.sin(self.x) - self.b * self.z
    
    k2x = math.sin(self.y + 0.5*dt*k1y) - self.b * (self.x + 0.5*dt*k1x)
    k2y = math.sin(self.z + 0.5*dt*k1z) - self.b * (self.y + 0.5*dt*k1y)
    k2z = math.sin(self.x + 0.5*dt*k1x) - self.b * (self.z + 0.5*dt*k1z)
    
    k3x = math.sin(self.y + 0.5*dt*k2y) - self.b * (self.x + 0.5*dt*k2x)
    k3y = math.sin(self.z + 0.5*dt*k2z) - self.b * (self.y + 0.5*dt*k2y)
    k3z = math.sin(self.x + 0.5*dt*k2x) - self.b * (self.z + 0.5*dt*k2z)
    
    k4x = math.sin(self.y + dt*k3y) - self.b * (self.x + dt*k3x)
    k4y = math.sin(self.z + dt*k3z) - self.b * (self.y + dt*k3y)
    k4z = math.sin(self.x + dt*k3x) - self.b * (self.z + dt*k3z)
    
    self.x += (dt/6) * (k1x + 2*k2x + 2*k3x + k4x)
    self.y += (dt/6) * (k1y + 2*k2y + 2*k3y + k4y)
    self.z += (dt/6) * (k1z + 2*k2z + 2*k3z + k4z)
    
    return self.x, self.y, self.z
```

### Parameter Roles

The Thomas attractor has a single primary parameter:

- **`b` (Damping/Nonlinearity)**: Controls the damping factor and the strength of the sinusoidal coupling. Higher values increase damping and can suppress chaos; lower values allow more complex behavior. Classic chaotic range: 0.1-0.3. Default: 0.2 (typical). Range: 0.0-1.0.

In the legacy system, this was mapped to `speed` and `amplitude` UI controls (0-10 range). The VJLive3 implementation uses direct `b` parameter for clarity, but also includes `speed` and `amplitude` for compatibility with the node wrapper.

### State Initialization

The attractor starts with initial conditions:
- `x = 0.1`
- `y = 0.0`
- `z = 0.0`

These values are near the attractor's basin of attraction. The system is deterministic, so identical initial conditions produce identical trajectories.

### Output Normalization

The raw attractor output (x, y, z) can range from approximately -2 to +2. For use in VJLive3's modulation system, these values are normalized to a 0-1 range:

```python
def _normalize(self, val: float, scale: float = 2.0) -> float:
    """Normalize attractor output to 0-1 range."""
    amp = self.amplitude / 5.0  # if using amplitude scaling
    return max(0.0, min(1.0, (val / scale + 1.0) * 0.5)) * amp
```

The legacy node wrapper uses `scale=30.0` for all attractors, but the Thomas attractor's natural range is smaller (~2). Using scale=30 would compress the signal. The actual legacy code likely uses the same normalization across all attractors for consistency, so we'll follow that: `scale=30.0`. This means the raw output is effectively multiplied by a gain to match the expected range.

### Reset Behavior

The `reset()` method sets the state back to initial conditions:
- `x = 0.1`
- `y = 0.0`
- `z = 0.0`

This allows for deterministic behavior when restarting a performance or changing parameters.

---

## Integration

### VJLive3 Modulation Ecosystem

The `VThomasPlugin` is a **modulation source** that integrates into the VJLive3 plugin ecosystem as follows:

```
[User Parameters] → [VThomasPlugin] → [Modulation Output] → [Other Plugins]
```

**Position in pipeline**:
- The plugin is instantiated as a modulation source in the ProgramPage UI
- It receives `dt` (delta time) from the VJLive3 time manager
- It outputs normalized (x, y, z) values to other plugins via the `step(dt)` method
- Other plugins can query these values to modulate parameters like color, position, scale, or opacity

**Typical usage**:

```python
# Initialize
thomas = VThomasPlugin(b=0.2, speed=1.0, amplitude=5.0)

# In the main loop (called once per frame)
x, y, z = thomas.step(delta_time)

# Use output to modulate other effects
effect.color = (x, y, z)  # Color modulation
effect.scale = y * 2.0    # Scale modulation
effect.position = (x, y, 0)  # Position modulation
```

**Metadata Integration**:

The `get_metadata()` method returns a dictionary that the ProgramPage UI uses to generate controls:

```python
{
    "name": "Thomas Attractor",
    "description": "Thomas chaotic attractor — grid-like modulation",
    "parameters": [
        {"id": "b", "name": "Damping", "min": 0.0, "max": 1.0, "default": 0.2},
        {"id": "speed", "name": "Speed", "min": 0.01, "max": 5.0, "default": 1.0},
        {"id": "amplitude", "name": "Amplitude", "min": 0.0, "max": 10.0, "default": 5.0}
    ],
    "default_values": {"b": 0.2, "speed": 1.0, "amplitude": 5.0}
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
- 21 multiplications
- 15 additions/subtractions
- 6 sine operations (math.sin)
- 6 comparisons for normalization

On any modern CPU, this is negligible (< 0.02 ms per call due to sin). The module can be updated every frame (60-120 Hz) without impact.

### Memory Usage

- **Minimal**: Stores 3 floats for state (x, y, z) and 3 floats for parameters (b, speed, amplitude)
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
| `test_error_handling` | Invalid parameter values (e.g., negative b) raise appropriate exceptions |
| `test_reset_state` | reset() method sets internal state to initial conditions and produces consistent output on next step |
| `test_metadata_consistency` | get_metadata() returns correct field names, descriptions, and default values matching legacy VThomasPlugin |
| `test_parameter_ranges` | Parameters outside valid range are clamped or raise ValueError |
| `test_deterministic_behavior` | Identical initial conditions and parameters produce identical trajectories |
| `test_step_consistency` | Multiple calls with same dt produce consistent state progression |
| `test_speed_scaling` | Changing speed factor effectively scales time evolution |
| `test_amplitude_scaling` | Changing amplitude scales normalized output values |
| `test_cleanup` | No resource leaks; can be destroyed cleanly |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

### [NEEDS RESEARCH]: What is the exact parameter `param` in the skeleton spec? Is it `b` or something else?

**Finding**: The skeleton spec uses `param: float = 1.0`. The Thomas attractor typically has a single parameter `b` (damping). The legacy plugin uses `speed` and `amplitude` as UI controls, not direct attractor parameters. The actual attractor class likely has a fixed `b` (maybe 0.2) and the `speed` attribute controls integration speed.

**Resolution**: The VJLive3 implementation should expose `b` as the primary attractor parameter, plus `speed` and `amplitude` for compatibility with the node wrapper. The skeleton's `param` is ambiguous; we'll interpret it as `b`. We'll add `speed` and `amplitude` as additional parameters.

### [NEEDS RESEARCH]: What is the natural range of Thomas attractor output (x, y, z)?

**Finding**: The Thomas attractor typically produces values in the range [-1.5, 1.5] for the classic parameters. However, the legacy normalization uses `scale=30.0`, which suggests they expected a larger range or they apply a gain before normalization. The node wrapper's `_normalize` uses `scale=30.0` and `amp = amplitude/5.0`.

**Resolution**: Use the same normalization as the other attractors: `normalized = max(0.0, min(1.0, (raw / 30.0 + 1.0) * 0.5)) * (amplitude / 5.0)`. This ensures consistency across the vattractors suite.

### [NEEDS RESEARCH]: How is the `speed` parameter used in the legacy attractor class?

**Finding**: The node wrapper sets `self.attractor.speed = 0.01 + norm_speed * 4.99` before calling `self.attractor.process(dt)`. This suggests the attractor's `process` method uses `self.speed` to scale the time derivative or to multiply `dt`.

**Resolution**: In the `step(dt)` method, we can scale the effective time step: `effective_dt = dt * self.speed`. Or we can multiply the derivatives by `speed`. We'll choose to scale `dt` inside `step`: `dt_eff = dt * self.speed`. This matches the legacy behavior where `speed` is a multiplier on time evolution.

---

## Configuration Schema

```python
METADATA = {
  "params": [
    {"id": "b", "name": "Damping", "default": 0.2, "min": 0.0, "max": 1.0, "type": "float", "description": "Damping/nonlinearity parameter for Thomas attractor"},
    {"id": "speed", "name": "Speed", "default": 1.0, "min": 0.01, "max": 5.0, "type": "float", "description": "Time scaling factor — speeds up or slows down attractor evolution"},
    {"id": "amplitude", "name": "Amplitude", "default": 5.0, "min": 0.0, "max": 10.0, "type": "float", "description": "Output amplitude scaling (0-10 maps to 0-1 normalization factor)"}
  ]
}
```

**Presets**: Not applicable; this is a modulation source.

---

## State Management

- **Per-update state**: `x`, `y`, `z` state variables. These are updated every `step()` call.
- **Persistent state**: All configuration parameters (`b`, `speed`, `amplitude`). These persist for the lifetime of the module instance.
- **Init-once state**: Nothing special; all state is simple data.
- **Thread safety**: The module is **not thread-safe** by default. `step()` and `reset()` must be called from the same thread with an active context. If used from multiple threads, external synchronization is required.

---

## GPU Resources

This module is **CPU-only**. It does not use any GPU resources (no shaders, no textures). It can run on any hardware, including headless servers.

---

## Public Interface

```python
class VThomasPlugin:
    def __init__(self, b: float = 0.2, speed: float = 1.0, amplitude: float = 5.0) -> None:
        """
        Initialize the Thomas attractor with parameters.
        
        Args:
            b: Damping/nonlinearity parameter (default 0.2)
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
    
    def set_parameters(self, b: float = None, speed: float = None, amplitude: float = None) -> None:
        """
        Set one or more parameters.
        
        Args:
            b: New damping parameter
            speed: New time scaling factor
            amplitude: New output amplitude scaling
        """
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `b` | `float` | Damping/nonlinearity parameter | Must be ≥ 0.0, default: 0.2 |
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
| `test_error_handling` | Invalid parameter values (e.g., negative b) raise appropriate exceptions |
| `test_reset_state` | reset() method sets internal state to initial conditions and produces consistent output on next step |
| `test_metadata_consistency` | get_metadata() returns correct field names, descriptions, and default values matching legacy VThomasPlugin |
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
- [ ] Git commit with `[Phase-X] P3-EXT191: Implement VThomasPlugin` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive1/plugins/core/modulation_attractors_thomas_attractor/plugin.json (L1-20)
```json
{
    "id": "thomas_attractor",
    "name": "Thomas Attractor",
    "version": "1.0.0",
    "description": "Thomas chaotic attractor — grid-like modulation",
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
    "module_path": "plugins.core.modulation_attractors_thomas_attractor",
    "modules": [
        {
            "id": "thomas_attractor",
            "name": "Thomas Attractor",
            "type": "EFFECT",
            "class_name": "VThomasPlugin",
            "description": "Thomas chaotic attractor — grid-like modulation",
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

[NEEDS RESEARCH]: The actual implementation of the ThomasAttractor class (the differential equations) was not found in the legacy code. The spec is based on the standard mathematical definition of the Thomas attractor and the behavior observed in the node wrapper. The implementation should be verified against any remaining legacy code or the original VJLive1 plugin if available. The core algorithm (Runge-Kutta integration) is standard for chaotic systems and should be straightforward to implement.
