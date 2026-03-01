````markdown
# P5-DM17: LayerSeparationEffect (datamosh_3d - layers mode)
> **Task ID:** `P5-DM17`
> **Priority:** P0 (Critical)
> **Source:** Ported behavior from legacy `Datamosh3DEffect` (mode="layers")
> **Class:** `LayerSeparationEffect` (convenience subclass of `Datamosh3DEffect`)
> **Phase:** Phase 5
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete, unambiguous Pass 2 specification for the `LayerSeparationEffect` variant
of the legacy `Datamosh3DEffect`. In the legacy code this is the `mode = 1` configuration of
`Datamosh3DEffect` (see `mode_names = ['displacement','layers','echo','shatter']`). The
objective is a precise plugin spec that reproduces the legacy "layers" visual behavior,
documents exact shader uniforms and remaps, supplies a CPU fallback, tests, and presets.

## Technical Requirements
- Implement as a VJLive3 plugin and register under `datamosh` family
- Follow the canonical spec template and match visual behavior of legacy "layers" mode
- Maintain 60 FPS at 1080p on a reasonable GPU (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines where feasible (Safety Rail 4)
- No silent failures; graceful GPU fallback to CPU path (Safety Rail 7)

## Implementation Notes / Porting Strategy
1. Reuse the legacy `DATAMOSH_3D_FRAGMENT` fragment shader as the authoritative
   source for uniform names, math intent, and feedback loop structure.
2. Implement `LayerSeparationEffect` as a tiny subclass (or factory) that sets
   `mode = 1` and exposes the same tunable uniforms to the UI.
3. Add light documentation for layer-specific UX-friendly parameters (see Public Interface).
4. Provide a deterministic NumPy CPU fallback that implements the same per-pixel math
   (depth bucketing → displacement → feedback accumulation) for testing and headless runs.
5. Include automated visual regression tests that assert per-pixel difference bounds
   against recorded golden frames from the legacy version.

## Public Interface
```python
class LayerSeparationEffect(Datamosh3DEffect):
    """Convenience wrapper which sets `mode = 1` (layers) on Datamosh3DEffect.

    UI-facing controls are intentionally normalized to 0.0—10.0 and remapped by
    the plugin to the precise internal ranges used by the shader.
    """

    def __init__(self, width: int = 1920, height: int = 1080):
        super().__init__(width, height)
        self.parameters['mode'] = 1  # fixed for this convenience class

        # Expose the same named parameters as Datamosh3DEffect, plus layer-count
        self.parameters.update({
            'flow_strength': 5.0,
            'depth_threshold': 2.0,
            'decay': 9.0,
            'noise_amount': 1.0,
            'u_mix': 10.0,
            'layer_count': 4.0,
            'layer_spacing': 2.0
        })

    # render() and apply_uniforms() are inherited from Datamosh3DEffect and
    # will bind the correct `mode` and computed uniforms for the shader.
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `flow_strength` (float, UI 0—10) → internal `F` = map_linear(x, 0,10, 0.0, 32.0)
  - Controls magnitude of depth-driven displacement vectors; typical sweet spot: 2—6
- `depth_threshold` (float, UI 0—10) → internal `T` = map_linear(x, 0,10, 0.0, 4.0)
  - Depth edge sensitivity: larger values ignore small depth variation
- `decay` (float, UI 0—10) → internal `D` = map_exp(x, 0,10, 0.0, 0.995)
  - Feedback persistence. Remap uses exponential curve so 10 → ~0.995 (long persistence)
- `noise_amount` (float, UI 0—10) → internal `N` = map_linear(x, 0,10, 0.0, 1.0)
  - Adds stochastic perturbation to flow vectors
- `u_mix` (float, UI 0—10) → internal `M` = map_linear(x, 0,10, 0.0, 1.0)
  - Final blend of fresh sample vs feedback buffer
- `layer_count` (float, UI 0—10) → `L` = clamp(round(map_linear(x,0,10,1,16)), 1, 32)
  - Number of discrete depth layers to produce; maps to integer buckets
- `layer_spacing` (float, UI 0—10) → `S` = map_linear(x,0,10, 0.0, 8.0)
  - Per-layer pixel offset multiplier (in pixels when combined with `F`)

Notes on remap functions used above:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`
- `map_exp(v,a,b,c,d)` applies a smooth exponential curve chosen so UX feels
  logarithmic (implementation detail in apply_uniforms())

## Shader uniforms (authoritative names from legacy fragment)
- `uniform float flow_strength;`
- `uniform float depth_threshold;`
- `uniform float decay;`
- `uniform float noise_amount;`
- `uniform float u_mix;`
- `uniform int mode;`  // will be 1 for LayerSeparationEffect
- `uniform int layer_count;`  // supplied via apply_uniforms()
- `uniform float layer_spacing;`

## Effect Math (concise, shader/CPU-consistent description)
All math below is deliberately written so it can be implemented identically in
GLSL (fragment shader) and NumPy (CPU fallback).

1) Depth bucketing (discrete layers):

   Let z(x,y) be normalized depth in [0,1] sampled from `texDepth`.
   Compute integer depth bucket index b(x,y) = floor(z * L).
   Layer center depth for bucket b: z_b = (b + 0.5) / L.

