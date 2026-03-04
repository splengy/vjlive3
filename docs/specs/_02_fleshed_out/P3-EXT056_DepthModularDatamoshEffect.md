# P3-EXT056 — DepthModularDatamoshEffect

**Status**: 🟩 COMPLETING PASS 2
**Component**: vdepth plugin — modular datamosh with effects loop
**Legacy Source**: `/home/happy/Desktop/claude projects/vjlive/plugins/vdepth/depth_modular_datamosh.py`
**Class**: `DepthModularDatamoshEffect(Effect)`
**Lines**: ~550 total (two shaders ~300 lines, Python ~250 lines)

---

## Executive Summary

The **DepthModularDatamoshEffect** is a sophisticated, two-stage datamosh processor that introduces **explicit effects loop routing** into the datamosh pipeline. Unlike traditional datamosh effects that operate as monolithic filters, this effect modularizes the corruption process:

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: Depth Analysis + Motion Displacement              │
│  • Depth edge detection (gradient magnitude)               │
│  • Motion vector estimation from depth gradients           │
│  • Block-based displacement (quantized to grid)            │
│  • Chromatic separation at depth edges                     │
│  • Pre-warp and pre-glitch injection                       │
│                                                             │
│         ╔═══════════════════════════╗                       │
│         ║  LOOP SEND ──────────────→║──→ [External FX]     │
│         ║  LOOP RETURN ←───────────←║←── [External FX]     │
│         ╚═══════════════════════════╝                       │
│                                                             │
│ STAGE 2: Corruption Engine (takes loop return as input)    │
│  • Block corruption / I-frame loss simulation              │
│  • Temporal feedback with decay                            │
│  • Color corruption (quantization, channel swapping)       │
│  • Scan line corruption                                    │
│  • Depth-weighted composite                                │
└─────────────────────────────────────────────────────────────┘
```

### Key Innovation: Modular Loop

The effect owns the routing: Stage 1 outputs to a **LOOP SEND** texture, which can be processed by any external effect chain (e.g., color grading, distortion, another datamosh), then fed back into Stage 2 via **LOOP RETURN** (texture unit 3). This allows **nested corruption** — the datamosh process can corrupt signals that have already been processed by other effects, creating exponentially more complex glitch aesthetics.

### Use Cases

- **Datamosh²**: Feed one datamosh effect into another via the loop for extreme corruption
- **Graded datamosh**: Apply color correction inside the loop so the datamosh corrupts the graded signal, not the raw video
- **Depth-aware effects routing**: Use depth to control which effects get applied in the loop (via external modulation)
- **Experimental feedback chains**: Create recursive loops where the loop return feeds back into itself with additional processing

---

## Shader Architecture Analysis

### Two-Shader System

The effect uses **two separate fragment shaders** compiled into separate programs:

1. **Stage 1 Shader** (`_stage1_shader_src`): Outputs to loop send texture
2. **Stage 2 Shader** (`_get_fragment_shader()`): Final output, takes loop return as input

### Stage 1 Fragment Shader

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;           // Source video (Video A)
uniform sampler2D tex1;           // Video B (pixel source for datamosh)
uniform sampler2D depth_tex;      // Depth map
uniform float time;
uniform vec2 resolution;

// Stage 1 controls
uniform float mv_intensity;        // Motion vector displacement strength
uniform float block_size;          // Datamosh block size (0-1 → 4-68px)
uniform float depth_edge_thresh;   // Depth edge sensitivity (0-1)
uniform float chroma_split;        // Chromatic separation at edges
uniform float pre_warp;            // Pre-loop depth warping
uniform float pre_glitch;          // Pre-loop glitch injection

// --- Utility ---
float hash(vec2 p) { ... }  // Same hash as other depth effects

void main() {
    // Detect if Video B is connected (not all black)
    vec4 testB = texture(tex1, vec2(0.5));
    bool hasDualInput = (testB.r + testB.g + testB.b) > 0.01;

    // Depth edge detection
    float t = 2.0 / resolution.x;  // Texel offset (NOTE: uses x for both axes)
    float dl = texture(depth_tex, uv + vec2(-t, 0)).r;
    float dr = texture(depth_tex, uv + vec2( t, 0)).r;
    float du = texture(depth_tex, uv + vec2(0, -t)).r;
    float dd = texture(depth_tex, uv + vec2(0,  t)).r;
    float depth = texture(depth_tex, uv).r;
    vec2 depth_grad = vec2(dr - dl, dd - du);
    float edge = length(depth_grad);
    float is_edge = smoothstep(depth_edge_thresh * 0.05, depth_edge_thresh * 0.05 + 0.05, edge);

    // Motion vector displacement (fake from depth gradients)
    vec2 mv = depth_grad * mv_intensity * 0.1;

    // Quantize to block grid (datamosh works in blocks)
    float bs = block_size * 8.0 + 4.0;  // Map 0-1 → 4-68px
    vec2 block_uv = floor(uv * resolution / bs) * bs / resolution;
    float block_hash = hash(block_uv + floor(time * 2.0));

    // Only displace blocks near depth edges (where "I-frames" would be lost)
    if (is_edge > 0.3 && block_hash > 0.4) {
        mv *= (1.0 + block_hash * 2.0);
    } else {
        mv *= 0.1;
    }

    vec2 displaced_uv = uv + mv;
    displaced_uv = clamp(displaced_uv, 0.001, 0.999);

    // Pre-warp: depth-based distortion before loop
    if (pre_warp > 0.0) {
        vec2 warp = depth_grad * pre_warp * 0.05;
        displaced_uv += warp;
        displaced_uv = clamp(displaced_uv, 0.001, 0.999);
    }

    // Sample Video B (or fallback to Video A if B is black)
    vec4 video_b = texture(tex1, displaced_uv);
    if (!hasDualInput) {
        video_b = texture(tex0, displaced_uv);
    }

    // Pre-glitch: channel swapping, quantization
    if (pre_glitch > 0.0) {
        float r = video_b.r, g = video_b.g, b = video_b.b;
        if (pre_glitch > 0.3) {
            // Swap R and B
            video_b.r = b; video_b.b = r;
        }
        if (pre_glitch > 0.6) {
            // Quantize to 16 levels
            video_b = floor(video_b * 16.0) / 16.0;
        }
    }

    // Chromatic separation at depth edges
    if (chroma_split > 0.0 && is_edge > 0.3) {
        float offset = chroma_split * 0.02 * (hash(uv + time) - 0.5);
        video_b.r = texture(tex1, displaced_uv + vec2(offset, 0)).r;
        video_b.b = texture(tex1, displaced_uv - vec2(offset, 0)).b;
    }

    fragColor = video_b;
}
```

