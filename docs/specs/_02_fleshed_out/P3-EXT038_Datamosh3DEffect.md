# Datamosh3DEffect — Depth-Driven Pixel Sorting and Smearing

**Task ID:** P3-EXT038  
**Module:** `Datamosh3DEffect`  
**Phase:** Pass 2 Fleshing Out  
**Status:** Ready for Phase 3 Review  

---

## Overview

The [`Datamosh3DEffect`](docs/specs/_02_fleshed_out/P3-EXT038_Datamosh3DEffect.md:67) class implements a depth-driven datamosh effect that uses depth map gradients to simulate optical flow and create pixel smearing artifacts. The effect samples the previous frame with an offset determined by the depth gradient, then mixes the previous and current frames based on flow magnitude and decay parameters. This creates a glitchy, smeared visual style that responds to depth changes.

**What This Module Does**

- Calculates optical flow from depth map gradients (finite differences)
- Applies pixel smearing by sampling the previous frame with flow-based offset
- Mixes previous and current frames based on flow magnitude and decay
- Adds optional noise to flow for chaotic displacement
- Provides depth-aware feedback loop that preserves structure
- Supports audio reactivity for dynamic parameter modulation
- Provides 4 core parameters plus mix control

**What This Module Does NOT Do**

- Does not include traditional datamosh compression artifacts (no motion vector displacement from video encoding)
- Does not support 3D geometry or raymarching (uses 2D depth gradient)
- Does not provide temporal smoothing beyond the single `texPrev` feedback
- Does not include color grading or palette effects
- Does not support multiple feedback loops or complex temporal networks

---

## Detailed Behavior and Parameter Interactions

### Texture Unit Layout

The effect uses the following texture units:

| Unit | Name | Type | Purpose |
|------|------|------|---------|
| 0 | `tex0` | `sampler2D` | Current video frame |
| 1 | `texPrev` | `sampler2D` | Previous frame (feedback buffer) |
| 2 | `texDepth` | `sampler2D` | Depth map (single channel, typically red) |

**Important:** The effect expects `texDepth` to be bound to texture unit 2. This is hardcoded in the `apply_uniforms` method: `self.shader.set_uniform("texDepth", 2)`.

### Core Algorithm: Depth-Driven Flow and Feedback

The effect operates in a single pass with the following steps:

1. **Parameter normalization**:
   ```glsl
   float strength = flow_strength / 10.0;
   float thresh = depth_threshold / 10.0;
   float dec = decay / 10.0;
   float noise = noise_amount / 10.0;
   ```

2. **Depth sampling and gradient calculation**:
   ```glsl
   float d = texture(texDepth, uv).r;
   float dx = d - texture(texDepth, uv + vec2(0.01, 0.0)).r;
   float dy = d - texture(texDepth, uv + vec2(0.0, 0.01)).r;
   vec2 flow = vec2(dx, dy) * strength * 50.0;
   ```

   The flow vector is computed as the depth gradient (finite difference with 0.01 offset) scaled by `flow_strength` and a constant factor of 50.0. This means the maximum flow offset is approximately `(1.0 * 5.0 * 50.0) = 250` pixels in normalized coordinates? Actually, the gradient is in depth units (0-1), so `dx` and `dy` are in range [-1, 1]. Multiplying by `strength * 50.0` gives a flow in texture coordinate space (0-1). With `strength=1.0` (flow_strength=10), max flow is 50.0 in UV space, which is huge (50x the texture size). This seems off. Let's recalculate: `dx` is depth difference, typically small. If depth changes by 0.1 over 0.01 UV, then `dx=0.1`, flow = 0.1 * 1.0 * 50 = 5.0 UV units — that's 5 times the texture size, which would wrap or clamp. This suggests the scaling might be intended for pixel coordinates, not UV. But the code uses UV coordinates. There may be a bug or the `0.01` offset is in UV and the scaling is meant to produce small offsets. Actually, if we want flow in UV, a typical optical flow might be a few percent. With `strength=0.5` (flow_strength=5), and depth gradient 0.05, flow = 0.05 * 0.5 * 50 = 1.25 UV — still large. Possibly the `50.0` should be `0.5`? Or the offset should be smaller? This needs verification from legacy behavior. [NEEDS RESEARCH]

