"""Status Window - Phase 0 Kitten Check

Displays FPS, memory usage, and agent status in a simple window.
This satisfies the Phase 0 gate requirement: "Status window running (FPS ≥ 58, visible)"
"""

import sys
import time
import psutil
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import glfw
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    print("Warning: GLFW not available - status window will run in console mode only")

from vjlive3.core.sigil import sigil


class StatusWindow:
    """Simple status display for Phase 0 verification."""
    
    def __init__(self, target_fps=58):
        self.target_fps = target_fps
        self.start_time = time.time()
        self.frame_count = 0
        self.current_fps = 0.0
        self.running = True
        self.window = None
        
        # Get sigil status
        self.sigil_verified = sigil.verify() is None
        
        # Initialize OpenGL window if available
        if OPENGL_AVAILABLE:
            self._init_window()
    
    def _get_memory_usage(self) -> float:
        """Get current process memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0
    
    def _init_window(self):
        """Initialize GLFW window for visual display."""
        if not glfw.init():
            raise RuntimeError("Failed to initialize GLFW")
        
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        
        self.window = glfw.create_window(400, 200, "VJLive3 Status", None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("Failed to create GLFW window")
        
        glfw.make_context_current(self.window)
        glfw.set_key_callback(self.window, self._key_callback)
    
    def _key_callback(self, window, key, scancode, action, mods):
        """Handle keyboard input."""
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            self.running = False
    
    def update(self):
        """Update status metrics."""
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        if elapsed >= 1.0:
            self.current_fps = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = current_time
    
    def render(self):
        """Render status information."""
        if self.window:
            # OpenGL rendering would go here
            # For now, we just update the window title
            glfw.set_window_title(
                self.window,
                f"VJLive3 Status - FPS: {self.current_fps:.1f} - Target: {self.target_fps}"
            )
        else:
            # Console mode
            print(f"\rFPS: {self.current_fps:.1f} | Target: {self.target_fps} | Sigil: {'✓' if self.sigil_verified else '✗'}", end="")
    
    def run(self):
        """Main loop."""
        print("=" * 60)
        print("VJLive3 Phase 0 Status Window")
        print("=" * 60)
        print(f"Target FPS: {self.target_fps}")
        print(f"Memory Usage: {self._get_memory_usage():.1f} MB")
        print(f"Silicon Sigil: {'VERIFIED' if self.sigil_verified else 'FAILED'}")
        print("Press ESC to exit")
        print("=" * 60)
        
        try:
            while self.running and (not self.window or not glfw.window_should_close(self.window)):
                self.update()
                self.render()
                
                if self.window:
                    glfw.swap_buffers(self.window)
                    glfw.poll_events()
                else:
                    time.sleep(0.016)  # ~60 FPS
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        if self.window:
            glfw.destroy_window(self.window)
            glfw.terminate()
        
        # Final status report
        print("\n" + "=" * 60)
        print("Phase 0 Status Window - Final Report")
        print("=" * 60)
        print(f"Final FPS: {self.current_fps:.1f}")
        print(f"Target Met: {'✓' if self.current_fps >= self.target_fps else '✗'}")
        print(f"Memory Usage: {self._get_memory_usage():.1f} MB")
        print(f"Silicon Sigil: {'VERIFIED' if self.sigil_verified else 'FAILED'}")
        print("=" * 60)


def main():
    """Entry point."""
    window = StatusWindow(target_fps=58)
    window.run()


if __name__ == "__main__":
    main()