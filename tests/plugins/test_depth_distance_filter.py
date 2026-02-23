import os
import pytest
import numpy as np
from typing import Dict, Any

from vjlive3.plugins.depth_distance_filter import DepthDistanceFilterPlugin, METADATA

@pytest.fixture
def plugin():
    return DepthDistanceFilterPlugin()

@pytest.fixture
def context():
    ctx = MagicMock()(engine=None)
    ctx.inputs = {}
    ctx.outputs = {}
    ctx.inputs["depth_in"] = 123  # Mock texture ID
    ctx.width = 1920
    ctx.height = 1080
    return ctx

def test_plugin_metadata():
    """Verify metadata follows VJLive3 standards"""
    assert METADATA["name"] == "DepthDistanceFilter"
    assert "version" in METADATA
    assert "filter" in METADATA["tags"]
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "video_out" in METADATA["outputs"]
    
    # Check parameters
    params = METADATA["parameters"]
    names = [p["name"] for p in params]
    assert "filter_type" in names
    assert "near_distance" in names
    assert "blur_radius" in names
    assert "filter_strength" in names
    assert "brightness_shift" in names

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
    
    result = plugin.process_frame(input_tex, {"filter_type": "blur"}, context)
    
    assert result == input_tex
    assert context.outputs["video_out"] == input_tex

def test_plugin_cleanup(plugin):
    """Test cleanup runs without errors regardless of state"""
    try:
        plugin.cleanup()
    except Exception as e:
        pytest.fail(f"Cleanup raised exception: {e}")

from unittest.mock import MagicMock, patch

@patch('vjlive3.plugins.depth_distance_filter.gl')
@patch('vjlive3.plugins.depth_distance_filter.HAS_GL', True)
def test_full_gl_execution_defaults(mock_gl, plugin, context):
    """Test full initialization and rendering path using default strings"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin.prog is not None
    assert plugin._mock_mode is False
    
    res = plugin.process_frame(123, {}, context)
    assert res is not None
    
    mock_gl.glUniform1i.assert_called()
    mock_gl.glUniform1f.assert_called()

@patch('vjlive3.plugins.depth_distance_filter.gl')
@patch('vjlive3.plugins.depth_distance_filter.HAS_GL', True)
def test_full_gl_execution_strings_types(mock_gl, plugin, context):
    """Test filter_type string mapping strictly hitting all 5 configurations"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    plugin._mock_mode = False
    plugin.initialize(context)
    
    for f_type in ["fog", "blur", "contrast", "saturation", "brightness", "invalid_type"]:
        params = {
            "filter_type": f_type,
            "fog_color": [1.0, 0.5], # Test malformed arrays (len 2)
            "filter_strength": 0.8
        }
        res = plugin.process_frame(123, params, context)
        assert res is not None

@patch('vjlive3.plugins.depth_distance_filter.gl')
@patch('vjlive3.plugins.depth_distance_filter.HAS_GL', True)
def test_gl_compile_failure(mock_gl, plugin, context):
    """Test shader compilation failure fallback to mock mode"""
    mock_gl.glGetShaderiv.return_value = False
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin._mock_mode is True

@patch('vjlive3.plugins.depth_distance_filter.gl')
@patch('vjlive3.plugins.depth_distance_filter.HAS_GL', True)
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
