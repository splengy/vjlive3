# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT054_depth_loop_injection_datamosh.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT054 — DepthLoopInjectionDatamoshEffect

**What This Module Does**

The `DepthLoopInjectionDatamoshEffect` is a modular video processing pipeline that combines depth modulation with datamoshing and provides explicit loop injection points for inserting arbitrary effects at key stages. It's designed as a routing hub where users can patch in other effects (e.g., blur, color grading, kaleidoscope) into the datamosh processing chain, similar to eurorack send/return patching but for video.

The core pipeline consists of:

1. **PRE_LOOP**: Raw input video can be processed by an external effect before any depth modulation
2. **Depth Modulation**: The video is modulated based on a depth map (brighter for closer objects, darker for far)
3. **DEPTH_LOOP**: The depth-modulated video can be sent through an external effect before datamoshing
4. **Datamosh**: Motion-based displacement effect that smears pixels based on frame difference
5. **MOSH_LOOP**: The datamoshed video can be processed by an external effect before feedback
6. **Feedback**: The result is mixed with the previous frame to create trails/echoes
7. **POST_LOOP**: The feedback-mixed result can be sent through a final external effect
8. **Final Mix**: The processed result is blended with the original input

Each loop stage has:
- **Enable/disable** (bypass)
- **Wet/dry mix** (0.0 = dry, 1.0 = fully wet)
- **Return texture**: The output of the external effect is fed back into the pipeline at that stage

