# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT207_silver_visions.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT207 — silver_visions (SilverVisionsEffect)

**What This Module Does**

The `SilverVisionsEffect` is a high-fidelity 3D particle system with a chrome/metallic aesthetic, built on top of `AdvancedParticle3DSystem`. It generates dense, responsive particles using a spherical emitter and turbulence forces, rendered as billboards with color interpolation from bright silver/white to cyan fade-out. The system is designed to be highly audio-reactive, pulsing with the beat and responding to frequency bands. It provides three macro-control parameters ("turbulence", "density", "flow_speed") that map to multiple underlying system settings for easy performance control.

The effect is ideal for creating shimmering, metallic particle fields that dance with music, suitable for VJ performances with electronic or ambient music.

**What This Module Does NOT Do**

- Does NOT implement its own particle physics (inherits from AdvancedParticle3DSystem)
- Does NOT support custom color schemes (fixed silver/cyan palette)
- Does NOT provide per-emitter or per-force control (uses a single emitter and noise force)
- Does NOT implement advanced rendering like mesh particles or lines (billboards only)
- Does NOT handle audio analysis itself (relies on external audio features)
- Does NOT support multiple render targets or post-processing (outputs to screen/FBO)

---

## Detailed Behavior and Parameter Interactions

### Inheritance Architecture

`SilverVisionsEffect` extends `AdvancedParticle3DSystem` and overrides its configuration to provide a curated aesthetic. The base class provides:
- Particle physics (gravity, drag, turbulence, attractor, vortex)
- Emission system (emitter parameters)
- Rendering pipeline (OpenGL with VBOs, shaders)
- Audio reactivity infrastructure

The subclass configures a specific preset and provides simplified macro-parameter mapping.

### Default Configuration

Upon initialization, `SilverVisionsEffect` sets up:

1. **Single Sphere Emitter**:
   - Type: Sphere (particles spawn within a spherical volume)
   - Emission rate: 500 particles per frame (high density)
   - Particle lifetime: 4.0 seconds (average)
   - Initial speed: 0.5 units/sec
   - Speed variation: ±20% randomness
   - Size range: 0.5 to 2.5 units (random per particle)
   - Position: (0, 0, 0) — center of scene
   - Color gradient: from silver/white `(0.9, 0.9, 1.0, 1.0)` to cyan fade-out `(0.0, 0.8, 0.9, 0.0)`
   - Emit on beat: When `audio_beat` signal is high, extra particles are emitted (pulse effect)

2. **Single Noise Force (Turbulence)**:
   - Type: Noise (procedural 3D noise field)
   - Strength: 0.5 (moderate chaotic motion)
   - Noise scale: 2.0 (frequency of noise variations)
   - Noise speed: 0.5 (how fast noise evolves over time)

3. **Rendering**:
   - Mode: `BILLBOARDS` (particles always face camera)
   - Point size: 3.0 pixels (base size, perspective-scaled in shader)
   - Blend mode: Additive (for glowing effect)
   - Texture: Optional particle sprite (if provided)

4. **Audio Reactivity**:
   - Audio sensitivity: 2.0 (higher than default, making particles more responsive)
   - Beat pulse: Emitter emits extra particles when beat is detected
   - Shader uniforms: `audio_bass`, `audio_mid`, `audio_treble`, `audio_beat` affect particle size and vertical displacement

### Macro-Parameter Mapping

The `set_parameter(name, value)` method maps user-friendly controls to internal system parameters:

| Macro Name | Mapping | Value Range (input) | Internal Effect |
|------------|---------|---------------------|-----------------|
| `turbulence` | `forces[0].strength = value * 2.0` | 0.0-1.0 → 0.0-2.0 | Increases noise force strength, making particles jitter more |
| `density` | `emitters[0].rate = value * 200.0` | 0.0-1.0 → 0-200 particles/frame | Controls emission rate (density of particle field) |
| `flow_speed` | `forces[0].noise_speed = value`<br>`emitters[0].initial_speed = value * 0.5` | 0.0-1.0 → 0.0-1.0 (noise)<br>0.0-0.5 (speed) | Speeds up noise evolution and particle initial velocity |

