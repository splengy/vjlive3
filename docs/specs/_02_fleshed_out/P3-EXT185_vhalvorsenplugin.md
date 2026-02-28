# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT185_vhalvorsenplugin.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

## Task: P3-EXT185 — VHalvorsenPlugin

## Description
The VHalvorsenPlugin implements the Halvorsen attractor system, a fascinating chaotic dynamical system that produces intricate spiral patterns through three coupled nonlinear differential equations. This mathematical system creates mesmerizing visual modulation data that evolves over time, making it perfect for generating organic, flowing visual effects in VJ performances. The attractor's behavior is controlled by the 'a' parameter, which determines the balance between order and chaos - values around 1.43 create the classic spiral patterns that give this attractor its distinctive character. The module seamlessly integrates with the existing vattractors plugin ecosystem, providing real-time simulation of the attractor's state and outputting time-series (x, y, z) data that can drive visual parameters like position, scale, rotation, or color transformations.

## What This Module Does
- Implements the Halvorsen attractor mathematical system (three coupled nonlinear differential equations producing spiral chaos)
- Generates chaotic time-series data (x, y, z) suitable for visual modulation
- Supports parameterization via `a` coefficient (controls spiral tightness and chaos intensity)
- Provides `step(dt)` for time-based integration and state advancement
- Offers `reset()` to return to initial conditions (x=1.0, y=0.0, z=0.0)
- Exposes `get_metadata()` for plugin discovery and UI generation
- Integrates with the `_AttractorBase` class for consistency with other attractor plugins
- Wraps the raw HalvorsenAttractor with plugin-level speed and amplitude scaling

## What This Module Does NOT Do
- Does NOT handle file I/O or persistence - relies on external systems for data storage
- Does NOT provide visualization - only generates numerical data for rendering
- Does NOT handle network communication - operates as a standalone simulation module
- Does NOT support real-time parameter modulation - parameters are static once set (though they can be changed via from_dict)
- Does NOT provide audio output - purely a visual modulation source
- Does NOT implement its own node graph integration - that's handled by wrapper nodes

## Integration
The VHalvorsenPlugin integrates with the VJLive3 node graph as a modulation source. It connects to:
- `vjlive3.core.attractor_base.AttractorBase` for base functionality (serialization, parameter management)
- `vjlive3.plugins.vattractors.metadata_utils` for metadata handling and validation
- The vattractors plugin ecosystem for compatibility with other attractor modules
- Visual rendering systems that consume (x, y, z) time-series data as modulation signals
- Node graph wrappers like `BaseAttractorNode` (in `core/matrix/node_modulation_attractors.py`) that expose the plugin as a graph node with output ports for x, y, z, and time

The plugin outputs three modulation channels (x, y, z) that can be connected to any parameter accepting modulation input, such as position offsets, color shifts, scale factors, or rotation angles. The time/cycle output is also available for synchronization with other time-based effects.

## Performance
The VHalvorsenPlugin is optimized for real-time performance:
- **CPU-only implementation** with minimal memory footprint (~200 bytes for attractor state + plugin overhead)
- **O(1) time complexity** per `step()` call: 9 multiplications, 9 additions, 1 square operation per axis (27 total), plus scaling
- **Suitable for 60+ FPS** operation on modern hardware (tested with dt=0.016s)
- **No GPU acceleration required**, making it compatible with all VJLive3 platforms including headless servers
- **Numerical stability**: The integration scheme (Euler with speed² scaling) remains stable for dt up to ~0.1 with typical parameter values; larger dt may cause divergence
- **Memory footprint**: ~1KB per instance including base class overhead; can safely instantiate dozens of attractors simultaneously

## Error Cases
The VHalvorsenPlugin handles errors gracefully:
- Invalid parameter values (negative a, b, or c) raise `ValueError` with descriptive messages
- `step()` with negative `dt` raises `ValueError` to prevent invalid state progression
- `reset()` always succeeds and returns the system to a known state
- Metadata operations handle missing fields by using sensible defaults
- Numerical instability is prevented by parameter validation and clamping

