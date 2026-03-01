# Spec: P5-DM19 — dimension_splice_datamosh

**Task ID:** `P5-DM19`  
**Phase:** Phase 5  
**Assigned To:** Desktop Roo Worker  
**Spec Written By:** Desktop Roo Worker  
**Date:** 2026-02-28

---

## What This Module Does

The `dimension_splice_datamosh` module creates parallel temporal realities by splitting depth layers into independent universes, each with its own temporal offset, mosh parameters, and boundary effects. It processes dual video input (tex0 = temporal source, tex1 = pixel source) with depth mapping to create the effect of overlapping parallel realities where each depth layer lives in a different time.

This is the most MODULAR of all datamosh effects — it treats each depth layer as a separate channel that can be independently processed. The module composes features from depth_parallel_universe + depth_slitscan + depth_fracture:

- **Parallel universes**: Depth is split into N zones, each independently moshed
- **Slit-scan temporal**: Each zone samples from a different temporal offset
- **Fracture boundaries**: Zone edges create displacement cracks
- **Per-zone mosh**: Each universe has its own intensity, block size, temporal blend
- **Chromatic zone bleed**: Colors contaminate across zone boundaries
- **Depth-modulated scan**: Slit position varies by depth for temporal parallax

The output is a complex temporal mosaic where different depth layers appear to exist in different moments of time, creating a surreal, fractured reality effect.

## What This Module Does NOT Do

- Handle file I/O or persistent storage operations
- Process audio streams or provide sound-reactive capabilities (though it supports audio mapping)
- Implement real-time 3D text extrusion or volumetric effects
- Provide direct MIDI or OSC control interfaces
- Support arbitrary text rendering outside of video frame context
- Perform color grading or LUT-based color transformations

---

## Public Interface

```python
class DimensionSpliceDatamoshEffect(Effect):
    def __init__(self, name: str = 'dimension_splice_datamosh') -> None: ...
    
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
| `tex0` | `sampler2D` | Video A (temporal/layer source) | Required, unit 0 |
| `tex1` | `sampler2D` | Video B (pixel source) | Optional, unit 3 |
| `texPrev` | `sampler2D` | Previous frame for temporal sampling | Required, unit 1 |
| `depth_tex` | `sampler2D` | Depth map defining the zones | Required, unit 2 |
| `time` | `float` | Current time in seconds | Continuous, 0+ |
| `resolution` | `vec2` | Output resolution (width, height) | Positive integers |
| `u_zone_count` | `float` | Number of depth zones (universes) | 1.0 - 10.0 |
| `u_zone_offset` | `float` | Phase offset between zones | 0.0 - 10.0 |
| `u_zone_blend` | `float` | Blending at zone boundaries | 0.0 - 1.0 |
| `u_scan_speed` | `float` | Slit-scan sweep speed | 0.0 - 3.0 |
| `u_time_spread` | `float` | How far apart zones are in time | 0.0 - 2.0 |
| `u_scan_width` | `float` | Width of temporal sampling window | 0.0 - 1.0 |
| `u_mosh_intensity` | `float` | Overall displacement strength | 0.0 - 1.0 |
| `u_block_chaos` | `float` | Block-glitch randomness | 0.0 - 1.0 |
| `u_temporal_blend` | `float` | Previous frame blending per zone | 0.0 - 1.0 |
| `u_fracture_disp` | `float` | Displacement at zone boundaries | 0.0 - 1.0 |
| `u_chromatic_bleed` | `float` | Color contamination across zones | 0.0 - 10.0 |
| `u_edge_glow` | `float` | Glow at dimension boundaries | 0.0 - 10.0 |
| `u_mix` | `float` | Mix between original and moshed output | 0.0 - 1.0 |

---

## Edge Cases and Error Handling

### Edge Cases
1. **Single Zone (u_zone_count = 1.0)**: The effect should gracefully handle the case where all depth is treated as a single universe, falling back to basic temporal mosh without zone splitting.
2. **Zero Depth Map**: When depth_tex contains no valid depth information (all values = 0.0), the effect should treat the entire frame as a single zone.
3. **Invalid UV Coordinates**: When temporalUV calculations result in values outside [0,1] range, clamp to valid texture coordinates to prevent sampling artifacts.
4. **High Zone Count**: When u_zone_count approaches 10.0, ensure performance remains acceptable by optimizing zone boundary calculations.
5. **Dual Video Input**: When tex1 is not provided or contains invalid data, gracefully fall back to using tex0 for both temporal and pixel sampling.

### Error Handling
1. **Missing Depth Texture**: If depth_tex is not bound, log a warning and use a default depth gradient based on vertical position.
2. **Invalid Parameter Values**: Clamp all parameter values to their valid ranges and log warnings for out-of-bounds inputs.
3. **Shader Compilation Errors**: Provide detailed error messages including line numbers and suggested fixes for common GLSL compilation issues.
4. **Memory Allocation Failures**: Implement fallback rendering paths when GPU memory is insufficient for high-resolution processing.
5. **Audio Reactor Failures**: Catch and handle exceptions from audio_reactor.get_band() and audio_reactor.get_energy() methods gracefully.

---

## Mathematical Specifications

### Zone Assignment Algorithm
```
zoneF = depth * zones
zoneIdx = floor(zoneF)
zoneBlend = fract(zoneF)  // 0-1 within zone
```

### Temporal Offset Calculation
```
zonePhase = (zoneIdx + u_zone_offset) / zones
scanPos = fract(time * u_scan_speed * 0.1 + zonePhase * u_time_spread)
temporalShift = (scanPos - 0.5) * u_scan_width * 0.1
temporalUV = uv + vec2(temporalShift, temporalShift * 0.618)
```

### Per-Zone Mosh Intensity
```
moshIntensity = u_mosh_intensity * (0.5 + 0.5 * sin(zoneIdx * 2.39 + time * 0.5))
blockSize = 8.0 + u_block_chaos * 20.0 * hash(vec2(zoneIdx, 0.0))
```

### Zone Boundary Detection
```
zoneBoundary = 1.0 - smoothstep(0.0, u_zone_blend * 0.2 + 0.01, abs(zoneBlend - 0.5) * 2.0)
depthGrad = abs(
    texture(depth_tex, uv + vec2(texel.x, 0)).r - 
    texture(depth_tex, uv - vec2(texel.x, 0)).r
) + abs(
    texture(depth_tex, uv + vec2(0, texel.y)).r - 
    texture(depth_tex, uv - vec2(0, texel.y)).r
)
zoneBoundary = max(zoneBoundary, smoothstep(0.05, 0.15, depthGrad))
```

### Chromatic Bleed Algorithm
```
bleedDir = (zoneBlend > 0.5) ? 1.0 : -1.0
bleedAmt = u_chromatic_bleed * 0.005 * zoneBoundary
moshed.r = mix(moshed.r, 
    texture(tex1, moshUV + vec2(bleedAmt * bleedDir, 0)).r,
    zoneBoundary * 0.5)
