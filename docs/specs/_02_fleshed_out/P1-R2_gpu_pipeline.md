# Spec: P1-R2 — GPU Pipeline + RenderTarget Management (Resource Pooling)

**Phase:** Phase 1 / P1-R2
**Assigned To:** TBD (awaiting DISPATCH.md entry)
**Spec Written By:** Antigravity (Manager Agent)
**Date:** 2026-02-21
**Source:** `VJlive-2/core/shaders/` (chain.py · framebuffer.py · program.py)

---

## What This Module Does

Implements the VJLive3 GPU rendering pipeline as a collection of RAII-safe renderer-agnostic components (defaulting to wgpu/WebGPU). It provides:

1. **`RenderTarget`** — an RGBA offscreen render target (abstract texture/view attachment) with context-manager lifecycle
2. **`RenderPipeline`** — a WGSL shader pipeline with cached bind groups and optional security validation
3. **`EffectChain`** — a ping-pong render target effect pipeline that accepts an input texture view, runs zero or more `Effect` objects in order, and returns the output texture view; also provides async mapped buffer readback and projection mapping post-processing

All three classes must be leak-free: GPU resources (texture views, buffers, bind groups, pipelines) must be deleted when the object is destroyed, even if exceptions occurred.

---

## What It Does NOT Do

- Does NOT compile user-authored shaders or Milkdrop presets (that is P1-R3)
- Does NOT manage a texture pool or atlas (that is P1-R4)
- Does NOT drive the 60 FPS render loop (that is P1-R5)
- Does NOT provide audio analysis or reactivity (P1-A*)
- Does NOT implement `Effect` subclasses — only the base `Effect` interface lives here
- Does NOT handle window management or RenderContext creation (P1-R1)
- Does NOT implement the spatial stitching business logic — only passes `view_offset` / `view_scale` uniforms to shaders

---

## Public Interface

### `RenderTarget`

```python
from typing import Any, Optional, List, Tuple, Dict

class RenderTarget:
    """RGBA offscreen render target. RAII lifecycle via context manager."""

    def __init__(self, width: int, height: int) -> None:
        """Create texture view attachment.

        Args:
            width, height: Dimensions in pixels.

        Raises:
            RuntimeError: If render target is not complete after construction.
        """

    def bind(self, encoder: Any) -> None:
        """Bind for rendering via active command encoder."""

    def unbind(self, encoder: Any) -> None:
        """Unbind from command encoder."""

    def delete(self) -> None:
        """Delete abstract texture view. Safe to call multiple times."""

    def __enter__(self) -> "RenderTarget": ...
    def __exit__(self, *_) -> None: ...  # calls delete()
    def __del__(self) -> None: ...       # calls delete()

    # Read-only properties
    width:   int
    height:  int
    texture: Any  # Abstract backend texture view
```

### `RenderPipeline`

```python
class RenderPipeline:
    """Compiled WGSL shader pipeline with cached bind groups."""

    def __init__(
        self,
        shader_source: str,
        name: str = "unnamed",
    ) -> None:
        """Compile and link shader. Caches all active bind groups.

        Args:
            shader_source:   WGSL shader source.
            name:            Debug name for logging.

        Raises:
            RuntimeError: Compilation failure.
        """

    def use(self, encoder: Any) -> None:
        """Set pipeline on the provided command encoder."""

    def set_uniform(self, name: str, value: object) -> None:
        """Set a uniform by Python type dispatch via mapped buffer updates."""

    def delete(self) -> None:
        """Release pipeline resources. Safe to call multiple times."""

    def __del__(self) -> None: ...  # calls delete()

    name:    str
    pipeline: Any  # Abstract backend pipeline
    uniforms: Dict[str, Any]  # uniform name → bind group cache
```

### `Effect` (base class)

```python
class Effect:
    """Base class for all VJLive3 effects. Holds shader + parameters."""

    METADATA: dict  # required — see PRIME_DIRECTIVE Rule 2

    def __init__(self, name: str, fragment_source: str) -> None: ...

    # Override in subclasses:
    def apply_uniforms(
        self,
        time: float,
        resolution: Tuple[int, int],
        audio_reactor: Any,
        semantic_layer: Any,
    ) -> None: ...

    def pre_process(self, chain: "EffectChain", input_tex: Any) -> Optional[Any]:
        """Optional pre-pass (CPU ML, etc.). Return alt texture or None."""
        ...

    # Config
    enabled:       bool    # default True
    mix:           float   # 0.0–1.0 blend weight, default 1.0
    manual_render: bool    # If True, effect calls chain internally

    pipeline: RenderPipeline
    name:     str
```

