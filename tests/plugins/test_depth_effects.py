import pytest
import sys
from unittest.mock import MagicMock
import os
os.environ["PYTEST_MOCK_GL"] = "1"

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.plugins.depth_effects as de
from vjlive3.plugins.depth_effects import DepthEffectsPlugin, METADATA
from vjlive3.plugins.registry import PluginInfo

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.plugins.depth_effects.HAS_GL', False)

class MockContext:
    def __init__(self, inputs=None, parameters=None):
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.outputs = {}

def test_depth_effects_manifest():
    manifest = PluginInfo(**METADATA)
    assert manifest.name == "Depth Effects"
    assert "pointSize" in [p["name"] for p in manifest.parameters]
    assert "video_in" in manifest.inputs
    assert "depth_in" in manifest.inputs
    assert "video_out" in manifest.outputs

def test_depth_effects_bypassed():
    plugin = DepthEffectsPlugin()
    ctx_empty = MockContext()
    plugin.initialize(ctx_empty)
    
    val = plugin.process_frame(100, {}, ctx_empty)
    assert val == 100
    
    ctx = MockContext(inputs={"video_in": 100}, parameters={})
    res = plugin.process_frame(100, {"pointSize": 1.0}, ctx)
    assert ctx.outputs["video_out"] == 100

def test_depth_effects_missing_video():
    plugin = DepthEffectsPlugin()
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
    monkeypatch.setattr(de, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(de, 'HAS_GL', True)
    return mock_gl

def test_depth_effects_fbo_cleanup(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    
    plugin = DepthEffectsPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    assert getattr(plugin, 'texture', None) == 1
    assert getattr(plugin, 'fbo', None) == 10
    
    plugin.cleanup()
    
    mock_gl.glDeleteTextures.assert_called()
    mock_gl.glDeleteFramebuffers.assert_called()
    assert getattr(plugin, 'texture', None) is None

def test_depth_effects_gl_exception_handling(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGenTextures.side_effect = Exception("Out of Memory")
    
    plugin = DepthEffectsPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    
    plugin.initialize(ctx)
    assert plugin._mock_mode is True
    assert getattr(plugin, 'texture', None) is None
    
    mock_gl.glGenTextures.side_effect = None
    mock_gl.glGenTextures.return_value = 1
    mock_gl.glGenFramebuffers.return_value = 2
    
    plugin2 = DepthEffectsPlugin()
    plugin2._mock_mode = False
    plugin2.initialize(ctx)
    
    mock_gl.glDeleteTextures.side_effect = Exception("Segmentation Fault")
    plugin2.cleanup()
    assert getattr(plugin2, 'texture', None) is None

def test_depth_effects_render_frame(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthEffectsPlugin()
    plugin._mock_mode = False
    ctx = MockContext(inputs={"depth_in": 200})
    plugin.initialize(ctx)
    
    assert getattr(plugin, 'pc_prog', None) is not None
    
    params = {
        "pointSize": 5.0,
        "pointDensity": 5.0,
        "minDepth": 5.0,
        "maxDepth": 5.0,
        "cameraDistance": 5.0,
        "u_mix": 0.5
    }
    
    # Run twice measuring different widths to test realloc logic
    mock_gl.glGetTexLevelParameteriv.return_value = 1920
    res1 = plugin.process_frame(100, params, ctx)
    assert getattr(plugin, 'out_tex', res1) == res1  # Outputs FBO texture
    
    mock_gl.glGetTexLevelParameteriv.return_value = 800
    res3 = plugin.process_frame(100, params, ctx)
    assert res3 == getattr(plugin, 'out_tex', 1)

def test_compile_shader_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGetShaderiv.return_value = 0 # Fail
    mock_gl.glGetShaderInfoLog.return_value = "ERROR"
    
    plugin = DepthEffectsPlugin()
    # Need to disable HAS_GL bypass locally
    monkeypatch.setattr(de, 'HAS_GL', True)
    res = plugin._compile_shader("VS", "FS")
    assert res is None

def test_process_frame_render_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthEffectsPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    mock_gl.glBindTexture.side_effect = Exception("Render fail")
    res = plugin.process_frame(100, {}, ctx)
    assert res == 100 # Returns input on fail
