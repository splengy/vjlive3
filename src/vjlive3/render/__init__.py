"""
VJLive3 Render Pipeline
Provides RAII-managed GPU resources utilizing ModernGL.
"""
from .shader_compiler import ShaderCompiler
from .texture_manager import TextureManager, TextureStats
from .engine import RenderEngine

__all__ = [
    'OpenGLContext',
    'ShaderCompiler',
    'TextureManager',
    'TextureStats',
    'RenderEngine',
]
