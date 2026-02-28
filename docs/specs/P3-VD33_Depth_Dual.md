# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD33_Depth_Dual.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD33 — DepthDualEffect

## Description

The Depth Dual effect is the first VJ effect designed for dual depth camera setups. It accepts two independent depth inputs from any combination of depth cameras (Kinect, RealSense, Face ID, Surface, etc.) and combines them using one of six interaction modes: Collision, Interference, Difference, Volumetric, XOR, or Parallax. This enables advanced 3D scene reconstruction, stereoscopic effects, and volumetric visualization by fusing depth data from multiple viewpoints.

The effect is essential for multi-camera depth setups where you want to create a more complete 3D representation, detect occlusions, or generate stereoscopic output. Each mode implements a different mathematical combination of the two depth fields, producing distinct visual results ranging from "where surfaces meet" to "exclusive visibility zones."

## What This Module Does

- Accepts two independent depth sources (`depth_source_a` and `depth_source_b`)
- Provides six interaction modes that combine the two depth fields in different ways
- Supports mixing between the original video and the processed result
- Integrates with `DepthEffect` base class for depth source management
- Uses GPU-accelerated fragment shaders for real-time performance at 60 FPS
- Handles depth texture lifecycle for both sources
- Allows audio reactivity to modulate interaction parameters

## What This Module Does NOT Do

- Does NOT perform camera calibration or depth alignment (assumes depth maps are already registered)
- Does NOT generate depth maps (requires two external `AstraDepthSource` providers)
- Does NOT support more than two depth inputs (dual only)
- Does NOT provide CPU fallback (requires GPU for shader-based processing)
- Does NOT manage node graph connections (caller must route both depth sources)
- Does NOT store persistent state across sessions (all parameters in-memory)
- Does NOT implement advanced 3D reconstruction (only depth field combination)

---

## Detailed Behavior

### Dual Depth Sources

The effect requires two separate depth sources, each providing a depth map. These can come from:
- Two different depth cameras (e.g., two Kinects, or Kinect + RealSense)
- The same camera with different viewpoints (stereo pair)
- A depth camera and a simulated depth source (e.g., from a 3D model)
- Any combination as long as the depth maps are spatially aligned

Both depth sources are updated each frame via `update_depth_data()` calls.

### Interaction Modes

The six modes define how the two depth fields are combined:

1. **Collision** (`mode = "collision"`):
   - Highlights regions where the two depth fields meet or intersect
   - Useful for detecting where objects from two viewpoints overlap
   - Implementation: `result = min(depth_a, depth_b)` or `smoothstep` on difference
   - Visual: Bright/colored where depths are similar, dark where they differ

2. **Interference** (`mode = "interference"`):
   - Creates wave-like interference patterns from the depth overlay
   - Simulates volumetric interference fringes
   - Implementation: `result = sin((depth_a - depth_b) * frequency) * amplitude`
   - Visual: Moiré-like patterns, concentric rings

3. **Difference** (`mode = "difference"`):
   - Shows the absolute difference between the two depth fields
   - Reveals occlusions and depth discrepancies
   - Implementation: `result = abs(depth_a - depth_b)`
   - Visual: Bright where depths differ, dark where they match

4. **Volumetric** (`mode = "volumetric"`):
   - Attempts crude volume rendering by treating depth difference as density
   - Creates a pseudo-3D volumetric effect
   - Implementation: `result = depth_a * depth_b` or similar multiplication
   - Visual: Fog-like, with denser regions where both depths are high

5. **XOR** (`mode = "xor"`):
   - Exclusive visibility: shows regions that are visible in only one depth field
   - Implementation: `result = max(depth_a, depth_b) - min(depth_a, depth_b)` or logical XOR
   - Visual: Highlights areas where one camera sees something the other doesn't

6. **Parallax** (`mode = "parallax"`):
   - Simulates stereoscopic reconstruction by computing depth from disparity
   - Implementation: `result = depth_a / (depth_b + epsilon)` or inverse relationship
   - Visual: Creates a sense of 3D depth from two viewpoints

### Processing Pipeline

Each frame:

1. **Depth Fetch**: Sample depth maps from both sources (`depth_a`, `depth_b`)
2. **Mode Selection**: Based on `interaction_mode` parameter, compute combined depth:
   - Collision: `combined = smoothstep(threshold - width, threshold + width, abs(depth_a - depth_b))`
   - Interference: `combined = 0.5 + 0.5 * sin((depth_a - depth_b) * frequency)`
   - Difference: `combined = abs(depth_a - depth_b)`
   - Volumetric: `combined = depth_a * depth_b`
   - XOR: `combined = max(depth_a, depth_b) - min(depth_a, depth_b)`
   - Parallax: `combined = depth_a / (depth_b + 0.001)`
