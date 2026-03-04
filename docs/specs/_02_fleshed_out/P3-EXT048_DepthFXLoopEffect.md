# P3-EXT048 — DepthFXLoopEffect

**Status:** Pass 2 Fleshed Out  
**Agent:** desktop-roo  
**Date:** 2025-03-03  
**Legacy Origin:** VJLive (Original) + VJLive-2  
**Module ID:** `depth_fx_loop`  
**Class:** `DepthFXLoopEffect`  
**GPU Tier:** MEDIUM

---

## Executive Summary

The DepthFXLoopEffect is a sophisticated routing node that creates explicit feedback loops in the node graph, analogous to a modular synthesizer's effects send/return bus. It enables video signals to be routed out to external effect chains, processed, and returned for compositing with depth-gated mixing, temporal feedback, and multiple blend modes. This is the **central hub for modular video effects processing** in VJLive3.

**Key Innovation:** Unlike traditional effects that process internally, this node explicitly breaks the acyclic graph constraint to create intentional loops, enabling complex feedback architectures, multi-stage processing, and side-chaining between effects.

---

## What This Module Does

The DepthFXLoopEffect implements a **dual-shader architecture**:

1. **FX SEND** (output): Processes the input video with depth-aware operations and emits it to an external effects chain
2. **FX RETURN** (input): Receives the processed signal back and composites it with the original using:
   - Depth-gated mixing (only apply FX in specific depth ranges)
   - Wet/dry blend control
   - Four blend modes (Normal, Screen, Multiply, Difference)
   - Temporal feedback with decay and hue drift
   - Pre-send brightness/saturation adjustments

The node maintains a **feedback buffer** (`texPrev`) that stores the previous frame's output, enabling recursive processing that creates accumulating visual effects over time.

**Graph Topology:**
```
┌─────────────────────────────────────┐
│  Depth FX Loop                       │
│  ┌──video_in    fx_send──┐          │
│  │                       ↓          │
│  │  [External Effects Chain]        │
│  │                       ↓          │
│  └──depth_in   fx_return──┘         │
│       └──────video_out──────┘       │
└─────────────────────────────────────┘
```

---

## What This Module Does NOT Do

- **Does NOT** manage the external effects chain — that is the user's responsibility in the node graph
- **Does NOT** allocate feedback buffers automatically beyond the single `texPrev` texture
- **Does NOT** perform depth estimation — requires external depth map input
- **Does NOT** handle multi-pass rendering beyond the single feedback buffer
- **Does NOT** provide built-in effects — only the routing and compositing infrastructure
- **Does NOT** support multiple independent feedback loops (single loop only)

---

## Detailed Behavior and Parameter Interactions

### 2.1 Shader Architecture

#### 2.1.1 Main Fragment Shader (FX RETURN)

The primary shader runs on the output port and performs the final compositing:

**Input Textures:**
- `tex0` (unit 0): Original video input
- `texPrev` (unit 1): Previous frame's output (feedback buffer)
- `depth_tex` (unit 2): Depth map (single-channel, normalized 0-1)
- `fx_return_tex` (unit 3): Signal returning from external effects chain

**Processing Pipeline:**

1. **Depth Gate Calculation** (lines 116-121):
   ```glsl
   float gate = smoothstep(depth_gate_min - gate_softness * 0.1,
                          depth_gate_min + gate_softness * 0.1, depth) *
                (1.0 - smoothstep(depth_gate_max - gate_softness * 0.1,
                                  depth_gate_max + gate_softness * 0.1, depth));
   ```
   Creates a soft window where FX are applied. Gate = 1.0 when `depth_gate_min < depth < depth_gate_max`, with smooth transitions defined by `gate_softness`.

2. **Feedback Retrieval** (lines 123-135):
   - Reads `prev.rgb` from `texPrev`
   - Applies **brightness decay**: `feedback *= (1.0 - feedback_decay * 0.1)`
   - Applies **hue drift** if `feedback_hue_drift > 0`: rotates hue in HSV space by `feedback_hue_drift * 0.02` radians
   - Feedback is **not** depth-gated — it's a full-frame buffer

3. **Return Processing** (lines 137-144):
   - Applies selected **blend mode** between `source.rgb` and `returned.rgb`
   - Multiplies by `gate` and `return_opacity`
   - Result is: `blended = mix(source.rgb, blended, gate * return_opacity)`

4. **Wet/Dry Mix** (line 147):
   - `result = mix(source.rgb, blended, wet_dry)`

5. **Feedback Accumulation** (lines 149-152):
   - If `feedback_amount > 0`: `result = mix(result, feedback, feedback_amount * 0.5)`
   - This mixes in the processed previous frame, creating the loop

