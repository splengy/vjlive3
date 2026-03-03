# Spec: P1-R4 — Texture Pool (Pooled, Leak-Free)

**Phase:** Phase 1 / P1-R4
**Tier:** 🖥️ Pro-Tier Native — `TexturePool` directly wraps `wgpu.GPUTexture` Python objects. Browser tier uses `GPUTexture` objects natively but with different lifecycle management (no Python pooling layer).
**Assigned To:** TBD
**Spec Written By:** Antigravity (Manager Agent) — revised 2026-03-03
**Date:** 2026-03-03
**Source:** `vjlive/core/effects/shader_base.py` → `Framebuffer.__init__()` (lines 492–516), `EffectChain.upload_texture()` (line 194)

---

## What This Module Does

Implements a pooled, leak-free GPU texture manager for VJLive3. Instead of allocating and destroying `wgpu.GPUTexture` objects every frame (which causes GPU memory fragmentation and GC pressure), the pool keeps a set of reusable textures bucketed by `(width, height, format)`.

Two classes:

1. **`TexturePool`** — Core pool. `acquire(width, height, format)` returns a `PooledTexture` wrapper. `release()` returns the texture to the pool for reuse. Pool has a configurable max size per bucket; excess textures are destroyed.
2. **`PooledTexture`** — RAII wrapper around a `wgpu.GPUTexture`. Use as a context manager: exits automatically return the texture to the pool.

---

## What This Module Does NOT Do

- Does NOT use `moderngl.Texture`, `moderngl.Buffer`, or any OpenGL resource. **WebGPU (`wgpu.GPUTexture`) only.**
- Does NOT manage render targets or pipelines (P1-R2)
- Does NOT manage the shader cache (P1-R3)
- Does NOT handle texture upload from numpy arrays directly — that is `EffectChain.upload_texture()` in P1-R2, which calls into this pool

---

## Public Interface

```python
# src/vjlive3/render/texture_pool.py
from typing import Optional
import wgpu

class PooledTexture:
    """RAII wrapper. Return to pool via .release() or context manager exit."""

    def __init__(self, texture: wgpu.GPUTexture, pool: "TexturePool") -> None: ...

    def release(self) -> None:
        """Return texture to pool. Safe to call multiple times."""

    def __enter__(self) -> "PooledTexture": ...
    def __exit__(self, *_) -> None: ...  # calls release()
    def __del__(self) -> None: ...       # calls release() if not already released

    # Read-only
    texture: wgpu.GPUTexture
    width:   int
    height:  int
    format:  wgpu.TextureFormat


class TexturePool:
    """Bucketed GPU texture pool keyed by (width, height, format)."""

    def __init__(
        self,
        device: wgpu.GPUDevice,
        max_per_bucket: int = 4,
    ) -> None:
        """
        Args:
            device:          Active wgpu device.
            max_per_bucket:  Max idle textures kept per (w, h, fmt) bucket.
                             Excess are destroyed immediately on release.
        """

    def acquire(
        self,
        width: int,
        height: int,
        format: wgpu.TextureFormat = wgpu.TextureFormat.rgba8unorm,
        usage: int = wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING,
    ) -> PooledTexture:
        """Return a pooled texture matching dimensions and format.

        Reuses an idle texture if available, otherwise allocates a new one.

        Raises:
            RuntimeError: If texture allocation fails.
        """

    def release(self, texture: PooledTexture) -> None:
        """Return texture to pool. Called by PooledTexture.release()."""

    def clear(self) -> None:
        """Destroy all pooled textures. Call on shutdown."""

    @property
    def stats(self) -> dict:
        """Return {'buckets': int, 'idle_total': int, 'allocated_total': int}."""
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `device` | `wgpu.GPUDevice` | Active device from P1-R1 `RenderContext` | Must be valid |
| `width`, `height` | `int` | Texture dimensions | 1–4096 |
| `format` | `wgpu.TextureFormat` | Pixel format | Default `rgba8unorm` |
| `usage` | `int` | WebGPU usage flags | Default: `RENDER_ATTACHMENT | TEXTURE_BINDING` |
| `max_per_bucket` | `int` | Max idle textures per bucket | Default 4 |
| **output** | `PooledTexture` | RAII wrapper with `.texture` access | Valid until `.release()` |

---

## Edge Cases and Error Handling

| Scenario | Required Behaviour |
|----------|--------------------|
| `acquire()` with no idle texture | Allocate new `wgpu.GPUTexture`; log `DEBUG` |
| `release()` on full bucket | Destroy texture immediately; log `DEBUG` |
| `acquire()` after `clear()` | Allocates fresh texture; no error |
| Double `release()` on same `PooledTexture` | Silent no-op; sets internal flag |
| `wgpu` allocation failure | Raises `RuntimeError` with message |
| `max_per_bucket = 0` | Valid — pool always destroys on release (no-pool mode) |

---

## Dependencies

- **wgpu-py** — `wgpu.GPUDevice`, `wgpu.GPUTexture`, `wgpu.TextureFormat`, `wgpu.TextureUsage`
- **threading** — `RLock` protecting bucket dict during concurrent render threads
- **logging** — pool stats and allocation events at `DEBUG` level

---

## File Layout

```
src/vjlive3/render/
    texture_pool.py    — TexturePool + PooledTexture  (~140 lines)
```

---

## Test Plan

| Test | File | What It Verifies |
|------|------|-----------------|
| `test_pool_acquire_new` | `test_texture_pool.py` | First acquire creates texture |
| `test_pool_acquire_reuse` | `test_texture_pool.py` | Acquire → release → acquire returns same texture object |
| `test_pool_different_dims` | `test_texture_pool.py` | Different (w, h) → different bucket, different texture |
| `test_pool_bucket_overflow` | `test_texture_pool.py` | Release beyond max_per_bucket destroys texture |
| `test_pool_context_manager` | `test_texture_pool.py` | `with pool.acquire(...)` auto-releases on exit |
| `test_pool_double_release` | `test_texture_pool.py` | Second `.release()` is a no-op |
| `test_pool_clear` | `test_texture_pool.py` | `clear()` empties all buckets, stats = 0 |
| `test_pool_stats` | `test_texture_pool.py` | `stats` returns correct counts |
| `test_pool_thread_safety` | `test_texture_pool.py` | Concurrent acquire/release from 4 threads, no crash |

**Minimum coverage:** 80%

> Note: All GPU tests require a wgpu device. Use `VJ_HEADLESS=true` for CI.

---

## Definition of Done

- [ ] Spec reviewed and approved
- [ ] All 9 tests pass
- [ ] `texture_pool.py` under 140 lines
- [ ] Zero stubs
- [ ] No `moderngl` imports anywhere in file
- [ ] `grep -n "moderngl" src/vjlive3/render/texture_pool.py` returns nothing
- [ ] Git commit: `[Phase-1] P1-R4: Texture pool (wgpu, pooled, leak-free, thread-safe)`
- [ ] BOARD.md P1-R4 marked ✅
- [ ] Lock released from LOCKS.md

---

## LEGACY CODE REFERENCES

**`vjlive/core/effects/shader_base.py` — `Framebuffer.__init__()` (lines 492–516):**

The legacy code creates a new FBO + texture every time. No pooling. This is what caused memory pressure in long vjlive sessions. VJLive3 must not repeat this.

The new pool replaces the pattern:
```python
# OLD (vjlive): allocate every time
self.fbo = glGenFramebuffers(1)
self.texture = glGenTextures(1)

# NEW (VJLive3): acquire from pool
tex = pool.acquire(width, height)
# use tex.texture
# tex.release()  — or use as context manager
```
