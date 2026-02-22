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
    manifest = PluginInfo(**METADATA)
    assert manifest.name == "Depth Loop Injection"
    assert "pre_loop_mix" in [p["name"] for p in manifest.parameters]
    assert "video_in" in manifest.inputs
    assert "video_out" in manifest.outputs

def test_depth_loop_bypassed():
    plugin = DepthLoopInjectionPlugin()
    ctx_empty = MockContext()
    plugin.initialize(ctx_empty)
    
    val = plugin.process_frame(100, {}, ctx_empty)
    assert val == 100
    
    ctx = MockContext(inputs={"video_in": 100}, parameters={})
    res = plugin.process_frame(100, {"pre_loop_mix": 1.0, "depth_loop_mix": 0.5, "mosh_loop_mix": 1.0, "post_loop_mix": 0.5}, ctx)
    
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
    assert res == 300
    assert ctx.outputs["pre_send"] == 100

def setup_mock_gl(monkeypatch):
    mock_gl = MagicMock()
    mock_gl.glGenTextures.return_value = [1, 2, 3, 4, 5, 6]
    mock_gl.glGenFramebuffers.return_value = [10, 20, 30, 40, 50, 60]
    mock_gl.GL_TRUE = 1
    mock_gl.glGetShaderiv.return_value = 1
    mock_gl.glGetTexLevelParameteriv.return_value = 1920
    monkeypatch.setattr(dli, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dli, 'HAS_GL', True)
    return mock_gl

def test_depth_loop_fbo_cleanup_headless(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    
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
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGenTextures.return_value = 99
    mock_gl.glGenFramebuffers.return_value = 100
    
    plugin = DepthLoopInjectionPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    assert plugin.textures["pre_send"] == 99

def test_depth_loop_gl_exception_handling(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGenTextures.side_effect = Exception("Out of Memory")
    
    plugin = DepthLoopInjectionPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    
    plugin.initialize(ctx)
    assert plugin._mock_mode is True
    assert plugin.textures["pre_send"] is None
    
    mock_gl.glGenTextures.side_effect = None
    mock_gl.glGenTextures.return_value = 1
    mock_gl.glGenFramebuffers.return_value = 2
    
    plugin2 = DepthLoopInjectionPlugin()
    plugin2._mock_mode = False
    plugin2.initialize(ctx)
    
    mock_gl.glDeleteTextures.side_effect = Exception("Segmentation Fault")
    plugin2.cleanup()
    assert plugin2.textures["pre_send"] is None

def test_depth_loop_render_frame(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthLoopInjectionPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    assert plugin.prog is not None
    
    # Process with full parameters to hit all uniform bindings
    params = {
        "pre_loop_mix": 1.0,
        "depth_loop_mix": 1.0,
        "mosh_loop_mix": 1.0,
        "post_loop_mix": 1.0,
        "depth_modulation": 0.5,
        "depth_threshold": 0.5,
        "invert_depth": 1,
        "datamosh_intensity": 0.5,
        "mosh_threshold": 0.3,
        "block_size": 0.4,
        "feedback_amount": 0.8,
        "u_mix": 1.0
    }
    
    # Run once to hit the setup
    res1 = plugin.process_frame(100, params, ctx)
    assert res1 == 6 # Ping pong 0 texture is 5, 1 is 6
    assert plugin.ping_pong == 1
    
    # Run again to hit the other ping-pong buffer
    mock_gl.glGetTexLevelParameteriv.return_value = 1920 # size didn't change!
    res2 = plugin.process_frame(100, params, ctx)
    assert res2 == 5

    # Run again with a resized texture!
    mock_gl.glGetTexLevelParameteriv.return_value = 800
    res3 = plugin.process_frame(100, params, ctx)
    assert res3 == 6

    # Test edge case: Process with None texture
    res4 = plugin.process_frame(0, params, ctx)
    assert res4 == 0

def test_compile_shader_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGetShaderiv.return_value = 0 # Fail
    mock_gl.glGetShaderInfoLog.return_value = "ERROR"
    
    plugin = DepthLoopInjectionPlugin()
    res = plugin._compile_shader()
    assert res is None

def test_process_frame_render_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthLoopInjectionPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    mock_gl.glBindTexture.side_effect = Exception("Render fail")
    res = plugin.process_frame(100, {}, ctx)
    assert res == 100 # Returns input on fail