6. **Final Output** (line 154):
   - `fragColor = mix(source, vec4(clamp(result, 0.0, 1.5), 1.0), u_mix)`
   - Note: Clamp allows values up to 1.5 (HDR-like behavior), then `u_mix` blends with original source

#### 2.1.2 Send Fragment Shader (FX SEND)

The secondary shader runs on the `fx_send` output port:

**Input Textures:**
- `tex0`: Source video
- `depth_tex`: Depth map

**Send Modes** (based on `send_mode` parameter):

- **Mode 0** (Direct Send, `send_mode < 3.3`):
  - Applies brightness adjustment: `result *= pow(2.0, (send_brightness - 0.5) * 2.0)`
  - No depth processing

- **Mode 1** (Depth-Masked, `3.3 <= send_mode < 6.6`):
  - Computes depth mask: `mask = smoothstep(0.2, 0.4, depth) * (1.0 - smoothstep(0.6, 0.8, depth))`
  - Multiplies result by mask (only mid-depth pixels survive)
  - **Hard-coded depth range** (0.2-0.4 rising, 0.6-0.8 falling) — not parameterized!

- **Mode 2** (Depth-Displaced, `send_mode >= 6.6`):
  - Computes depth gradient using central differences:
    ```glsl
    float t = 2.0 / resolution.x;
    grad.x = texture(depth_tex, uv + vec2(t, 0)).r - texture(depth_tex, uv - vec2(t, 0)).r;
    grad.y = texture(depth_tex, uv + vec2(0, t)).r - texture(depth_tex, uv - vec2(0, t)).r;
    ```
  - Displaces UV: `displaced_uv = uv + grad * 0.05`
  - Samples source at displaced coordinates (creates refraction-like effect)

**Post-Processing (all modes):**
- Converts RGB to HSV
- Multiplies saturation by `send_saturation * 2.0` (range 0-2.0)
- Clamps saturation to [0, 1]
- Converts back to RGB

---

### 2.2 Parameter Mapping

All user-facing parameters are **0-10 normalized floats** (matching the VJLive UI slider convention). They are mapped to shader ranges via `_map_param()`:

```python
def _map_param(self, name, out_min, out_max):
    val = self.parameters.get(name, 5.0)
    return out_min + (val / 10.0) * (out_max - out_min)
```

**Parameter Dictionary** (lines 237-254):

| Parameter | Default | Shader Target | Mapped Range | Purpose |
|-----------|---------|---------------|--------------|---------|
| `sendMode` | 0.0 | `send_mode` | 0.0 - 10.0 | Selects send mode (0=direct, 3.3=masked, 6.6=displaced) |
| `wetDry` | 6.0 | `wet_dry` | 0.0 - 1.0 | Mix between original (0) and FX-returned (1) |
| `depthGateMin` | 0.0 | `depth_gate_min` | 0.0 - 1.0 | Lower bound of depth gate window |
| `depthGateMax` | 10.0 | `depth_gate_max` | 0.0 - 1.0 | Upper bound of depth gate window |
| `gateSoftness` | 3.0 | `gate_softness` | 0.0 - 1.0 | Transition width of depth gate |
| `feedbackAmount` | 4.0 | `feedback_amount` | 0.0 - 1.0 | Strength of temporal feedback |
| `feedbackDecay` | 3.0 | `feedback_decay` | 0.0 - 1.0 | Brightness loss per frame in feedback |
| `feedbackHueDrift` | 2.0 | `feedback_hue_drift` | 0.0 - 1.0 | Hue rotation per frame in feedback |
| `sendBrightness` | 5.0 | `send_brightness` | 0.0 - 1.0 | Pre-send brightness boost |
| `sendSaturation` | 5.0 | `send_saturation` | 0.0 - 1.0 | Pre-send saturation boost |
| `returnBlendMode` | 0.0 | `return_blend_mode` | 0.0 - 10.0 | Blend mode selector |
| `returnOpacity` | 7.0 | `return_opacity` | 0.0 - 1.0 | Opacity of returned signal |

**Default Values Analysis:**
- `wetDry = 6.0` → mapped 0.6 (moderate wet/dry mix)
- `depthGateMax = 10.0` → mapped 1.0 (includes all depths by default)
- `feedbackAmount = 4.0` → mapped 0.4 (moderate feedback)
- `returnOpacity = 7.0` → mapped 0.7 (fairly transparent FX)

---

### 2.3 Depth Source Management

The node does **not** generate depth. It expects an external depth source connected to the `depth_in` port. The depth source must implement:

```python
class DepthSource:
    def get_filtered_depth_frame(self) -> np.ndarray:
        """Returns depth map as float32 array, normalized [0, 1]"""
```

The legacy implementation uses a `depth_source` attribute set via `set_depth_source()`. The depth frame is updated each frame in `update_depth_data()` (line 274-276).

