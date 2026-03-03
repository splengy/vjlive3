"""
P1-R2 — RenderTarget (Offscreen Framebuffer)
Spec: docs/specs/_02_fleshed_out/P1-R2_gpu_pipeline.md
File: src/vjlive3/render/framebuffer.py  (~120 lines)

RAII-safe offscreen RGBA render target backed by a wgpu.GPUTexture.
Device is obtained from the active RenderContext via get_current_device().
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RenderTarget:
    """
    RGBA offscreen render target. RAII lifecycle via context manager.

    Usage:
        with RenderTarget(1920, 1080) as rt:
            # rt.texture is a wgpu.GPUTextureView
            pass

    Requires an active RenderContext (used for device access).
    """

    METADATA: dict = {
        "spec": "P1-R2",
        "tier": "Pro-Tier Native",
        "module": "vjlive3.render.framebuffer",
    }

    def __init__(self, width: int, height: int) -> None:
        """
        Create an RGBA offscreen texture.

        Args:
            width, height: Pixel dimensions. Must be > 0.

        Raises:
            RuntimeError: If dimensions are invalid or GPU allocation fails.
        """
        import wgpu  # lazy — allows mocking in tests
        from vjlive3.render.render_context import get_current_device  # lazy

        # Set all instance vars FIRST — __del__ must never hit AttributeError
        # even if the constructor raises before completing.
        self._deleted = False
        self._gpu_texture = None
        self._view = None
        self._width = width
        self._height = height

        if width <= 0 or height <= 0:
            raise RuntimeError(
                f"RenderTarget: invalid dimensions {width}×{height}. Must be > 0."
            )

        device = get_current_device()
        try:
            self._gpu_texture = device.create_texture(
                size=(width, height, 1),
                format=wgpu.TextureFormat.rgba8unorm,
                usage=(
                    wgpu.TextureUsage.RENDER_ATTACHMENT
                    | wgpu.TextureUsage.TEXTURE_BINDING
                    | wgpu.TextureUsage.COPY_SRC
                ),
                dimension="2d",
                mip_level_count=1,
                sample_count=1,
            )
            self._view = self._gpu_texture.create_view()
        except Exception as exc:
            raise RuntimeError(
                f"RenderTarget: GPU texture creation failed ({width}×{height}): {exc}"
            ) from exc

        logger.debug("RenderTarget: allocated %dx%d", width, height)

    def bind(self, encoder: Any) -> None:
        """Provide this target's view as the render attachment on encoder."""
        # In wgpu, attachment binding happens when creating a render pass.
        # This method exists for API symmetry; callers use self.texture directly
        # when constructing GPURenderPassColorAttachment descriptors.

    def unbind(self, encoder: Any) -> None:
        """Signal end of use for this render target. No-op in wgpu (pass.end() handles it)."""

    def delete(self) -> None:
        """Destroy GPU texture. Safe to call multiple times (idempotent)."""
        if self._deleted:
            return
        self._deleted = True
        if self._gpu_texture is not None:
            try:
                self._gpu_texture.destroy()
            except Exception:
                pass
            self._gpu_texture = None
            self._view = None
        logger.debug("RenderTarget: deleted %dx%d", self._width, self._height)

    def __enter__(self) -> "RenderTarget":
        return self

    def __exit__(self, *_: Any) -> None:
        self.delete()

    def __del__(self) -> None:
        self.delete()

    # ---- Properties ---------------------------------------------------------

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def texture(self) -> Any:
        """The wgpu.GPUTextureView — pass to render pass color attachments."""
        return self._view
