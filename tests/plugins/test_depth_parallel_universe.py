import pytest
import numpy as np
import sys
from unittest.mock import MagicMock, patch

from vjlive3.plugins.api import PluginContext
from vjlive3.plugins.depth_parallel_universe import DepthParallelUniversePlugin, METADATA

def test_parallel_universe_manifest():
    plugin = DepthParallelUniversePlugin()
    meta = plugin.get_metadata()
    
    assert meta["name"] == "Depth Parallel Universe"
    assert "video_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    assert "universe_a_return" in meta["inputs"]
    assert "video_out" in meta["outputs"]
    assert "universe_c_send" in meta["outputs"]
    
    param_names = [p["name"] for p in meta["parameters"]]
    assert "depth_split_near" in param_names
    assert "universe_b_intensity" in param_names

def test_parallel_universe_mock_pass():
    plugin = DepthParallelUniversePlugin()
    plugin._mock_mode = True # Ensure mock mode
    
    ctx = PluginContext(MagicMock())
    ctx.inputs = {
        "video_in": 42,
        "depth_in": 12,
        "universe_a_return": 33
    }
    ctx.outputs = {}
    
    params = {
        "depth_split_near": 0.4,
        "depth_split_far": 0.3 # Triggers inversion
    }
    
    res = plugin.process_frame(42, params, ctx)
    assert res == 42
    assert ctx.outputs["video_out"] == 42
    assert ctx.outputs["universe_c_send"] == 42

def test_parallel_universe_split_clamp():
    # If Near > Far, python processing should clamp / swap them before shader execution. 
    # To test this, we can capture the glUniform1f arguments using a mock of PyOpenGL.
    plugin = DepthParallelUniversePlugin()
    
    with patch("vjlive3.plugins.depth_parallel_universe.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 1
        plugin.prog = 2
        plugin.out_textures = [1, 2, 3, 4]
        
        ctx = PluginContext(MagicMock())
        ctx.inputs = {"video_in": 5}
        ctx.outputs = {}
        
        params = {
            "depth_split_near": 0.8,
            "depth_split_far": 0.2
        }
        
        # Set glGetUniformLocation to return some ID to track
        mock_gl.glGetUniformLocation.side_effect = lambda prog, name: name
        
        plugin.process_frame(5, params, ctx)
        
        # Verify it swapped correctly
        mock_gl.glUniform1f.assert_any_call("depth_split_near", 0.2)
        mock_gl.glUniform1f.assert_any_call("depth_split_far", 0.8)

def test_parallel_universe_fbo_cleanup():
    plugin = DepthParallelUniversePlugin()
    
    with patch("vjlive3.plugins.depth_parallel_universe.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fbo = 99
        plugin.out_textures = [10, 11, 12, 13]
        plugin.prev_tex = 14
        plugin.vao = 22
        plugin.vbo = 33
        plugin.prog = 44
        
        plugin.cleanup()
        
        mock_gl.glDeleteTextures.assert_any_call(4, [10, 11, 12, 13])
        mock_gl.glDeleteTextures.assert_any_call(1, [14])
        mock_gl.glDeleteFramebuffers.assert_called_with(1, [99])
        mock_gl.glDeleteVertexArrays.assert_called_with(1, [22])
        mock_gl.glDeleteProgram.assert_called_with(44)
        
        # State cleared
        assert plugin.out_textures == []
        assert plugin.fbo is None
        assert plugin.prog is None

def test_parallel_universe_gl_setup_error_handling():
    plugin = DepthParallelUniversePlugin()
    
    with patch("vjlive3.plugins.depth_parallel_universe.gl") as mock_gl:
        # Simulate compilation failure
        mock_gl.glGetShaderiv.return_value = 0 # GL_FALSE
        mock_gl.glGetShaderInfoLog.return_value = b"Error compiling"
        
        plugin.initialize(PluginContext(MagicMock()))
        assert plugin._mock_mode is True

def test_parallel_universe_empty_input_texture():
    plugin = DepthParallelUniversePlugin()
    ctx = PluginContext(MagicMock())
    res = plugin.process_frame(0, {}, ctx)
    assert res == 0

def test_parallel_universe_gl_full_pipeline():
    plugin = DepthParallelUniversePlugin()
    ctx = PluginContext(MagicMock())
    ctx.inputs = {"video_in": 1, "depth_in": 2, "universe_a_return": 3}
    ctx.outputs = {}
    
    with patch("vjlive3.plugins.depth_parallel_universe.gl") as mock_gl:
        # Mock successful shader compilation
        mock_gl.glGetShaderiv.return_value = 1 # GL_TRUE
        mock_gl.glGetProgramiv.return_value = 1 # GL_TRUE
        
        # Setup mocks that return ID lists
        mock_gl.glGenTextures.side_effect = [[11, 12, 13, 14], 15] # 4 for fb, 1 for prev
        
        plugin._mock_mode = False
        plugin.initialize(ctx)
        
        # Ensure it didn't fallback to mock
        assert plugin._mock_mode is False
        assert len(plugin.out_textures) == 4
        
        # Now process
        res = plugin.process_frame(1, {"depth_split_near": 0.5, "depth_split_far": 0.7}, ctx)
        
        # Verify texture outputs
        assert res == plugin.out_textures[0]
        assert ctx.outputs["video_out"] == plugin.out_textures[0]
        assert ctx.outputs["universe_b_send"] == plugin.out_textures[2]
        
        # Ensure process ran draw arrays
        mock_gl.glDrawArrays.assert_called()
