# P3-EXT082_FractureRaveDatamoshEffect.md

# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT082 — FractureRaveDatamoshEffect

### What This Module Does
Implements a high-energy datamosh effect that fractures video based on depth edges, creates crack networks, and amplifies them with laser beams that pulse to audio bass. The effect is designed to be used as a post-processor that can chain after any other effect to create complex visual distortions.

### What This Module Does NOT Do
Does not handle primary video processing or source input handling. Focuses solely on the fracture and laser amplification components of the datamosh effect.

### Detailed Behavior and Parameter Interactions

#### Core Functionality
- **Depth-Based Fracture Detection**: Analyzes depth information to identify edges and create fracture networks
- **Laser Beam Generation**: Creates animated laser beams that follow fracture paths
- **Audio Reactivity**: Pulses laser intensity and frequency based on bass frequencies
- **Visual Amplification**: Enhances existing datamosh effects by adding glowing elements and displacement

#### Key Parameters
1. **fracture_sens** (float, 0.0-10.0): Sensitivity threshold for fracture detection
2. **fracture_width** (float, 0.0-10.0): Width of fracture lines
3. **fracture_glow** (float, 0.0-10.0): Intensity of laser glow effect
4. **chromatic_split** (float, 0.0-10.0): Degree of color channel separation
5. **laser_count** (float, 0.0-10.0): Number of laser beams generated
6. **laser_speed** (float, 0.0-10.0): Speed of laser beam animation
7. **laser_hue** (float, 0.0-10.0): Base hue for laser color cycling
8. **bass_pulse** (float, 0.0-10.0): Strength of audio bass pulsing effect
9. **body_glow** (float, 0.0-10.0): Overall glow intensity
10. **euphoria** (float, 0.0-10.0): Randomness factor for organic movement
11. **trails** (float, 0.0-10.0): Intensity of motion trails behind lasers
12. **mosh_intensity** (float, 0.0-10.0): Overall effect intensity multiplier

#### Interaction with Audio System
- **Bass Detection**: Uses audio analyzer to detect bass frequencies
- **Pulse Synchronization**: Laser effects pulse in time with detected bass beats
- **Dynamic Parameter Modulation**: Parameters like laser_hue and bass_pulse are modulated by audio features

#### Preset Configurations
- **club_cracks**: High-energy club environment with bright lasers and strong bass response
- **psychedelic_rave**: Trippy, organic movement with color cycling and trail effects
- **industrial_glitch**: Aggressive, metallic fractures with sharp laser beams

### Public Interface
```python
class FractureRaveDatamoshEffect(Effect):
    def __init__(self, **kwargs):
        # Initialize with parameters from kwargs
        # Set up shader programs and texture samplers

    def update(self, dt: float):
        # Update animation parameters based on time delta
        # Process audio reactivity if audio analyzer is available

    def apply(self, input_texture: int, extra_textures: list = None) -> int:
        # Apply fracture detection and laser effects to input texture
        # Return processed texture

    def set_parameter(self, name: str, value: float):
        # Update a specific parameter value

    def set_audio_analyzer(self, analyzer):
        # Set audio analyzer for bass detection
```

### Inputs and Outputs
- **Inputs**: 
  - Primary video texture (signal_in)
  - Optional extra textures for advanced effects
- **Outputs**: 
  - Processed video texture with fracture and laser effects applied

### Edge Cases and Error Handling
- Invalid parameter ranges (clamped to valid ranges)
- Missing depth texture (graceful degradation to basic datamosh)
- Shader compilation failures (fallback to simpler effect)
- Texture sampling errors (handled with texture fallback)

### Mathematical Formulations
- **Fracture Detection**: `fractureMask = step(edgeStrength, fracture_sens) * (1.0 - smoothstep(0.0, 1.0, edgeStrength))`
- **Laser Positioning**: `laserPos = fracturePos + sin(time * laser_speed + laser_hue) * 0.1`
- **Color Cycling**: `glowColor = hsv2rgb(vec3(fract(time * u_laser_hue * 0.05 + depth), 0.8, 1.0))`
- **Bass Pulse**: `pulseFactor = audio_bass * bass_pulse * 0.5`
- **Trail Effect**: `trailFactor = max(mix(1.0, trailFactor, u_trails), 0.0)`

### Performance Characteristics
- **GPU-Bound**: Entirely shader-based processing
- **Memory**: ~2-3 additional texture samplers and FBOs
- **Resolution Dependent**: O(N) where N = pixel count
- **Typical Performance**: 60+ FPS at 1080p on mid-range GPU
- **Multi-pass**: Requires 4-6 render passes per frame due to multi-stage processing

### Test Plan
1. Verify fracture detection works on various depth inputs
2. Test all parameter ranges and clamping behavior
3. Validate laser animation and movement patterns
4. Test audio reactivity with different music genres
5. Validate preset configurations produce expected visual results
6. Measure performance at various resolutions (720p, 1080p, 4K)
7. Test chaining with other effects (datamosh, pixel_sort, etc.)
8. Verify cleanup of all allocated resources

### Definition of Done
- [ ] Spec reviewed by Manager
- [ ] All test cases pass
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

## LEGACY CODE REFERENCES
- plugins/vdatamosh/fracture_rave_datamosh.py (Main implementation)
- core/matrix/node_datamosh.py (Effect node registration)
- plugins/core/fracture_rave_datamosh/plugin.json (Parameter definitions)
- core/effects/shader_base.py (Base Effect class)
- tests/test_legacy_migration.py (Test coverage)
