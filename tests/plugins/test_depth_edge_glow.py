import os
import pytest
import numpy as np
from typing import Dict, Any

from vjlive3.plugins.depth_edge_glow import DepthEdgeGlowPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    return DepthEdgeGlowPlugin()

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
    assert METADATA["name"] == "DepthEdgeGlow"
    assert "version" in METADATA
    assert "glow" in METADATA["tags"]
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "video_out" in METADATA["outputs"]
    
    # Check parameters
    params = METADATA["parameters"]
    names = [p["name"] for p in params]
    assert "glow_intensity" in names
    assert "glow_radius" in names
    assert "edge_threshold" in names
    assert "glow_color" in names
    assert "glow_falloff" in names
    assert "glow_only" in names
    assert "edge_smoothness" in names

def test_plugin_initialization_mock_mode(plugin, context):
    """Test plugin initializes safely without OpenGL context"""
    plugin._mock_mode = True
    plugin.initialize(context)
    assert plugin._mock_mode is True
    assert plugin.prog_edge is None
    assert plugin.prog_blur_h is None
    assert plugin.prog_blur_v is None

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
    
    result = plugin.process_frame(input_tex, {"glow_radius": 5}, context)
    
    assert result == input_tex
    assert context.outputs["video_out"] == input_tex

def test_plugin_cleanup(plugin):
    """Test cleanup runs without errors regardless of state"""
    try:
        plugin.cleanup()
    except Exception as e:
        pytest.fail(f"Cleanup raised exception: {e}")

from unittest.mock import MagicMock, patch

@patch('vjlive3.plugins.depth_edge_glow.gl')
@patch('vjlive3.plugins.depth_edge_glow.HAS_GL', True)
def test_full_gl_execution_defaults(mock_gl, plugin, context):
    """Test full initialization and rendering path using default strings"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin.prog_edge is not None
    assert plugin.prog_blur_h is not None
    assert plugin.prog_blur_v is not None
    assert plugin._mock_mode is False
    
    res = plugin.process_frame(123, {}, context)
    assert res is not None
    
    # 3 FBO switches should occur
    assert mock_gl.glBindFramebuffer.call_count >= 3
    # Uniforms assigned
    mock_gl.glUniform1i.assert_called()
    mock_gl.glUniform1f.assert_called()

@patch('vjlive3.plugins.depth_edge_glow.gl')
@patch('vjlive3.plugins.depth_edge_glow.HAS_GL', True)
def test_full_gl_execution_strings_types(mock_gl, plugin, context):
    """Test falloff string mapping across exponential, linear, and gaussian modes safely"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    plugin._mock_mode = False
    plugin.initialize(context)
    
    for falloff in ["linear", "exponential", "gaussian", "invalid"]:
        params = {
            "glow_falloff": falloff,
            "glow_only": True,
            "glow_color": [1.0, 0.5], # Verify malformed lists load safely
            "edge_smoothness": 5
        }
        res = plugin.process_frame(123, params, context)
        assert res is not None

@patch('vjlive3.plugins.depth_edge_glow.gl')
@patch('vjlive3.plugins.depth_edge_glow.HAS_GL', True)
def test_gl_compile_failure(mock_gl, plugin, context):
    """Test shader compilation failure fallback to mock mode"""
    mock_gl.glGetShaderiv.return_value = False
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin._mock_mode is True

@patch('vjlive3.plugins.depth_edge_glow.gl')
@patch('vjlive3.plugins.depth_edge_glow.HAS_GL', True)
def test_gl_cleanup(mock_gl, plugin, context):
    """Test cleanup of all 3 GL resources strictly"""
    plugin._mock_mode = False
    plugin.tex_out = 1
    plugin.fbo_out = 1
    plugin.tex_edge = 2
    plugin.fbo_edge = 2
    plugin.tex_blur_h = 3
    plugin.fbo_blur_h = 3
    
    plugin.prog_edge = 1
    plugin.prog_blur_h = 2
    plugin.prog_blur_v = 3
    
    plugin.vao = 1
    plugin.vbo = 1
    
    plugin.cleanup()
    
    # Textures deleted
    assert mock_gl.glDeleteTextures.call_count >= 3
    # FBOs deleted
    assert mock_gl.glDeleteFramebuffers.call_count >= 3
    # Programs deleted
    assert mock_gl.glDeleteProgram.call_count >= 3