The `get_parameter(name)` method returns the normalized macro value (0.0-1.0) by reversing the mapping.

### Audio Reactivity Details

The system integrates with an audio analyzer (external) that provides four features per frame:
- `bass` (0.0-1.0): Low-frequency energy
- `mid` (0.0-1.0): Mid-frequency energy
- `treble` (0.0-1.0): High-frequency energy
- `beat` (0.0 or 1.0): Beat detection flag

These values are used in two ways:

1. **CPU-side**: The `emit_on_beat` flag on the emitter causes extra emission when `beat == 1`. The number of extra particles could be a multiplier on `rate`.

2. **GPU-side (vertex shader)**:
   - Particle Y position gets displaced: `pos.y += audio_bass * 0.1 * sin(pos.x * 5.0 + time)`
   - Particle size gets scaled: `size = props.y * (1.0 + audio_mid * 0.5)`
   - These create a throbbing, vibrating effect synchronized to music.

### Rendering Pipeline

The system uses GPU instancing via OpenGL:
- CPU updates particle positions, velocities, colors, sizes in NumPy arrays.
- Each frame, the active particle data is uploaded to VBOs (position, color, props).
- Vertex shader transforms particles with MVP matrix, applies audio displacement, computes point size.
- Fragment shader renders either circular points or textured sprites (if `use_texture=True`).
- Additive blending creates a glowing, metallic look.

The billboard rendering ensures particles always face the camera, giving a 2D sprite-like appearance in 3D space.

---

## Integration

### VJLive3 Pipeline Integration

`SilverVisionsEffect` is a **self-contained generator** that renders directly to the current framebuffer. It does not take input textures. It should be added to the effects chain as a source that other effects can composite over.

**Typical usage**:

```python
# Initialize
silver = SilverVisionsEffect()
silver.set_audio_features(bass=0.5, mid=0.3, treble=0.2, beat=1.0)  # Each frame
silver.update(delta_time)
silver.render()  # Draws to screen or current FBO
```

The effect requires an active OpenGL context with a valid camera and projection matrix set via the base class methods.

### Audio Integration

The effect expects audio features to be provided each frame via `set_audio_features(bass, mid, treble, beat)`. These values should come from an `AudioAnalyzer` instance that processes the audio input in real-time. The effect does not analyze audio itself.

---

## Performance

### Computational Cost

The system is **mixed CPU/GPU**, inheriting performance characteristics from `AdvancedParticle3DSystem`:

- **CPU**: Physics update for up to 10,000 particles. With default emission (500/frame) and lifetime (4s), active count ~2000. Each particle update: ~30 FLOPs. Total ~60,000 FLOPs/frame, negligible.
- **GPU**: Vertex shader for ~2000 particles, plus fragment shader for point sprites. Memory bandwidth: uploading ~2000 × 11 floats ≈ 88 KB per frame. Very light.

**Expected performance**: 60+ fps easily on integrated graphics; 2000 particles is conservative; can go up to 10,000 with care.

### Memory Usage

- **CPU**: NumPy arrays for max_particles (10,000) × (3+3+1+4+4) floats ≈ 150 KB
- **GPU**: VBOs ≈ 150 KB, shaders < 50 KB, optional texture ~16 KB
- **Total**: < 1 MB

### Optimization Strategies

- Use `glBufferSubData` with `GL_DYNAMIC_DRAW` for VBO updates.
- Consider using `glMapBuffer` for async updates if needed.
- Reduce `max_particles` on low-end hardware.

### Platform-Specific Considerations

