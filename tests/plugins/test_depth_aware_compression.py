import pytest
from unittest.mock import MagicMock, patch

from vjlive3.plugins.api import PluginContext
from vjlive3.plugins.depth_aware_compression import DepthAwareCompressionPlugin

def test_depth_compression_manifest():
    plugin = DepthAwareCompressionPlugin()
    meta = plugin.get_metadata()
    
    assert meta["name"] == "Depth Aware Compression"
    assert "video_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    assert "video_out" in meta["outputs"]
    
    param_names = [p["name"] for p in meta["parameters"]]
    assert "block_size" in param_names
    assert "quality" in param_names
    assert "color_quantization" in param_names
    assert "depth_compression_ratio" in param_names
    assert "block_size_by_depth" in param_names

def test_depth_compression_bypass():
    # Validating SAFETY RAIL #7 (Missing depth handled smoothly globally safely)
    plugin = DepthAwareCompressionPlugin()
    
    with patch("vjlive3.plugins.depth_aware_compression.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 1
        plugin.prog = 3
        plugin.tex = 9
        plugin.vao = 1
        plugin._width = 1920
        plugin._height = 1080
        
        ctx = PluginContext(MagicMock())
        ctx.inputs = {"video_in": 5}  # missing depth_in
        ctx.outputs = {}
        
        mock_gl.glGetUniformLocation.side_effect = lambda prog, name: name
        
        plugin.process_frame(5, {}, ctx)
        
        mock_gl.glUniform1i.assert_any_call("has_depth", 0)

def test_depth_compression_mock_bypass():
    plugin = DepthAwareCompressionPlugin()
    plugin._mock_mode = True
    
    ctx = PluginContext(MagicMock())
    ctx.inputs = {"video_in": 123, "depth_in": 321}
    ctx.outputs = {}
    
    res = plugin.process_frame(123, {}, ctx)
    assert res == 123
    assert ctx.outputs["video_out"] == 123

def test_depth_compression_fbo_lifecycle():
    # Validating SAFETY RAIL #8 (Datamosh Explicit FBO Cleanup)
    plugin = DepthAwareCompressionPlugin()
    
    with patch("vjlive3.plugins.depth_aware_compression.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 100
        plugin.tex = 200
        plugin.vao = 22
        plugin.vbo = 33
        plugin.prog = 44
        
        plugin.cleanup()
        
        mock_gl.glDeleteTextures.assert_any_call(1, [200])
        mock_gl.glDeleteFramebuffers.assert_any_call(1, [100])
        
        assert plugin.tex is None
        assert plugin.fbo is None

def test_depth_compression_empty_input():
    plugin = DepthAwareCompressionPlugin()
    ctx = PluginContext(MagicMock())
    res = plugin.process_frame(0, {}, ctx)
    assert res == 0

def test_depth_compression_full_pipeline():
    plugin = DepthAwareCompressionPlugin()
    ctx = PluginContext(MagicMock())
    ctx.inputs = {"video_in": 1, "depth_in": 2}
    ctx.outputs = {}
    
    with patch("vjlive3.plugins.depth_aware_compression.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 1 
        mock_gl.glGetProgramiv.return_value = 1 
        mock_gl.glGenFramebuffers.return_value = 5
        mock_gl.glGenTextures.return_value = 15 
        
        plugin._mock_mode = False
        plugin.initialize(ctx)
        
        res = plugin.process_frame(1, {"quality": 1.0}, ctx)
        
        assert plugin._mock_mode is False
        assert mock_gl.glDrawArrays.called
        assert res == 15
        assert ctx.outputs["video_out"] == 15
