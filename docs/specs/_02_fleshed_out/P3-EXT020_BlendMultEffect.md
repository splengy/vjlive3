# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT020_BlendMultEffect.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT020 — BlendMultEffect

**Phase:** Phase 3 / P3-EXT020
**Assigned To:** Desktop Roo Worker
**Spec Written By:** Desktop Roo Worker
**Date:** 2026-03-01

---

## What This Module Does

BlendMultEffect implements a multiply/screen blend mode that combines two video streams (current frame `tex0` and previous frame `texPrev`) using either multiplicative blending or screen blending. The effect supports channel masking (RGB or luma), gamma correction, spatial offset of the blend source, and an invert flag that toggles between multiply and screen modes. All parameters use a 0.0-10.0 normalized range from UI sliders, which are internally remapped to appropriate shader values. The effect integrates into the VJLive3 effect chain system, receiving textures from the chain and outputting a blended result with optional mix control for smooth transitions.

---

## What It Does NOT Do

- Does NOT perform additive blending (use [`BlendAddEffect`](../vjlive/core/effects/blend.py:249) for that)
- Does NOT implement difference blending (use [`BlendDiffEffect`](../vjlive/core/effects/blend.py:457))
- Does NOT handle feedback loops with temporal accumulation (use [`FeedbackEffect`](../vjlive/core/effects/blend.py:151) for trails)
- Does NOT support HDR or wide-gamut color spaces beyond standard sRGB
- Does NOT perform alpha premultiplication or advanced compositing operations
- Does NOT include audio reactivity (no `set_audio_analyzer` method)
- Does NOT support 3D textures or cubemaps
- Does NOT implement custom blend equations beyond multiply/screen

---

## Detailed Behavior and Parameter Interactions

### Effect Overview

BlendMultEffect operates as a two-input blend operation within an effect chain. The primary input (`tex0`) is the current frame from the chain. The secondary input (`texPrev`) is the previous frame buffer, automatically provided by the [`EffectChain`](../vjlive/core/effects/shader_base.py:854) for all effects that need it. The effect samples both textures at the same UV coordinate (optionally offset for `texPrev`), applies channel masking to select which color channels participate, performs the blend operation, applies gamma correction, and outputs a result that is mixed with the original input based on the `u_mix` uniform controlled by the effect's `mix` parameter.

### Parameter Semantics

All parameters are normalized to the 0.0-10.0 range from the UI. The shader internally remaps them:

- **`amount`** (default: 10.0): Blend strength between current and multiplied result. Remapped to `amt = amount / 10.0` (0.0-1.0). At 0.0, output equals input; at 10.0, full blend effect.
- **`channel_mask`** (default: 0.0): Selects which channels of `texPrev` participate in the blend. Remapped to `cm = channel_mask / 10.0 * 4.0` (0.0-4.0). The shader uses range checks:
  - `0.0-0.5`: All channels (no masking)
  - `1.5-2.5`: Green only (`vec3(0.0, 1.0, 0.0)`)
  - `2.5-3.5`: Blue only (`vec3(0.0, 0.0, 1.0)`)
  - `>3.5`: Luma (grayscale) using `dot(b_col, vec3(0.299, 0.587, 0.114))`
- **`gamma`** (default: 5.0): Gamma correction applied to the blended result. Remapped to `gm = 0.5 + gamma / 10.0 * 2.5` (0.5-3.0). The final color is raised to `pow(result, 1.0/gm)`. A gamma of 0.5 gives brighter results; 3.0 gives darker, higher-contrast results.
- **`offset_x`** and **`offset_y`** (default: 5.0 each): Spatial offset applied to `texPrev` sampling. Remapped to `off = vec2((offset_x / 10.0 - 0.5) * 0.4, (offset_y / 10.0 - 0.5) * 0.4)`. This produces offsets in the range [-0.2, 0.2] in UV space, allowing subtle misalignment for chromatic or ghosting effects.
- **`invert_b`** (default: 0.0): Boolean-like flag (0.0-10.0 range) that inverts the `texPrev` color before blending. Remapped to `inv = invert_b / 10.0` (0.0-1.0). When `inv < 0.5`, the blend is pure multiply: `result = a.rgb * b_col`. When `inv > 0.5`, `b_col` is inverted (`1.0 - b_col`) and the final result is inverted (`1.0 - mult`) to complete the screen blend formula: `screen = 1 - (1-a)*(1-b)`.

