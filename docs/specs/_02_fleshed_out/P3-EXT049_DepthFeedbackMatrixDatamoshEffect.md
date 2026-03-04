# P3-EXT049 — DepthFeedbackMatrixDatamoshEffect

**Status:** Pass 2 Fleshed Out  
**Agent:** desktop-roo  
**Date:** 2025-03-03  
**Legacy Origin:** VJLive (Original) + VJLive-2  
**Module ID:** `depth_feedback_matrix_datamosh`  
**Class:** `DepthFeedbackMatrixDatamoshEffect`  
**GPU Tier:** MEDIUM

---

## Executive Summary

The DepthFeedbackMatrixDatamoshEffect is a sophisticated multi-tap feedback routing system that creates complex, cascading feedback structures sculpted by depth. Unlike simple single-buffer feedback, this effect implements a **4-tap feedback matrix** where each tap:

- Has independent delay, depth gating, and feedback amount
- Can route through an external effects loop (insertion point)
- Cross-feeds into subsequent taps with configurable mixing
- Supports depth-dependent routing (only certain depth ranges participate)

This is essentially a **modular feedback processor** — think of it as a 4-channel delay matrix with depth-controlled routing and datamosh integration. It enables VJs to build intricate, evolving feedback sculptures that respond to depth topology.

**Key Innovation:** The combination of multi-tap feedback, cross-feed matrix, and external loop insertion points allows for arbitrarily complex feedback topologies, from simple dual-tap echoes to infinite recirculation grids.

---

## What This Module Does

The effect processes video through a **4-stage feedback pipeline**:

1. **Base Datamosh:** Applies motion-based displacement using the previous frame buffer
2. **Tap 1 (Near-field):** Short delay, typically for foreground feedback
3. **Tap 2 (Mid-field):** Medium delay, receives cross-feed from Tap 1
4. **Tap 3 (Far-field):** Long delay, receives cross-feed from Tap 2
5. **Tap 4 (Recirculation):** Can feed back into Tap 1, creating loops

Each tap:
- Samples from its **return texture** (connected via external routing)
- Applies **depth gating** (only processes pixels within a depth range)
- Applies **time-based displacement** (delay simulated via UV offset)
- Mixes with current signal based on **feedback amount**
- Can optionally **cross-feed** into the next tap

**External Loop Insertion:** Each tap has an `enable_loop` flag. When enabled, the tap's output can be routed out to external effects, processed, and fed back via the corresponding `tapX_return` texture. This allows inserting reverb, distortion, color grading, or any other effect between taps.

**Graph Topology:**
```
Input Video ──┬─> [Datamosh] ──┬─> Tap1 ──┬─> Tap2 ──┬─> Tap3 ──┬─> Tap4 ──> Output
               │                │          │          │          │
               │                ↓          ↓          ↓          ↓
               │              [Ext1]     [Ext2]     [Ext3]     [Ext4]
               │                │          │          │          │
               └────────────────┴──────────┴──────────┴──────────┘
                                ↓          ↓          ↓          ↓
                              tap1_ret   tap2_ret   tap3_ret   tap4_ret
```

---

## What This Module Does NOT Do

- **Does NOT** allocate or manage the tap return textures — they must be provided externally via `set_tap_return_texture()`
- **Does NOT** implement the external effects themselves — only the routing infrastructure
- **Does NOT** provide a user interface for routing — graph connections are manual
- **Does NOT** automatically prevent infinite feedback loops — user must configure feedback amounts and enable flags carefully
- **Does NOT** support more than 4 taps (fixed architecture)
- **Does NOT** perform depth estimation — requires external depth map input

---

## Detailed Behavior and Parameter Interactions

### 2.1 Shader Architecture

The fragment shader (`DEPTH_FEEDBACK_MATRIX_FRAGMENT`) implements the full pipeline in a single pass. It uses multiple texture units:

**Texture Bindings:**
- `tex0` (unit 0): Current input frame
- `tex1` (unit 1): Video B (used for dual-input detection, not otherwise used)
- `texPrev` (unit 2): Previous frame (feedback buffer)
- `depth_tex` (unit 3): Depth map
- `tap1_return` (unit 4): Tap 1 external return
- `tap2_return` (unit 5): Tap 2 external return
- `tap3_return` (unit 6): Tap 3 external return
- `tap4_return` (unit 7): Tap 4 external return

**Note:** The shader expects 8 texture units total. The texture unit assignments in `apply_uniforms()` match this (units 3-6 for taps, unit 2 for depth). However, the code sets `depth_tex` to unit 2 but also uses `texPrev` on unit 2 — **CONFLICT!** This is a bug: both `texPrev` and `depth_tex` are set to unit 2 (lines 367 and 363 in the Python code). The shader expects `depth_tex` on unit 3? Let's check:

In `apply_uniforms()`:
- Line 367: `self.shader.set_uniform("depth_tex", 2)` — sets depth to unit 2
- Line 368: `self.shader.set_uniform("tap1_return", 3)` — tap1 to unit 3
- Line 369: `self.shader.set_uniform("tap2_return", 4)` — tap2 to unit 4
- Line 370: `self.shader.set_uniform("tap3_return", 5)` — tap3 to unit 5
- Line 371: `self.shader.set_uniform("tap4_return", 6)` — tap4 to unit 6

