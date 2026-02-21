# Spec: P1-R2 — GPU Pipeline + Framebuffer Management (RAII)

**Phase:** Phase 1 / P1-R2
**Assigned To:** TBD (awaiting DISPATCH.md entry)
**Spec Written By:** Antigravity (Manager Agent)
**Date:** 2026-02-21
**Source:** `VJlive-2/core/shaders/` (chain.py · framebuffer.py · program.py)

---

## What This Module Does

Implements the VJLive3 GPU rendering pipeline as a collection of RAII-safe ModernGL components. It provides:

1. **`Framebuffer`** — an RGBA offscreen render target (FBO + texture attachment) with context-manager lifecycle
2. **`ShaderProgram`** — a ModernGL vertex+fragment shader with cached uniform locations and optional security validation
3. **`EffectChain`** — a ping-pong framebuffer effect pipeline that accepts an input texture, runs zero or more `Effect` objects in order, and returns the output texture ID; also provides async PBO readback and projection mapping post-processing

All three classes must be leak-free: GPU resources (FBOs, textures, VAOs, PBOs) must be deleted when the object is destroyed, even if exceptions occurred.

---

## What It Does NOT Do

- Does NOT compile user-authored shaders or Milkdrop presets (that is P1-R3)
- Does NOT manage a texture pool or atlas (that is P1-R4)
- Does NOT drive the 60 FPS render loop (that is P1-R5)
- Does NOT provide audio analysis or reactivity (P1-A*)
- Does NOT implement `Effect` subclasses — only the base `Effect` interface lives here
- Does NOT handle window management or OpenGL context creation (P1-R1)
- Does NOT implement the spatial stitching business logic — only passes `view_offset` / `view_scale` uniforms to shaders

---

## Public Interface

### `Framebuffer`

```python
class Framebuffer:
    """RGBA offscreen render target. RAII lifecycle via context manager."""

    def __init__(self, width: int, height: int) -> None:
        """Create FBO + RGBA texture attachment.

        Args:
            width, height: Dimensions in pixels.

        Raises:
            RuntimeError: If framebuffer is not complete after construction.
        """

    def bind(self) -> None:
        """Bind for rendering. Sets glViewport to (0, 0, width, height)."""

    def unbind(self) -> None:
        """Bind default framebuffer (0)."""

    def bind_texture(self, unit: int = 0) -> None:
        """Bind the colour texture to the given texture unit."""

    def delete(self) -> None:
        """Delete FBO and texture. Safe to call multiple times."""

    def __enter__(self) -> "Framebuffer": ...
    def __exit__(self, *_) -> None: ...  # calls delete()
    def __del__(self) -> None: ...       # calls delete()

    # Read-only properties
    width:   int
    height:  int
    fbo:     int  # GL framebuffer object ID
    texture: int  # GL texture ID
```

### `ShaderProgram`

```python
class ShaderProgram:
    """Compiled GLSL vertex + fragment shader with cached uniform setters."""

    def __init__(
        self,
        vertex_source: str,
        fragment_source: str,
        name: str = "unnamed",
    ) -> None:
        """Compile and link shader. Caches all active uniform locations.

        Args:
            vertex_source:   GLSL 330 core vertex shader source.
            fragment_source: GLSL 330 core fragment shader source.
            name:            Debug name for logging.

        Raises:
            RuntimeError: Vertex or fragment compilation failure, or link failure.
        """

    def use(self) -> None:
        """glUseProgram(self.program)."""

    def set_uniform(self, name: str, value: object) -> None:
        """Set a uniform by Python type dispatch.

        Dispatches:
            int          → glUniform1i
            float        → glUniform1f
            bool         → glUniform1i (0/1)
            tuple[2]     → glUniform2f
            np.ndarray   → glUniform2/3/4fv or array-of-vec dispatch
        """

    def delete(self) -> None:
        """glDeleteProgram(self.program). Safe to call multiple times."""

    def __del__(self) -> None: ...  # calls delete()

    name:    str
    program: int  # GL program ID
    uniforms: Dict[str, int]  # uniform name → location cache
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

    def pre_process(self, chain: "EffectChain", input_tex: int) -> Optional[int]:
        """Optional pre-pass (CPU ML, etc.). Return alt texture or None."""
        ...

    # Config
    enabled:       bool    # default True
    mix:           float   # 0.0–1.0 blend weight, default 1.0
    manual_render: bool    # If True, effect calls chain internally

    shader: ShaderProgram
    name:   str
```