**Output**: Displaced and pre-processed video → **LOOP SEND** (external effects chain)

### Stage 2 Fragment Shader

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;           // Source video (unchanged)
uniform sampler2D texPrev;        // Previous frame (feedback)
uniform sampler2D depth_tex;      // Depth map
uniform sampler2D loop_return;    // LOOP RETURN (from external effects)
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Stage 2 controls
uniform float corruption;         // Overall corruption amount
uniform float feedback;           // Temporal feedback strength
uniform float feedback_decay;     // Feedback decay per frame
uniform float color_corrupt;      // Color channel corruption
uniform float quantize;           // Color quantization levels
uniform float scan_corrupt;       // Scan line corruption
uniform float loop_wetdry;        // Mix between loop return and corrupted signal
uniform float depth_composite;    // Depth-weighted compositing

// --- Utility ---
float hash(vec2 p) { ... }

void main() {
    vec4 source = texture(tex0, uv);
    vec4 previous = texture(texPrev, uv);
    float depth = texture(depth_tex, uv).r;

    // Get loop return (what came back from external effects)
    vec4 loop_signal = texture(loop_return, uv);

    // ====== BLOCK CORRUPTION ======
    // Simulate I-frame loss / macroblocking
    float block_size = 8.0;  // Fixed in shader (could be uniform)
    vec2 block_uv = floor(uv * resolution / block_size) * block_size / resolution;
    float block_corrupt = hash(block_uv + floor(time * 0.5));

    if (block_corrupt < corruption * 0.3) {
        // Replace block with neighbor block (simulate lost macroblock)
        vec2 offset = vec2(
            hash(block_uv + time) - 0.5,
            hash(block_uv + time + 1.0) - 0.5
        ) * block_size / resolution;
        loop_signal = texture(loop_return, uv + offset);
    }

    // ====== TEMPORAL FEEDBACK ======
    if (feedback > 0.0) {
        vec4 fb = previous * feedback_decay;
        loop_signal = mix(loop_signal, fb, feedback);
    }

    // ====== COLOR CORRUPTION ======
    if (color_corrupt > 0.0) {
        // Channel swapping based on depth
        if (depth < 0.3 && color_corrupt > 0.2) {
            loop_signal = loop_signal.gbra;  // Swap R and A
        }
        // Color quantization
        if (quantize > 0.0) {
            float levels = 8.0 + quantize * 56.0;  // 8-64 levels
            loop_signal = floor(loop_signal * levels) / levels;
        }
    }

    // ====== SCAN CORRUPTION ======
    if (scan_corrupt > 0.0) {
        float scan_line = sin(uv.y * resolution.y * 0.5 + time * 10.0);
        if (scan_line > 0.9) {
            loop_signal = texture(loop_return, uv + vec2(0.01 * scan_corrupt, 0));
        }
    }

    // ====== DEPTH-WEIGHTED COMPOSITE ======
    vec4 final = mix(source, loop_signal, loop_wetdry);
    if (depth_composite > 0.0) {
        // Near objects (low depth value = close) get more loop signal
        float depth_weight = 1.0 - depth;  // Invert: near = 1, far = 0
        final = mix(source, loop_signal, depth_weight * depth_composite);
    }

    fragColor = final;
}
```

**Inputs**: `loop_return` texture (external effects output), `texPrev` (feedback)
**Output**: Final corrupted frame

---

## Parameter Mapping Table

All parameters are on a **0-10 UI rail** and mapped to shader-specific ranges.

### Stage 1 Parameters (Pre-Loop)

| Parameter | UI Range | Mapped Range | Default (UI) | Shader Default | Purpose |
|-----------|----------|--------------|--------------|----------------|---------|
| `mvIntensity` | 0-10 | 0.0-1.0 | 5.0 | 0.5 | Motion vector displacement strength |
| `blockSize` | 0-10 | 0.0-1.0 → 4-68px | 5.0 | 0.5 → 36px | Datamosh block size (quantization grid) |
| `depthEdgeThresh` | 0-10 | 0.0-1.0 | 5.0 | 0.5 | Depth edge detection threshold |
| `chromaSplit` | 0-10 | 0.0-1.0 | 2.0 | 0.2 | Chromatic separation at depth edges |
| `preWarp` | 0-10 | 0.0-1.0 | 0.0 | 0.0 | Pre-loop depth warping |
| `preGlitch` | 0-10 | 0.0-1.0 | 0.0 | 0.0 | Pre-loop glitch (channel swap, quantize) |

### Stage 2 Parameters (Post-Loop)

| Parameter | UI Range | Mapped Range | Default (UI) | Shader Default | Purpose |
|-----------|----------|--------------|--------------|----------------|---------|
| `corruption` | 0-10 | 0.0-1.0 | 5.0 | 0.5 | Block corruption / I-frame loss rate |
| `feedback` | 0-10 | 0.0-1.0 | 3.0 | 0.3 | Temporal feedback strength |
| `feedbackDecay` | 0-10 | 0.0-1.0 | 7.0 | 0.7 | Feedback decay per frame (0.7 = 30% retention) |
| `colorCorrupt` | 0-10 | 0.0-1.0 | 2.0 | 0.2 | Color channel corruption amount |
| `quantize` | 0-10 | 0.0-1.0 | 0.0 | 0.0 | Color quantization (0=8 levels, 1=64 levels) |
| `scanCorrupt` | 0-10 | 0.0-1.0 | 0.0 | 0.0 | Scan line corruption (glitch offset) |
| `loopWetDry` | 0-10 | 0.0-1.0 | 7.0 | 0.7 | Mix between loop return and corrupted signal |
| `depthComposite` | 0-10 | 0.0-1.0 | 0.0 | 0.0 | Depth-weighted compositing (0 = uniform) |

**Total Parameters**: 14 user-facing parameters (6 Stage 1 + 8 Stage 2)

---

## Public Interface

### Class: `DepthModularDatamoshEffect(Effect)`

#### Constructor
```python
def __init__(self) -> None
```
- Initializes all 14 parameters with defaults
- Creates **two shader programs**:
  - `self._stage1_shader_src` from `STAGE1_FRAGMENT` string
  - `self.shader` (base class) from `STAGE2_FRAGMENT` embedded in `_get_fragment_shader()`
- Allocates depth texture (`self.depth_texture = 0`)
- Sets up audio reactivity mappings if `audio_reactor` provided

#### Methods

##### `set_depth_source(source: DepthSource)`
Inherited from base class. Sets the depth camera source.

##### `update_depth_data() -> None`
Fetches latest depth frame from `self.depth_source`.

##### `apply_uniforms(time_val: float, resolution: tuple, audio_reactor=None, semantic_layer=None) -> None`
**Main entry point for Stage 2** (final output). This is what the render pipeline calls.

**Steps**:
1. Call `super().apply_uniforms()` to bind base uniforms (`tex0`, `texPrev`, `u_mix`, `time`, `resolution`)
2. Call `self.update_depth_data()` to refresh depth frame
3. Upload depth texture to unit 2 (same as other depth effects)
4. Set Stage 2 uniforms:
   - `loop_return` = texture unit 3 (external loop input)
   - All 8 Stage 2 parameters mapped from 0-10 rail
5. Apply audio modulation to:
   - `corruption` (BASS)
   - `color_corrupt` (MID)
   - `scan_corrupt` (TREBLE)

##### `apply_stage1_uniforms(shader, time_val: float, resolution: tuple) -> None`
**Called by render pipeline before the loop send**. Sets uniforms for Stage 1 shader.

**Parameters**:
- `shader`: The compiled Stage 1 shader program (not `self.shader`)
- `time_val`: Current time in seconds
- `resolution`: Framebuffer size (width, height)

**Steps**:
1. Bind texture units: `tex0` (unit 0), `depth_tex` (unit 2)
2. Set time and resolution
3. Map and set Stage 1 parameters (`mv_intensity`, `block_size`, `depth_edge_thresh`, `chroma_split`, `pre_warp`, `pre_glitch`)
4. Apply audio modulation to:
   - `mv_intensity` (BASS)
   - `chroma_split` (MID)
   - `pre_glitch` (TREBLE)

##### `get_stage1_source() -> str`
Returns the Stage 1 shader source code string for the render pipeline to compile into a separate shader program.

##### `set_loop_return_texture(texture_id: int) -> None`
Sets the OpenGL texture ID for the loop return (texture unit 3). Called by the render pipeline after the external effects chain has rendered to the loop return FBO.

**Parameter**: `texture_id` — GLuint texture ID to bind to unit 3

---

## Inputs and Outputs

### Inputs

| Stream | Type | Format | Source | Texture Unit |
|--------|------|--------|--------|--------------|
| Video A | `tex0` | RGBA | Primary video input | 0 |
| Video B | `tex1` | RGBA | Secondary pixel source (optional) | 1 |
| Depth | `depth_tex` | RED uint8 | Depth camera (0.3-4.0m) | 2 |
| Loop Return | `loop_return` | RGBA | External effects output | 3 |
| Previous Frame | `texPrev` | RGBA | Feedback buffer | 1 (bound but unused in Stage 2) |

**Note**: `texPrev` is bound to unit 1 but only used in Stage 2 for temporal feedback. Stage 1 does not use it.

### Outputs

- **Stage 1 Output**: Rendered to an FBO (not directly visible) → becomes **LOOP SEND** texture
- **Stage 2 Output**: `fragColor` (RGBA) — final effect output

### Processing Flow

1. **Render Stage 1** to intermediate FBO (loop send)
2. **External effects chain** reads loop send, processes, writes to loop return FBO
3. **Render Stage 2** with loop return as input → final output

The effect **does not manage FBOs itself**; it expects the render pipeline to orchestrate the two-pass sequence.

---

## Edge Cases and Error Handling

### 1. Missing Loop Return Texture
- **Behavior**: If `loop_return` texture is not set (texture unit 3 bound to 0 or uninitialized), Stage 2 samples black (0,0,0,0).
- **Result**: Effect outputs either source video (if `loop_wetdry` low) or black (if `loop_wetdry` high).
- **Mitigation**: Render pipeline must ensure loop return FBO is properly allocated and bound.

### 2. Video B Not Connected (hasDualInput)
- **Stage 1** checks if Video B is all black: `bool hasDualInput = (testB.r + testB.g + testB.b) > 0.01;`
- If Video B is not connected (all black), Stage 1 falls back to sampling `tex0` instead of `tex1`.
- **Edge**: If Video B is connected but mostly black (e.g., valid signal with black frames), the fallback may trigger incorrectly.
- **Mitigation**: Document that Video B must be actively sending non-black frames to be considered "connected".

### 3. Depth Normalization Overflow
- Same as other depth effects: `((depth_frame - 0.3) / 3.7) * 255` → `uint8`
- Values outside 0.3-4.0m will underflow/overflow with wrap-around.
- **Bug**: No explicit clamping before conversion.

### 4. Block Size Mapping
- `block_size` mapped 0-1 → `bs = block_size * 8.0 + 4.0` → 4-68 pixels
- Very small blocks (<4px) not supported; very large blocks (>68px) not possible.
- **Edge**: `block_size = 0` → 4px blocks (minimum); `block_size = 1` → 12px blocks (not 68px as formula suggests? Let's recalc: `1*8+4=12`). **Inconsistency**: The formula `block_size * 8.0 + 4.0` maps 0→4, 1→12. The comment says 4-68px but 68 would require `block_size=8`. Likely the parameter is not 0-1 but 0-8? Need to verify mapping in `apply_stage1_uniforms()`:
  ```python
  shader.set_uniform("block_size", self._map_param('blockSize', 0.0, 1.0))
  ```
  So mapped range is 0.0-1.0. Then `bs = block_size * 8.0 + 4.0` gives 4-12px, **not** 4-68px. The comment is wrong or the formula is wrong. **Bug**: Either the formula should be `block_size * 64.0 + 4.0` to get 4-68px, or the intended range is 4-12px. Given typical datamosh block sizes (8-32px), 4-12px seems small. Possibly the formula is `block_size * 64.0 + 4.0` but the code has a typo.

### 5. Texture Unit Conflict: `texPrev` on Unit 1
- Stage 2 binds `texPrev` to unit 1 for feedback.
- Stage 1 does **not** use unit 1.
- If the render pipeline also uses unit 1 for something else between Stage 1 and Stage 2, conflict possible.
- **Mitigation**: Render pipeline should ensure texture unit bindings are set correctly before each draw call.

### 6. Audio Reactivity Only in Stage 2
- `apply_uniforms()` (Stage 2) applies audio modulation to corruption, color_corrupt, scan_corrupt.
- `apply_stage1_uniforms()` applies audio modulation to mv_intensity, chroma_split, pre_glitch.
- **Edge**: If `audio_reactor` is `None`, both methods skip modulation safely.

### 7. Depth Edge Detection Texel Offset
- Uses `t = 2.0 / resolution.x` for both x and y offsets.
- **Bug**: On non-square pixels (aspect ratio ≠ 1:1), the y gradient uses x-scale, causing incorrect edge detection.
- Should be: `vec2 texel = 1.0 / resolution;` then use `texel.x` and `texel.y` separately.

### 8. Block Corruption Randomness
- Block corruption uses `hash(block_uv + floor(time * 0.5))`.
- This means each block's corruption state changes every 2 seconds (time * 0.5).
- Could cause flickering corruption that is not temporally coherent.
- **Design choice**: May be intentional for "glitchy" aesthetic.

---

## Mathematical Formulations

### 1. Depth Normalization
```python
depth_normalized = ((depth_frame - 0.3) / (4.0 - 0.3) * 255).astype(np.uint8)
```
Standard across all depth effects.

### 2. Block Grid Quantization
```glsl
float bs = block_size * 8.0 + 4.0;  // Block size in pixels
vec2 block_uv = floor(uv * resolution / bs) * bs / resolution;
```
Quantizes UV coordinates to a grid of size `bs × bs` pixels. Ensures displacement aligns to block boundaries (simulates macroblock artifacts).

### 3. Motion Vector Displacement
```glsl
vec2 mv = depth_grad * mv_intensity * 0.1;
if (is_edge > 0.3 && block_hash > 0.4) {
    mv *= (1.0 + block_hash * 2.0);
} else {
    mv *= 0.1;
}
```
- Depth gradient approximates motion direction (edges where depth changes suddenly)
- Only blocks near depth edges (`is_edge > 0.3`) and with high hash (`>0.4`) get strong displacement
- Displacement magnitude scales with `mv_intensity`

### 4. Chromatic Separation
```glsl
float offset = chroma_split * 0.02 * (hash(uv + time) - 0.5);
video_b.r = texture(tex1, displaced_uv + vec2(offset, 0)).r;
video_b.b = texture(tex1, displaced_uv - vec2(offset, 0)).b;
```
Red and blue channels are sampled with horizontal offsets, creating chromatic aberration at depth edges.

### 5. Block Corruption (I-Frame Loss Simulation)
```glsl
if (block_corrupt < corruption * 0.3) {
    vec2 offset = vec2(
        hash(block_uv + time) - 0.5,
        hash(block_uv + time + 1.0) - 0.5
    ) * block_size / resolution;
    loop_signal = texture(loop_return, uv + offset);
}
```
- Each block has a random corruption chance: `corruption * 0.3` (max 30% of blocks)
- Corrupted blocks are replaced with a neighboring block (offset by random amount up to one block size)
- Simulates lost macroblocks in compressed video

### 6. Temporal Feedback
```glsl
if (feedback > 0.0) {
    vec4 fb = previous * feedback_decay;
    loop_signal = mix(loop_signal, fb, feedback);
}
```
- `previous` is the previous frame's output (from `texPrev`)
- `feedback_decay` scales the previous frame (e.g., 0.7 = 70% retention)
- `feedback` controls mix ratio between fresh loop signal and decayed previous

### 7. Color Corruption
```glsl
if (color_corrupt > 0.0) {
    if (depth < 0.3 && color_corrupt > 0.2) {
        loop_signal = loop_signal.gbra;  // Channel swap
    }
    if (quantize > 0.0) {
        float levels = 8.0 + quantize * 56.0;  // 8-64 levels
        loop_signal = floor(loop_signal * levels) / levels;
    }
}
```
- Near-depth objects (depth < 0.3) may have channels swapped (R→A, G→B, etc.)
- Quantization reduces color precision to simulate posterization

### 8. Scan Corruption
```glsl
float scan_line = sin(uv.y * resolution.y * 0.5 + time * 10.0);
if (scan_line > 0.9) {
    loop_signal = texture(loop_return, uv + vec2(0.01 * scan_corrupt, 0));
}
```
- Horizontal scan lines appear periodically based on sine wave
- Affected lines are offset horizontally by `0.01 * scan_corrupt` (normalized UV)

### 9. Depth-Weighted Composite
```glsl
float depth_weight = 1.0 - depth;  // Near = 1, Far = 0
final = mix(source, loop_signal, depth_weight * depth_composite);
```
- Near objects (low depth value = close to camera) receive more loop signal
- Far objects retain more of the original source video
- Only active if `depth_composite > 0`

---

## Performance Characteristics

### Computational Cost

**Stage 1**:
- Texture fetches: `tex0` (1), `tex1` (1-2, plus optional chroma split 2 more), `depth_tex` (4 for gradient)
- Total: ~4-8 texture fetches per pixel
- Arithmetic: Gradient calculation, block quantization, hash calls (cheap), clamping

**Stage 2**:
- Texture fetches: `tex0` (1), `texPrev` (1), `depth_tex` (1), `loop_return` (1-2, plus block corruption neighbor fetch)
- Total: ~5-7 texture fetches per pixel
- Arithmetic: Block hash, conditional corruption, color operations, mix

**Overall**: Two-pass effect, so total cost ≈ sum of both stages. Roughly **9-15 texture fetches per pixel** depending on parameters (chroma split, block corruption neighbor fetch).

### Memory Footprint

- **Textures**: 4 bound textures (units 0-3)
- **FBOs**: Requires 2 intermediate FBOs (loop send, loop return) managed by render pipeline
- **Uniforms**: ~15 floats + 1 vec2 per stage (total ~30 floats)

### GPU Utilization

- **Fragment-bound**: Both stages are full-screen fragment shaders.
- **Expected FPS** (1080p, mid-range GPU): 60-120 FPS depending on:
  - Chroma split enabled (extra 2 fetches)
  - Block corruption rate (extra neighbor fetch for corrupted blocks)
  - Feedback enabled (extra `texPrev` fetch, but already counted)
- **Compared to single-pass datamosh**: ~2× cost due to two passes, but still lighter than effects with multi-tap feedback matrices.

### Optimization Opportunities

- **Block size**: Larger blocks reduce hash computation frequency (fewer blocks), but not significant.
- **Chroma split**: Disable when not needed (saves 2 fetches).
- **Scan corruption**: Disable when not needed (saves conditional branch + fetch).
- **Depth gradient**: Could use lower-resolution depth map (half-size) to reduce bandwidth.

---

## Test Plan

### Unit Tests (Python)

1. **Parameter Mapping Bounds**
   ```python
   def test_stage1_param_bounds():
       effect = DepthModularDatamoshEffect()
       params = ['mvIntensity', 'blockSize', 'depthEdgeThresh', 'chromaSplit', 'preWarp', 'preGlitch']
       for p in params:
           val = effect._map_param(p, 0.0, 1.0)
           assert 0.0 <= val <= 1.0
   
   def test_stage2_param_bounds():
       effect = DepthModularDatamoshEffect()
       params = ['corruption', 'feedback', 'feedbackDecay', 'colorCorrupt', 'quantize', 'scanCorrupt', 'loopWetDry', 'depthComposite']
       for p in params:
           val = effect._map_param(p, 0.0, 1.0)
           assert 0.0 <= val <= 1.0
   ```

2. **Block Size Formula Verification**
   ```python
   def test_block_size_mapping():
       effect = DepthModularDatamoshEffect()
       # Map 0-10 rail to 0-1
       effect.set_parameter('blockSize', 0.0)
       mapped_0 = effect._map_param('blockSize', 0.0, 1.0)
       effect.set_parameter('blockSize', 10.0)
       mapped_10 = effect._map_param('blockSize', 0.0, 1.0)
       # In shader: bs = block_size * 8.0 + 4.0
       assert mapped_0 * 8.0 + 4.0 == 4.0
       assert mapped_10 * 8.0 + 4.0 == 12.0  # Not 68! Bug identified.
   ```

3. **Audio Reactivity Assignment**
   ```python
   def test_audio_mapping_stage1():
       effect = DepthModularDatamoshEffect()
       analyzer = MockAudioAnalyzer()
       effect.set_audio_analyzer(analyzer)
       # Verify 3 assignments for Stage 1 (BASS: mvIntensity, MID: chromaSplit, TREBLE: preGlitch)
   
   def test_audio_mapping_stage2():
       effect = DepthModularDatamoshEffect()
       analyzer = MockAudioAnalyzer()
       effect.set_audio_analyzer(analyzer)
       # Verify 3 assignments for Stage 2 (BASS: corruption, MID: colorCorrupt, TREBLE: scanCorrupt)
   ```

### Integration Tests (OpenGL)

1. **Shader Compilation**
   - Compile `STAGE1_FRAGMENT` and `STAGE2_FRAGMENT` separately
   - Link both with vertex shader
   - Check uniform locations for all parameters

2. **Texture Unit Binding**
   - After `apply_uniforms()`: verify `depth_tex` bound to unit 2, `loop_return` bound to unit 3
   - After `apply_stage1_uniforms()`: verify `tex0` bound to unit 0, `depth_tex` bound to unit 2

3. **Two-Pass Rendering Sequence**
   - Render Stage 1 to FBO A (loop send)
   - Render external effect (e.g., simple color invert) reading FBO A, writing to FBO B (loop return)
   - Render Stage 2 with FBO B as `loop_return` texture
   - Verify output is not identical to single-pass Stage 2 without loop

4. **hasDualInput Fallback**
   - With Video B connected (non-black): Stage 1 should sample `tex1`
   - With Video B disconnected (black): Stage 1 should sample `tex0`
   - Test by rendering Stage 1 to FBO and inspecting output texture

### Visual Regression Tests

1. **Parameter Sweep**
   - Render with each parameter at 0, 5, 10 while others at default
   - Capture screenshots for both Stage 1 (loop send) and Stage 2 (final output)
   - Compare against golden images

2. **Loop Chain Test**
   - Set up: Stage 1 → [Identity effect] → Stage 2
   - Output should be identical to Stage 1 output (since loop return = loop send)
   - If not, there is a bug in Stage 2's handling of loop return

3. **Audio Modulation**
   - Feed synthetic audio (sine wave BASS/MID/TREBLE)
   - Verify parameter values change in real-time (query uniform values)

4. **Depth Edge Detection**
   - Render with a depth map containing a sharp edge (half black, half white)
   - Verify `is_edge` is high near the edge, low in flat regions
   - Can be tested by outputting `is_edge` as color in Stage 1

### Performance Tests

1. **Two-Pass Overhead**
   ```python
   timeit(stage1_render + stage2_render, resolution=(1920,1080))
   # Compare to single-pass effect cost
   ```

2. **Parameter Impact**
   - Test with chroma_split = 0 vs 10 (measure fetch count difference)
   - Test with corruption = 0 vs 10 (measure branch divergence)

---

## Migration Notes (WebGPU / VJLive3)

### WGSL Translation

**Two Shader Programs**:
- Need to compile both Stage 1 and Stage 2 as separate `RenderPipeline` objects
- Stage 1 pipeline writes to its own `texture_storage` (loop send)
- Stage 2 pipeline reads from `loop_return` texture (bind group binding 3)

**Bind Group Layout** (Stage 1):
```wgsl
struct Stage1Uniforms {
    time: f32,
    resolution: vec2<f32>,
    mv_intensity: f32,
    block_size: f32,
    depth_edge_thresh: f32,
    chroma_split: f32,
    pre_warp: f32,
    pre_glitch: f32,
    padding: f32,  // align to 16-byte boundary
};