But the shader declares:
- `uniform sampler2D texPrev;` — no explicit unit set in code, but likely unit 1 (since tex0=0, tex1=1)
- `uniform sampler2D depth_tex;` — no explicit unit, but code sets to 2
- `uniform sampler2D tap1_return;` — code sets to 3
- etc.

So the conflict is: `texPrev` is never explicitly set, so it defaults to whatever the base class sets. The base `Effect` class likely sets `tex0` to 0 and `texPrev` to 1. Then `depth_tex` is set to 2, which is fine. But wait — the shader code shows `texPrev` is used, but we don't see where it's set. Let's check the base class pattern. In the legacy code, the base `Effect` class probably handles `tex0` and `texPrev` in its `apply_uniforms()`. The `super().apply_uniforms()` call at line 342 would set those. So likely:
- `tex0` = unit 0 (set by base)
- `texPrev` = unit 1 (set by base)
- `depth_tex` = unit 2 (set by this class)
- `tap1_return` = unit 3
- `tap2_return` = unit 4
- `tap3_return` = unit 5
- `tap4_return` = unit 6

That's 7 units total, which is fine. No conflict. My earlier confusion was mistaken — `texPrev` is set by base, `depth_tex` is set to 2, so they're different. Good.

**Processing Flow:**

1. **Dual Input Detection** (lines 124-126):
   ```glsl
   vec4 testB = texture(tex1, vec2(0.5));
   bool hasDualInput = (testB.r + testB.g + testB.b) > 0.01;
   ```
   Checks if Video B is connected (non-black). This flag is currently **unused** in the rest of the shader — likely a leftover from development. Should be removed or used.

2. **Depth Normalization** (line 131):
   ```glsl
   depth = clamp((depth - 0.3) / 3.7, 0.0, 1.0);
   ```
   Same hard-coded meter-to-normalized conversion as in DepthFXLoopEffect. Assumes depth in meters with near=0.3m, far=4.0m (0.3+3.7=4.0). This is a **legacy assumption**.

3. **Base Datamosh** (lines 133-146):
   - Computes block-based motion using `block_size` parameter
   - Block UV: `floor(uv * resolution / block) * block / resolution`
   - Motion = `length(current.rgb - block_prev.rgb)`
   - Displacement = `block_diff.rg * mosh_intensity * 0.03`
   - Samples `texPrev` at displaced UV to get datamoshed result
   - Blends with current based on motion threshold: `smoothstep(0.05, 0.15, motion) * mosh_intensity`
   - This creates a **motion-based smear** effect, where moving areas smear previous frames

4. **Tap Processing** (lines 148-193):
   Each tap calls `apply_tap()` with its configuration. The function:

   ```glsl
   vec4 apply_tap(vec4 current, sampler2D tap_return, float depth,
                  float depth_min, float depth_max, float feedback,
                  int enable_loop, float delay) {
       float depth_gate = smoothstep(depth_min, depth_min + 0.1, depth) *
                         (1.0 - smoothstep(depth_max - 0.1, depth_max, depth));
       if (depth_gate < 0.01) return current;
       
       vec2 delay_offset = vec2(
           sin(time * 0.3 + depth * 10.0) * delay * 0.01,
           cos(time * 0.4 + depth * 10.0) * delay * 0.01
       );
       vec2 tap_uv = uv + delay_offset;
       tap_uv = clamp(tap_uv, 0.001, 0.999);
       
       vec4 tap_signal = texture(tap_return, tap_uv);
       
       float mix_amount = feedback * depth_gate;
       return mix(current, tap_signal, mix_amount);
   }
   ```

   - **Depth gate:** Soft window with 0.1 transition width (hard-coded)
   - **Delay displacement:** Time-varying UV offset using `sin`/`cos` with depth modulation. The `delay` parameter scales the offset (max ~0.01 pixels? Actually `delay * 0.01` means delay=1 → 0.01, delay=10 → 0.1 pixels — very small).
   - **Feedback mix:** `mix(current, tap_signal, feedback * depth_gate)`

   The taps are applied sequentially, with cross-feed:

   - **Tap 1:** Directly applies to `result`
   - **Tap 2:** `cross_feed = mix(result, tap1_output, tap1_to_tap2 * 0.5)` then applies tap2 to `cross_feed`, result becomes `cross_feed`
   - **Tap 3:** `cross_feed = mix(result, tap2_output, tap2_to_tap3 * 0.5)` then tap3
   - **Tap 4:** `cross_feed = mix(result, tap3_output, tap3_to_tap4 * 0.5)` then tap4, plus recirculation: `result = mix(result, cross_feed, tap4_to_tap1 * 0.3)`

   The cross-feed factors are multiplied by 0.5 (or 0.3 for tap4 recirc) — these are **hard-coded scalars** not exposed as parameters.

5. **Final Mix** (line 195):
   ```glsl
   fragColor = mix(current, result, u_mix);
   ```
   Blends original input with fully processed result.

### 2.2 Parameter Mapping

All UI parameters are 0-10 normalized floats. Mapping function:

```python
def _map_param(self, name, out_min, out_max):
    val = self.parameters.get(name, 5.0)
    return out_min + (val / 10.0) * (out_max - out_min)
```

**Parameter Dictionary** (lines 274-312):