3. **Noise addition**:
   ```glsl
   flow += (vec2(random(uv + time), random(uv - time)) - 0.5) * noise * 0.1;
   ```

   Random noise in range [-0.5, 0.5] scaled by `noise * 0.1`. With `noise=1.0` (noise_amount=10), the noise contribution is up to 0.05 UV units — small.

4. **Previous frame lookup with offset**:
   ```glsl
   vec2 lookup = uv - flow;
   vec4 prev = texture(texPrev, lookup);
   ```

   The previous frame is sampled at `uv - flow`. This creates the smear effect: pixels from elsewhere in the previous frame are brought here.

5. **Current frame sample**:
   ```glsl
   vec4 curr = texture(tex0, uv);
   ```

6. **Mix factor calculation**:
   ```glsl
   float diff = length(flow);
   float mixFactor = smoothstep(thresh, thresh + 0.1, diff);
   mixFactor = max(mixFactor, 0.05);
   mixFactor = mix(mixFactor, 1.0, 1.0 - dec);
   ```

   The mix factor determines how much of the current frame to use vs. previous frame. It is based on the flow magnitude:
   - If `diff` is below `thresh`, `mixFactor` is 0 (mostly previous frame)
   - If `diff` is above `thresh+0.1`, `mixFactor` is 1 (mostly current frame)
   - A minimum of 0.05 ensures some refresh
   - `decay` (dec) reduces the mix factor over time? Actually `mix(mixFactor, 1.0, 1.0 - dec)` means: if `dec` is high (close to 1.0), then `1.0 - dec` is small, so `mixFactor` stays near its current value. If `dec` is low, then `1.0 - dec` is large, pushing `mixFactor` toward 1.0. So `decay` controls how quickly the feedback fades to the current frame. High `decay` means persistent smearing (low mix factor), low `decay` means quick refresh (high mix factor). This matches the description: "feedback decay".

7. **Final blend**:
   ```glsl
   fragColor = mix(prev, curr, mixFactor);
   ```

### Parameter Space and UI Mapping

All user-facing parameters use a normalized `0.0` to `10.0` range. The shader expects these parameters already divided by 10.0, so the Python class likely passes them directly or divides them in `apply_uniforms`. Looking at the legacy code, the class does not override `apply_uniforms` except to set `texDepth`. The base class `Effect.apply_uniforms` likely sets all parameters from `self.parameters` directly. The shader code divides by 10.0 internally: `float strength = flow_strength / 10.0;` etc. So the Python class should store parameters in the 0-10 range and the shader will normalize.

| Parameter | UI Range | Shader Usage | Purpose |
|-----------|----------|--------------|---------|
| `flow_strength` | 0.0-10.0 | `flow_strength / 10.0` → scales depth gradient | Intensity of depth-driven displacement |
| `depth_threshold` | 0.0-10.0 | `depth_threshold / 10.0` → threshold for mix factor | Sensitivity to depth edges for pixel refresh |
| `decay` | 0.0-10.0 | `decay / 10.0` → feedback persistence | Feedback persistence (0=instant fade, 10=infinite) |
| `noise_amount` | 0.0-10.0 | `noise_amount / 10.0` → noise scale | Random chaotic displacement |
| `u_mix` | 0.0-10.0 | Likely used by base class for final blend | Blend between original and effect result |

**Note:** The `u_mix` parameter is in `_parameter_ranges` and `parameters` but not used in the custom shader code. It is likely used by the base `Effect` class to blend the effect output with the original input at a higher level (e.g., in `EffectChain`). The shader itself outputs the full effect; `u_mix` is applied externally.

### Audio Reactivity

