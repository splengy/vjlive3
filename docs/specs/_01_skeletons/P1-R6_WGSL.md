# Spec: P1-R6 — WGSL Shader Library (Base Embedded Shaders)

**Phase:** Phase 1 / P1-R6
**Assigned To:** TBD
**Spec Written By:** Antigravity (Manager Agent) — revised 2026-03-03
**Date:** 2026-03-03
**Source:** `vjlive/core/effects/shader_base.py` (BASE_VERTEX_SHADER, PASSTHROUGH_FRAGMENT, WARP_VERTEX_SHADER, WARP_BLEND_FRAGMENT)

---

## What This Module Does

Provides the canonical embedded WGSL shader strings used by the VJLive3 render pipeline. These are not user-authored effects — they are the infrastructure shaders that `P1-R2` (`RenderPipeline`, `EffectChain`) depends on for fullscreen quad rendering, passthrough blitting, and multi-node edge blending.

This module is a **pure constant library**: no classes, no runtime logic, just WGSL source strings and one validation helper.

The five base shaders are:

| Constant | Purpose |
|----------|---------|
| `BASE_VERTEX_WGSL` | Fullscreen quad vertex shader. Outputs `uv` (global, 0–1) and `v_uv` (local, 0–1) for multi-node stitching via `u_ViewOffset`, `u_ViewResolution`, `u_TotalResolution` uniforms. |
| `PASSTHROUGH_FRAGMENT_WGSL` | Identity — samples `tex0` at `v_uv`. Used as the no-op effect stage. |
| `OVERLAY_FRAGMENT_WGSL` | Copies overlay texture into the render target at full alpha. |
| `WARP_VERTEX_WGSL` | 4-point corner-pin or 5×5 Bézier mesh warp via `warp_mode` uniform (0 = none, 1 = corner, 2 = bezier). |
| `WARP_BLEND_FRAGMENT_WGSL` | Edge feathering for multi-projector overlap blending. Optional calibration grid overlay via `calibrationMode` uniform. |

---

## What This Module Does NOT Do

- Does NOT compile or cache shaders (that is `P1-R2 RenderPipeline`)
- Does NOT implement user-authored effects (those are in `P1-EXT*` and `P3-VD*`)
- Does NOT include GLSL. All shaders are WGSL only.
- Does NOT have runtime logic — purely constants + `validate_wgsl(source: str) -> bool`

---

## Public Interface

```python
# src/vjlive3/render/shaders.py

BASE_VERTEX_WGSL: str          # fullscreen quad + global UVs
PASSTHROUGH_FRAGMENT_WGSL: str  # identity blit
OVERLAY_FRAGMENT_WGSL: str      # overlay copy
WARP_VERTEX_WGSL: str           # corner-pin / bezier warp
WARP_BLEND_FRAGMENT_WGSL: str   # edge feather + calibration grid

def validate_wgsl(source: str) -> bool:
    """
    Returns True if source is non-empty and contains required WGSL entry point markers.
    Does NOT invoke the GPU compiler — lightweight pre-submission check only.
    Logs WARNING and returns False on failure.
    """
```

---

## Inputs and Outputs

These are WGSL string constants. Inputs and outputs are expressed in terms of shader interface:

**`BASE_VERTEX_WGSL` uniforms (bind group 0):**

| Uniform | Type | Description |
|---------|------|-------------|
| `u_ViewOffset` | `vec2<f32>` | Pixel offset of this node on the global canvas |
| `u_ViewResolution` | `vec2<f32>` | Resolution of this node (e.g., 1920×1080) |
| `u_TotalResolution` | `vec2<f32>` | Total canvas resolution (e.g., 5760×1080 for 3-node) |

**`WARP_BLEND_FRAGMENT_WGSL` uniforms:**

