import pytest
from unittest.mock import MagicMock, patch

from vjlive3.plugins.depth_blur import DepthBlurPlugin

def test_depth_blur_manifest():
    plugin = DepthBlurPlugin()
    meta = plugin.get_metadata()
    
    assert meta["name"] == "Depth Blur"
    assert "video_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    assert "video_out" in meta["outputs"]
    
    param_names = [p["name"] for p in meta["parameters"]]
    assert "focal_distance" in param_names
    assert "blur_amount" in param_names
    assert "chromatic_fringe" in param_names
    assert "tilt_shift" in param_names

def test_depth_blur_mock_bypass():
    plugin = DepthBlurPlugin()
    plugin._mock_mode = True
    
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {"video_in": 123, "depth_in": 321}
    ctx.outputs = {}
    
    res = plugin.process_frame(123, {}, ctx)
    assert res == 123
    assert ctx.outputs["video_out"] == 123

def test_depth_blur_fbo_cleanup():
    plugin = DepthBlurPlugin()
    
    with patch("vjlive3.plugins.depth_blur.gl") as mock_gl:
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

def test_depth_blur_tilt_shift_fallback():
    # If depth_in is missing, it should auto-fallback processing the spatial gradient. 
    # We verify the shader binds `has_depth = 0`.
    plugin = DepthBlurPlugin()
    
    with patch("vjlive3.plugins.depth_blur.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 1
        plugin.prog = 3
        plugin.tex = 9
        plugin.vao = 1
        plugin._width = 1920
        plugin._height = 1080
        
        ctx = MagicMock()(MagicMock())
        ctx.inputs = {"video_in": 5}  # No depth_in bound
        ctx.outputs = {}
        
        mock_gl.glGetUniformLocation.side_effect = lambda prog, name: name
        
        plugin.process_frame(5, {}, ctx)
        
        # Checking native depth status mapping false natively
        mock_gl.glUniform1i.assert_any_call("has_depth", 0)

def test_depth_blur_empty_input():
    plugin = DepthBlurPlugin()
    ctx = MagicMock()(MagicMock())
    res = plugin.process_frame(0, {}, ctx)
    assert res == 0

def test_depth_blur_full_pipeline():
    plugin = DepthBlurPlugin()
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {"video_in": 1, "depth_in": 2}
    ctx.outputs = {}
    
    with patch("vjlive3.plugins.depth_blur.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 1 
        mock_gl.glGetProgramiv.return_value = 1 
        mock_gl.glGenFramebuffers.return_value = 5
        mock_gl.glGenTextures.return_value = 15 
        
        plugin._mock_mode = False
        plugin.initialize(ctx)
        
        res = plugin.process_frame(1, {"blur_amount": 1.0}, ctx)
        
        assert plugin._mock_mode is False
        assert mock_gl.glDrawArrays.called
        assert ctx.outputs["video_out"] == 15