2) Local depth gradient / flow vector:

   Compute gradient g = ∇z(x,y) = (dz/dx, dz/dy) using central differences.
   Deterministic noise vector n = hash_vec2(x,y, seed) scaled by `noise_amount`.
   Raw flow v = normalize(g + n) * F.

3) Layer displacement:

   Compute discrete layer offset O = b * S (in normalized pixel units scaled by resolution)
   Pixel sample coordinate for a layer: uv' = uv + v * (1.0 + O)
   Sample color_c = texture(input, uv') for each pixel's layer bucket b.

4) Feedback accumulation and decay:

   Let accum be the persistent feedback buffer. New accum is computed per-frame:
   accum_new = decay * accum_old + (1.0 - decay) * color_c
   Final color_out = mix(color_c, accum_new, M)

5) Depth threshold gating (edge refresh):

   If |g| < T then treat pixel as "flat" and reduce displacement to avoid smearing.
   This uses smoothstep around `depth_threshold` to avoid discontinuities.

These steps are implemented in the fragment shader as a single-pass computation
that selects the proper layer and blends with the feedback buffer. The CPU
fallback implements the same steps on NumPy arrays in row-major order.

## CPU Fallback (NumPy sketch)
- Accepts `frame` (H,W,3) and `depth` (H,W) arrays.
- Compute `b = floor(depth * L)` and `z_b` as above.
- Compute central-difference gradients via convolutions with [[-0.5, 0, 0.5]]
- Compute `v`, offset `uv'`, and sample with bilinear interpolation (scipy.ndimage.map_coordinates
  or custom bilinear sampler) to produce `color_c`.
- Maintain `accum` buffer as float32 array; update with exponential decay.

## Presets (recommended)
- `Subtle Layers`:
  - `flow_strength` 2.0, `layer_count` 3, `layer_spacing` 1.0, `decay` 7.5, `u_mix` 8.0
- `Deep Slices`:
  - `flow_strength` 6.0, `layer_count` 8, `layer_spacing` 3.0, `decay` 9.6, `u_mix` 9.6
- `Noisy Cut`:
  - `flow_strength` 4.0, `noise_amount` 6.0, `layer_count` 6, `layer_spacing` 2.0, `decay` 6.0

## Edge Cases and Error Handling
- If `texDepth` is missing, fall back to luminance-based proxy depth computed
  via `Y = 0.2126 R + 0.7152 G + 0.0722 B`. Emit a warning in logs.
- Enforce `layer_count >= 1` and clamp to a reasonable maximum (32).
- Clamp remapped uniforms to safe ranges before uploading to GPU.
- If GPU shader compile fails, fall back to CPU path and continue running.

## Test Plan (minimum)
- `test_layer_bucket_consistency` — verify integer bucket assignment is stable across identical depth frames
- `test_flow_vector_bounds` — ensure `|v| <= F_max + epsilon` after remap
- `test_feedback_decay` — validate exponential decay behavior of accum buffer
- `test_preset_visual_regressions` — per-preset golden-frame comparison (pixel-diff threshold)
- `test_missing_depth_fallback` — ensure luminance proxy path runs and produces output without crashing
- `test_performance_1080p_60fps` — smoke perf test (may be marked xfail on CI machines without GPU)

## Verification Checkpoints
- [ ] `LayerSeparationEffect` class exists and registers with plugin registry
- [ ] Shader uniforms match names listed above and are bound in `apply_uniforms()`
- [ ] CPU fallback produces visually comparable frames (within tolerance)
- [ ] Presets render and match golden-frame thresholds
- [ ] Tests pass and coverage ≥ 80%

## Implementation Handoff Notes
- This spec assumes `Datamosh3DEffect` supplies the low-level shader and feedback
  loop infrastructure; `LayerSeparationEffect` only fixes `mode = 1` and exposes
  additional UX-friendly parameters documented above.
- Reference legacy fragment name: `DATAMOSH_3D_FRAGMENT` (use this as a porting anchor)

## Resources
- Legacy source fragment: `DATAMOSH_3D_FRAGMENT` in backup (extracted earlier)
- Related fleshed spec (reference): [docs/specs/_02_fleshed_out/P5-P5-DM16_datamosh_3d.md](docs/specs/_02_fleshed_out/P5-P5-DM16_datamosh_3d.md)

````