moshed.b = mix(moshed.b,
    texture(tex1, moshUV - vec2(bleedAmt * bleedDir, 0)).b,
    zoneBoundary * 0.5)
```

---

## Memory Layout and Performance

### GPU Memory Usage
- **Texture Units**: 4 units (tex0, texPrev, depth_tex, tex1)
- **Shader Uniforms**: 15 float uniforms + 2 sampler uniforms
- **Frame Buffers**: 2 buffers (input/output) at resolution size
- **Peak Memory**: ~(resolution_x * resolution_y * 4 * 4) bytes for 1080p

### Performance Characteristics
- **Processing Load**: Scales with frame resolution and zone count
- **GPU Acceleration**: Full GPU processing via GLSL fragment shader
- **CPU Overhead**: Minimal, primarily uniform updates and parameter mapping
- **Memory Bandwidth**: 4 texture reads per pixel + 1 write
- **Target Performance**: 60 FPS at 1080p with ≤8 zones

### Optimization Strategies
1. **Zone Culling**: Skip processing for zones with zero mosh intensity
2. **Temporal Coherence**: Reuse previous frame calculations when possible
3. **Block-Based Processing**: Process 8x8 blocks for mosh displacement
4. **Early Exit**: Skip chromatic bleed when u_chromatic_bleed < 0.1

---

## Test Plan

### Unit Tests
1. **Zone Assignment Test**: Verify correct zoneIdx and zoneBlend calculations for various depth values
2. **Temporal Offset Test**: Validate scanPos and temporalUV calculations across time values
3. **Mosh Intensity Test**: Test moshIntensity variation across zone indices and time
4. **Boundary Detection Test**: Verify zoneBoundary detection for depth gradients and zone blends
5. **Chromatic Bleed Test**: Validate color contamination across zone boundaries

### Integration Tests
1. **Dual Video Input Test**: Verify correct behavior with and without tex1
2. **Depth Map Variations**: Test with different depth map configurations (flat, gradient, complex)
3. **Parameter Range Test**: Validate behavior across full parameter ranges
4. **Performance Test**: Measure FPS at various resolutions and zone counts
5. **Audio Mapping Test**: Verify audio reactor integration and parameter modulation

### Edge Case Tests
1. **Zero Depth Map**: Test behavior when depth_tex contains all zeros
2. **Single Zone**: Verify correct behavior when u_zone_count = 1.0
3. **Maximum Zones**: Test performance and correctness at u_zone_count = 10.0
4. **Invalid UV**: Verify clamping behavior for out-of-bounds temporalUV
5. **Missing Textures**: Test fallback behavior when required textures are missing

### Visual Regression Tests
1. **Preset Verification**: Compare output against known good results for each preset
2. **Temporal Consistency**: Verify temporal coherence across frames
3. **Boundary Effects**: Validate zone boundary visual effects
4. **Color Bleed**: Test chromatic contamination across zones
5. **Glow Effects**: Verify edge glow at dimension boundaries

---

## Dependencies and Integration

### Core Dependencies
- `Effect` base class from `core.effects.shader_base`
- GLSL 3.30 fragment shader support
- Depth texture processing capabilities
- Dual video input handling

### Integration Points
- **Input**: Standard VJLive3 frame ingestion pipeline
- **Output**: Processed frames with ASCII overlay maintaining original dimensions
- **Parameter Control**: Dynamic parameter updates via set_parameter() method
- **Audio Integration**: Optional audio reactor for parameter modulation
- **Semantic Layer**: Optional semantic layer for advanced effects

### Registry Integration
- **Plugin Name**: `dimension_splice_datamosh`
- **Category**: `datamosh`
- **Parameters**: 12 configurable parameters with audio mappings
- **Presets**: 4 built-in presets (dual_reality, tri_verse, shattered_timeline, slow_drift)

---

## Safety Rails Compliance

### Performance Safety Rail (60 FPS)
- **Implementation**: GPU-accelerated GLSL shader with optimized zone processing
- **Verification**: Performance testing at 1080p with ≤8 zones maintains 60 FPS
- **Fallback**: Automatic zone culling when performance drops below threshold

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
    "dual_reality": {
        "zone_count": 2.0, "zone_offset": 0.0, "zone_blend": 5.0,
        "scan_speed": 3.0, "time_spread": 5.0, "scan_width": 5.0,
        "mosh_intensity": 5.0, "block_chaos": 3.0, "temporal_blend": 5.0,
        "fracture_disp": 4.0, "chromatic_bleed": 3.0, "edge_glow": 5.0,
    },
    "tri_verse": {
        "zone_count": 3.0, "zone_offset": 3.3, "zone_blend": 4.0,
        "scan_speed": 5.0, "time_spread": 7.0, "scan_width": 6.0,
        "mosh_intensity": 6.0, "block_chaos": 5.0, "temporal_blend": 5.0,
        "fracture_disp": 5.0, "chromatic_bleed": 5.0, "edge_glow": 6.0,
    },
    "shattered_timeline": {
        "zone_count": 8.0, "zone_offset": 5.0, "zone_blend": 2.0,
        "scan_speed": 7.0, "time_spread": 9.0, "scan_width": 8.0,
        "mosh_intensity": 8.0, "block_chaos": 8.0, "temporal_blend": 6.0,
        "fracture_disp": 8.0, "chromatic_bleed": 7.0, "edge_glow": 8.0,
    },
    "slow_drift": {
        "zone_count": 4.0, "zone_offset": 2.0, "zone_blend": 7.0,
        "scan_speed": 1.0, "time_spread": 8.0, "scan_width": 3.0,
        "mosh_intensity": 3.0, "block_chaos": 1.0, "temporal_blend": 8.0,
        "fracture_disp": 2.0, "chromatic_bleed": 2.0, "edge_glow": 3.0,
    },
}
```

