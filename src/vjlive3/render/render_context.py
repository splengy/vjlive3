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
        self._screen_format: str = "rgba8unorm"
        self._screen_blit_pipeline = None
        self._screen_blit_sampler = None

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
        """Initialise GLFW window via rendercanvas and attach a wgpu surface."""
        import math
        import wgpu
        from rendercanvas.glfw import GlfwRenderCanvas  # type: ignore[import]

        # GlfwRenderCanvas calls glfw.init() internally via enable_glfw().
        # No need for a manual glfw.init() check here.
        self._canvas = GlfwRenderCanvas(
            title=self._title,
            size=(self._width, self._height),
        )
        self._ctx = self._canvas.get_context("wgpu")

        self._adapter = wgpu.gpu.request_adapter_sync(
            power_preference="high-performance",
        )
        if self._adapter is None:
            self._canvas.close()
            raise RuntimeError(
                "RenderContext: wgpu adapter unavailable. "
                "Ensure Vulkan, Metal, or DX12 drivers are installed."
            )
        self._device = self._adapter.request_device_sync()
        logger.debug("Windowed adapter: %s", self._adapter.info)

        # Configure the canvas context for screen rendering.
        # Must be done before calling get_current_texture() each frame.
        preferred_fmt = self._ctx.get_preferred_format(self._adapter)
        self._ctx.configure(
            device=self._device,
            format=preferred_fmt,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT,
        )
        self._screen_format = preferred_fmt
        logger.debug("Canvas ctx configured — format=%s", preferred_fmt)

    def blit_to_screen(
        self,
        src_view: object = None,
        frame_time: float = 0.0,
    ) -> None:
        """
        Blit a GPU texture view (chain output) to the screen surface each frame.

        When *src_view* is provided this function builds a fullscreen blit
        pipeline (SCREEN_BLIT_WGSL) on the first call and renders the texture
        to the screen surface via a triangle-strip draw.  When *src_view* is
        None it falls back to the colour-cycle clear pattern to keep the window
        alive and animated even when no effects are loaded.

        Args:
            src_view:   A ``GPUTextureView`` produced by the EffectChain (or
                        any other offscreen render target).  Pass ``None`` to
                        activate the animated colour-cycle fallback.
            frame_time: Seconds since start, used by the colour-cycle fallback.
        """
        if self._headless or self._ctx is None or self._device is None:
            return
        try:
            screen_tex = self._ctx.get_current_texture()
            screen_view = screen_tex.create_view()

            if src_view is not None:
                # --- GPU texture blit path -------------------------------------
                self._ensure_screen_blit_pipeline()
                bg = self._device.create_bind_group(
                    layout=self._screen_blit_pipeline.get_bind_group_layout(0),
                    entries=[
                        {"binding": 0, "resource": src_view},
                        {"binding": 1, "resource": self._screen_blit_sampler},
                    ],
                )
                encoder = self._device.create_command_encoder(label="screen-blit")
                rp = encoder.begin_render_pass(
                    color_attachments=[{
                        "view": screen_view,
                        "resolve_target": None,
                        "load_op": "clear",
                        "store_op": "store",
                        "clear_value": (0.0, 0.0, 0.0, 1.0),
                    }]
                )
                rp.set_pipeline(self._screen_blit_pipeline)
                rp.set_bind_group(0, bg)
                rp.draw(4)
                rp.end()
                self._device.queue.submit([encoder.finish()])

            else:
                # --- Colour-cycle fallback (no chain output yet) ---------------
                import math
                t = frame_time * 0.2
                r = 0.5 + 0.4 * math.sin(math.tau * t)
                g = 0.5 + 0.4 * math.sin(math.tau * t + math.tau / 3)
                b = 0.5 + 0.4 * math.sin(math.tau * t + 2 * math.tau / 3)
                encoder = self._device.create_command_encoder(label="screen-blit-cycle")
                rp = encoder.begin_render_pass(
                    color_attachments=[{
                        "view": screen_view,
                        "resolve_target": None,
                        "load_op": "clear",
                        "store_op": "store",
                        "clear_value": (r, g, b, 1.0),
                    }]
                )
                rp.end()
                self._device.queue.submit([encoder.finish()])

        except Exception as exc:
            logger.debug("RenderContext.blit_to_screen: %s", exc)

    def _ensure_screen_blit_pipeline(self) -> None:
        """Lazily create the SCREEN_BLIT_WGSL pipeline and sampler once."""
        if self._screen_blit_pipeline is not None:
            return
        import wgpu
        from vjlive3.render.shaders import SCREEN_BLIT_WGSL

        module = self._device.create_shader_module(code=SCREEN_BLIT_WGSL, label="screen-blit")
        self._screen_blit_pipeline = self._device.create_render_pipeline(
            layout="auto",
            label="screen-blit",
            vertex={
                "module": module,
                "entry_point": "vs_main",
            },
            fragment={
                "module": module,
                "entry_point": "fs_main",
                "targets": [{"format": self._screen_format}],
            },
            primitive={"topology": "triangle-strip"},
        )
        self._screen_blit_sampler = self._device.create_sampler(
            label="screen-blit",
            min_filter="linear",
            mag_filter="linear",
        )
        logger.debug("Screen blit pipeline created (format=%s)", self._screen_format)


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
        import glfw as _glfw
        _glfw.poll_events()
        # GlfwRenderCanvas._maybe_close() checks glfw.window_should_close()
        # and calls canvas.close() if the user clicked X. Must be called after
        # poll_events to propagate the close signal into canvas.is_closed().
        if hasattr(self._canvas, "_maybe_close"):
            self._canvas._maybe_close()


    def should_close(self) -> bool:
        """Return True if the user has requested window close. Always False in headless."""
        if self._headless or self._canvas is None:
            return False
        # GlfwRenderCanvas exposes get_closed() in rendercanvas 2.x (is_closed() deprecated)
        get_closed = getattr(self._canvas, "get_closed", None)
        if get_closed is not None:
            return bool(get_closed())
        return bool(self._canvas.is_closed())

    def swap_buffers(self) -> None:
        """Present the current rendered frame to the display. No-op in headless mode."""
        if self._headless or self._canvas is None:
            return
        # Use canvas.force_draw() — the correct public API to trigger a synchronous
        # present from outside the canvas event loop. Path:
        #   force_draw() -> _rc_force_paint() -> _time_to_paint()
        #   -> _draw_and_present(force_sync=True) -> ctx._rc_present(force_sync=True)
        #   -> wgpu_context.present() -> screen surface is updated.
        if hasattr(self._canvas, "force_draw"):
            self._canvas.force_draw()


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