### Blend Mathematics

The core blend operation proceeds in these steps:

1. **Sample inputs**: `a = texture(tex0, uv)`, `b = texture(texPrev, uv + off)`
2. **Apply channel mask** to `b` to produce `b_col`:
   - If masking, zero out unwanted channels or replace with luma
3. **Mix with amount**: `mult = a.rgb * mix(vec3(1.0), b_col, amt)`
   - When `amt=0`, result is `a.rgb` (no blend)
   - When `amt=1`, result is `a.rgb * b_col` (full multiply)
4. **Gamma correction**: `mult = pow(max(mult, vec3(0.0)), vec3(1.0 / gm))`
   - Prevents negative values, applies power function to each channel
5. **Screen completion** (if `inv > 0.5`): `mult = 1.0 - mult`
6. **Alpha composition**: `blended = vec4(clamp(mult, 0.0, 1.0), max(a.a, b.a))`
7. **Final mix**: `fragColor = mix(a, blended, u_mix)`

The `u_mix` uniform comes from the effect's `mix` attribute (0.0-1.0), allowing the effect to be crossfaded in the chain.

### Presets

Three built-in presets demonstrate typical parameter configurations:

- **`darken`**: `{"amount": 10.0, "channel_mask": 0.0, "gamma": 5.0, "offset_x": 5.0, "offset_y": 5.0, "invert_b": 0.0}` — Pure multiply blend, darkens image by overlaying previous frame.
- **`screen`**: `{"amount": 10.0, "channel_mask": 0.0, "gamma": 5.0, "offset_x": 5.0, "offset_y": 5.0, "invert_b": 10.0}` — Screen blend mode, lightens image (inverse of multiply).
- **`soft_mult`**: `{"amount": 5.0, "channel_mask": 0.0, "gamma": 7.0, "offset_x": 5.0, "offset_y": 5.0, "invert_b": 0.0}` — Gentler multiply with higher gamma for contrast control.

### Integration with EffectChain

When added to an [`EffectChain`](../vjlive/core/effects/shader_base.py:854), the BlendMultEffect participates in the ping-pong framebuffer rendering loop. The chain automatically:

- Binds `tex0` to texture unit 0 (current input)
- Binds `texPrev` to texture unit 1 (previous frame from `fbo_prev`)
- Sets standard uniforms: `time`, `resolution`, `u_mix` (from effect's `mix`)
- Sets effect-specific uniforms from `self.parameters` dictionary
- Renders a fullscreen quad with the effect's shader
- Swaps framebuffers and copies current to previous after the chain

The effect does **not** need to manage framebuffers or texture binding; the [`EffectChain.render()`](../vjlive/core/effects/shader_base.py:1062) method handles all OpenGL state.

---

## Public Interface

### Class: `BlendMultEffect`

Inherits from: [`Effect`](../vjlive/core/effects/shader_base.py:538)

#### Constructor

```python
def __init__(self) -> None:
    """Initialize BlendMultEffect with default parameters and shader."""
```

**Behavior:**
- Calls `super().__init__("blend_mult", BLEND_MULT_FRAGMENT)`
- Initializes `self.parameters` dictionary with 6 default values
- Sets `self.effect_tags = ["blend", "multiply", "screen", "composite"]`
- Sets `self.effect_category = "blend"`
- Defines `self._parameter_groups` for UI organization:
  - `"blend"`: `["amount", "gamma", "invert_b"]`
  - `"mask"`: `["channel_mask"]`
  - `"offset"`: `["offset_x", "offset_y"]`
- Defines `self._chaos_rating` (0.0-1.0 scale) for each parameter indicating visual impact:
  - `amount: 0.2`, `channel_mask: 0.3`, `gamma: 0.3`, `offset_x: 0.3`, `offset_y: 0.3`, `invert_b: 0.3`

#### Inherited Methods (from `Effect`)

The BlendMultEffect relies entirely on the base class implementation; it does **not** override any methods.

- **`set_parameter(name: str, value: float)`** — Set a parameter with validation and clamping to defined ranges. See [`Effect.set_parameter()`](../vjlive/core/effects/shader_base.py:567).
- **`get_parameter(name: str, default: float = 0.0) -> float`** — Retrieve parameter value with fallback. See [`Effect.get_parameter()`](../vjlive/core/effects/shader_base.py:613).
- **`apply_uniforms(time: float, resolution: Tuple[int, int], audio_reactor=None, semantic_layer=None)`** — Apply all parameters as shader uniforms. See [`Effect.apply_uniforms()`](../vjlive/core/effects/shader_base.py:686).
- **`reload_fragment(fragment_source: str)`** — Hot-reload the fragment shader (used in development). See [`Effect.reload_fragment()`](../vjlive/core/effects/shader_base.py:596).
- **`get_parameter_info() -> Dict[str, Dict]`** — Return metadata about all parameters (value, range, type). See [`Effect.get_parameter_info()`](../vjlive/core/effects/shader_base.py:779).
- **`validate_parameters() -> Dict[str, List[str]]`** — Validate all parameters against ranges and types. See [`Effect.validate_parameters()`](../vjlive/core/effects/shader_base.py:790).
- **`reset_parameters()`** — Reset to defaults (not typically used as defaults are set in `__init__`). See [`Effect.reset_parameters()`](../vjlive/core/effects/shader_base.py:821).
- **`copy_parameters(other_effect: Effect)`** — Copy parameters from another effect instance. See [`Effect.copy_parameters()`](../vjlive/core/effects/shader_base.py:841).

#### Class Attributes

- **`PRESETS: Dict[str, Dict[str, float]]`** — Three preset configurations: `"darken"`, `"screen"`, `"soft_mult"`. Each preset is a dictionary mapping parameter names to their preset values (all within 0.0-10.0 range).
- **`BLEND_MULT_FRAGMENT: str`** — The GLSL fragment shader source code (see below for full text).

#### Module-Level Constant

```python
BLENDS = {
    "blend_mult": BlendMultEffect,
    # ... other blend effects
}
```

This registry in [`blend.py`](../vjlive/core/effects/blend.py:1462) allows the effect system to discover and instantiate BlendMultEffect by name.

### GLSL Fragment Shader Interface

The shader expects these uniforms (all set by the Python wrapper):

| Uniform Name | Type | Description |
|--------------|------|-------------|
| `tex0` | `sampler2D` | Current frame input (bound to unit 0) |
| `texPrev` | `sampler2D` | Previous frame input (bound to unit 1) |
| `time` | `float` | Elapsed time in seconds |
| `resolution` | `vec2` | Viewport resolution in pixels |
| `u_mix` | `float` | Effect blend amount (0.0 = bypass, 1.0 = full effect) |
| `amount` | `float` | Blend strength (0.0-1.0 after remapping) |
| `channel_mask` | `float` | Channel selection mask (0.0-4.0 after remapping) |
| `gamma` | `float` | Gamma correction factor (0.5-3.0 after remapping) |
| `offset_x` | `float` | UV offset X for `texPrev` (-0.2 to 0.2 after remapping) |
| `offset_y` | `float` | UV offset Y for `texPrev` (-0.2 to 0.2 after remapping) |
| `invert_b` | `float` | Invert flag (0.0 or 1.0 after remapping) |

---

## Inputs and Outputs

### EffectChain Integration

| Aspect | Details |
|--------|---------|
| **Input Texture** | `tex0`: `sampler2D`, bound to texture unit 0, format `GL_RGBA`/`GL_RGB` (typically 8-bit unsigned byte or 32-bit float) |
| **Secondary Texture** | `texPrev`: `sampler2D`, bound to texture unit 1, same format as input, contains previous frame output |
| **Uniforms** | See "GLSL Fragment Shader Interface" above. All floats except `tex0`, `texPrev`, `resolution` |
| **Resolution** | `vec2(width, height)` in pixels, must match framebuffer size |
| **Time** | `float` seconds, monotonically increasing from chain start |
| **Mix Control** | `u_mix` from effect's `mix` attribute (0.0-1.0) |
| **Output** | `fragColor`: `vec4` RGBA, written to framebuffer, values clamped to [0.0, 1.0] |

### Parameter Ranges (UI → Shader)

| Parameter | UI Range | Shader Range | Remapping Formula | Default (UI) |
|-----------|----------|--------------|-------------------|--------------|
| `amount` | 0.0-10.0 | 0.0-1.0 | `amount / 10.0` | 10.0 |
| `channel_mask` | 0.0-10.0 | 0.0-4.0 | `channel_mask / 10.0 * 4.0` | 0.0 |
| `gamma` | 0.0-10.0 | 0.5-3.0 | `0.5 + gamma / 10.0 * 2.5` | 5.0 |
| `offset_x` | 0.0-10.0 | -0.2 to 0.2 | `(offset_x / 10.0 - 0.5) * 0.4` | 5.0 |
| `offset_y` | 0.0-10.0 | -0.2 to 0.2 | `(offset_y / 10.0 - 0.5) * 0.4` | 5.0 |
| `invert_b` | 0.0-10.0 | 0.0 or 1.0 | `invert_b / 10.0` (thresholded at >0.5) | 0.0 |

---

## Edge Cases and Error Handling

### Shader Compilation Failures

If the GLSL shader fails to compile or link, the [`Effect`](../vjlive/core/effects/shader_base.py:538) base class constructor catches the exception and logs an error. The effect instance will have `self.shader = None` if compilation fails. The [`EffectChain.render()`](../vjlive/core/effects/shader_base.py:1062) method checks for enabled effects and will skip rendering if `effect.shader` is None, falling back to passthrough. No crash, but the effect is silently disabled.

**Mitigation**: The shader code is static and pre-validated; runtime failures should be rare unless OpenGL context is lost.

### Parameter Validation

The base [`Effect.set_parameter()`](../vjlive/core/effects/shader_base.py:567) method validates:
- Parameter name is non-empty string
- Value is numeric (int/float/numpy numeric)
- Value is clamped to `_parameter_ranges` if defined

BlendMultEffect does not define custom ranges in `_init_parameter_ranges()`, so it inherits the base defaults. However, the shader expects values in specific ranges after remapping. The UI layer should constrain sliders to 0.0-10.0. If out-of-range values are set programmatically, they will be passed as-is to the shader, which may produce unexpected results (e.g., negative gamma, huge offsets). **No additional validation** is performed at the effect level.

### Texture Binding Issues

If `texPrev` is not bound (e.g., first frame or chain misconfiguration), the shader will sample from texture unit 1 which may contain undefined data. The effect does not check for texture completeness. The [`EffectChain`](../vjlive/core/effects/shader_base.py:854) always binds `fbo_prev` to unit 1, so this is only an issue if the effect is used outside a properly initialized chain.

### Division by Zero

The shader contains no divisions by parameters that could be zero. The gamma power function uses `max(mult, vec3(0.0))` to avoid negative bases, and the exponent `1.0/gm` is safe because `gm` is always ≥0.5. No NaN/Inf generation expected.

### Channel Mask Ambiguity

The channel mask uses range checks with hard-coded boundaries (0.5, 1.5, 2.5, 3.5). If a user sets `channel_mask` to exactly 1.5, it falls in the gap between R-only and G-only; the shader's `if-else` chain will skip the first two conditions and fall through to the next, eventually hitting the luma case if `cm > 3.5`. This creates non-linear transitions. The UI should snap sliders to avoid exact boundary values, or the shader could use `floor(cm)` for discrete selection. This is a **known design quirk** inherited from the legacy implementation.

### Gamma Correction Artifacts

Gamma values near 0.5 can cause `pow()` to produce very bright results that may clip to 1.0. Values above 3.0 produce very dark results. The remapping formula ensures `gm` stays in [0.5, 3.0], but extreme values still cause visual artifacts. No error is raised; this is a creative control.

### Offset Wrapping

The `texPrev` UV offset is added to the base UV without wrapping checks. If `offset` pushes UV outside [0,1], the texture sampler's wrap mode (typically `GL_CLAMP_TO_EDGE`) determines the result. This is expected behavior.

### Performance Edge Cases

- **Large resolutions**: The shader does two texture fetches per pixel (`tex0`, `texPrev`) and minimal arithmetic. Memory bandwidth is the limiting factor, not compute.
- **Blending with `u_mix=0`**: The shader still executes all operations but returns `a` at the end. The [`EffectChain`](../vjlive/core/effects/shader_base.py:1062) could optimize by skipping effects with `mix=0`, but currently only skips if `enabled and mix > 0` (line 1081). So `mix=0` still renders. This is a **performance bug** in the chain, not in this effect.
- **Channel mask branching**: The `if-else` chain for channel masking is evaluated per-pixel. Modern GPUs handle this efficiently, but extreme divergence within a warp could cause slowdown. Not a practical concern for fullscreen quads.

---

## Mathematical Formulations

### Parameter Remapping

All UI parameters `p_ui ∈ [0, 10]` are remapped in the shader:

```glsl
float amt = amount / 10.0;                              // [0, 1]
float cm = channel_mask / 10.0 * 4.0;                   // [0, 4]
float gm = 0.5 + gamma / 10.0 * 2.5;                    // [0.5, 3.0]
vec2 off = vec2((offset_x / 10.0 - 0.5) * 0.4,
                (offset_y / 10.0 - 0.5) * 0.4);        // [-0.2, 0.2] each
float inv = invert_b / 10.0;                            // [0, 1]
```

### Blend Operation

Let:
- `a = texture(tex0, uv)` — current frame color (RGBA)
- `b = texture(texPrev, uv + off)` — previous frame color (RGBA)
- `b_col = b.rgb` after optional channel masking

**Channel masking** (applied to `b.rgb`):

```glsl
if (cm > 0.5 && cm < 1.5) b_col *= vec3(1.0, 0.0, 0.0);  // R only
else if (cm > 1.5 && cm < 2.5) b_col *= vec3(0.0, 1.0, 0.0);  // G only
else if (cm > 2.5 && cm < 3.5) b_col *= vec3(0.0, 0.0, 1.0);  // B only
else if (cm > 3.5) {
    float l = dot(b_col, vec3(0.299, 0.587, 0.114));
    b_col = vec3(l);  // luma
}
```

**Multiply blend**:

```glsl
vec3 mult = a.rgb * mix(vec3(1.0), b_col, amt);
```

This is equivalent to: `result = a * (b_col * amt + (1-amt) * 1.0) = a * (1 - amt + amt * b_col)`

**Gamma correction** (applied to multiply result):

```glsl
mult = pow(max(mult, vec3(0.0)), vec3(1.0 / gm));
```

**Screen blend completion** (if `inv > 0.5`):

```glsl
if (inv > 0.5) mult = 1.0 - mult;
```

The screen blend formula is: `screen = 1 - (1-a)*(1-b)`. The code achieves this by inverting `b` before multiply (`b_col = 1 - b_col`), computing `a * (1-b)`, then inverting the result. This is algebraically equivalent to the standard screen formula.

**Alpha handling**: `max(a.a, b.a)` preserves the maximum alpha of the two inputs (no blending of alpha).

**Final mix with effect strength**:

```glsl
vec4 blended = vec4(clamp(mult, 0.0, 1.0), max(a.a, b.a));
fragColor = mix(a, blended, u_mix);
```

### Color Space Assumptions

All operations assume linear RGB color space. The input textures are expected to be linear; if they are sRGB-encoded, the blend results will be incorrect (too dark). The effect does **not** perform sRGB-to-linear conversion or linear-to-sRGB encoding. This is consistent with the legacy VJLive architecture where color space management is handled upstream/downstream.

### Luma Calculation

The luma mask uses the Rec. 709 weights: `vec3(0.299, 0.587, 0.114)`. This is standard for SD/HD video. No gamma correction is applied to the luma calculation; it operates on the raw linear RGB values.

---

## Performance Characteristics

### Computational Complexity

- **Texture fetches**: 2 per pixel (`tex0`, `texPrev`)
- **Arithmetic operations**: ~30 FLOPs per pixel (mix, dot, pow, branch)
- **Branches**: 1-4 channel mask checks (divergent but cheap)
- **No loops**: Single-pass fragment shader

### Memory Bandwidth

At 1920×1080 @ 60fps:
- Input texture read: 1920 × 1080 × 4 bytes = ~8.3 MB per frame
- Previous frame read: same = ~8.3 MB
- Output write: ~8.3 MB
- **Total**: ~24.9 MB/frame × 60 fps = **1.5 GB/s** bandwidth

This is the dominant cost; the arithmetic is negligible on modern GPUs.

### Framebuffer Usage

The effect does **not** allocate its own framebuffers. It uses the [`EffectChain`](../vjlive/core/effects/shader_base.py:854)'s ping-pong buffers (`fbo_a`, `fbo_b`) and the previous-frame buffer (`fbo_prev`). Memory overhead is 3 full-resolution framebuffers (RGBA8 or RGBA32F depending on chain configuration).

### Latency

- **One-frame delay**: The use of `texPrev` introduces exactly one frame of latency. The output at time `t` depends on the input at `t-1`.
- **No additional latency** beyond the chain's inherent ping-pong.

### Optimization Opportunities

- The channel mask could be moved to a uniform `vec3 mask` instead of branching, but the current approach is likely faster due to early rejection.
- The `invert_b` flag duplicates the screen blend formula; a separate shader variant could avoid the branch, but the cost is negligible.
- Gamma correction uses `pow()` which is expensive (~30-50 cycles). Could be approximated with a lookup texture or polynomial if profiling shows it as bottleneck.

### Comparison to Other Blend Effects

- **BlendAddEffect**: Similar structure but uses additive blending (`a + b * amt`). Slightly cheaper (no gamma, no invert).
- **BlendDiffEffect**: Uses absolute difference and thresholding; similar cost.
- **FeedbackEffect**: Much more expensive due to blur loop (5×5), hue/saturation conversions, noise functions.

BlendMultEffect is **low to medium** computational cost, suitable for real-time 60fps on integrated GPUs at 1080p.

---

## Test Plan

### Unit Tests (Effect Class)

| Test Name | What It Verifies |
|-----------|------------------|
| `test_blendmult_creation` | Effect instantiates without error, name is "blend_mult" |
| `test_blendmult_default_parameters` | All 6 parameters exist with correct default values (amount=10.0, channel_mask=0.0, gamma=5.0, offset_x=5.0, offset_y=5.0, invert_b=0.0) |
| `test_blendmult_parameter_setting` | `set_parameter()` accepts valid floats and clamps to reasonable ranges (base class behavior) |
| `test_blendmult_parameter_validation` | `validate_parameters()` returns valid list for all parameters |
| `test_blendmult_presets_exist` | Three presets (`darken`, `screen`, `soft_mult`) are defined with correct parameter keys |
| `test_blendmult_preset_values` | Preset values are within 0.0-10.0 range and produce expected remapped shader values |
| `test_blendmult_chaos_rating` | `_chaos_rating` dict exists with 6 entries, all values in [0,1] |
| `test_blendmult_parameter_groups` | `_parameter_groups` has keys "blend", "mask", "offset" with correct parameter lists |
| `test_blendmult_effect_tags` | Tags include "blend", "multiply", "screen", "composite" |
| `test_blendmult_effect_category` | Category is "blend" |

### Shader Compilation Tests

| Test Name | What It Verifies |
|-----------|------------------|
| `test_blendmult_shader_compiles` | GLSL fragment shader compiles and links without errors (requires OpenGL context) |
| `test_blendmult_shader_has_uniforms` | All expected uniforms (`tex0`, `texPrev`, `time`, `resolution`, `u_mix`, `amount`, `channel_mask`, `gamma`, `offset_x`, `offset_y`, `invert_b`) are found in the program |
| `test_blendmult_shader_no_errors` | `glGetShaderiv` and `glGetProgramiv` report no compilation/linking errors |

### Rendering Tests (Integration with EffectChain)

| Test Name | What It Verifies |
|-----------|------------------|
| `test_blendmult_chain_render` | Effect renders without crashing when added to an EffectChain and chain.render() is called |
| `test_blendmult_output_texture` | Render produces a valid texture ID (non-zero) |
| `test_blendmult_mix_zero_bypass` | With `mix=0`, output equals input (effect bypassed) |
| `test_blendmult_mix_one_full` | With `mix=1`, output is fully blended (verify by comparing to known input patterns) |
| `test_blendmult_amount_variation` | Varying `amount` from 0 to 10 produces monotonic change in output brightness (multiply darkens) |
| `test_blendmult_screen_mode` | Setting `invert_b=10` produces screen blend (lighter output than input) |
| `test_blendmult_channel_mask_red` | With `channel_mask=3.0` (R-only), only red channel of `texPrev` affects result |
| `test_blendmult_channel_mask_green` | With `channel_mask=5.0` (G-only), only green channel affects |
| `test_blendmult_channel_mask_blue` | With `channel_mask=7.0` (B-only), only blue channel affects |
| `test_blendmult_channel_mask_luma` | With `channel_mask=10.0` (luma), blend uses grayscale version of `texPrev` |
| `test_blendmult_gamma_dark` | High gamma (10.0) produces darker, higher-contrast result |
| `test_blendmult_gamma_light` | Low gamma (0.0) produces brighter, lower-contrast result |
| `test_blendmult_offset_xy` | Non-zero offsets shift the `texPrev` sampling position, creating a misalignment effect |
| `test_blendmult_previous_frame_used` | Verify that `texPrev` actually contains the previous frame by rendering two frames with different inputs and checking temporal correlation |

### Preset Tests

| Test Name | What It Verifies |
|-----------|------------------|
| `test_blendmult_preset_darken` | Preset "darken" has `invert_b=0` and produces darker output than input |
| `test_blendmult_preset_screen` | Preset "screen" has `invert_b=10` and produces lighter output than input |
| `test_blendmult_preset_soft_mult` | Preset "soft_mult" has `amount=5.0` (half strength) and `gamma=7.0` |

### Edge Case Tests

| Test Name | What It Verifies |
|-----------|------------------|
| `test_blendmult_extreme_offsets` | Offsets at UI extremes (0 or 10) produce UV shifts of ±0.2 and do not crash |
| `test_blendmult_zero_previous` | If `texPrev` is all zeros, multiply produces black where `amt>0` |
| `test_blendmult_white_previous` | If `texPrev` is all ones, multiply preserves input (multiply by 1) |
| `test_blendmult_black_input` | If `tex0` is all zeros, output is black regardless of `texPrev` |
| `test_blendmult_high_contrast_pattern` | Checkerboard pattern input produces expected alternating bright/dark regions |
| `test_blendmult_parameter_type_coercion` | Setting parameter with integer value works (auto-converted to float) |
| `test_blendmult_negative_ui_bypass` | If UI sends negative value (bug), shader receives negative and clamps internally; verify no crash |

### Regression Tests

| Test Name | What It Verifies |
|-----------|------------------|
| `test_blendmult_vs_legacy_reference` | Render output matches a pre-rendered reference image from the legacy vjlive implementation (pixel-perfect or within epsilon) |
| `test_blendmult_preset_consistency` | Loading and saving preset parameters produces identical shader output |

### Performance Tests

| Test Name | What It Verifies |
|-----------|------------------|
| `test_blendmult_render_time_1080p` | Single effect render time < 2ms on reference GPU (60fps budget = 16.6ms total for all effects) |
| `test_blendmult_no_allocation` | Repeated renders do not leak OpenGL objects (textures, framebuffers) — verify with `glGet` counters or memory profiling |

**Minimum coverage**: 80% of lines in `BlendMultEffect` class and the `BLEND_MULT_FRAGMENT` shader (branch coverage). The base `Effect` class is covered by other effect tests.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT020: BlendMultEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES

### Full BlendMultEffect Class (v1 Implementation)

From [`../vjlive/core/effects/blend.py`](../vjlive/core/effects/blend.py:373-402):

```python
class BlendMultEffect(Effect):
    """Multiply/screen blend with channel mask, gamma, offset."""

    PRESETS = {
        "darken": {"amount": 10.0, "channel_mask": 0.0, "gamma": 5.0, "offset_x": 5.0, "offset_y": 5.0, "invert_b": 0.0},
        "screen": {"amount": 10.0, "channel_mask": 0.0, "gamma": 5.0, "offset_x": 5.0, "offset_y": 5.0, "invert_b": 10.0},
        "soft_mult": {"amount": 5.0, "channel_mask": 0.0, "gamma": 7.0, "offset_x": 5.0, "offset_y": 5.0, "invert_b": 0.0},
    }

    def __init__(self):
        super().__init__("blend_mult", BLEND_MULT_FRAGMENT)
        self.parameters = {
            "amount": 10.0,
            "channel_mask": 0.0,
            "gamma": 5.0,
            "offset_x": 5.0,
            "offset_y": 5.0,
            "invert_b": 0.0,
        }
        self.effect_tags = ["blend", "multiply", "screen", "composite"]
        self.effect_category = "blend"
        self._parameter_groups = {
            "blend": ["amount", "gamma", "invert_b"],
            "mask": ["channel_mask"],
            "offset": ["offset_x", "offset_y"],
        }
        self._chaos_rating = {
            "amount": 0.2, "channel_mask": 0.3, "gamma": 0.3,
            "offset_x": 0.3, "offset_y": 0.3, "invert_b": 0.3,
        }
```

### Full GLSL Fragment Shader

From [`../vjlive/core/effects/blend.py`](../vjlive/core/effects/blend.py:319-370):

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

uniform float amount;       // 0-10 → 0-1 blend strength
uniform float channel_mask; // 0-10 → 0=all, 3=R, 5=G, 7=B, 10=luma
uniform float gamma;        // 0-10 → 0.5-3.0 gamma curve on result
uniform float offset_x;     // 0-10 → -0.2 to 0.2 offset blend source
uniform float offset_y;     // 0-10 → -0.2 to 0.2
uniform float invert_b;     // 0-10 → 0-1 invert B before multiply (screen mode)

void main() {
    vec4 a = texture(tex0, uv);
    float amt = amount / 10.0;
    float cm = channel_mask / 10.0 * 4.0;
    float gm = 0.5 + gamma / 10.0 * 2.5;
    vec2 off = vec2((offset_x / 10.0 - 0.5) * 0.4, (offset_y / 10.0 - 0.5) * 0.4);
    float inv = invert_b / 10.0;

    vec4 b = texture(texPrev, uv + off);

    // Optionally invert B (screen blend = 1 - (1-a)*(1-b))
    vec3 b_col = mix(b.rgb, 1.0 - b.rgb, inv);

    // Channel mask
    if (cm > 0.5 && cm < 1.5) b_col *= vec3(1.0, 0.0, 0.0);  // R only
    else if (cm > 1.5 && cm < 2.5) b_col *= vec3(0.0, 1.0, 0.0);  // G only
    else if (cm > 2.5 && cm < 3.5) b_col *= vec3(0.0, 0.0, 1.0);  // B only
    else if (cm > 3.5) {
        float l = dot(b_col, vec3(0.299, 0.587, 0.114));
        b_col = vec3(l);
    }

    vec3 mult = a.rgb * mix(vec3(1.0), b_col, amt);

    // Gamma correction
    mult = pow(max(mult, vec3(0.0)), vec3(1.0 / gm));

    // If inverted, complete the screen blend
    if (inv > 0.5) mult = 1.0 - mult;

    vec4 blended = vec4(clamp(mult, 0.0, 1.0), max(a.a, b.a));
    fragColor = mix(a, blended, u_mix);
}
```

### Base Effect Class Reference

The [`Effect`](../vjlive/core/effects/shader_base.py:538) base class provides:

- **Shader management**: Compilation, uniform caching, hot-reload via `reload_fragment()`
- **Parameter handling**: Type-safe storage, validation, range enforcement via `set_parameter()`
- **Uniform application**: `apply_uniforms()` sets all parameters as shader uniforms, optionally with audio modulation
- **Integration with EffectChain**: The chain's `render()` method calls `effect.shader.use()`, sets uniforms, binds textures, and draws the fullscreen quad

Key methods that BlendMultEffect inherits (no overrides needed):

```python
class Effect:
    def __init__(self, name: str, fragment_source: str, vertex_source: Optional[str] = None): ...
    def set_parameter(self, name: str, value: float): ...
    def get_parameter(self, name: str, default: float = 0.0) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None, semantic_layer=None): ...
    def reload_fragment(self, fragment_source: str): ...
    def get_parameter_info(self) -> Dict[str, Dict[str, Any]]: ...
    def validate_parameters(self) -> Dict[str, List[str]]: ...
    def reset_parameters(self): ...
    def copy_parameters(self, other_effect: 'Effect'): ...