The legacy code does **not** define `audio_mappings` for this effect. The skeleton may have included it, but the actual implementation lacks audio reactivity. This is a gap. If audio reactivity is desired, it would need to be added. [NEEDS RESEARCH]

### Preset Configurations

The legacy code does **not** define any presets. The skeleton may have included placeholder presets, but the actual implementation has none. This effect would benefit from presets like "subtle_flow", "heavy_smear", "chaotic", etc. [NEEDS RESEARCH]

---

## Public Interface

### Class: `Datamosh3DEffect`

**Inheritance:** [`Effect`](docs/specs/_02_fleshed_out/P3-EXT038_Datamosh3DEffect.md:67) (from `core.effects.shader_base`)

**Constructor:** `__init__(self, width=VideoConstants.DEFAULT_WIDTH, height=VideoConstants.DEFAULT_HEIGHT)`

Initializes the effect with default parameters:

```python
self._parameter_ranges = {
    'flow_strength': (0.0, 10.0),
    'depth_threshold': (0.0, 10.0),
    'decay': (0.0, 10.0),
    'noise_amount': (0.0, 10.0),
    'u_mix': (0.0, 10.0)
}
self.parameters = {
    'flow_strength': 5.0,
    'depth_threshold': 2.0,
    'decay': 9.0,
    'noise_amount': 1.0,
    'u_mix': 10.0
}
self._parameter_descriptions = {
    'flow_strength': "Intensity of depth-driven displacement",
    'depth_threshold': "Sensitivity to depth edges for pixel refresh",
    'decay': "Feedback persistence (0=instant fade, 10=infinite)",
    'noise_amount': "Random chaotic displacement"
}
self._sweet_spots = {
    'flow_strength': [2.0, 5.0, 8.0],
    'decay': [9.0, 9.8],
    'depth_threshold': [1.5]
}
```

**Properties:**

- `name = "Datamosh 3D"`
- `fragment_shader = DATAMOSH_3D_FRAGMENT` — GLSL fragment shader (lines 6-64 in legacy file)
- `effect_category = "glitch"`
- `effect_tags = ["depth", "datamosh", "distortion", "feedback"]`
- `features = ["DEPTH_AWARE", "FEEDBACK_LOOP"]`
- `usage_tags = ["REQUIRES_DEPTH"]`
- `_parameter_ranges` — dict of parameter ranges
- `_parameter_descriptions` — dict of human-readable descriptions
- `_sweet_spots` — dict of recommended parameter values for quick presets

**Methods:**

- `render(tex_in: int, extra_textures: list = None, chain=None) -> int`: Custom render to handle `texDepth` binding. Expects `extra_textures[0]` to be the depth texture. Binds depth to texture unit 2. Returns `tex_in` (the chain handles drawing).
- `apply_uniforms(time: float, resolution: tuple, audio_reactor=None, semantic_layer=None)`: Overrides base to set `texDepth` uniform to 2. Also calls `super().apply_uniforms(...)` to set other uniforms.

**Class Attributes:**

- `DATAMOSH_3D_FRAGMENT` — The full GLSL shader code (lines 6-64).
- `BASE_VERTEX_SHADER` — Inherited from `Effect`.

---

## Inputs and Outputs

### Inputs

| Pin | Type | Description |
|-----|------|-------------|
| `tex0` | `sampler2D` | Current video frame |
| `texPrev` | `sampler2D` | Previous frame (feedback buffer) |
| `texDepth` | `sampler2D` | Depth map (single channel, typically red) |
| `u_mix` | `float` | Blend factor between original and effect result (0.0-1.0) — likely used by base class |
| `time` | `float` | Shader time in seconds (for noise animation) |
| `resolution` | `vec2` | Viewport resolution in pixels |
| `uv` | `vec2` | Normalized texture coordinates |

All parameters are passed as uniforms (see table above).

### Outputs

| Pin | Type | Description |
|-----|------|-------------|
| `fragColor` | `vec4` | RGBA output with datamosh effect applied (alpha unchanged) |