| Parameter | Default | Shader Target | Mapped Range | Purpose |
|-----------|---------|---------------|--------------|---------|
| **Tap 1 (Near-field)** |
| `tap1Delay` | 0.0 | `tap1_delay` | 0.0 - 1.0 | Delay amount (UV offset scale) |
| `tap1DepthMin` | 0.0 | `tap1_depth_min` | 0.0 - 1.0 | Lower depth bound |
| `tap1DepthMax` | 5.0 | `tap1_depth_max` | 0.0 - 1.0 | Upper depth bound |
| `tap1Feedback` | 3.0 | `tap1_feedback` | 0.0 - 1.0 | Mix amount from tap1 return |
| `tap1EnableLoop` | 0.0 | `tap1_enable_loop` | N/A (bool) | Enable external loop (threshold >5.0) |
| **Tap 2 (Mid-field)** |
| `tap2Delay` | 2.0 | `tap2_delay` | 0.0 - 1.0 | Delay amount |
| `tap2DepthMin` | 3.0 | `tap2_depth_min` | 0.0 - 1.0 | Depth min |
| `tap2DepthMax` | 7.0 | `tap2_depth_max` | 0.0 - 1.0 | Depth max |
| `tap2Feedback` | 3.0 | `tap2_feedback` | 0.0 - 1.0 | Mix amount |
| `tap2EnableLoop` | 0.0 | `tap2_enable_loop` | N/A (bool) | Enable external loop |
| **Tap 3 (Far-field)** |
| `tap3Delay` | 5.0 | `tap3_delay` | 0.0 - 1.0 | Delay amount |
| `tap3DepthMin` | 6.0 | `tap3_depth_min` | 0.0 - 1.0 | Depth min |
| `tap3DepthMax` | 10.0 | `tap3_depth_max` | 0.0 - 1.0 | Depth max |
| `tap3Feedback` | 3.0 | `tap3_feedback` | 0.0 - 1.0 | Mix amount |
| `tap3EnableLoop` | 0.0 | `tap3_enable_loop` | N/A (bool) | Enable external loop |
| **Tap 4 (Recirculation)** |
| `tap4Delay` | 7.0 | `tap4_delay` | 0.0 - 1.0 | Delay amount |
| `tap4DepthMin` | 0.0 | `tap4_depth_min` | 0.0 - 1.0 | Depth min |
| `tap4DepthMax` | 10.0 | `tap4_depth_max` | 0.0 - 1.0 | Depth max |
| `tap4Feedback` | 2.0 | `tap4_feedback` | 0.0 - 1.0 | Mix amount |
| `tap4EnableLoop` | 0.0 | `tap4_enable_loop` | N/A (bool) | Enable external loop |
| **Cross-feed Matrix** |
| `tap1ToTap2` | 2.0 | `tap1_to_tap2` | 0.0 - 1.0 | Tap1→Tap2 cross-feed (×0.5 in shader) |
| `tap2ToTap3` | 2.0 | `tap2_to_tap3` | 0.0 - 1.0 | Tap2→Tap3 cross-feed (×0.5) |
| `tap3ToTap4` | 2.0 | `tap3_to_tap4` | 0.0 - 1.0 | Tap3→Tap4 cross-feed (×0.5) |
| `tap4ToTap1` | 1.0 | `tap4_to_tap1` | 0.0 - 1.0 | Tap4→Tap1 recirc (×0.3 in shader) |
| **Datamosh** |
| `moshIntensity` | 5.0 | `mosh_intensity` | 0.0 - 1.0 | Motion-based smear strength |
| `blockSize` | 4.0 | `block_size` | 0.0 - 1.0 | Block size (scaled to 4-44px) |

**Presets** (lines 212-261):
- `simple_dual_tap`: Only taps 1 and 2 active, basic two-tap echo
- `cascading_depth_layers`: All taps active with depth-separated ranges, cross-feeds enabled
- `infinite_recirculation`: All taps full open with strong cross-feeds, creates dense feedback
- `full_matrix_chaos`: Maximum values everywhere — chaotic feedback grid

### 2.3 Depth Source Management

Same pattern as DepthFXLoopEffect:

- `set_depth_source(source)`: Attaches depth provider
- `update_depth_data()`: Calls `source.get_filtered_depth_frame()` each frame
- Depth texture uploaded with normalization: `((depth_frame - 0.3) / (4.0 - 0.3) * 255).astype(np.uint8)`
- Texture ID reused after first allocation (`glGenTextures(1)` once)

**Critical:** The normalization uses hard-coded 0.3-4.0 meter range. This is a **legacy constraint** that may not match all depth sources.

### 2.4 Tap Return Texture Management

**External Interface:**

```python
def set_tap_return_texture(self, tap_index: int, texture_id: int):
    if 0 <= tap_index < 4:
        self.tap_return_textures[tap_index] = texture_id
```

The node **does not create** these textures. They must be provided by the node graph or external effects chain. Each tap's return texture should contain the processed output from that tap's external loop.

**Texture Unit Assignment in Shader:**
- `tap1_return` → unit 3
- `tap2_return` → unit 4
- `tap3_return` → unit 5
- `tap4_return` → unit 6

The `apply_uniforms()` method sets these uniforms to the respective texture IDs (lines 368-371). However, it does **not** bind the textures — it only sets the sampler uniform to the texture unit. The actual texture binding (`glBindTexture`) must happen externally before rendering this shader, or the shader will sample from whatever texture is bound to those units.

**Important:** The code assumes the texture IDs are already bound to the correct units. This is a **contract** with the rendering system: before drawing this effect, the graph must bind each tap return texture to its assigned unit (3-6). Alternatively, the effect could bind them itself, but it doesn't.

### 2.5 Audio Reactivity