**Depth Texture Upload** (lines 282-296):
- First frame: generates GL texture with `glGenTextures(1)`
- Re-uses texture ID on subsequent frames (no re-allocation)
- Normalization: `dn = ((self.depth_frame - 0.3) / (4.0 - 0.3) * 255).astype(np.uint8)`
  - **Hard-coded depth range**: 0.3 to 4.0 (meters?) scaled to 0-255
  - This assumes depth values are in **meters** with near=0.3m, far=4.0m
  - Values outside range are clamped implicitly by the arithmetic
- Uploads as `GL_RED` single-channel texture
- Texture unit 2 bound for shader access

**Critical Observation:** The normalization uses fixed constants, not derived from camera intrinsics. This is a **legacy assumption** that may need revisiting in VJLive3 if depth sources vary.

---

### 2.4 Audio Reactivity

The node supports audio-driven parameter modulation via `AudioReactor`:

```python
self.audio_reactor.assign_audio_feature("fxloop", "wetDry", AudioFeature.BASS, 0.0, 1.0)
self.audio_reactor.assign_audio_feature("fxloop", "feedbackAmount", AudioFeature.MID, 0.0, 1.0)
self.audio_reactor.assign_audio_feature("fxloop", "returnOpacity", AudioFeature.TREBLE, 0.0, 1.0)
```

- **Bass** modulates `wetDry` (0.0 to 1.0)
- **Mid** modulates `feedbackAmount` (0.0 to 1.0)
- **Treble** modulates `returnOpacity` (0.0 to 1.0)

The audio modulation is applied **after** parameter mapping in `apply_uniforms()` (lines 326-332), overriding the static values with audio-derived ones.

---

## Public Interface

### 4.1 Constructor

```python
def __init__(self):
    super().__init__("depth_fx_loop", DEPTH_FX_LOOP_FRAGMENT)
```

- Registers shader name: `"depth_fx_loop"`
- Loads main fragment shader (DEPTH_FX_LOOP_FRAGMENT)
- Initializes parameters to defaults (see table above)
- Sets `self.depth_source = None`, `self.depth_frame = None`, `self.depth_texture = 0`

### 4.2 Core Methods

#### `set_depth_source(source: DepthSource)`
Attaches a depth source object that provides `get_filtered_depth_frame()`.

#### `set_audio_analyzer(analyzer: AudioAnalyzer)`
Enables audio reactivity. Creates `AudioReactor` and assigns default feature mappings (BASS→wetDry, MID→feedbackAmount, TREBLE→returnOpacity). If `analyzer` is `None`, disables audio reactivity.

#### `update_depth_data()`
Calls `self.depth_source.get_filtered_depth_frame()` if depth source exists. Stores result in `self.depth_frame`. Should be called each frame before rendering.

#### `apply_uniforms(time_val, resolution, audio_reactor=None, semantic_layer=None)`
Main per-frame method called by the rendering system:

1. Calls `super().apply_uniforms()` (sets up base shader uniforms)
2. Calls `self.update_depth_data()`
3. If depth frame exists:
   - Creates/updates GL texture with depth data
   - Sets uniform `depth_tex` to texture unit 2
4. Sets all texture uniforms (`tex0`, `texPrev`, `depth_tex`, `fx_return_tex`)
5. Maps and sets all scalar parameters via `self.shader.set_uniform()`
6. If audio reactor present, applies audio modulation overrides

**Note:** The method does **not** handle feedback buffer management (`texPrev`). That is expected to be managed by the parent rendering system (likely a ping-pong FBO setup).

---

## Inputs and Outputs

### 5.1 Node Graph Ports

Based on legacy `plugin.json` (from Qdrant snippets):

**Inputs:**
- `signal_in` (video): Main video stream to process
- `depth_in` (depth): Depth map for gating and displacement

**Outputs:**
- `signal_out` (video): Final composited result
- `fx_send` (video): Processed signal sent to external effects chain

**Type:** EFFECT node (not a generator or filter)

### 5.2 Data Format Expectations

**Video:**
- Format: RGBA8 or floating point (shader uses `vec4` throughout)
- Resolution: Arbitrary, but depth map **must match** video resolution exactly
- Color space: Linear RGB assumed (no sRGB conversion in shader)

**Depth:**
- Format: Single-channel (GL_RED)
- Normalized: [0, 1] floating point expected by shader
- **BUT** legacy upload normalizes from meters (0.3-4.0) to 0-255 uint8
- Resolution: Must match video resolution

**Feedback Buffer (`texPrev`):**
- Format: Same as video output
- Must be preserved between frames (ping-pong FBO)
- Initial content: undefined (first frame may show artifacts)

---

## Edge Cases and Error Handling

### 6.1 Missing Depth Source

**Condition:** `self.depth_source` is `None` or `get_filtered_depth_frame()` returns `None`/empty array.

