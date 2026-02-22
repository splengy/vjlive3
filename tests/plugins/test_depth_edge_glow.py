import pytest
import sys
from unittest.mock import MagicMock

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.plugins.depth_edge_glow as deg
from vjlive3.plugins.depth_edge_glow import DepthEdgeGlowPlugin, METADATA
from vjlive3.plugins.registry import PluginInfo

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.plugins.depth_edge_glow.HAS_GL', False)

class MockContext:
    def __init__(self, inputs=None, parameters=None):
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.outputs = {}

def test_depth_edge_glow_manifest():
    manifest = PluginInfo(**METADATA)
    assert manifest.name == "Depth Edge Glow"
    assert "edgeThreshold" in [p["name"] for p in manifest.parameters]
    assert "video_in" in manifest.inputs
    assert "depth_in" in manifest.inputs
    assert "video_out" in manifest.outputs

def test_depth_edge_glow_bypassed():
    plugin = DepthEdgeGlowPlugin()
    ctx_empty = MockContext()
    plugin.initialize(ctx_empty)
    
    val = plugin.process_frame(100, {}, ctx_empty)
    assert val == 100
    
    ctx = MockContext(inputs={"video_in": 100}, parameters={})
    res = plugin.process_frame(100, {"edgeThreshold": 1.0}, ctx)
    assert ctx.outputs["video_out"] == 100

def test_depth_edge_glow_missing_video():
    plugin = DepthEdgeGlowPlugin()
    ctx = MockContext()
    
    plugin.initialize(ctx)
    val = plugin.process_frame(None, {}, ctx)
    assert val == 0
    val2 = plugin.process_frame(0, {}, ctx)
    assert val2 == 0

def setup_mock_gl(monkeypatch):
    mock_gl = MagicMock()
    mock_gl.glGenTextures.return_value = 1
    mock_gl.glGenFramebuffers.return_value = 10
    mock_gl.GL_TRUE = 1
    mock_gl.glGetShaderiv.return_value = 1
    mock_gl.glGetTexLevelParameteriv.return_value = 1920
    monkeypatch.setattr(deg, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(deg, 'HAS_GL', True)
    return mock_gl

def test_depth_edge_glow_fbo_cleanup(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    
    plugin = DepthEdgeGlowPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    assert plugin.texture == 1
    assert plugin.fbo == 10
    
    plugin.cleanup()
    
    mock_gl.glDeleteTextures.assert_called_once_with(1, [1])
    mock_gl.glDeleteFramebuffers.assert_called_once_with(1, [10])
    assert plugin.texture is None

def test_depth_edge_glow_gl_exception_handling(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGenTextures.side_effect = Exception("Out of Memory")
    
    plugin = DepthEdgeGlowPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    
    plugin.initialize(ctx)
    assert plugin._mock_mode is True
    assert plugin.texture is None
    
    mock_gl.glGenTextures.side_effect = None
    mock_gl.glGenTextures.return_value = 1
    mock_gl.glGenFramebuffers.return_value = 2
    
    plugin2 = DepthEdgeGlowPlugin()
    plugin2._mock_mode = False
    plugin2.initialize(ctx)
    
    mock_gl.glDeleteTextures.side_effect = Exception("Segmentation Fault")
    plugin2.cleanup()
    assert plugin2.texture is None

def test_depth_edge_glow_render_frame(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthEdgeGlowPlugin()
    plugin._mock_mode = False
    ctx = MockContext(inputs={"depth_in": 200})
    plugin.initialize(ctx)
    
    assert plugin.prog is not None
    
    params = {
        "edgeThreshold": 5.0,
        "edgeThickness": 5.0,
        "glowRadius": 5.0,
        "glowIntensity": 5.0,
        "contourLines": 5.0,
        "contourWidth": 5.0,
        "hueMode": 5.0,
        "edgeColorR": 5.0,
        "edgeColorG": 5.0,
        "edgeColorB": 5.0,
        "pulseSpeed": 5.0,
        "pulseAmount": 5.0,
        "sourceDim": 5.0,
        "innerGlow": 5.0,
        "u_mix": 0.5
    }
    
    res1 = plugin.process_frame(100, params, ctx)
    assert res1 == 1 
    
    mock_gl.glGetTexLevelParameteriv.return_value = 1920
    res2 = plugin.process_frame(100, params, ctx)
    assert res2 == 1

    mock_gl.glGetTexLevelParameteriv.return_value = 800
    res3 = plugin.process_frame(100, params, ctx)
    assert res3 == 1

def test_compile_shader_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGetShaderiv.return_value = 0 # Fail
    mock_gl.glGetShaderInfoLog.return_value = "ERROR"
    
    plugin = DepthEdgeGlowPlugin()
    res = plugin._compile_shader()
    assert res is None

def test_process_frame_render_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthEdgeGlowPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    mock_gl.glBindTexture.side_effect = Exception("Render fail")
    res = plugin.process_frame(100, {}, ctx)
    assert res == 100 # Returns input on fail