The class has `self.audio_reactor = None` (line 314) but **no `set_audio_analyzer()` method** and **no audio feature assignments** in `__init__`. Unlike DepthFXLoopEffect, this effect does **not** appear to have built-in audio reactivity. The base class may support audio uniforms, but this subclass doesn't use them.

---

## Public Interface

### 4.1 Constructor

```python
def __init__(self):
    super().__init__("depth_feedback_matrix_datamosh", DEPTH_FEEDBACK_MATRIX_FRAGMENT)
    # Sets up parameters, depth source, depth texture, tap return textures
```

Initializes all parameters to defaults (see table above). Creates empty depth texture handle (0) and tap return texture handles ([0,0,0,0]).

### 4.2 Core Methods

#### `set_depth_source(source: DepthSource)`
Attaches depth source. Identical to other depth effects.

#### `set_tap_return_texture(tap_index: int, texture_id: int)`
Sets the return texture for a specific tap. Must be called for each tap that is enabled, with a valid OpenGL texture ID.

#### `update_depth_data()`
Updates depth frame from source. Same as other depth effects.

#### `apply_uniforms(time_val, resolution, audio_reactor=None, semantic_layer=None)`
Per-frame setup:

1. `super().apply_uniforms()` — sets `tex0`, `texPrev`, `time`, `resolution`, `u_mix` (from base class)
2. `self.update_depth_data()` — fetches depth
3. If depth exists, uploads to `depth_texture` (unit 2)
4. Sets tap return sampler uniforms to units 3-6
5. Maps and sets all 20 parameters (5 per tap × 4 taps + 4 cross-feed + 2 datamosh)
6. Converts `tapXEnableLoop` to int (1 if >5.0 else 0)

**Note:** Does **not** bind tap return textures. Assumes they are already bound to units 3-6 by the renderer.

---

## Inputs and Outputs

### 5.1 Node Graph Ports

Based on `plugin.json` snippets:

**Inputs:**
- `signal_in` (video): Main video stream

**Outputs:**
- `signal_out` (video): Processed result

**Type:** EFFECT node

**Missing:** The plugin manifest does **not** define tap return inputs. The legacy system likely uses a different mechanism (maybe the node has 4 additional "tap_return" input ports that are not listed in the basic manifest, or the tap returns are set via method calls rather than graph connections). For VJLive3, we need to decide: either expose 4 additional input ports (`tap1_return`, `tap2_return`, `tap3_return`, `tap4_return`) or use a different mechanism (e.g., the node graph automatically routes feedback buffers). The spec should recommend exposing these as video inputs.

---

## Edge Cases and Error Handling

### 6.1 Missing Tap Return Textures

**Condition:** `set_tap_return_texture()` not called for an enabled tap, or texture_id=0.

**Behavior:**
- Shader samples from texture unit with ID 0 (default texture)
- Likely returns black or undefined data
- Result: Tap contributes nothing (or garbage)

**Expected Handling:** The node graph should ensure all enabled taps have valid return textures connected. Could add validation in `apply_uniforms()` to warn or disable taps with missing textures.

### 6.2 Depth Frame Size Mismatch

Same as other depth effects — misaligned depth causes incorrect gating.

### 6.3 Infinite Feedback Loops

**Condition:** All taps enabled with high feedback values and cross-feeds, especially `tap4_to_tap1` > 0.

**Behavior:**
- Each frame, signal recirculates through the matrix
- Without sufficient decay (feedback amounts < 1.0), values may grow
- The datamosh and cross-feed multipliers (0.5, 0.3) provide some damping
- But still possible to create stable or growing oscillations

**Expected Handling:** User must configure feedback amounts carefully. Could add a `max_feedback` safety clamp, but legacy doesn't have one.

### 6.4 Depth Gate Full Open

**Condition:** `depth_min = 0`, `depth_max = 1.0` (after mapping).

**Behavior:** `smoothstep(0, 0.1, depth) * (1 - smoothstep(0.9, 1.0, depth))` → gate ≈ 1.0 for most depths. Tap processes all pixels.

### 6.5 Depth Gate Fully Closed

**Condition:** `depth_min` and `depth_max` such that gate window doesn't overlap typical depth values.

**Behavior:** `depth_gate < 0.01` triggers early return in `apply_tap()`, skipping tap entirely.

### 6.6 Zero Block Size in Datamosh

**Condition:** `blockSize` parameter = 0 → `block = max(4.0, 0 + 4.0) = 4.0` (minimum enforced in shader line 134).

**Behavior:** Minimum block size of 4 pixels ensures some datamosh effect still occurs.

### 6.7 High Mosh Intensity

**Condition:** `moshIntensity` = 10.0 → mapped 1.0.

**Behavior:** Displacement = `block_diff.rg * 1.0 * 0.03 = block_diff.rg * 0.03`. Since `block_diff` can be up to ~1.0 per channel, max displacement ~0.03 UV units (30 pixels at 1000px width). This is moderate.

### 6.8 Unused Dual Input Flag

**Condition:** `hasDualInput` computed but never used.

**Behavior:** No effect on output. This is dead code.

**Expected Handling:** Could be removed, or used to switch between two input sources (like a blend mode). Legacy oversight.

### 6.9 Hard-Coded Cross-Feed Multipliers

**Condition:** Cross-feed mixing uses fixed factors: `* 0.5` for taps 1-3, `* 0.3` for tap4 recirc.

**Behavior:** User-controlled `tapXToTapY` parameters are scaled down before mixing. This limits cross-feed strength regardless of parameter value.