**Behavior:** 
- Depth texture is **not** uploaded
- Shader uniform `depth_tex` still set to unit 2, but texture may be unbound
- Depth gate will use whatever value is in uninitialized texture (typically 0)
- **Result:** All depth-gated operations will likely zero out the FX

**Expected Handling:** The node graph should ensure depth source is connected. No explicit error is raised.

### 6.2 Depth Frame Size Mismatch

**Condition:** Depth frame dimensions do not match current viewport resolution.

**Behavior:**
- `glTexImage2D` will upload mismatched texture
- Shader samples with `texture(depth_tex, uv)` where `uv` is screen-space
- **Result:** Depth values will be misaligned or stretched

**Expected Handling:** The rendering system should validate depth resolution matches video resolution before binding.

### 6.3 First Frame Feedback

**Condition:** `texPrev` contains undefined data on first frame.

**Behavior:**
- Feedback path will inject garbage into output
- May cause flash or noise on first frame only

**Expected Handling:** Initialize feedback FBO to black or copy of first output after rendering.

### 6.4 Depth Normalization Range Violation

**Condition:** Depth values outside [0.3, 4.0] meters (or whatever the source produces).

**Behavior:**
- Normalization: `dn = ((depth_frame - 0.3) / (4.0 - 0.3) * 255)`
- Values < 0.3 → negative → wraps to large uint8 (255+)
- Values > 4.0 → >255 → clamped to 255 by `astype(np.uint8)`
- **Result:** Near depths (<0.3m) become 255 (far), far depths (>4.0m) become 255 (far). Everything clamps to far plane.

**Expected Handling:** Depth source should provide normalized [0,1] data, or the normalization constants should be configurable. **This is a legacy bug/limitation.**

### 6.5 Feedback Decay Overflow

**Condition:** `feedback_decay` mapped near 0 (little decay) over many frames.

**Behavior:**
- Feedback accumulates: `result = mix(result, feedback, feedback_amount * 0.5)`
- Without decay, values can grow unbounded (though clamped to 1.5 at output)
- **Result:** Eventually all pixels saturate to 1.5 (white bloom)

**Expected Handling:** Monitor feedback buffer values; decay should be >0 for stable loops.

### 6.6 Depth Gate Full Open

**Condition:** `depth_gate_min = 0`, `depth_gate_max = 1.0` (after mapping).

**Behavior:**
- `gate = smoothstep(0 - softness*0.1, 0 + softness*0.1, depth) * (1 - smoothstep(1.0 - softness*0.1, 1.0 + softness*0.1, depth))`
- For `depth` in [0,1], both smoothsteps evaluate to 1.0 if `softness` is reasonable
- **Result:** Gate = 1.0 everywhere (FX fully applied)

**Expected Handling:** This is intentional — full open is a valid state.

### 6.7 Send Mode 1 Hard-Coded Depth Range

**Condition:** Using `sendMode` in [3.3, 6.6) (depth-masked send).

**Behavior:**
- Mask computed as: `smoothstep(0.2, 0.4, depth) * (1.0 - smoothstep(0.6, 0.8, depth))`
- **Hard-coded** to pass depths between ~0.2-0.8 (approximate)
- No parameterization — user cannot adjust this range

**Expected Handling:** This is a **legacy limitation**. The VJLive3 spec should either:
- Expose these thresholds as parameters, OR
- Document that send mode 1 uses a fixed mid-depth mask

### 6.8 Audio Reactor Not Set

**Condition:** `audio_reactor` is `None` but audio analyzer was provided.

**Behavior:**
- Audio modulation calls will fail (no override applied)
- Static parameter values used instead

**Expected Handling:** Ensure `set_audio_analyzer()` is called if audio reactivity is desired.

---

## Mathematical Formulations

### 7.1 Parameter Mapping

All UI parameters `p ∈ [0, 10]` map to shader ranges:

```
p_mapped = p_min + (p / 10.0) * (p_max - p_min)
```

Where `(p_min, p_max)` depends on parameter (see Section 2.2 table).

**Inverse mapping** (for UI to display actual shader value):
```
p = 10.0 * (p_mapped - p_min) / (p_max - p_min)
```

### 7.2 Depth Gate

Soft window function:

```
gate(d) = S(d, d_min - w*0.1, d_min + w*0.1) × (1 - S(d, d_max - w*0.1, d_max + w*0.1))
```

Where:
- `d` = depth value ∈ [0, 1]
- `d_min`, `d_max` = gate bounds
- `w` = `gate_softness` ∈ [0, 1]
- `S(x, a, b)` = `smoothstep(a, b, x)` (Hermite interpolation)

**Properties:**
- `gate ≈ 0` when `d < d_min` or `d > d_max`
- `gate ≈ 1` when `d_min < d < d_max`
- Transition width ≈ `0.2 × w`

### 7.3 Blend Modes

