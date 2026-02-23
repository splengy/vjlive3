import os
import pytest
import numpy as np
from typing import Dict, Any

from vjlive3.plugins.depth_camera_splitter import DepthCameraSplitterPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    return DepthCameraSplitterPlugin()

@pytest.fixture
def context():
    ctx = PluginContext(engine=None)
    ctx.inputs = {}
    ctx.outputs = {}
    ctx.inputs["depth_in"] = 123  # Mock texture ID
    ctx.width = 1920
    ctx.height = 1080
    return ctx

def test_plugin_metadata():
    """Verify metadata follows VJLive3 standards"""
    assert METADATA["name"] == "DepthCameraSplitter"
    assert "version" in METADATA
    assert "camera" in METADATA["tags"]
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "video_out" in METADATA["outputs"]
    
    # Check parameters
    params = METADATA["parameters"]
    names = [p["name"] for p in params]
    assert "num_splits" in names
    assert "split_method" in names
    assert "custom_depths" in names
    assert "camera_offsets" in names
    assert "blend_edges" in names

def test_plugin_initialization_mock_mode(plugin, context):
    """Test plugin initializes safely without OpenGL context"""
    plugin._mock_mode = True
    plugin.initialize(context)
    assert plugin._mock_mode is True
    assert plugin.prog is None

def test_process_frame_empty_input(plugin, context):
    """Test handling of 0/None input texture"""
    res = plugin.process_frame(0, {}, context)
    assert res == 0
    res2 = plugin.process_frame(None, {}, context)
    assert res2 == 0

def test_process_frame_mock_mode(plugin, context):
    """Test process_frame falls back to passthrough correctly in mock mode"""
    plugin._mock_mode = True
    input_tex = 404
    
    result = plugin.process_frame(input_tex, {"num_splits": 3}, context)
    assert result == input_tex
    assert context.outputs["video_out"] == input_tex

def test_plugin_cleanup(plugin):
    """Test cleanup runs without errors regardless of state"""
    try:
        plugin.cleanup()
    except Exception as e:
        pytest.fail(f"Cleanup raised exception: {e}")

from unittest.mock import MagicMock, patch

@patch('vjlive3.plugins.depth_camera_splitter.gl')
@patch('vjlive3.plugins.depth_camera_splitter.HAS_GL', True)
def test_full_gl_execution_uniform(mock_gl, plugin, context):
    """Test full initialization and rendering path using uniform splits"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin.prog is not None
    assert plugin._mock_mode is False
    
    params = {
        "num_splits": 4,
        "split_method": "uniform",
        "blend_edges": True
    }
    res = plugin.process_frame(123, params, context)
    assert res is not None
    
    mock_gl.glUniform1fv.assert_called()
    mock_gl.glUniform4fv.assert_called()

@patch('vjlive3.plugins.depth_camera_splitter.gl')
@patch('vjlive3.plugins.depth_camera_splitter.HAS_GL', True)
def test_full_gl_execution_custom_splits_and_offsets(mock_gl, plugin, context):
    """Test execution with custom split boundaries and specific transform dictionaries"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    plugin._mock_mode = False
    plugin.initialize(context)
    
    params = {
        "num_splits": 3,
        "split_method": "custom",
        "custom_depths": [0.2, 0.4, 0.9],
        "camera_offsets": [
            {"offset_x": 0.1, "zoom": 1.5},
            {"offset_y": -0.2, "rotation": 3.14},
            {} # Empty dict fallback
        ],
        "blend_edges": False
    }
    res = plugin.process_frame(123, params, context)
    assert res is not None

@patch('vjlive3.plugins.depth_camera_splitter.gl')
@patch('vjlive3.plugins.depth_camera_splitter.HAS_GL', True)
def test_full_gl_execution_malformed_arrays(mock_gl, plugin, context):
    """Test graceful handling of bad offsets and out of bounds custom lengths"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    plugin._mock_mode = False
    plugin.initialize(context)
    
    params = {
        "num_splits": 10,  # over max bound 8
        "split_method": "custom",
        "custom_depths": [0.1], # under provided limits
        "camera_offsets": "NotAList" # String instead of list
    }
    # Should not crash Python or raise out of bounds
    res = plugin.process_frame(123, params, context)
    assert res is not None

@patch('vjlive3.plugins.depth_camera_splitter.gl')
@patch('vjlive3.plugins.depth_camera_splitter.HAS_GL', True)
def test_gl_compile_failure(mock_gl, plugin, context):
    """Test shader compilation failure fallback to mock mode"""
    mock_gl.glGetShaderiv.return_value = False
    
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin._mock_mode is True

@patch('vjlive3.plugins.depth_camera_splitter.gl')
@patch('vjlive3.plugins.depth_camera_splitter.HAS_GL', True)
def test_gl_cleanup(mock_gl, plugin, context):
    """Test cleanup of GL resources"""
    plugin._mock_mode = False
    plugin.out_tex = 1
    plugin.fbo = 1
    plugin.prog = 1
    plugin.vao = 1
    plugin.vbo = 1
    
    plugin.cleanup()
    
    mock_gl.glDeleteTextures.assert_called()
    mock_gl.glDeleteFramebuffers.assert_called()
    mock_gl.glDeleteProgram.assert_called()
    assert plugin.out_tex is None