- **Desktop**: No issues; OpenGL 3.3+ required.
- **Embedded (Raspberry Pi)**: May need to lower `max_particles` and `emit_rate`.
- **Mobile**: Use lower particle counts and avoid heavy turbulence.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect initializes without crashing if OpenGL context missing; raises clear error |
| `test_silver_presets_applied` | After init, emitter rate=500, noise strength=0.5, render mode=BILLBOARDS, colors set correctly |
| `test_macro_parameter_turbulence` | Setting `turbulence` from 0.0-1.0 scales `forces[0].strength` linearly 0.0-2.0 |
| `test_macro_parameter_density` | Setting `density` from 0.0-1.0 scales `emitters[0].rate` linearly 0-200 |
| `test_macro_parameter_flow_speed` | Setting `flow_speed` sets `forces[0].noise_speed` directly and `emitters[0].initial_speed` to value*0.5 |
| `test_get_parameter_returns_normalized` | `get_parameter("turbulence")` returns `forces[0].strength / 2.0` etc. |
| `test_audio_reactivity_emission` | When `audio_beat` is high, extra particles are emitted (check active_count increase) |
| `test_audio_reactivity_shader` | Audio uniforms affect vertex shader (size increase with audio_mid, Y displacement with audio_bass) |
| `test_color_gradient` | Particles spawn with colors interpolating from start to end over lifetime |
| `test_billboard_rendering` | Particles are rendered as screen-facing quads (check vertex shader output) |
| `test_inherited_functionality` | Base class methods (set_gravity, set_drag, etc.) still work |
| `test_cleanup` | All OpenGL resources released on stop() |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

### [NEEDS RESEARCH]: The base class `AdvancedParticle3DSystem` uses a simple emitter model (emit_rate per frame). The legacy `SilverVisionsEffect` references `EmitterType.SPHERE`, `emitter.rate`, `emitter.lifetime`, `initial_speed`, `speed_variation`, `size_range`, `color_range`, `emit_on_beat`. This suggests the base class has a more sophisticated emitter object system. The skeleton spec for AdvancedParticle3DSystem did not include these emitter objects; it had flat parameters. We need to reconcile.

**Finding**: The legacy `SilverVisionsEffect` imports `EmitterType, ForceType, RenderMode` from `.particles_3d`. The base class likely has:
- `self.emitters` list
- `self.forces` list
- `add_emitter(type)` method
- `add_force(type)` method
- Each emitter has properties: `rate`, `lifetime`, `initial_speed`, `speed_variation`, `size_range`, `color_range`, `position`, `emit_on_beat`
- Each force has properties: `strength`, `noise_scale`, `noise_speed` (for NOISE type)

The earlier skeleton spec for AdvancedParticle3DSystem had flat parameters like `emit_rate`, `particle_life_min/max`, `color_start/end`. That's a simpler design. The SilverVisions code expects a more modular emitter/force architecture.

**Resolution**: The VJLive3 `AdvancedParticle3DSystem` should be implemented with an emitter/force object system to support SilverVisions and similar subclasses. The enriched spec for P3-EXT206 should be updated to include this object-oriented structure. However, since we're only enriching SilverVisions here, we'll document that SilverVisions relies on the base class providing:
- `self.emitters: List[Emitter]`
- `self.forces: List[Force]`
- `add_emitter(EmitterType) -> index`
- `add_force(ForceType) -> index`
- Emitter attributes: `rate` (float, particles/sec or per frame), `lifetime` (float), `initial_speed` (float), `speed_variation` (float), `size_range` (tuple min,max), `color_range` (tuple start_color, end_color), `position` (np.array), `emit_on_beat` (bool)
- Force attributes: `strength` (float), `noise_scale` (float), `noise_speed` (float) for NOISE type

We'll note this dependency in the spec.

### [NEEDS RESEARCH]: How does `emit_on_beat` work? Does it multiply rate or add extra particles?

**Finding**: Not detailed. Likely, during `update(dt)`, if `audio_beat` is true, the emitter spawns additional particles (maybe `rate * beat_multiplier`). The base class should handle this.

**Resolution**: In the emitter update, if `emit_on_beat` and `audio_beat == 1.0`, spawn an extra `rate * beat_multiplier` particles (or a fixed burst). We'll define that the base class handles it; SilverVisions sets `emit_on_beat=True` and relies on base.

### [NEEDS RESEARCH]: What is `RenderMode.BILLBOARDS`? How does it differ from POINTS?

