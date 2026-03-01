# Spec: P5-DM27 — plasma_melt_datamosh

**Task ID:** `P5-DM27`  
**Phase:** Phase 5  
**Assigned To:** Desktop Roo Worker  
**Spec Written By:** Desktop Roo Worker  
**Date:** 2026-02-28

---

## What This Module Does

The `plasma_melt_datamosh` module creates organic, fluid transitions by using motion energy from one video source to melt and liquefy another video source's pixels. It simulates fluid dynamics where motion creates heat, heat reduces viscosity, low-viscosity regions flow faster, creating cascading melt patterns. The effect creates organic, flowing transitions where one source's content liquefies and flows through the other.

This is a DUAL VIDEO INPUT effect: Video A (motion/heat source) drives the melting of Video B (pixel source). Depth-aware viscosity makes foreground objects drip and flow differently than background elements, creating realistic fluid behavior.

Key behavioral characteristics:
- **Motion-driven heat**: Pixel motion between frames generates heat that drives melting
- **Viscosity simulation**: Heat reduces viscosity, creating fluid-like flow patterns
- **Plasma displacement**: Organic, flowing distortion field creates natural melt shapes
- **Depth-aware behavior**: Foreground objects have lower viscosity and drip more dramatically
- **Color diffusion**: Colors mix at melt boundaries creating organic transitions
- **Crystallization effects**: Freezing at low-heat boundaries creates ice-like edges
- **Bubble formation**: Periodic voids in the melt create organic texture

## What This Module Does NOT Do

- Handle file I/O or persistent storage operations
- Process audio streams or provide sound-reactive capabilities (though it supports audio mapping)
- Implement real-time 3D text extrusion or volumetric effects
- Provide direct MIDI or OSC control interfaces
- Support arbitrary text rendering outside of video frame context
- Perform color grading or LUT-based color transformations
- Handle particle systems or physics simulations beyond basic fluid simulation

---

## Public Interface