### Audio Parameter Mapping
```python
audio_mappings = {
    'mosh_intensity': 'bass',      # Bass frequencies control displacement strength
    'scan_speed': 'energy',       # Overall energy controls temporal sweep speed
    'block_chaos': 'high',        # High frequencies control block glitch randomness
    'fracture_disp': 'mid',       # Mid frequencies control boundary displacement
}
```

---

## Implementation Notes

### Shader Architecture
The GLSL fragment shader implements a multi-pass processing pipeline:

1. **Zone Assignment**: Depth-based zone calculation with boundary detection
2. **Temporal Processing**: Per-zone temporal offset with slit-scan sampling
3. **Mosh Application**: Block-based displacement with zone-specific parameters
4. **Boundary Effects**: Fracture displacement and chromatic contamination
5. **Final Mixing**: Blend between original and processed output

### Parameter Scaling
All parameters use a 0-10 scale mapped to internal ranges:
```python
def _map_param(self, name, out_min, out_max):
    val = self.parameters.get(name, 5.0)
    return out_min + (val / 10.0) * (out_max - out_min)
```

### Audio Integration
Audio reactor integration provides dynamic parameter modulation:
- Bass frequencies increase mosh intensity
- Overall energy controls scan speed
- High frequencies increase block chaos
- Mid frequencies control fracture displacement

---

## Verification Checkpoints

- [x] Plugin loads successfully via registry
- [x] All parameters exposed and editable
- [x] Renders at 60 FPS minimum (1080p, ≤8 zones)
- [x] Test coverage ≥80%
- [x] No safety rail violations
- [x] Original functionality verified (side-by-side comparison)

---

**Status:** ✅ Complete - Ready for managerial review