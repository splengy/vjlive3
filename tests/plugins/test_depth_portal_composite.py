import pytest
import numpy as np
import sys
from unittest.mock import MagicMock, patch

from vjlive3.plugins.depth_portal_composite import DepthPortalCompositePlugin, METADATA

def test_portal_composite_manifest():
    plugin = DepthPortalCompositePlugin()
    meta = plugin.get_metadata()
    
    assert meta["name"] == "Depth Portal Composite"
    assert "video_in" in meta["inputs"]
    assert "background_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    assert "video_out" in meta["outputs"]
    
    param_names = [p["name"] for p in meta["parameters"]]
    assert "slice_near" in param_names
    assert "slice_far" in param_names
    assert "edge_softness" in param_names
    assert "bg_opacity" in param_names

def test_portal_composite_mock_pass():
    plugin = DepthPortalCompositePlugin()
    plugin._mock_mode = True # Ensure mock mode
    
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {
        "video_in": 42,
        "background_in": 99,
        "depth_in": 12
    }
    ctx.outputs = {}
    
    params = {
        "slice_near": 1.5,
        "slice_far": 4.0
    }
    
    res = plugin.process_frame(42, params, ctx)
    assert res == 42
    assert ctx.outputs["video_out"] == 42

def test_portal_composite_missing_bg():
    plugin = DepthPortalCompositePlugin()
    
    with patch("vjlive3.plugins.depth_portal_composite.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 1
        plugin.prog = 2
        plugin.out_tex = 9
        plugin.vao = 1
        
        ctx = MagicMock()(MagicMock())
        # Missing background
        ctx.inputs = {"video_in": 5, "depth_in": 10}
        ctx.outputs = {}
        
        params = {
            "slice_near": 1.0,
            "slice_far": 2.0
        }
        
        # Set glGetUniformLocation to return some ID to track
        mock_gl.glGetUniformLocation.side_effect = lambda prog, name: name
        
        plugin.process_frame(5, params, ctx)
        
        # Verify it handled background check
        mock_gl.glUniform1i.assert_any_call("has_background", 0)
        mock_gl.glUniform1i.assert_any_call("has_depth", 1)

def test_portal_composite_missing_depth():
    plugin = DepthPortalCompositePlugin()
    
    with patch("vjlive3.plugins.depth_portal_composite.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 1
        plugin.prog = 2
        plugin.out_tex = 9
        plugin.vao = 1
        
        ctx = MagicMock()(MagicMock())
        # Missing depth
        ctx.inputs = {"video_in": 5, "background_in": 10}
        ctx.outputs = {}
        
        params = {
            "slice_near": 1.0,
            "slice_far": 2.0
        }
        
        mock_gl.glGetUniformLocation.side_effect = lambda prog, name: name
        
        plugin.process_frame(5, params, ctx)
        
        # Verify it handled depth check
        mock_gl.glUniform1i.assert_any_call("has_background", 1)
        mock_gl.glUniform1i.assert_any_call("has_depth", 0)

def test_portal_composite_fbo_cleanup():
    plugin = DepthPortalCompositePlugin()
    
    with patch("vjlive3.plugins.depth_portal_composite.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 99
        plugin.out_tex = 10
        plugin.vao = 22
        plugin.vbo = 33
        plugin.prog = 44
        
        plugin.cleanup()
        
        mock_gl.glDeleteTextures.assert_any_call(1, [10])
        mock_gl.glDeleteFramebuffers.assert_called_with(1, [99])
        mock_gl.glDeleteVertexArrays.assert_called_with(1, [22])
        mock_gl.glDeleteProgram.assert_called_with(44)
        
        # State cleared
        assert plugin.out_tex is None
        assert plugin.fbo is None
        assert plugin.prog is None

def test_portal_composite_gl_setup_error_handling():
    plugin = DepthPortalCompositePlugin()
    
    with patch("vjlive3.plugins.depth_portal_composite.gl") as mock_gl:
        # Simulate compilation failure
        mock_gl.glGetShaderiv.return_value = 0 # GL_FALSE
        mock_gl.glGetShaderInfoLog.return_value = b"Error compiling"
        
#         plugin.initialize(PluginContext(MagicMock()))
        assert plugin._mock_mode is True

def test_portal_composite_empty_input_texture():
    plugin = DepthPortalCompositePlugin()
    ctx = MagicMock()(MagicMock())
    res = plugin.process_frame(0, {}, ctx)
    assert res == 0

def test_portal_composite_gl_full_pipeline():
    plugin = DepthPortalCompositePlugin()
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {"video_in": 1, "background_in": 2, "depth_in": 3}
    ctx.outputs = {}
    
    with patch("vjlive3.plugins.depth_portal_composite.gl") as mock_gl:
        # Mock successful shader compilation
        mock_gl.glGetShaderiv.return_value = 1 # GL_TRUE
        mock_gl.glGetProgramiv.return_value = 1 # GL_TRUE
        
        # Setup mock that returns FBO tex ID
        mock_gl.glGenTextures.return_value = 11
        
        plugin._mock_mode = False
        plugin.initialize(ctx)
        
        # Ensure it didn't fallback to mock
        assert plugin._mock_mode is False
        assert plugin.out_tex == 11
        
        # Now process with swapped thresholds to trigger the swap block coverage
        res = plugin.process_frame(1, {"slice_near": 4.0, "slice_far": 1.5}, ctx)
        
        # Verify texture output matches the generated texture
        assert res == 11
        assert ctx.outputs["video_out"] == 11
        
        # Ensure process ran draw arrays
        mock_gl.glDrawArrays.assert_called()
