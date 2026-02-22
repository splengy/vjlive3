import pytest
import sys
from unittest.mock import MagicMock

# Force mock OpenGL before loading
sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.plugins.depth_distance_filter as ddf
from vjlive3.plugins.depth_distance_filter import DepthDistanceFilterPlugin, METADATA
from vjlive3.plugins.registry import PluginInfo

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.plugins.depth_distance_filter.HAS_GL', False)

class MockContext:
    def __init__(self, inputs=None, parameters=None):
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.outputs = {}

def test_distance_filter_manifest():
    manifest = PluginInfo(**METADATA)
    assert manifest.name == "Depth Distance Filter"
    assert "nearClip" in [p["name"] for p in manifest.parameters]
    assert "video_in" in manifest.inputs
    assert "depth_in" in manifest.inputs
    assert "tex_b" in manifest.inputs
    assert "video_out" in manifest.outputs

def test_distance_filter_bypassed():
    plugin = DepthDistanceFilterPlugin()
    ctx_empty = MockContext()
    plugin.initialize(ctx_empty)
    
    val = plugin.process_frame(100, {}, ctx_empty)
    assert val == 100
    
    ctx = MockContext(inputs={"video_in": 100}, parameters={})
    res = plugin.process_frame(100, {"invert": 1.0}, ctx)
    
    assert ctx.outputs["video_out"] == 100

def test_distance_filter_missing_video():
    plugin = DepthDistanceFilterPlugin()
    ctx = MockContext()
    
    plugin.initialize(ctx)
    val = plugin.process_frame(None, {}, ctx)
    assert val == 0
    val2 = plugin.process_frame(0, {}, ctx)
    assert val2 == 0

def setup_mock_gl(monkeypatch):
    mock_gl = MagicMock()
    mock_gl.glGenTextures.return_value = [1, 2]
    mock_gl.glGenFramebuffers.return_value = [10, 20]
    mock_gl.GL_TRUE = 1
    mock_gl.glGetShaderiv.return_value = 1
    mock_gl.glGetTexLevelParameteriv.return_value = 1920
    monkeypatch.setattr(ddf, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(ddf, 'HAS_GL', True)
    return mock_gl

def test_distance_filter_fbo_cleanup_headless(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    
    plugin = DepthDistanceFilterPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    assert plugin.textures["feedback_0"] == 1
    assert plugin.fbos["feedback_0"] == 10
    
    plugin.cleanup()
    
    mock_gl.glDeleteTextures.assert_called_once_with(2, [1, 2])
    mock_gl.glDeleteFramebuffers.assert_called_once_with(2, [10, 20])
    assert plugin.textures["feedback_0"] is None

def test_distance_filter_fbo_cleanup_single_ints(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGenTextures.return_value = 99
    mock_gl.glGenFramebuffers.return_value = 100
    
    plugin = DepthDistanceFilterPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    assert plugin.textures["feedback_0"] == 99
    assert plugin.textures["feedback_1"] == 100

def test_distance_filter_gl_exception_handling(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGenTextures.side_effect = Exception("Out of Memory")
    
    plugin = DepthDistanceFilterPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    
    plugin.initialize(ctx)
    assert plugin._mock_mode is True
    assert plugin.textures["feedback_0"] is None
    
    mock_gl.glGenTextures.side_effect = None
    mock_gl.glGenTextures.return_value = 1
    mock_gl.glGenFramebuffers.return_value = 2
    
    plugin2 = DepthDistanceFilterPlugin()
    plugin2._mock_mode = False
    plugin2.initialize(ctx)
    
    mock_gl.glDeleteTextures.side_effect = Exception("Segmentation Fault")
    plugin2.cleanup()
    assert plugin2.textures["feedback_0"] is None

def test_distance_filter_render_frame(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthDistanceFilterPlugin()
    plugin._mock_mode = False
    ctx = MockContext(inputs={"depth_in": 200, "tex_b": 300})
    plugin.initialize(ctx)
    
    assert plugin.prog is not None
    
    # Process with parameters to hit uniform bindings
    params = {
        "nearClip": 5.0,
        "farClip": 5.0,
        "edgeSoftness": 5.0,
        "invert": 6.0,
        "fillMode": 5.0,
        "fillColorR": 5.0,
        "fillColorG": 5.0,
        "fillColorB": 5.0,
        "edgeRefine": 5.0,
        "smoothing": 5.0,
        "showMask": 6.0,
        "depthColorize": 5.0,
        "u_mix": 0.5
    }
    
    # Run once to hit the setup
    res1 = plugin.process_frame(100, params, ctx)
    assert res1 == 2 # Ping pong 0 texture is 1, 1 is 2
    assert plugin.ping_pong == 1
    
    # Run again to hit the other ping-pong buffer
    mock_gl.glGetTexLevelParameteriv.return_value = 1920 # size didn't change!
    res2 = plugin.process_frame(100, params, ctx)
    assert res2 == 1

    # Run again with a resized texture!
    mock_gl.glGetTexLevelParameteriv.return_value = 800
    res3 = plugin.process_frame(100, params, ctx)
    assert res3 == 2

def test_compile_shader_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGetShaderiv.return_value = 0 # Fail
    mock_gl.glGetShaderInfoLog.return_value = "ERROR"
    
    plugin = DepthDistanceFilterPlugin()
    res = plugin._compile_shader()
    assert res is None

def test_process_frame_render_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthDistanceFilterPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    mock_gl.glBindTexture.side_effect = Exception("Render fail")
    res = plugin.process_frame(100, {}, ctx)
    assert res == 100 # Returns input on fail