---

## Edge Cases and Error Handling

### Edge Cases

1. **No previous frame**: `texPrev` must be a valid texture containing the previous frame's output. If not provided or uninitialized, the feedback will sample undefined data (likely black or garbage). The host must manage framebuffer ping-pong.

2. **No depth map**: `texDepth` is required. The effect binds it to texture unit 2 via `apply_uniforms`. If not provided, the depth gradient will be zero, resulting in zero flow (unless noise is added). The effect will essentially just pass through the current frame with minimal mixing based on decay.

3. **Extreme parameter values**:
   - `flow_strength = 10.0` → `strength = 1.0`, flow = `depth_gradient * 50.0`. With a depth gradient of 1.0 (max possible over 0.01 offset), flow = 50.0 UV units — far outside the texture, causing complete wrap/clamp and total garbage. This parameter needs careful scaling or clamping. [NEEDS RESEARCH]
   - `depth_threshold = 10.0` → `thresh = 1.0`. Since `diff = length(flow)` and flow can be huge, `smoothstep(1.0, 1.1, diff)` will be 1.0 for most non-zero flow, meaning always refresh (no smear). This effectively disables the effect.
   - `decay = 0.0` → `dec = 0.0`, then `mixFactor = mix(mixFactor, 1.0, 1.0)` = 1.0 always, so no persistence (always current frame).
   - `decay = 10.0` → `dec = 1.0`, then `mixFactor = mix(mixFactor, 1.0, 0.0)` = `mixFactor` unchanged, so persistence is high (low refresh).
   - `noise_amount = 10.0` → `noise = 1.0`, noise contribution up to 0.05 UV — moderate.

4. **Flow magnitude overflow**: The flow calculation can produce very large values if depth gradient is large. This can cause `lookup = uv - flow` to be far outside [0,1], leading to texture wrap or clamp artifacts. The shader does not clamp `lookup`. This is a potential source of visual artifacts but not crashes.

5. **Division by zero**: None.

6. **Random function**: The `random` function uses `fract(sin(dot(...)) * 43758.5453123)`. This is standard and safe.

7. **Audio reactivity**: Not implemented. If added, would need to modulate parameters.

### Error Handling

- **No runtime errors** — all operations are safe GLSL.
- **Parameter clamping**: Python `set_parameter()` should clamp values to [0.0, 10.0] as per `_parameter_ranges`.
- **No NaN propagation**: All math is well-conditioned except possibly large flow values, but those produce finite floats.

---

## Mathematical Formulations

### Parameter Normalization

All UI parameters `p_ui` ∈ [0, 10] are divided by 10.0 in the shader:

```
strength = flow_strength / 10.0
thresh = depth_threshold / 10.0
dec = decay / 10.0
noise = noise_amount / 10.0
```

### Flow Calculation

The optical flow vector is computed as:

```
dx = d(uv) - d(uv + (0.01, 0))
dy = d(uv) - d(uv + (0, 0.01))
flow = (dx, dy) * strength * 50.0
```

where `d(uv)` is the depth value at coordinate `uv`. This is a simple forward difference gradient.

**Issue:** The scaling factor 50.0 is large. If `dx` is in the range [-1, 1] (depth difference), then `flow` components can be up to `strength * 50.0`. With `strength=1.0`, that's 50.0 UV units, which is 50 times the texture size. This suggests either:
- The `0.01` offset is in pixel units, not UV? But the code uses UV offsets.
- The scaling factor should be much smaller (e.g., 0.5 or 0.05).
- The depth values are not normalized 0-1? Possibly they are in some other range.

This needs verification against legacy behavior. [NEEDS RESEARCH]

### Mix Factor

The mix factor between previous and current frame is:

```
diff = length(flow)
mixFactor = smoothstep(thresh, thresh + 0.1, diff)
mixFactor = max(mixFactor, 0.05)
mixFactor = mix(mixFactor, 1.0, 1.0 - dec)
```

