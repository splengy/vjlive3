# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD54_Depth_Loop_Injection_Datamosh.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD54 — DepthLoopInjectionDatamoshEffect

## Description

The DepthLoopInjectionDatamoshEffect is a modular routing hub that provides 4 explicit send/return loop points for inserting external effects into the datamosh pipeline. It acts as a central patchbay where you can route other effects through specific stages of the datamosh processing chain. The four loop points are:

- **PRE_LOOP**: Before depth modulation
- **DEPTH_LOOP**: After depth processing, before datamosh
- **MOSH_LOOP**: After datamosh, before feedback
- **POST_LOOP**: After feedback, before final output

Each loop has an enable flag and a wet/dry mix control, allowing you to blend the processed signal with the original. This effect is designed for advanced VJ workflows where you need to inject custom processing at precise points in the datamosh chain, creating complex, layered effect architectures.

## What This Module Does

- Provides 4 modular send/return injection points
- Routes signal through external effects at configurable pipeline stages
- Supports enable/disable for each loop
- Provides wet/dry mix control per loop
- Maintains separate feedback loops for each injection point
- GPU-accelerated with flexible shader architecture
- Enables creative routing of effects through datamosh pipeline

## What This Module Does NOT Do

- Does NOT include built-in effects (only routing infrastructure)
- Does NOT manage external effect instances (user must connect)
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT implement loopback protection (user must avoid infinite loops)
- Does NOT include audio reactivity (may be added later)

---

## Detailed Behavior

### Pipeline Architecture

```
[Input]
   |
   v
[PRE_LOOP] ---> [External Effect] --> (mix) --> [Depth Modulation]
   |
   v
[DEPTH_LOOP] ---> [External Effect] --> (mix) --> [Datamosh]
   |
   v
[MOSH_LOOP] ---> [External Effect] --> (mix) --> [Feedback]
   |
   v
[POST_LOOP] ---> [External Effect] --> (mix) --> [Output]
```

Each loop point:
1. Sends current signal to external effect via output
2. Receives processed signal from external effect via input
3. Blends with original signal using wet/dry mix
4. Feeds result into next pipeline stage

### Loop Points

#### PRE_LOOP
- **Location**: Before any depth modulation
- **Use case**: Apply effects to raw video before depth processing
- **Examples**: Color correction, sharpening, noise reduction

#### DEPTH_LOOP
- **Location**: After depth modulation, before datamosh
- **Use case**: Process depth-modulated signal before datamosh artifacts
- **Examples**: Edge enhancement, contour extraction, depth-based colorization

#### MOSH_LOOP
- **Location**: After datamosh, before feedback
- **Use case**: Process datamosh artifacts before they enter feedback loop
- **Examples**: Glitch intensification, pixel sorting, color channel shifting

#### POST_LOOP
- **Location**: After feedback, before final output
- **Use case**: Final polish after all recursive processing
- **Examples**: Color grading, vignette, grain, final blend

### Parameters

For each loop (4 loops total), the following parameters exist:

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `enablePre` / `enableDepth` / `enableMosh` / `enablePost` | float | 0.0 | 0.0-10.0 | Enable loop (0=off, >0=on) |
| `preMix` / `depthMix` / `moshMix` / `postMix` | float | 0.0 | 0.0-10.0 | Wet/dry mix (0=dry, 10=wet) |

Additionally, core datamosh parameters (inherited from base datamosh effect):

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `datamoshStrength` | float | 5.0 | 0.0-10.0 | Intensity of datamosh artifacts |
| `feedbackAmount` | float | 0.5 | 0.0-10.0 | Feedback loop strength |
| `feedbackDecay` | float | 0.9 | 0.0-10.0 | Feedback decay per frame |
| `depthInfluence` | float | 5.0 | 0.0-10.0 | How much depth modulates datamosh |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class DepthLoopInjectionDatamoshEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray,
                      pre_return: Optional[np.ndarray] = None,
                      depth_return: Optional[np.ndarray] = None,
                      mosh_return: Optional[np.ndarray] = None,
                      post_return: Optional[np.ndarray] = None) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| `pre_return` | `np.ndarray` (optional) | Return from external effect at PRE_LOOP |
| `depth_return` | `np.ndarray` (optional) | Return from external effect at DEPTH_LOOP |
| `mosH_return` | `np.ndarray` (optional) | Return from external effect at MOSH_LOOP |
| `post_return` | `np.ndarray` (optional) | Return from external effect at POST_LOOP |
| **Output** | `np.ndarray` | Final processed frame (HxWxC, RGB) |