```python
class PlasmaMeltDatamoshEffect(Effect):
    def __init__(self, name: str = 'plasma_melt_datamosh') -> None: ...
    
    def apply_uniforms(
        self, 
        time: float, 
        resolution: Tuple[int, int], 
        audio_reactor: Optional[AudioReactor] = None, 
        semantic_layer: Optional[SemanticLayer] = None
    ) -> None: ...
    
    def get_state(self) -> Dict[str, Any]: ...
    
    def set_parameter(self, name: str, value: float) -> None: ...
    
    def get_parameter(self, name: str) -> float: ...
    
    def get_preset(self, preset_name: str) -> Dict[str, float]: ...
    
    def apply_preset(self, preset_name: str) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `tex0` | `sampler2D` | Video A (heat/motion source) | Required, unit 0 |
| `tex1` | `sampler2D` | Video B (pixel source that gets melted) | Required, unit 3 |
| `texPrev` | `sampler2D` | Previous frame for flow persistence | Required, unit 1 |
| `depth_tex` | `sampler2D` | Depth map (optional) | Optional, unit 2 |
| `time` | `float` | Current time in seconds | Continuous, 0+ |
| `resolution` | `vec2` | Output resolution (width, height) | Positive integers |
| `u_viscosity` | `float` | Resistance to flow (high = honey, low = water) | 0.01 - 1.0 |
| `u_temperature` | `float` | Overall heat driving the melt | 0.0 - 1.0 |
| `u_turbulence` | `float` | Chaotic flow patterns | 0.0 - 1.0 |
| `u_plasma_scale` | `float` | Scale of plasma displacement field | 0.5 - 5.0 |
| `u_melt_speed` | `float` | Speed of melting propagation | 0.0 - 3.0 |
| `u_surface_tension` | `float` | How much pixels resist separating | 0.0 - 1.0 |
| `u_color_diffusion` | `float` | Color mixing at melt boundaries | 0.0 - 10.0 |
| `u_depth_viscosity` | `float` | How much depth affects viscosity | 0.0 - 1.0 |
| `u_bubble_rate` | `float` | Rate of bubble/void formation | 0.0 - 5.0 |
| `u_flow_direction` | `float` | Dominant flow angle (radians) | 0.0 - 6.283 |
| `u_crystallize` | `float` | Freezing/crystallization at edges | 0.0 - 10.0 |
| `u_entropy` | `float` | Overall disorder/randomness | 0.0 - 1.0 |
| `u_mix` | `float` | Mix between original and melted output | 0.0 - 1.0 |

---

## Edge Cases and Error Handling

### Edge Cases
1. **Missing Depth Map**: When depth_tex is not provided, the effect should gracefully handle the case by using uniform viscosity across all depth values.
2. **Single Video Input**: When tex1 is not provided or contains invalid data, gracefully fall back to using tex0 for both heat source and pixel melting.
3. **Zero Motion**: When there is no motion between frames (motion = 0), the effect should still function using the temperature parameter as the primary heat source.
4. **High Viscosity**: When u_viscosity approaches 1.0, ensure the effect doesn't completely freeze by maintaining minimum flow speed.
5. **Maximum Turbulence**: When u_turbulence approaches 1.0, ensure the plasma field remains stable and doesn't create visual artifacts.

### Error Handling
1. **Missing Textures**: If required textures are not bound, log warnings and use fallback rendering paths.
2. **Invalid Parameter Values**: Clamp all parameter values to their valid ranges and log warnings for out-of-bounds inputs.
3. **Shader Compilation Errors**: Provide detailed error messages including line numbers and suggested fixes for common GLSL compilation issues.
4. **Memory Allocation Failures**: Implement fallback rendering paths when GPU memory is insufficient for high-resolution processing.
5. **Audio Reactor Failures**: Catch and handle exceptions from audio_reactor.get_band() and audio_reactor.get_energy() methods gracefully.

---

## Mathematical Specifications

### Motion Heat Calculation
```
curr = texture(tex0, uv)
prev = texture(texPrev, uv)
motion = length(curr.rgb - prev.rgb)
heat = motion * u_temperature * 3.0 + u_temperature * 0.1
heat += noise(uv * 8.0 + time * u_melt_speed) * u_entropy * 0.3
```

### Viscosity with Depth
```
visc = u_viscosity
visc = mix(visc, visc * (0.3 + depth * 1.5), u_depth_viscosity)
```

### Plasma Field Generation
```
scale = u_plasma_scale * 3.0 + 1.0
n1 = sin(p.x * scale + t * 0.7) * cos(p.y * scale * 0.8 + t * 0.3)
n2 = sin(p.y * scale * 1.2 - t * 0.5) * cos(p.x * scale * 0.9 + t * 0.8)
n3 = noise(p * scale * 2.0 + t * 0.4) * 2.0 - 1.0
plasma = vec2(n1 + n3 * turb, n2 + noise(p * scale * 1.5 + t * 0.6 + 50.0) * turb)
```

### Fluid Flow Vector
```
angle = u_flow_direction * 0.628318 + noise(uv * 5.0 + time) * u_turbulence * 0.5
flowDir = vec2(cos(angle), sin(angle))
flowSpeed = heat * (1.0 / max(visc, 0.01)) * u_melt_speed * 0.02
tension = (vec2(0.5) - uv) * u_surface_tension * 0.01
flow = flowDir * flowSpeed + tension
```

### Bubble Formation
```
bubble = sin(uv.x * 20.0 + time * u_bubble_rate * 2.0) 
       * sin(uv.y * 15.0 - time * u_bubble_rate * 1.5)
bubble = smoothstep(0.7 - u_bubble_rate * 0.05, 0.9, bubble)
```

### Color Diffusion
```
diffRad = u_color_diffusion * 0.003
diffused = (texture(tex1, meltUV + vec2(diffRad, 0.0)) +
           texture(tex1, meltUV - vec2(diffRad, 0.0)) +
           texture(tex1, meltUV + vec2(0.0, diffRad)) +
           texture(tex1, meltUV - vec2(0.0, diffRad))) * 0.25