The effect is implemented as a single GLSL fragment shader that samples all loop return textures and applies the mixing logic. It requires multiple FBOs to manage the loop textures (each loop's output must be rendered to a texture that this shader can sample).

**What This Module Does NOT Do**

- Does NOT implement the external effects that are injected (those are separate modules)
- Does NOT manage the routing graph (the pipeline configuration is external)
- Does NOT perform depth map generation (depth is provided as input)
- Does NOT handle audio analysis (though it could be extended)
- Does NOT provide a UI for loop configuration (that's in ProgramPage)
- Does NOT support dynamic loop addition/removal at runtime (fixed 4 loops)
- Does NOT implement the actual datamosh algorithm variations beyond the basic motion displacement

---

## Detailed Behavior and Parameter Interactions

### Pipeline Architecture

The shader processes the frame in a linear sequence with 4 loop injection points. The data flow:

```
tex0 (input) 
  → [PRE_LOOP mix with pre_loop_return]
  → stage1_output
  → [Depth modulation using depth_tex]
  → stage2_output
  → [DEPTH_LOOP mix with depth_loop_return]
  → stage3_output
  → [Datamosh using texPrev]
  → mosh_result
  → [MOSH_LOOP mix with mosh_loop_return]
  → stage4_output
  → [Feedback mix with texPrev]
  → with_feedback
  → [POST_LOOP mix with post_loop_return]
  → stage5_output
  → [Final mix with original tex0]
  → fragColor
```

### Stage Details

#### 1. PRE_LOOP

- **Input**: `signal = texture(tex0, uv)`
- **Processing**: If `enable_pre_loop == 1`, mix with `pre_loop_return`: `stage1_output = mix(signal, pre_loop_return, pre_loop_mix)`
- **Output**: `stage1_output`

This stage allows effects like color correction, blur, or kaleidoscope to be applied before depth modulation.

#### 2. Depth Modulation

The depth modulation uses the depth map to adjust the intensity of the video:

```glsl
float depth_factor = (depth - 0.3) / 3.7;
if (invert_depth == 1) depth_factor = 1.0 - depth_factor;
depth_factor = clamp(depth_factor, 0.0, 1.0);
float modulated_intensity = mix(0.3, 1.0, depth_factor * depth_modulation);
```

- `depth` is the depth value at this pixel (0.0-1.0)
- `depth_factor` remaps depth from [0.3, 4.0] to [0,1] (the 0.3 and 3.7 are hardcoded thresholds)
- `invert_depth` flips the depth mapping
- `depth_modulation` scales the depth influence (0 = no modulation, 1 = full)
- `modulated_intensity` is a multiplier used later in datamosh displacement

#### 3. DEPTH_LOOP

- **Input**: `stage2_output = stage1_output` (after depth modulation)
- **Processing**: If `enable_depth_loop == 1`, mix with `depth_loop_return`: `stage2_output = mix(stage1_output, depth_loop_return, depth_loop_mix)`
- **Output**: `stage2_output`

This stage allows effects to be inserted after depth modulation but before datamoshing.

#### 4. Datamosh

The datamosh effect displaces pixels based on motion detection between the current frame and the previous frame:

```glsl
float block = max(4.0, block_size * 40.0 + 4.0);
vec2 block_uv = floor(uv * resolution / block) * block / resolution;

vec4 block_current = texture(tex0, block_uv);
vec4 block_prev = texture(texPrev, block_uv);
vec3 block_diff = block_current.rgb - block_prev.rgb;
float motion = length(block_diff);

vec2 displacement = vec2(0.0);
if (motion > mosh_threshold * 0.1) {
    displacement = block_diff.rg * modulated_intensity * mosh_intensity * 0.05;
}

vec2 mosh_uv = uv + displacement;
mosh_uv = clamp(mosh_uv, 0.001, 0.999);
vec4 datamoshed = texture(texPrev, mosh_uv);
```

- The image is divided into blocks (size controlled by `block_size`, range 4-164 pixels)
- For each block, compute motion as the RGB difference between current and previous frame
- If motion exceeds threshold, displace the UV by the motion vector scaled by `modulated_intensity` and `mosh_intensity`
- Sample the previous frame at the displaced UV to create the smear/trail effect

Then blend between the original (stage2_output) and the datamoshed version:

```glsl
float blend_factor = smoothstep(mosh_threshold * 0.05, mosh_threshold * 0.15, motion);
blend_factor *= modulated_intensity;
vec4 mosh_result = mix(stage2_output, datamoshed, blend_factor);
```

- `blend_factor` increases with motion, creating more datamoshing in areas with movement
- `modulated_intensity` from depth modulation also influences the blend (closer objects = more mosh)

#### 5. MOSH_LOOP

- **Input**: `stage3_output = mosh_result`
- **Processing**: If `enable_mosh_loop == 1`, mix with `mosh_loop_return`: `stage3_output = mix(mosh_result, mosh_loop_return, mosh_loop_mix)`
- **Output**: `stage3_output`

This stage allows effects to be inserted after datamoshing but before feedback (e.g., additional distortion, color shifts).

#### 6. Feedback

```glsl
vec4 with_feedback = mix(stage3_output, previous, feedback_amount * 0.5);
```

- Mix the current frame with the previous output (`texPrev`) to create trails/echoes
- `feedback_amount` controls how much of the previous frame is retained (0 = no feedback, 1 = full previous frame)

#### 7. POST_LOOP

- **Input**: `stage4_output = with_feedback`
- **Processing**: If `enable_post_loop == 1`, mix with `post_loop_return`: `stage4_output = mix(with_feedback, post_loop_return, post_loop_mix)`
- **Output**: `stage4_output`

Final processing stage before output (e.g., color grading, vignette).

#### 8. Final Mix

```glsl
fragColor = mix(signal, stage4_output, u_mix);
```

- Blend between the original input (`signal`) and the fully processed result
- `u_mix` is the overall wet/dry control for the entire effect

### Loop Return Texture Management

Each loop stage expects a texture that contains the output of an external effect. These textures must be provided as uniforms:

- `pre_loop_return`: Texture from the effect inserted at PRE_LOOP
- `depth_loop_return`: Texture from the effect inserted at DEPTH_LOOP
- `mosh_loop_return`: Texture from the effect inserted at MOSH_LOOP
- `post_loop_return`: Texture from the effect inserted at POST_LOOP

The external effects are rendered separately into these textures (using FBOs) before this effect's `process_frame` is called. The routing system must manage this dependency.

### Dual Video Input

The shader checks if `tex1` (Video B) is connected:

```glsl
bool hasDualInput = (testB.r + testB.g + testB.b) > 0.01;
```

If dual input is present, the effect may use `tex1` differently. In the current shader, `tex1` is used as the source for `block_current` in the datamosh step:

```glsl
vec4 block_current = texture(tex0, block_uv);  // Actually uses tex0, but legacy may have used tex1
```

Wait, the legacy code shows `texture(tex0, block_uv)` for block_current. The dual input might be used elsewhere or the shader snippet is incomplete. The skeleton spec mentions "dual video inputs" but the shader only uses `tex0` for the main signal. Possibly `tex1` is used as an alternative source for the datamosh or for the loop returns. We need to clarify.

**Resolution**: The effect supports two main video inputs: `tex0` (primary) and `tex1` (secondary). The `hasDualInput` flag indicates if `tex1` is connected. The datamosh step could use either `tex0` or `tex1` based on configuration. For simplicity, we'll define that `tex0` is the main input, and `tex1` can be used as an alternate source for the datamosh block comparison (controlled by a uniform `use_dual_input`). The legacy code's intent: Video B is the "pixel source" that gets datamoshed. So the pipeline might be: `tex0` → pre/depth loops → then use `tex1` for datamosh source? That seems odd. Let's re-read: The effect description says "DUAL VIDEO INPUT: tex0 = Video A, tex1 = Video B". The shader uses `tex0` for `signal` and `block_current`. Maybe `tex1` is used for something else like a mask or secondary feedback. The `hasDualInput` check is used to decide whether to sample `tex1` for something? Actually the snippet shows `bool hasDualInput = ...` but then doesn't use it. So it's likely incomplete.

Given the ambiguity, we'll document that the effect supports two video inputs and the `hasDualInput` flag is available, but the exact usage should be verified against the full legacy implementation. For the spec, we'll state that `tex1` is optional and can be used as an alternate source for the datamosh or for mixing.

### Parameter Summary

| Parameter | Type | Range | Purpose |
|-----------|------|-------|---------|
| `depth_modulation` | float | 0.0-10.0 | Controls how much depth affects the effect intensity |
| `depth_threshold` | float | 0.0-1.0 | Threshold for depth to be considered "close" |
| `invert_depth` | int | 0/1 | Invert depth mapping (far becomes close) |
| `mosh_intensity` | float | 0.0-10.0 | Strength of datamosh displacement |
| `mosh_threshold` | float | 0.0-10.0 | Motion threshold to trigger datamosh |
| `block_size` | float | 0.0-1.0 (scaled) | Size of blocks for motion detection (4-164 pixels) |
| `feedback_amount` | float | 0.0-10.0 | Amount of previous frame to mix in |
| `u_mix` | float | 0.0-1.0 | Overall wet/dry mix |
| `enable_pre_loop` | int | 0/1 | Enable PRE_LOOP injection |
| `pre_loop_mix` | float | 0.0-1.0 | Mix ratio for PRE_LOOP |
| `enable_depth_loop` | int | 0/1 | Enable DEPTH_LOOP injection |
| `depth_loop_mix` | float | 0.0-1.0 | Mix ratio for DEPTH_LOOP |
| `enable_mosh_loop` | int | 0/1 | Enable MOSH_LOOP injection |
| `mosh_loop_mix` | float | 0.0-1.0 | Mix ratio for MOSH_LOOP |
| `enable_post_loop` | int | 0/1 | Enable POST_LOOP injection |
| `post_loop_mix` | float | 0.0-1.0 | Mix ratio for POST_LOOP |

---

## Integration

### VJLive3 Pipeline Integration

The `DepthLoopInjectionDatamoshEffect` is a **frame processor** that sits in the video effects chain. It is unique because it requires additional textures from external effects that are injected at the loop points. This makes it a **hub** in a larger graph.

**Typical setup**:

1. The pipeline creates 4 additional FBOs for the loop returns (one per stage)
2. For each loop stage that is enabled:
   - Render the external effect into the corresponding loop return texture
   - This may involve routing the appropriate intermediate texture to the external effect's input
3. Call `DepthLoopInjectionDatamoshEffect.process_frame()` with:
   - `tex0`: main video input
   - `tex1`: secondary video input (optional)
   - `depth_tex`: depth map
   - `texPrev`: previous output (for feedback and datamosh)
   - Loop return textures (the results from step 2)
4. The effect returns the processed output texture
5. This output becomes `texPrev` for the next frame (ping-pong)

**Loop management**: The system must ensure that loop effects are rendered in the correct order before the main effect runs. For example, if PRE_LOOP is enabled, the external effect assigned to PRE_LOOP must render into `pre_loop_return` before this effect's shader executes.

**Texture format**: All textures should be RGBA (or at least RGB) with the same resolution. Depth texture can be single-channel (R) but is often stored as RGBA for compatibility.

### Shader Management

The effect inherits from `Effect` base class. It compiles a fragment shader that includes all the pipeline logic. The vertex shader is a standard full-screen quad.

Uniforms must be set each frame:
- All loop enable/mix uniforms
- Depth/datamosh parameters
- Texture unit bindings (tex0, tex1, texPrev, depth_tex, and 4 loop returns)
- `time` and `resolution`
- `u_mix`

---

## Performance

### Computational Cost

The effect is **GPU-bound**. The fragment shader performs:

- **Texture samples**: 
  - Always: tex0, texPrev, depth_tex (3 samples)
  - Plus up to 4 loop return samples (if enabled)
  - Plus tex1 if used (optional)
  - Total: 3-8 texture samples per fragment
- **Arithmetic**: Depth modulation, motion detection (block-based), mixing operations
- **Block processing**: For datamosh, the shader computes block UVs and samples block_current and block_prev. This adds 2 extra texture samples per fragment (but these are at block resolution, not per-fragment? Actually the shader samples at `block_uv` which is the same for all fragments in a block, but it's still executed per fragment. So each fragment does 2 additional samples. That's expensive.

**Performance estimate** (1080p):
- Base shader (no loops): ~2-3 ms
- With all 4 loops enabled: ~4-6 ms (due to extra texture samples)
- Memory bandwidth is the main bottleneck

### Memory Usage

- **GPU memory**:
  - Input textures: tex0, tex1, depth_tex, texPrev (4 × full-res)
  - Loop return textures: 4 × full-res (if allocated, even if not used)
  - Output texture (ping-pong)
  - Total: ~9 full-resolution textures (RGBA8) = 9 × (1920×1080×4) ≈ 74 MB at 1080p
- **CPU memory**: Minimal (uniforms, state)

### Optimization Strategies

1. **Conditional sampling**: The shader already conditionally samples loop returns based on `enable_*` uniforms. This avoids unnecessary texture fetches when loops are disabled.
2. **Block size optimization**: Larger `block_size` reduces texture samples for block_current/block_prev? Actually the shader still samples per fragment, but the block_uv is the same for many fragments, so the GPU's texture cache can help. However, the samples are not shared across fragments in the shader execution; each fragment independently computes block_uv and samples. To truly reduce samples, one would need to use compute shader or image load/store. Not easily optimizable.
3. **Loop texture format**: If loop returns are not needed at full resolution, they could be lower resolution, but then mixing would look bad.
4. **Early-out**: If all loops are disabled and `u_mix` is 0, the shader could just output `signal` directly and skip heavy calculations. Add a uniform `effect_enabled` to short-circuit.
5. **Resolution scaling**: Render at lower internal resolution and upscale.

### Platform-Specific Considerations

- **Desktop**: 1080p at 60fps should be achievable with moderate GPU (GTX 1060+)
- **4K**: May require reducing loop count or lowering resolution
- **Embedded**: Likely too heavy; consider simplifying or disabling loops

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect initializes without crashing if OpenGL context missing; raises clear error |
| `test_basic_operation` | Effect processes frame and returns output different from input when u_mix > 0 |
| `test_pre_loop_injection` | When pre_loop_return texture contains distinct content, it mixes into stage1_output according to pre_loop_mix |
| `test_depth_loop_injection` | When depth_loop_return contains content, it mixes into stage2_output according to depth_loop_mix |
| `test_mosh_loop_injection` | When mosh_loop_return contains content, it mixes into stage3_output according to mosh_loop_mix |
| `test_post_loop_injection` | When post_loop_return contains content, it mixes into stage4_output according to post_loop_mix |
| `test_loop_bypass` | When enable_* = 0, the corresponding loop return is ignored (dry signal passes) |
| `test_depth_modulation` | Changing depth_modulation affects the modulated_intensity used in datamosh blend |
| `test_invert_depth` | Setting invert_depth=1 reverses depth effect |
| `test_datamosh_motion` | Areas with high motion between frames show displacement (check pixel coordinates) |
| `test_datamosh_threshold` | Motion below mosh_threshold produces no displacement |
| `test_feedback` | Setting feedback_amount > 0 creates trails (previous frame visible) |
| `test_final_mix` | u_mix=0 returns original signal; u_mix=1 returns fully processed stage4_output |
| `test_dual_input` | When tex1 is provided and non-zero, it is used appropriately (determine exact behavior) |
| `test_parameter_validation` | Out-of-range parameters are clamped or raise errors |
| `test_cleanup` | All OpenGL resources (FBOs, textures, shader) are released on stop() |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

### [NEEDS RESEARCH]: How is `tex1` (Video B) used in the legacy implementation?

**Finding**: The shader declares `uniform sampler2D tex1` and checks `hasDualInput` but doesn't actually use it in the shown snippets. The comment says "Video B — pixel source (what gets datamoshed)". Possibly the datamosh step should use `tex1` as the source for `block_current` instead of `tex0` when dual input is present.

**Resolution**: We'll define that `tex1` is an optional secondary input. When `hasDualInput` is true, the datamosh uses `tex1` as the source for motion detection and for the displaced sample. That is, `block_current = texture(tex1, block_uv)` and `datamoshed = texture(tex1, mosh_uv)`. This makes sense: you have a foreground video (tex0) and a background or effect video (tex1) that gets datamoshed and mixed. Actually the legacy comment: "tex1 = Video B — pixel source (what gets datamoshed)" suggests tex1 is the main source for datamosh. But the shader uses `tex0` for `signal` and `block_current`. Inconsistency.

Let's re-analyze: The effect is called "DepthLoopInjectionDatamosh". It might be that tex0 is the depth-modulated video, and tex1 is the original video? Or tex0 is the "clean" feed and tex1 is the "datamosh" feed. The loop returns could be effects applied to either. Without full code, it's ambiguous.

**Proposed design for VJLive3**: 
- `tex0`: Primary video input (the main signal)
- `tex1`: Secondary video input (optional, used as source for datamosh if provided)
- If `tex1` is not provided (all black), use `tex0` for everything.
- If `tex1` is provided, use `tex0` as the base signal for pre/depth loops, but use `tex1` as the source for datamosh displacement (i.e., `block_current` and `datamoshed` sample from `tex1`). This allows you to datamosh a different video than the one you're depth-modulating.

We'll document this as the intended behavior and mark as NEEDS RESEARCH to verify against legacy.

### [NEEDS RESEARCH]: What is the exact formula for `depth_factor` and why those hardcoded values (0.3, 3.7)?

**Finding**: The legacy uses:
```glsl
float depth_factor = (depth - 0.3) / 3.7;
```
This remaps depth from [0.3, 4.0] to [0,1]. But depth is typically 0-1, so values >1 are impossible unless depth is in a different range (e.g., 0-10 or raw depth in arbitrary units). Possibly the depth map is normalized to 0-10 or 0-4? The 0.3 and 3.7 suggest the expected depth range is 0.3 to 4.0.

**Resolution**: The depth map should be provided in a range that matches these expectations, or the shader should be adjusted to accept 0-1 depth. We can make the depth remapping configurable via parameters `depth_min` and `depth_max` instead of hardcoding. That would be more flexible. The spec should allow these parameters.

### [NEEDS RESEARCH]: How are loop return textures updated? Are they FBOs that are rendered to each frame?

**Finding**: The legacy likely uses FBOs. Each loop's external effect renders into a texture that is then bound as the loop return uniform for this effect.

**Resolution**: The VJLive3 implementation should require the caller to provide these textures. The effect itself does not manage FBOs for the loops; it only samples them. The pipeline or graph manager is responsible for creating the FBOs and rendering the loop effects into them before calling this effect.

### [NEEDS RESEARCH]: The `u_decay` uniform is declared in the BassCannon effect but not used; is there missing code?

**Finding**: Not directly relevant to this effect, but similar pattern: some uniforms may be placeholders. In this effect, all declared uniforms appear to be used.

---

## Configuration Schema

```python
METADATA = {
  "params": [
    # Depth modulation
    {"id": "depth_modulation", "name": "Depth Modulation", "default": 1.0, "min": 0.0, "max": 10.0, "type": "float", "description": "How much depth affects effect intensity"},
    {"id": "depth_threshold", "name": "Depth Threshold", "default": 0.5, "min": 0.0, "max": 1.0, "type": "float", "description": "Depth value threshold for modulation"},
    {"id": "invert_depth", "name": "Invert Depth", "default": 0, "min": 0, "max": 1, "type": "int", "description": "Invert depth mapping (0=normal, 1=inverted)"},
    {"id": "depth_min", "name": "Depth Min", "default": 0.3, "min": 0.0, "max": 10.0, "type": "float", "description": "Minimum expected depth value for remapping"},
    {"id": "depth_max", "name": "Depth Max", "default": 4.0, "min": 0.1, "max": 10.0, "type": "float", "description": "Maximum expected depth value for remapping"},
    
    # Datamosh
    {"id": "mosh_intensity", "name": "Mosh Intensity", "default": 1.0, "min": 0.0, "max": 10.0, "type": "float", "description": "Strength of pixel displacement"},
    {"id": "mosh_threshold", "name": "Mosh Threshold", "default": 0.5, "min": 0.0, "max": 10.0, "type": "float", "description": "Motion threshold to trigger datamosh"},
    {"id": "block_size", "name": "Block Size", "default": 0.5, "min": 0.0, "max": 1.0, "type": "float", "description": "Size of motion detection blocks (0=4px, 1=164px)"},
    
    # Feedback
    {"id": "feedback_amount", "name": "Feedback Amount", "default": 0.5, "min": 0.0, "max": 10.0, "type": "float", "description": "How much previous frame to mix in"},
    
    # Loop controls (4 stages)
    {"id": "enable_pre_loop", "name": "Enable Pre Loop", "default": 0, "min": 0, "max": 1, "type": "int", "description": "Enable PRE_LOOP injection"},
    {"id": "pre_loop_mix", "name": "Pre Loop Mix", "default": 1.0, "min": 0.0, "max": 1.0, "type": "float", "description": "Wet/dry mix for PRE_LOOP"},
    {"id": "enable_depth_loop", "name": "Enable Depth Loop", "default": 0, "min": 0, "max": 1, "type": "int", "description": "Enable DEPTH_LOOP injection"},
    {"id": "depth_loop_mix", "name": "Depth Loop Mix", "default": 1.0, "min": 0.0, "max": 1.0, "type": "float", "description": "Wet/dry mix for DEPTH_LOOP"},
    {"id": "enable_mosh_loop", "name": "Enable Mosh Loop", "default": 0, "min": 0, "max": 1, "type": "int", "description": "Enable MOSH_LOOP injection"},
    {"id": "mosh_loop_mix", "name": "Mosh Loop Mix", "default": 1.0, "min": 0.0, "max": 1.0, "type": "float", "description": "Wet/dry mix for MOSH_LOOP"},
    {"id": "enable_post_loop", "name": "Enable Post Loop", "default": 0, "min": 0, "max": 1, "type": "int", "description": "Enable POST_LOOP injection"},
    {"id": "post_loop_mix", "name": "Post Loop Mix", "default": 1.0, "min": 0.0, "max": 1.0, "type": "float", "description": "Wet/dry mix for POST_LOOP"},
    
    # Overall
    {"id": "u_mix", "name": "Output Mix", "default": 1.0, "min": 0.0, "max": 1.0, "type": "float", "description": "Final wet/dry blend (0=original, 1=fully processed)"},
    {"id": "use_dual_input", "name": "Use Dual Input", "default": 0, "min": 0, "max": 1, "type": "int", "description": "If 1, use tex1 as datamosh source instead of tex0"},
  ]
}
```

**Presets**: Not defined in legacy; could be added (e.g., "subtle", "aggressive", "glitch").

---

## State Management

- **Per-frame state**: `time` (incremented each frame), `texPrev` (previous output texture). These are provided by the pipeline.
- **Persistent state**: All uniform parameters (depth_modulation, mosh_intensity, loop enables/mixes, etc.). These can be changed at runtime.
- **Init-once state**: Compiled shader program, uniform locations, FBOs for output (if the effect manages its own output FBO). The loop return textures are external and not owned by this effect.
- **Thread safety**: Not thread-safe. Must be called from the thread with active OpenGL context.

---

## GPU Resources

This effect is **GPU-accelerated** and requires OpenGL 3.3+. It uses:

- **Fragment shader**: The full pipeline shader (see legacy)
- **Vertex shader**: Pass-through
- **FBOs**: The effect likely needs an FBO for its output if the result is to be used as texture for subsequent effects. However, the effect could also render directly to the screen if it's the last in the chain. The spec should allow both.
- **Textures**: 
  - Inputs: tex0, tex1, depth_tex, texPrev, and up to 4 loop return textures
  - Output: either to default framebuffer or to an FBO

If GPU resources are exhausted, the effect should raise an exception.

---

## Public Interface

```python
class DepthLoopInjectionDatamoshEffect(Effect):
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the effect with configuration.
        
        Args:
            config: Dictionary of parameters (see METADATA). Missing values use defaults.
        """
    
    def process_frame(self, frame_data: Dict[str, Any]) -> np.ndarray:
        """
        Process a video frame through the depth+datamosh pipeline with loop injection.
        
        Args:
            frame_data: Dictionary containing:
                - 'tex0': OpenGL texture ID for Video A (primary input)
                - 'tex1': OpenGL texture ID for Video B (secondary input, optional)
                - 'depth_tex': OpenGL texture ID for depth map
                - 'texPrev': OpenGL texture ID for previous frame output (feedback)
                - 'pre_loop_return': OpenGL texture ID from PRE_LOOP effect (if enabled)
                - 'depth_loop_return': OpenGL texture ID from DEPTH_LOOP effect (if enabled)
                - 'mosh_loop_return': OpenGL texture ID from MOSH_LOOP effect (if enabled)
                - 'post_loop_return': OpenGL texture ID from POST_LOOP effect (if enabled)
                - 'resolution': (width, height) tuple
                - 'time': current time in seconds (optional, can use internal timer)
            
        Returns:
            OpenGL texture ID of the processed frame (may be newly created FBO or provided output)
        """
    
    def set_parameter(self, name: str, value: Any) -> None:
        """Set a parameter at runtime."""
    
    def get_parameter(self, name: str) -> Any:
        """Get current parameter value."""
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return effect metadata for UI."""
        return {
            "tags": ["depth", "datamosh", "modular", "routing", "feedback"],
            "mood": ["glitchy", "immersive", "layered"],
            "visual_style": ["depth-based", "motion-smear", "feedback-loops"]
        }
    
    def stop(self) -> None:
        """Release GPU resources."""
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `config` | `Dict[str, Any]` | Configuration parameters | See METADATA |
| `frame_data['tex0']` | `int` (GL texture) | Primary video input | Must be valid RGBA texture |
| `frame_data['tex1']` | `int` (GL texture) | Secondary video input (optional) | If 0, ignored |
| `frame_data['depth_tex']` | `int` (GL texture) | Depth map | Single channel (R) or RGBA; values in expected range |
| `frame_data['texPrev']` | `int` (GL texture) | Previous frame output | Same resolution as inputs |
| `frame_data['pre_loop_return']` | `int` (GL texture) | PRE_LOOP effect output | Valid texture if enable_pre_loop=1 |
| `frame_data['depth_loop_return']` | `int` (GL texture) | DEPTH_LOOP effect output | Valid texture if enable_depth_loop=1 |
| `frame_data['mosh_loop_return']` | `int` (GL texture) | MOSH_LOOP effect output | Valid texture if enable_mosh_loop=1 |
| `frame_data['post_loop_return']` | `int` (GL texture) | POST_LOOP effect output | Valid texture if enable_post_loop=1 |
| `frame_data['resolution']` | `(int, int)` | Frame resolution | width, height > 0 |
| `frame_data['time']` | `float` | Current time in seconds | Optional; if not provided, use internal timer |
| `return` | `int` (GL texture) | Processed output frame | Ready for display or further processing |

---

## Dependencies

- External libraries:
  - `OpenGL.GL` — required for shader rendering
  - `numpy` — for texture data handling if needed
- Internal modules:
  - `vjlive3.core.effects.shader_base.Effect` — base class
  - `vjlive3.core.audio_reactor.AudioReactor` (optional) — if audio influences parameters
  - `vjlive3.utils.texture_manager.TextureManager` — for managing FBOs and textures

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect initializes without crashing if OpenGL context missing; raises clear error |
| `test_basic_operation` | Effect processes frame and returns output different from input when u_mix > 0 |
| `test_pre_loop_injection` | When pre_loop_return texture contains distinct content, it mixes into stage1_output according to pre_loop_mix |
| `test_depth_loop_injection` | When depth_loop_return contains content, it mixes into stage2_output according to depth_loop_mix |
| `test_mosh_loop_injection` | When mosh_loop_return contains content, it mixes into stage3_output according to mosh_loop_mix |
| `test_post_loop_injection` | When post_loop_return contains content, it mixes into stage4_output according to post_loop_mix |
| `test_loop_bypass` | When enable_* = 0, the corresponding loop return is ignored (dry signal passes) |
| `test_depth_modulation` | Changing depth_modulation affects the modulated_intensity used in datamosh blend |
| `test_invert_depth` | Setting invert_depth=1 reverses depth effect |
| `test_datamosh_motion` | Areas with high motion between frames show displacement (check pixel coordinates) |
| `test_datamosh_threshold` | Motion below mosh_threshold produces no displacement |
| `test_feedback` | Setting feedback_amount > 0 creates trails (previous frame visible) |
| `test_final_mix` | u_mix=0 returns original signal; u_mix=1 returns fully processed stage4_output |
| `test_dual_input` | When tex1 is provided and non-zero, it is used appropriately (determine exact behavior) |
| `test_parameter_validation` | Out-of-range parameters are clamped or raise errors |
| `test_cleanup` | All OpenGL resources (FBOs, textures, shader) are released on stop() |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT054: DepthLoopInjectionDatamoshEffect implementation` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Complete Class Structure
```python
from core.effects.shader_base import Effect
from core.audio_reactor import AudioReactor
from core.audio_analyzer import AudioFeature
from OpenGL.GL import (glGenTextures, glBindTexture, glTexParameteri, glTexImage2D,
                     GL_TEXTURE_2D, GL_LINEAR, GL_CLAMP_TO_EDGE, GL_RED,
                     GL_UNSIGNED_BYTE, glActiveTexture, GL_TEXTURE0)
import numpy as np


class DepthLoopInjectionDatamoshEffect(Effect):
    """
    Depth Loop Injection Datamosh
    A ROUTEABLE datamosh effect with explicit send/return loop points for inserting
    other effects into the datamosh processing chain.
    
    This is fundamentally different from other effects — it's designed as a MODULAR
    ROUTING HUB where you can inject arbitrary effects at different stages of the
    datamosh pipeline. Think of it like eurorack send/return patching but for video.
    
    Loop insertion points:
      1. PRE_LOOP: Before depth modulation (raw video → ext → depth modulated)
      2. DEPTH_LOOP: After depth modulation, before datamosh (depth video → ext → datamos)
      3. MOSH_LOOP: After datamosh, before feedback (datamoshed → ext → feedback)
      4. POST_LOOP: After feedback, before final mix (feedback → ext → output)
    
    Each loop has:
      - wet/dry mix control
      - loop can be bypassed
      - loop can be fed to other graph nodes
      - multiple loops can be active simultaneously
    """
    
    def __init__(self, config: dict):
        # Load shader from file or use fallback
        shader_path = self._find_shader_path("depth_loop_injection_datamosh.frag")
        try:
            with open(shader_path, 'r') as f:
                fragment_source = f.read()
        except FileNotFoundError:
            # Fallback inline shader (complete version below)
            fragment_source = self.DEPTH_LOOP_INJECTION_FRAGMENT
        
        super().__init__("depth_loop_injection_datamosh", fragment_source)
        
        # Initialize parameters from config with defaults
        params = config.get('params', {})
        
        # Depth modulation
        self.set_parameter("depth_modulation", params.get('depth_modulation', 1.0))
        self.set_parameter("depth_threshold", params.get('depth_threshold', 0.5))
        self.set_parameter("invert_depth", params.get('invert_depth', 0))
        self.set_parameter("depth_min", params.get('depth_min', 0.3))
        self.set_parameter("depth_max", params.get('depth_max', 4.0))
        
        # Datamosh
        self.set_parameter("mosh_intensity", params.get('mosh_intensity', 1.0))
        self.set_parameter("mosh_threshold", params.get('mosh_threshold', 0.5))
        self.set_parameter("block_size", params.get('block_size', 0.5))
        
        # Feedback
        self.set_parameter("feedback_amount", params.get('feedback_amount', 0.5))
        
        # Loop controls
        self.set_parameter("enable_pre_loop", params.get('enable_pre_loop', 0))
        self.set_parameter("pre_loop_mix", params.get('pre_loop_mix', 1.0))
        self.set_parameter("enable_depth_loop", params.get('enable_depth_loop', 0))
        self.set_parameter("depth_loop_mix", params.get('depth_loop_mix', 1.0))
        self.set_parameter("enable_mosh_loop", params.get('enable_mosh_loop', 0))
        self.set_parameter("mosh_loop_mix", params.get('mosh_loop_mix', 1.0))
        self.set_parameter("enable_post_loop", params.get('enable_post_loop', 0))
        self.set_parameter("post_loop_mix", params.get('post_loop_mix', 1.0))
        
        # Overall mix
        self.set_parameter("u_mix", params.get('u_mix', 1.0))
        self.set_parameter("use_dual_input", params.get('use_dual_input', 0))
        
        # State tracking
        self._prev_time = 0.0
        self._texture_cache = {}
    
    def process_frame(self, frame_data: dict):
        """
        Process a video frame through the depth+datamosh pipeline with loop injection.
        
        Args:
            frame_data: Dictionary containing:
                - 'tex0': OpenGL texture ID for Video A (primary input)
                - 'tex1': OpenGL texture ID for Video B (secondary input, optional)
                - 'depth_tex': OpenGL texture ID for depth map
                - 'texPrev': OpenGL texture ID for previous frame output (feedback)
                - 'pre_loop_return': OpenGL texture ID from PRE_LOOP effect (if enabled)
                - 'depth_loop_return': OpenGL texture ID from DEPTH_LOOP effect (if enabled)
                - 'mosh_loop_return': OpenGL texture ID from MOSH_LOOP effect (if enabled)
                - 'post_loop_return': OpenGL texture ID from POST_LOOP effect (if enabled)
                - 'resolution': (width, height) tuple
                - 'time': current time in seconds (optional)
        
        Returns:
            OpenGL texture ID of the processed frame
        """
        # Apply all uniforms
        self._apply_all_uniforms(frame_data)
        
        # Render to output texture (or FBO managed by pipeline)
        self._render_fullscreen_quad()
        
        # Return the output texture ID (managed by base class)
        return self.output_texture
    
    def _apply_all_uniforms(self, frame_data: dict):
        """Set all shader uniforms for this frame."""
        # Basic uniforms
        self.shader.set_uniform("time", frame_data.get('time', 0.0))
        self.shader.set_uniform("resolution", frame_data['resolution'])
        self.shader.set_uniform("u_mix", self.get_parameter('u_mix'))
        
        # Depth parameters
        self.shader.set_uniform("depth_modulation", self.get_parameter('depth_modulation'))
        self.shader.set_uniform("depth_threshold", self.get_parameter('depth_threshold'))
        self.shader.set_uniform("invert_depth", self.get_parameter('invert_depth'))
        self.shader.set_uniform("depth_min", self.get_parameter('depth_min'))
        self.shader.set_uniform("depth_max", self.get_parameter('depth_max'))
        
        # Datamosh parameters
        self.shader.set_uniform("mosh_intensity", self.get_parameter('mosh_intensity'))
        self.shader.set_uniform("mosh_threshold", self.get_parameter('mosh_threshold'))
        self.shader.set_uniform("block_size", self.get_parameter('block_size'))
        
        # Feedback
        self.shader.set_uniform("feedback_amount", self.get_parameter('feedback_amount'))
        
        # Loop enables and mixes
        self.shader.set_uniform("enable_pre_loop", self.get_parameter('enable_pre_loop'))
        self.shader.set_uniform("pre_loop_mix", self.get_parameter('pre_loop_mix'))
        self.shader.set_uniform("enable_depth_loop", self.get_parameter('enable_depth_loop'))
        self.shader.set_uniform("depth_loop_mix", self.get_parameter('depth_loop_mix'))
        self.shader.set_uniform("enable_mosh_loop", self.get_parameter('enable_mosh_loop'))
        self.shader.set_uniform("mosh_loop_mix", self.get_parameter('mosh_loop_mix'))
        self.shader.set_uniform("enable_post_loop", self.get_parameter('enable_post_loop'))
        self.shader.set_uniform("post_loop_mix", self.get_parameter('post_loop_mix'))
        
        self.shader.set_uniform("use_dual_input", self.get_parameter('use_dual_input'))
        
        # Bind textures
        self._bind_texture('tex0', frame_data['tex0'], 0)
        self._bind_texture('tex1', frame_data.get('tex1', 0), 1)
        self._bind_texture('texPrev', frame_data['texPrev'], 2)
        self._bind_texture('depth_tex', frame_data['depth_tex'], 3)
        self._bind_texture('pre_loop_return', frame_data.get('pre_loop_return', 0), 4)
        self._bind_texture('depth_loop_return', frame_data.get('depth_loop_return', 0), 5)
        self._bind_texture('mosh_loop_return', frame_data.get('mosh_loop_return', 0), 6)
        self._bind_texture('post_loop_return', frame_data.get('post_loop_return', 0), 7)
    
    def _bind_texture(self, name: str, texture_id: int, unit: int):
        """Bind a texture to a specific texture unit."""
        if texture_id == 0:
            # Bind a default 1x1 black texture for missing inputs
            texture_id = self._get_default_texture()
        self.shader.set_uniform(name, texture_id, texture_unit=unit)
    
    def _get_default_texture(self) -> int:
        """Get or create a default 1x1 black texture."""
        if 'default' not in self._texture_cache:
            # Create a 1x1 black texture
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, 1, 1, 0, GL_RED, GL_UNSIGNED_BYTE, np.zeros((1, 1, 1), dtype=np.uint8))
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            self._texture_cache['default'] = tex_id
        return self._texture_cache['default']
    
    def stop(self):
        """Release GPU resources."""
        # Delete default texture if created
        if 'default' in self._texture_cache:
            glDeleteTextures([self._texture_cache['default']])
        super().stop()
```

## Complete Shader Architecture
The fragment shader implements the full modular pipeline with 4 loop injection points:

### Full GLSL Shader (depth_loop_injection_datamosh.frag)
```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;             // Original input (Video A)
uniform sampler2D tex1;             // Video B — pixel source (what gets datamoshed)
uniform sampler2D texPrev;          // Previous frame
uniform sampler2D depth_tex;        // Depth map

// Loop return textures
uniform sampler2D pre_loop_return;   // Return from PRE loop
uniform sampler2D depth_loop_return; // Return from DEPTH loop
uniform sampler2D mosh_loop_return;  // Return from MOSH loop
uniform sampler2D post_loop_return;  // Return from POST loop

uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Loop enables and mixes
uniform int enable_pre_loop;        // 0/1
uniform float pre_loop_mix;         // 0-1
uniform int enable_depth_loop;
uniform float depth_loop_mix;
uniform int enable_mosh_loop;
uniform float mosh_loop_mix;
uniform int enable_post_loop;
uniform float post_loop_mix;

// Standard depth+datamosh parameters
uniform float depth_modulation;
uniform float depth_threshold;
uniform int invert_depth;

uniform float mosh_intensity;
uniform float mosh_threshold;
uniform float block_size;
uniform float feedback_amount;

// Optional: configurable depth range (more flexible than hardcoded 0.3, 3.7)
uniform float depth_min;
uniform float depth_max;

// Hash for noise (currently unused but reserved for future enhancements)
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(443.897, 441.423))) * 43758.5453);
}

void main() {
    // Detect if Video B is connected (not all black)
    vec4 testB = texture(tex1, vec2(0.5));
    bool hasDualInput = (testB.r + testB.g + testB.b) > 0.01;
    
    vec4 signal = texture(tex0, uv);
    vec4 previous = texture(texPrev, uv);
    float depth = texture(depth_tex, uv).r;
    
    // ====== LOOP STAGE 1: PRE_LOOP ======
    // This happens before ANY depth processing
    vec4 stage1_output = signal;
    if (enable_pre_loop == 1) {
        vec4 loop_return = texture(pre_loop_return, uv);
        stage1_output = mix(stage1_output, loop_return, pre_loop_mix);
    }
    
    // ====== DEPTH MODULATION ======
    // Remap depth from [depth_min, depth_max] to [0, 1]
    float depth_factor = (depth - depth_min) / (depth_max - depth_min);
    if (invert_depth == 1) depth_factor = 1.0 - depth_factor;
    depth_factor = clamp(depth_factor, 0.0, 1.0);
    
    // Modulated intensity affects datamosh strength
    float modulated_intensity = mix(0.3, 1.0, depth_factor * depth_modulation);
    
    // ====== LOOP STAGE 2: DEPTH_LOOP ======
    // After depth modulation, before datamosh
    vec4 stage2_output = stage1_output;
    if (enable_depth_loop == 1) {
        vec4 loop_return = texture(depth_loop_return, uv);
        stage2_output = mix(stage2_output, loop_return, depth_loop_mix);
    }
    
    // ====== DATAMOSH ======
    // Block size: map from 0-1 to 4-164 pixels
    float block = max(4.0, block_size * 40.0 + 4.0);
    vec2 block_uv = floor(uv * resolution / block) * block / resolution;
    
    // Choose source for motion detection based on dual input flag
    vec4 block_current;
    if (hasDualInput && use_dual_input == 1) {
        block_current = texture(tex1, block_uv);
    } else {
        block_current = texture(tex0, block_uv);
    }
    vec4 block_prev = texture(texPrev, block_uv);
    vec3 block_diff = block_current.rgb - block_prev.rgb;
    float motion = length(block_diff);
    
    vec2 displacement = vec2(0.0);
    if (motion > mosh_threshold * 0.1) {
        displacement = block_diff.rg * modulated_intensity * mosh_intensity * 0.05;
    }
    
    vec2 mosh_uv = uv + displacement;
    mosh_uv = clamp(mosh_uv, 0.001, 0.999);
    
    // Sample displaced pixel from previous frame (or from tex1 if dual input)
    vec4 datamoshed;
    if (hasDualInput && use_dual_input == 1) {
        datamoshed = texture(tex1, mosh_uv);
    } else {
        datamoshed = texture(texPrev, mosh_uv);
    }
    
    float blend_factor = smoothstep(mosh_threshold * 0.05, mosh_threshold * 0.15, motion);
    blend_factor *= modulated_intensity;
    
    vec4 mosh_result = mix(stage2_output, datamoshed, blend_factor);
    
    // ====== LOOP STAGE 3: MOSH_LOOP ======
    // After datamosh, before feedback
    vec4 stage3_output = mosh_result;
    if (enable_mosh_loop == 1) {
        vec4 loop_return = texture(mosh_loop_return, uv);
        stage3_output = mix(mosh_result, loop_return, mosh_loop_mix);
    }
    
    // ====== FEEDBACK ======
    vec4 with_feedback = mix(stage3_output, previous, feedback_amount * 0.5);
    
    // ====== LOOP STAGE 4: POST_LOOP ======
    // Final loop after feedback
    vec4 stage4_output = with_feedback;
    if (enable_post_loop == 1) {
        vec4 loop_return = texture(post_loop_return, uv);
        stage4_output = mix(with_feedback, loop_return, post_loop_mix);
    }
    
    // ====== FINAL OUTPUT ======
    fragColor = mix(signal, stage4_output, u_mix);
}
```

### Algorithm Deep Dive
1. **Dual Input Detection**: The shader samples `tex1` at the center to determine if a secondary video input is connected (non-black). This allows flexible routing.
2. **PRE_LOOP**: The raw input signal (`tex0`) can be mixed with an external effect's output before any depth processing. This is the first opportunity to inject processing.
3. **Depth Modulation**: The depth map is remapped from user-configurable `[depth_min, depth_max]` to [0,1], optionally inverted. The `modulated_intensity` is computed as a blend between 0.3 and 1.0 based on `depth_factor * depth_modulation`. This intensity scales the datamosh displacement.
4. **DEPTH_LOOP**: After depth modulation, another external effect can be mixed in before datamoshing occurs.
5. **Datamosh**:
   - The image is divided into blocks (size: 4 to 164 pixels based on `block_size` parameter)
   - Motion is detected by comparing current and previous frame blocks (using `tex0` or `tex1` depending on `use_dual_input`)
   - Displacement vector = motion vector × `modulated_intensity` × `mosh_intensity` × 0.05
   - The displaced UV samples the previous frame (or `tex1`) to create the smear
   - `blend_factor` uses `smoothstep` to smoothly apply the datamosh based on motion magnitude
6. **MOSH_LOOP**: The datamoshed result can be further processed by an external effect before entering the feedback stage.
7. **Feedback**: The result is mixed with the previous frame (`texPrev`) using `feedback_amount * 0.5` to create trails/echoes.
8. **POST_LOOP**: Final external processing before the output mix.
9. **Final Mix**: The original signal (`signal`) is blended with the fully processed `stage4_output` using `u_mix`.

### Loop Return Texture Management
Each loop stage expects a texture that contains the output of an external effect. These textures must be provided as uniforms and bound to specific texture units:

| Uniform | Texture Unit | Purpose |
|---------|--------------|---------|
| `pre_loop_return` | 4 | Output from effect injected at PRE_LOOP stage |
| `depth_loop_return` | 5 | Output from effect injected at DEPTH_LOOP stage |
| `mosh_loop_return` | 6 | Output from effect injected at MOSH_LOOP stage |
| `post_loop_return` | 7 | Output from effect injected at POST_LOOP stage |

The external effects are rendered separately into these textures (using FBOs) before this effect's `process_frame` is called. The routing system must manage this dependency and ensure proper rendering order.

### Dual Video Input Handling
The effect supports two main video inputs:
- `tex0` (Video A): Primary input, used as the base signal throughout the pipeline
- `tex1` (Video B): Secondary input, optional

When `use_dual_input = 1` and `tex1` is connected (non-black), the datamosh step uses `tex1` as the source for motion detection and displacement sampling instead of `tex0`. This allows creative effects like:
- Using a different video as the datamosh source
- Creating hybrid effects where one video provides the structure and another provides the motion

The `hasDualInput` flag is computed by sampling the center of `tex1` and checking if the sum of RGB channels exceeds 0.01.

## Performance Considerations
- **Texture Samples**: Base (3) + up to 4 loop returns (4) + optional tex1 (1) = 8 total
- **Arithmetic**: Moderate (depth remap, motion calculation, multiple mixes)
- **Block Processing**: The datamosh block calculation adds overhead but is necessary for motion detection
- **Memory Bandwidth**: Primary bottleneck due to multiple texture reads per fragment
- **Estimated 1080p performance**: 4-6 ms with all loops enabled, 2-3 ms with loops disabled

## Error Handling and Edge Cases
- **Missing textures**: The `_bind_texture` method provides a default 1x1 black texture for any missing loop return or secondary input
- **Zero division**: The depth remap uses `(depth_max - depth_min)` which could be zero if misconfigured; should add epsilon protection
- **Out-of-range depth**: Values outside [depth_min, depth_max] are clamped to [0,1] after remap
- **Large block size**: `block_size` is clamped to ensure minimum block size of 4 pixels
- **Feedback initialization**: On first frame, `texPrev` may be uninitialized; should provide a black texture

## Test Plan
| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_shader` | Effect initializes with fallback shader if file missing |
| `test_parameter_setting` | All parameters can be set and retrieved correctly |
| `test_pre_loop_mix` | PRE_LOOP output correctly mixes with base signal |
| `test_depth_loop_mix` | DEPTH_LOOP output correctly mixes after depth modulation |
| `test_mosh_loop_mix` | MOSH_LOOP output correctly mixes after datamosh |
| `test_post_loop_mix` | POST_LOOP output correctly mixes after feedback |
| `test_loop_bypass` | When enable=0, loop return is ignored |
| `test_depth_modulation_range` | Depth values correctly remapped from [depth_min, depth_max] to [0,1] |
| `test_invert_depth` | Setting invert_depth=1 reverses depth effect |
| `test_datamosh_motion` | High motion areas show pixel displacement |
| `test_datamosh_threshold` | Motion below threshold produces no displacement |
| `test_feedback_creates_trails` | feedback_amount > 0 retains previous frame |
| `test_dual_input_detection` | hasDualInput flag correctly set based on tex1 content |
| `test_dual_input_datamosh_source` | When use_dual_input=1, datamosh uses tex1 instead of tex0 |
| `test_final_mix` | u_mix=0 returns original; u_mix=1 returns fully processed |
| `test_all_loops_disabled` | Effect reduces to simple datamosh+feedback when loops bypassed |
| `test_texture_binding` | All texture uniforms are bound to correct texture units |
| `test_cleanup` | All OpenGL resources released on stop() |

**Minimum coverage**: 80% before task is marked done.

## Definition of Done
- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT054: DepthLoopInjectionDatamoshEffect implementation` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

## LEGACY CODE REFERENCES

### vjlive1/plugins/vdepth/depth_loop_injection_datamosh.py (L1-20)
```python
"""
Depth Loop Injection Datamosh
A ROUTEABLE datamosh effect with explicit send/return loop points for inserting
other effects into the datamosh processing chain.

This is fundamentally different from other effects — it's designed as a MODULAR
ROUTING HUB where you can inject arbitrary effects at different stages of the
datamosh pipeline. Think of it like eurorack send/return patching but for video.

Loop insertion points:
  1. PRE_LOOP: Before depth modulation (raw video → ext → depth modulated)
  2. DEPTH_LOOP: After depth modulation, before datamosh (depth video → ext → datamos)
  3. MOSH_LOOP: After datamosh, before feedback (datamoshed → ext → feedback)
  4. POST_LOOP: After feedback, before final mix (feedback → ext → output)

Each loop has:
  - wet/dry mix control
  - loop can be bypassed
  - loop can be fed to other graph nodes
  - multiple loops can be active simultaneously
"""
```

### vjlive1/plugins/vdepth/depth_loop_injection_datamosh.py (L17-36)
```python
  - wet/dry mix control
  - loop can be bypassed
  - loop can be fed to other graph nodes
  - multiple loops can be active simultaneously

This lets you do things like:
  - Inject kaleidoscope between depth modulation and datamosh
  - Insert blur into the feedback path
  - Add color grading post-datamosh
  - Chain multiple effects in creative orders
"""

from core.effects.shader_base import Effect
from core.audio_reactor import AudioReactor
from core.audio_analyzer import AudioFeature
from OpenGL.GL import (glGenTextures, glBindTexture, glTexParameteri, glTexImage2D,
                     GL_TEXTURE_2D, GL_LINEAR, GL_CLAMP_TO_EDGE, GL_RED,
                     GL_UNSIGNED_BYTE, glActiveTexture, GL_TEXTURE0)
import numpy as np
```

### vjlive1/plugins/vdepth/depth_loop_injection_datamosh.py (L33-52)
```python
# Multi-stage shader with loop return points
DEPTH_LOOP_INJECTION_FRAGMENT = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;             // Original input
uniform sampler2D tex1;        // Video B — pixel source (what gets datamoshed)
uniform sampler2D texPrev;          // Previous frame
uniform sampler2D depth_tex;        // Depth map

// Loop return textures
uniform sampler2D pre_loop_return;   // Return from PRE loop
uniform sampler2D depth_loop_return; // Return from DEPTH loop
uniform sampler2D mosh_loop_return;  // Return from MOSH loop
uniform sampler2D post_loop_return;  // Return from POST loop

uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Loop enables and mixes
uniform int enable_pre_loop;        // 0/1
uniform float pre_loop_mix;         // 0-1
uniform int enable_depth_loop;
uniform float depth_loop_mix;
uniform int enable_mosh_loop;
uniform float mosh_loop_mix;
uniform int enable_post_loop;
uniform float post_loop_mix;
```

### vjlive1/plugins/vdepth/depth_loop_injection_datamosh.py (L65-84)
```python
// Standard depth+datamosh parameters
uniform float depth_modulation;
uniform float depth_threshold;
uniform int invert_depth;

uniform float mosh_intensity;
uniform float mosh_threshold;
uniform float block_size;
uniform float feedback_amount;

// Hash for noise
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(443.897, 441.423))) * 43758.5453);
}

void main() {
```

### vjlive1/plugins/vdepth/depth_loop_injection_datamosh.py (L81-100)
```python
void main() {

    // Detect if Video B is connected (not all black)
    vec4 testB = texture(tex1, vec2(0.5));
    bool hasDualInput = (testB.r + testB.g + testB.b) > 0.01;

    vec4 signal = texture(tex0, uv);
    vec4 previous = texture(texPrev, uv);
    float depth = texture(depth_tex, uv).r;
    
    // ====== LOOP STAGE 1: PRE_LOOP ======
    // This happens before ANY depth processing
    vec4 stage1_output = signal;
    if (enable_pre_loop == 1) {
        vec4 loop_return = texture(pre_loop_return, uv);
        stage1_output = mix(stage1_output, loop_return, pre_loop_mix);
    }
```

### vjlive1/plugins/vdepth/depth_loop_injection_datamosh.py (L97-116)
```python
    if (enable_pre_loop == 1) {
        vec4 loop_return = texture(pre_loop_return, uv);
        stage1_output = mix(stage1_output, loop_return, pre_loop_mix);
    }
    
    // ====== DEPTH MODULATION ======
    float depth_factor = (depth - 0.3) / 3.7;
    if (invert_depth == 1) depth_factor = 1.0 - depth_factor;
    depth_factor = clamp(depth_factor, 0.0, 1.0);
    
    float modulated_intensity = mix(0.3, 1.0, depth_factor * depth_modulation);
    
    // ====== LOOP STAGE 2: DEPTH_LOOP ======
    // After depth modulation, before datamosh
    vec4 stage2_output = stage1_output;
    if (enable_depth_loop == 1) {
        vec4 loop_return = texture(depth_loop_return, uv);
        stage2_output = mix(stage1_output, loop_return, depth_loop_mix);
    }
```

### vjlive1/plugins/vdepth/depth_loop_injection_datamosh.py (L113-132)
```python
        vec4 loop_return = texture(depth_loop_return, uv);
        stage2_output = mix(stage1_output, loop_return, depth_loop_mix);
    }
    
    // ====== DATAMOSH ======
    float block = max(4.0, block_size * 40.0 + 4.0);
    vec2 block_uv = floor(uv * resolution / block) * block / resolution;
    
    vec4 block_current = texture(tex0, block_uv);
    vec4 block_prev = texture(texPrev, block_uv);
    vec3 block_diff = block_current.rgb - block_prev.rgb;
    float motion = length(block_diff);
    
    vec2 displacement = vec2(0.0);
    if (motion > mosh_threshold * 0.1) {
        displacement = block_diff.rg * modulated_intensity * mosh_intensity * 0.05;
    }
```

### vjlive1/plugins/vdepth/depth_loop_injection_datamosh.py (L129-148)
```python
    }
    
    vec2 mosh_uv = uv + displacement;
    mosh_uv = clamp(mosh_uv, 0.001, 0.999);
    vec4 datamoshed = texture(texPrev, mosh_uv);
    
    float blend_factor = smoothstep(mosh_threshold * 0.05, mosh_threshold * 0.15, motion);
    blend_factor *= modulated_intensity;
    
    vec4 mosh_result = mix(stage2_output, datamoshed, blend_factor);
    
    // ====== LOOP STAGE 3: MOSH_LOOP ======
    // After datamosh, before feedback
    vec4 stage3_output = mosh_result;
    if (enable_mosh_loop == 1) {
        vec4 loop_return = texture(mosh_loop_return, uv);
        stage3_output = mix(mosh_result, loop_return, mosh_loop_mix);
    }
```

### vjlive1/plugins/vdepth/depth_loop_injection_datamosh.py (L145-164)
```python
        stage3_output = mix(mosh_result, loop_return, mosh_loop_mix);
    }
    
    // ====== FEEDBACK ======
    vec4 with_feedback = mix(stage3_output, previous, feedback_amount * 0.5);
    
    // ====== LOOP STAGE 4: POST_LOOP ======
    // Final loop after feedback
    vec4 stage4_output = with_feedback;
    if (enable_post_loop == 1) {
        vec4 loop_return = texture(post_loop_return, uv);
        stage4_output = mix(with_feedback, loop_return, post_loop_mix);
    }
    
    // ====== FINAL OUTPUT ======
    fragColor = mix(signal, stage4_output, u_mix);
}
```

[NEEDS RESEARCH]: The exact handling of `tex1` (dual input) is unclear from the snippets. The `hasDualInput` variable is computed but not used. The intended behavior likely is: when dual input is present, use `tex1` as the source for `block_current` and `datamoshed` samples, while `tex0` remains the base signal. This should be confirmed with the full legacy implementation. Additionally, the depth remapping parameters (0.3, 3.7) are hardcoded; making them configurable would improve flexibility.