**Note**: The effect has multiple optional return inputs for each loop point. If a return is None, that loop is bypassed (dry signal passes through).

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Latest depth frame
- `_depth_texture: int` — GL texture for depth data
- `_parameters: dict` — All loop and datamosh parameters
- `_shader: ShaderProgram` — Compiled shader
- `_feedback_textures: List[int]` — 4 feedback textures (one per loop that has feedback)
- `_framebuffers: List[int]` — FBOs for ping-pong rendering
- `_current_loop_indices: List[int]` — Ping-pong indices per loop

**Per-Frame:**
- Update depth data from source
- Upload depth texture
- For each loop (in order):
  1. If enabled and return provided, blend with current signal
  2. Render to feedback texture for next frame (if feedback enabled)
- Apply datamosh processing
- Apply feedback from previous frame
- Return final result

**Initialization:**
- Create depth texture (lazy)
- Create feedback textures and FBOs for each loop (lazy, only if enabled)
- Compile shader
- Default parameters: all loops disabled, datamoshStrength=5.0, feedbackAmount=0.5, feedbackDecay=0.9, depthInfluence=5.0

**Cleanup:**
- Delete depth texture
- Delete all feedback textures
- Delete all framebuffers
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_RED, GL_UNSIGNED_BYTE | depth_frame size | Updated each frame |
| Feedback textures (up to 4) | GL_TEXTURE_2D | GL_RGBA8 | frame size | Created per enabled loop |
| Framebuffers (up to 4) | GL_FRAMEBUFFER | N/A | frame size | Created per enabled loop |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Depth texture: 307,200 bytes
- Feedback textures: 4 × 921,600 = 3,686,400 bytes (if all enabled)
- Framebuffers: negligible
- Shader: ~30-60 KB (complex routing)
- Total: ~4 MB (worst case)

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | Use uniform depth (0.5) | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Feedback texture creation fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Return frame size mismatch | Resize or raise `ValueError` | Ensure consistent sizing |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and texture updates must occur on the thread with the OpenGL context. Multiple feedback textures are updated each frame, and the complex shader uses multiple render passes, so concurrent `process_frame()` calls will cause race conditions and visual artifacts. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth texture upload: ~0.5-1 ms
- Shader execution (per loop, with datamosh): ~4-8 ms per enabled loop
- Texture copies for feedback: ~0.5-1 ms per loop
- Total: ~4-12 ms per enabled loop (worst case ~16-32 ms with all 4 loops)

**Optimization Strategies:**
- Disable unused loops (set enable=0)
- Reduce feedback texture resolution
- Use simpler shader branches for disabled loops
- Combine loops into single pass if possible
- Use compute shader for parallel processing
- Cache depth texture if depth hasn't changed

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Loop parameters configured (enable, mix for each loop)
- [ ] Datamosh parameters configured
- [ ] External effects connected to loop returns
- [ ] `process_frame()` called each frame with return frames
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_pre_loop` | PRE_LOOP routing works correctly |
| `test_depth_loop` | DEPTH_LOOP routing works correctly |
| `test_mosh_loop` | MOSH_LOOP routing works correctly |
| `test_post_loop` | POST_LOOP routing works correctly |
| `test_loop_mix` | Wet/dry mix blends correctly |
| `test_loop_disabled` | Disabled loops bypass signal |
| `test_feedback_per_loop` | Each loop maintains separate feedback |
| `test_datamosh_strength` | Datamosh intensity controlled correctly |
| `test_feedback_amount` | Feedback amount affects recursion |
| `test_feedback_decay` | Decay controls feedback persistence |
| `test_depth_influence` | Depth modulates datamosh correctly |
| `test_all_loops_combined` | Multiple loops work together |
| `test_process_frame_no_returns` | All loops bypassed = dry signal |
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
- [ ] Git commit with `[Phase-3] P3-VD54: depth_loop_injection_datamosh_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_loop_injection_datamosh.py` — VJLive Original implementation
- `plugins/core/depth_loop_injection_datamosh/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_loop_injection_datamosh/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthLoopInjectionDatamoshEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_loop_injection_datamosh`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for depth modulation
- 4 loop points: PRE_LOOP, DEPTH_LOOP, MOSH_LOOP, POST_LOOP
- Parameters: `enablePre`, `preMix`, `enableDepth`, `depthMix`, `enableMosh`, `mosH_Mix`, `enablePost`, `postMix`, plus datamosh params
- Allocates GL resources: depth texture, up to 4 feedback textures and FBOs
- Shader implements modular routing with per-loop feedback
- PRESETS defined: "clean_chain" (all loops bypassed)

---

## Notes for Implementers

1. **Modular Routing Architecture**: This effect is essentially a "patchbay" that lets you inject external effects at 4 strategic points in the datamosh pipeline. Each loop point is independent and can be enabled/disabled and mixed separately.

2. **Loop Point Semantics**:
   - **PRE_LOOP**: Signal before any depth processing. Good for pre-processing (denoise, sharpen, color correct).
   - **DEPTH_LOOP**: Signal after depth modulation but before datamosh. Good for depth-based effects (contour extraction, edge detection).
   - **MOSH_LOOP**: Signal after datamosh but before feedback. Good for intensifying glitch effects (pixel sort, channel shift).
   - **POST_LOOP**: Signal after feedback but before output. Good for final polish (color grade, grain, vignette).

3. **Feedback per Loop**: Each loop can have its own feedback texture, allowing recursive processing at that stage. This means you can create feedback loops that only include certain stages of the pipeline.

4. **Shader Structure**: The shader will be complex because it needs to handle 4 potential injection points. Consider:
   - Using `#define` flags for each loop (compile-time enable/disable)
   - Or runtime branching based on enable flags
   - Each loop may need its own feedback texture sampling

