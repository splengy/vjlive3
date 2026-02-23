import pytest
from unittest.mock import MagicMock, patch

from vjlive3.plugins.depth_fracture_datamosh import DepthFractureDatamoshPlugin

def test_fracture_datamosh_manifest():
    plugin = DepthFractureDatamoshPlugin()
    meta = plugin.get_metadata()
    
    assert meta["name"] == "Depth Fracture Datamosh"
    assert "video_in" in meta["inputs"]
    assert "video_b_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    assert "video_out" in meta["outputs"]
    
    param_names = [p["name"] for p in meta["parameters"]]
    assert "fracture_sensitivity" in param_names
    assert "fracture_width" in param_names
    assert "fracture_decay" in param_names
    assert "bleed_amount" in param_names
    assert "displacement_strength" in param_names

def test_fracture_datamosh_fbo_lifecycle():
    # Validating SAFETY RAIL #8 (Datamosh Explicit FBO Cleanup)
    plugin = DepthFractureDatamoshPlugin()
    
    with patch("vjlive3.plugins.depth_fracture_datamosh.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo1 = 100
        plugin.fbo2 = 101
        plugin.tex1 = 200
        plugin.tex2 = 201
        plugin.vao = 22
        plugin.vbo = 33
        plugin.prog = 44
        
        plugin.cleanup()
        
        mock_gl.glDeleteTextures.assert_any_call(1, [200])
        mock_gl.glDeleteTextures.assert_any_call(1, [201])
        mock_gl.glDeleteFramebuffers.assert_any_call(1, [100])
        mock_gl.glDeleteFramebuffers.assert_any_call(1, [101])
        
        assert plugin.tex1 is None
        assert plugin.tex2 is None
        assert plugin.fbo1 is None
        assert plugin.fbo2 is None

def test_fracture_datamosh_mock_bypass():
    plugin = DepthFractureDatamoshPlugin()
    plugin._mock_mode = True
    
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {"video_in": 123, "depth_in": 321}
    ctx.outputs = {}
    
    res = plugin.process_frame(123, {}, ctx)
    assert res == 123
    assert ctx.outputs["video_out"] == 123

def test_fracture_datamosh_missing_inputs():
    # Assuring missing video_b or missing depth intercepts safely (SAFETY RAIL #7)
    plugin = DepthFractureDatamoshPlugin()
    
    with patch("vjlive3.plugins.depth_fracture_datamosh.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo1 = 1
        plugin.fbo2 = 2
        plugin.prog = 3
        plugin.tex1 = 9
        plugin.tex2 = 8
        plugin.vao = 1
        plugin._width = 1920
        plugin._height = 1080
        
        ctx = MagicMock()(MagicMock())
        ctx.inputs = {"video_in": 5}  # missing depth and video_b
        ctx.outputs = {}
        
        mock_gl.glGetUniformLocation.side_effect = lambda prog, name: name
        
        plugin.process_frame(5, {}, ctx)
        
        mock_gl.glUniform1i.assert_any_call("has_depth", 0)
        mock_gl.glUniform1i.assert_any_call("has_video_b", 0)

def test_fracture_datamosh_empty_input():
    plugin = DepthFractureDatamoshPlugin()
    ctx = MagicMock()(MagicMock())
    res = plugin.process_frame(0, {}, ctx)
    assert res == 0

def test_fracture_datamosh_full_pipeline():
    plugin = DepthFractureDatamoshPlugin()
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {"video_in": 1, "video_b_in": 4, "depth_in": 2}
    ctx.outputs = {}
    
    with patch("vjlive3.plugins.depth_fracture_datamosh.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 1 
        mock_gl.glGetProgramiv.return_value = 1 
        mock_gl.glGenFramebuffers.side_effect = [5, 6]
        mock_gl.glGenTextures.side_effect = [15, 16] 
        
        plugin._mock_mode = False
        plugin.initialize(ctx)
        
        res = plugin.process_frame(1, {"displacement_strength": 1.0}, ctx)
        
        assert plugin._mock_mode is False
        assert mock_gl.glDrawArrays.called
        assert res in [15, 16]
        assert ctx.outputs["video_out"] in [15, 16]
