import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from vjlive3.plugins.depth_acid_fractal_datamosh import DepthAcidFractalDatamoshEffectPlugin
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def mock_gl():
    with patch("vjlive3.plugins.depth_acid_fractal_datamosh.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 1
        mock_gl.glGetProgramiv.return_value = 1
        mock_gl.glGenFramebuffers.return_value = 100
        mock_gl.glGenTextures.side_effect = [200, 201]  # tex, prev_tex
        mock_gl.glGenVertexArrays.return_value = 300
        mock_gl.glGenBuffers.return_value = 400
        mock_gl.glCheckFramebufferStatus.return_value = 36053 # GL_FRAMEBUFFER_COMPLETE
        yield mock_gl

class MutableContext(PluginContext):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.outputs = {}

def test_acid_fractal_manifest():
    plugin = DepthAcidFractalDatamoshEffectPlugin()
    meta = plugin.get_metadata()
    assert meta["name"] == "DepthAcidFractalDatamoshEffect"
    assert "datamosh_intensity" in [p["name"] for p in meta["parameters"]]

def test_acid_fractal_mock_mode():
    with patch("vjlive3.plugins.depth_acid_fractal_datamosh.HAS_GL", False):
        plugin = DepthAcidFractalDatamoshEffectPlugin()
        ctx = MutableContext(inputs={"video_in": 5}, width=1920, height=1080)
        
        plugin.initialize(ctx)
        out = plugin.process_frame(5, {}, ctx)
        
        assert out == 5
        assert ctx.outputs["video_out"] == 5

def test_acid_fractal_missing_depth(mock_gl):
    # Safety Rail #7 validation
    plugin = DepthAcidFractalDatamoshEffectPlugin()
    plugin._mock_mode = False
    
    ctx = MutableContext(inputs={"video_in": 5}, width=1920, height=1080, time=1.0)
    plugin.initialize(ctx)
    plugin.process_frame(5, {"fractal_scale": 3.0}, ctx)
    
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(plugin.prog, "has_depth"), 0)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(plugin.prog, "fractal_scale"), 3.0)

def test_acid_fractal_with_depth(mock_gl):
    plugin = DepthAcidFractalDatamoshEffectPlugin()
    plugin._mock_mode = False
    
    ctx = MutableContext(inputs={"depth_in": 10}, width=1920, height=1080, time=1.0)
    plugin.initialize(ctx)
    plugin.process_frame(5, {}, ctx)
    
    # Verify depth mapping correctly activated
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(plugin.prog, "has_depth"), 1)
    # prev_tex is bound to texture unit 2
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(plugin.prog, "prevTex"), 2)

def test_acid_fractal_cleanup(mock_gl):
    # Safety Rail #8 validation
    plugin = DepthAcidFractalDatamoshEffectPlugin()
    plugin._mock_mode = False
    
    ctx = MutableContext(inputs={}, width=1920, height=1080)
    plugin.initialize(ctx)
    plugin.process_frame(5, {}, ctx)
    
    plugin.cleanup()
    
    assert mock_gl.glDeleteTextures.call_count >= 2
    mock_gl.glDeleteTextures.assert_any_call(1, [200]) # tex
    mock_gl.glDeleteTextures.assert_any_call(1, [201]) # prev_tex
    mock_gl.glDeleteFramebuffers.assert_any_call(1, [100])
    mock_gl.glDeleteBuffers.assert_any_call(1, [400])
    mock_gl.glDeleteVertexArrays.assert_any_call(1, [300])
