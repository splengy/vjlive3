import pytest
import moderngl
from vjlive3.render.framebuffer import Framebuffer
from vjlive3.render.opengl_context import OpenGLContext
import os

@pytest.fixture(scope="session")
def gl_context():
    # Require headless fallback for CI 
    # Must use dict patching directly here via environ for session level
    os.environ['VJ_HEADLESS'] = 'true'
    ctx = OpenGLContext(800, 600, headless=True)
    ctx.make_current()
    yield ctx
    ctx.terminate()

def test_framebuffer_create(gl_context):
    fbo = Framebuffer(1920, 1080)
    assert fbo.width == 1920
    assert fbo.height == 1080
    assert fbo.fbo > 0
    assert fbo.texture > 0
    fbo.delete()

def test_framebuffer_bind_unbind(gl_context):
    fbo = Framebuffer(1920, 1080)
    fbo.bind()
    fbo.unbind()
    fbo.delete()

def test_framebuffer_context_manager(gl_context):
    with Framebuffer(256, 256) as fbo:
        fbo_id = fbo.fbo
        tex_id = fbo.texture
        assert fbo_id > 0
        assert tex_id > 0
    # On exit, _mgl_fbo and _mgl_texture are None
    assert fbo._mgl_fbo is None
    assert fbo._mgl_texture is None

def test_framebuffer_double_delete(gl_context):
    fbo = Framebuffer(100, 100)
    fbo.delete()
    fbo.delete() # Shouldn't raise
    
def test_framebuffer_incomplete_raises(gl_context):
    """ModernGL will raise an error internally if dimensions are impossible (e.g., 0)."""
    with pytest.raises(Exception):
        Framebuffer(0, 0)
