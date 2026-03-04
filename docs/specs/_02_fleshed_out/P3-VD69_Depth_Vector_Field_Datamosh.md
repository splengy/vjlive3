# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD69_Depth_Vector_Field_Datamosh.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD69 — DepthVectorFieldDatamoshEffect

## Description

The DepthVectorFieldDatamoshEffect is "THE MISSING LINK" — the purest algorithmic marriage of depth camera data and classic datamosh P-frame propagation. Frame-to-frame depth deltas become the motion vectors that drive datamosh. Where depth is changing, pixels smear. Where depth is static, pixels hold. The depth camera's temporal changes literally ARE the datamosh vectors.

This effect creates a unique datamosh where the depth camera's own temporal changes drive the corruption. It's ideal for creating organic, depth-aware datamosh effects where the depth camera's movement and scene changes create natural-looking temporal artifacts. The effect can simulate everything from subtle smearing to dramatic block corruption.

## What This Module Does

- Computes frame-to-frame depth deltas (temporal depth changes)
- Uses depth deltas as motion vectors for datamosh propagation
- Where depth changes: pixels smear along motion vectors
- Where depth is static: pixels hold (no smearing)
- Classic P-frame datamosh propagation using depth vectors
- Configurable vector scale, temporal blend, and propagation decay
- Depth threshold for motion detection
- Block-based corruption with chaos factor
- GPU-accelerated with multiple history buffers

## What This Module Does NOT Do

- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT include audio reactivity (may be added later)
- Does NOT implement true optical flow (uses simple depth deltas)
- Does NOT support arbitrary vector fields (only depth-based)
- Does NOT include motion compensation (raw depth deltas)

---

## Detailed Behavior

### Vector Field Datamosh Pipeline

1. **Capture current frame**: `current_frame` (HxWxC)
2. **Capture current depth**: `current_depth` (HxW, normalized 0-1)
3. **Maintain history**: Store previous frame and depth
4. **Compute depth deltas**: `depth_delta = current_depth - previous_depth`
5. **Compute motion vectors**: `motion_vector = depth_delta * vectorScale`
6. **For each pixel**:
   - If `|depth_delta| > depthThreshold`: apply datamosh
   - Else: hold pixel (no change)
7. **Datamosh propagation**: Use motion vectors to smear pixels
8. **Temporal blending**: Blend with previous datamosh result
9. **Block corruption**: Apply block-based corruption with chaos
10. **Composite**: Mix with original via `u_mix`

### Depth Delta Computation

The core concept: depth changes over time become motion vectors.

```glsl
float current_depth = texture(current_depth_tex, uv).r;
float previous_depth = texture(previous_depth_tex, uv).r;
float depth_delta = current_depth - previous_depth;

// Only consider significant changes
if (abs(depth_delta) > depthThreshold) {
    // This pixel has depth motion
    vec2 motion_vector = vec2(depth_delta * vectorScale, 0.0);
    // Apply datamosh using this vector
}
```

### Motion Vector Field

The depth delta field becomes a 2D vector field:

```glsl
vec2 vector_field(vec2 uv) {
    float depth = texture(current_depth_tex, uv).r;
    float prev_depth = texture(previous_depth_tex, uv).r;
    float delta = depth - prev_depth;
    
    if (abs(delta) > depthThreshold) {
        // Scale delta to create vector
        vec2 vector = vec2(delta * vectorScale, 0.0);
        // Could also use vertical component for 2D vectors
        return vector;
    } else {
        return vec2(0.0);  // No motion
    }
}
```

### Datamosh Propagation

Use motion vectors to propagate pixel values:

```glsl
vec2 motion = vector_field(uv);
vec2 sample_uv = uv - motion * temporalBlend;
vec4 color = texture(current_tex, sample_uv);
```

### Block Corruption

Apply block-based corruption where depth is changing:

