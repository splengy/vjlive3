"""
P1-R1: OpenGL Rendering Context (Synthesized from VJlive-2)
Handles GLFW window lifecycle exactly as legacy `window.py` did, but
attaches ModernGL contexts directly, deprecating `gl_wrapper.py` completely.
"""
import os
import sys
import logging
from typing import Optional
import moderngl

logger = logging.getLogger("vjlive3.render.opengl_context")

# Legacy Headless Environmental Override (From VJlive-2 core.window)
HEADLESS = os.environ.get("VJ_HEADLESS", "false").lower() == "true"

if not HEADLESS:
    try:
        import glfw
        HAS_GLFW = True
        logger.debug("GLFW imported successfully.")
    except ImportError as e:
        logger.warning(f"GLFW not found: {e}. Falling back to HEADLESS mode.")
        glfw = None
        HAS_GLFW = False
    except OSError as e:
        logger.warning(f"System libraries missing/incompatible: {e}. Falling back to HEADLESS mode.")
        glfw = None
        HAS_GLFW = False
else:
    logger.debug("VJ_HEADLESS env set to true.")
    glfw = None
    HAS_GLFW = False

class OpenGLContext:
    """
    RAII-managed OpenGL context and Window provider.
    Replaces VJlive-2 `Window` and PyOpenGL generic wrappers.
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
        self.headless = headless or HEADLESS or not HAS_GLFW
        self._window = None
        self.ctx: Optional[moderngl.Context] = None

        logger.info(f"OpenGLContext initialized with headless={self.headless}")

        if self.headless:
            logger.info("Starting in HEADLESS mode. No window will be created.")
            try:
                self.ctx = moderngl.create_context(standalone=True)
            except Exception as e:
                logger.critical(f"Failed to create standalone ModernGL context: {e}")
                raise RuntimeError(f"ModernGL context creation failed: {e}")
            return

        if not glfw.init():
            logger.critical("Failed to initialize GLFW.")
            raise RuntimeError("GLFW initialization failed")

        # Port from VJlive-2 window.py configuration
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
        glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
        glfw.window_hint(glfw.SAMPLES, 4)

        self._window = glfw.create_window(self.width, self.height, title, None, None)
        if not self._window:
            glfw.terminate()
            logger.critical("Failed to create GLFW window.")
            raise RuntimeError("GLFW window creation failed")

        glfw.make_context_current(self._window)
        
        # Port from VJlive-2 window.py (VSync lock)
        glfw.swap_interval(1)

        try:
            # Replaces VJlive-2's GLContext entirely by attaching modernGL state directly
            self.ctx = moderngl.create_context()
        except Exception as e:
            glfw.destroy_window(self._window)
            glfw.terminate()
            logger.critical(f"Failed to attach ModernGL to GLFW context: {e}")
            raise RuntimeError(f"ModernGL attachment failed: {e}")

        logger.info(f"Window / Context initialized: {width}x{height}")

    def make_current(self) -> None:
        if not self.headless and self._window and glfw:
            glfw.make_context_current(self._window)

    def poll_events(self) -> None:
        if not self.headless and glfw:
            glfw.poll_events()

    def should_close(self) -> bool:
        if self.headless or not self._window or not glfw:
            return False
        return glfw.window_should_close(self._window)

    def swap_buffers(self) -> None:
        if not self.headless and self._window and glfw:
            glfw.swap_buffers(self._window)

    def terminate(self) -> None:
        if self.ctx is not None:
            self.ctx.release()
            self.ctx = None

        if not self.headless and self._window and glfw:
            glfw.destroy_window(self._window)
            self._window = None
            glfw.terminate()
            logger.info("OpenGLContext cleanly terminated.")

    def __enter__(self) -> "OpenGLContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.terminate()

    def __del__(self) -> None:
        self.terminate()
