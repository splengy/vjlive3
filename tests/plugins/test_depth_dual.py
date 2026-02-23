import os
import pytest
import numpy as np
from typing import Dict, Any

from vjlive3.plugins.depth_dual import DepthDualPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    return DepthDualPlugin()

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
    assert METADATA["name"] == "DepthDual"
    assert "version" in METADATA
    assert "composite" in METADATA["tags"]
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "video_out" in METADATA["outputs"]
    
    # Check parameters
    params = METADATA["parameters"]
    names = [p["name"] for p in params]
    assert "effect_a_type" in names
    assert "effect_b_type" in names
    assert "blend_mode" in names
    assert "effect_a_params" in names
    assert "effect_b_params" in names

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
    
    result = plugin.process_frame(input_tex, {"blend_mode": "depth"}, context)
    
    assert result == input_tex
    assert context.outputs["video_out"] == input_tex

def test_plugin_cleanup(plugin):
    """Test cleanup runs without errors regardless of state"""
    try:
        plugin.cleanup()
    except Exception as e:
        pytest.fail(f"Cleanup raised exception: {e}")

def test_parse_params_to_vec4(plugin):
    """Evaluate dict -> vec4 arrays without GL calls to assure dictionary mapping logic is solid"""
    res1 = plugin._parse_params_to_vec4("blur", {"radius": 0.8})
    assert res1[0] == 0.8
    assert res1[1] == 0.0
    
    res2 = plugin._parse_params_to_vec4("color_grade", {"tint": [0.5, 0.4, 0.3], "intensity": 0.9})
    assert res2[0] == 0.5
    assert res2[3] == 0.9
    
    res3 = plugin._parse_params_to_vec4("distortion", {"frequency": 0.2, "amplitude": 0.1})
    assert res3[0] == 0.2
    assert res3[1] == 0.1
    
    # Failures / empty / unexpected formats
    res_err1 = plugin._parse_params_to_vec4("color_grade", {"tint": "not_an_array"})
    res_err2 = plugin._parse_params_to_vec4("blur", None)
    assert res_err1[0] == 1.0 # default tint
    assert res_err2[0] == 0.5 # default radius

from unittest.mock import MagicMock, patch

@patch('vjlive3.plugins.depth_dual.gl')
@patch('vjlive3.plugins.depth_dual.HAS_GL', True)
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

@patch('vjlive3.plugins.depth_dual.gl')
@patch('vjlive3.plugins.depth_dual.HAS_GL', True)
def test_full_gl_execution_strings_types(mock_gl, plugin, context):
    """Test effect_type string mapping across various blends hitting the dictionary routines"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    plugin._mock_mode = False
    plugin.initialize(context)
    
    for blend in ["depth", "uniform", "radial", "custom", "invalid_mode"]:
        for ef_type in ["blur", "color_grade", "distortion", "none", "invalid_type"]:
            params = {
                "blend_mode": blend,
                "effect_a_type": ef_type,
                "effect_b_type": "blur",
                "effect_a_params": {"radius": 0.5},
                "effect_b_params": {"radius": 0.2},
                "invert_blend": True
            }
            res = plugin.process_frame(123, params, context)
            assert res is not None

@patch('vjlive3.plugins.depth_dual.gl')
@patch('vjlive3.plugins.depth_dual.HAS_GL', True)
def test_gl_compile_failure(mock_gl, plugin, context):
    """Test shader compilation failure fallback to mock mode"""
    mock_gl.glGetShaderiv.return_value = False
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin._mock_mode is True

@patch('vjlive3.plugins.depth_dual.gl')
@patch('vjlive3.plugins.depth_dual.HAS_GL', True)
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
