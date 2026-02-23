import os
import pytest
import numpy as np
from typing import Dict, Any

from vjlive3.plugins.depth_data_mux import DepthDataMuxPlugin, METADATA

@pytest.fixture
def plugin():
    return DepthDataMuxPlugin()

@pytest.fixture
def context():
    ctx = MagicMock()(engine=None)
    ctx.inputs = {
        "depth1": 101,
        "depth2": 102,
        "depth3": 103,
        "depth4": 104
    }
    ctx.outputs = {}
    ctx.width = 1920
    ctx.height = 1080
    return ctx

def test_plugin_metadata():
    """Verify metadata follows EXT044 standards"""
    assert METADATA["name"] == "DepthDataMux"
    assert "version" in METADATA
    assert "depth1" in METADATA["inputs"]
    assert "depth4" in METADATA["inputs"]
    assert "composite_depth" in METADATA["outputs"]
    
    params = METADATA["parameters"]
    names = [p["name"] for p in params]
    assert "blend_mode" in names
    assert "priority_order" in names
    assert "fallback_depth" in names
    assert "weight4" in names

def test_plugin_initialization_mock_mode(plugin, context):
    """Test plugin initializes safely without OpenGL context"""
    plugin._mock_mode = True
    plugin.initialize(context)
    assert plugin._mock_mode is True
    assert plugin.prog is None

def test_process_frame_empty_inputs(plugin, context):
    """Test mock fallback when input dict is entirely empty"""
    plugin._mock_mode = True
    context.inputs = {}
    res = plugin.process_frame(0, {}, context)
    assert res == 0 # no inputs
    
def test_process_frame_partial_inputs_mock_mode(plugin, context):
    """Test mock fallback passes the first active texture"""
    plugin._mock_mode = True
    context.inputs = {"depth3": 999}
    res = plugin.process_frame(0, {}, context)
    assert res == 999
    assert context.outputs["composite_depth"] == 999

def test_plugin_cleanup(plugin):
    """Test cleanup runs without errors regardless of state"""
    try:
        plugin.cleanup()
    except Exception as e:
        pytest.fail(f"Cleanup raised exception: {e}")

from unittest.mock import MagicMock, patch

@patch('vjlive3.plugins.depth_data_mux.gl')
@patch('vjlive3.plugins.depth_data_mux.HAS_GL', True)
def test_full_gl_execution_average(mock_gl, plugin, context):
    """Test standard average blending over 4 active textures"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    plugin._mock_mode = False
    plugin.initialize(context)
    
    params = {
        "blend_mode": "average",
        "weight1": 0.5,
        "normalize": True
    }
    res = plugin.process_frame(0, params, context)
    assert res is not None
    mock_gl.glUniform1i.assert_called()

@patch('vjlive3.plugins.depth_data_mux.gl')
@patch('vjlive3.plugins.depth_data_mux.HAS_GL', True)
def test_full_gl_execution_max_min(mock_gl, plugin, context):
    """Test blending mode text parsing routing to the math shader uniforms"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    plugin._mock_mode = False
    plugin.initialize(context)
    
    params_max = {"blend_mode": "max"}
    res1 = plugin.process_frame(0, params_max, context)
    
    params_min = {"blend_mode": "min"}
    res2 = plugin.process_frame(0, params_min, context)
    
    assert res1 is not None and res2 is not None

@patch('vjlive3.plugins.depth_data_mux.gl')
@patch('vjlive3.plugins.depth_data_mux.HAS_GL', True)
def test_full_gl_execution_priority_logic(mock_gl, plugin, context):
    """Test priority_order iterating missing arrays without exceptions"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    plugin._mock_mode = False
    plugin.initialize(context)
    
    # Context only has depth2 and depth4 live
    context.inputs = {"depth2": 200, "depth4": 400} 
    
    # Valid priority array
    params = {
        "blend_mode": "priority1",
        "priority_order": [1, 3, 2, 4] # Should select index 2
    }
    plugin.process_frame(0, params, context)
    
    # Malformed array with illegal types and out-of-bounds indices
    params_err = {
        "blend_mode": "priority1",
        "priority_order": ["hello", None, 99, -1, 4] # Should evaluate index 4
    }
    res = plugin.process_frame(0, params_err, context)
    assert res is not None

@patch('vjlive3.plugins.depth_data_mux.gl')
@patch('vjlive3.plugins.depth_data_mux.HAS_GL', True)
def test_gl_compile_failure(mock_gl, plugin, context):
    """Test shader compilation failure fallback to mock mode"""
    mock_gl.glGetShaderiv.return_value = False
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin._mock_mode is True

@patch('vjlive3.plugins.depth_data_mux.gl')
@patch('vjlive3.plugins.depth_data_mux.HAS_GL', True)
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