### `EffectChain`

```python
class EffectChain:
    """Ping-pong framebuffer effect pipeline."""

    METADATA: dict  # required — PRIME_DIRECTIVE Rule 2

    def __init__(self, width: int = 1920, height: int = 1080) -> None:
        """Allocate FBO-A, FBO-B, FBO-prev, fullscreen quad VAO, passthrough shader.

        Args:
            width, height: Render resolution (may differ from window size on HiDPI).
        """

    # Effect management
    def add_effect(self, effect: Effect) -> None: ...
    def remove_effect(self, name: str) -> None: ...
    def get_available_effects(self) -> List[str]: ...

    # Core render
    def render(
        self,
        input_texture: int,
        extra_textures: Optional[List[int]] = None,
        audio_reactor: Any = None,
        semantic_layer: Any = None,
    ) -> int:
        """Run enabled effects in order via ping-pong FBOs.

        Returns:
            GL texture ID of the output (owned by internal FBO — copy if needed).
        """

    # CPU readback
    def readback_texture(self, texture_id: int) -> Optional[np.ndarray]:
        """Synchronous glReadPixels. Returns H×W×3 uint8 (Y flipped). Slow — avoid in hot path."""

    def readback_texture_async(
        self, texture_id: int, fmt: str = "rgb"
    ) -> Optional[np.ndarray]:
        """PBO ping-pong async readback. 1-frame latency, non-blocking. Returns H×W×3 uint8."""

    def readback_last_output(self) -> Optional[np.ndarray]:
        """Convenience: readback_texture(self._last_output_texture)."""

    # Downsampled readback (for CPU analysis / stream output)
    def create_downsampled_fbo(self, width: int, height: int) -> Optional[Framebuffer]: ...
    def render_to_downsampled_fbo(self, input_texture: int, fbo: Framebuffer) -> None: ...

    # Texture upload
    def upload_texture(self, image: np.ndarray) -> int:
        """Upload H×W×3 uint8 BGR. Returns GL texture ID."""

    def update_texture(self, texture: int, image: np.ndarray) -> None:
        """Update existing texture. Resizes image if dimensions changed."""

    def upload_float_texture(self, image: np.ndarray) -> int:
        """Upload H×W×{1,2,3,4} float32. Returns GL texture ID."""

    def update_float_texture(self, texture: int, image: np.ndarray) -> None: ...

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
        self, texture: int, viewport: Tuple[int, int, int, int]
    ) -> None:
        """Blit texture to default framebuffer. Applies projection mapping if set."""

    # Lifecycle
    def delete(self) -> None:
        """Delete all FBOs, VAOs, PBOs, shader. Safe to call multiple times."""

    def __enter__(self) -> "EffectChain": ...
    def __exit__(self, *_) -> None: ...  # calls delete()
    def __del__(self) -> None: ...       # calls delete()
```

---

## Built-in GLSL Shaders (Embedded Strings)

| Constant | Purpose |
|----------|---------|
| `BASE_VERTEX_SHADER` | Quad vertex shader. Computes global UV for multi-node stitching via `u_ViewOffset`, `u_ViewResolution`, `u_TotalResolution` uniforms. |
| `PASSTHROUGH_FRAGMENT` | Identity — samples `tex0` at `v_uv`. |
| `OVERLAY_FRAGMENT` | Copy overlay texture into framebuffer. |
| `WARP_VERTEX_SHADER` | 4-point corner-pin or 5×5 Bézier mesh warp via `warp_mode` uniform. |
| `WARP_BLEND_FRAGMENT` | Edge feathering for multi-projector overlap blending; optional calibration grid overlay. |

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `input_texture` | `int` | GL texture ID from source or previous effect | Must be valid when `render()` is called |
| `extra_textures` | `List[int]` | Additional samplers (e.g., mix channels) | Optional, max ~14 (GL limit − 2) |
| `audio_reactor` | `Any` | Audio analysis object passed to effects | Optional, duck-typed |
| `width`, `height` | `int` | Render resolution | 1–4096 |
| `fmt` | `str` | Readback format: `'rgb'` or `'rgba'` | Default `'rgb'` |
| **output (render)** | `int` | GL texture ID of final rendered frame | Owned by internal FBO; copy if long-lived |
| **output (readback)** | `np.ndarray | None` | H×W×3 uint8, Y-flipped corrected | `None` on first async frame or error |