**Finding**: The legacy defines `RenderMode` enum with POINTS, TEXTURED, LINES, MESH. BILLBOARDS is not in the snippet but is used. Possibly BILLBOARDS is a mode where particles are quads that always face the camera, using point sprites or actual quads. POINTS might be simple GL_POINTS without texture.

**Resolution**: Define `RenderMode.BILLBOARDS` as rendering particles as textured quads (or point sprites with texture) that face the camera. The vertex shader would generate quad vertices in geometry shader or use point sprite. Simpler: use `GL_POINTS` with `gl_PointSize` and a texture in fragment shader, which is essentially billboarding. We'll treat BILLBOARDS as TEXTURED mode with a default particle texture.

### [NEEDS RESEARCH]: The base class `AdvancedParticle3DSystem` had `use_texture` and `render_mode`. SilverVisions sets `render_mode = RenderMode.BILLBOARDS`. We need to ensure the base class supports this.

**Resolution**: The base class should have a `render_mode` attribute and handle different modes in rendering. For SilverVisions, we'll set `render_mode = RenderMode.BILLBOARDS` and ensure the shader uses a texture if available.

---

## Configuration Schema

Since SilverVisions inherits most configuration from AdvancedParticle3DSystem, we only need to document the macro-parameters and the fixed preset values. However, for completeness, we can reference the base class schema.

**SilverVisions-specific parameters (exposed via `set_parameter`)**:

```python
METADATA = {
  "params": [
    {"id": "turbulence", "name": "Turbulence", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float", "description": "Controls noise force strength (0-2.0)"},
    {"id": "density", "name": "Density", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float", "description": "Controls emission rate (0-200 particles/frame)"},
    {"id": "flow_speed", "name": "Flow Speed", "default": 0.0, "min": 0.0, "max": 1.0, "type": "float", "description": "Controls noise evolution speed and particle initial speed"}
  ]
}
```

**Base class parameters** (inherited, not directly set via `set_parameter` but could be):
- All the physics, emitter, visual, audio, force field, camera parameters from P3-EXT206 spec.

SilverVisions fixes many of these to specific values (e.g., `gravity = (0,0,0)`? Not specified; assume base defaults). The preset sets:
- `turbulence_strength = 0.5` (but macro overrides)
- `turbulence_scale = 2.0`
- `turbulence_speed` controlled by flow_speed
- `emit_rate` controlled by density
- `initial_speed` controlled by flow_speed
- `color_start = (0.9,0.9,1.0,1.0)`, `color_end = (0.0,0.8,0.9,0.0)`
- `render_mode = BILLBOARDS`
- `point_size = 3.0`
- `audio_sensitivity = 2.0`
- `emit_on_beat = True` on the emitter

---

## State Management

- **Per-frame state**: Active particle arrays, VBO data (updated each frame).
- **Persistent state**: All configuration parameters (emitter settings, force settings, rendering options, audio sensitivity). Macro-parameters (`turbulence`, `density`, `flow_speed`) are derived from base parameters.
- **Init-once state**: OpenGL objects (VAO, VBOs, shader, texture), emitter/force objects.
- **Thread safety**: Not thread-safe. Must be used from a single thread with OpenGL context.

---

## GPU Resources

Inherits from `AdvancedParticle3DSystem`. Requires OpenGL 3.3+. Uses VAO, VBOs, shaders, optional texture.

---

## Public Interface

