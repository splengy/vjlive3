import pytest
from unittest.mock import MagicMock, patch

from vjlive3.plugins.api import PluginContext
from vjlive3.plugins.depth_color_grade import DepthColorGradePlugin

def test_depth_color_grade_manifest():
    plugin = DepthColorGradePlugin()
    meta = plugin.get_metadata()
    
    assert meta["name"] == "Depth Color Grade"
    assert "video_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    assert "video_out" in meta["outputs"]
    
    param_names = [p["name"] for p in meta["parameters"]]
    assert "zone_near" in param_names
    assert "zone_far" in param_names
    assert "near_hue" in param_names
    assert "mid_saturation" in param_names
    assert "far_temperature" in param_names
    assert "contrast" in param_names
    assert "film_curve" in param_names

def test_color_grade_mock_bypass():
    plugin = DepthColorGradePlugin()
    plugin._mock_mode = True
    
    ctx = PluginContext(MagicMock())
    ctx.inputs = {"video_in": 123, "depth_in": 321}
    ctx.outputs = {}
    
    res = plugin.process_frame(123, {}, ctx)
    assert res == 123
    assert ctx.outputs["video_out"] == 123

def test_depth_color_grade_fbo_cleanup():
    plugin = DepthColorGradePlugin()
    
    with patch("vjlive3.plugins.depth_color_grade.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 50
        plugin.tex = 60
        plugin.vao = 22
        plugin.vbo = 33
        plugin.prog = 44
        
        plugin.cleanup()
        
        mock_gl.glDeleteTextures.assert_any_call(1, [60])
        mock_gl.glDeleteFramebuffers.assert_any_call(1, [50])
        mock_gl.glDeleteVertexArrays.assert_called_with(1, [22])
        mock_gl.glDeleteProgram.assert_called_with(44)
        
        assert plugin.tex is None
        assert plugin.fbo is None

def test_depth_color_grade_zone_swap():
    # If zone_near > zone_far, the python wrapper must swap them prior to Shader binding.
    plugin = DepthColorGradePlugin()
    
    with patch("vjlive3.plugins.depth_color_grade.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 1
        plugin.prog = 3
        plugin.tex = 9
        plugin.vao = 1
        plugin._width = 1920
        plugin._height = 1080
        
        ctx = PluginContext(MagicMock())
        ctx.inputs = {"video_in": 5}
        ctx.outputs = {}
        
        mock_gl.glGetUniformLocation.side_effect = lambda prog, name: name
        
        # Setting inverted near and far explicitly mapping swapped bindings natively.
        plugin.process_frame(5, {"zone_near": 0.8, "zone_far": 0.2}, ctx)
        
        mock_gl.glUniform1f.assert_any_call("zone_near", 0.2)
        mock_gl.glUniform1f.assert_any_call("zone_far", 0.8)

def test_depth_color_grade_empty_input():
    plugin = DepthColorGradePlugin()
    ctx = PluginContext(MagicMock())
    res = plugin.process_frame(0, {}, ctx)
    assert res == 0

def test_depth_color_grade_full_pipeline():
    plugin = DepthColorGradePlugin()
    ctx = PluginContext(MagicMock())
    ctx.inputs = {"video_in": 1, "depth_in": 2}
    ctx.outputs = {}
    
    with patch("vjlive3.plugins.depth_color_grade.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 1 
        mock_gl.glGetProgramiv.return_value = 1 
        mock_gl.glGenFramebuffers.return_value = 5
        mock_gl.glGenTextures.return_value = 15 
        
        plugin._mock_mode = False
        plugin.initialize(ctx)
        
        res = plugin.process_frame(1, {"contrast": 0.8}, ctx)
        
        assert plugin._mock_mode is False
        assert mock_gl.glDrawArrays.called
        assert ctx.outputs["video_out"] == 15
