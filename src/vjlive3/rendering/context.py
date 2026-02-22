import glfw
import moderngl

class OpenGLContext:
    def __init__(self, width: int, height: int, title: str, vsync: bool = False, debug: bool = False):
        glfw.init()
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        if debug:
            glfw.window_hint(glfw.CONTEXT_DEBUG, True)
        self.window = glfw.create_window(width, height, title, None, None)
        glfw.make_context_current(self.window)
        self.ctx = moderngl.create_context(require=330)
        glfw.swap_interval(1 if vsync else 0)

    def make_current(self):
        glfw.make_context_current(self.window)

    def swap_buffers(self):
        glfw.swap_buffers(self.window)

    def poll_events(self):
        glfw.poll_events()

    def should_close(self):
        return glfw.window_should_close(self.window)

    def get_framebuffer_size(self):
        width, height = glfw.get_framebuffer_size(self.window)
        return width, height

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        glfw.destroy_window(self.window)
