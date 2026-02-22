"""
P1-R2: Framebuffer Management
RAII-managed offscreen render targets.
"""
import moderngl
from typing import Optional

class Framebuffer:
    """RGBA offscreen render target. RAII lifecycle via context manager."""
    
    # Required by PRIME_DIRECTIVE Rule 2 (Data Provenance)
    METADATA = {
        "author": "Antigravity (Manager)",
        "phase": "P1-R2",
        "description": "RAII Framebuffer built on ModernGL"
    }

    def __init__(self, width: int, height: int) -> None:
        """Create FBO + RGBA texture attachment."""
        # The OpenGLContext must be initialized and active before this is called
        ctx = moderngl.get_context()
        if not ctx:
            raise RuntimeError("No active ModernGL context found. Ensure OpenGLContext is active.")
            
        self.width = width
        self.height = height
        
        try:
            # Create the color attachment texture (RGBA 8-bit per channel)
            self._mgl_texture = ctx.texture((width, height), 4)
            # Nearest neighbor or Linear filtering setup depending on requirements (Linear by default in VJlive-2)
            self._mgl_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self._mgl_texture.repeat_x = False
            self._mgl_texture.repeat_y = False
            
            # Create the framebuffer
            self._mgl_fbo = ctx.framebuffer(color_attachments=[self._mgl_texture])
        except Exception as e:
            raise RuntimeError(f"Framebuffer not complete: {e}")
            
    @property
    def fbo(self) -> int:
        """GL framebuffer object ID"""
        return self._mgl_fbo.glo
        
    @property
    def texture(self) -> int:
        """GL texture ID"""
        return self._mgl_texture.glo
        
    def bind(self) -> None:
        """Bind for rendering. Sets glViewport implicitly in ModernGL."""
        if self._mgl_fbo:
            self._mgl_fbo.use()
            # ModernGL's fbo.use() automatically sets the viewport to the FBO size
            
    def unbind(self) -> None:
        """Bind default framebuffer (0)."""
        ctx = moderngl.get_context()
        if ctx and ctx.screen:
            ctx.screen.use()
            
    def bind_texture(self, unit: int = 0) -> None:
        """Bind the colour texture to the given texture unit."""
        if self._mgl_texture:
            self._mgl_texture.use(location=unit)
            
    def delete(self) -> None:
        """Delete FBO and texture. Safe to call multiple times."""
        if hasattr(self, '_mgl_fbo') and self._mgl_fbo:
            self._mgl_fbo.release()
            self._mgl_fbo = None
            
        if hasattr(self, '_mgl_texture') and self._mgl_texture:
            self._mgl_texture.release()
            self._mgl_texture = None

    def __enter__(self) -> "Framebuffer":
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.delete()
        
    def __del__(self) -> None:
        self.delete()