**Expected Handling:** Document these scalars. Consider exposing them as separate parameters if fine control needed.

### 6.10 Depth Normalization Range Violation

Same as DepthFXLoopEffect: values outside [0.3, 4.0] meters clamp to 0 or 255, causing depth gating errors.

---

## Mathematical Formulations

### 7.1 Parameter Mapping

Same linear mapping: `p_mapped = p_min + (p/10)*(p_max-p_min)`

For boolean `enable_loop`: `1 if p > 5.0 else 0`

### 7.2 Depth Gate

```glsl
float gate = smoothstep(d_min, d_min + 0.1, depth) * 
            (1.0 - smoothstep(d_max - 0.1, d_max, depth));
```

Transition width = 0.1 (hard-coded). Gate ∈ [0, 1].

### 7.3 Delay Displacement

```glsl
vec2 offset = vec2(
    sin(time * 0.3 + depth * 10.0) * delay * 0.01,
    cos(time * 0.4 + depth * 10.0) * delay * 0.01
);
```

- Time frequency: 0.3 and 0.4 rad/s (≈0.05 Hz)
- Depth modulation: `depth * 10.0` adds spatial variation
- Delay scaling: `delay * 0.01` (max delay=1.0 → 0.01 UV offset)
- Result: Subtle wiggling displacement, not a true temporal delay (no framebuffer read with time offset)

**Important:** This is **not** a true delay line. It's a time-varying UV distortion that simulates delay visually but does not actually store past frames beyond the single `texPrev` buffer. The effect relies on the feedback matrix to create temporal integration.

### 7.4 Datamosh Motion Detection

Block-based:

```glsl
vec2 block_uv = floor(uv * resolution / block) * block / resolution;
vec4 block_prev = texture(texPrev, block_uv);
vec3 block_diff = current.rgb - block_prev.rgb;
float motion = length(block_diff);
```

- `block = max(4.0, block_size * 40.0 + 4.0)` → block size ∈ [4, 44] pixels
- Motion = Euclidean distance in RGB space
- Displacement: `vec2(motion_vector) * mosh_intensity * 0.03`
- Blend: `smoothstep(0.05, 0.15, motion) * mosh_intensity`

So datamosh effect strength depends on both `moshIntensity` and actual motion in the frame.

### 7.5 Cross-Feed Mixing

For tap N (N≥2):

```glsl
vec4 cross_feed = mix(previous_result, previous_tap_output, cross_feed_factor * 0.5);
```

For tap4 recirculation:

```glsl
result = mix(result, cross_feed, tap4_to_tap1 * 0.3);
```

The `* 0.5` and `* 0.3` are **hard-coded dampeners**.

### 7.6 Feedback Loop Dynamics

Let:
- `I_t` = input frame at time t
- `F_t` = `texPrev` buffer (previous output)
- `D_t` = datamosh result from `I_t` and `F_t`
- `T1_t`, `T2_t`, `T3_t`, `T4_t` = tap outputs after processing
- `R1_t`, `R2_t`, `R3_t`, `R4_t` = tap return textures (external processing results)

Processing:

```
# Base datamosh
M_t = datamosh(I_t, F_{t-1})

# Tap 1
T1_t = apply_tap(M_t, R1_t, depth_t, ...)

# Tap 2 (with cross-feed from T1)
CF2_t = mix(M_t, T1_t, tap1_to_tap2 * 0.5)
T2_t = apply_tap(CF2_t, R2_t, depth_t, ...)

# Tap 3 (with cross-feed from T2)
CF3_t = mix(T2_t, T2_t_previous? Actually code uses result after tap2, which is T2_t)
T3_t = apply_tap(CF3_t, R3_t, depth_t, ...)

# Tap 4 (with cross-feed from T3)
CF4_t = mix(T3_t, T3_t_previous? code uses result after tap3)
T4_t = apply_tap(CF4_t, R4_t, depth_t, ...)

# Recirculation from T4 back to final mix
O_t = mix(T4_t, T4_t, tap4_to_tap1 * 0.3)  # Actually: result = mix(result, cross_feed, ...) after tap4

# Final blend with original
Output_t = mix(I_t, O_t, u_mix)
```

Then `F_t = Output_t` (written to `texPrev` for next frame).

The system is a **stateful** with memory in `texPrev` and the tap return textures (which are external framebuffers).

---

## Performance Characteristics

### 8.1 GPU Workload

