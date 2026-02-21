# Spec: P1-R1 — OpenGL Rendering Context (ModernGL)

**Phase:** Phase 1 / P1-R1
**Assigned To:** Roo Coder (1)
**Spec Written By:** ROO CODE (Manager)
**Date:** 2026-02-21

---

## What This Module Does

Creates a ModernGL rendering context with proper OpenGL 3.3+ core profile support. This is the foundation for all GPU rendering in VJLive3. It initializes GLFW for window management, creates the OpenGL context with appropriate flags (forward-compatible, debug mode in dev), and provides a clean RAII wrapper for context lifecycle management. The context must support modern OpenGL features required by the rendering pipeline (shaders, framebuffers, texture formats).

---

## What It Does NOT Do

- Does NOT implement any rendering logic (that's P1-R5)
- Does NOT manage textures or framebuffers (that's P1-R4)
- Does NOT compile shaders (that's P1-R3)
- Does NOT handle audio or node graph integration
- Does NOT provide UI or user interaction
- Does NOT manage multiple windows (single window only for now)

---

## Public Interface

```python
class OpenGLContext:
    """ModernGL rendering context with GLFW window management."""
    
    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        title: str = "VJLive3",
        vsync: bool = True,
        debug: bool = True
    ) -> None:
        """Initialize GLFW window and OpenGL context.
        
        Args:
            width: Window width in pixels (default 1920)
            height: Window height in pixels (default 1080)
            title: Window title
            vsync: Enable vertical sync (default True for 60 FPS cap)
            debug: Enable OpenGL debug context and logging (default True in dev)
        
        Raises:
            RuntimeError: If GLFW initialization or context creation fails
        """
    
    def __enter__(self) -> 'OpenGLContext':
        """Context manager entry."""
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clean shutdown of context and window."""
    
    def make_current(self) -> None:
        """Make this context current on the calling thread."""
    
    def swap_buffers(self) -> None:
        """Swap front/back buffers (call after rendering)."""
    
    def poll_events(self) -> None:
        """Process GLFW events (keyboard, mouse, window close)."""
    
    def should_close(self) -> bool:
        """Check if window close requested."""
    
    def get_framebuffer_size(self) -> Tuple[int, int]:
        """Get actual framebuffer size (may differ from window size on HiDPI)."""
    
    @property
    def window(self) -> Any:
        """Get underlying GLFW window handle (for ModernGL)."""
    
    @property
    def ctx(self) -> moderngl.Context:
        """Get ModernGL context object."""
    
    def set_title(self, title: str) -> None:
        """Update window title."""
    
    def set_vsync(self, vsync: bool) -> None:
        """Toggle vertical sync at runtime."""
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `width` | `int` | Window width | 640–4096, default 1920 |
| `height` | `int` | Window height | 480–2160, default 1080 |
| `title` | `str` | Window title | Non-empty |
| `vsync` | `bool` | V-sync enable | Default True |
| `debug` | `bool` | Debug context | Default True (False in prod) |

**Outputs:**
- ModernGL context object ready for rendering
- GLFW window with valid OpenGL 3.3+ core profile
- RAII lifecycle management (no resource leaks)

---

## Edge Cases and Error Handling

- **GLFW not available:** Raise RuntimeError with clear message "GLFW initialization failed"
- **OpenGL version too old:** Raise RuntimeError "OpenGL 3.3+ required"
- **Context creation failure:** Clean up GLFW and raise error
- **HiDPI displays:** Use `glfwGetFramebufferSize` to get actual pixel dimensions
- **Thread safety:** Context must be used on the thread that created it (document in docstring)
- **Multiple init calls:** Guard against double initialization (raise if already initialized)
- **Shutdown:** Ensure GLFW is terminated exactly once, even if exceptions occur

---

## Dependencies

### External Libraries
- **glfw** (>= 2.0) — window/context creation
  - Fallback: If import fails, raise clear error "pip install glfw"
- **moderngl** (>= 5.0) — OpenGL wrapper
  - Fallback: If import fails, raise clear error "pip install moderngl"

### Internal Modules
- None (this is the foundation)

---

## Test Plan

| Test | What It Verifies |
|------|------------------|
| `test_context_creation` | OpenGLContext() succeeds with default params |
| `test_custom_dimensions` | 1280x720 window creates correctly |
| `test_context_manager` | `with OpenGLContext():` enters and exits cleanly |
| `test_should_close_initial` | should_close() returns False initially |
| `test_get_framebuffer_size` | Returns tuple matching or exceeding window size |
| `test_make_current` | make_current() succeeds without error |
| `test_swap_buffers` | swap_buffers() can be called (doesn't crash) |
| `test_set_title` | set_title() updates window title |
| `test_set_vsync` | Toggling vsync doesn't crash |
| `test_debug_context` | Debug context creates successfully (when debug=True) |
| `test_cleanup_on_exception` | Context cleans up even if exception raised inside `with` |
| `test_no_double_init` | Second OpenGLContext() on same thread raises error |
| `test_ctx_property` | ctx property returns moderngl.Context instance |
| `test_window_property` | window property returns GLFW window handle |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All 14 tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint P1-R1 checked in VERIFICATION_CHECKPOINTS.md
- [ ] Git commit with `[Phase-1] P1-R1: OpenGL context with ModernGL + GLFW` message
- [ ] BOARD.md P1-R1 marked ✅
- [ ] Lock released from LOCKS.md
- [ ] AGENT_SYNC.md handoff note written (summary, FPS test result, any issues)

---

## Technical Notes for Implementer

**ModernGL Context Creation Pattern:**
```python
import glfw
import moderngl

# Init GLFW
glfw.init()
# Set OpenGL 3.3+ core profile
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
# Debug context (dev only)
if debug:
    glfw.window_hint(glfw.CONTEXT_DEBUG, True)

# Create window
window = glfw.create_window(width, height, title, None, None)
# Make context current
glfw.make_context_current(window)
# Create ModernGL context
ctx = moderngl.create_context(require=330)

# Vsync
glfw.swap_interval(1 if vsync else 0)
```

**Cleanup Pattern:**
```python
def __exit__(self, *args):
    glfw.destroy_window(self.window)
    glfw.terminate()
```

**HiDPI Handling:**
```python
fb_width, fb_height = glfw.get_framebuffer_size(window)
# Use these for ModernGL viewport, not window size
```

**Thread Safety:** Document clearly that the context is NOT thread-safe and must only be used on the thread that created it.

**Performance:** This is a foundational layer — zero allocations in hot path. Context creation happens once at startup.

---

## Verification Commands

```bash
# Run tests
PYTHONPATH=src python3 -m pytest tests/unit/test_opengl_context.py -v

# Manual smoke test (should open window for 3 seconds)
PYTHONPATH=src python3 -c "
from vjlive3.render.opengl_context import OpenGLContext
with OpenGLContext(1280, 720, 'Test') as ctx:
    import time
    start = time.time()
    while time.time() - start < 3:
        ctx.poll_events()
        if ctx.should_close():
            break
        ctx.make_current()
        # Clear to blue
        ctx.ctx.clear(0.0, 0.0, 1.0, 1.0)
        ctx.swap_buffers()
"
# Expected: Blue window appears, runs 3 seconds, closes cleanly