Interpretation:
- If `diff` is low (below `thresh`), `mixFactor` ≈ 0 → use mostly previous frame (smear).
- If `diff` is high (above `thresh+0.1`), `mixFactor` ≈ 1 → use mostly current frame (refresh).
- The minimum 0.05 ensures some refresh always.
- `decay` (dec) pushes `mixFactor` toward 1.0 when `dec` is low (less decay, more refresh). When `dec` is high, `mixFactor` stays closer to its smoothstep value (more persistence).

### Noise

Random noise is added to flow:

```
noise_vec = (random(uv + time), random(uv - time)) - 0.5
flow += noise_vec * noise * 0.1
```

The `random` function is a standard GLSL hash.

---

## Performance Characteristics

### Computational Complexity

- **Base cost**: Low to moderate. The shader performs:
  - 3 texture samples: `texDepth` (2 extra samples for gradient), `texPrev`, `tex0` → total 4 samples per pixel (5 if counting both gradient samples separately? Actually: depth at uv, depth at uv+offset_x, depth at uv+offset_y = 3 depth samples, plus prev and curr = 5 total)
  - Simple arithmetic: gradient, length, smoothstep, mix
  - 2 calls to `random` function (which uses sin, dot, fract)
- **No loops** — constant time.
- **Light to moderate GPU load**: This is a `MEDIUM` tier effect as per plugin manifest. Expect 1-3ms per 1080p frame on modern GPU.

### Memory Usage

- **Uniforms**: 5 floats + standard uniforms (time, resolution) = ~7 uniforms.
- **Textures**: Requires 3 texture units bound simultaneously.
- **Framebuffer**: Requires a separate framebuffer for `texPrev` feedback (ping-pong). The host must manage this.

### GPU Optimization Notes

- The effect is relatively lightweight. The main cost is the 5 texture samples per pixel.
- The depth gradient could be computed more efficiently using a single sample with derivative instructions (`dFdx`, `dFdy`), but that would require changing the algorithm.
- The `random` function uses `sin` and `dot`, which are moderately expensive but only called twice per pixel.
- Suitable for real-time at 1080p and likely 4K on modern GPUs.

---

## Test Plan

**Minimum coverage:** 80% before task is marked done.

### Unit Tests (Python)

1. **Parameter remapping**: Since the shader divides by 10.0 internally, verify that passing `flow_strength=5.0` results in `strength=0.5` in the shader (via uniform query or by checking shader behavior).
2. **Parameter clamping**: Test `set_parameter` clamps to [0.0, 10.0].
3. **Get/set symmetry**: For each parameter, verify `get_parameter` returns the value set.
4. **Default parameters**: Verify all 5 parameters have expected default values.
5. **Parameter ranges**: Verify `_parameter_ranges` dict contains correct min/max for each parameter.
6. **Parameter descriptions**: Verify `_parameter_descriptions` contains all keys.
7. **Sweet spots**: Verify `_sweet_spots` contains expected keys and value lists.
8. **Metadata**: Verify `effect_category`, `effect_tags`, `features`, `usage_tags` are set correctly.
9. **Render method**: Test that `render` binds depth texture to unit 2 and returns `tex_in`.
10. **Apply uniforms**: Test that `apply_uniforms` calls super and sets `texDepth` to 2.

### Integration Tests (Shader Rendering)