5. **Parameter Naming**: The legacy uses names like `enablePre`, `preMix`, etc. Follow this pattern for all 4 loops:
   ```python
   parameters = {
       'enablePre': 0.0, 'preMix': 0.0,
       'enableDepth': 0.0, 'depthMix': 0.0,
       'enableMosh': 0.0, 'mosH_Mix': 0.0,
       'enablePost': 0.0, 'postMix': 0.0,
       # Datamosh params
       'datamoshStrength': 5.0,
       'feedbackAmount': 0.5,
       'feedbackDecay': 0.9,
       'depthInfluence': 5.0,
   }
   ```

6. **Process Frame Signature**: The `process_frame` method should accept optional return frames for each loop:
   ```python
   def process_frame(self, frame, pre_return=None, depth_return=None,
                     mosh_return=None, post_return=None):
   ```
   If a return is None, that loop is bypassed (dry signal passes through).

7. **Shader Uniforms**:
   ```glsl
   uniform sampler2D tex0;          // Input frame
   uniform sampler2D depth_tex;     // Depth texture
   uniform sampler2D texPreRet;     // PRE_LOOP return (optional)
   uniform sampler2D texDepthRet;   // DEPTH_LOOP return (optional)
   uniform sampler2D texMoshRet;    // MOSH_LOOP return (optional)
   uniform sampler2D texPostRet;    // POST_LOOP return (optional)
   uniform sampler2D texPreFb;      // PRE_LOOP feedback (optional)
   uniform sampler2D texDepthFb;    // DEPTH_LOOP feedback (optional)
   uniform sampler2D texMoshFb;     // MOSH_LOOP feedback (optional)
   uniform sampler2D texPostFb;     // POST_LOOP feedback (optional)
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float enablePre;    // 0 or 1
   uniform float preMix;       // 0-1 (map from 0-10)
   uniform float enableDepth;
   uniform float depthMix;
   uniform float enableMosh;
   uniform float mosH_Mix;
   uniform float enablePost;
   uniform float postMix;
   
   uniform float datamoshStrength;
   uniform float feedbackAmount;
   uniform float feedbackDecay;
   uniform float depthInfluence;
   ```

8. **Ping-Pong Textures**: For each loop that has feedback, you need a pair of textures for ping-pong:
   ```python
   self.pre_fb_tex = [glGenTextures(2), glGenFramebuffers(2)] if pre_enabled else None
   self.depth_fb_tex = [glGenTextures(2), glGenFramebuffers(2)] if depth_enabled else None
   # ... similarly for mosh and post
   ```

9. **Pipeline Execution Order**:
   - Start with input frame
   - **PRE_LOOP**: If enabled, send to external, receive return, mix with current signal, store in pre feedback texture
   - **Depth modulation**: Apply depth-based effects to pre-loop output (or input if pre disabled)
   - **DEPTH_LOOP**: If enabled, send to external, receive return, mix, store in depth feedback texture
   - **Datamosh**: Apply datamosh to depth-loop output (or depth-modulated if depth disabled)
   - **MOSH_LOOP**: If enabled, send to external, receive return, mix, store in mosh feedback texture
   - **Feedback**: Blend current mosh output with previous frame's feedback (from mosh or earlier)
   - **POST_LOOP**: If enabled, send to external, receive return, mix, store in post feedback texture
   - Output final signal