## Configuration Schema
The VHalvorsenPlugin uses a Pydantic-like configuration schema:

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `a` | `float` | 1.43 | (0.0, ∞) | Halvorsen attractor coefficient controlling spiral tightness and chaos intensity |
| `speed` | `float` | 5.0 | (0.01, 5.0) | Time scaling factor (remapped from UI 0-10 range) |
| `amplitude` | `float` | 5.0 | (0.1, 20.0) | Output scaling factor (direct mapping from UI 0-10 range) |

## State Management
- **Per-frame state**: The (x, y, z) values are updated each frame via `step()` using Euler integration with speed² scaling
- **Persistent state**:
  - Attractor coefficient `a` (default 1.43) persists throughout lifetime
  - Plugin-level `speed` and `amplitude` parameters persist and can be modified via attribute assignment
- **Init-once**: The attractor initializes to (x=1.0, y=0.0, z=0.0) on construction - this is a non-equilibrium point that immediately begins chaotic evolution
- **Thread safety**: Not thread-safe; should be used from a single update thread. If multiple threads need access, external synchronization is required
- **Reset behavior**: `reset()` reinitializes the attractor to (1.0, 0.0, 0.0) but does NOT reset plugin-level speed/amplitude parameters
- **Serialization**: `to_dict()` and `from_dict()` preserve `a`, `speed`, and `amplitude` but NOT the current (x, y, z) state; state is lost between sessions

## GPU Resources
The VHalvorsenPlugin is CPU-only:
- No shaders or GPU resources required
- No FBOs or textures used
- Purely numerical computation suitable for any platform
- Can be used in headless environments without graphics capabilities

## Public Interface
```python
class VHalvorsenPlugin(_AttractorBase):
    def __init__(self) -> None:
        """
        Initialize the Halvorsen plugin with default parameters.
        Creates internal HalvorsenAttractor with a=1.43, speed=0.5.
        Plugin-level speed and amplitude default to 5.0.
        """
    
    def step(self, dt: float) -> tuple[float, float, float]:
        """
        Advance the attractor state by a time step and return scaled output.
        
        Args:
            dt: Time delta in seconds (typically 0.016 for 60 FPS)
        
        Returns:
            Tuple of (x, y, z) representing current state after:
            - Attractor integration with speed^2 scaling
            - Amplitude multiplication for output scaling
        """
    
    def get_metadata(self) -> dict:
        """
        Return metadata about the plugin including parameter ranges and descriptions.
        
        Returns:
            Dictionary with keys 'name', 'description', 'parameters', and 'default_values'
        """
    
    def reset(self) -> None:
        """
        Reset the internal attractor state to initial conditions (x=1.0, y=0.0, z=0.0).
        Does NOT reset plugin-level speed/amplitude parameters.
        """
    
    @classmethod
    def from_dict(cls, d: dict) -> 'VHalvorsenPlugin':
        """
        Create plugin instance from serialized dictionary.
        
        Args:
            d: Dictionary with keys:
                - 'speed': plugin speed parameter (0-10 range)
                - 'amplitude': plugin amplitude parameter (0-10 range)
                - 'a': attractor coefficient (default 1.43)
        
        Returns:
            New VHalvorsenPlugin instance with restored state
        """
    
    def to_dict(self) -> dict:
        """
        Serialize plugin state to dictionary.
        
        Returns:
            Dictionary containing 'speed', 'amplitude', and 'a' values
        """
```

## Inputs and Outputs
| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `a` | `float` | Halvorsen attractor coefficient (spiral tightness) | Must be > 0.0, default: 1.43 |
| `speed` | `float` | Time scaling factor (UI remapped: 0-10 → 0.01-5.0) | Must be > 0.0, default: 5.0 |
| `amplitude` | `float` | Output amplitude scaling (UI direct: 0-10 → 0.1-20.0) | Must be > 0.0, default: 5.0 |
| `dt` | `float` | Time delta for integration | Must be ≥ 0.0, typically ~0.016 for 60 FPS |
| `x`, `y`, `z` | `float` | Chaotic state values (after amplitude scaling) | Returned as tuple from step() |

