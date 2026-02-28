# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD46_Depth_Erosion_Datamosh.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD46 — DepthErosionDatamoshEffect

## Description

The DepthErosionDatamoshEffect applies morphological operations (erosion, dilation, opening, closing) to depth maps, then datamoshes at the morphological boundaries to create organic, cellular dissolution and growth artifacts. The effect creates visuals that appear to biologically eat away at objects or grow from them into the background, following the natural topology of the depth field.

This effect is ideal for creating organic decay, cellular growth, and biological dissolution effects. It's particularly useful for creating "cellular decay" visuals where objects appear to dissolve into organic patterns, or for "growth" effects where new structures emerge from depth boundaries. The effect is highly reactive to audio and can create evolving, organic patterns that respond to music.

## What This Module Does

- Applies morphological operations to depth maps (erosion, dilation, opening, closing)
- Creates organic dissolution and growth artifacts at morphological boundaries
- Generates cellular, biological-looking patterns that eat away at or grow from objects
- Supports multiple effect modes: erosion, dilation, opening, closing
- Includes boundary detection and gradient-based artifact spreading
- Features chromatic morphing and edge-glow effects
- Highly audio-reactive with temporal decay and propagation speed controls
- GPU-accelerated with fragment shader for real-time performance

## What This Module Does NOT Do

- Does NOT perform standard image datamosh (only depth-based)
- Does NOT provide CPU fallback (GPU required)
- Does NOT implement advanced ML-based morphology
- Does NOT store persistent state across sessions
- Does NOT handle camera motion compensation
- Does NOT provide real-time mask refinement beyond basic blur

---

## Detailed Behavior

### Morphological Operations Pipeline

1. **Apply morphological operation**: Based on `morphMode`, apply one of:
   - **Erosion (0)**: Shrinks foreground objects, removes small details
   - **Dilation (1)**: Expands foreground objects, fills small holes
   - **Opening (2)**: Erosion followed by dilation (removes noise)
   - **Closing (3)**: Dilation followed by erosion (fills gaps)

2. **Detect boundaries**: Find edges between morphological regions using gradient detection:
   ```
   boundary = gradient(morphological_result)
   ```

3. **Generate artifacts**: At boundaries, create datamosh artifacts:
   - **Artifact intensity**: Controls strength of datamosh
   - **Boundary width**: Controls how wide the artifact region is
   - **Propagation speed**: Controls how fast artifacts spread
   - **Temporal decay**: Controls how long artifacts persist

4. **Chromatic morphing**: Apply color shifts to artifacts for organic look:
   ```
   artifact_color = base_color + chromatic_shift * artifact_intensity
   ```

5. **Edge glow**: Add glow around boundaries for enhanced visual effect:
   ```
   glow = edge_detection(boundary) * glow_intensity
   ```

### Effect Modes

**Morphological Modes:**
- **Erosion (0)**: Objects dissolve from edges inward
- **Dilation (1)**: Objects grow outward from edges
- **Opening (2)**: Removes small objects, smooths boundaries
- **Closing (3)**: Fills small holes, connects nearby objects

**Visual Effects:**
- **Cellular dissolution**: Objects appear to decay into organic patterns
- **Growth emergence**: New structures grow from depth boundaries
- **Boundary datamosh**: Artifacts appear at morphological edges
- **Chromatic shift**: Color changes create organic look
- **Edge glow**: Enhanced boundaries with glow effects

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `morphMode` | int | 0 | 0-3 | Morphological operation: 0=erosion, 1=dilation, 2=opening, 3=closing |
| `kernelSize` | float | 2.0 | 1.0-10.0 | Size of morphological kernel (larger = stronger effect) |
| `iterations` | float | 1.0 | 1.0-10.0 | Number of times to apply operation (more = stronger) |
| `depthBias` | float | 5.0 | 0.0-10.0 | Depth sensitivity (higher = more depth-based variation) |
| `artifactIntensity` | float | 3.0 | 0.0-10.0 | Strength of datamosh artifacts |
| `boundaryWidth` | float | 4.0 | 1.0-10.0 | Width of artifact boundary region |
| `temporalDecay` | float | 3.0 | 0.0-10.0 | How quickly artifacts fade (higher = longer persistence) |
| `propagationSpeed` | float | 3.0 | 0.0-10.0 | How fast artifacts spread |
| `chromaticMorph` | float | 2.0 | 0.0-10.0 | Strength of color shifting |
| `feedback` | float | 2.0 | 0.0-10.0 | Self-feedback intensity |
| `glowEdges` | float | 1.0 | 0.0-10.0 | Edge glow intensity |

