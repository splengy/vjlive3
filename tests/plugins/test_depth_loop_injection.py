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
from vjlive3.plugins.registry import Manifest

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
    manifest = Manifest(**METADATA)
    assert manifest.name == "Depth Loop Injection"
    assert "pre_loop_mix" in [p.name for p in manifest.parameters]
    assert "video_in" in manifest.inputs
    assert "video_out" in manifest.outputs

def test_depth_loop_bypassed(mock_api):
    plugin = DepthLoopInjectionPlugin(mock_api)
    plugin.on_load()
    
    # Empty inputs should return safely
    ctx_empty = MockContext()
    plugin.process(ctx_empty)
    assert not ctx_empty.outputs
    
    # Supplied video but no return textures
    ctx = MockContext(
        inputs={"video_in": 100}, 
        parameters={"pre_loop_mix": 1.0, "depth_loop_mix": 0.5, "mosh_loop_mix": 1.0, "post_loop_mix": 0.5}
    )
    
    plugin.process(ctx)
    
    # Bypasses the returns to output the base signal cleanly
    assert ctx.outputs["video_out"] == 100
    assert ctx.outputs["pre_send"] == 100

def test_depth_loop_processing_mock_injection(mock_api):
    plugin = DepthLoopInjectionPlugin(mock_api)
    plugin.on_load()
    
    ctx = MockContext(
        inputs={"video_in": 100, "pre_return": 200, "depth_return": 300},
        parameters={"pre_loop_mix": 1.0, "depth_loop_mix": 1.0, "mosh_loop_mix": 0.0}
    )
    plugin.process(ctx)
    assert ctx.outputs["video_out"] == 300 # Mosh loop mix is 0 so it bypasses to depth return
    assert ctx.outputs["pre_send"] == 100

def test_depth_loop_fbo_cleanup_headless(monkeypatch, mock_api):
    mock_gl = MagicMock()
    mock_gl.glGenTextures.return_value = [1, 2, 3, 4, 5, 6]
    mock_gl.glGenFramebuffers.return_value = [10, 20, 30, 40, 50, 60]
    
    monkeypatch.setattr(dli, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dli, 'HAS_GL', True)
    
    plugin = DepthLoopInjectionPlugin(mock_api)
    plugin._mock_mode = False
    
    plugin.on_load()
    assert plugin.textures["pre_send"] == 1
    assert plugin.fbos["pre_send"] == 10
    
    plugin.on_unload()
    
    mock_gl.glDeleteTextures.assert_called_once_with(6, [1, 2, 3, 4, 5, 6])
    mock_gl.glDeleteFramebuffers.assert_called_once_with(6, [10, 20, 30, 40, 50, 60])
    assert plugin.textures["pre_send"] is None

def test_depth_loop_fbo_cleanup_single_ints(monkeypatch, mock_api):
    """Test when PyOpenGL returns a single integer instead of arrays"""
    mock_gl = MagicMock()
    mock_gl.glGenTextures.return_value = 99
    mock_gl.glGenFramebuffers.return_value = 100
    
    monkeypatch.setattr(dli, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dli, 'HAS_GL', True)
    
    plugin = DepthLoopInjectionPlugin(mock_api)
    plugin._mock_mode = False
    plugin.on_load()
    
    assert plugin.textures["pre_send"] == 99
    assert plugin.fbos["pre_send"] == 100