```python
class SilverVisionsEffect(AdvancedParticle3DSystem):
    def __init__(self) -> None:
        """
        Initialize the Silver Visions effect with default chrome/metallic preset.
        """
    
    def _configure_silver_presets(self) -> None:
        """Internal method to set up emitter, forces, and rendering. Called from __init__."""
    
    def set_parameter(self, name: str, value: float) -> None:
        """
        Set a macro control parameter.
        
        Args:
            name: One of "turbulence", "density", "flow_speed"
            value: Float between 0.0 and 1.0
        
        Raises:
            ValueError: If name is not recognized or value out of range
        """
    
    def get_parameter(self, name: str) -> float:
        """
        Get the current value of a macro control parameter (normalized 0.0-1.0).
        
        Args:
            name: Parameter name
            
        Returns:
            Float value in [0.0, 1.0]
        
        Raises:
            ValueError: If name is not recognized
        """
    
    # Inherited methods:
    # - update(dt)
    # - render()
    # - set_audio_features(bass, mid, treble, beat)
    # - set_camera(...), set_projection_matrix(...)
    # - set_texture(texture_id)
    # - enable(enabled)
    # - get_particle_count()
    # - stop()
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `name` | `str` | Macro parameter name | Must be "turbulence", "density", or "flow_speed" |
| `value` | `float` | Macro parameter value | Must be in [0.0, 1.0] |
| `bass, mid, treble` | `float` | Audio features | 0.0-1.0 |
| `beat` | `float` or `int` | Beat flag | Typically 0.0 or 1.0 |
| `dt` | `float` | Time delta for physics | ≥ 0.0 |
| `texture_id` | `int` | OpenGL texture ID for particle sprite | Optional |
| `enabled` | `bool` | Enable/disable system | - |
| `return` (from get_parameter) | `float` | Normalized macro value | 0.0-1.0 |
| `return` (from get_particle_count) | `int` | Active particle count | ≤ max_particles |

---

## Dependencies

- External libraries:
  - `numpy` — required for particle arrays
  - `OpenGL.GL` — required for rendering
- Internal modules:
  - `vjlive3.core.effects.particles_3d.AdvancedParticle3DSystem` — base class
  - `vjlive3.core.audio_analyzer.AudioAnalyzer` (optional) — for audio features
  - `vjlive3.utils.math_utils` — for noise, matrix math

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect initializes without crashing if OpenGL context missing; raises clear error |
| `test_silver_presets_applied` | After init, emitter rate=500, noise strength=0.5, render mode=BILLBOARDS, colors set correctly |
| `test_macro_parameter_turbulence` | Setting `turbulence` from 0.0-1.0 scales `forces[0].strength` linearly 0.0-2.0 |
| `test_macro_parameter_density` | Setting `density` from 0.0-1.0 scales `emitters[0].rate` linearly 0-200 |
| `test_macro_parameter_flow_speed` | Setting `flow_speed` sets `forces[0].noise_speed` directly and `emitters[0].initial_speed` to value*0.5 |
| `test_get_parameter_returns_normalized` | `get_parameter("turbulence")` returns `forces[0].strength / 2.0` etc. |
| `test_audio_reactivity_emission` | When `audio_beat` is high, extra particles are emitted (check active_count increase) |
| `test_audio_reactivity_shader` | Audio uniforms affect particle size and position in vertex shader |
| `test_color_gradient` | Particles spawn with colors interpolating from start to end over lifetime |
| `test_billboard_rendering` | Particles are rendered as screen-facing quads (check vertex shader output) |
| `test_inherited_functionality` | Base class methods (set_gravity, set_drag, etc.) still work |
| `test_cleanup` | All OpenGL resources released on stop() |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT207: silver_visions effect implementation` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive1/core/effects/silver_visions.py (L1-20)
```python
"""
Silver Visions Effect
Advanced 3D Particle System with a chrome/metallic aesthetic.
Inherits from AdvancedParticle3DSystem to leverage GPU acceleration.
"""

from .particles_3d import AdvancedParticle3DSystem, EmitterType, ForceType, RenderMode
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SilverVisionsEffect(AdvancedParticle3DSystem):
    """
    Silver Visions - A chrome/metallic particle system.
    Features:
    - High-density particle emission
    - Turbulence forces
    - Billboard rendering with metallic coloring (White/Silver/Cyan)
    """
```

### vjlive1/core/effects/silver_visions.py (L17-36)
```python
    Features:
    - High-density particle emission
    - Turbulence forces
    - Billboard rendering with metallic coloring (White/Silver/Cyan)
    """
    
    def __init__(self):
        super().__init__()
        self.name = "SilverVisions"
        
        # Override default configuration for "Silver" look
        self._configure_silver_presets()
        
    def _configure_silver_presets(self):
        """Configure the system for the Silver Visions aesthetic."""
        
        # 1. Clear default emitters and forces if any (though super __init__ adds one)
        self.emitters = []
        self.forces = []
```