| Uniform | Type | Description |
|---------|------|-------------|
| `edgeFeather` | `f32` | Blend width as fraction of screen (0.0–1.0) |
| `nodeSide` | `i32` | 0 = left, 1 = middle, 2 = right |
| `calibrationMode` | `u32` | 1 = show calibration grid, 0 = normal |

---

## Edge Cases and Error Handling

| Scenario | Required Behaviour |
|----------|-------------------|
| `validate_wgsl("")` | Returns `False`, logs `WARNING` |
| `u_TotalResolution` = (0, 0) | Shader falls back to `u_ViewResolution` to avoid division by zero (handled in shader source) |
| `warp_mode` out of range | Shader treats as 0 (no warp) |

---

## Dependencies

- None. This module contains only string constants and a pure-Python validation helper.
- Used by: `P1-R2` (`RenderPipeline`, `EffectChain`), `P1-R5` (render loop passthrough), any effect that needs the base vertex shader.

---

## File Layout

```
src/vjlive3/render/
    shaders.py    — All five WGSL constants + validate_wgsl()  (~180 lines)
```

---

## Test Plan

| Test | File | What It Verifies |
|------|------|-----------------|
| `test_base_vertex_is_wgsl` | `test_shaders.py` | `BASE_VERTEX_WGSL` contains `@vertex` entry point |
| `test_passthrough_is_wgsl` | `test_shaders.py` | `PASSTHROUGH_FRAGMENT_WGSL` contains `@fragment` entry point |
| `test_overlay_is_wgsl` | `test_shaders.py` | `OVERLAY_FRAGMENT_WGSL` contains `@fragment` entry point |
| `test_warp_vertex_is_wgsl` | `test_shaders.py` | `WARP_VERTEX_WGSL` contains `@vertex` entry point |
| `test_warp_blend_is_wgsl` | `test_shaders.py` | `WARP_BLEND_FRAGMENT_WGSL` contains `@fragment` entry point |
| `test_validate_wgsl_empty` | `test_shaders.py` | `validate_wgsl("")` returns `False` |
| `test_validate_wgsl_valid` | `test_shaders.py` | `validate_wgsl(BASE_VERTEX_WGSL)` returns `True` |
| `test_no_glsl_keywords` | `test_shaders.py` | None of the constants contain `#version`, `gl_Position`, or `uniform` (GLSL-style) |

**Minimum coverage:** 90% (pure constants — tests are trivial)

> Note: These tests are CPU-only. No GPU context required.

---

## Definition of Done

- [ ] Spec reviewed and approved (Manager or User)
- [ ] All 8 tests above pass
- [ ] No GLSL keywords in any WGSL string (`grep -n "#version\|gl_Position" src/vjlive3/render/shaders.py` returns nothing)
- [ ] `shaders.py` under 200 lines
- [ ] Zero stubs
- [ ] Git commit: `[Phase-1] P1-R6: WGSL base shader library (vertex, passthrough, warp, blend)`
- [ ] BOARD.md P1-R6 marked ✅
- [ ] Lock released from LOCKS.md

---

## LEGACY CODE REFERENCES

**Source:** `vjlive/core/effects/shader_base.py`

The legacy shaders are GLSL 330. They must be rewritten as WGSL. Key translation notes:
- `#version 330 core` → removed (WGSL has no version directive)
- `in vec2 uv` → `@location(0) uv: vec2<f32>` in vertex output struct
- `uniform sampler2D tex0` → `@group(0) @binding(0) var tex0: texture_2d<f32>` + separate sampler binding
- `texture(tex0, uv)` → `textureSample(tex0, tex0_sampler, uv)`
- `gl_Position` → `@builtin(position) pos: vec4<f32>` in vertex output struct
- `vec2/vec3/vec4` → `vec2<f32>/vec3<f32>/vec4<f32>`
- `float` → `f32`
- `int` → `i32`
- `bool` → `bool` (same)
- `fract/mix/clamp/smoothstep/length/abs/sin/cos/step` → same names in WGSL