10. **Parameter Mapping**: Map 0-10 UI ranges to shader values:
    - `enable*`: 0-10 → 0.0 or 1.0 (threshold at >0)
    - `*Mix`: 0-10 → 0.0-1.0 (divide by 10)
    - `datamoshStrength`: 0-10 → multiplier
    - `feedbackAmount`: 0-10 → 0.0-1.0 (divide by 10)
    - `feedbackDecay`: 0-10 → 0.0-1.0 (divide by 10, where 1.0 = no decay)
    - `depthInfluence`: 0-10 → multiplier

11. **PRESETS**: The legacy defines a "clean_chain" preset with all loops disabled. Define additional presets:
    ```python
    PRESETS = {
        "clean_chain": {
            "enablePre": 0.0, "preMix": 0.0,
            "enableDepth": 0.0, "depthMix": 0.0,
            "enableMosh": 0.0, "mosH_Mix": 0.0,
            "enablePost": 0.0, "postMix": 0.0,
            "datamoshStrength": 5.0, "feedbackAmount": 0.5,
            "feedbackDecay": 0.9, "depthInfluence": 5.0,
        },
        "pre_processed": {
            "enablePre": 1.0, "preMix": 5.0,  # 50% wet
            # others disabled
        },
        "depth_enhanced": {
            "enableDepth": 1.0, "depthMix": 7.0,  # 70% wet
            # others disabled
        },
        "mosh_intensifier": {
            "enableMosh": 1.0, "mosH_Mix": 8.0,  # 80% wet
            # others disabled
        },
        "full_chain": {
            "enablePre": 1.0, "preMix": 5.0,
            "enableDepth": 1.0, "depthMix": 5.0,
            "enableMosh": 1.0, "mosH_Mix": 5.0,
            "enablePost": 1.0, "postMix": 5.0,
            "datamoshStrength": 6.0, "feedbackAmount": 0.6,
            "feedbackDecay": 0.8, "depthInfluence": 6.0,
        },
    }
    ```

12. **Testing Strategy**: Test each loop independently by disabling others. Verify:
    - PRE_LOOP: External effect processes signal before depth
    - DEPTH_LOOP: External effect processes depth-modulated signal
    - MOSH_LOOP: External effect processes datamosh output
    - POST_LOOP: External effect processes final signal
    - Mix controls blend correctly
    - Feedback textures maintain state across frames
    - Disabled loops pass signal unchanged

13. **Shader Complexity**: The shader will be large. Consider:
    - Splitting into multiple shader programs (one per loop stage)
    - Using `#define` to compile only needed loops
    - Using separate render passes for each loop
    - Documenting the pipeline clearly in comments

14. **Memory Management**: Each enabled loop allocates 2 textures (ping-pong) and 1 FBO. If memory is a concern, allow loops to share feedback textures if they don't need separate state.

15. **Future Extensions**:
    - Add per-loop feedback enable/disable
    - Add per-loop feedback decay control
    - Add audio reactivity to loop parameters
    - Add loop bypass (true dry signal vs 100% wet)
    - Add loop order reconfiguration

---

## Easter Egg Idea

When all 4 loops are enabled with exact mix values of 6.66, `datamoshStrength` set to 6.66, `feedbackAmount` to 0.666, `feedbackDecay` to 0.666, and the depth map contains a perfect tesseract, the effect enters a "hyperloop" state where the 4 feedback loops synchronize into a 4-dimensional torus, creating a recursive visual that appears to fold through itself at exactly 6.66 Hz. VJs report experiencing a "dimensional shear" where the visual seems to exist in multiple states simultaneously, perfectly balanced between all 4 loop points.

---

## References

- Effects routing: https://en.wikipedia.org/wiki/Effects_unit#Signal_processing
- Feedback: https://en.wikipedia.org/wiki/Feedback
- Datamosh: https://en.wikipedia.org/wiki/Datamosh
- Modular synthesis: https://en.wikipedia.org/wiki/Modular_synthesizer
- VJLive legacy: `plugins/vdepth/depth_loop_injection_datamosh.py`

---

## Implementation Tips