### `EffectChain`

```python
class EffectChain:
    """Ping-pong render target effect pipeline."""

    METADATA: dict  # required — PRIME_DIRECTIVE Rule 2

    def __init__(self, width: int = 1920, height: int = 1080) -> None:
        """Allocate Target-A, Target-B, Target-prev, fullscreen geometries, passthrough shader.

        Args:
            width, height: Render resolution.
        """

    # Effect management
    def add_effect(self, effect: Effect) -> None: ...
    def remove_effect(self, name: str) -> None: ...
    def get_available_effects(self) -> List[str]: ...

    # Core render
    def render(
        self,
        input_texture: Any,
        extra_textures: Optional[List[Any]] = None,
        audio_reactor: Any = None,
        semantic_layer: Any = None,
    ) -> Any:
        """Run enabled effects in order via ping-pong render targets.

        Returns:
            Texture view output (owned by internal target — copy if needed).
        """

    # CPU readback
    def readback_texture(self, texture: Any) -> Optional[np.ndarray]:
        """Synchronous map_async block. Returns H×W×3 uint8. Slow — avoid in hot path."""

    def readback_texture_async(
        self, texture: Any, fmt: str = "rgb"
    ) -> Optional[np.ndarray]:
        """Buffer mapping async readback. 1-frame latency, non-blocking. Returns H×W×3 uint8."""

    def readback_last_output(self) -> Optional[np.ndarray]:
        """Convenience: readback_texture(self._last_output_texture)."""

    # Downsampled readback (for CPU analysis / stream output)
    def create_downsampled_target(self, width: int, height: int) -> Optional[RenderTarget]: ...
    def render_to_downsampled_target(self, input_texture: Any, target: RenderTarget) -> None: ...

    # Texture upload
    def upload_texture(self, image: np.ndarray) -> Any:
        """Upload H×W×3 uint8 BGR. Returns abstract texture view."""

    def update_texture(self, texture: Any, image: np.ndarray) -> None:
        """Update existing texture. Resizes image if dimensions changed."""

    def upload_float_texture(self, image: np.ndarray) -> Any:
        """Upload H×W×{1,2,3,4} float32. Returns abstract texture view."""

    def update_float_texture(self, texture: Any, image: np.ndarray) -> None: ...

    # Spatial stitching (multi-node)
    def set_spatial_view(self, offset: List[float], scale: List[float]) -> None:
        """Set view_offset/view_scale uniforms for multi-node stitching."""

    # Projection mapping post-process
    def set_projection_mapping(
        self,
        warp_mode: int = 0,
        corners: Optional[List[float]] = None,
        bezier_mesh: Optional[List[float]] = None,
        edge_feather: float = 0.0,
        node_side: int = 1,
        calibration_mode: bool = False,
    ) -> None: ...

    # Screen output
    def render_to_screen(
        self, texture: Any, viewport: Tuple[int, int, int, int]
    ) -> None:
        """Blit texture to default view. Applies projection mapping if set."""

    # Lifecycle
    def delete(self) -> None:
        """Delete all render targets, buffers, pipelines. Safe to call multiple times."""

    def __enter__(self) -> "EffectChain": ...
    def __exit__(self, *_) -> None: ...  # calls delete()
    def __del__(self) -> None: ...       # calls delete()
```

---

## Built-in WGSL Shaders (Embedded Strings)

