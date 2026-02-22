import os
import pytest
from unittest.mock import patch, MagicMock

# Force headless override before the module imports to mimic VJ_HEADLESS loading 
# since module level code evaluates HEADLESS early.
os.environ["VJ_HEADLESS"] = "true"

from vjlive3.render.opengl_context import OpenGLContext
import vjlive3.render.opengl_context as opengl_ctx

@pytest.fixture(autouse=True)
def force_headless_globals():
    """Ensure testing env global state defaults back to headless cleanly off-tests."""
    opengl_ctx.HEADLESS = True
    opengl_ctx.HAS_GLFW = False

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
        # Temporarily force HAS_GLFW and reset HEADLESS just for this failure check
        opengl_ctx.HEADLESS = False
        opengl_ctx.HAS_GLFW = True
        OpenGLContext(headless=False)

@patch('vjlive3.render.opengl_context.glfw')
def test_glfw_window_failure(mock_glfw):
    """create_window fails -> raises RuntimeError and calls terminate"""
    mock_glfw.init.return_value = True
    mock_glfw.create_window.return_value = None
    
    with pytest.raises(RuntimeError, match="GLFW window creation failed"):
        opengl_ctx.HEADLESS = False
        opengl_ctx.HAS_GLFW = True
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
        opengl_ctx.HEADLESS = False
        opengl_ctx.HAS_GLFW = True
        OpenGLContext(headless=False)
            
    mock_glfw.destroy_window.assert_called_once_with(mock_window)
    mock_glfw.terminate.assert_called_once()

@patch('vjlive3.render.opengl_context.glfw')
@patch('vjlive3.render.opengl_context.moderngl')
def test_windowed_methods(mock_mgl, mock_glfw):
    """Verifies that actual window method calls propagate to GLFW correctly."""
    mock_glfw.init.return_value = True
    mock_window = MagicMock()
    mock_glfw.create_window.return_value = mock_window
    
    mock_mgl_ctx = MagicMock()
    mock_mgl.create_context.return_value = mock_mgl_ctx
    
    opengl_ctx.HEADLESS = False
    opengl_ctx.HAS_GLFW = True
    
    ctx = OpenGLContext(headless=False)
    
    ctx.make_current()
    mock_glfw.make_context_current.assert_called_with(mock_window)
    
    ctx.poll_events()
    mock_glfw.poll_events.assert_called_once()
    
    mock_glfw.window_should_close.return_value = True
    assert ctx.should_close() is True
    
    ctx.swap_buffers()
    mock_glfw.swap_buffers.assert_called_with(mock_window)
    
    ctx.terminate()
    mock_mgl_ctx.release.assert_called_once()
    mock_glfw.destroy_window.assert_called_with(mock_window)
    mock_glfw.terminate.assert_called()

import sys
import importlib

def test_module_load_no_glfw():
    """Forces an ImportError during module load to hit the fallback."""
    original_glfw = sys.modules.get('glfw')
    sys.modules['glfw'] = None
    try:
        with patch.dict(os.environ, {"VJ_HEADLESS": "false"}):
            import vjlive3.render.opengl_context as mod
            importlib.reload(mod)
            assert mod.HAS_GLFW is False
    finally:
        if original_glfw is not None:
            sys.modules['glfw'] = original_glfw
        elif 'glfw' in sys.modules:
            del sys.modules['glfw']
        # Restore module state to safe headless defaults for other tests
        with patch.dict(os.environ, {"VJ_HEADLESS": "true"}):
            import vjlive3.render.opengl_context as mod
            importlib.reload(mod)
