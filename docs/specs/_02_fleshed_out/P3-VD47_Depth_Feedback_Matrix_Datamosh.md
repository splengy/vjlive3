# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD47_Depth_Feedback_Matrix_Datamosh.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD47 — DepthFeedbackMatrixDatamoshEffect

## Description

The DepthFeedbackMatrixDatamoshEffect creates complex cascading 4-tap feedback structures sculpted by depth, with cross-feeding delays through the void. It implements a multi-tap feedback routing matrix where each tap has depth range gating, external loop insertion points, and cross-feed to the next tap. This creates intricate, evolving feedback patterns that are controlled by depth data, allowing for sophisticated datamosh effects that respond to the 3D structure of the scene.

This effect is ideal for creating complex, recursive visual patterns that evolve over time. The feedback matrix can produce everything from subtle echo trails to chaotic datamosh explosions, all modulated by depth. The ability to insert external effects between taps allows for creative routing and signal processing.

## What This Module Does

- Implements 4-tap feedback routing matrix with depth control
- Each tap has independent depth range gating
- Supports external loop insertion points between taps
- Enables cross-feed from one tap to the next
- Creates cascading feedback structures sculpted by depth
- Produces complex, evolving datamosh patterns
- GPU-accelerated with fragment shader for real-time performance

## What This Module Does NOT Do

- Does NOT provide single-tap feedback (requires 4-tap matrix)
- Does NOT implement depth-based routing without feedback
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT include built-in effects between taps (external only)
- Does NOT handle audio reactivity (may be added later)

---

## Detailed Behavior

### Feedback Matrix Architecture

The effect implements a 4-tap feedback delay line:

```
Input → [Tap 0] → [External Effect] → [Tap 1] → [External Effect] → [Tap 2] → [External Effect] → [Tap 3] → Output
   ↑                                      ↑                                      ↑
   └──────────────── Cross-feed ──────────┘                                      │
                                                                                 │
   └─────────────────────────────────────────────────────────────────────────────┘
```

Each tap:
1. **Depth range gating**: Only passes pixels within a specific depth range
2. **Delay buffer**: Stores previous frames for feedback
3. **Cross-feed**: Sends output to next tap (with optional external effect in between)
4. **Mix control**: Blends between original and feedback

### Tap Parameters

Each of the 4 taps has:

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `tap{i}_depth_min` | float | 0.0 | 0.0-10.0 | Minimum depth for this tap (0-10 normalized) |
| `tap{i}_depth_max` | float | 10.0 | 0.0-10.0 | Maximum depth for this tap |
| `tap{i}_delay` | float | 0.0 | 0.0-10.0 | Delay time in frames (0=no delay, 10=max) |
| `tap{i}_feedback` | float | 0.0 | 0.0-10.0 | Feedback amount (how much to loop back) |
| `tap{i}_mix` | float | 1.0 | 0.0-10.0 | Mix between original and feedback |
| `tap{i}_crossfeed` | float | 0.0 | 0.0-10.0 | Amount to send to next tap |

Where `i` = 0, 1, 2, 3.

