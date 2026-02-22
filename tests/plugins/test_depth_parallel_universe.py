import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.plugins.depth_parallel_universe as dpu
from vjlive3.plugins.depth_parallel_universe import DepthParallelUniversePlugin, METADATA
from vjlive3.plugins.registry import PluginInfo

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.plugins.depth_parallel_universe.HAS_GL', False)

class MockContext:
    def __init__(self, inputs=None, parameters=None):
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.outputs = {}

def test_parallel_universe_manifest():
    manifest = PluginInfo(**METADATA)
    assert manifest.name == "Depth Parallel Universe"
    assert "universe_a_intensity" in [p["name"] for p in manifest.parameters]
    assert "universe_c_send" in manifest.outputs

def test_parallel_universe_split_clamp():
    plugin = DepthParallelUniversePlugin()
    ctx = MockContext()
    plugin.initialize(ctx)
    
    params = {
        "depth_split_near": 0.8, # Invalid logic, near > far
        "depth_split_far": 0.2
    }
    plugin.process_frame(100, params, ctx)
    
    # Assert clamped boundaries inverted back to sanity
    assert params["_clamped_near"] == 0.2
    assert params["_clamped_far"] == 0.8

def test_parallel_universe_bypassed():
    plugin = DepthParallelUniversePlugin()
    ctx_empty = MockContext()
    plugin.initialize(ctx_empty)
    
    val = plugin.process_frame(100, {}, ctx_empty)
    assert val == 100
    
    ctx = MockContext(
        inputs={"video_in": 100}, 
        parameters={}
    )
    res = plugin.process_frame(100, {"universe_a_intensity": 1.0, "universe_b_intensity": 1.0, "universe_c_intensity": 1.0}, ctx)
    assert res == 100
    assert ctx.outputs["universe_a_send"] == 100

def test_parallel_universe_processing_mock_injection():
    plugin = DepthParallelUniversePlugin()
    ctx = MockContext(
        inputs={"video_in": 100, "universe_a_return": 200, "universe_b_return": 300},
        parameters={}
    )
    plugin.initialize(ctx)
    
    res = plugin.process_frame(100, {"universe_a_intensity": 1.0, "universe_b_intensity": 1.0, "universe_c_intensity": 0.0}, ctx)
    assert res == 200 # Universe A return
    assert ctx.outputs["universe_b_send"] == 100

def test_parallel_universe_fbo_cleanup_headless(monkeypatch):
    mock_gl = MagicMock()
    mock_gl.glGenTextures.return_value = [1, 2, 3, 4, 5, 6]
    mock_gl.glGenFramebuffers.return_value = [10, 20, 30, 40, 50, 60]
    
    monkeypatch.setattr(dpu, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dpu, 'HAS_GL', True)
    
    plugin = DepthParallelUniversePlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    assert plugin.textures["universe_a_send"] == 1
    assert plugin.fbos["universe_a_send"] == 10
    
    plugin.cleanup()
    mock_gl.glDeleteTextures.assert_called_once_with(6, [1, 2, 3, 4, 5, 6])
    mock_gl.glDeleteFramebuffers.assert_called_once_with(6, [10, 20, 30, 40, 50, 60])
    
def test_parallel_universe_fbo_cleanup_single_ints(monkeypatch):
    mock_gl = MagicMock()
    mock_gl.glGenTextures.return_value = 99
    mock_gl.glGenFramebuffers.return_value = 100
    
    monkeypatch.setattr(dpu, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dpu, 'HAS_GL', True)
    
    plugin = DepthParallelUniversePlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    assert plugin.textures["universe_a_send"] == 99

def test_parallel_universe_gl_exception_handling(monkeypatch):
    mock_gl = MagicMock()
    mock_gl.glGenTextures.side_effect = Exception("Out of Memory")
    
    monkeypatch.setattr(dpu, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dpu, 'HAS_GL', True)
    
    plugin = DepthParallelUniversePlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    
    plugin.initialize(ctx)
    assert plugin._mock_mode is True
    
    mock_gl.glGenTextures.side_effect = None
    mock_gl.glGenTextures.return_value = 1
    mock_gl.glGenFramebuffers.return_value = 2
    
    plugin2 = DepthParallelUniversePlugin()
    plugin2._mock_mode = False
    plugin2.initialize(ctx)
    
    mock_gl.glDeleteTextures.side_effect = Exception("Segmentation Fault")
    plugin2.cleanup()
    assert plugin2.textures["universe_a_send"] is None