```

### EffectChain Rendering Loop (Context)

From [`../vjlive/core/effects/shader_base.py`](../vjlive/core/effects/shader_base.py:1062-1195), the relevant uniforms are set as:

```python
# Inside EffectChain.render():
effect.shader.use()
effect.shader.set_uniform("u_view_offset", self.view_offset)
effect.shader.set_uniform("u_view_scale", self.view_scale)
effect.apply_uniforms(current_time, resolution, audio_reactor, semantic_layer)

# Bind input textures
glActiveTexture(GL_TEXTURE0)
if pre_tex:
    glBindTexture(GL_TEXTURE_2D, pre_tex)
else:
    if use_input:
        glBindTexture(GL_TEXTURE_2D, input_texture)
    else:
        read_fbo.bind_texture(0)
effect.shader.set_uniform("tex0", 0)

# Bind extra textures (if any)
if extra_textures:
    for j, tex_id in enumerate(extra_textures):
        unit = j + 2
        glActiveTexture(GL_TEXTURE0 + unit)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        effect.shader.set_uniform(f"tex{j+1}", unit)

# Bind previous frame
glActiveTexture(GL_TEXTURE1)
self.fbo_prev.bind_texture(1)
effect.shader.set_uniform("texPrev", 1)

# Draw fullscreen quad
glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
```

BlendMultEffect expects `texPrev` on unit 1, which the chain provides automatically.

---