---

## Edge Cases and Error Handling

| Scenario | Required Behaviour |
|----------|--------------------|
| No effects in chain | `render()` returns `input_texture` unchanged — no GPU draw |
| Framebuffer incomplete | `Framebuffer.__init__` raises `RuntimeError("Framebuffer not complete")` |
| Shader compile error | `ShaderProgram.__init__` raises `RuntimeError` with GLSL info log |
| Uniform not found | `set_uniform()` silently skips — cached only if found |
| PBO map failure | Logs warning; async readback returns `None` for that frame |
| `delete()` after `delete()` | No-op, no double-free |
| Slow effect (> 5 ms) | Log `DEBUG` warning; do not drop or skip |
| Chain > 16 ms total | Log `DEBUG` warning — 60 FPS budget is 16.67 ms |
| Effect exception during render | Log `ERROR` and continue to next effect; never crash the loop |
| Texture dimension mismatch on update | `update_texture` resizes with `cv2.resize` to match GPU dimensions |

---

## Dependencies

### External Libraries
- **moderngl** (≥ 5.0) — OpenGL Python wrapper; required (no fallback)
- **numpy** (≥ 1.21) — array operations for readback, texture upload
- **cv2** (opencv-python) — used only in `update_texture` resize; soft fallback: skip resize if absent, log warning

### Internal Modules
- `vjlive3.render.opengl_context` (P1-R1) — active GL context must exist before any `Framebuffer` / `ShaderProgram` is instantiated

---

## File Layout

```
src/vjlive3/render/
    __init__.py           — re-exports
    framebuffer.py        — Framebuffer class only  (~120 lines)
    program.py            — ShaderProgram + built-in GLSL constants  (~200 lines)
    effect.py             — Effect base class  (~100 lines)
    chain.py              — EffectChain  (~420 lines; within 750-line limit)
```

> Source note: VJlive-2's `chain.py` is 849 lines and violates the 750-line rule. VJLive3 must split it exactly as shown above. `EffectChain` imports from the other three files; there are no circular dependencies.

---

## Test Plan

| Test | File | What It Verifies |
|------|------|-----------------|
| `test_framebuffer_create` | `test_framebuffer.py` | `Framebuffer(1920, 1080)` constructs without error |
| `test_framebuffer_bind_unbind` | `test_framebuffer.py` | `bind()` / `unbind()` can be called |
| `test_framebuffer_context_manager` | `test_framebuffer.py` | `with Framebuffer(…)` deletes on exit |
| `test_framebuffer_double_delete` | `test_framebuffer.py` | Second `delete()` is a no-op |
| `test_framebuffer_incomplete_raises` | `test_framebuffer.py` | Invalid dimensions raise `RuntimeError` |
| `test_shader_compile_passthrough` | `test_program.py` | `ShaderProgram(BASE_VERTEX_SHADER, PASSTHROUGH_FRAGMENT)` succeeds |
| `test_shader_bad_vertex_raises` | `test_program.py` | Malformed vertex source raises `RuntimeError` |
| `test_shader_bad_fragment_raises` | `test_program.py` | Malformed fragment source raises `RuntimeError` |
| `test_shader_set_uniform_int` | `test_program.py` | `set_uniform("x", 1)` dispatches to `glUniform1i` |
| `test_shader_set_uniform_float` | `test_program.py` | `set_uniform("x", 1.0)` dispatches to `glUniform1f` |
| `test_shader_set_unknown_uniform` | `test_program.py` | Unknown uniform name does not raise |
| `test_effect_chain_create` | `test_chain.py` | `EffectChain(1920, 1080)` allocates FBOs and quad |
| `test_effect_chain_no_effects` | `test_chain.py` | `render()` with empty chain returns `input_texture` unchanged |
| `test_effect_chain_add_remove` | `test_chain.py` | `add_effect` + `remove_effect` update the list |
| `test_effect_chain_render_passthrough` | `test_chain.py` | Single passthrough effect returns output texture ID |
| `test_effect_chain_delete` | `test_chain.py` | `delete()` releases all GPU resources without error |
| `test_effect_chain_context_manager` | `test_chain.py` | `with EffectChain():` calls `delete()` on exit |
| `test_effect_chain_readback` | `test_chain.py` | `readback_last_output()` returns H×W×3 numpy array or None |
| `test_effect_chain_upload_texture` | `test_chain.py` | `upload_texture(zeros((720, 1280, 3), uint8))` returns int > 0 |
| `test_spatial_view` | `test_chain.py` | `set_spatial_view([0, 0], [1, 1])` does not raise |
| `test_projection_mapping` | `test_chain.py` | `set_projection_mapping(warp_mode=1, corners=8×float)` sets up shader |

