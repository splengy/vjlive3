import pytest
from unittest.mock import MagicMock, patch

from vjlive3.plugins.depth_acid_fractal import DepthAcidFractalPlugin

def test_acid_fractal_manifest():
    plugin = DepthAcidFractalPlugin()
    meta = plugin.get_metadata()
    
    assert meta["name"] == "Depth Acid Fractal"
    assert "video_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    assert "video_out" in meta["outputs"]
    
    param_names = [p["name"] for p in meta["parameters"]]
    assert "fractal_intensity" in param_names
    assert "prism_split" in param_names
    assert "solarize_level" in param_names
    assert "neon_burn" in param_names
    assert "zoom_blur" in param_names
    assert "depth_threshold" in param_names

def test_acid_fractal_mock_bypass():
    plugin = DepthAcidFractalPlugin()
    plugin._mock_mode = True
    
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {"video_in": 123, "depth_in": 321}
    ctx.outputs = {}
    
    res = plugin.process_frame(123, {}, ctx)
    assert res == 123
    assert ctx.outputs["video_out"] == 123

def test_acid_fractal_fbo_cleanup():
    plugin = DepthAcidFractalPlugin()
    
    with patch("vjlive3.plugins.depth_acid_fractal.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = [50, 51]
        plugin.tex = [60, 61]
        plugin.vao = 22
        plugin.vbo = 33
        plugin.prog = 44
        
        plugin.cleanup()
        
        mock_gl.glDeleteTextures.assert_any_call(2, [60, 61])
        mock_gl.glDeleteFramebuffers.assert_any_call(2, [50, 51])
        mock_gl.glDeleteVertexArrays.assert_called_with(1, [22])
        mock_gl.glDeleteProgram.assert_called_with(44)
        
        assert plugin.tex == [None, None]
        assert plugin.fbo == [None, None]

def test_acid_fractal_missing_depth():
    plugin = DepthAcidFractalPlugin()
    
    with patch("vjlive3.plugins.depth_acid_fractal.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = [1, 2]
        plugin.prog = 3
        plugin.tex = [9, 10]
        plugin.vao = 1
        plugin._width = 1920
        plugin._height = 1080
        
        ctx = MagicMock()(MagicMock())
        ctx.inputs = {"video_in": 5}  # No depth_in
        ctx.outputs = {}
        
        mock_gl.glGetUniformLocation.side_effect = lambda prog, name: name
        
        plugin.process_frame(5, {}, ctx)
        
        mock_gl.glUniform1i.assert_any_call("has_depth", 0)

def test_acid_fractal_empty_input():
    plugin = DepthAcidFractalPlugin()
    ctx = MagicMock()(MagicMock())
    res = plugin.process_frame(0, {}, ctx)
    assert res == 0

def test_acid_fractal_full_pipeline():
    plugin = DepthAcidFractalPlugin()
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {"video_in": 1, "depth_in": 2}
    ctx.outputs = {}
    
    with patch("vjlive3.plugins.depth_acid_fractal.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 1 
        mock_gl.glGetProgramiv.return_value = 1 
        mock_gl.glGenFramebuffers.return_value = [5, 6]
        mock_gl.glGenTextures.return_value = [15, 16] 
        
        plugin._mock_mode = False
        plugin.initialize(ctx)
        
        res = plugin.process_frame(1, {"fractal_intensity": 1.0}, ctx)
        
        assert plugin._mock_mode is False
        assert mock_gl.glDrawArrays.called
        assert ctx.outputs["video_out"] in [15, 16]
        
        # Verify Ping Pong swapping
        initial_ping_pong = plugin.ping_pong
        res2 = plugin.process_frame(1, {"fractal_intensity": 1.0}, ctx)
        assert initial_ping_pong != plugin.ping_pong