3. **Colorization**: Map the combined depth value to a color (grayscale or false-color)
4. **Blend**: Mix with original video frame using `u_mix` parameter

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `interaction_mode` | str | "collision" | "collision", "interference", "difference", "volumetric", "xor", "parallax" | How to combine the two depth fields |
| `threshold` | float | 0.1 | 0.0 - 1.0 | Threshold for collision mode (similarity threshold) |
| `frequency` | float | 10.0 | 1.0 - 100.0 | Frequency for interference mode (wave density) |
| `amplitude` | float | 1.0 | 0.0 - 2.0 | Amplitude for interference mode (contrast) |
| `colorize` | bool | False | — | If true, apply false-color to combined depth |
| `colormap` | str | "thermal" | "thermal", "rainbow", "depth", "mono" | Color palette when colorize=true |
| `invert` | bool | False | — | Invert the combined depth values |
| `blend` | float | 0.8 | 0.0 - 1.0 | Blend factor between original and processed output |

---

## Public Interface

```python
class DepthDualEffect:
    def __init__(self) -> None: ...
    def set_depth_source_a(self, source) -> None: ...
    def set_depth_source_b(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_audio_analyzer(self, audio_analyzer) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame` | `np.ndarray` | Input video frame (HWC, 3 or 4 channels) | dtype: uint8 or float32 |
| `depth_source_a` | `AstraDepthSource` | First depth map provider | Must implement `get_depth_frame()` |
| `depth_source_b` | `AstraDepthSource` | Second depth map provider | Must implement `get_depth_frame()` |
| `audio_analyzer` | `AudioAnalyzer` | Optional audio feature source | Provides BEAT_INTENSITY, TEMPO, ENERGY |

**Output**: `np.ndarray` — Processed frame with dual-depth interaction applied, same shape/format as input

---

## State Management

**Persistent State:**
- `parameters: dict` — Current parameter values (see table above)
- `_depth_source_a: Optional[AstraDepthSource]` — First depth map provider
- `_depth_source_b: Optional[AstraDepthSource]` — Second depth map provider
- `_depth_frame_a: Optional[np.ndarray]` — Cached depth map from source A
- `_depth_frame_b: Optional[np.ndarray]` — Cached depth map from source B
- `_depth_texture_a: int` — OpenGL texture ID for depth A
- `_depth_texture_b: int` — OpenGL texture ID for depth B
- `_shader: ShaderProgram` — Compiled fragment shader
- `_frame_width: int` — Current frame width
- `_frame_height: int` — Current frame height

**Per-Frame State:**
- Temporary shader uniform values
- Intermediate framebuffer bindings

**Initialization:**
- Depth textures created on first `update_depth_data()` or `process_frame()`
- Shader compiled in `__init__()`

**Cleanup:**
- Delete both depth textures (`glDeleteTextures`)
- Delete shader program

---

## GPU Resources

| Resource | Type | Format | Dimensions | Count |
|----------|------|--------|------------|-------|
| Depth texture A | GL_TEXTURE_2D | GL_R8 or GL_RGBA8 | frame size | 1 |
| Depth texture B | GL_TEXTURE_2D | GL_R8 or GL_RGBA8 | frame size | 1 |
| Main shader | GLSL program | vertex + fragment | N/A | 1 |

**Memory Budget (1080p):**
- 2 × depth textures: 2 × 2.1 MB = ~4.2 MB (GL_R8)
- Total: ~4.2 MB + shader overhead

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth source A not set | `RuntimeError("No depth source A")` | Call `set_depth_source_a()` before processing |
| Depth source B not set | `RuntimeError("No depth source B")` | Call `set_depth_source_b()` before processing |
| Depth frame missing from A | `RuntimeError("Depth data A not available")` | Ensure source A is providing frames |
| Depth frame missing from B | `RuntimeError("Depth data B not available")` | Ensure source B is providing frames |
| Shader compilation failure | `ShaderCompilationError` | Log error, effect becomes no-op |
| Texture creation fails | `RuntimeError` | Propagate to caller; may indicate out of GPU memory |
| Invalid interaction_mode | `ValueError("Invalid mode")` | Validate against allowed modes |
| Resolution mismatch between depth sources | Undefined behavior | Ensure both sources provide same resolution or handle resizing |
| `threshold` out of range | Clamped to [0,1] | Document valid range; optionally clamp |
| `frequency` too high | Aliasing artifacts | Warn if `frequency > 50` |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations must occur on the thread owning the OpenGL context. The `_depth_frame_a` and `_depth_frame_b` caches are per-instance and mutated each frame, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (1080p):**
- Two depth texture fetches: ~0.5 ms
- Mode-specific computation (varies):
  - Collision: ~0.5 ms (simple comparison)
  - Interference: ~1 ms (sin function)
  - Difference: ~0.3 ms (absolute difference)
  - Volumetric: ~0.5 ms (multiplication)
  - XOR: ~0.3 ms (max-min)
  - Parallax: ~0.5 ms (division)
