# Spec: P1-R1 — Agnostic Render Context

**Phase:** Phase 1 / P1-R1
**Tier:** 🖥️ Pro-Tier Native — `RenderContext` wraps GLFW + wgpu surface. Desktop only. Requires a browser-equivalent spec (WebGPU canvas bootstrap) before bifurcated pipeline is complete.
**Assigned To:** TBD
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-21
**Source:** `VJlive-2/core/window.py` & `VJlive-2/core/gl_wrapper.py`

---

## What This Module Does

Implements the root renderer context creation and Window management for VJLive3. It replaces `VJlive-2/core/window.py` and PyOpenGL dependency by providing:

1. **`RenderContext`** — A RAII-style context manager that creates a visible window via GLFW, initializes a `wgpu` surface and adapter, and handles system-level window events (polling, buffer swapping).
2. **Headless Mode** — Graceful fallback for cloud/CI environments. If `VJ_HEADLESS=true` is set (or requested via constructor), it bypasses window creation and requests a `wgpu` adapter without a surface for offscreen rendering.

All GPU resources in VJLive3 rely exclusively on **WebGPU/WGSL via `wgpu-py`**. No OpenGL or ModernGL calls exist anywhere in VJLive3.

---

## What It Does NOT Do

- Does NOT render any effects or geometry (that is P1-R2 and P1-R5)
- Does NOT compile shaders (P1-R3)
- Does NOT drive the 60 FPS main loop or calculate delta time (Engine logic handles that)
- Does NOT handle application state, nodes, or plugins
- Does NOT manage textures beyond exposing the `wgpu.GPUDevice` reference

---

## Public Interface

### `RenderContext`

```python
import wgpu

class RenderContext:
    """
    RAII-managed render context and Window provider.
    Handles window initialization and backend context attachment.
    """

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        title: str = "VJLive 3.0 :: The Reckoning",
        headless: bool = False
    ) -> None:
        """Initialize the Window and OpenGL context.

        Args:
            width, height: Dimensions of the window (ignored in headless).
            title: Title of the window.
            headless: If True (or if VJ_HEADLESS env var is 'true'), create a standalone context without a visible window.

        Raises:
            RuntimeError: If window fails to initialize or backend context creation fails.
        """

    def make_current(self) -> None:
        """Make the context current for the calling thread. No-op in headless mode."""

    def poll_events(self) -> None:
        """Process pending GLFW window events. No-op in headless mode."""

    def should_close(self) -> bool:
        """Check if the user has requested to close the window. Returns False in headless mode."""

    def swap_buffers(self) -> None:
        """Swap front and back buffers. No-op in headless mode."""

    def terminate(self) -> None:
        """Destroy the window, release the context, and terminate subsystems. Safe to call multiple times."""

    def __enter__(self) -> "RenderContext": ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...  # calls terminate()
    def __del__(self) -> None: ...  # calls terminate()

    # Read-only properties
    width: int
    height: int
    headless: bool
    ctx: wgpu.GPUCanvasContext  # The active generic provider instance
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `width`, `height` | `int` | Window / render resolution | 1–4096. Fixed size (non-resizable). |
| `title` | `str` | Window title bar text | |
| `headless` | `bool` | Bypass window creation | Driven by param OR `VJ_HEADLESS=true` env var |
| **output** | `RenderContext` | Context manager instance | Must be held for the lifetime of the Engine |
| `ctx` | `BackendContext` | Abstract API object | Passed to all render pipelines (e.g., P1-R2) |

---

## Edge Cases and Error Handling

| Scenario | Required Behaviour |
|----------|--------------------|
| GLFW fails to init | Logs `CRITICAL`, raises `RuntimeError` |
| `VJ_HEADLESS=true` | Skips GLFW completely; requests `wgpu.gpu.request_adapter()` without a surface for offscreen compute |
| `make_current()` when headless | Silent no-op, prevents crashes when calling window functions |
| `terminate()` called twice | No-op, no double-free. Sets `self.ctx = None` |
| Multiple instances | Only one window/context is supported per process. Additional creations should raise `RuntimeError` if GLFW doesn't allow it cleanly, or terminate previous. |

---

## Dependencies

- **wgpu-py** — WebGPU rendering API. Required. No fallback.
- **glfw** — Window creation and event loop. Required for windowed mode; skipped in headless.
- **logging** — Standard library logger.

## File Layout

```
src/vjlive3/render/
    render_context.py      — RenderContext class implementation (~150 lines)
```

---

## Test Plan

| Test | File | What It Verifies |
|------|------|-----------------|
| `test_context_create_window` | `test_render_context.py` | Instantiating context creates window and `ctx` is valid backend |
| `test_context_headless_override` | `test_render_context.py` | `headless=True` bypasses window, `ctx` is standalone |
| `test_context_env_headless` | `test_render_context.py` | `VJ_HEADLESS=true` env var forces headless |
| `test_context_manager_lifecycle` | `test_render_context.py` | `with RenderContext(...)` cleans up resources on exit |
| `test_context_double_terminate` | `test_render_context.py` | Calling `terminate()` twice doesn't crash |
| `test_window_methods_headless` | `test_render_context.py` | `swap_buffers()`, `poll_events()`, `make_current()` do not crash in headless mode |

**Minimum coverage:** 90% before task is marked done.

> Note: Window-creation tests require a real display or Xvfb (`DISPLAY=:99 Xvfb :99 &`).

## Definition of Done

- [ ] Spec reviewed and approved (Manager or User)
- [ ] All 6 tests above pass
- [ ] No file over 750 lines
- [ ] Zero stubs
- [ ] Git commit: `[Phase-1] P1-R1: WebGPU rendering context (wgpu-py + GLFW)`
- [ ] BOARD.md P1-R1 marked ✅
- [ ] Lock released from LOCKS.md
