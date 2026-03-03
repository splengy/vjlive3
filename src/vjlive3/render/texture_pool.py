"""
P1-R4 — Texture Pool (Pooled, Leak-Free)
Spec: docs/specs/P1-R4_pooled, leak-free_spec.md
Tier: 🖥️ Pro-Tier Native — wraps wgpu.GPUTexture, desktop only.

Replaces the legacy per-frame FBO allocation pattern:
  OLD: glGenTextures(1) every frame → memory fragmentation after hours of use
  NEW: pool.acquire(w, h) → reuse idle texture from bucket → pool.release()
"""

import logging
import threading
from typing import TYPE_CHECKING, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Bucket key: (width, height, format_value, usage_flags)
_BucketKey = Tuple[int, int, Any, int]


class PooledTexture:
    """
    RAII wrapper around a wgpu.GPUTexture.

    Use as a context manager, or call .release() explicitly.
    Double-release is a silent no-op.
    """

    def __init__(
        self,
        texture: Any,       # wgpu.GPUTexture
        pool: "TexturePool",
        key: _BucketKey,
        width: int,
        height: int,
        fmt: Any,           # wgpu.TextureFormat value
    ) -> None:
        self._texture = texture
        self._pool = pool
        self._key = key
        self._width = width
        self._height = height
        self._fmt = fmt
        self._released: bool = False

    def release(self) -> None:
        """Return texture to the pool. Safe to call multiple times (idempotent)."""
        if self._released:
            return
        self._released = True
        self._pool.release(self)

    def __enter__(self) -> "PooledTexture":
        return self

    def __exit__(self, *_: Any) -> None:
        self.release()

    def __del__(self) -> None:
        self.release()

    # ---- Read-only properties -----------------------------------------------

    @property
    def texture(self) -> Any:
        """The underlying wgpu.GPUTexture."""
        return self._texture

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def format(self) -> Any:
        """wgpu.TextureFormat value."""
        return self._fmt


class TexturePool:
    """
    Bucketed GPU texture pool keyed by (width, height, format, usage).

    Textures are reused across frames to avoid GPU memory fragmentation.
    Thread-safe via RLock for concurrent render / upload threads.
    """

    METADATA: dict = {
        "spec": "P1-R4",
        "tier": "Pro-Tier Native",
        "module": "vjlive3.render.texture_pool",
    }

    def __init__(self, device: Any, max_per_bucket: int = 4) -> None:
        """
        Args:
            device:          wgpu.GPUDevice from RenderContext.
            max_per_bucket:  Max idle textures per (w, h, fmt, usage) bucket.
                             0 = no pooling (always destroy on release).
        """
        self._device = device
        self._max = max_per_bucket
        self._buckets: dict[_BucketKey, list[PooledTexture]] = {}
        self._allocated: int = 0
        self._lock = threading.RLock()

    def acquire(
        self,
        width: int,
        height: int,
        format: Any = None,     # wgpu.TextureFormat.rgba8unorm
        usage: int = 0,
    ) -> PooledTexture:
        """
        Return a pooled texture for (width, height, format, usage).

        Reuses an idle texture if one is available in the bucket;
        otherwise allocates a new wgpu.GPUTexture from the device.

        Raises:
            RuntimeError: If GPU texture allocation fails.
        """
        import wgpu  # lazy — allows mocking in tests

        if format is None:
            format = wgpu.TextureFormat.rgba8unorm
        if usage == 0:
            usage = wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING

        key: _BucketKey = (width, height, format, usage)

        with self._lock:
            bucket = self._buckets.get(key)
            if bucket:
                pt = bucket.pop()
                pt._released = False  # re-activate
                logger.debug("TexturePool: reused %dx%d fmt=%s", width, height, format)
                return pt

        # Allocate new texture outside the bucket lock — GPU alloc may be slow
        try:
            tex = self._device.create_texture(
                size=(width, height, 1),
                format=format,
                usage=usage,
                dimension="2d",
                mip_level_count=1,
                sample_count=1,
            )
        except Exception as exc:
            raise RuntimeError(
                f"TexturePool: wgpu texture allocation failed ({width}×{height} {format}): {exc}"
            ) from exc

        with self._lock:
            self._allocated += 1

        logger.debug("TexturePool: allocated %dx%d fmt=%s (total=%d)", width, height, format, self._allocated)
        return PooledTexture(texture=tex, pool=self, key=key, width=width, height=height, fmt=format)

    def release(self, pt: PooledTexture) -> None:
        """Return a PooledTexture to the pool. Called by PooledTexture.release()."""
        key = pt._key
        with self._lock:
            bucket = self._buckets.setdefault(key, [])
            if len(bucket) < self._max:
                bucket.append(pt)
                logger.debug("TexturePool: returned to bucket %s (idle=%d)", key[:2], len(bucket))
            else:
                # Bucket full — destroy immediately
                self._allocated -= 1
                self._destroy_texture(pt._texture, label=str(key[:2]))

    def clear(self) -> None:
        """Destroy all idle pooled textures. Call on shutdown."""
        with self._lock:
            for bucket in self._buckets.values():
                for pt in bucket:
                    self._allocated -= 1
                    self._destroy_texture(pt._texture)
            self._buckets.clear()
        logger.info("TexturePool: cleared (allocated_total now %d)", self._allocated)

    @property
    def stats(self) -> dict:
        """Return dict with pool diagnostic counters."""
        with self._lock:
            non_empty = sum(1 for b in self._buckets.values() if b)
            idle = sum(len(b) for b in self._buckets.values())
        return {
            "buckets": non_empty,
            "idle_total": idle,
            "allocated_total": self._allocated,
        }

    @staticmethod
    def _destroy_texture(tex: Any, label: str = "") -> None:
        """Attempt to destroy a wgpu.GPUTexture without crashing."""
        fn = getattr(tex, "destroy", None)
        if fn is not None:
            try:
                fn()
            except Exception as exc:
                logger.warning("TexturePool: destroy failed (%s): %s", label, exc)
