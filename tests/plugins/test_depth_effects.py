import os
import pytest
import numpy as np
from typing import Dict, Any

from vjlive3.plugins.depth_effects import DepthEffectsPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    return DepthEffectsPlugin()

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
    assert METADATA["name"] == "DepthEffects"
    assert "version" in METADATA
    assert "chain" in METADATA["tags"]
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "video_out" in METADATA["outputs"]
    
    # Check parameters
    params = METADATA["parameters"]
    names = [p["name"] for p in params]
    assert "effect_chain" in names
    assert "effect_order" in names
    assert "effect_params" in names
    assert "blend_mode" in names
    assert "blend_weights" in names
    assert "preserve_original" in names

def test_plugin_initialization_mock_mode(plugin, context):
    """Test plugin initializes safely without OpenGL context"""
    plugin._mock_mode = True
    plugin.initialize(context)
    assert plugin._mock_mode is True
    assert len(plugin.programs) == 0

def test_process_frame_empty_input(plugin, context):
    """Test handling of 0/None input texture"""
    res = plugin.process_frame(0, {}, context)
    assert res == 0
    res2 = plugin.process_frame(None, {}, context)
    assert res2 == 0

def test_process_frame_mock_mode(plugin, context):
    """Test process_frame falls back to passthrough correctly in mock mode"""
    plugin._mock_mode = True
    plugin.initialize(context)
    input_tex = 404
    
    result = plugin.process_frame(input_tex, {"effect_order": ["blur"]}, context)
    
    assert result == input_tex
    assert context.outputs["video_out"] == input_tex

def test_plugin_cleanup(plugin):
    """Test cleanup runs without errors regardless of state"""
    try:
        plugin.cleanup()
    except Exception as e:
        pytest.fail(f"Cleanup raised exception: {e}")

from unittest.mock import MagicMock, patch

@patch('vjlive3.plugins.depth_effects.gl')
@patch('vjlive3.plugins.depth_effects.HAS_GL', True)
def test_full_gl_execution_empty_chain(mock_gl, plugin, context):
    """Test full initialization safely routing an empty chain list"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    
    plugin._mock_mode = False
    plugin.initialize(context)
    assert len(plugin.programs) == 7 # (6 fx + 1 copy)
    
    res = plugin.process_frame(123, {"effect_order": []}, context)
    assert res == 123
    assert mock_gl.glBindFramebuffer.call_count == 6 # the 3 FBO creations (bind + unbind each)

@patch('vjlive3.plugins.depth_effects.gl')
@patch('vjlive3.plugins.depth_effects.HAS_GL', True)
def test_full_gl_execution_sequential(mock_gl, plugin, context):
    """Test full initialization and rendering path sequentially utilizing PingPong FBO swaps"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    
    plugin._mock_mode = False
    plugin.initialize(context)
    
    params = {
        "effect_order": ["blur", "color_grade", "distortion", "glow", "fog", "sharpen", "invalid_rule"],
        "blend_mode": "sequential",
        "effect_params": {
            "blur": {"radius": 10.0},
            "color_grade": {"color_shift": [1.0, 0.5]}, # malformed on purpose
            "glow": {"glow_color": 1} # invalid format
        },
        "preserve_original": True # will force an extra pass into fboB
    }
    
    res = plugin.process_frame(123, params, context)
    assert res is not None
    
    assert mock_gl.glBindFramebuffer.call_count >= 8 # Init(3) + 6 effects(6) + copy(1) + reset(2) = safe
    mock_gl.glUniform1i.assert_called()
    mock_gl.glUniform1f.assert_called()

@patch('vjlive3.plugins.depth_effects.gl')
@patch('vjlive3.plugins.depth_effects.HAS_GL', True)
def test_full_gl_execution_parallel_weighted(mock_gl, plugin, context):
    """Test parallel additive blending execution with dynamic weights array"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    
    plugin._mock_mode = False
    plugin.initialize(context)
    
    for mode in ["parallel", "weighted"]:
        params = {
            "effect_order": ["distortion", "fog"],
            "blend_mode": mode,
            "blend_weights": [0.3, "invalid", 0.9],
            "preserve_original": False
        }
        res = plugin.process_frame(123, params, context)
        assert res is not None

@patch('vjlive3.plugins.depth_effects.gl')
@patch('vjlive3.plugins.depth_effects.HAS_GL', True)
def test_gl_compile_failure(mock_gl, plugin, context):
    """Test shader compilation failure fallback to mock mode"""
    mock_gl.glGetShaderiv.return_value = False
    plugin._mock_mode = False
    plugin.initialize(context)
    assert plugin._mock_mode is True

@patch('vjlive3.plugins.depth_effects.gl')
@patch('vjlive3.plugins.depth_effects.HAS_GL', True)
def test_gl_cleanup(mock_gl, plugin, context):
    """Test strict native cleanup of all 3 GL resources and 7 programs"""
    plugin._mock_mode = False
    plugin.texA, plugin.fboA = 1, 1
    plugin.texB, plugin.fboB = 2, 2
    plugin.texOut, plugin.fboOut = 3, 3
    
    plugin.programs = {"test1": 1, "test2": 2}
    plugin.vao = 1
    plugin.vbo = 1
    
    plugin.cleanup()
    
    # Textures deleted
    assert mock_gl.glDeleteTextures.call_count >= 3
    # FBOs deleted
    assert mock_gl.glDeleteFramebuffers.call_count >= 3
    # Programs deleted
    assert mock_gl.glDeleteProgram.call_count >= 2
    assert len(plugin.programs) == 0