- Colorization (if enabled): ~0.5 ms
- Total: ~1-2 ms on discrete GPU, ~3-5 ms on integrated GPU

**Optimization Strategies:**
- Use `GL_R8` for depth textures to minimize memory bandwidth
- Early-out if both depth sources haven't changed (cache frame counters)
- Precompute mode-specific constants (e.g., `sin_lookup` for interference) if frequency is fixed
- If `colorize=false`, skip color LUT lookup

---

## Integration Checklist

- [ ] Both depth sources are connected via `set_depth_source_a()` and `set_depth_source_b()` before processing
- [ ] Depth maps from both sources have matching resolutions (or effect handles resizing)
- [ ] Depth maps are spatially aligned (same viewpoint or registered)
- [ ] Shader compiles successfully on all target platforms
- [ ] Parameters are validated before being sent to shader
- [ ] `cleanup()` is called when effect is destroyed to release GPU resources
- [ ] Pipeline orchestrator calls `update_depth_data()` each frame to refresh both depth textures

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect instantiates without errors |
| `test_set_depth_sources` | Both depth sources are stored correctly |
| `test_update_depth_data` | Both depth textures are created/updated with valid data |
| `test_process_frame_missing_a` | Raises error if depth source A not set |
| `test_process_frame_missing_b` | Raises error if depth source B not set |
| `test_collision_mode` | Collision mode produces expected output (high where depths match) |
| `test_interference_mode` | Interference mode creates wave patterns |
| `test_difference_mode` | Difference mode shows absolute depth difference |
| `test_volumetric_mode` | Volumetric mode multiplies depths |
| `test_xor_mode` | XOR mode highlights exclusive regions |
| `test_parallax_mode` | Parallax mode computes ratio of depths |
| `test_colorization` | When enabled, applies colormap to combined depth |
| `test_invert` | Invert flag reverses combined depth values |
| `test_cleanup` | All GPU resources released |
| `test_audio_reactivity` | Audio features can modulate parameters if reactor connected |

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD33: depth_dual` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_dual.py` — Original VJLive implementation
- `plugins/core/depth_dual/__init__.py` — VJLive-2 version
- `plugins/vdepth/__init__.py` — Registration in depth plugin module
- `gl_leaks.txt` — Notes on texture allocation (missing `glDeleteTextures`)

Design decisions inherited:
- Effect name: `"depth_dual"`
- Six interaction modes: collision, interference, difference, volumetric, xor, parallax
- Parameters: `threshold`, `frequency`, `amplitude`, `colorize`, `colormap`, `invert`
- Uses `DEPTH_DUAL_FRAGMENT` shader
- Dual depth source architecture: `depth_source_a` and `depth_source_b`
- Texture resource management: allocates with `glGenTextures`, must free with `glDeleteTextures` (noted as missing in legacy)
- Inherits from base `Effect` class (not `DepthEffect` specifically, though it uses depth sources)

---

## Notes for Implementers

1. **Depth Alignment**: The two depth maps must be spatially aligned (same camera viewpoint or registered). If they come from different cameras, the caller must ensure proper alignment before passing to this effect. The effect does not perform any warping or registration.

2. **Mode Implementations**:
   - **Collision**: Use a smooth threshold: `float diff = abs(depth_a - depth_b); float collision = 1.0 - smoothstep(threshold - width, threshold + width, diff);`
   - **Interference**: `float interference = 0.5 + 0.5 * sin((depth_a - depth_b) * frequency * 3.14159 * 2.0);`
   - **Difference**: `float diff = abs(depth_a - depth_b);`
   - **Volumetric**: `float vol = depth_a * depth_b;` (may need scaling)
   - **XOR**: `float xor = max(depth_a, depth_b) - min(depth_a, depth_b);`
   - **Parallax**: `float parallax = depth_a / (depth_b + 0.001);` (clamp result to reasonable range)