```glsl
if (abs(depth_delta) > depthThreshold) {
    // Block corruption
    vec2 block_coord = floor(uv * blockSize) / blockSize;
    vec2 block_motion = motion * blockChaos;
    vec2 block_uv = block_coord + block_motion;
    color = texture(current_tex, block_uv);
    
    // Add some chaos: random block shifts
    if (random(uv) < blockChaos * 0.1) {
        color = texture(current_tex, uv + vec2(random(uv) - 0.5, random(uv.yx) - 0.5));
    }
}
```

### Temporal Blending

Blend current datamosh with previous result for persistence:

```glsl
vec4 previous_result = texture(previous_result_tex, uv);
vec4 final = mix(color, previous_result, temporalBlend);
```

### Propagation Decay

Decay the effect over time to prevent infinite propagation:

```glsl
float decay = exp(-propagationDecay * time);
final = mix(final, current_color, decay);
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `vectorScale` | float | 3.0 | 0.0-10.0 | Scale of depth-based motion vectors |
| `temporalBlend` | float | 3.0 | 0.0-10.0 | Temporal persistence of datamosh |
| `propagationDecay` | float | 2.0 | 0.0-10.0 | How quickly datamosh decays over time |
| `depthThreshold` | float | 5.0 | 0.0-10.0 | Minimum depth change to trigger datamosh |
| `blockSize` | float | 5.0 | 1.0-20.0 | Size of corruption blocks |
| `blockChaos` | float | 1.0 | 0.0-10.0 | Randomness in block corruption |

**Inherited from Effect**: `u_mix`

---

## Public Interface

```python
class DepthVectorFieldDatamoshEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def clear_history(self) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| **Output** | `np.ndarray` | Vector field datamosh output (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Current depth frame
- `_previous_depth_frame: Optional[np.ndarray]` — Previous depth frame
- `_previous_result: Optional[np.ndarray]` — Previous datamosh result
- `_parameters: dict` — Vector field parameters
- `_shader: ShaderProgram` — Compiled shader
- `_temp_texture: int` — For intermediate rendering

**Per-Frame:**
- Update depth data from source
- Compute depth deltas from previous depth
- Render datamosh effect using depth-based motion vectors
- Store current result as previous for next frame
- Return result

**Initialization:**
- Compile shader
- Default parameters: vectorScale=3.0, temporalBlend=3.0, propagationDecay=2.0, depthThreshold=5.0, blockSize=5.0, blockChaos=1.0
- Initialize `_previous_depth_frame = None`, `_previous_result = None`

**Cleanup:**
- Delete temporary textures
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Shader: ~20-30 KB
- No large textures (uses current frame only)
- Total: ~30 KB (lightweight)

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| No depth source | Use uniform depth (0.5) | Normal operation |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| First frame (no previous) | Use current frame as result | Normal operation |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations, texture updates, and shader operations must occur on the thread with the OpenGL context. The effect maintains state between frames (previous depth, previous result); concurrent `process_frame()` calls will cause race conditions and corrupted datamosh. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Shader execution (depth delta computation, datamosh propagation): ~2-5 ms
- Total: ~2-5 ms on GPU (very lightweight)

**Optimization Strategies:**
- Use lower resolution for depth processing
- Simplify block corruption (no chaos, fixed blocks)
- Use simpler motion vector computation
- Early depth test to skip static regions

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Vector field parameters configured
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_depth_delta` | Depth deltas computed correctly |
| `test_vector_scale` | Vector scale affects motion magnitude |
| `test_temporal_blend` | Temporal persistence works |
| `test_propagation_decay` | Decay reduces effect over time |
| `test_depth_threshold` | Only significant depth changes trigger datamosh |
| `test_block_corruption` | Block-based corruption applied |
| `test_block_chaos` | Chaos adds randomness to corruption |
| `test_first_frame` | Handles first frame without previous depth |
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
- [ ] Git commit with `[Phase-3] P3-VD69: depth_vector_field_datamosh_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_vector_field_datamosh.py` — VJLive Original implementation
- `plugins/core/depth_vector_field_datamosh/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_vector_field_datamosh/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthVectorFieldDatamoshEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_vector_field_datamosh`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for motion vector computation
- Parameters: `vectorScale`, `temporalBlend`, `propagationDecay`, `depthThreshold`, `blockSize`, `blockChaos`
- Allocates GL resources: temporary textures for intermediate rendering
- Shader implements depth delta computation, motion vector field, datamosh propagation, block corruption
- Method `_ensure_textures()` creates GPU resources
- Presets: "subtle_approach"

---

## Notes for Implementers

1. **Core Concept**: This effect uses the depth camera's own temporal changes as motion vectors for datamosh. Where depth changes between frames, pixels smear along the depth delta. Where depth is static, pixels hold. This creates a natural, depth-aware datamosh that responds to scene movement.

2. **Depth Delta as Motion**:
   ```glsl
   float depth = texture(current_depth_tex, uv).r;
   float prev_depth = texture(previous_depth_tex, uv).r;
   float delta = depth - prev_depth;
   
   if (abs(delta) > depthThreshold) {
       // This pixel has depth motion
       vec2 motion = vec2(delta * vectorScale, 0.0);
       // Use motion to smear pixel
   }
   ```

3. **Motion Vector Field**: The depth delta field becomes a 2D vector field. Could be 1D (horizontal only) or 2D (both components). The legacy uses horizontal motion (x-axis).

4. **Datamosh Propagation**: Use motion vectors to sample from current frame at displaced positions:
   ```glsl
   vec2 motion = vector_field(uv);
   vec2 sample_uv = uv - motion * temporalBlend;
   vec4 color = texture(current_tex, sample_uv);
   ```

5. **Block Corruption**: Where depth is changing, apply block-based corruption:
   ```glsl
   if (abs(delta) > depthThreshold) {
       vec2 block_coord = floor(uv * blockSize) / blockSize;
       vec2 block_motion = motion * blockChaos;
       vec2 block_uv = block_coord + block_motion;
       color = texture(current_tex, block_uv);
   }
   ```

6. **Temporal Blending**: Blend current result with previous to create persistence:
   ```glsl
   vec4 previous = texture(previous_result_tex, uv);
   vec4 final = mix(color, previous, temporalBlend);
   ```

7. **Propagation Decay**: Prevent infinite propagation:
   ```glsl
   float decay = exp(-propagationDecay * time);
   final = mix(final, current_color, decay);
   ```

8. **Shader Uniforms**:
   ```glsl
   uniform sampler2D current_tex;
   uniform sampler2D depth_tex;
   uniform sampler2D previous_depth_tex;
   uniform sampler2D previous_result_tex;
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float vectorScale;        // 0-10
   uniform float temporalBlend;       // 0-10
   uniform float propagationDecay;    // 0-10
   uniform float depthThreshold;      // 0-10
   uniform float blockSize;           // 1-20
   uniform float blockChaos;          // 0-10
   ```

9. **Parameter Mapping**:
   - `vectorScale`: 0-10 → 0-1 (divide by 10)
   - `temporalBlend`: 0-10 → 0-1 (divide by 10)
   - `propagationDecay`: 0-10 → 0-1 (divide by 10)
   - `depthThreshold`: 0-10 → 0-1 (divide by 10)
   - `blockSize`: 1-20 → pixels (use directly)
   - `blockChaos`: 0-10 → 0-1 (divide by 10)

10. **PRESETS**:
    ```python
    PRESETS = {
        "subtle_approach": {
            "vectorScale": 3.0, "temporalBlend": 3.0, "propagationDecay": 2.0,
            "depthThreshold": 5.0, "blockSize": 5.0, "blockChaos": 1.0,
        },
        "aggressive_datamosh": {
            "vectorScale": 8.0, "temporalBlend": 6.0, "propagationDecay": 1.0,
            "depthThreshold": 3.0, "blockSize": 3.0, "blockChaos": 5.0,
        },
        "smooth_propagation": {
            "vectorScale": 2.0, "temporalBlend": 8.0, "propagationDecay": 4.0,
            "depthThreshold": 6.0, "blockSize": 8.0, "blockChaos": 2.0,
        },
        "block_chaos": {
            "vectorScale": 5.0, "temporalBlend": 4.0, "propagationDecay": 2.0,
            "depthThreshold": 4.0, "blockSize": 4.0, "blockChaos": 8.0,
        },
        "minimal_motion": {
            "vectorScale": 1.0, "temporalBlend": 2.0, "propagationDecay": 3.0,
            "depthThreshold": 8.0, "blockSize": 10.0, "blockChaos": 0.5,
        },
    }
    ```

11. **Testing Strategy**:
    - Test with uniform depth: no datamosh should occur
    - Test with depth gradient: datamosh should follow depth changes
    - Test vectorScale: higher = more smearing
    - Test temporalBlend: higher = more persistence
    - Test propagationDecay: higher = faster decay
    - Test depthThreshold: higher = less sensitive to changes
    - Test blockSize: larger = bigger corruption blocks
    - Test blockChaos: higher = more random corruption

12. **Performance**: Very lightweight — only current frame and depth processing. Should be very fast.

13. **Memory**: Minimal — no large history buffers needed. Only temporary textures for intermediate rendering.

14. **Debug Mode**: Visualize depth deltas (color-coded), show motion vectors, display corruption blocks.

---
-

## References

- Datamosh: https://en.wikipedia.org/wiki/Datamosh
- Motion estimation: https://en.wikipedia.org/wiki/Motion_estimation
- Depth buffer: https://en.wikipedia.org/wiki/Depth_buffer
- VJLive legacy: `plugins/vdepth/depth_vector_field_datamosh.py`

---

## Implementation Tips

1. **Full Shader**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D current_tex;
   uniform sampler2D depth_tex;
   uniform sampler2D previous_depth_tex;
   uniform sampler2D previous_result_tex;
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float vectorScale;        // 0-10
   uniform float temporalBlend;       // 0-10
   uniform float propagationDecay;    // 0-10
   uniform float depthThreshold;      // 0-10
   uniform float blockSize;           // 1-20
   uniform float blockChaos;          // 0-10
   
   // Simple pseudo-random
   float random(vec2 uv) {
       return fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453);
   }
   
   void main() {
       float depth = texture(depth_tex, uv).r;
       float prev_depth = texture(previous_depth_tex, uv).r;
       float delta = depth - prev_depth;
       
       vec4 color = texture(current_tex, uv);
       
       // Check if depth change is significant
       if (abs(delta) > depthThreshold * 0.1) {
           // Compute motion vector
           vec2 motion = vec2(delta * vectorScale * 0.1, 0.0);
           
           // Apply temporal blending
           vec2 sample_uv = uv - motion * temporalBlend * 0.1;
           color = texture(current_tex, sample_uv);
           
           // Apply block corruption
           if (blockSize > 1.0) {
               vec2 block_coord = floor(uv * blockSize) / blockSize;
               vec2 block_motion = motion * blockChaos * 0.1;
               vec2 block_uv = block_coord + block_motion;
               color = texture(current_tex, block_uv);
               
               // Add chaos
               if (random(uv) < blockChaos * 0.01) {
                   color = texture(current_tex, uv + vec2(random(uv) - 0.5, random(uv.yx) - 0.5));
               }
           }
       }
       
       // Temporal blending with previous result
       vec4 previous = texture(previous_result_tex, uv);
       float blend = temporalBlend * 0.1;
       color = mix(color, previous, blend);
       
       // Propagation decay
       float decay = exp(-propagationDecay * 0.1 * time);
       color = mix(color, texture(current_tex, uv), decay);
       
       fragColor = mix(texture(current_tex, uv), color, u_mix);
   }
   ```

2. **Python Implementation**:
   ```python
   class DepthVectorFieldDatamoshEffect(Effect):
       def __init__(self):
           super().__init__("depth_vector_field_datamosh", VECTOR_VERTEX, VECTOR_FRAGMENT)
           
           self.depth_source = None
           self.depth_frame = None
           self.previous_depth_frame = None
           self.previous_result = None
           
           self.parameters = {
               'vectorScale': 3.0,
               'temporalBlend': 3.0,
               'propagationDecay': 2.0,
               'depthThreshold': 5.0,
               'blockSize': 5.0,
               'blockChaos': 1.0,
           }
           
           self.shader = None
           self.temp_texture = 0
       
       def _ensure_textures(self, width, height):
           if self.temp_texture == 0:
               self.temp_texture = glGenTextures(1)
               glBindTexture(GL_TEXTURE_2D, self.temp_texture)
               glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
       
       def process_frame(self, frame):
           h, w = frame.shape[:2]
           self._ensure_textures(w, h)
           
           # Update depth
           self._update_depth()
           
           # Compute depth delta (if we have previous depth)
           if self.previous_depth_frame is None:
               # First frame: no datamosh
               self.previous_depth_frame = self.depth_frame.copy()
               self.previous_result = frame.copy()
               return frame
           
           # Upload current frame to temp texture
           glBindTexture(GL_TEXTURE_2D, self.temp_texture)
           glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, frame)
           
           # Render effect
           glBindFramebuffer(GL_FRAMEBUFFER, 0)
           
           self.shader.use()
           self._apply_uniforms(time, (w, h))
           
           # Bind textures
           glActiveTexture(GL_TEXTURE0)
           glBindTexture(GL_TEXTURE_2D, self.temp_texture)
           glUniform1i(glGetUniformLocation(self.shader.program, "current_tex"), 0)
           
           glActiveTexture(GL_TEXTURE1)
           glBindTexture(GL_TEXTURE_2D, self.depth_texture)
           glUniform1i(glGetUniformLocation(self.shader.program, "depth_tex"), 1)
           
           glActiveTexture(GL_TEXTURE2)
           glBindTexture(GL_TEXTURE_2D, self.previous_depth_texture)
           glUniform1i(glGetUniformLocation(self.shader.program, "previous_depth_tex"), 2)
           
           glActiveTexture(GL_TEXTURE3)
           glBindTexture(GL_TEXTURE_2D, self.previous_result_texture)
           glUniform1i(glGetUniformLocation(self.shader.program, "previous_result_tex"), 3)
           
           draw_fullscreen_quad()
           
           # Read result
           result = self._read_pixels()
           
           # Update previous state
           self.previous_depth_frame = self.depth_frame.copy()
           self.previous_result = result.copy()
           
           return result
   ```

3. **Motion Vector Computation**: The motion vector is simply the depth delta scaled by `vectorScale`. This creates a 1D vector field (horizontal motion only). Could extend to 2D by using both x and y components.

4. **Block Corruption**: The block corruption applies only where depth is changing significantly. It uses fixed-size blocks and adds random chaos for variety.

5. **Temporal Blending**: The `temporalBlend` parameter controls how much of the previous datamosh result is mixed with the current. Higher values create more persistence.

6. **Propagation Decay**: The `propagationDecay` parameter ensures the effect doesn't persist forever. It exponentially decays the datamosh over time.

7. **First Frame Handling**: On the first frame, there's no previous depth, so the effect should return the current frame unchanged.

8. **Performance**: This is a very lightweight effect — only current frame and depth processing. Should be extremely fast.

9. **Memory**: Minimal — only temporary textures for intermediate rendering. No large history buffers needed.

10. **Debug Mode**: Visualize depth deltas (color-coded), show motion vectors, display corruption blocks, show where datamosh is applied.

---

## Conclusion

The DepthVectorFieldDatamoshEffect is "THE MISSING LINK" — a unique datamosh effect where the depth camera's own temporal changes drive the corruption. Frame-to-frame depth deltas become motion vectors, creating organic, depth-aware datamosh that responds naturally to scene movement. With configurable vector scale, temporal persistence, and block corruption, it's a powerful tool for creating dynamic, depth-driven visual corruption effects.

---