**Inherited from Effect**: `u_mix`, `resolution`, etc.

---

## Public Interface

```python
class DepthErosionDatamoshEffect(Effect):
    def __init__(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def delete(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| **Output** | `np.ndarray` | Depth erosion datamosh frame (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Latest depth frame
- `_depth_texture: int` — GL texture for depth data
- `_morph_mode: int` — Current morphological operation
- `_kernel_size: float` — Morphological kernel size
- `_iterations: float` — Number of iterations
- `_depth_bias: float` — Depth sensitivity
- `_artifact_intensity: float` — Artifact strength
- `_boundary_width: float` — Boundary region width
- `_temporal_decay: float` — Artifact persistence
- `_propagation_speed: float` — Artifact spread speed
- `_chromatic_morph: float` — Color shifting strength
- `_feedback: float` — Self-feedback intensity
- `_glow_edges: float` — Edge glow intensity
- `_shader: ShaderProgram` — Compiled shader
- `_previous_frame: Optional[np.ndarray]` — For temporal effects

**Per-Frame:**
- Update depth data from source
- Apply morphological operation to depth map
- Detect boundaries and generate artifacts
- Apply chromatic morphing and edge glow
- Upload result to GPU
- Render with shader

**Initialization:**
- Create depth texture (lazy)
- Compile shader
- Default parameters from PRESETS (e.g., "gentle_erosion")

**Cleanup:**
- Delete depth texture
- Delete shader
- Call `super().delete()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_RED, GL_UNSIGNED_BYTE | depth_frame size | Updated each frame |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget:**
- Depth texture: W×H×1 byte (e.g., 640×480 = 307,200 bytes)
- Shader: ~10-50 KB
- Total: < 1 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | Skip effect, render original | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Kernel size too large | Clamp to reasonable maximum | Document max kernel size |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and buffer updates must occur on the thread with the OpenGL context. The depth texture is updated each frame, and the shader is used for rendering, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth texture upload: ~0.5-1 ms
- Morphological operation (CPU): ~2-5 ms
- Boundary detection: ~1-2 ms
- Artifact generation: ~1-3 ms
- Total: ~4-10 ms on CPU+GPU

**Optimization Strategies:**
- Reduce `kernel_size` for faster morphology
- Reduce `iterations` for faster processing
- Use separable morphological operations
- Implement morphology in compute shader
- Cache results if depth hasn't changed significantly
- Use lower resolution for morphology, upscale result

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Morphological parameters configured (mode, kernel, iterations)
- [ ] Artifact parameters tuned (intensity, boundary, temporal, propagation)
- [ ] Chromatic and glow effects configured
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | Parameters can be set and clamped |
| `test_get_parameter` | Parameters can be retrieved |
| `test_morphological_operations` | Each morph mode produces expected results |
| `test_kernel_size` | Kernel size affects morphological strength |
| `test_iterations` | Multiple iterations increase effect |
| `test_artifact_generation` | Artifacts appear at boundaries |
| `test_chromatic_morph` | Color shifting creates organic look |
| `test_edge_glow` | Glow enhances boundaries |
| `test_temporal_decay` | Artifacts fade over time |
| `test_propagation_speed` | Artifacts spread at configured speed |
| `test_feedback` | Self-feedback creates recursive effects |
| `test_process_frame_no_depth` | Renders original when no depth |
| `test_process_frame_with_depth` | Applies effect when depth available |
| `test_cleanup` | All GPU resources released |
| `test_no_memory_leak` | Repeated init/cleanup cycles don't leak |

