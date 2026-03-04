# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT124_PatternDistortionEffect.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT124 — PatternDistortionEffect

**What This Module Does**
- Applies geometric pattern distortion to video frames using mathematical transformations
- Creates visual effects like kaleidoscope, mirror, tiling, and wave distortions
- Supports real-time parameter modulation for dynamic visual effects
- Integrates with AudioReactor for audio-reactive pattern transformations

**What This Module Does NOT Do**
- Does not perform color correction or grading
- Does not handle video encoding/decoding
- Does not manage audio processing (delegates to AudioReactor)
- Does not provide 3D transformations (2D only)

---

## Detailed Behavior and Parameter Interactions

PatternDistortionEffect applies mathematical transformations to create repeating geometric patterns and distortions. The core behavior involves:

1. **Pattern Generation**: Creates base patterns using mathematical functions (sine waves, radial patterns, grid patterns)
2. **Distortion Application**: Applies geometric transformations to warp the pattern space
3. **Video Mapping**: Maps the distorted pattern onto the input video frame
4. **Audio Reactivity**: Modulates transformation parameters based on audio analysis

**Parameter Interactions**:
- `pattern_type` (0.0-10.0) determines the base pattern algorithm
- `distortion_strength` (0.0-10.0) controls the intensity of geometric warping
- `frequency` (0.0-10.0) affects the scale of pattern repetition
- `phase` (0.0-10.0) shifts the pattern position over time
- `audio_reactivity` (0.0-10.0) scales audio-driven modulation

---

## Public Interface

```python
class PatternDistortionEffect(Effect):
    def __init__(self):
        super().__init__()
        
        # Core parameters
        self.pattern_type = Parameter("Pattern Type", 0.0, 10.0, default=0.0)
        self.distortion_strength = Parameter("Distortion Strength", 0.0, 10.0, default=5.0)
        self.frequency = Parameter("Frequency", 0.0, 10.0, default=5.0)
        self.phase = Parameter("Phase", 0.0, 10.0, default=0.0)
        self.audio_reactivity = Parameter("Audio Reactivity", 0.0, 10.0, default=0.0)
        
        # Advanced parameters
        self.wave_type = Parameter("Wave Type", 0.0, 10.0, default=0.0)
        self.symmetry = Parameter("Symmetry", 0.0, 10.0, default=5.0)
        self.rotation = Parameter("Rotation", 0.0, 10.0, default=0.0)
        
        # Audio-reactive parameters
        self.audio_low_reactivity = Parameter("Audio Low Reactivity", 0.0, 10.0, default=0.0)
        self.audio_mid_reactivity = Parameter("Audio Mid Reactivity", 0.0, 10.0, default=0.0)
        self.audio_high_reactivity = Parameter("Audio High Reactivity", 0.0, 10.0, default=0.0)
```

---

## Inputs and Outputs

**Inputs:**
- `video_in` (required): Input video frame (RGBA format)
- `audio_in` (optional): Audio analysis data from AudioReactor

**Outputs:**
- `video_out` (required): Distorted video frame with applied patterns
- `pattern_data` (optional): Debug output showing the base pattern before distortion

---

## Edge Cases and Error Handling

**Edge Cases:**
- **Empty input frame**: Returns black frame with error overlay
- **Zero frequency**: Returns original frame without pattern application
- **Maximum distortion**: May cause visual artifacts; clamps to safe limits
- **Audio data missing**: Falls back to default parameter values
- **High symmetry values**: May cause performance degradation; optimizes for common cases

**Error Handling:**
- Graceful degradation when audio data unavailable
- Parameter clamping to prevent extreme values
- Performance monitoring with frame rate fallback
- Memory management for large pattern buffers

---

## Mathematical Formulations

**Pattern Generation Functions:**

```glsl
// Basic wave pattern
float wavePattern(vec2 uv, float frequency, float phase) {
    return sin(uv.x * frequency + phase) * 0.5 + 0.5;
}

// Radial pattern
float radialPattern(vec2 uv, float frequency, float phase) {
    float dist = length(uv - 0.5);
    return sin(dist * frequency + phase) * 0.5 + 0.5;
}

// Grid pattern
float gridPattern(vec2 uv, float frequency, float phase) {
    vec2 grid = floor(uv * frequency + phase);
    return mod(grid.x + grid.y, 2.0);
}
```

