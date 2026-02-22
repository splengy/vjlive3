import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

# Force mock OpenGL before loading
sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.plugins.depth_loop_injection as dli
from vjlive3.plugins.depth_loop_injection import DepthLoopInjectionPlugin, METADATA
from vjlive3.plugins.registry import PluginInfo

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.plugins.depth_loop_injection.HAS_GL', False)

@pytest.fixture
def mock_api():
    return MagicMock()

class MockContext:
    def __init__(self, inputs=None, parameters=None):
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.outputs = {}

def test_depth_loop_injection_manifest():
    """Verify METADATA maps cleanly to the expected Pydantic schema."""
    manifest = PluginInfo(**METADATA)
    assert manifest.name == "Depth Loop Injection"
    # parameters is a list of dicts, not objects
    assert "pre_loop_mix" in [p["name"] for p in manifest.parameters]
    assert "video_in" in manifest.inputs
    assert "video_out" in manifest.outputs

def test_depth_loop_bypassed():
    plugin = DepthLoopInjectionPlugin()
    
    # Initialize properly via API base
    ctx_empty = MockContext()
    plugin.initialize(ctx_empty)
    
    # Empty inputs should return safely
    val = plugin.process_frame(100, {}, ctx_empty)
    # The _mock_passthrough automatically pushes current_tex to all outputs even with empty mixing dicts.
    assert val == 100
    
    # Supplied video but no return textures
    ctx = MockContext(
        inputs={"video_in": 100}, 
        parameters={}
    )
    
    res = plugin.process_frame(100, {"pre_loop_mix": 1.0, "depth_loop_mix": 0.5, "mosh_loop_mix": 1.0, "post_loop_mix": 0.5}, ctx)
    
    # Bypasses the returns to output the base signal cleanly
    assert ctx.outputs["video_out"] == 100
    assert ctx.outputs["pre_send"] == 100

def test_depth_loop_processing_mock_injection():
    plugin = DepthLoopInjectionPlugin()
    ctx = MockContext(
        inputs={"video_in": 100, "pre_return": 200, "depth_return": 300},
        parameters={}
    )
    plugin.initialize(ctx)
    
    res = plugin.process_frame(100, {"pre_loop_mix": 1.0, "depth_loop_mix": 1.0, "mosh_loop_mix": 0.0, "post_loop_mix": 0.0}, ctx)
    assert res == 300 # Mosh loop mix is 0 so it bypasses to depth return (300). Post is 0 so bypasses to current (300).
    assert ctx.outputs["pre_send"] == 100

def test_depth_loop_fbo_cleanup_headless(monkeypatch):
    mock_gl = MagicMock()
    mock_gl.glGenTextures.return_value = [1, 2, 3, 4, 5, 6]
    mock_gl.glGenFramebuffers.return_value = [10, 20, 30, 40, 50, 60]
    
    monkeypatch.setattr(dli, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dli, 'HAS_GL', True)
    
    plugin = DepthLoopInjectionPlugin()
    plugin._mock_mode = False
    
    ctx = MockContext()
    plugin.initialize(ctx)
    assert plugin.textures["pre_send"] == 1
    assert plugin.fbos["pre_send"] == 10
    
    plugin.cleanup()
    
    mock_gl.glDeleteTextures.assert_called_once_with(6, [1, 2, 3, 4, 5, 6])
    mock_gl.glDeleteFramebuffers.assert_called_once_with(6, [10, 20, 30, 40, 50, 60])
    assert plugin.textures["pre_send"] is None

def test_depth_loop_fbo_cleanup_single_ints(monkeypatch):
    """Test when PyOpenGL returns a single integer instead of arrays"""
    mock_gl = MagicMock()
    mock_gl.glGenTextures.return_value = 99
    mock_gl.glGenFramebuffers.return_value = 100
    
    monkeypatch.setattr(dli, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dli, 'HAS_GL', True)
    
    plugin = DepthLoopInjectionPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    assert plugin.textures["pre_send"] == 99
def test_depth_loop_gl_exception_handling(monkeypatch):
    """Test standard exceptions thrown during PyOpenGL initializations cleanly fallback."""
    mock_gl = MagicMock()
    mock_gl.glGenTextures.side_effect = Exception("Out of Memory")
    
    monkeypatch.setattr(dli, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dli, 'HAS_GL', True)
    
    plugin = DepthLoopInjectionPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    
    # Should fallback to mock mode safely
    plugin.initialize(ctx)
    assert plugin._mock_mode is True
    assert plugin.textures["pre_send"] is None
    
    # Check shutdown exceptions
    mock_gl.glGenTextures.side_effect = None
    mock_gl.glGenTextures.return_value = 1
    mock_gl.glGenFramebuffers.return_value = 2
    
    plugin2 = DepthLoopInjectionPlugin()
    plugin2._mock_mode = False
    plugin2.initialize(ctx)
    
    mock_gl.glDeleteTextures.side_effect = Exception("Segmentation Fault")
    # Should not crash the main thread
    plugin2.cleanup()
    assert plugin2.textures["pre_send"] is None