**Minimum coverage:** 85%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD46: depth_erosion_datamosh_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_erosion_datamosh.py` — VJLive Original implementation
- `plugins/core/depth_erosion_datamosh/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthErosionDatamoshEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_erosion_datamosh`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for depth data
- Implements morphological operations on depth maps
- Parameters: `morphMode`, `kernelSize`, `iterations`, `depthBias`, `artifactIntensity`, `boundaryWidth`, `temporalDecay`, `propagationSpeed`, `chromaticMorph`, `feedback`, `glowEdges`
- Allocates GL resources: depth texture
- Shader includes morphological and datamosh operations
- Supports multiple effect modes via `morphMode`

---

## Notes for Implementers

1. **Morphological Operations**: The effect should implement:
   - **Erosion**: Shrinks foreground objects
   - **Dilation**: Expands foreground objects
   - **Opening**: Erosion then dilation (removes noise)
   - **Closing**: Dilation then erosion (fills gaps)
   Use OpenCV or implement custom morphological operations.

2. **Boundary Detection**: After morphological operation, detect boundaries:
   ```python
   # Simple gradient-based boundary detection
   grad_x = cv2.Sobel(morph_result, cv2.CV_32F, 1, 0)
   grad_y = cv2.Sobel(morph_result, cv2.CV_32F, 0, 1)
   grad_mag = np.sqrt(grad_x**2 + grad_y**2)
   boundaries = grad_mag > threshold
   ```

3. **Artifact Generation**: At boundaries, create datamosh artifacts:
   ```python
   # Simple artifact generation
   artifacts = np.random.normal(0, artifact_intensity, morph_result.shape)
   artifacts = artifacts * boundaries
   ```

4. **Chromatic Morphing**: Apply color shifts to artifacts:
   ```python
   # Simple chromatic shift
   artifact_color = base_color + np.random.normal(0, chromatic_morph, base_color.shape)
   ```

5. **Edge Glow**: Add glow around boundaries:
   ```python
   # Simple glow
   glow = cv2.GaussianBlur(boundaries.astype(np.float32), (glow_kernel, glow_kernel), 0)
   glow = glow * glow_intensity
   ```

6. **Temporal Effects**: For `temporalDecay` and `propagationSpeed`, maintain state:
   ```python
   # Simple temporal decay
   if self._previous_artifacts is not None:
       artifacts = (self._previous_artifacts * temporal_decay + new_artifacts) / (temporal_decay + 1)
   ```

7. **Shader Integration**: The shader should handle:
   - Sampling depth texture
   - Applying morphological operations (if done in shader)
   - Generating artifacts
   - Applying chromatic morphing
   - Adding edge glow
   - Mixing with original frame

8. **Performance**: Morphological operations are CPU-intensive. Consider:
   - Using separable operations
   - Reducing resolution for morphology
   - Implementing in compute shader
   - Caching results

9. **Testing**: Create synthetic depth with known objects and verify:
   - Erosion shrinks objects
   - Dilation expands objects
   - Artifacts appear at boundaries
   - Chromatic morphing creates organic look
   - Glow enhances boundaries

10. **Future Extensions**:
    - Add audio-reactive parameters
    - Add depth-based artifact variation
    - Add multiple morphological layers
    - Add real-time parameter animation
    - Add export/import of presets

---

## Easter Egg Idea

When `morphMode` is set exactly to 3.14, `kernelSize` to exactly 3.14, `iterations` to exactly 3.14, and `artifactIntensity` to exactly 3.14, and the depth map contains a perfect circle, the morphological operations spontaneously create a "pi spiral" where artifacts follow a logarithmic spiral pattern for exactly 3.14 seconds before returning to normal cellular decay. The effect creates a mathematical resonance that VJs can feel as a "sacred geometry" pattern.

---

## References

- Morphological operations: https://en.wikipedia.org/wiki/Mathematical_morphology
- Erosion/dilation: https://docs.opencv.org/master/d9/d61/tutorial_py_morphological_ops.html
- Datamosh: https://en.wikipedia.org/wiki/Datamosh
- VJLive legacy: `plugins/vdepth/depth_erosion_datamosh.py`

---

## Implementation Tips

1. **OpenCV Implementation**:
   ```python
   import cv2
   
   def apply_morphology(depth_frame, morph_mode, kernel_size, iterations):
       kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
       
       if morph_mode == 0:  # Erosion
           return cv2.erode(depth_frame, kernel, iterations=iterations)
       elif morph_mode == 1:  # Dilation
           return cv2.dilate(depth_frame, kernel, iterations=iterations)
       elif morph_mode == 2:  # Opening
           return cv2.morphologyEx(depth_frame, cv2.MORPH_OPEN, kernel, iterations=iterations)
       elif morph_mode == 3:  # Closing
           return cv2.morphologyEx(depth_frame, cv2.MORPH_CLOSE, kernel, iterations=iterations)
   ```

2. **Boundary Detection**:
   ```python
   def detect_boundaries(morph_result):
       grad_x = cv2.Sobel(morph_result, cv2.CV_32F, 1, 0, ksize=3)
       grad_y = cv2.Sobel(morph_result, cv2.CV_32F, 0, 1, ksize=3)
       grad_mag = np.sqrt(grad_x**2 + grad_y**2)
       return grad_mag > 0.1  # Simple threshold
   ```

3. **Artifact Generation**:
   ```python
   def generate_artifacts(boundaries, intensity):
       artifacts = np.random.normal(0, intensity, boundaries.shape)
       return artifacts * boundaries
   ```

4. **Chromatic Morphing**:
   ```python
   def apply_chromatic_morph(base_color, intensity):
       shift = np.random.normal(0, intensity, base_color.shape)
       return np.clip(base_color + shift, 0, 255)
   ```

5. **Edge Glow**:
   ```python
   def add_edge_glow(boundaries, intensity, kernel_size):
       glow = cv2.GaussianBlur(boundaries.astype(np.float32), (kernel_size, kernel_size), 0)
       return glow * intensity
   ```

6. **Shader Integration**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;        // Video input
   uniform sampler2D depth_tex;   // Depth texture
   uniform vec2 resolution;
   uniform float u_mix;
   uniform int morphMode;         // 0-3
   uniform float kernelSize;      // 1.0-10.0
   uniform float iterations;      // 1.0-10.0
   uniform float depthBias;       // 0.0-10.0
   uniform float artifactIntensity; // 0.0-10.0
   uniform float boundaryWidth;   // 1.0-10.0
   uniform float temporalDecay;   // 0.0-10.0
   uniform float propagationSpeed; // 0.0-10.0
   uniform float chromaticMorph;  // 0.0-10.0
   uniform float feedback;        // 0.0-10.0
   uniform float glowEdges;       // 0.0-10.0
   
   // Morphological operations, boundary detection, artifact generation, etc.
   ```

7. **PRESETS**: Define useful presets:
   ```python
   PRESETS = {
       "gentle_erosion": {
           "morphMode": 0.0, "kernelSize": 2.0, "iterations": 1.0, "depthBias": 5.0,
           "artifactIntensity": 3.0, "boundaryWidth": 4.0, "temporalDecay": 3.0,
           "propagationSpeed": 3.0, "chromaticMorph": 2.0, "feedback": 2.0,
           "glowEdges": 1.0,
       },
       "aggressive_growth": {
           "morphMode": 1.0, "kernelSize": 5.0, "iterations": 3.0, "depthBias": 8.0,
           "artifactIntensity": 7.0, "boundaryWidth": 6.0, "temporalDecay": 1.0,
           "propagationSpeed": 7.0, "chromaticMorph": 5.0, "feedback": 5.0,
           "glowEdges": 3.0,
       },
   }
   ```

---

## Conclusion

The DepthErosionDatamoshEffect creates organic, cellular dissolution and growth effects by combining morphological operations with datamosh artifacts. It transforms depth maps into evolving, biological-looking patterns that can dissolve objects or grow new structures, making it a powerful tool for creating organic, evolving visuals in VJ performances.

---
>>>>>>> REPLACE