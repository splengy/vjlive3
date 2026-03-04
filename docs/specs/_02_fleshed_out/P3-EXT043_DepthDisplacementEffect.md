# Spec: P3-EXT043 — DepthDisplacementEffect

**File naming:** `docs/specs/P3-EXT043_DepthDisplacementEffect.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT043 — DepthDisplacementEffect

**What This Module Does**

DepthDisplacementEffect is a depth-aware pixel displacement effect that uses depth map gradients to drive optical flow simulation. It creates a 3D-like displacement effect by analyzing depth differences between neighboring pixels and applying calculated flow vectors to create a sense of depth-based motion and distortion.

**What This Module Does NOT Do**

- Does not perform actual 3D rendering or geometry manipulation
- Does not create volumetric effects (those are handled by separate volumetric datamosh modules)
- Does not support audio reactivity (depth displacement is purely depth-driven)
- Does not work without depth input (requires depth texture as input)

---

## Detailed Behavior and Parameter Interactions

### Core Algorithm
1. **Depth Gradient Calculation**: For each pixel, calculate depth differences in X and Y directions:
   - `dx = d - texture(texDepth, uv + vec2(0.01, 0.0)).r`
   - `dy = d - texture(texDepth, uv + vec2(0.0, 0.01)).r`

2. **Flow Vector Generation**: Create flow vector based on depth gradient:
   - `vec2 flow = vec2(dx, dy) * strength * 50.0`

3. **Noise Application**: Add pseudo-random noise to flow for chaotic displacement:
   - `flow += (vec2(random(uv + time), random(uv - time)) - 0.5) * noise * 0.1`

4. **Pixel Sampling**: Sample previous frame with offset and current frame:
   - `vec2 lookup = uv - flow`
   - `vec4 prev = texture(texPrev, lookup)`
   - `vec4 curr = texture(tex0, uv)`

5. **Mix Factor Calculation**: Determine blend between previous and current pixels:
   - `float diff = length(flow)`
   - `float mixFactor = smoothstep(thresh, thresh + 0.1, diff)`
   - `mixFactor = max(mixFactor, 0.05)` (minimum refresh)
   - `mixFactor = mix(mixFactor, 1.0, 1.0 - dec)` (decay application)

6. **Final Output**: Blend previous and current pixels:
   - `fragColor = mix(prev, curr, mixFactor)`

### Parameter Interactions
- **Intensity** controls overall displacement strength (0.0-10.0)
- **Scale** affects the magnitude of displacement vectors (0.0-10.0)
- **Speed** controls temporal displacement rate (0.0-10.0)
- **Depth Threshold** determines sensitivity to depth edges (0.0-10.0)
- **Noise Amount** adds chaotic displacement (0.0-10.0)

Higher intensity and scale create more dramatic displacement effects, while higher depth threshold creates sharper transitions between displaced and non-displaced areas.

---

## Public Interface

### Class Definition
```python
class DepthDisplacementEffect(DepthVideoEffect):
    """Depth-driven displacement effect."""
    
    def __init__(self, name: str = 'depth_displacement'):
        super().__init__(name)
        self.parameters['mode'] = 0  # Displacement mode
```

### Parameters
- **intensity**: Overall displacement strength (float, 0.0-10.0, default: 5.0)
- **scale**: Magnitude of displacement vectors (float, 0.0-10.0, default: 1.0)
- **speed**: Temporal displacement rate (float, 0.0-10.0, default: 1.0)
- **depth_threshold**: Sensitivity to depth edges (float, 0.0-10.0, default: 0.5)
- **noise_amount**: Random chaotic displacement (float, 0.0-10.0, default: 0.0)

---

## Inputs and Outputs

### Inputs
- **video_in**: Video texture (required)
- **depth_in**: Depth texture (required)

### Outputs
- **video_out**: Displaced video texture

### Input Requirements
- Depth texture must be single-channel (R) format
- Video and depth textures must have matching resolution
- Depth values should be normalized (0.0-1.0)

---

## Edge Cases and Error Handling

### Edge Cases
1. **Zero Depth Values**: If depth is 0.0, displacement is minimal to avoid artifacts
2. **High Depth Threshold**: If threshold is very high, most pixels will refresh with current frame
3. **Maximum Intensity**: At intensity=10.0, displacement can cause significant pixel smearing
4. **Minimum Parameters**: At all parameters=0.0, effect becomes a simple passthrough

### Error Handling
- If depth texture is not provided, effect falls back to passthrough
- If video texture resolution doesn't match depth texture, effect scales depth to match
- Invalid parameter values are clamped to valid ranges

---

## Mathematical Formulations

### Flow Vector Calculation
```glsl
float dx = d - texture(texDepth, uv + vec2(0.01, 0.0)).r;
float dy = d - texture(texDepth, uv + vec2(0.0, 0.01)).r;
vec2 flow = vec2(dx, dy) * strength * 50.0;
```

### Noise Function
```glsl
float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
}
```

### Mix Factor Calculation
```glsl
float diff = length(flow);
float mixFactor = smoothstep(thresh, thresh + 0.1, diff);
mixFactor = max(mixFactor, 0.05);
mixFactor = mix(mixFactor, 1.0, 1.0 - dec);
```

---

## Performance Characteristics

### Computational Complexity
- **Per-pixel operations**: ~15-20 floating point operations
- **Texture samples**: 4-5 texture samples per pixel (depth, video, previous frame)
- **Memory bandwidth**: Moderate (requires reading previous frame for feedback)

### Performance Optimizations
- Uses single-pass fragment shader
- Depth gradient calculation uses small offsets (0.01) for efficiency
- Noise function is lightweight pseudo-random
- Mix factor calculation uses smoothstep for efficient blending

### Bottlenecks
- Feedback loop requires storing previous frame (memory usage)
- Multiple texture samples can be bandwidth-limited on older hardware
- Complex displacement at high intensity can cause visual artifacts

---

## Test Plan

### Unit Tests
1. **Parameter Clamping**: Test that parameters are clamped to valid ranges
2. **Zero Depth Handling**: Test behavior with depth=0.0
3. **Maximum Parameters**: Test extreme parameter values
4. **Input Validation**: Test behavior with missing/invalid inputs

### Integration Tests
1. **Basic Displacement**: Test with simple depth gradient (ramp)
2. **Edge Detection**: Test with sharp depth edges
3. **Temporal Stability**: Test with moving video input
4. **Performance**: Test at different resolutions and parameter settings

### Visual Tests
1. **Displacement Accuracy**: Verify displacement follows depth gradients
2. **Noise Application**: Verify noise is applied correctly
3. **Mix Factor Behavior**: Verify smooth transitions between displaced and non-displaced areas
4. **Feedback Loop**: Verify temporal stability

**Minimum coverage:** 85% before task is marked done.

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT043: DepthDisplacementEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Based on VJlive v1/v2 implementations:
- Core algorithm from `plugins/vdatamosh/datamosh_3d.py` (lines 289-308)
- Parameter definitions from `plugins/vdatamosh/manifest.json`
- Base class from `core/depth_video.py`
- Shader logic from `core/effects/datamosh_3d.py` fragment shader

**Note:** This effect is part of the vdatamosh plugin system and inherits from Datamosh3DEffect with mode=0 (displacement mode).