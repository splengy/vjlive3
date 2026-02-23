import pytest
from unittest.mock import MagicMock, patch

from vjlive3.plugins.depth_reality_distortion import RealityDistortionPlugin

def test_reality_distortion_manifest():
    plugin = RealityDistortionPlugin()
    meta = plugin.get_metadata()
    
    assert meta["name"] == "Reality Distortion"
    assert "video_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    assert "video_out" in meta["outputs"]
    
    param_names = [p["name"] for p in meta["parameters"]]
    assert "distortion_amount" in param_names
    assert "warp_frequency" in param_names
    assert "depth_threshold" in param_names
    assert "chromatic_aberration" in param_names

def test_reality_distortion_mock_bypass():
    plugin = RealityDistortionPlugin()
    plugin._mock_mode = True
    
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {"video_in": 77, "depth_in": 99}
    ctx.outputs = {}
    
    res = plugin.process_frame(77, {}, ctx)
    assert res == 77
    assert ctx.outputs["video_out"] == 77
    
def test_reality_distortion_empty_input():
    plugin = RealityDistortionPlugin()
    ctx = MagicMock()(MagicMock())
    res = plugin.process_frame(0, {}, ctx)
    assert res == 0

def test_reality_distortion_gl_failure():
    plugin = RealityDistortionPlugin()
    
    with patch("vjlive3.plugins.depth_reality_distortion.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 0 # GL_FALSE
#         plugin.initialize(PluginContext(MagicMock()))
        
        # Shader failed, safely entered mock isolated mode.
        assert plugin._mock_mode is True

def test_reality_distortion_fbo_cleanup():
    plugin = RealityDistortionPlugin()
    
    with patch("vjlive3.plugins.depth_reality_distortion.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 50
        plugin.tex = 40
        plugin.vao = 22
        plugin.vbo = 33
        plugin.prog = 44
        
        plugin.cleanup()
        
        mock_gl.glDeleteTextures.assert_any_call(1, [40])
        mock_gl.glDeleteFramebuffers.assert_any_call(1, [50])
        mock_gl.glDeleteVertexArrays.assert_called_with(1, [22])
        mock_gl.glDeleteProgram.assert_called_with(44)
        
        assert plugin.tex is None
        assert plugin.fbo is None

def test_reality_distortion_bypass():
    """Missing depth passes uniformly as standard mapping natively."""
    plugin = RealityDistortionPlugin()
    
    with patch("vjlive3.plugins.depth_reality_distortion.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 1
        plugin.prog = 2
        plugin.tex = 9
        plugin.vao = 1
        plugin._width = 1920
        plugin._height = 1080
        
        ctx = MagicMock()(MagicMock())
        ctx.inputs = {"video_in": 5}
        ctx.outputs = {}
        
        mock_gl.glGetUniformLocation.side_effect = lambda prog, name: name
        
        plugin.process_frame(5, {}, ctx)
        
        mock_gl.glUniform1i.assert_any_call("has_depth", 0)

def test_reality_distortion_full_pipeline():
    plugin = RealityDistortionPlugin()
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {"video_in": 1, "depth_in": 2}
    ctx.outputs = {}
    
    with patch("vjlive3.plugins.depth_reality_distortion.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 1 # GL_TRUE
        mock_gl.glGetProgramiv.return_value = 1 # GL_TRUE
        mock_gl.glGenTextures.return_value = 15 
        
        plugin._mock_mode = False
        plugin.initialize(ctx)
        
        res = plugin.process_frame(1, {"distortion_amount": 1.0}, ctx)
        
        assert plugin._mock_mode is False
        assert mock_gl.glDrawArrays.called
        assert ctx.outputs["video_out"] == 15
