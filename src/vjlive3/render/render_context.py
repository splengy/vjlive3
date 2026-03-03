"""
P1-R1 — Agnostic Render Context
Spec: docs/specs/_02_fleshed_out/P1-R1_opengl_context.md
Tier: 🖥️ Pro-Tier Native — GLFW + wgpu-py, desktop only.

RAII-managed WebGPU context and GLFW window provider.
All imports of wgpu and glfw are lazy (inside methods) to allow full mocking in tests.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Single-instance guard: only one render context per process.
_active_instance: Optional["RenderContext"] = None


def get_current_device():
    """
    Return the wgpu.GPUDevice from the active RenderContext.

    Called by RenderTarget, RenderPipeline, and EffectChain to avoid
    requiring an explicit device argument on every constructor.

    Raises:
        RuntimeError: If no RenderContext is active.
    """
    if _active_instance is None or _active_instance._terminated:
        raise RuntimeError(
            "get_current_device(): no active RenderContext. "
            "Create a RenderContext before using render objects."
        )
    return _active_instance.device


class RenderContext:
    """
    RAII-managed WebGPU render context + GLFW window.

    Spec: P1-R1. Tier: Pro-Tier Native (ADR-024).

    Usage:
        with RenderContext(width=1920, height=1080) as ctx:
            while not ctx.should_close():
                ctx.poll_events()
                # ... render ...
                ctx.swap_buffers()

    Headless mode (VJ_HEADLESS=true or headless=True):
        Creates a wgpu adapter without any display surface.
        All window-related methods become no-ops.
    """

    METADATA: dict = {
        "spec": "P1-R1",
        "tier": "Pro-Tier Native",
        "module": "vjlive3.render.render_context",
    }

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        title: str = "VJLive 3.0 :: The Reckoning",
        headless: bool = False,
    ) -> None:
        """
        Initialise the render context.

        Args:
            width:    Window width in pixels (ignored in headless mode).
            height:   Window height in pixels (ignored in headless mode).
            title:    Window title bar text.
            headless: If True, bypass window creation. Overridden by VJ_HEADLESS=true.

        Raises:
            RuntimeError: If wgpu adapter is unavailable, or GLFW fails to init.
        """
        global _active_instance
        # Set ALL instance variables first — ensures __del__ never raises
        # AttributeError regardless of where __init__ fails.
        self._terminated: bool = False
        self._canvas = None
        self._ctx = None
        self._adapter = None
        self._device = None

        if _active_instance is not None and not _active_instance._terminated:
            raise RuntimeError(
                "RenderContext: only one instance is allowed per process. "
                "Call terminate() on the existing context first."
            )

        self._width: int = width
        self._height: int = height
        self._title: str = title

        # VJ_HEADLESS env var always wins over constructor arg (ADR-020)
        env_headless = os.environ.get("VJ_HEADLESS", "").lower() == "true"
        self._headless: bool = headless or env_headless

        if self._headless:
            self._init_headless()
        else:
            self._init_windowed()

        _active_instance = self
        logger.info(
            "RenderContext ready — %s %dx%d",
            "headless" if self._headless else "windowed",
            self._width,
            self._height,
        )

    # -------------------------------------------------------------------------
    # Initialisation helpers
    # -------------------------------------------------------------------------

    def _init_headless(self) -> None:
        """Request a wgpu adapter without display surface for offscreen compute."""
        import wgpu  # lazy import — allows mocking in tests

        self._adapter = wgpu.gpu.request_adapter_sync(
            power_preference="high-performance"
        )
        if self._adapter is None:
            raise RuntimeError(
                "RenderContext: wgpu adapter unavailable in headless mode. "
                "Ensure Vulkan, Metal, or DX12 drivers are installed."
            )
        self._device = self._adapter.request_device_sync()
        logger.debug("Headless adapter: %s", self._adapter.info)

    def _init_windowed(self) -> None:
        """Initialise GLFW window and attach a wgpu surface to it."""
        import glfw  # lazy import — allows mocking in tests
        import wgpu
        from wgpu.gui.glfw import WgpuCanvas  # type: ignore[import]

        if not glfw.init():
            raise RuntimeError(
                "RenderContext: glfw.init() failed. "
                "Ensure a display is available or use VJ_HEADLESS=true."
            )

        self._canvas = WgpuCanvas(
            title=self._title,
            size=(self._width, self._height),
        )
        self._ctx = self._canvas.get_context("wgpu")

        self._adapter = wgpu.gpu.request_adapter_sync(
            power_preference="high-performance",
            canvas=self._canvas,
        )
        if self._adapter is None:
            glfw.terminate()
            raise RuntimeError(
                "RenderContext: wgpu adapter unavailable. "
                "Ensure Vulkan, Metal, or DX12 drivers are installed."
            )
        self._device = self._adapter.request_device_sync()
        logger.debug("Windowed adapter: %s", self._adapter.info)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def make_current(self) -> None:
        """Make context current for calling thread. No-op in headless mode."""
        # wgpu-py handles context currency internally; no explicit call needed.
        # Exists for API compatibility with callers that expect this method.

    def poll_events(self) -> None:
        """Process pending GLFW window events. No-op in headless mode."""
        if self._headless or self._canvas is None:
            return
        import glfw
        glfw.poll_events()

    def should_close(self) -> bool:
        """Return True if the user has requested window close. Always False in headless."""
        if self._headless or self._canvas is None:
            return False
        return bool(self._canvas.is_closed())

    def swap_buffers(self) -> None:
        """Present the current rendered frame to the display. No-op in headless mode."""
        if self._headless or self._canvas is None:
            return
        self._canvas.present()

    def terminate(self) -> None:
        """
        Destroy the window and release all GPU resources.

        Safe to call multiple times — idempotent (ADR in DECISIONS.md).
        """
        if self._terminated:
            return
        self._terminated = True

        global _active_instance
        if _active_instance is self:
            _active_instance = None

        if self._device is not None:
            try:
                self._device.destroy()
            except Exception:  # noqa: BLE001 — GPU teardown must never crash
                pass
            self._device = None

        if self._canvas is not None:
            try:
                self._canvas.close()
            except Exception:  # noqa: BLE001
                pass
            self._canvas = None
            try:
                import glfw
                glfw.terminate()
            except Exception:  # noqa: BLE001
                pass

        self._ctx = None
        self._adapter = None
        logger.info("RenderContext terminated")

    # -------------------------------------------------------------------------
    # Context manager protocol
    # -------------------------------------------------------------------------

    def __enter__(self) -> "RenderContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.terminate()

    def __del__(self) -> None:
        # Best-effort cleanup on GC. terminate() is idempotent.
        self.terminate()

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def width(self) -> int:
        """Window width in pixels."""
        return self._width

    @property
    def height(self) -> int:
        """Window height in pixels."""
        return self._height

    @property
    def headless(self) -> bool:
        """True if this context was created without a display."""
        return self._headless

    @property
    def ctx(self):
        """
        The wgpu.GPUCanvasContext (windowed mode only).
        None in headless mode.
        """
        return self._ctx

    @property
    def device(self):
        """
        The wgpu.GPUDevice — the primary GPU resource for all render operations.
        Always set after successful initialisation.
        """
        return self._device

    @property
    def adapter(self):
        """The wgpu.GPUAdapter selected by wgpu for this context."""
        return self._adapter