1. **Multi-Pass Approach**: Given the complexity, consider using multiple render passes:
   - Pass 1: PRE_LOOP (if enabled)
   - Pass 2: Depth modulation
   - Pass 3: DEPTH_LOOP (if enabled)
   - Pass 4: Datamosh
   - Pass 5: MOSH_LOOP (if enabled)
   - Pass 6: Feedback
   - Pass 7: POST_LOOP (if enabled)
   - Pass 8: Final mix

   This simplifies each shader but adds render overhead.

2. **Single-Pass with Branching**: Alternatively, one giant shader with conditionals:
   ```glsl
   void main() {
       vec4 color = texture(tex0, uv);
       
       // PRE_LOOP
       if (enablePre > 0.5) {
           vec4 pre_out = texture(texPreRet, uv);
           color = mix(color, pre_out, preMix);
           // Store to pre feedback texture
       }
       
       // Depth modulation
       color = apply_depth_modulation(color, depth);
       
       // DEPTH_LOOP
       if (enableDepth > 0.5) {
           vec4 depth_out = texture(texDepthRet, uv);
           color = mix(color, depth_out, depthMix);
           // Store to depth feedback texture
       }
       
       // ... and so on
   }
   ```

3. **Feedback Texture Management**: For each loop, you need ping-pong textures:
   ```python
   class LoopFeedback:
       def __init__(self):
           self.tex = glGenTextures(2)
           self.fbo = glGenFramebuffers(2)
           self.current = 0
           
       def swap(self):
           self.current = 1 - self.current
           
       def get_read_tex(self):
           return self.tex[self.current]
           
       def get_write_fbo(self):
           return self.fbo[1 - self.current]
   ```

4. **Process Frame Implementation**:
   ```python
   def process_frame(self, frame, pre_return=None, depth_return=None,
                     mosh_return=None, post_return=None):
       h, w = frame.shape[:2]
       self._ensure_resources(w, h)
       
       # Upload depth
       self._upload_depth_texture()
       
       # Determine which loops are active
       pre_enabled = self.parameters['enablePre'] > 0
       depth_enabled = self.parameters['enableDepth'] > 0
       mosh_enabled = self.parameters['enableMosh'] > 0
       post_enabled = self.parameters['enablePost'] > 0
       
       # Create textures from numpy arrays
       frame_tex = self._texture_from_array(frame)
       
       # PRE_LOOP pass
       if pre_enabled and pre_return is not None:
           pre_return_tex = self._texture_from_array(pre_return)
           # Render to pre feedback FBO
           glBindFramebuffer(GL_FRAMEBUFFER, self.pre_loop.get_write_fbo())
           # Set uniforms, draw
           # ...
           self.pre_loop.swap()
           
       # Depth modulation pass
       # Render depth-modulated signal to intermediate texture
       # ...
       
       # DEPTH_LOOP pass
       if depth_enabled and depth_return is not None:
           # Similar to pre-loop
           
       # Datamosh pass
       # Apply datamosh to current signal
       
       # MOSH_LOOP pass
       if mosh_enabled and mosh_return is not None:
           # Similar
           
       # Feedback pass
       # Blend with previous feedback texture
       
       # POST_LOOP pass
       if post_enabled and post_return is not None:
           # Similar
           
       # Read final result
       result = self._read_pixels()
       
       return result
   ```

5. **Shader Uniform Management**: With many uniforms, consider:
   ```python
   def _apply_loop_uniforms(self, loop_name, enable, mix):
       self.shader.set_uniform(f"enable{loop_name}", 1.0 if enable else 0.0)
       self.shader.set_uniform(f"{loop_name}Mix", mix / 10.0)
   ```

6. **Resource Cleanup**: Each loop allocates resources. Track them separately for easy cleanup:
   ```python
   self.loops = {
       'pre': {'enabled': False, 'fb': None, 'tex': []},
       'depth': {'enabled': False, 'fb': None, 'tex': []},
       'mosh': {'enabled': False, 'fb': None, 'tex': []},
       'post': {'enabled': False, 'fb': None, 'tex': []},
   }
   ```

7. **Performance**: The effect can be very heavy if all 4 loops are enabled with feedback. Document this and recommend disabling unused loops.

8. **Testing**: Create simple external effects (e.g., invert colors, blur) and verify they route correctly through each loop point.

---

## Conclusion

The DepthLoopInjectionDatamoshEffect is a powerful modular routing hub that gives VJs unprecedented control over the datamosh pipeline. By providing 4 explicit injection points with independent enable/mix controls and feedback loops, it enables complex, layered effect architectures that can be reconfigured on the fly. This effect turns datamosh from a monolithic process into a flexible, modular system.

---
>>>>>>> REPLACE