3. **Colorization**: When `colorize=true`, map the combined depth value (0-1) through a 1D colormap texture. Provide at least three palettes: thermal (black→red→yellow→white), rainbow (blue→green→red), and mono (grayscale).

4. **Performance**: The effect should be very fast since it only does a few arithmetic operations per pixel. The bottleneck will be texture fetches. Use `GL_R8` for depth textures.

5. **Audio Reactivity**: Consider mapping audio features to parameters:
   - `BEAT_INTENSITY` → `amplitude` (beats increase interference strength)
   - `ENERGY` → `frequency` (high energy increases wave density)
   - `TEMPO` → `threshold` (tempo shifts collision threshold)

6. **Edge Cases**: Handle cases where one or both depth values are invalid (NaN or outside 0-1). Typically, depth cameras return 0 for no data. Decide whether to treat 0 as "far" or "invalid" and document.

7. **Testing**: Create synthetic depth pairs:
   - Two identical gradients → collision should be all 1, difference all 0
   - One gradient, one constant → difference shows gradient magnitude
   - Two offset gradients → parallax shows constant ratio

8. **Resource Management**: The legacy code notes missing `glDeleteTextures`. Ensure your `cleanup()` deletes both depth textures.

9. **Shader Precision**: Use `highp float` for depth calculations to avoid precision issues, especially for parallax division.

10. **Extensibility**: Future modes could be added by extending the shader with `#define` or uniform enum. Design the shader to be easily modifiable.

---

## Easter Egg Idea

When `interaction_mode` is set to "collision", `threshold` exactly to 0.333, `frequency` exactly to 3.33, and both depth sources provide perfectly aligned gradients, the collision pattern briefly forms a hidden "double helix" structure that lasts exactly 6.66 seconds before returning to normal. The helix is visible only in the combined depth's alpha channel and requires a debug view to see, but subtly influences the final output in a way that VJs can feel rather than see.

---

## References

- VJLive1 legacy codebase: `vjlive1/plugins/depth_dual.py` (if exists)
- Stereoscopic depth: https://en.wikipedia.org/wiki/Stereoscopy
- Depth map fusion: https://en.wikipedia.org/wiki/Depth_fusion
- ShaderToy depth experiments: https://www.shadertoy.com/view/4dlyR4

---

## Implementation Tips

1. **Shader Structure**:
   ```glsl
   uniform sampler2D u_depth_a;
   uniform sampler2D u_depth_b;
   uniform int u_mode; // 0=collision, 1=interference, 2=difference, 3=volumetric, 4=xor, 5=parallax
   uniform float u_threshold;
   uniform float u_frequency;
   uniform float u_amplitude;
   uniform bool u_colorize;
   uniform int u_colormap; // 0=thermal, 1=rainbow, 2=depth, 3=mono
   uniform bool u_invert;
   
   void main() {
       float da = texture(u_depth_a, uv).r;
       float db = texture(u_depth_b, uv).r;
       float combined = 0.0;
       
       if (u_mode == 0) { // collision
           float diff = abs(da - db);
           combined = 1.0 - smoothstep(u_threshold - 0.05, u_threshold + 0.05, diff);
       } else if (u_mode == 1) { // interference
           combined = 0.5 + 0.5 * sin((da - db) * u_frequency * 6.28318);
       } else if (u_mode == 2) { // difference
           combined = abs(da - db);
       } else if (u_mode == 3) { // volumetric
           combined = da * db;
       } else if (u_mode == 4) { // xor
           combined = max(da, db) - min(da, db);
       } else if (u_mode == 5) { // parallax
           combined = da / (db + 0.001);
           combined = clamp(combined, 0.0, 1.0);
       }
       
       if (u_invert) combined = 1.0 - combined;
       
       vec3 color = u_colorize ? apply_colormap(combined, u_colormap) : vec3(combined);
       fragColor = mix(source, vec4(color, 1.0), u_mix);
   }
   ```

2. **Mode Switching**: Use a uniform integer for mode to avoid string comparisons in shader. The Python side maps mode names to integers.

3. **Colormap**: Implement colormap as a 1D texture or as a series of `if` statements for small palettes. For performance, precompute a 256-entry LUT.

4. **Debugging**: Provide a debug mode that outputs the raw combined depth as grayscale to verify mode behavior.

5. **Resource Management**: Both depth textures must be deleted in `cleanup()`. Also delete any colormap LUT texture if created.

6. **Testing**: Write unit tests for each mode with known depth pairs to verify correct output.

---
>>>>>>> REPLACE