Given base color `B` (original) and layer color `L` (FX returned):

- **Normal** (`mode < 3.3`): `R = L`
- **Screen** (`3.3 ≤ mode < 6.6`): `R = 1 - (1-B)×(1-L)`
- **Multiply** (`6.6 ≤ mode < 8.3`): `R = B × L`
- **Difference** (`mode ≥ 8.3`): `R = |B - L|`

All operations component-wise in RGB.

### 7.4 Feedback Loop

Let:
- `I_t` = input frame at time `t`
- `F_t` = feedback buffer content at time `t` (previous output)
- `R_t` = returned FX signal at time `t`
- `O_t` = final output at time `t`

Processing:

```
# Depth gate
G_t = gate(depth_t)

# Blend returned FX with input
B_t = blend(I_t, R_t, return_blend_mode)
M_t = mix(I_t, B_t, G_t × return_opacity)

# Wet/dry mix
W_t = mix(I_t, M_t, wet_dry)

# Feedback accumulation
F_t_processed = F_{t-1} × (1 - feedback_decay × 0.1)
if feedback_hue_drift > 0:
    F_t_processed = hue_rotate(F_t_processed, feedback_hue_drift × 0.02)

O_t = mix(W_t, F_t_processed, feedback_amount × 0.5)
```

Then `O_t` is written to feedback buffer for next frame.

**Note:** The `× 0.5` factor on `feedback_amount` is **hard-coded** — maximum feedback blend is 0.5 even if `feedback_amount` maps to 1.0.

### 7.5 Send Mode 1 Depth Mask

```
mask(d) = S(d, 0.2, 0.4) × (1 - S(d, 0.6, 0.8))
```

This creates a band-pass mask passing depths approximately 0.2-0.8. **Not parameterized.**

### 7.6 Send Mode 2 Depth Displacement

Gradient computation (central differences):

```
dx = depth(uv + (t, 0)) - depth(uv - (t, 0))
dy = depth(uv + (0, t)) - depth(uv - (0, t))
```

Where `t = 2.0 / resolution.x` (2-pixel step in UV space).

Displaced UV: `uv' = uv + (dx, dy) × 0.05`

The factor 0.05 controls displacement strength — **not parameterized** (hard-coded).

---

## Performance Characteristics

### 8.1 GPU Workload

**Fragment Shader Complexity:**
- Main shader: ~155 lines, multiple texture fetches (4), HSV conversions (conditional), blend modes, smoothsteps
- Send shader: ~75 lines, 2 texture fetches, optional gradient computation (4 extra fetches in mode 2)

**Texture Bandwidth:**
- Main shader: 4 texture reads per fragment (video, prev, depth, fx_return)
- Send shader: 2 texture reads (video, depth) + up to 4 extra for gradient (mode 2 only)

**Memory:**
- One persistent depth texture (size = viewport width × height × 1 byte)
- One feedback texture (size = viewport width × height × 4 bytes)
- Both allocated once, reused

**GPU Tier:** MEDIUM (as per legacy `plugin.json`)

### 8.2 CPU Overhead

- Per-frame: `update_depth_data()` calls depth source (may involve CPU-side filtering)
- Depth texture upload: `glTexImage2D` each frame (not `glTexSubImage2D` — re-allocates!)
  - **Performance Issue:** Legacy code re-uploads entire depth texture every frame with `glTexImage2D` instead of using `glTexSubImage2D` for updates. This causes GPU driver re-allocation overhead.
- Parameter mapping: trivial (12 parameters)

### 8.3 Bottlenecks

1. **Depth texture re-allocation:** Using `glTexImage2D` every frame forces GPU to allocate new memory. Should use persistent texture + `glTexSubImage2D`.
2. **Feedback buffer management:** Not shown in this class — assumed handled externally. Must be ping-pong FBO to read/write safely.
3. **HSV conversions:** Two HSV conversions per fragment in send shader (RGB→HSV→RGB). Could be optimized if saturation is 1.0 (no-op).

### 8.4 Parallelization

- Fully parallel per-fragment — no inter-fragment dependencies
- Feedback buffer introduces frame-to-frame dependency (must complete previous frame before starting next)
- Depth texture upload must complete before shader execution (CPU-GPU sync point)

---

## Test Plan

### 9.1 Unit Tests

**Minimum Coverage Target:** 80% of code paths

**Test Cases:**

1. **Parameter Mapping**
   - Test `_map_param()` for all parameters at boundaries (0, 10) and defaults
   - Verify linear mapping: `p=0 → out_min`, `p=10 → out_max`, `p=5 → midpoint`
   - Test default fallback: `parameters.get(name, 5.0)` returns 5.0 when key missing