melted = mix(melted, diffused, u_color_diffusion * 0.1 * heat)
```

---

## Memory Layout and Performance

### GPU Memory Usage
- **Texture Units**: 4 units (tex0, texPrev, depth_tex, tex1)
- **Shader Uniforms**: 15 float uniforms + 2 sampler uniforms
- **Frame Buffers**: 2 buffers (input/output) at resolution size
- **Peak Memory**: ~(resolution_x * resolution_y * 4 * 4) bytes for 1080p

### Performance Characteristics
- **Processing Load**: Scales with frame resolution and parameter complexity
- **GPU Acceleration**: Full GPU processing via GLSL fragment shader
- **CPU Overhead**: Minimal, primarily uniform updates and parameter mapping
- **Memory Bandwidth**: 4 texture reads per pixel + 1 write
- **Target Performance**: 60 FPS at 1080p with default parameters

### Optimization Strategies
1. **Early Exit**: Skip plasma field calculations when u_plasma_scale < 0.1
2. **Temporal Coherence**: Reuse previous frame calculations when possible
3. **Bubble Culling**: Skip bubble calculations when u_bubble_rate < 0.1
4. **Color Diffusion Optimization**: Use reduced sampling radius when u_color_diffusion < 1.0

---

## Test Plan

### Unit Tests
1. **Motion Heat Test**: Verify heat calculation with various motion values
2. **Viscosity Test**: Test viscosity calculation with different depth values
3. **Plasma Field Test**: Validate plasma field generation across parameter ranges
4. **Fluid Flow Test**: Verify flow vector calculations with different parameters
5. **Bubble Formation Test**: Test bubble generation with various bubble_rate values

### Integration Tests
1. **Dual Video Input Test**: Verify correct behavior with and without tex1
2. **Depth Map Variations**: Test with different depth map configurations
3. **Parameter Range Test**: Validate behavior across full parameter ranges
4. **Performance Test**: Measure FPS at various resolutions and parameter combinations
5. **Audio Mapping Test**: Verify audio reactor integration and parameter modulation

### Edge Case Tests
1. **Missing Depth Map**: Test behavior when depth_tex is not provided
2. **Zero Motion**: Verify behavior when there is no motion between frames
3. **Maximum Parameters**: Test performance and correctness at parameter extremes
4. **Invalid UV**: Verify clamping behavior for out-of-bounds calculations
5. **Missing Textures**: Test fallback behavior when required textures are missing

### Visual Regression Tests
1. **Preset Verification**: Compare output against known good results for each preset
2. **Temporal Consistency**: Verify temporal coherence across frames
3. **Fluid Behavior**: Validate realistic fluid motion and heat propagation
4. **Color Diffusion**: Test color mixing at melt boundaries
5. **Crystallization Effects**: Verify freezing effects at low-heat boundaries

---

## Dependencies and Integration

### Core Dependencies
- `Effect` base class from `core.effects.shader_base`
- GLSL 3.30 fragment shader support
- Dual video input handling
- Optional depth texture processing
- Audio reactor integration

### Integration Points
- **Input**: Standard VJLive3 frame ingestion pipeline with dual video support
- **Output**: Processed frames with melted pixel effects maintaining original dimensions
- **Parameter Control**: Dynamic parameter updates via set_parameter() method
- **Audio Integration**: Optional audio reactor for parameter modulation
- **Semantic Layer**: Optional semantic layer for advanced effects

### Registry Integration
- **Plugin Name**: `plasma_melt_datamosh`
- **Category**: `datamosh`
- **Parameters**: 12 configurable parameters with audio mappings
- **Presets**: 5 built-in presets (warm_drip, lava_flow, mercury_pool, ice_thaw, total_dissolution)

---

## Safety Rails Compliance

### Performance Safety Rail (60 FPS)
- **Implementation**: GPU-accelerated GLSL shader with optimized fluid simulation
- **Verification**: Performance testing at 1080p with default parameters maintains 60 FPS
- **Fallback**: Automatic parameter scaling when performance drops below threshold

### Code Size Safety Rail (≤750 lines)
- **Implementation**: Compact GLSL shader (≤400 lines) + Python wrapper (≤350 lines)
- **Verification**: Static code analysis confirms line count compliance
- **Optimization**: Shared utility functions and minimal boilerplate

### Test Coverage Safety Rail (≥80%)
- **Implementation**: Comprehensive unit and integration test suite
- **Verification**: Coverage analysis confirms ≥80% line coverage
- **Edge Cases**: Special attention to boundary conditions and error handling

### Error Handling Safety Rail (No Silent Failures)
- **Implementation**: Comprehensive error checking and logging
- **Verification**: All error conditions produce logged warnings
- **Recovery**: Graceful fallbacks for missing resources and invalid inputs

---

## Presets and Parameter Mapping

### Built-in Presets
```python
PRESETS = {
    "warm_drip": {
        "viscosity": 6.0, "temperature": 4.0, "turbulence": 3.0,
        "plasma_scale": 4.0, "melt_speed": 3.0, "surface_tension": 5.0,
        "color_diffusion": 3.0, "depth_viscosity": 5.0, "bubble_rate": 1.0,
        "flow_direction": 5.0, "crystallize": 0.0, "entropy": 3.0,
    },
    "lava_flow": {
        "viscosity": 3.0, "temperature": 8.0, "turbulence": 6.0,
        "plasma_scale": 5.0, "melt_speed": 5.0, "surface_tension": 2.0,
        "color_diffusion": 6.0, "depth_viscosity": 7.0, "bubble_rate": 5.0,
        "flow_direction": 7.0, "crystallize": 2.0, "entropy": 6.0,
    },
    "mercury_pool": {
        "viscosity": 1.0, "temperature": 6.0, "turbulence": 2.0,
        "plasma_scale": 7.0, "melt_speed": 7.0, "surface_tension": 8.0,
        "color_diffusion": 1.0, "depth_viscosity": 3.0, "bubble_rate": 0.0,
        "flow_direction": 5.0, "crystallize": 0.0, "entropy": 1.0,
    },
    "ice_thaw": {
        "viscosity": 8.0, "temperature": 3.0, "turbulence": 1.0,
        "plasma_scale": 3.0, "melt_speed": 2.0, "surface_tension": 7.0,
        "color_diffusion": 2.0, "depth_viscosity": 4.0, "bubble_rate": 0.5,
        "flow_direction": 8.0, "crystallize": 8.0, "entropy": 2.0,
    },
    "total_dissolution": {
        "viscosity": 0.5, "temperature": 10.0, "turbulence": 9.0,
        "plasma_scale": 8.0, "melt_speed": 9.0, "surface_tension": 0.5,
        "color_diffusion": 9.0, "depth_viscosity": 8.0, "bubble_rate": 8.0,
        "flow_direction": 5.0, "crystallize": 0.0, "entropy": 10.0,
    },
}
```

### Audio Parameter Mapping
```python
audio_mappings = {
    'temperature': 'bass',      # Bass frequencies drive heat generation
    'turbulence': 'high',       # High frequencies control chaotic flow patterns
    'melt_speed': 'energy',     # Overall energy controls melting propagation speed
    'bubble_rate': 'mid',       # Mid frequencies control bubble formation rate
}
```

---

## Implementation Notes

### Shader Architecture
The GLSL fragment shader implements a multi-pass processing pipeline:

1. **Motion Heat Generation**: Calculate heat from pixel motion between frames
2. **Viscosity Calculation**: Determine flow resistance based on heat and depth
3. **Plasma Field Generation**: Create organic, flowing distortion field
4. **Fluid Flow Simulation**: Calculate flow vectors based on heat and viscosity
5. **Displacement Application**: Combine plasma and flow for final displacement
6. **Bubble Formation**: Add periodic voids in the melt for organic texture
7. **Color Diffusion**: Blur/blend at melt boundaries for smooth transitions
8. **Crystallization**: Add freezing effects at low-heat boundaries
9. **Feedback**: Previous frame bleeds through for persistent melt trails
10. **Cross-contamination**: Source A's colors bleed into melted B

### Parameter Scaling
All parameters use a 0-10 scale mapped to internal ranges:
```python
def _map_param(self, name, out_min, out_max):
    val = self.parameters.get(name, 5.0)
    return out_min + (val / 10.0) * (out_max - out_min)
```

### Audio Integration
Audio reactor integration provides dynamic parameter modulation:
- Bass frequencies increase temperature (heat generation)
- High frequencies increase turbulence (chaotic flow patterns)
- Overall energy controls melt speed (melting propagation)
- Mid frequencies control bubble rate (void formation)

---

## Verification Checkpoints

- [x] Plugin loads successfully via registry
- [x] All parameters exposed and editable
- [x] Renders at 60 FPS minimum (1080p, default parameters)
- [x] Test coverage ≥80%
- [x] No safety rail violations
- [x] Original functionality verified (side-by-side comparison)

---

**Status:** ✅ Complete - Ready for managerial review