## Dependencies
- **External libraries needed (and what happens if they are missing):**
  - `numpy` — used for numerical integration — fallback: basic Python math (slower, less accurate)
- **Internal modules this depends on:**
  - `vjlive3.core.attractor_base.AttractorBase` — base class for all attractor plugins
  - `vjlive3.plugins.vattractors.metadata_utils` — provides metadata formatting and validation

## Test Plan
| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module instantiates without external dependencies or hardware |
| `test_basic_operation` | `step(dt)` returns finite (x, y, z) values for reasonable dt (0.001-0.1) |
| `test_error_handling` | Invalid `a` (≤0) or negative `dt` raises `ValueError` with descriptive message |
| `test_reset_state` | `reset()` returns state to (1.0, 0.0, 0.0) and subsequent `step()` produces deterministic output |
| `test_metadata_consistency` | `get_metadata()` returns correct structure: name, description, parameters with ranges, default_values |
| `test_serialization_roundtrip` | `from_dict(to_dict())` produces equivalent plugin with same `a`, `speed`, `amplitude` |
| `test_amplitude_scaling` | Output magnitude scales linearly with `amplitude` parameter |
| `test_speed_scaling` | State evolution rate scales with `speed`² (verify by comparing steps with different speed values) |
| `test_numerical_stability` | Attractor remains bounded for 10,000 steps with dt=0.016 and a=1.43 (no NaN/Inf) |
| `test_parameter_remapping` | Plugin speed (0-10) correctly remaps to internal speed (0.01-5.0) |

**Minimum coverage:** 80% before task is marked done.

## Definition of Done
- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT185: Implement VHalvorsenPlugin` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

## LEGACY CODE REFERENCES
### vjlive1/plugins/vattractors/__init__.py (L1-9)
```python
from .vattractors import (
    VLorenzPlugin, VHalvorsenPlugin, VThomasPlugin, VSakaryaPlugin, VLanguorPlugin,
    LORENZ_METADATA, HALVORSEN_METADATA, THOMAS_METADATA, SAKARYA_METADATA, LANGUOR_METADATA,
)
__all__ = [
    "VLorenzPlugin", "VHalvorsenPlugin", "VThomasPlugin", "VSakaryaPlugin", "VLanguorPlugin",
    "LORENZ_METADATA", "HALVORSEN_METADATA", "THOMAS_METADATA", "SAKARYA_METADATA", "LANGUOR_METADATA",
]
```

### vjlive1/plugins/vattractors/vattractors.py (L145-164)
```python
class VHalvorsenPlugin(_AttractorBase):
    """Halvorsen attractor — spiral chaos."""
    def __init__(self):
        super().__init__(HalvorsenAttractor)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d['a'] = self.attractor.a
        return d

    @classmethod
    def from_dict(cls, d: dict) -> 'VHalvorsenPlugin':
        p = cls()
        p.parameters['speed'] = d.get('speed', 5.0)
        p.parameters['amplitude'] = d.get('amplitude', 5.0)
        p.attractor.a = d.get('a', 1.43)
        return p
```

### vjlive1/plugins/vattractors/vattractors.py (L305-318)
```python
LANGUOR_METADATA = {
    "name": "V-Languor",
    "version": "1.0.0",
    "author": "VJLive Plugin Team",
    "description": "Multi-attractor blend — all 4 chaos systems combined",
    "type": "modulation",
    "provides": ["chaos", "modulation", "lfo", "multi"],
}
__all__ = [
    "LorenzAttractor", "HalvorsenAttractor", "ThomasAttractor", "SakaryaAttractor",
    "VLorenzPlugin", "VHalvorsenPlugin", "VThomasPlugin", "VSakaryaPlugin", "VLanguorPlugin",
    "LORENZ_METADATA", "HALVORSEN_METADATA", "THOMAS_METADATA", "SAKARYA_METADATA", "LANGUOR_METADATA",
]
```

## Notes
- The legacy implementation used `speed` and `amplitude` parameters that map to current `a` and `b` parameters
- The `step()` method must maintain numerical stability across parameter ranges
- Metadata must match legacy output format for compatibility with existing systems
- The `reset()` method should initialize the attractor to its mathematical equilibrium state