2. **Depth Source Management**
   - `set_depth_source(None)` sets `self.depth_source = None`
   - `set_depth_source(obj)` stores object
   - `update_depth_data()` with `None` source leaves `depth_frame` unchanged/None
   - `update_depth_data()` with valid source calls `get_filtered_depth_frame()` and stores result

3. **Audio Reactor Setup**
   - `set_audio_analyzer(None)` results in `self.audio_reactor = None`
   - `set_audio_analyzer(analyzer)` creates `AudioReactor` and assigns 3 features
   - Verify feature assignments: `wetDry`→BASS, `feedbackAmount`→MID, `returnOpacity`→TREBLE

4. **Uniform Application (Mocked GL)**
   - Mock `self.shader.set_uniform` and verify calls:
     - Texture uniforms: `tex0=0`, `texPrev=1`, `depth_tex=2`, `fx_return_tex=3`
     - All 12 parameters mapped and set
     - Audio modulation overrides when reactor present
   - Test with `depth_frame = None` → no depth texture upload
   - Test with valid `depth_frame` → `glGenTextures` called once, `glTexImage2D` called with correct normalized data

5. **Depth Normalization**
   - Given depth array with values [0.3, 2.15, 4.0]:
     - 0.3 → 0
     - 2.15 → 127.5 (midpoint)
     - 4.0 → 255
   - Values <0.3 → negative → uint8 wraps to 255 (verify overflow behavior)
   - Values >4.0 → >255 → clamped to 255

6. **Shader Compilation**
   - Compile `DEPTH_FX_LOOP_FRAGMENT` and `DEPTH_FX_SEND_FRAGMENT` separately
   - Verify no GLSL errors
   - Check uniform locations can be queried

### 9.2 Integration Tests

1. **Full Rendering Pipeline**
   - Set up FBOs for feedback (ping-pong)
   - Render sequence of frames with known input video and depth
   - Connect mock external effects chain (identity shader) to `fx_send` → `fx_return`
   - Verify:
     - Output matches expectations for `wetDry=0` (dry) and `wetDry=1` (wet)
     - Feedback accumulates over frames when `feedbackAmount > 0`
     - Depth gate correctly masks FX when depth outside range

2. **Send Modes**
   - Test each send mode (0, 1, 2) with known patterns:
     - Mode 0: Output equals input × brightness factor
     - Mode 1: Output masked to mid-depths only (verify 0.2-0.8 range)
     - Mode 2: Output displaced according to depth gradient (verify refraction effect)

3. **Blend Modes**
   - Test all 4 blend modes with known `source` and `returned` colors
   - Verify mathematical formulas match specification

4. **Audio Modulation**
   - Mock `AudioReactor.get_audio_modulation()` to return known values
   - Verify overridden uniforms match audio-derived values
   - Test with audio reactor absent → static values used

5. **Feedback Decay and Hue Drift**
   - Render many frames with constant input and `feedbackAmount=1`
   - Verify brightness decays per frame according to `feedbackDecay`
   - Verify hue rotates per frame according to `feedbackHueDrift`

### 9.3 Visual Regression Tests

Capture reference frames from legacy VJLive-2 for known parameter sets and compare (within tolerance) to VJLive3 implementation.

**Scenarios:**
- Static image with depth gradient, `wetDry=0.5`, `feedbackAmount=0`
- Looping feedback with `feedbackAmount=0.5`, `feedbackDecay=0.1`
- Depth-gated FX with `depthGateMin=0.3`, `depthGateMax=0.7`
- All blend modes on test pattern

### 9.4 Edge Case Tests

- Zero depth frame (all zeros) → gate should zero FX
- Full white depth (all ones) → gate behavior depends on `depthGateMax`
- Mismatched depth resolution → expect misalignment (documented behavior)
- Extremely high `feedbackAmount` with zero decay → saturation after N frames
- `sendSaturation=0` in send shader → output grayscale

---

## Legacy Code References

### Primary Implementation

**File:** `/home/happy/Desktop/claude projects/vjlive/plugins/vdepth/depth_fx_loop.py`

- Lines 1-33: Module docstring with topology diagram
- Lines 44-156: `DEPTH_FX_LOOP_FRAGMENT` (main shader)
- Lines 159-219: `DEPTH_FX_SEND_FRAGMENT` (send shader)
- Lines 222-333: `DepthFXLoopEffect` class

**Secondary Location (VJLive-2):**  
`/home/happy/Desktop/claude projects/vjlive-2/plugins/core/depth_fx_loop/__init__.py` (identical content per Qdrant snippets)

**Plugin Manifest:**  
`/home/happy/Desktop/claude projects/vjlive-2/plugins/core/depth_fx_loop/plugin.json` (metadata, GPU tier, I/O ports)

**Memory Leak Note:**  
`gl_leaks.txt` identifies `DepthFXLoopEffect` as allocating `glGenTextures` without corresponding `glDeleteTextures`. The legacy code **does not clean up** the depth texture. VJLive3 must implement proper `__del__` or resource cleanup.