### vjlive1/core/effects/silver_visions.py (L33-52)
```python
        # 1. Clear default emitters and forces if any (though super __init__ adds one)
        self.emitters = []
        self.forces = []
        
        # 2. Main Central Emitter - High Rate, Sphere shape
        emitter_idx = self.add_emitter(EmitterType.SPHERE)
        emitter = self.emitters[emitter_idx]
        emitter.rate = 500.0  # High emission
        emitter.lifetime = 4.0
        emitter.initial_speed = 0.5
        emitter.speed_variation = 0.2
        emitter.size_range = (0.5, 2.5) # Varied sizes
        emitter.position = np.array([0.0, 0.0, 0.0])
        emitter.color_range = (
            np.array([0.9, 0.9, 1.0, 1.0]), # Silver/White
            np.array([0.0, 0.8, 0.9, 0.0])  # Cyan fadeout
        )
        emitter.emit_on_beat = True # Pulse with beat
        
        # 3. Turbulence Force (Noise)
```

### vjlive1/core/effects/silver_visions.py (L49-68)
```python
        )
        emitter.emit_on_beat = True # Pulse with beat
        
        # 3. Turbulence Force (Noise)
        force_idx = self.add_force(ForceType.NOISE)
        force = self.forces[force_idx]
        force.strength = 0.5
        force.noise_scale = 2.0
        force.noise_speed = 0.5
        
        # 4. Rendering Mode
        self.render_mode = RenderMode.BILLBOARDS
        self.point_size = 3.0
        
        # 5. Audio Reactivity
        # We want the system to be very responsive
        self.audio_sensitivity = 2.0
        
        logger.info("Silver Visions: Initialized with Chrome/Metallic presets.")
```

### vjlive1/core/effects/silver_visions.py (L65-84)
```python
        self.audio_sensitivity = 2.0
        
        logger.info("Silver Visions: Initialized with Chrome/Metallic presets.")

    def set_parameter(self, name: str, value: float):
        """
        Override set_parameter to map generic sliders to specific
        Silver Visions macro-controls.
        """
        # Map common macro knobs to complex system parameters
        if name == "turbulence":
            # Control noise strength
            if self.forces:
                self.forces[0].strength = value * 2.0
        elif name == "density":
            # Control emission rate
            if self.emitters:
                self.emitters[0].rate = value * 200.0
        elif name == "flow_speed":
            # Control noise speed and particle speed
            if self.forces:
                self.forces[0].noise_speed = value
            if self.emitters:
                self.emitters[0].initial_speed = value * 0.5
        else:
            # Pass through to base class for standard params (camera, etc)
            super().set_parameter(name, value)
```

### vjlive1/core/effects/silver_visions.py (L81-100)
```python
            if self.emitters:
                self.emitters[0].rate = value * 200.0
        elif name == "flow_speed":
            # Control noise speed and particle speed
            if self.forces:
                self.forces[0].noise_speed = value
            if self.emitters:
                self.emitters[0].initial_speed = value * 0.5
        else:
            # Pass through to base class for standard params (camera, etc)
            super().set_parameter(name, value)
            
    def get_parameter(self, name: str) -> float:
        if name == "turbulence":
            return self.forces[0].strength / 2.0 if self.forces else 0.0
        elif name == "density":
            return self.emitters[0].rate / 200.0 if self.emitters else 0.0
        elif name == "flow_speed":
            return self.forces[0].noise_speed if self.forces else 0.0
        return super().get_parameter(name)
```

[NEEDS RESEARCH]: The base class `AdvancedParticle3DSystem` must be enhanced to support an emitter/force object model as used by SilverVisions. The earlier spec for P3-EXT206 should be updated accordingly to maintain consistency. Additionally, the exact behavior of `emit_on_beat` and the noise implementation details need to be defined in the base class. The `RenderMode.BILLBOARDS` should be clearly distinguished from POINTS; likely it uses point sprites with a texture.
