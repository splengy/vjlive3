"""
P1-R1: OpenGL Rendering Context
Handles GLFW window lifecycle and ModernGL context creation.
"""
import os
import logging
from typing import Optional
import moderngl

# For headless testing environments where glfw cannot load properly
try:
    if os.environ.get("VJ_HEADLESS") == "true":
        raise ImportError("Forced headless mode")
    import glfw
    HAS_GLFW = True
except ImportError:
    glfw = None
    HAS_GLFW = False

logger = logging.getLogger("vjlive3.render.opengl_context")

class OpenGLContext:
    """
    RAII-managed OpenGL context and Window provider.
    Handles GLFW initialization and ModernGL context attachment.
    """

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        title: str = "VJLive 3.0 :: The Reckoning",
        headless: bool = False
    ) -> None:
        self.width = width
        self.height = height
        self.headless = headless or not HAS_GLFW or os.environ.get("VJ_HEADLESS", "").lower() == "true"
        self._window = None
        self.ctx: Optional[moderngl.Context] = None

        if self.headless:
            logger.info("Initializing OpenGLContext in HEADLESS mode (standalone context).")
            try:
                # Require backend parameter to avoid implicit window server lookup failures
                self.ctx = moderngl.create_context(standalone=True)
            except Exception as e:
                logger.critical(f"Failed to create standalone ModernGL context: {e}")
                raise RuntimeError(f"ModernGL context creation failed: {e}")
        else:
            logger.info(f"Initializing OpenGLContext with GLFW Window ({width}x{height}).")
            if not glfw.init():
                logger.critical("Failed to initialize GLFW.")
                raise RuntimeError("GLFW initialization failed")

            # Configure strict modern OpenGL specs (3.3 Core profile minimum)
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
            glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)

            # 4x MSAA for smoother edge lines
            glfw.window_hint(glfw.SAMPLES, 4)

            self._window = glfw.create_window(width, height, title, None, None)
            if not self._window:
                glfw.terminate()
                logger.critical("Failed to create GLFW window.")
                raise RuntimeError("GLFW window creation failed")

            glfw.make_context_current(self._window)
            
            try:
                # ModernGL will automatically detect the active GLFW context
                self.ctx = moderngl.create_context()
            except Exception as e:
                glfw.destroy_window(self._window)
                glfw.terminate()
                logger.critical(f"Failed to attach ModernGL to GLFW context: {e}")
                raise RuntimeError(f"ModernGL attachment failed: {e}")

    def make_current(self) -> None:
        """Make the GLFW OpenGL context current for the calling thread."""
        if not self.headless and self._window and glfw:
            glfw.make_context_current(self._window)

    def poll_events(self) -> None:
        """Process pending GLFW window events."""
        if not self.headless and glfw:
            glfw.poll_events()

    def should_close(self) -> bool:
        """Check if the user has requested to close the window."""
        if self.headless or not self._window or not glfw:
            return False
        return glfw.window_should_close(self._window)

    def swap_buffers(self) -> None:
        """Swap front and back buffers."""
        if not self.headless and self._window and glfw:
            glfw.swap_buffers(self._window)

    def terminate(self) -> None:
        """Destroy the window, release the ModernGL context, and terminate GLFW."""
        if self.ctx is not None:
            self.ctx.release()
            self.ctx = None
            logger.debug("ModernGL context released.")

        if not self.headless and self._window and glfw:
            glfw.destroy_window(self._window)
            self._window = None
            glfw.terminate()
            logger.debug("GLFW window destroyed and terminated.")

    def __enter__(self) -> "OpenGLContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.terminate()

    def __del__(self) -> None:
        self.terminate()
