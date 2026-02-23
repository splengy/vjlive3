import os
import pytest
import numpy as np
from typing import Dict, Any

from vjlive3.plugins.depth_contour_datamosh import DepthContourDatamoshPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    return DepthContourDatamoshPlugin()

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
    assert METADATA["name"] == "DepthContourDatamosh"
    assert "version" in METADATA
    assert "datamosh" in METADATA["tags"]
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "video_out" in METADATA["outputs"]
    
    # Check parameters
    params = METADATA["parameters"]
    names = [p["name"] for p in params]
    assert "contour_threshold" in names
    assert "contour_smoothness" in names
    assert "datamosh_intensity" in names
    assert "fragment_size" in names
    assert "glitch_probability" in names
    assert "preserve_edges" in names
    assert "color_shift" in names

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
    
    time_start = plugin.time_val
    result = plugin.process_frame(input_tex, {"preserve_edges": False}, context)
    time_end = plugin.time_val
    
    assert result == input_tex
    assert context.outputs["video_out"] == input_tex
    assert time_end > time_start # Verify time still increments

def test_plugin_cleanup(plugin):
    """Test cleanup runs without errors regardless of state"""
    try:
        plugin.cleanup()
    except Exception as e:
        pytest.fail(f"Cleanup raised exception: {e}")

from unittest.mock import MagicMock, patch

@patch('vjlive3.plugins.depth_contour_datamosh.gl')
@patch('vjlive3.plugins.depth_contour_datamosh.HAS_GL', True)
def test_full_gl_execution_defaults(mock_gl, plugin, context):
    """Test full initialization and rendering path using default strings"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin.prog is not None
    assert plugin._mock_mode is False
    
    params = {
        "contour_threshold": 0.2,
        "preserve_edges": False,
        "datamosh_intensity": 0.8
    }
    res = plugin.process_frame(123, params, context)
    assert res is not None
    
    mock_gl.glUniform1i.assert_called()
    mock_gl.glUniform1f.assert_called()

@patch('vjlive3.plugins.depth_contour_datamosh.gl')
@patch('vjlive3.plugins.depth_contour_datamosh.HAS_GL', True)
def test_full_gl_execution_custom_params(mock_gl, plugin, context):
    """Test execution with custom type mapped configurations"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    plugin._mock_mode = False
    plugin.initialize(context)
    
    params = {
        "contour_smoothness": 10,
        "fragment_size": 32,
        "preserve_edges": True, # Test boolean to integer cast
        "color_shift": 1.0
    }
    
    time_stamp_1 = plugin.time_val
    res = plugin.process_frame(123, params, context)
    time_stamp_2 = plugin.time_val
    
    assert res is not None
    assert time_stamp_2 > time_stamp_1

@patch('vjlive3.plugins.depth_contour_datamosh.gl')
@patch('vjlive3.plugins.depth_contour_datamosh.HAS_GL', True)
def test_gl_compile_failure(mock_gl, plugin, context):
    """Test shader compilation failure fallback to mock mode"""
    mock_gl.glGetShaderiv.return_value = False
    
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin._mock_mode is True

@patch('vjlive3.plugins.depth_contour_datamosh.gl')
@patch('vjlive3.plugins.depth_contour_datamosh.HAS_GL', True)
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
