import pytest
import sys
from unittest.mock import MagicMock

# Force mock OpenGL before loading
sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.plugins.depth_dual as dd
from vjlive3.plugins.depth_dual import DepthDualPlugin, METADATA
from vjlive3.plugins.registry import PluginInfo

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.plugins.depth_dual.HAS_GL', False)

class MockContext:
    def __init__(self, inputs=None, parameters=None):
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.outputs = {}

def test_depth_dual_manifest():
    manifest = PluginInfo(**METADATA)
    assert manifest.name == "Depth Dual"
    assert "interactionMode" in [p["name"] for p in manifest.parameters]
    assert "video_in" in manifest.inputs
    assert "depth_in_a" in manifest.inputs
    assert "depth_in_b" in manifest.inputs
    assert "video_out" in manifest.outputs

def test_depth_dual_bypassed():
    plugin = DepthDualPlugin()
    ctx_empty = MockContext()
    plugin.initialize(ctx_empty)
    
    val = plugin.process_frame(100, {}, ctx_empty)
    assert val == 100
    
    ctx = MockContext(inputs={"video_in": 100}, parameters={})
    res = plugin.process_frame(100, {"interactionMode": 1.0}, ctx)
    assert ctx.outputs["video_out"] == 100

def test_depth_dual_missing_video():
    plugin = DepthDualPlugin()
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
    monkeypatch.setattr(dd, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dd, 'HAS_GL', True)
    return mock_gl

def test_depth_dual_fbo_cleanup_headless(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    
    plugin = DepthDualPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    assert plugin.textures["feedback_0"] == 1
    assert plugin.fbos["feedback_0"] == 10
    
    plugin.cleanup()
    
    mock_gl.glDeleteTextures.assert_called_once_with(2, [1, 2])
    mock_gl.glDeleteFramebuffers.assert_called_once_with(2, [10, 20])
    assert plugin.textures["feedback_0"] is None

def test_depth_dual_fbo_cleanup_single_ints(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGenTextures.return_value = 99
    mock_gl.glGenFramebuffers.return_value = 100
    
    plugin = DepthDualPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    assert plugin.textures["feedback_0"] == 99
    assert plugin.textures["feedback_1"] == 100

def test_depth_dual_gl_exception_handling(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGenTextures.side_effect = Exception("Out of Memory")
    
    plugin = DepthDualPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    
    plugin.initialize(ctx)
    assert plugin._mock_mode is True
    assert plugin.textures["feedback_0"] is None
    
    mock_gl.glGenTextures.side_effect = None
    mock_gl.glGenTextures.return_value = 1
    mock_gl.glGenFramebuffers.return_value = 2
    
    plugin2 = DepthDualPlugin()
    plugin2._mock_mode = False
    plugin2.initialize(ctx)
    
    mock_gl.glDeleteTextures.side_effect = Exception("Segmentation Fault")
    plugin2.cleanup()
    assert plugin2.textures["feedback_0"] is None

def test_depth_dual_render_frame(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthDualPlugin()
    plugin._mock_mode = False
    ctx = MockContext(inputs={"depth_in_a": 200, "depth_in_b": 300})
    plugin.initialize(ctx)
    
    assert plugin.prog is not None
    
    params = {
        "interactionMode": 1.0,
        "interactionAmount": 5.0,
        "depthAlign": 5.0,
        "depthScaleB": 5.0,
        "collisionGlow": 5.0,
        "collisionWidth": 5.0,
        "collisionHue": 5.0,
        "interferenceFreq": 5.0,
        "interferencePhase": 5.0,
        "volumeDensity": 5.0,
        "volumeAbsorption": 5.0,
        "edgeEnhance": 5.0,
        "colorDepthA": 5.0,
        "colorDepthB": 5.0,
        "feedback": 5.0,
        "u_mix": 0.5
    }
    
    res1 = plugin.process_frame(100, params, ctx)
    assert res1 == 2 # Ping pong 0 texture is 1, 1 is 2
    assert plugin.ping_pong == 1
    
    mock_gl.glGetTexLevelParameteriv.return_value = 1920
    res2 = plugin.process_frame(100, params, ctx)
    assert res2 == 1

    mock_gl.glGetTexLevelParameteriv.return_value = 800
    res3 = plugin.process_frame(100, params, ctx)
    assert res3 == 2

def test_compile_shader_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGetShaderiv.return_value = 0 # Fail
    mock_gl.glGetShaderInfoLog.return_value = "ERROR"
    
    plugin = DepthDualPlugin()
    res = plugin._compile_shader()
    assert res is None

def test_process_frame_render_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthDualPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    mock_gl.glBindTexture.side_effect = Exception("Render fail")
    res = plugin.process_frame(100, {}, ctx)
    assert res == 100 # Returns input on fail
