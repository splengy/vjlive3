import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.plugins.depth_reverb as dr
from vjlive3.plugins.depth_reverb import DepthReverbPlugin, METADATA
from vjlive3.plugins.registry import PluginInfo

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.plugins.depth_reverb.HAS_GL', False)

class MockContext:
    def __init__(self, inputs=None, parameters=None):
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.outputs = {}
        self.render_width = 1920
        self.render_height = 1080

def test_depth_reverb_manifest():
    manifest = PluginInfo(**METADATA)
    assert manifest.name == "Depth Reverb"
    assert "decay_time" in [p["name"] for p in manifest.parameters]
    assert "video_out" in manifest.outputs

def test_depth_reverb_resolution_change():
    plugin = DepthReverbPlugin()
    ctx = MockContext(inputs={"video_in": 100})
    plugin.initialize(ctx)
    
    # Process First Frame
    val = plugin.process_frame(100, {}, ctx)
    assert val == 100
    assert plugin._current_width == 1920
    assert plugin.texture_prev == 999 # mock ping
    
    # Process Frame with resize simulation
    ctx.render_width = 1280
    ctx.render_height = 720
    val2 = plugin.process_frame(100, {}, ctx)
    assert val2 == 100
    assert plugin._current_width == 1280

def test_depth_reverb_no_depth_bypassed():
    plugin = DepthReverbPlugin()
    ctx = MockContext(inputs={"video_in": 100}) # Missing depth_in
    plugin.initialize(ctx)
    
    params = {}
    val = plugin.process_frame(100, params, ctx)
    
    assert val == 100
    assert params["_uniform_reverb"] is True

def test_depth_reverb_with_depth_processed():
    plugin = DepthReverbPlugin()
    ctx = MockContext(inputs={"video_in": 100, "depth_in": 200})
    plugin.initialize(ctx)
    
    params = {}
    val = plugin.process_frame(100, params, ctx)
    
    assert val == 100
    assert params["_uniform_reverb"] is False

def test_depth_reverb_empty_returns_0():
    plugin = DepthReverbPlugin()
    ctx = MockContext()
    plugin.initialize(ctx)
    val = plugin.process_frame(None, {}, ctx)
    assert val == 0

def test_depth_reverb_fbo_lifecycle(monkeypatch):
    mock_gl = MagicMock()
    mock_gl.glGenTextures.return_value = [101, 102]
    mock_gl.glGenFramebuffers.return_value = [201, 202]
    
    monkeypatch.setattr(dr, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dr, 'HAS_GL', True)
    
    plugin = DepthReverbPlugin()
    plugin._mock_mode = False
    ctx = MockContext(inputs={"video_in": 100})
    plugin.initialize(ctx)
    
    # Initial trigger to allocate FBO
    plugin.process_frame(100, {}, ctx)
    assert plugin.texture_prev == 101
    assert plugin.fbo_ping == 201
    
    # Verify cleanup runs properly
    plugin.cleanup()
    mock_gl.glDeleteTextures.assert_called_once_with(2, [101, 102])
    mock_gl.glDeleteFramebuffers.assert_called_once_with(2, [201, 202])
    
def test_depth_reverb_exception_handling(monkeypatch):
    mock_gl = MagicMock()
    mock_gl.glGenTextures.side_effect = Exception("Out of Memory GL")
    
    monkeypatch.setattr(dr, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dr, 'HAS_GL', True)
    
    plugin = DepthReverbPlugin()
    plugin._mock_mode = False
    ctx = MockContext(inputs={"video_in": 100})
    plugin.initialize(ctx)
    
    # Trigger bad allocation causing mock mode downgrade
    plugin.process_frame(100, {}, ctx)
    assert plugin._mock_mode is True
    
    # Check teardown logic failure states
    mock_gl.glGenTextures.side_effect = None
    mock_gl.glGenTextures.return_value = [1, 2]
    mock_gl.glGenFramebuffers.return_value = [3, 4]
    
    plugin2 = DepthReverbPlugin()
    plugin2._mock_mode = False
    plugin2.initialize(ctx)
    plugin2.process_frame(100, {}, ctx)
    
    mock_gl.glDeleteTextures.side_effect = Exception("Segmentation Fault")
    plugin2.cleanup() # Must not crash
    assert plugin2.texture_prev is None
    
def test_depth_reverb_single_int_fbo_handling(monkeypatch):
    mock_gl = MagicMock()
    mock_gl.glGenTextures.return_value = 555
    mock_gl.glGenFramebuffers.return_value = 666
    
    monkeypatch.setattr(dr, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dr, 'HAS_GL', True)
    
    plugin = DepthReverbPlugin()
    plugin._mock_mode = False
    ctx = MockContext(inputs={"video_in": 100})
    plugin.initialize(ctx)
    plugin.process_frame(100, {}, ctx)
    
    assert plugin.texture_prev == 555
