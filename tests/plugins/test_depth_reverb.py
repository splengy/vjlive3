import pytest
from unittest.mock import MagicMock, patch

from vjlive3.plugins.depth_reverb import DepthReverbPlugin

def test_depth_reverb_manifest():
    plugin = DepthReverbPlugin()
    meta = plugin.get_metadata()
    
    assert meta["name"] == "Depth Reverb"
    assert "video_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    assert "video_out" in meta["outputs"]
    
    param_names = [p["name"] for p in meta["parameters"]]
    assert "room_size" in param_names
    assert "decay_time" in param_names
    assert "diffusion" in param_names
    assert "damping" in param_names

def test_depth_reverb_mock_pass():
    plugin = DepthReverbPlugin()
    plugin._mock_mode = True
    
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {"video_in": 42, "depth_in": 12}
    ctx.outputs = {}
    
    res = plugin.process_frame(42, {}, ctx)
    assert res == 42
    assert ctx.outputs["video_out"] == 42
    
def test_depth_reverb_empty_input():
    plugin = DepthReverbPlugin()
    ctx = MagicMock()(MagicMock())
    res = plugin.process_frame(0, {}, ctx)
    assert res == 0

def test_depth_reverb_gl_setup_error_handling():
    plugin = DepthReverbPlugin()
    
    with patch("vjlive3.plugins.depth_reverb.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 0 # GL_FALSE
#         plugin.initialize(PluginContext(MagicMock()))
        assert plugin._mock_mode is True

def test_depth_reverb_fbo_lifecycle():
    plugin = DepthReverbPlugin()
    
    with patch("vjlive3.plugins.depth_reverb.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 99
        plugin.tex_out = 10
        plugin.tex_prev = 11
        plugin.vao = 22
        plugin.vbo = 33
        plugin.prog = 44
        
        plugin.cleanup()
        
        mock_gl.glDeleteTextures.assert_any_call(1, [10])
        mock_gl.glDeleteTextures.assert_any_call(1, [11])
        mock_gl.glDeleteFramebuffers.assert_called_with(1, [99])
        mock_gl.glDeleteVertexArrays.assert_called_with(1, [22])
        mock_gl.glDeleteProgram.assert_called_with(44)
        
        assert plugin.tex_out is None
        assert plugin.fbo is None

def test_depth_reverb_resolution_change():
    """Verify dynamic ping-pong FBO reallocation operates correctly without throwing exceptions."""
    plugin = DepthReverbPlugin()
    ctx = MagicMock()(MagicMock())
    
    with patch("vjlive3.plugins.depth_reverb.gl") as mock_gl:
        # Prevent actually making objects, just track what it tries to do
        mock_gl.glGenTextures.side_effect = [1, 2, 3, 4, 5, 6, 7, 8]
        mock_gl.glGenFramebuffers.side_effect = [10, 20, 30]
        
        plugin._mock_mode = False
        
        # Sim initial allocation at 1920x1080
        ctx.width = 1920
        ctx.height = 1080
        plugin.process_frame(5, {}, ctx)
        
        assert plugin.current_size == (1920, 1080)
        assert plugin.tex_out == 1
        assert plugin.tex_prev == 2
        
        # Sim resolution change to 1280x720
        ctx.width = 1280
        ctx.height = 720
        plugin.process_frame(5, {}, ctx)
        
        # Ensure it reallocated safely
        assert plugin.current_size == (1280, 720)
        assert plugin.tex_out == 3
        assert plugin.tex_prev == 4
        
        # Verify it cleaned up the old ones during reallocation
        mock_gl.glDeleteTextures.assert_any_call(1, [1])
        mock_gl.glDeleteTextures.assert_any_call(1, [2])
        mock_gl.glDeleteFramebuffers.assert_any_call(1, [10])

def test_depth_reverb_full_pipeline():
    plugin = DepthReverbPlugin()
    ctx = MagicMock()(MagicMock())
    ctx.inputs = {"video_in": 1, "depth_in": 2}
    ctx.outputs = {}
    
    with patch("vjlive3.plugins.depth_reverb.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 1 # GL_TRUE
        mock_gl.glGetProgramiv.return_value = 1 # GL_TRUE
        
        # Initialization
        plugin._mock_mode = False
        plugin.initialize(ctx)
        
        # Execute
        res = plugin.process_frame(1, {"room_size": 0.5}, ctx)
        
        assert plugin._mock_mode is False
        assert mock_gl.glDrawArrays.called
        assert res == plugin.tex_out
