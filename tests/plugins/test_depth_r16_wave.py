import pytest
from unittest.mock import MagicMock, patch

from vjlive3.plugins.depth_r16_wave import DepthR16WavePlugin

def test_r16_wave_manifest():
    plugin = DepthR16WavePlugin()
    meta = plugin.get_metadata()
    
    assert meta["name"] == "R16 Depth Wave"
    assert "video_in" in meta["inputs"]
    assert "depth_raw_in" in meta["inputs"]
    assert "video_out" in meta["outputs"]
    assert "depth_raw_out" in meta["outputs"]
    
    param_names = [p["name"] for p in meta["parameters"]]
    assert "wave_amplitude" in param_names
    assert "wave_frequency" in param_names
    assert "wave_speed" in param_names
    assert "phase_offset" in param_names

def test_r16_wave_mock_bypass():
    plugin = DepthR16WavePlugin()
    plugin._mock_mode = True
    
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {"video_in": 100, "depth_raw_in": 200}
    ctx.outputs = {}
    
    res = plugin.process_frame(100, {}, ctx)
    assert res == 100
    assert ctx.outputs["video_out"] == 100
    assert ctx.outputs["depth_raw_out"] == 200

def test_r16_wave_mock_missing_depth():
    plugin = DepthR16WavePlugin()
    plugin._mock_mode = True
    
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {"video_in": 100} # missing depth_raw_in
    ctx.outputs = {}
    
    res = plugin.process_frame(100, {}, ctx)
    assert res == 100
    assert ctx.outputs["video_out"] == 100
    assert ctx.outputs["depth_raw_out"] == 0
    
def test_r16_wave_empty_input():
    plugin = DepthR16WavePlugin()
    ctx = MagicMock()(MagicMock())
    res = plugin.process_frame(0, {}, ctx)
    assert res == 0

def test_r16_texture_allocation():
    plugin = DepthR16WavePlugin()
    
    with patch("vjlive3.plugins.depth_r16_wave.gl") as mock_gl:
        plugin._mock_mode = False
        
        # Override glGenTextures to return a list of two distinct pointers since MRT calls need 2.
        mock_gl.glGenTextures.return_value = [55, 66]
        
        plugin._allocate_buffers(1920, 1080)
        
        assert plugin.tex_video == 55
        assert plugin.tex_depth == 66
        
        # Verify MRT binds exactly to dual color attachments natively.
        mock_gl.glDrawBuffers.assert_called_with(2, [mock_gl.GL_COLOR_ATTACHMENT0, mock_gl.GL_COLOR_ATTACHMENT1])
        
        # Verify 16-bit format natively bound to target
        mock_gl.glTexImage2D.assert_any_call(
            mock_gl.GL_TEXTURE_2D, 0, mock_gl.GL_R16F, 1920, 1080, 0, mock_gl.GL_RED, mock_gl.GL_FLOAT, None
        )

def test_r16_wave_fbo_cleanup():
    plugin = DepthR16WavePlugin()
    
    with patch("vjlive3.plugins.depth_r16_wave.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 50
        plugin.tex_video = 40
        plugin.tex_depth = 41
        plugin.vao = 22
        plugin.vbo = 33
        plugin.prog = 44
        
        plugin.cleanup()
        
        # It should free exactly 2 textures
        mock_gl.glDeleteTextures.assert_any_call(2, [40, 41])
        mock_gl.glDeleteFramebuffers.assert_any_call(1, [50])
        mock_gl.glDeleteVertexArrays.assert_called_with(1, [22])
        mock_gl.glDeleteProgram.assert_called_with(44)
        
        assert plugin.tex_video is None
        assert plugin.tex_depth is None
        assert plugin.fbo is None

def test_r16_wave_bypass():
    """Missing depth binds uniform has_depth == 0 mapping output safely."""
    plugin = DepthR16WavePlugin()
    
    with patch("vjlive3.plugins.depth_r16_wave.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 1
        plugin.prog = 2
        plugin.tex_video = 9
        plugin.tex_depth = 10
        plugin.vao = 1
        plugin._width = 1920
        plugin._height = 1080
        
        ctx = MagicMock()(MagicMock())
        ctx.inputs = {"video_in": 5}
        ctx.outputs = {}
        
        mock_gl.glGetUniformLocation.side_effect = lambda prog, name: name
        
        plugin.process_frame(5, {}, ctx)
        
        mock_gl.glUniform1i.assert_any_call("has_depth", 0)
        assert ctx.outputs["depth_raw_out"] == 10

def test_r16_wave_full_pipeline():
    plugin = DepthR16WavePlugin()
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {"video_in": 1, "depth_raw_in": 2}
    ctx.outputs = {}
    
    with patch("vjlive3.plugins.depth_r16_wave.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 1 # GL_TRUE
        mock_gl.glGetProgramiv.return_value = 1 # GL_TRUE
        mock_gl.glGenTextures.return_value = [15, 16] 
        
        plugin._mock_mode = False
        plugin.initialize(ctx)
        
        res = plugin.process_frame(1, {"wave_amplitude": 1.0}, ctx)
        
        assert plugin._mock_mode is False
        assert mock_gl.glDrawArrays.called
        assert ctx.outputs["video_out"] == 15
        assert ctx.outputs["depth_raw_out"] == 16