---

## VJLive3 Migration Considerations

### 10.1 WebGPU Translation

The legacy OpenGL ES 3.0 shader must be ported to WebGPU WGSL. Key differences:

- **Texture bindings:** WebGPU uses explicit bind group layouts. The 4 textures (`tex0`, `texPrev`, `depth_tex`, `fx_return_tex`) should be in a single bind group.
- **Uniform buffers:** Parameters should be packed into a uniform buffer struct rather than individual `set_uniform` calls.
- **Precision:** Use `f32` for all floats; consider `f16` if WebGPU implementation supports it for performance.
- **HSV functions:** WGSL lacks built-in `mix`, `step`, `smoothstep` — same as GLSL, but syntax differs.
- **Feedback buffer:** Must be a storage texture or separate texture with appropriate usage flags (`TEXTURE_BINDING | STORAGE_BINDING` depending on approach).

**Suggested WGSL struct:**

```wgsl
struct Params {
    send_mode: f32,
    wet_dry: f32,
    depth_gate_min: f32,
    depth_gate_max: f32,
    gate_softness: f32,
    feedback_amount: f32,
    feedback_decay: f32,
    feedback_hue_drift: f32,
    send_brightness: f32,
    send_saturation: f32,
    return_blend_mode: f32,
    return_opacity: f32,
    // padding to 16-byte alignment
    _pad: f32,
}
```

### 10.2 Resource Management

**Critical:** The legacy code leaks the depth texture. VJLive3 must:

1. Store `depth_texture` ID in a resource manager
2. Provide `release()` or `__del__()` that calls `glDeleteTextures([depth_texture])` (or WebGPU equivalent)
3. Also release feedback texture if owned by this node (likely not — it's external)

### 10.3 Parameter Normalization

The 0-10 UI scale is legacy. Consider:
- Keeping it for UI compatibility
- Internally using normalized [0,1] values
- Documenting the mapping explicitly in the node's schema

### 10.4 Depth Normalization

The hard-coded meter-to-byte conversion is problematic:

```python
dn = ((self.depth_frame - 0.3) / (4.0 - 0.3) * 255).astype(np.uint8)
```

**Recommendations:**
- Make near/far plane configurable parameters
- Or, require depth source to provide pre-normalized [0,1] data and skip this step
- If keeping legacy behavior, document the 0.3m-4.0m assumption

### 10.5 Send Mode 1 Hard-Coded Mask

The depth-masked send uses fixed thresholds (0.2, 0.4, 0.6, 0.8). This is **not parameterized** and likely a bug/oversight.

**Recommendation:** Either:
- Expose `sendMaskMin`/`sendMaskMax` parameters, OR
- Document that mode 1 uses a fixed mid-depth band and consider removing it if not useful

### 10.6 Feedback Buffer Ownership

The legacy code does not show who owns `texPrev`. In VJLive3:
- This node should likely **own** its feedback texture
- Allocate in `__init__` or first frame
- Manage ping-pong between two textures (read from N-1, write to N)
- Provide method to swap buffers each frame

---

## Open Questions (Needs Research)

1. **Feedback buffer lifecycle:** Who creates `texPrev`? Is it a separate FBO managed by the node graph, or should this node allocate it?
2. **Depth source interface:** What is the exact contract for `get_filtered_depth_frame()`? Return type (float32? uint8?), normalization (0-1 or meters?), dimensions.
3. **External effects chain routing:** How does `fx_send` connect to external nodes and back to `fx_return`? Is this a special graph edge type?
4. **GPU resource cleanup:** Is there a base `Effect` class that handles texture cleanup? The leak report suggests not.
5. **Send mode 1 mask:** Are the 0.2/0.4/0.6/0.8 thresholds documented anywhere, or just magic numbers?
6. **`u_mix` uniform:** What is `u_mix`? It appears in final line but is not set in `apply_uniforms()`. Likely inherited from base class? Need to check `Effect` base class.

---

## Definition of Done (Pass 2)

- [x] Spec fully fleshed out with technical details
- [x] All parameters documented with types, ranges, defaults, and mapping
- [x] Shader logic explained line-by-line
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

## Appendix: Full Shader Listings

### A.1 Main Fragment Shader (DEPTH_FX_LOOP_FRAGMENT)

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;           // Original video
uniform sampler2D texPrev;        // Previous frame (for temporal feedback)
uniform sampler2D depth_tex;      // Depth map
uniform sampler2D fx_return_tex;  // Coming back from external FX chain
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Core
uniform float send_mode;           // What to send out (0=video, 3.3=depth-masked, 6.6=depth-displaced)
uniform float wet_dry;             // Mix between original (dry) and returned FX (wet)
uniform float depth_gate_min;      // Only return FX signal where depth > min
uniform float depth_gate_max;      // Only return FX signal where depth < max
uniform float gate_softness;       // Gate transition softness

// Feedback
uniform float feedback_amount;     // How much previous frame bleeds through
uniform float feedback_decay;      // Brightness decay per feedback iteration
uniform float feedback_hue_drift;  // Color shift per feedback cycle

// Send processing
uniform float send_brightness;     // Pre-send brightness
uniform float send_saturation;     // Pre-send saturation

// Return processing
uniform float return_blend_mode;   // 0=normal, 3.3=screen, 6.6=multiply, 10=difference
uniform float return_opacity;      // Opacity of returned signal

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0/3.0, 1.0/3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

// Blend modes
vec3 blend(vec3 base, vec3 layer, float mode) {
    vec3 result;
    if (mode < 3.3) {
        // Normal
        result = layer;
    } else if (mode < 6.6) {
        // Screen (brighten — great for neon/glow effects)
        result = 1.0 - (1.0 - base) * (1.0 - layer);
    } else if (mode < 8.3) {
        // Multiply (darken — great for shadow effects)
        result = base * layer;
    } else {
        // Difference (psychedelic — phase cancellation)
        result = abs(base - layer);
    }
    return result;
}

void main() {
    vec4 source = texture(tex0, uv);
    vec4 prev = texture(texPrev, uv);
    float depth = texture(depth_tex, uv).r;
    vec4 fx_ret = texture(fx_return_tex, uv);

    // ====== DEPTH GATE ======
    // Only allow returned FX signal in certain depth ranges
    float gate = smoothstep(depth_gate_min - gate_softness * 0.1,
                           depth_gate_min + gate_softness * 0.1, depth) *
                 (1.0 - smoothstep(depth_gate_max - gate_softness * 0.1,
                                   depth_gate_max + gate_softness * 0.1, depth));

    // ====== FEEDBACK ======
    vec3 feedback = prev.rgb;
    if (feedback_amount > 0.0) {
        // Decay brightness
        feedback *= (1.0 - feedback_decay * 0.1);

        // Hue drift
        if (feedback_hue_drift > 0.0) {
            vec3 fb_hsv = rgb2hsv(clamp(feedback, 0.0, 1.0));
            fb_hsv.x = fract(fb_hsv.x + feedback_hue_drift * 0.02);
            feedback = hsv2rgb(fb_hsv);
        }
    }

    // ====== RETURN PROCESSING ======
    vec3 returned = fx_ret.rgb;

    // Apply blend mode
    vec3 blended = blend(source.rgb, returned, return_blend_mode);

    // Apply gate — FX only in gated depth range
    blended = mix(source.rgb, blended, gate * return_opacity);

    // ====== WET/DRY MIX ======
    vec3 result = mix(source.rgb, blended, wet_dry);

    // ====== ACCUMULATE FEEDBACK ======
    if (feedback_amount > 0.0) {
        result = mix(result, feedback, feedback_amount * 0.5);
    }

    fragColor = mix(source, vec4(clamp(result, 0.0, 1.5), 1.0), u_mix);
}
```

### A.2 Send Fragment Shader (DEPTH_FX_SEND_FRAGMENT)

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform float time;
uniform vec2 resolution;

uniform float send_mode;
uniform float send_brightness;
uniform float send_saturation;

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0/3.0, 1.0/3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

void main() {
    vec4 source = texture(tex0, uv);
    float depth = texture(depth_tex, uv).r;
    vec3 result = source.rgb;

    if (send_mode < 3.3) {
        // Direct send — just brightness/saturation
        result *= pow(2.0, (send_brightness - 0.5) * 2.0);
    }
    else if (send_mode < 6.6) {
        // Depth-masked send — only send pixels in certain depth range
        float mask = smoothstep(0.2, 0.4, depth) * (1.0 - smoothstep(0.6, 0.8, depth));
        result *= mask;
    }
    else {
        // Depth-displaced send — warp the video using depth as displacement
        vec2 grad;
        float t = 2.0 / resolution.x;
        grad.x = texture(depth_tex, uv + vec2(t, 0)).r - texture(depth_tex, uv - vec2(t, 0)).r;
        grad.y = texture(depth_tex, uv + vec2(0, t)).r - texture(depth_tex, uv - vec2(0, t)).r;
        vec2 displaced_uv = uv + grad * 0.05;
        result = texture(tex0, clamp(displaced_uv, 0.001, 0.999)).rgb;
    }

    // Pre-send saturation adjust
    vec3 hsv = rgb2hsv(clamp(result, 0.0, 1.0));
    hsv.y *= send_saturation * 2.0;
    hsv.y = clamp(hsv.y, 0.0, 1.0);
    result = hsv2rgb(hsv);

    fragColor = vec4(result, 1.0);
}
```

---