| Constant | Purpose |
|----------|---------|
| `BASE_VERTEX_SHADER` | WGSL Quad vertex shader. Computes global UV for multi-node stitching via `u_ViewOffset`, `u_ViewResolution`, `u_TotalResolution` uniforms. |
| `PASSTHROUGH_FRAGMENT` | WGSL Identity — samples from texture view at `v_uv`. |
| `OVERLAY_FRAGMENT` | WGSL Copy overlay texture into render target. |
| `WARP_VERTEX_SHADER` | WGSL 4-point corner-pin or 5×5 Bézier mesh warp via `warp_mode` uniform. |
| `WARP_BLEND_FRAGMENT` | WGSL Edge feathering for multi-projector overlap blending; optional calibration grid overlay. |

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `input_texture` | `Any` | Abstract texture view from source or previous effect | Must be valid when `render()` is called |
| `extra_textures` | `List[Any]` | Additional samplers (e.g., mix channels) | Optional |
| `audio_reactor` | `Any` | Audio analysis object passed to effects | Optional, duck-typed |
| `width`, `height` | `int` | Render resolution | 1–4096 |
| `fmt` | `str` | Readback format: `'rgb'` or `'rgba'` | Default `'rgb'` |
| **output (render)** | `Any` | Abstract texture view of final rendered frame | Owned by internal render target |
| **output (readback)** | `np.ndarray | None` | H×W×3 uint8 | `None` on first async frame or error |

---

## Edge Cases and Error Handling

| Scenario | Required Behaviour |
|----------|--------------------|
| No effects in chain | `render()` returns `input_texture` unchanged — no GPU draw |
| Target incomplete | `RenderTarget.__init__` raises `RuntimeError` |
| Shader compile error | `RenderPipeline.__init__` raises `RuntimeError` |
| Uniform not found | `set_uniform()` silently skips — cached only if found |
| Buffer map failure | Logs warning; async readback returns `None` for that frame |
| `delete()` after `delete()` | No-op, no double-free |
| Slow effect (> 5 ms) | Log `DEBUG` warning; do not drop or skip |
| Chain > 16 ms total | Log `DEBUG` warning — 60 FPS budget is 16.67 ms |
| Effect exception during render | Log `ERROR` and continue to next effect; never crash the loop |
| Texture dimension mismatch on update | `update_texture` resizes with `cv2.resize` to match GPU dimensions |

---

## Dependencies

### External Libraries
- **wgpu-py** — Primary WGSL / WebGPU rendering API wrapper; required.
- **numpy** (≥ 1.21) — array operations for readback, texture upload
- **cv2** (opencv-python) — used only in `update_texture` resize; soft fallback: skip resize if absent, log warning

### Internal Modules
- `vjlive3.render.render_context` (P1-R1) — active agnostic context must exist before any `RenderTarget` / `RenderPipeline` is instantiated

---

## File Layout

```
src/vjlive3/render/
    __init__.py           — re-exports
    framebuffer.py        — Framebuffer class only  (~120 lines)
    program.py            — RenderPipeline + built-in WGSL constants  (~200 lines)
    effect.py             — Effect base class  (~100 lines)
    chain.py              — EffectChain  (~420 lines; within 750-line limit)
```

> Source note: VJlive-2's `chain.py` is 849 lines and violates the 750-line rule. VJLive3 must split it exactly as shown above. `EffectChain` imports from the other three files; there are no circular dependencies.

---

## Test Plan

| Test | File | What It Verifies |
|------|------|-----------------|
| `test_render_target_create` | `test_render_target.py` | `RenderTarget(1920, 1080)` constructs without error |
| `test_render_target_bind_unbind` | `test_render_target.py` | `bind()` / `unbind()` can be called |
| `test_render_target_context_manager` | `test_render_target.py` | `with RenderTarget(…)` deletes on exit |
| `test_render_target_double_delete` | `test_render_target.py` | Second `delete()` is a no-op |
| `test_render_target_incomplete_raises` | `test_render_target.py` | Invalid dimensions raise `RuntimeError` |
| `test_pipeline_compile_passthrough` | `test_pipeline.py` | `RenderPipeline(BASE_VERTEX_SHADER)` succeeds |
| `test_pipeline_bad_shader_raises` | `test_pipeline.py` | Malformed source raises `RuntimeError` |
| `test_pipeline_bad_fragment_raises` | `test_pipeline.py` | Malformed fragment source raises `RuntimeError` |
| `test_pipeline_set_uniform_int` | `test_pipeline.py` | `set_uniform("x", 1)` dispatches successfully |
| `test_pipeline_set_uniform_float` | `test_pipeline.py` | `set_uniform("x", 1.0)` dispatches successfully |
| `test_pipeline_set_unknown_uniform` | `test_pipeline.py` | Unknown uniform name does not raise |
| `test_effect_chain_create` | `test_chain.py` | `EffectChain(1920, 1080)` allocates targets |
| `test_effect_chain_no_effects` | `test_chain.py` | `render()` with empty chain returns `input_texture` unchanged |
| `test_effect_chain_add_remove` | `test_chain.py` | `add_effect` + `remove_effect` update the list |
| `test_effect_chain_render_passthrough` | `test_chain.py` | Single passthrough effect returns output view |
| `test_effect_chain_delete` | `test_chain.py` | `delete()` releases all GPU resources without error |
| `test_effect_chain_context_manager` | `test_chain.py` | `with EffectChain():` calls `delete()` on exit |
| `test_effect_chain_readback` | `test_chain.py` | `readback_last_output()` returns H×W×3 numpy array or None |
| `test_effect_chain_upload_texture` | `test_chain.py` | `upload_texture(...)` succeeds |
| `test_spatial_view` | `test_chain.py` | `set_spatial_view([0, 0], [1, 1])` does not raise |
| `test_projection_mapping` | `test_chain.py` | `set_projection_mapping(...)` sets up shader |

