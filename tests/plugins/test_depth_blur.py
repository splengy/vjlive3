import os
import pytest
import numpy as np
from typing import Dict, Any

from vjlive3.plugins.depth_blur import DepthBlurPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    return DepthBlurPlugin()

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
    assert METADATA["name"] == "DepthBlur"
    assert "version" in METADATA
    assert "depth" in METADATA["tags"]
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "video_out" in METADATA["outputs"]
    
    # Check parameters
    params = METADATA["parameters"]
    names = [p["name"] for p in params]
    assert "blur_radius" in names
    assert "focus_start" in names
    assert "transition_smoothness" in names
    assert "blur_type" in names
    assert "bokeh_shape" in names
    assert "anisotropic_scale" in names

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
    
    result = plugin.process_frame(input_tex, {"blur_radius": 10}, context)
    assert result == input_tex
    assert context.outputs["video_out"] == input_tex

def test_plugin_cleanup(plugin):
    """Test cleanup runs without errors regardless of state"""
    try:
        plugin.cleanup()
    except Exception as e:
        pytest.fail(f"Cleanup raised exception: {e}")

def test_all_metadata_parameters_have_bounds():
    """Verify all parameters have min/max/default or options"""
    for param in METADATA["parameters"]:
        assert "name" in param
        assert "type" in param
        
        if param["type"] == "str":
            assert "options" in param
        elif param["type"] != "bool":
            assert "min" in param
            assert "max" in param
            assert "default" in param
            assert param["min"] <= param["default"] <= param["max"]

from unittest.mock import MagicMock, patch

@patch('vjlive3.plugins.depth_blur.gl')
@patch('vjlive3.plugins.depth_blur.HAS_GL', True)
def test_full_gl_execution(mock_gl, plugin, context):
    """Test full initialization and rendering path using mocked GL with Gaussian setup"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin.prog is not None
    assert plugin._mock_mode is False
    
    # Process Frame
    res = plugin.process_frame(123, {"blur_radius": 15, "blur_type": "gaussian", "bokeh_shape": "circular"}, context)
    assert res is not None
    
    mock_gl.glUniform1f.assert_called()
    mock_gl.glUniform1i.assert_called()

@patch('vjlive3.plugins.depth_blur.gl')
@patch('vjlive3.plugins.depth_blur.HAS_GL', True)
def test_full_gl_execution_bokeh_hex(mock_gl, plugin, context):
    """Test full initialization and rendering path using mocked GL with Bokeh Hex setup"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    
    plugin._mock_mode = False
    plugin.initialize(context)
    
    # Process Frame (Forces other branch routines)
    res = plugin.process_frame(123, {"blur_radius": 15, "blur_type": "bokeh", "bokeh_shape": "hexagonal", "anisotropic_scale": 1.5}, context)
    assert res is not None
    
    # Octagonal + motion
    res = plugin.process_frame(123, {"blur_radius": 15, "blur_type": "motion", "bokeh_shape": "octagonal", "anisotropic_scale": 1.5}, context)
    assert res is not None

    # Anisotropic
    res = plugin.process_frame(123, {"blur_radius": 15, "blur_type": "anisotropic", "anisotropic_scale": 2.5}, context)
    assert res is not None


@patch('vjlive3.plugins.depth_blur.gl')
@patch('vjlive3.plugins.depth_blur.HAS_GL', True)
def test_gl_compile_failure(mock_gl, plugin, context):
    """Test shader compilation failure fallback to mock mode"""
    mock_gl.glGetShaderiv.return_value = False
    
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin._mock_mode is True

@patch('vjlive3.plugins.depth_blur.gl')
@patch('vjlive3.plugins.depth_blur.HAS_GL', True)
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