11. **Flow direction**: Render with a synthetic depth gradient (e.g., depth increasing to the right) and verify flow direction matches gradient (pixels smear leftward if depth increases to the right? Actually flow = (dx, dy) * strength, and lookup = uv - flow. So if dx positive (depth higher to the right), flow positive, lookup = uv - positive → leftward smear. That seems plausible.)
12. **Flow strength**: Test that increasing `flow_strength` increases smear distance.
13. **Depth threshold**: Test that increasing `depth_threshold` reduces smear in areas of low depth gradient (only high gradients cause refresh).
14. **Decay**: Test that `decay=0` gives no persistence (mostly current frame), while `decay=10` gives strong persistence (smearing).
15. **Noise**: Test that `noise_amount` adds random jitter to smear direction.
16. **Depth requirement**: Test with no depth map (all zeros) and verify effect essentially passes through with minimal mixing.
17. **Feedback loop**: Render consecutive frames and verify temporal persistence (smearing builds up over time).
18. **Edge case: zero flow**: With `flow_strength=0` and `noise_amount=0`, verify output is just mix of prev and curr based on decay (no spatial smear).
19. **Edge case: high flow**: With `flow_strength=10` and high depth gradient, verify sampling wraps/clamps as expected.
20. **Audio reactivity**: Not applicable (not implemented). [NEEDS RESEARCH]

### Performance Tests

21. **Benchmark 1080p**: Measure frame time with default parameters; should be < 5ms for 60fps.
22. **Texture sample count**: Use GPU profiling to verify ~5 texture samples per pixel.

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass (80% coverage minimum)
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT038: Datamosh3DEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

This spec is derived from the following legacy implementations:

- [`core/effects/datamosh_3d.py`](home/happy/Desktop/claude projects/VJlive-2/core/effects/datamosh_3d.py:1) (VJlive Original) — Full implementation with shader code (lines 6-64) and class (lines 67-166).
- [`plugins/vdatamosh/datamosh_3d.py`](home/happy/Desktop/claude projects/VJlive-2/plugins/vdatamosh/datamosh_3d.py:1) (VJlive-2 Legacy) — Likely similar or same implementation in plugin form.
- [`core/core_plugins/examples/run_depth_demo.py`](home/happy/Desktop/claude projects/VJlive-2/core/core_plugins/examples/run_depth_demo.py:1) — Example usage demonstrating how to set up the effect with synthetic inputs.

The legacy code validates the parameter ranges, default values, and core algorithm described in this spec. The effect is a lightweight depth-driven datamosh that creates pixel smearing via optical flow simulation and feedback.

---

## Open Questions / [NEEDS RESEARCH]

- **Flow scaling factor**: The shader multiplies depth gradient by `50.0`. This seems excessively large for UV coordinates. With `flow_strength=10` (strength=1.0) and a depth gradient of 0.1, flow = 5.0 UV — 5 times the texture size. This would cause extreme wrap/clamp artifacts. Is this intended? Should the offset be in pixel coordinates? Or should the scaling be smaller (e.g., 0.5)? [NEEDS RESEARCH — verify with legacy demo]
- **Depth gradient offset**: The finite difference uses a fixed 0.01 UV offset. Is this appropriate for all resolutions? Should it be resolution-dependent? [NEEDS RESEARCH]
- **Audio reactivity**: The skeleton may have included `audio_mappings`, but the actual implementation lacks it. Should this effect be audio-reactive? If so, which parameters map to which audio features? [NEEDS RESEARCH]
- **Presets**: The effect has no presets. Should we define a set (e.g., "subtle_flow", "heavy_smear", "chaotic", "edge_refresh")? [NEEDS RESEARCH]
- **Parameter `u_mix`**: The class includes `u_mix` in parameters and ranges, but the custom shader does not use it. It is likely used by the base `Effect` class to blend the effect output with the original input. Is this correct? Should `u_mix` be exposed to users? [NEEDS RESEARCH]
- **Render method**: The `render` method returns `tex_in` and binds depth manually. This suggests the effect may need `manual_render=True` to work correctly in an `EffectChain`. The legacy code does not set `manual_render`. How does the base class handle this? [NEEDS RESEARCH]
- **Sweet spots**: The `_sweet_spots` dict provides recommended values but the effect has no preset system to apply them. Should presets be added? [NEEDS RESEARCH]
- **Depth map channel**: The shader samples `texDepth.r` only. Should we support other channels or combinations? [NEEDS RESEARCH]

---

*— desktop-roo, 2026-03-03*