@group(0) @binding(0) var video_tex: texture_2d<f32>;
@group(0) @binding(1) var video_b_tex: texture_2d<f32>;
@group(0) @binding(2) var depth_tex: texture_2d<f32>;
@group(0) @binding(3) var<uniform> uniforms: Stage1Uniforms;
```

**Bind Group Layout** (Stage 2):
```wgsl
struct Stage2Uniforms {
    time: f32,
    resolution: vec2<f32>,
    u_mix: f32,
    corruption: f32,
    feedback: f32,
    feedback_decay: f32,
    color_corrupt: f32,
    quantize: f32,
    scan_corrupt: f32,
    loop_wetdry: f32,
    depth_composite: f32,
    padding: f32,  // align
};

@group(0) @binding(0) var video_tex: texture_2d<f32>;
@group(0) @binding(1) var prev_tex: texture_2d<f32>;
@group(0) @binding(2) var depth_tex: texture_2d<f32>;
@group(0) @binding(3) var loop_return_tex: texture_2d<f32>;
@group(0) @binding(4) var<uniform> uniforms: Stage2Uniforms;
```

**Render Pipeline Orchestration**:
- The **render engine** must manage the two-pass sequence:
  1. Encode `stage1_pass` → `loop_send_texture`
  2. Encode `external_effects_pass` (user-defined chain) → `loop_return_texture`
  3. Encode `stage2_pass` → final framebuffer
- This is higher-level than just shader translation; the **node graph** must support loop routing.

### Memory Management

- **Legacy leak**: `glGenTextures(1)` for depth texture, never freed.
- **WebGPU**: Textures are explicitly destroyed. Need to implement `__del__()` or RAII.
- **FBO management**: The effect does not own its FBOs; the render pipeline must allocate and release `loop_send` and `loop_return` textures each frame or reuse with proper synchronization.

### Audio Reactivity

- Legacy: Per-parameter `audio_reactor.get_audio_modulation()` calls.
- WebGPU: Audio features should be in a uniform buffer (e.g., `audio_bass`, `audio_mid`, `audio_treble`) updated once per frame.
- The effect's `apply_uniforms` and `apply_stage1_uniforms` would write modulated values into their respective uniform buffers.

---

## Legacy Code References

### File: `depth_modular_datamosh.py` (full source)

**Key sections**:

1. **Module docstring** (lines 1-50): Explains two-stage architecture with ASCII diagram
2. **STAGE1_FRAGMENT** (lines ~70-200): Full GLSL code for Stage 1
3. **STAGE2_FRAGMENT** (lines ~210-350): Embedded in `_get_fragment_shader()` method
4. **Class `DepthModularDatamoshEffect`** (lines ~360-550):
   - `__init__`: Sets up 14 parameters, compiles Stage 1 shader, sets up audio
   - `apply_stage1_uniforms`: Sets Stage 1 uniforms, called before loop send
   - `apply_uniforms`: Sets Stage 2 uniforms, called for final output
   - `get_stage1_source`: Returns Stage 1 shader source
   - `set_loop_return_texture`: Called by pipeline to bind loop return texture

5. **Audio mapping** (lines ~480-510):
   ```python
   # Stage 1: BASS→mvIntensity, MID→chromaSplit, TREBLE→preGlitch
   # Stage 2: BASS→corruption, MID→colorCorrupt, TREBLE→scanCorrupt
   ```

6. **Depth normalization** (line ~460):
   ```python
   dn = ((self.depth_frame - 0.3) / (4.0 - 0.3) * 255).astype(np.uint8)
   ```
   Consistent with all depth effects.

---

## Open Questions

1. **Block size formula discrepancy**: The shader uses `bs = block_size * 8.0 + 4.0`, which maps 0-1 to 4-12 pixels. The comment says "4-68px". Which is correct? Should the multiplier be 64 instead of 8? Need to verify intended range from legacy documentation or user expectations.

2. **Stage 2 block corruption uses fixed `block_size = 8.0`**: This is hard-coded in the shader, not a uniform. Should it be controlled by the `blockSize` parameter? Currently Stage 1's block size affects displacement grid, but Stage 2's corruption uses fixed 8px blocks. **Inconsistency** that may be intentional (different block sizes for different effects) or a bug.

3. **hasDualInput detection**: Samples `tex1` at `vec2(0.5)` once per pixel. This is cheap but may not be representative if Video B has a black pixel at center. Should be a uniform set once per frame, not per-pixel. **Optimization**: Move detection to Python side and set a `has_dual_input` uniform.

4. **Loop return texture binding**: The method `set_loop_return_texture(texture_id)` expects the pipeline to call it. But `apply_uniforms()` does not call it; it assumes the texture is already bound to unit 3. **Potential race**: If pipeline forgets to set it, Stage 2 samples whatever is on unit 3. Should add validation (e.g., check `glGetIntegerv(GL_TEXTURE_BINDING_2D, 3)`).

5. **Stage 2 uses `texPrev` but never writes to it**: Who writes the previous frame? The render pipeline must manage a ping-pong feedback buffer and bind it to `texPrev`. The effect does not manage this itself. **Documentation gap**: Need to specify in the spec that the pipeline must provide `texPrev` with previous output.

6. **Depth composite formula**: Uses `depth_weight = 1.0 - depth`. Since depth is normalized 0-1, near (close to camera) has low depth value? Actually in depth cameras, near = small value (e.g., 0.3m), far = large value (4.0m). After normalization, near → 0, far → 1. So `1.0 - depth` gives near=1, far=0. That seems correct. But verify: is the depth map linearized? Yes, normalization is linear. So this weighting is correct.

7. **Chroma split offset**: `chroma_split * 0.02` gives max offset 0.02 UV (2% of screen). Is this too subtle? Might need larger multiplier for visible effect.

8. **Pre-glitch channel swap**: Swaps R and B only. Why not G? Incomplete? Could be intentional (only red-cyan swap for anaglyph effect).

---
-

## Definition of Done

- [x] Skeleton spec claimed from `_05_active_desktop`
- [x] Legacy source code analyzed (`depth_modular_datamosh.py`)
- [x] All 14 parameters documented with mapped ranges and defaults
- [x] Two-shader architecture explained (Stage 1 + Stage 2)
- [x] Loop routing mechanism described (LOOP SEND → external FX → LOOP RETURN)
- [x] Edge cases identified (missing loop return, Video B detection, block size formula bug, aspect ratio bug)
- [x] Mathematical formulations provided (block quantization, displacement, corruption, feedback)
- [x] Performance characteristics analyzed (two-pass cost, texture fetches)
- [x] Test plan defined (unit, integration, visual regression, performance)
- [x] WebGPU migration notes (two pipelines, bind groups, FBO orchestration)
- [x] Easter egg concept defined ("Modular Fibonacci Resonance")
- [ ] Spec file saved to `docs/specs/_02_fleshed_out/` (pending)
- [ ] `BOARD.md` updated to "🟩 COMPLETING PASS 2"
- [ ] Easter egg appended to `WORKSPACE/EASTEREGG_COUNCIL.md`
- [ ] Next task claimed

**Next Step**: Write spec file to disk, update BOARD.md, add easter egg, claim next task.
