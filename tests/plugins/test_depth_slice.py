import pytest
from unittest.mock import MagicMock, patch

from vjlive3.plugins.api import PluginContext
from vjlive3.plugins.depth_slice import DepthSlicePlugin

def test_depth_slice_manifest():
    plugin = DepthSlicePlugin()
    meta = plugin.get_metadata()
    
    assert meta["name"] == "Depth Slice"
    assert "video_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    assert "video_out" in meta["outputs"]
    
    param_names = [p["name"] for p in meta["parameters"]]
    assert "num_slices" in param_names
    assert "slice_thickness" in param_names
    assert "color_shift" in param_names
    assert "glitch_amount" in param_names

def test_depth_slice_mock_bypass():
    """Verify standard logic passing through straight when rendering system lacks OpenGL."""
    plugin = DepthSlicePlugin()
    plugin._mock_mode = True
    
    ctx = PluginContext(MagicMock())
    ctx.inputs = {"video_in": 77, "depth_in": 99}
    ctx.outputs = {}
    
    res = plugin.process_frame(77, {}, ctx)
    assert res == 77
    assert ctx.outputs["video_out"] == 77
    
def test_depth_slice_empty_input_handled():
    plugin = DepthSlicePlugin()
    ctx = PluginContext(MagicMock())
    res = plugin.process_frame(0, {}, ctx)
    assert res == 0

def test_depth_slice_gl_compilation_fallback():
    plugin = DepthSlicePlugin()
    
    with patch("vjlive3.plugins.depth_slice.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 0 # GL_FALSE
        plugin.initialize(PluginContext(MagicMock()))
        
        # Shader failed, safely entered mock isolated mode.
        assert plugin._mock_mode is True

def test_depth_slice_fbo_cleanup_handling():
    plugin = DepthSlicePlugin()
    
    with patch("vjlive3.plugins.depth_slice.gl") as mock_gl:
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
        
        assert plugin.out_tex is None

def test_depth_slice_bypass_missing_depth():
    """Missing depth natively passes through shader uniformly without slice computations."""
    plugin = DepthSlicePlugin()
    
    with patch("vjlive3.plugins.depth_slice.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 1
        plugin.prog = 2
        plugin.out_tex = 9
        plugin.vao = 1
        
        ctx = PluginContext(MagicMock())
        # Missing depth texture mapped intentionally 
        ctx.inputs = {"video_in": 5}
        ctx.outputs = {}
        
        # Identify the tracked uniform integer location proxy mapping
        mock_gl.glGetUniformLocation.side_effect = lambda prog, name: name
        
        plugin.process_frame(5, {}, ctx)
        
        mock_gl.glUniform1i.assert_any_call("has_depth", 0)

def test_depth_slice_full_pipeline_hit():
    """Verify executing complete fragment shader process logic directly allocating FBOs naturally."""
    plugin = DepthSlicePlugin()
    ctx = PluginContext(MagicMock())
    ctx.inputs = {"video_in": 1, "depth_in": 2}
    ctx.outputs = {}
    
    with patch("vjlive3.plugins.depth_slice.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 1 # GL_TRUE
        mock_gl.glGetProgramiv.return_value = 1 # GL_TRUE
        mock_gl.glGenTextures.return_value = 15 
        
        plugin._mock_mode = False
        plugin.initialize(ctx)
        
        res = plugin.process_frame(1, {"num_slices": 10}, ctx)
        
        assert plugin._mock_mode is False
        assert mock_gl.glDrawArrays.called
        assert res == 15
        assert ctx.outputs["video_out"] == 15