**Distortion Functions:**

```glsl
// Wave distortion
vec2 waveDistortion(vec2 uv, float strength) {
    return uv + vec2(
        sin(uv.y * 10.0) * strength * 0.01,
        sin(uv.x * 10.0) * strength * 0.01
    );
}

// Radial distortion
vec2 radialDistortion(vec2 uv, float strength) {
    vec2 center = uv - 0.5;
    float dist = length(center);
    float angle = atan(center.y, center.x);
    float new_dist = dist * (1.0 + strength * 0.1);
    return vec2(cos(angle), sin(angle)) * new_dist + 0.5;
}

// Kaleidoscope distortion
vec2 kaleidoscopeDistortion(vec2 uv, float symmetry) {
    vec2 center = uv - 0.5;
    float angle = atan(center.y, center.x);
    float sector = floor(angle / (2.0 * 3.14159 / symmetry));
    angle = mod(angle, 2.0 * 3.14159 / symmetry);
    return vec2(cos(angle), sin(angle)) * length(center) + 0.5;
}
```

**Audio-Reactive Modulation:**

```glsl
// Audio-reactive parameter modulation
float audioModulatedValue(float baseValue, float reactivity, float audioLevel) {
    return baseValue + (audioLevel - 0.5) * reactivity * 2.0;
}

// Frequency modulation based on audio bands
vec2 audioFrequencyModulation(vec2 uv, float low, float mid, float high) {
    float audioMod = low * 0.3 + mid * 0.5 + high * 0.2;
    return uv * (1.0 + audioMod * 0.1);
}
```

---

## Performance Characteristics

**Target Performance:**
- **60 FPS** at 1080p resolution on mid-range GPUs
- **30 FPS** at 4K resolution on high-end GPUs
- **Frame time**: <16.67ms for 1080p at 60 FPS

**Optimization Strategies:**
- **Pattern caching**: Pre-computes static patterns for reuse
- **Level-of-detail**: Reduces pattern complexity at lower resolutions
- **GPU acceleration**: Uses fragment shaders for parallel processing
- **Audio batching**: Processes audio data in chunks to reduce overhead

**Memory Usage:**
- **Pattern buffers**: ~2-4MB for common pattern sizes
- **Frame buffers**: Standard video frame size (4 bytes per pixel)
- **Audio buffers**: ~1KB for real-time audio analysis

**Scalability:**
- **Resolution scaling**: Linear scaling with resolution
- **Pattern complexity**: Logarithmic scaling with pattern detail
- **Audio reactivity**: Minimal overhead for audio processing

---

## Test Plan

**Unit Tests:**
- [ ] Pattern generation functions produce expected outputs
- [ ] Distortion functions maintain valid UV coordinates
- [ ] Audio reactivity scales correctly with input levels
- [ ] Parameter clamping prevents extreme values
- [ ] Memory allocation stays within limits

**Integration Tests:**
- [ ] Effect processes video frames at target frame rates
- [ ] Audio reactivity responds to real audio input
- [ ] Parameter changes update effect in real-time
- [ ] Effect integrates with AudioReactor correctly
- [ ] Memory usage remains stable over extended operation

**Performance Tests:**
- [ ] 60 FPS sustained at 1080p on target hardware
- [ ] Frame time variance <2ms under load
- [ ] Memory usage <50MB for typical operation
- [ ] Audio processing latency <10ms

**Visual Tests:**
- [ ] Pattern quality meets visual standards
- [ ] Distortion effects appear natural and intentional
- [ ] Audio reactivity creates musically responsive visuals
- [ ] Edge cases produce acceptable fallback behavior

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT124: PatternDistortionEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Based on analysis of VJLive legacy codebases, this effect draws from:
- `core/effects/visualizer.py` for audio-reactive pattern generation
- `core/effects/shader_base.py` for shader integration patterns
- `core/effects/morphology.py` for geometric transformation techniques
- `core/effects/legacy_trash/` for experimental pattern distortion implementations

The implementation follows VJLive's established patterns for real-time visual effects with audio reactivity and parameter-based control.