### Global Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `matrix_feedback` | float | 0.0 | 0.0-10.0 | Overall feedback matrix gain |
| `matrix_mix` | float | 1.0 | 0.0-10.0 | Overall mix between original and matrix output |
| `temporal_decay` | float | 1.0 | 0.0-10.0 | How quickly feedback decays over time |
| `depth_bias` | float | 0.0 | 0.0-10.0 | Global depth offset for all taps |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class DepthFeedbackMatrixDatamoshEffect(Effect):
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
| **Output** | `np.ndarray` | Feedback matrix processed frame (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Latest depth frame
- `_depth_texture: int` — GL texture for depth data
- `_tap_parameters: List[Dict]` — Parameters for each of 4 taps
- `_matrix_feedback: float` — Overall matrix feedback
- `_matrix_mix: float` — Overall matrix mix
- `_temporal_decay: float` — Temporal decay factor
- `_depth_bias: float` — Global depth offset
- `_shader: ShaderProgram` — Compiled shader
- `_feedback_buffers: List[int]` — 4 feedback textures (ping-pong)
- `_current_buffer_index: int` — Which buffer to read/write

**Per-Frame:**
- Update depth data from source
- Upload depth texture
- For each tap:
  - Sample depth and apply depth range gate
  - Sample feedback buffer (with delay)
  - Apply cross-feed to next tap
  - Write to feedback buffer
- Combine taps with matrix feedback
- Render final output

**Initialization:**
- Create depth texture (lazy)
- Create 4 feedback textures (ping-pong pairs)
- Compile shader
- Default tap parameters (from PRESETS)

**Cleanup:**
- Delete depth texture
- Delete 4 feedback textures
- Delete shader
- Call `super().delete()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_RED, GL_UNSIGNED_BYTE | depth_frame size | Updated each frame |
| Feedback buffers (4) | GL_TEXTURE_2D | GL_RGBA8 | frame size | Updated each frame (ping-pong) |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Depth texture: 307,200 bytes
- Feedback buffers: 4 × 640×480×3 = ~3.7 MB
- Shader: ~10-50 KB
- Total: ~4 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | Use uniform depth gate (all pixels pass) | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Feedback buffer creation fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and buffer updates must occur on the thread with the OpenGL context. The feedback buffers are updated each frame, and the shader is used for rendering, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth texture upload: ~0.5-1 ms
- Feedback buffer operations (4 taps): ~2-4 ms
- Shader execution: ~2-4 ms
- Total: ~4.5-9 ms on GPU

**Optimization Strategies:**
- Reduce number of taps (use only needed taps)
- Use lower resolution for feedback buffers
- Implement feedback in compute shader for better parallelism
- Use texture arrays for feedback buffers
- Cache depth texture if depth hasn't changed
- Use mipmaps for depth if appropriate

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Tap parameters configured (depth ranges, delays, feedback, mix)
- [ ] Matrix parameters tuned (feedback, mix, decay, bias)
- [ ] External effects inserted between taps (if used)
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with 4 taps and default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_depth_gate` | Each tap only processes pixels within its depth range |
| `test_delay` | Feedback delay works correctly |
| `test_feedback` | Feedback loops create recursive effects |
| `test_crossfeed` | Cross-feed between taps works |
| `test_matrix_feedback` | Overall matrix feedback controls recursion strength |
| `test_temporal_decay` | Feedback decays over time |
| `test_depth_bias` | Global depth offset affects all taps |
| `test_feedback_buffers` | 4 feedback buffers created and updated |
| `test_process_frame_no_depth` | Falls back to uniform depth gate |
| `test_process_frame_with_depth` | Depth gates filter feedback correctly |
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
- [ ] Git commit with `[Phase-3] P3-VD47: depth_feedback_matrix_datamosh_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_feedback_matrix_datamosh.py` — VJLive Original implementation
- `plugins/core/depth_feedback_matrix_datamosh/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthFeedbackMatrixDatamoshEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_feedback_matrix_datamosh`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for depth gating
- 4-tap feedback matrix architecture
- Parameters: per-tap depth ranges, delay, feedback, mix, crossfeed; global matrix_feedback, matrix_mix, temporal_decay, depth_bias
- Allocates GL resources: depth texture + 4 feedback textures
- Shader implements feedback routing and depth gating

---

## Notes for Implementers

1. **Feedback Buffer Management**: Use ping-pong buffers for each tap. Each tap needs a read texture and a write texture. Swap after each frame:
   ```python
   # For 4 taps, you need 8 textures (2 per tap) or use 4 textures with careful ordering
   # Simpler: use 4 textures and read from previous frame's buffer
   buffers = [tex0, tex1, tex2, tex3]
   read_idx = current_buffer_index
   write_idx = (current_buffer_index + 1) % 4
   ```

2. **Depth Gating**: In the shader, sample depth and gate:
   ```glsl
   float depth = texture(depth_tex, uv).r;
   float in_range = step(tap_depth_min, depth) * step(depth, tap_depth_max);
   vec4 tap_output = texture(feedback_buffer, uv) * in_range;
   ```

3. **Cross-Feed**: Connect tap outputs:
   ```glsl
   // Tap 0 output feeds into Tap 1 input (with crossfeed amount)
   tap1_input = mix(original_frame, tap0_output, crossfeed_0_1);
   ```

4. **Delay**: Implement delay by sampling from previous frame's buffer:
   ```glsl
   vec4 delayed = texture(feedback_buffer[tap_index], uv);
   // Apply feedback amount
   vec4 result = mix(current, delayed, feedback_amount);
   ```

5. **Temporal Decay**: Apply decay to feedback:
   ```glsl
   feedback_amount *= temporal_decay;
   ```

6. **Shader Architecture**: The shader needs to:
   - Sample depth texture
   - For each tap, read from feedback buffer, apply depth gate, compute output
   - Cross-feed between taps
   - Combine all taps with matrix feedback
   - Mix with original frame

7. **External Effects Insertion**: The architecture should allow external effects to be inserted between taps. This could be done by:
   - Having separate shader stages
   - Or having the effect chain call `process_frame` multiple times
   - Document the expected interface for external effects

8. **Parameter Naming**: Use consistent naming:
   - `tap0_depth_min`, `tap0_depth_max`, `tap0_delay`, `tap0_feedback`, `tap0_mix`, `tap0_crossfeed`
   - Same for tap1, tap2, tap3
   - `matrix_feedback`, `matrix_mix`, `temporal_decay`, `depth_bias`

9. **Performance**: 4 feedback buffers = 4 full-resolution textures. Consider:
   - Using half-resolution for feedback
   - Using fewer taps if not all needed
   - Using texture arrays

10. **Testing**: Create depth patterns (e.g., depth ramp) and verify:
    - Each tap only affects its depth range
    - Cross-feed connects taps correctly
    - Delay creates temporal echo
    - Feedback creates recursive patterns
    - Matrix feedback controls overall recursion

11. **Future Extensions**:
    - Add per-tap color tinting
    - Add per-tap distortion effects
    - Add audio-reactive depth gating
    - Add external effect chaining
    - Add preset system for common configurations

---
-

## References

- Feedback systems: https://en.wikipedia.org/wiki/Feedback
- Delay effects: https://en.wikipedia.org/wiki/Delay_(audio_effect)
- Datamosh: https://en.wikipedia.org/wiki/Datamosh
- VJLive legacy: `plugins/vdepth/depth_feedback_matrix_datamosh.py`

---

## Implementation Tips

1. **Shader Structure**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;        // Current frame
   uniform sampler2D depth_tex;   // Depth texture
   uniform sampler2D feedback0;   // Tap 0 feedback buffer
   uniform sampler2D feedback1;   // Tap 1 feedback buffer
   uniform sampler2D feedback2;   // Tap 2 feedback buffer
   uniform sampler2D feedback3;   // Tap 3 feedback buffer
   uniform vec2 resolution;
   uniform float u_mix;
   
   // Tap parameters
   uniform float tap0_depth_min, tap0_depth_max;
   uniform float tap0_delay, tap0_feedback, tap0_mix, tap0_crossfeed;
   // ... similarly for tap1, tap2, tap3
   
   uniform float matrix_feedback, matrix_mix, temporal_decay, depth_bias;
   
   void main() {
       vec4 current = texture(tex0, uv);
       float depth = texture(depth_tex, uv).r + depth_bias;
       
       // Tap 0
       float in_range0 = step(tap0_depth_min, depth) * step(depth, tap0_depth_max);
       vec4 tap0_fb = texture(feedback0, uv);
       vec4 tap0_out = mix(current, tap0_fb, tap0_feedback) * in_range0;
       
       // Tap 1 (receives crossfeed from tap0)
       float in_range1 = step(tap1_depth_min, depth) * step(depth, tap1_depth_max);
       vec4 tap1_input = mix(current, tap0_out, tap0_crossfeed);
       vec4 tap1_fb = texture(feedback1, uv);
       vec4 tap1_out = mix(tap1_input, tap1_fb, tap1_feedback) * in_range1;
       
       // Tap 2 (receives crossfeed from tap1)
       // ... similar
       
       // Tap 3 (receives crossfeed from tap2)
       // ... similar
       
       // Combine all taps with matrix feedback
       vec4 result = current;
       result = mix(result, tap0_out, tap0_mix * matrix_mix);
       result = mix(result, tap1_out, tap1_mix * matrix_mix);
       result = mix(result, tap2_out, tap2_mix * matrix_mix);
       result = mix(result, tap3_out, tap3_mix * matrix_mix);
       
       // Apply overall matrix feedback
       result = mix(current, result, matrix_feedback);
       
       fragColor = mix(current, result, u_mix);
   }
   ```

2. **Feedback Buffer Update**:
   ```python
   def process_frame(self, frame):
       # After computing shader output for this frame
       # Write output to feedback buffers for next frame
       for i, buffer in enumerate(self._feedback_buffers):
           glBindTexture(GL_TEXTURE_2D, buffer)
           glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, output_data)
       
       # Swap buffer indices for next frame
       self._current_buffer_index = (self._current_buffer_index + 1) % 4
       
       return output_frame
   ```

3. **Depth Gating**: Depth ranges are in normalized [0,1] space. Apply `depth_bias` as offset:
   ```python
   effective_depth = depth + self._depth_bias
   ```

4. **PRESETS**: Define useful configurations:
   ```python
   PRESETS = {
       "simple_echo": {
           # Tap 0: shallow depth, short delay
           "tap0_depth_min": 0.0, "tap0_depth_max": 0.3,
           "tap0_delay": 1.0, "tap0_feedback": 5.0, "tap0_mix": 8.0, "tap0_crossfeed": 0.0,
           # Other taps disabled
           "matrix_feedback": 3.0, "matrix_mix": 5.0, "temporal_decay": 8.0, "depth_bias": 0.0,
       },
       "cascading_void": {
           # All taps active, cascading through depth
           "tap0_depth_min": 0.0, "tap0_depth_max": 0.25, "tap0_delay": 2.0, "tap0_feedback": 7.0, "tap0_mix": 6.0, "tap0_crossfeed": 8.0,
           "tap1_depth_min": 0.25, "tap1_depth_max": 0.5, "tap1_delay": 4.0, "tap1_feedback": 6.0, "tap1_mix": 6.0, "tap1_crossfeed": 8.0,
           "tap2_depth_min": 0.5, "tap2_depth_max": 0.75, "tap2_delay": 6.0, "tap2_feedback": 5.0, "tap2_mix": 6.0, "tap2_crossfeed": 8.0,
           "tap3_depth_min": 0.75, "tap3_depth_max": 1.0, "tap3_delay": 8.0, "tap3_feedback": 4.0, "tap3_mix": 6.0, "tap3_crossfeed": 0.0,
           "matrix_feedback": 5.0, "matrix_mix": 7.0, "temporal_decay": 6.0, "depth_bias": 0.0,
       },
   }
   ```

5. **External Effects Insertion**: Document how to insert effects between taps. This may require:
   - Multiple effect instances in a chain
   - Or a special "insertion point" uniform that allows external shaders to process
   - Or the effect should be designed as a framework where taps are separate effects

6. **Depth Texture**: Ensure depth is normalized [0,1]. Apply `depth_bias` offset. Clamp to [0,1] after bias.

7. **Feedback Loop Control**: The `temporal_decay` parameter prevents infinite feedback loops. Multiply feedback by decay each frame:
   ```glsl
   float effective_feedback = tap_feedback * temporal_decay;
   ```

8. **Initialization**: On first frame, feedback buffers are empty (black). Consider initializing with current frame to avoid black flash.

9. **Performance**: 4 feedback buffers = 4 texture reads + 1 depth read + 1 frame read = 6 texture reads per pixel. This is heavy. Consider:
   - Reducing resolution of feedback buffers
   - Using compute shader with shared memory
   - Using texture arrays

10. **Testing**: Test with simple depth patterns (e.g., gradient) to verify depth gating. Test with static image to verify feedback loops create trails.

---

## Conclusion

The DepthFeedbackMatrixDatamoshEffect provides a powerful framework for creating complex, depth-controlled feedback structures. With 4 independent taps, depth range gating, cross-feed, and external effect insertion, it enables sophisticated datamosh effects that evolve over time and respond to depth. This effect is a versatile tool for creating recursive, cascading visuals in VJ performances.

---
