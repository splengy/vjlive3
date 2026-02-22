import os
import pytest
from unittest.mock import patch, MagicMock
from vjlive3.render.opengl_context import OpenGLContext

@pytest.fixture
def mock_headless_env(monkeypatch):
    monkeypatch.setenv("VJ_HEADLESS", "true")

def test_context_headless_override():
    """headless=True bypasses window, ctx is standalone"""
    ctx = OpenGLContext(headless=True)
    assert ctx.headless is True
    assert ctx._window is None
    assert ctx.ctx is not None
    # No-ops shouldn't crash
    ctx.make_current()
    ctx.poll_events()
    ctx.swap_buffers()
    assert ctx.should_close() is False
    ctx.terminate()

def test_context_env_headless(mock_headless_env):
    """VJ_HEADLESS=true env var forces headless"""
    ctx = OpenGLContext()
    assert ctx.headless is True
    ctx.terminate()

def test_context_manager_lifecycle():
    """with OpenGLContext(...) cleans up resources on exit"""
    with OpenGLContext(headless=True) as ctx:
        assert ctx.ctx is not None
        assert ctx.headless is True
    assert ctx.ctx is None # cleaned up

def test_context_double_terminate():
    """Calling terminate() twice doesn't crash"""
    ctx = OpenGLContext(headless=True)
    ctx.terminate()
    ctx.terminate() # should not throw
    assert ctx.ctx is None

def test_window_methods_headless():
    """swap_buffers(), poll_events(), make_current() do not crash in headless mode"""
    ctx = OpenGLContext(headless=True)
    ctx.make_current()
    ctx.poll_events()
    ctx.swap_buffers()
    assert not ctx.should_close()
    ctx.terminate()

@patch('vjlive3.render.opengl_context.glfw')
def test_glfw_init_failure(mock_glfw):
    """GLFW fails to init -> Raises RuntimeError"""
    mock_glfw.init.return_value = False
    
    with pytest.raises(RuntimeError, match="GLFW initialization failed"):
        # Force non-headless so it attempts to boot glfw
        with patch('vjlive3.render.opengl_context.HAS_GLFW', True):
            OpenGLContext(headless=False)

@patch('vjlive3.render.opengl_context.glfw')
def test_glfw_window_failure(mock_glfw):
    """create_window fails -> raises RuntimeError and calls terminate"""
    mock_glfw.init.return_value = True
    mock_glfw.create_window.return_value = None
    
    with pytest.raises(RuntimeError, match="GLFW window creation failed"):
        with patch('vjlive3.render.opengl_context.HAS_GLFW', True):
            OpenGLContext(headless=False)
    
    mock_glfw.terminate.assert_called_once()
    
@patch('vjlive3.render.opengl_context.moderngl')
def test_moderngl_standalone_creation_failure(mock_mgl):
    """Standalone modernGL fails -> raises RuntimeError"""
    mock_mgl.create_context.side_effect = Exception("No EGL backing")
    
    with pytest.raises(RuntimeError, match="ModernGL context creation failed"):
        OpenGLContext(headless=True)

@patch('vjlive3.render.opengl_context.glfw')
@patch('vjlive3.render.opengl_context.moderngl')
def test_moderngl_windowed_attachment_failure(mock_mgl, mock_glfw):
    """Window created but modernGl attach fails -> cleans up glfw and raises"""
    mock_glfw.init.return_value = True
    mock_window = MagicMock()
    mock_glfw.create_window.return_value = mock_window
    mock_mgl.create_context.side_effect = Exception("Bad format")
    
    with pytest.raises(RuntimeError, match="ModernGL attachment failed"):
        with patch('vjlive3.render.opengl_context.HAS_GLFW', True):
            OpenGLContext(headless=False)
            
    mock_glfw.destroy_window.assert_called_once_with(mock_window)
    mock_glfw.terminate.assert_called_once()
