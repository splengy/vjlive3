# Spec: P1-R4 — Texture Manager (Pooled, RAII, Leak-Free)

**Phase:** Phase 1 / P1-R4
**Assigned To:** TBD (awaiting Manager assignment)
**Spec Written By:** Antigravity (Agent 3)
**Date:** 2026-02-21
**Source References:** `VJlive-2/core/framebuffer.py`, `VJlive-2/docs/specs/P1-R2_gpu_pipeline.md`
**Depends On:** P1-R1 (OpenGLContext)

---

## What This Module Does

Manages GPU texture objects using a pool allocation strategy. Provides RAII `Texture2D` and
`Framebuffer` handles that release GPU resources automatically when they go out of scope.
Maintains separate pools keyed by (width, height, format) so textures can be reused across
frames without re-allocation. Also manages PBO (Pixel Buffer Object) readback objects for
async CPU-side pixel capture. Enforces 60 FPS by avoiding re-allocation in the hot path.
Validates SAFETY_RAIL 8 (no resource leaks) by tracking unreleased handles.

---

## What It Does NOT Do

- Does NOT compile shaders (P1-R3)
- Does NOT run the render loop (P1-R5)
- Does NOT decode image files — callers provide raw pixel data
- Does NOT upload video frames — that is P2's VideoSource scope

---

## Public Interface

```python
# vjlive3/render/textures.py

import moderngl
import numpy as np
from typing import Optional, Tuple
from enum import Enum


class TextureFormat(str, Enum):
    RGBA8   = "rgba8"      # 8-bit RGBA (most textures)
    RGBA16F = "rgba16f"    # 16-bit float RGBA (HDR)
    RGB8    = "rgb8"       # 8-bit RGB
    R8      = "r8"         # single channel


class Texture2D:
    """
    RAII wrapper around a moderngl.Texture.
    Returned by TextureManager.acquire() — do not construct directly.
    Release via context manager or explicit .release().
    """

    @property
    def mgl(self) -> moderngl.Texture:
        """Access underlying moderngl.Texture."""

    @property
    def width(self) -> int: ...

    @property
    def height(self) -> int: ...

    @property
    def format(self) -> TextureFormat: ...

    def write(self, data: bytes) -> None:
        """Upload pixel data. data must match width*height*channels bytes."""

    def use(self, location: int = 0) -> None:
        """Bind to a texture unit."""

    def release(self) -> None:
        """Return to pool. Idempotent."""

    def __enter__(self) -> 'Texture2D': ...
    def __exit__(self, *args) -> None: ...  # calls release()


class Framebuffer:
    """
    RAII wrapper around moderngl.Framebuffer with an attached Texture2D.
    Returned by TextureManager.acquire_framebuffer().
    """

    @property
    def mgl(self) -> moderngl.Framebuffer: ...

    @property
    def color_texture(self) -> Texture2D:
        """Access the colour attachment."""

    @property
    def width(self) -> int: ...

    @property
    def height(self) -> int: ...

    def use(self) -> None:
        """Bind as render target."""

    def clear(self, r: float = 0.0, g: float = 0.0, b: float = 0.0, a: float = 0.0) -> None:
        """Clear colour attachment."""

    def release(self) -> None:
        """Return to pool. Idempotent."""

    def __enter__(self) -> 'Framebuffer': ...
    def __exit__(self, *args) -> None: ...


class PBOReadback:
    """
    RAII PBO for async pixel readback (avoids GPU stall).

    Usage:
        pbo = manager.acquire_pbo(width, height)
        pbo.trigger_readback(framebuffer)  # non-blocking
        # One frame later:
        data = pbo.get_pixels()  # returns np.ndarray or None if not ready
        pbo.release()
    """

    def trigger_readback(self, framebuffer: Framebuffer) -> None:
        """Start async readback from framebuffer (non-blocking)."""

    def get_pixels(self) -> Optional[np.ndarray]:
        """
        Return pixel data if DMA transfer complete, else None.
        Shape: (height, width, 4) dtype uint8.
        """

    def release(self) -> None: ...

    def __enter__(self) -> 'PBOReadback': ...
    def __exit__(self, *args) -> None: ...


class TextureManager:
    """
    Pool-based GPU texture allocator. One instance per OpenGL context.

    Not thread-safe — must be used on the GL context thread.
    """

    def __init__(self, ctx: moderngl.Context) -> None:
        """
        Args:
            ctx: Active ModernGL context.
        """

    def acquire(
        self,
        width: int,
        height: int,
        fmt: TextureFormat = TextureFormat.RGBA8,
    ) -> Texture2D:
        """
        Get a texture of the given dimensions and format.

        Reuses a pooled texture if available, otherwise allocates a new one.
        Thread-unsafe — call from GL thread only.
        """

    def acquire_framebuffer(
        self,
        width: int,
        height: int,
        fmt: TextureFormat = TextureFormat.RGBA8,
    ) -> Framebuffer:
        """Get a framebuffer with attached colour texture from pool."""

    def acquire_pbo(self, width: int, height: int) -> PBOReadback:
        """Get a PBO for pixel readback from pool."""

    def stats(self) -> dict:
        """
        Return pool statistics for diagnostics.
        {'total_allocated': int, 'pooled': int, 'active': int, 'leaked': int}
        leaked = allocated - (pooled + active) — non-zero indicates RAIL 8 violation.
        """

    def shutdown(self) -> None:
        """Release all pooled and active textures. Logs RAIL 8 warning if leaked > 0."""
```

