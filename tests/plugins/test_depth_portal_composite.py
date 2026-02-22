import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.plugins.depth_portal_composite as vdc
from vjlive3.plugins.depth_portal_composite import DepthPortalCompositePlugin, METADATA
from vjlive3.plugins.registry import PluginInfo

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.plugins.depth_portal_composite.HAS_GL', False)

class MockContext:
    def __init__(self, inputs=None, parameters=None):
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.outputs = {}

def test_portal_composite_manifest():
    manifest = PluginInfo(**METADATA)
    assert manifest.name == "Depth Portal Composite"
    assert "slice_near" in [p["name"] for p in manifest.parameters]
    assert "video_out" in manifest.outputs

def test_portal_composite_empty():
    plugin = DepthPortalCompositePlugin()
    ctx = MockContext()
    plugin.initialize(ctx)
    val = plugin.process_frame(None, {}, ctx)
    assert val == 0

def test_portal_composite_missing_depth():
    plugin = DepthPortalCompositePlugin()
    ctx = MockContext(
        inputs={"video_in": 100, "color_in": 500}, 
        parameters={}
    )
    plugin.initialize(ctx)
    val = plugin.process_frame(100, {}, ctx)
    assert val == 100
    assert ctx.outputs["video_out"] == 100

def test_portal_composite_mock_success():
    plugin = DepthPortalCompositePlugin()
    ctx = MockContext(
        inputs={"video_in": 100, "depth_in": 200, "color_in": 500}, 
        parameters={}
    )
    plugin.initialize(ctx)
    
    val = plugin.process_frame(100, {"bg_opacity": 1.0, "slice_near": 0.5, "slice_far": 0.2}, ctx)
    assert params_clamped(plugin, ctx, 0.2, 0.5)
    assert val == 500
    assert ctx.outputs["video_out"] == 500
    
    val2 = plugin.process_frame(100, {"bg_opacity": 0.0}, ctx)
    assert val2 == 100

def params_clamped(plugin, ctx, near, far):
    p = {"slice_near": far, "slice_far": near}
    plugin.process_frame(100, p, ctx)
    return p["_clamped_near"] == near and p["_clamped_far"] == far

def setup_mock_gl(monkeypatch):
    mock_gl = MagicMock()
    mock_gl.glGenTextures.return_value = 10
    mock_gl.glGenFramebuffers.return_value = 20
    mock_gl.GL_TRUE = 1
    mock_gl.glGetShaderiv.return_value = 1
    mock_gl.glGetTexLevelParameteriv.return_value = 1920
    monkeypatch.setattr(vdc, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(vdc, 'HAS_GL', True)
    return mock_gl

def test_portal_composite_fbo_cleanup_headless(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    
    plugin = DepthPortalCompositePlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    assert plugin.out_tex == 10
    assert plugin.fbo == 20
    
    plugin.cleanup()
    mock_gl.glDeleteTextures.assert_called_once_with(1, [10])
    mock_gl.glDeleteFramebuffers.assert_called_once_with(1, [20])
    
def test_portal_composite_gl_exception_handling(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGenTextures.side_effect = Exception("Out of Memory")
    
    plugin = DepthPortalCompositePlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    
    plugin.initialize(ctx)
    assert plugin._mock_mode is True
    
    mock_gl.glGenTextures.side_effect = None
    mock_gl.glGenTextures.return_value = 1
    mock_gl.glGenFramebuffers.return_value = 2
    
    plugin2 = DepthPortalCompositePlugin()
    plugin2._mock_mode = False
    plugin2.initialize(ctx)
    
    mock_gl.glDeleteTextures.side_effect = Exception("Segmentation Fault")
    plugin2.cleanup()
    assert plugin2.out_tex is None

def test_portal_composite_render_frame(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthPortalCompositePlugin()
    plugin._mock_mode = False
    ctx = MockContext(inputs={"depth_in": 2, "color_in": 3})
    plugin.initialize(ctx)
    
    assert plugin.prog is not None
    
    params = {
        "slice_near": 0.8,
        "slice_far": 0.2,
        "edge_softness": 0.5,
        "spill_suppress": 0.5,
        "bg_opacity": 0.5,
        "fg_scale": 0.5,
        "fg_offset_x": 0.5,
        "fg_offset_y": 0.5,
        "u_mix": 1.0
    }
    
    res1 = plugin.process_frame(1, params, ctx)
    assert res1 == 10
    
    mock_gl.glGetTexLevelParameteriv.return_value = 1920
    res2 = plugin.process_frame(1, params, ctx)
    assert res2 == 10

    # Texture resize
    mock_gl.glGetTexLevelParameteriv.return_value = 800
    res3 = plugin.process_frame(1, params, ctx)
    assert res3 == 10

    res4 = plugin.process_frame(0, params, ctx)
    assert res4 == 0
    
    # Missing optional context maps natively fails back to VideoIn
    ctx2 = MockContext()
    res5 = plugin.process_frame(1, params, ctx2)
    assert res5 == 1

def test_compile_shader_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGetShaderiv.return_value = 0
    mock_gl.glGetShaderInfoLog.return_value = "ERROR"
    
    plugin = DepthPortalCompositePlugin()
    res = plugin._compile_shader()
    assert res is None

def test_process_frame_render_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthPortalCompositePlugin()
    plugin._mock_mode = False
    ctx = MockContext(inputs={"depth_in": 2, "color_in": 3})
    plugin.initialize(ctx)
    
    mock_gl.glBindTexture.side_effect = Exception("Render fail")
    res = plugin.process_frame(100, {}, ctx)
    assert res == 100