**Fragment Shader Complexity:**
- ~200 lines
- Texture fetches:
  - `tex0` (1)
  - `tex1` (1, only for unused check)
  - `texPrev` (1 for datamosh block_prev, plus 1 in each enabled tap's `apply_tap` → up to 4 more)
  - `depth_tex` (1)
  - `tapX_return` (up to 4, if enabled)
  - **Total:** Up to 8 texture fetches per fragment (worst case all taps enabled)
- Math: HSV conversions? None. Blend modes? None. Just mix, smoothstep, sin/cos, length.
- Datamosh block operations: floor division, texture fetch, vector math

**GPU Tier:** MEDIUM — reasonable but not trivial.

### 8.2 CPU Overhead

- Per-frame: depth source update, depth texture upload (`glTexImage2D` — reallocates every frame, same performance issue as DepthFXLoopEffect)
- Parameter mapping: 20 parameters, trivial
- No audio reactivity setup

### 8.3 Bottlenecks

1. **Depth texture reallocation:** Uses `glTexImage2D` instead of `glTexSubImage2D`. Same issue as other depth effects.
2. **High texture fetch count:** Up to 8 textures per fragment can pressure texture cache, especially at high resolutions.
3. **Branching in `apply_tap`:** Early return if `depth_gate < 0.01` may cause divergence but likely okay.

### 8.4 Parallelization

- Fully parallel per-fragment
- Frame-to-frame dependencies via `texPrev` and tap return textures (must complete previous frame before next)
- No inter-fragment dependencies

---

## Test Plan

### 9.1 Unit Tests

**Target:** 80% coverage

**Test Cases:**

1. **Parameter Mapping**
   - Test all 20 parameters at boundaries (0, 10) and defaults
   - Verify `tapXEnableLoop` boolean conversion: >5.0 → 1, ≤5.0 → 0
   - Test default fallback (5.0)

2. **Depth Source Management**
   - `set_depth_source()` stores source
   - `update_depth_data()` calls `get_filtered_depth_frame()` and stores
   - Handles None source gracefully

3. **Tap Return Texture Management**
   - `set_tap_return_texture(0, 123)` sets `self.tap_return_textures[0] = 123`
   - Out-of-range indices ignored (no crash)
   - Initial values are 0

4. **Uniform Application (Mocked GL)**
   - Mock `self.shader.set_uniform` and verify:
     - All 20 parameters mapped and set
     - `tapX_enable_loop` set to 0 or 1 based on parameter
     - Texture uniforms: `depth_tex=2`, `tap1_return=3`, `tap2_return=4`, `tap3_return=5`, `tap4_return=6`
   - Test with depth frame: `glGenTextures` called once, `glTexImage2D` called with normalized data
   - Test without depth frame: no texture upload

5. **Depth Normalization**
   - Same as DepthFXLoop: test 0.3→0, 2.15→127.5, 4.0→255, out-of-range clamping

6. **Shader Compilation**
   - Compile `DEPTH_FEEDBACK_MATRIX_FRAGMENT` alone
   - Check all uniform locations can be queried
   - Link success

### 9.2 Integration Tests

1. **Single Tap Isolation**
   - Enable only tap1, set `tap1Feedback=10` (max), provide known return texture
   - Verify output mixes tap1 return into result according to depth gate
   - Repeat for each tap individually

2. **Cross-Feed Chain**
   - Enable taps 1-4 with cross-feeds >0
   - Provide distinct patterns for each tap return (e.g., solid colors: R, G, B, W)
   - Verify cross-feed mixing: tap2 output should contain mix of tap1 and tap2 return, etc.
   - Check tap4 recirculation affects final output

3. **Depth Gating**
   - Use a depth ramp (0.0 left to 1.0 right)
   - Configure tap with narrow depth window (e.g., min=0.4, max=0.6)
   - Verify tap effect only appears in center region

4. **Datamosh Motion**
   - Feed static image → no datamosh (motion=0)
   - Feed moving pattern → datamosh smear appears
   - Vary `blockSize` and `moshIntensity` to confirm effect

5. **Feedback Stability**
   - Configure simple loop: tap1 enabled, `tap1Feedback=0.5`, no cross-feeds
   - Feed constant color, check output converges to stable state (not diverging)
   - Increase feedback to 1.0 → should approach steady state or oscillate

6. **Preset Configurations**
   - Load each preset (`simple_dual_tap`, `cascading_depth_layers`, etc.)
   - Render with test pattern, verify behavior matches preset description
   - Ensure no crashes with all taps enabled

### 9.3 Visual Regression

Capture reference frames from legacy VJLive-2 for each preset with standard test pattern (color bars + depth gradient).

### 9.4 Edge Cases

- All taps disabled → output = datamosh(I, F) mixed with I via `u_mix`
- Extremely high cross-feed values → check for saturation
- Depth all zeros → no taps contribute (gate closed)
- Depth all ones → depends on depth_max settings

---

## Legacy Code References

**Primary Implementation:**  
`/home/happy/Desktop/claude projects/vjlive/plugins/vdepth/depth_feedback_matrix_datamosh.py`

- Lines 1-27: Module docstring with topology description
- Lines 38-196: `DEPTH_FEEDBACK_MATRIX_FRAGMENT` shader
- Lines 200-410: `DepthFeedbackMatrixDatamoshEffect` class

**Secondary Location (VJLive-2):**  
`/home/happy/Desktop/claude projects/vjlive-2/plugins/core/depth_feedback_matrix_datamosh/__init__.py` (identical per Qdrant)

**Plugin Manifest:**  
`/home/happy/Desktop/claude projects/vjlive-2/plugins/core/depth_feedback_matrix_datamosh/plugin.json`

**Memory Leak:**  
`gl_leaks.txt` reports `glGenTextures` without `glDeleteTextures` for this class. Must fix in VJLive3.

---

## VJLive3 Migration Considerations

### 10.1 WebGPU Translation

The shader is moderately complex but straightforward to port to WGSL:

- Multiple texture bindings: need a bind group with 8 textures (input, prev, depth, 4 returns, maybe video B unused)
- Uniform buffer for 20 parameters (plus any missing from base class)
- Same branching logic, but WGSL handles it fine
- No special features

**Suggested WGSL struct:**

```wgsl
struct Params {
    // Tap 1
    tap1_delay: f32,
    tap1_depth_min: f32,
    tap1_depth_max: f32,
    tap1_feedback: f32,
    tap1_enable_loop: f32,  // or u32
    
    // Tap 2
    tap2_delay: f32,
    tap2_depth_min: f32,
    tap2_depth_max: f32,
    tap2_feedback: f32,
    tap2_enable_loop: f32,
    
    // Tap 3
    tap3_delay: f32,
    tap3_depth_min: f32,
    tap3_depth_max: f32,
    tap3_feedback: f32,
    tap3_enable_loop: f32,
    
    // Tap 4
    tap4_delay: f32,
    tap4_depth_min: f32,
    tap4_depth_max: f32,
    tap4_feedback: f32,
    tap4_enable_loop: f32,
    
    // Cross-feed
    tap1_to_tap2: f32,
    tap2_to_tap3: f32,
    tap3_to_tap4: f32,
    tap4_to_tap1: f32,
    
    // Datamosh
    mosh_intensity: f32,
    block_size: f32,
    _pad: f32,  // align to 16-byte
}
```

### 10.2 Resource Management

- Must delete `depth_texture` in `__del__` or via a resource manager
- Does **not** own tap return textures — external ownership, so no cleanup here
- Must ensure `texPrev` feedback buffer is managed by the renderer (ping-pong)

### 10.3 Texture Unit Conflicts

The legacy code sets `depth_tex` to unit 2, but the base class likely uses unit 2 for something else? Actually base uses unit 0 for `tex0` and unit 1 for `texPrev`. So unit 2 is free. However, the shader also declares `tex1` (Video B) but we don't know which unit it's on. In the base class, maybe `tex1` is not used. Need to verify base class uniform assignments. To be safe, VJLive3 should define explicit texture bindings in a bind group layout and not rely on implicit unit numbers.

### 10.4 External Loop Interface

**Critical Design Decision:** How should tap returns be connected in VJLive3?

**Option A: Explicit Input Ports**
- Add 4 video input ports: `tap1_return`, `tap2_return`, `tap3_return`, `tap4_return`
- Node graph connects these from external effects' outputs
- Simple and explicit

**Option B: Automatic Feedback Buffers**
- The node graph automatically provides feedback framebuffers for each tap
- User inserts effects by "tapping into" the feedback chain via special routing nodes
- More magical but less transparent

**Recommendation:** Use Option A for clarity. Each tap return is an input port. The node's `apply_uniforms()` would then bind the textures from those ports. The `set_tap_return_texture()` method would be called by the renderer based on connected ports.

### 10.5 Dual Input Unused

The `tex1` and `hasDualInput` are vestigial. Remove them in VJLive3 unless there's a hidden feature we're missing. The legacy code may have intended to support two primary inputs (like a switch between two sources based on depth) but never completed.

### 10.6 Depth Normalization

Same issue as DepthFXLoop: hard-coded 0.3-4.0 meters. Should either:
- Make near/far parameters, OR
- Require depth source to provide normalized [0,1] and skip this step

### 10.7 Cross-Feed Hard-Coded Scalars

The 0.5 and 0.3 multipliers are buried in shader. Consider exposing as parameters `tapXToTapYStrength` if users need more control.

---

## Open Questions (Needs Research)

1. **Base class uniform setup:** Which texture units does the parent `Effect` class assign to `tex0` and `texPrev`? We assumed 0 and 1, but need to verify.
2. **`tex1` purpose:** Why is Video B sampled but unused? Could be a leftover or a disabled feature (e.g., switch between two inputs based on depth). Should we keep it?
3. **Tap return texture lifecycle:** Who creates and owns the tap return textures? Are they separate FBOs? How are they cleared/initialized?
4. **Feedback buffer (`texPrev`) management:** Same as other effects — likely handled by renderer.
5. **Audio reactivity:** Not present in this class. Should it be added? The effect could benefit from modulating feedback amounts or datamosh intensity with audio.
6. **Cross-feed direction:** The chain is linear: 1→2→3→4→1. Could it be made more flexible (e.g., arbitrary matrix)? Probably overkill.
7. **`u_mix` uniform:** Set by base class? What does it blend? Likely original vs processed. Need to check base class.

---

## Definition of Done (Pass 2)

- [x] Spec fully fleshed out with technical details
- [x] All parameters documented with types, ranges, defaults, and mapping
- [x] Shader logic explained line-by-line, including datamosh and tap processing
- [x] Edge cases identified and described
- [x] Mathematical formulations provided
- [x] Performance characteristics analyzed
- [x] Test plan with ≥80% coverage target
- [x] Legacy code references cited
- [x] Migration considerations for WebGPU outlined
- [x] Open questions tagged with `[NEEDS RESEARCH]`
- [ ] Spec reviewed by Manager or User
- [ ] Moved to `docs/specs/_02_fleshed_out/`
- [ ] BOARD.md updated to `🟩 COMPLETING PASS 2`
- [ ] Easter egg added to `WORKSPACE/EASTEREGG_COUNCIL.md`

---

## Appendix: Full Shader Listing

### A.1 DEPTH_FEEDBACK_MATRIX_FRAGMENT

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D tex1;        // Video B — pixel source (what gets datamoshed)
uniform sampler2D texPrev;
uniform sampler2D depth_tex;

// Multi-tap feedback returns (from external loops)
uniform sampler2D tap1_return;
uniform sampler2D tap2_return;
uniform sampler2D tap3_return;
uniform sampler2D tap4_return;

uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Tap configurations
uniform float tap1_delay;          // Delay amount (0-1)
uniform float tap1_depth_min;      // Min depth for this tap
uniform float tap1_depth_max;      // Max depth for this tap
uniform float tap1_feedback;       // Feedback amount
uniform int tap1_enable_loop;      // External loop enabled

uniform float tap2_delay;
uniform float tap2_depth_min;
uniform float tap2_depth_max;
uniform float tap2_feedback;
uniform int tap2_enable_loop;

uniform float tap3_delay;
uniform float tap3_depth_min;
uniform float tap3_depth_max;
uniform float tap3_feedback;
uniform int tap3_enable_loop;

uniform float tap4_delay;
uniform float tap4_depth_min;
uniform float tap4_depth_max;
uniform float tap4_feedback;
uniform int tap4_enable_loop;

// Cross-feed matrix
uniform float tap1_to_tap2;        // How much tap1 feeds tap2
uniform float tap2_to_tap3;
uniform float tap3_to_tap4;
uniform float tap4_to_tap1;        // Recirculation

// Datamosh
uniform float mosh_intensity;
uniform float block_size;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(443.897, 441.423))) * 43758.5453);
}