---

## Pool Strategy

Pool key: `(width, height, format)` → `deque[Texture2D]`.
- `acquire()`: pop from deque if non-empty, else allocate new.
- `release()`: push back to deque.
- Pool size cap: 8 textures per key (configurable). If cap exceeded, destroy instead of pool.

---

## Edge Cases and Error Handling

- **GL out-of-memory:** Caught, raises `MemoryError("GPU OOM: cannot allocate {w}x{h} texture")`.
- **Double release:** Log WARNING, skip return to pool (idempotent).
- **write() size mismatch:** Raise `ValueError("Data size mismatch: expected {expected}, got {n}")`.
- **shutdown() with leaked handles:** Log ERROR per leaked handle (RAIL 8 violation).
- **PBO get_pixels before trigger:** Return None, log WARNING.

---

## Dependencies

### External
- `moderngl >= 5.0`
- `numpy >= 1.24`

### Internal
- `vjlive3.render.context.OpenGLContext` (P1-R1)

---

## Test Plan

| Test ID | What It Verifies |
|---------|-----------------|
| `test_acquire_returns_texture2d` | acquire() returns Texture2D with correct w/h |
| `test_release_returns_to_pool` | release then acquire at same dims → same pool slot |
| `test_context_manager_releases` | `with manager.acquire(...) as t:` auto-releases |
| `test_framebuffer_acquire` | acquire_framebuffer returns Framebuffer |
| `test_framebuffer_clear_noop` | clear() does not crash |
| `test_pbo_trigger_and_get` | trigger_readback + get_pixels returns ndarray or None |
| `test_stats_active_count` | stats().active == number of unreleased handles |
| `test_stats_leaked_zero_after_release` | release all → stats().leaked == 0 |
| `test_double_release_noop` | second release() doesn't raise |
| `test_write_size_mismatch_raises` | wrong size data → ValueError |
| `test_pool_cap_destroys_over_cap` | acquire/release more than cap → no OOM |

Tests run in headless OpenGL (mesa software renderer).

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] All 11 tests pass
- [ ] File < 750 lines
- [ ] No stubs
- [ ] No resource leaks (stats().leaked == 0 in all tests)
- [ ] BOARD.md P1-R4 marked ✅
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
