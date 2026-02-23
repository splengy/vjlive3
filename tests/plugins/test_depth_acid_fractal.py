import os
import pytest
import numpy as np
from typing import Dict, Any

from vjlive3.plugins.depth_acid_fractal import DepthAcidFractalDatamoshPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    return DepthAcidFractalDatamoshPlugin()

@pytest.fixture
def context():
    ctx = PluginContext(engine=None)
    ctx.inputs = {}
    ctx.outputs = {}
    ctx.inputs["depth_in"] = 123  # Mock texture ID
    return ctx
    return ctx

def test_plugin_metadata():
    """Verify metadata follows VJLive3 standards"""
    assert METADATA["name"] == "DepthAcidFractalDatamoshEffect"
    assert "version" in METADATA
    assert "fractal" in METADATA["tags"]
    assert "depth_in" in METADATA["inputs"]
    assert "video_out" in METADATA["outputs"]
    
    # Check parameters
    params = METADATA["parameters"]
    names = [p["name"] for p in params]
    assert "fractal_type" in names
    assert "datamosh_strength" in names
    assert "color_shift" in names
    assert "zoom" in names

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
    
    result = plugin.process_frame(input_tex, {"fractal_type": 1}, context)
    assert result == input_tex
    assert context.outputs["video_out"] == input_tex

def test_plugin_cleanup(plugin):
    """Test cleanup runs without errors regardless of state"""
    try:
        plugin.cleanup()
    except Exception as e:
        pytest.fail(f"Cleanup raised exception: {e}")

def test_all_metadata_parameters_have_bounds():
    """Verify all parameters have min/max/default"""
    for param in METADATA["parameters"]:
        assert "name" in param
        assert "type" in param
        assert "min" in param
        assert "max" in param
        assert "default" in param
        assert param["min"] <= param["default"] <= param["max"]

from unittest.mock import MagicMock, patch

@patch('vjlive3.plugins.depth_acid_fractal.gl')
@patch('vjlive3.plugins.depth_acid_fractal.HAS_GL', True)
def test_full_gl_execution(mock_gl, plugin, context):
    """Test full initialization and rendering path using mocked GL"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    
    # Initialize
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin.prog is not None
    assert plugin._mock_mode is False
    
    # Process Frame
    res = plugin.process_frame(123, {"fractal_type": 1}, context)
    assert res is not None
    
    # Ensure uniform binding occurred
    mock_gl.glUniform1f.assert_called()

@patch('vjlive3.plugins.depth_acid_fractal.gl')
@patch('vjlive3.plugins.depth_acid_fractal.HAS_GL', True)
def test_gl_compile_failure(mock_gl, plugin, context):
    """Test shader compilation failure fallback to mock mode"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin._mock_mode is True

@patch('vjlive3.plugins.depth_acid_fractal.gl')
@patch('vjlive3.plugins.depth_acid_fractal.HAS_GL', True)
def test_gl_cleanup(mock_gl, plugin, context):
    """Test cleanup of GL resources"""
    plugin._mock_mode = False
    plugin.textures["feedback_0"] = 1
    plugin.fbos["feedback_0"] = 1
    plugin.prog = 1
    plugin.vao = 1
    plugin.vbo = 1
    
    plugin.cleanup()
    
    mock_gl.glDeleteTextures.assert_called()
    mock_gl.glDeleteFramebuffers.assert_called()
    mock_gl.glDeleteProgram.assert_called()
    assert plugin.textures["feedback_0"] is None