// Apply depth-gated feedback tap
vec4 apply_tap(vec4 current, sampler2D tap_return, float depth,
               float depth_min, float depth_max, float feedback,
               int enable_loop, float delay) {
    // Depth gating
    float depth_gate = smoothstep(depth_min, depth_min + 0.1, depth) *
                      (1.0 - smoothstep(depth_max - 0.1, depth_max, depth));
    
    if (depth_gate < 0.01) return current;
    
    // Sample from tap (with delay displacement)
    vec2 delay_offset = vec2(
        sin(time * 0.3 + depth * 10.0) * delay * 0.01,
        cos(time * 0.4 + depth * 10.0) * delay * 0.01
    );
    vec2 tap_uv = uv + delay_offset;
    tap_uv = clamp(tap_uv, 0.001, 0.999);
    
    vec4 tap_signal = texture(tap_return, tap_uv);
    
    // Mix with current based on feedback amount and depth gate
    float mix_amount = feedback * depth_gate;
    return mix(current, tap_signal, mix_amount);
}

void main() {

    // Detect if Video B is connected (not all black)
    vec4 testB = texture(tex1, vec2(0.5));
    bool hasDualInput = (testB.r + testB.g + testB.b) > 0.01;

    vec4 current = texture(tex0, uv);
    vec4 previous = texture(texPrev, uv);
    float depth = texture(depth_tex, uv).r;
    depth = clamp((depth - 0.3) / 3.7, 0.0, 1.0);  // Normalize
    
    // ====== DATAMOSH BASE ======
    float block = max(4.0, block_size * 40.0 + 4.0);
    vec2 block_uv = floor(uv * resolution / block) * block / resolution;
    
    vec4 block_prev = texture(texPrev, block_uv);
    vec3 block_diff = current.rgb - block_prev.rgb;
    float motion = length(block_diff);
    
    vec2 displacement = block_diff.rg * mosh_intensity * 0.03;
    vec2 mosh_uv = clamp(uv + displacement, 0.001, 0.999);
    vec4 datamoshed = texture(texPrev, mosh_uv);
    
    float mosh_blend = smoothstep(0.05, 0.15, motion) * mosh_intensity;
    vec4 result = mix(current, datamoshed, mosh_blend);
    
    // ====== FEEDBACK TAP 1: NEAR-FIELD ======
    if (tap1_enable_loop == 1) {
        result = apply_tap(result, tap1_return, depth,
                          tap1_depth_min, tap1_depth_max,
                          tap1_feedback, tap1_enable_loop, tap1_delay);
    }
    
    vec4 tap1_output = result;
    
    // ====== FEEDBACK TAP 2: MID-FIELD (with cross-feed from tap1) ======
    if (tap2_enable_loop == 1) {
        // Cross-feed from tap1
        vec4 cross_feed = mix(result, tap1_output, tap1_to_tap2 * 0.5);
        
        cross_feed = apply_tap(cross_feed, tap2_return, depth,
                              tap2_depth_min, tap2_depth_max,
                              tap2_feedback, tap2_enable_loop, tap2_delay);
        result = cross_feed;
    }
    
    vec4 tap2_output = result;
    
    // ====== FEEDBACK TAP 3: FAR-FIELD (with cross-feed from tap2) ======
    if (tap3_enable_loop == 1) {
        vec4 cross_feed = mix(result, tap2_output, tap2_to_tap3 * 0.5);
        
        cross_feed = apply_tap(cross_feed, tap3_return, depth,
                              tap3_depth_min, tap3_depth_max,
                              tap3_feedback, tap3_enable_loop, tap3_delay);
        result = cross_feed;
    }
    
    vec4 tap3_output = result;
    
    // ====== FEEDBACK TAP 4: RECIRCULATION (with cross-feed from tap3) ======
    if (tap4_enable_loop == 1) {
        vec4 cross_feed = mix(result, tap3_output, tap3_to_tap4 * 0.5);
        
        cross_feed = apply_tap(cross_feed, tap4_return, depth,
                              tap4_depth_min, tap4_depth_max,
                              tap4_feedback, tap4_enable_loop, tap4_delay);
        result = cross_feed;
        
        // Recirculate tap4 back to mix (creates infinite loops if not careful!)
        result = mix(result, cross_feed, tap4_to_tap1 * 0.3);
    }
    
    fragColor = mix(current, result, u_mix);
}
```

---