**Minimum coverage:** 80% before task is marked done.

> Note: All GPU tests require a wgpu-compatible device. For headless/CI, use `VJ_HEADLESS=true` to run with an offscreen wgpu adapter. No X server required.

---

## Definition of Done

- [ ] Spec reviewed and approved (Manager or User)
- [ ] All 21 tests above pass
- [ ] No file over 750 lines (4-file split as specified)
- [ ] Zero stubs — `Logger.termination()` on all dead-end paths (ADR-003)
- [ ] `METADATA` constant on `Framebuffer`, `ShaderProgram`, `Effect`, `EffectChain`
- [ ] `render()` logs DEBUG warning when any effect exceeds 5 ms
- [ ] `render()` logs DEBUG warning when full chain exceeds 16 ms
- [ ] Sync + async readback both verified manually with `readback_last_output()`
- [ ] Git commit: `[Phase-1] P1-R2: GPU pipeline + render targets (ping-pong, async readback, RAII)`
- [ ] BOARD.md P1-R2 marked ✅
- [ ] Lock released from LOCKS.md
- [ ] AGENT_SYNC.md handoff note with FPS proof and any issues

---

## Technical Notes for Implementer

**Ping-pong pattern:**
Must implement WebGPU-compatible ping-ponging via abstract render passes and texture views.

**Async readback (zero-stall):**
Must use `wgpu` `Buffer.map_async` with a mapping callback to ensure the CPU does not block waiting for the GPU to finish reading pixels. The command encoder must dispatch `copy_texture_to_buffer`.

**Uniform type dispatch** — Must translate uniform mapping to proper WGSL bind groups and dynamic buffers.

**Renderer Agnosticism:** Must use abstract wrappers ensuring no raw ModernGL or wgpu API calls leak out of the module.

**Thread safety:** `EffectChain` uses an `RLock` around the effect list.

---

## Verification Commands

```bash
# Run unit tests (requires Xvfb or real display)
DISPLAY=:99 PYTHONPATH=src python3 -m pytest \
  tests/unit/test_framebuffer.py \
  tests/unit/test_program.py \
  tests/unit/test_chain.py \
  -v --override-ini="addopts="

# File size check
python3 scripts/check_file_size.py src/vjlive3/render/

# Stub check
python3 scripts/check_stubs.py src/vjlive3/render/

# Manual smoke test — should render 3 seconds, output "FPS: ~60"
PYTHONPATH=src python3 -c "
from vjlive3.render.render_context import RenderContext
from vjlive3.render.chain import EffectChain
import time, numpy as np

with RenderContext(1280, 720, 'P1-R2 Smoke') as backend:
    with EffectChain(1280, 720) as chain:
        dummy = np.zeros((720, 1280, 3), dtype=np.uint8)
        tex = chain.upload_texture(dummy)
        frames = 0
        start = time.time()
        while time.time() - start < 3:
            backend.poll_events()
            if backend.should_close(): break
            backend.make_current()
            out = chain.render(tex)
            chain.render_to_screen(out, (0, 0, 1280, 720))
            backend.swap_buffers()
            frames += 1
        elapsed = time.time() - start
        print(f'FPS: {frames / elapsed:.1f} (must be >=58)')
"
# Expected: FPS >= 58
```
