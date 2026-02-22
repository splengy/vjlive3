import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.plugins.depth_camera_splitter as dcs
from vjlive3.plugins.depth_camera_splitter import DepthCameraSplitterPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.plugins.depth_camera_splitter.HAS_GL', False)

class MockContext:
    def __init__(self, inputs=None, parameters=None):
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.outputs = {}

def test_manifest():
    assert METADATA["name"] == "Depth Camera Splitter"
    assert "depthMin" in [p["name"] for p in METADATA["parameters"]]
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "ir_in" in METADATA["inputs"]
    assert "video_out" in METADATA["outputs"]

def test_mock_processing_passthrough():
    plugin = DepthCameraSplitterPlugin()
    ctx = MockContext(inputs={"depth_in": 200, "ir_in": 300})
    plugin.initialize(ctx)
    
    assert plugin._mock_mode is True
    
    res = plugin.process_frame(100, {}, ctx)
    assert res == 100
    assert ctx.outputs["video_out"] == 100
    
    # Missing input
    assert plugin.process_frame(0, {}, ctx) == 0

def setup_mock_gl(monkeypatch):
    mock_gl = MagicMock()
    mock_gl.glGenTextures.return_value = [1, 2]
    mock_gl.glGenFramebuffers.return_value = [10, 20]
    mock_gl.GL_TRUE = 1
    mock_gl.glGetShaderiv.return_value = 1
    mock_gl.glGetTexLevelParameteriv.return_value = 1920
    monkeypatch.setattr(dcs, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dcs, 'HAS_GL', True)
    return mock_gl
    
def test_gl_initialization(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthCameraSplitterPlugin()
    plugin._mock_mode = False
    
    ctx = MockContext()
    plugin.initialize(ctx)
    
    assert plugin.prog is not None
    assert plugin.textures["feedback_0"] == 1
    assert plugin.textures["feedback_1"] == 2
    assert plugin.fbos["feedback_0"] == 10
    
def test_gl_fbo_cleanup(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthCameraSplitterPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    
    plugin.initialize(ctx)
    plugin.cleanup()
    
    mock_gl.glDeleteTextures.assert_called_once_with(2, [1, 2])
    mock_gl.glDeleteFramebuffers.assert_called_once_with(2, [10, 20])
    
def test_gl_exception_fallback(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGenTextures.side_effect = Exception("Out of Memory")
    
    plugin = DepthCameraSplitterPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    
    plugin.initialize(ctx)
    assert plugin._mock_mode is True
    
def test_gl_render_ping_pong(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthCameraSplitterPlugin()
    plugin._mock_mode = False
    ctx = MockContext(inputs={"depth_in": 300, "ir_in": 400})
    
    plugin.initialize(ctx)
    
    assert plugin.ping_pong == 0
    res1 = plugin.process_frame(100, {"outputSelect": 2.0, "depthMin": 1.0, "depthGamma": 3.0, "depthSmooth": 5.0}, ctx)
    assert res1 == 2
    assert plugin.ping_pong == 1
    
    mock_gl.glGetTexLevelParameteriv.return_value = 1920
    res2 = plugin.process_frame(100, {}, ctx)
    assert res2 == 1
    
    # Trigger texture size change reallocation branch
    mock_gl.glGetTexLevelParameteriv.return_value = 800
    res3 = plugin.process_frame(100, {}, ctx)
    assert res3 == 2

def test_gl_render_exception(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthCameraSplitterPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    mock_gl.glBindTexture.side_effect = Exception("Driver Crash")
    res = plugin.process_frame(100, {}, ctx)
    assert res == 100 # Return raw input unharmed
    
def test_shader_compile_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGetShaderiv.return_value = 0 # Fail flag
    
    plugin = DepthCameraSplitterPlugin()
    res = plugin._compile_shader()
    assert res is None

def test_single_int_generation(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGenTextures.return_value = 99
    mock_gl.glGenFramebuffers.return_value = 100
    
    plugin = DepthCameraSplitterPlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    assert plugin.textures["feedback_0"] == 99
    assert plugin.textures["feedback_1"] == 100