**Minimum coverage:** 80% before task is marked done.

> Note: All GPU tests require a real OpenGL context. Use `pytest-glfw` or run with a headless display (`Xvfb`). Headless CI: add `DISPLAY=:99 Xvfb :99 &` in CI script.

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
- [ ] Git commit: `[Phase-1] P1-R2: GPU pipeline + framebuffer (ping-pong FBO, PBO readback, RAII)`
- [ ] BOARD.md P1-R2 marked ✅
- [ ] Lock released from LOCKS.md
- [ ] AGENT_SYNC.md handoff note with FPS proof and any issues

---

## Technical Notes for Implementer

**Ping-pong pattern:**
```
fbo_a, fbo_b = Framebuffer(w, h), Framebuffer(w, h)
read_fbo, write_fbo = None, fbo_a
for effect in enabled_effects:
    write_fbo.bind()
    # draw using read_fbo.texture or input_texture
    read_fbo, write_fbo = write_fbo, (fbo_b if write_fbo is fbo_a else fbo_a)
output_tex = read_fbo.texture
```

**Async PBO readback (zero-stall):**
```python
# Frame N: trigger async read into pbo[write_idx]
glBindBuffer(GL_PIXEL_PACK_BUFFER, pbo[write_idx])
glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE, c_void_p(0))
# Frame N: map pbo[read_idx] — contains frame N-1 data
ptr = glMapBuffer(GL_PIXEL_PACK_BUFFER, GL_READ_ONLY)
ctypes.memmove(pre_allocated_buffer.ctypes.data, ptr, size)
glUnmapBuffer(GL_PIXEL_PACK_BUFFER)
```
Pre-allocate the numpy buffer on first use; reuse every frame (zero allocation in hot path).

**Uniform type dispatch** — match VJlive-2's `program.py` exactly: `int → 1i`, `float → 1f`, `bool → 1i`, `tuple[2] → 2f`, `ndarray[2] → 2fv`, `ndarray[3] → 3fv`, `ndarray[4] → 4fv`, `ndarray[2n] → array of vec2`, etc.

**ModernGL vs raw PyOpenGL:** VJlive-2 uses raw PyOpenGL (`glGenFramebuffers` etc.). VJLive3 uses **ModernGL** (per P1-R1 decision). Port the FBO/texture/VAO logic using `ctx.framebuffer()`, `ctx.texture()`, `ctx.vertex_array()` equivalents from the ModernGL API. The resulting behaviour must be identical; only the API surface changes.

**Thread safety:** `EffectChain` uses an `RLock` around the effect list. All GL calls must still happen on the render thread that owns the context.

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
from vjlive3.render.opengl_context import OpenGLContext
from vjlive3.render.chain import EffectChain
import time, numpy as np

with OpenGLContext(1280, 720, 'P1-R2 Smoke') as gl:
    with EffectChain(1280, 720) as chain:
        dummy = np.zeros((720, 1280, 3), dtype=np.uint8)
        tex = chain.upload_texture(dummy)
        frames = 0
        start = time.time()
        while time.time() - start < 3:
            gl.poll_events()
            if gl.should_close(): break
            gl.make_current()
            gl.ctx.clear(0, 0, 0, 1)
            out = chain.render(tex)
            chain.render_to_screen(out, (0, 0, 1280, 720))
            gl.swap_buffers()
            frames += 1
        elapsed = time.time() - start
        print(f'FPS: {frames / elapsed:.1f} (must be >=58)')
"
# Expected: FPS >= 58
```
