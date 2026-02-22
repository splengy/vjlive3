import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_acid_fractal import DepthAcidFractalPlugin, METADATA
from vjlive3.plugins.api import PluginContext

def test_acid_fractal_manifest():
    """Verifies Pydantic/Dict manifest structure."""
    assert METADATA["name"] == "Depth Acid Fractal"
    assert "video_in" in METADATA["inputs"]
    assert "fractal_intensity" in [p["name"] for p in METADATA["parameters"]]
    assert "prism_split" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthAcidFractalPlugin()
    assert plugin.name == "Depth Acid Fractal"

def test_acid_fractal_fbo_cleanup():
    """Ensures no textures are left dangling after on_unload/cleanup."""
    plugin = DepthAcidFractalPlugin()
    context = MagicMock()
    
    plugin.initialize(context)
    assert plugin._fbo_feedback_a is True
    assert plugin._fbo_feedback_b is True
    
    plugin.cleanup()
    assert plugin._fbo_feedback_a is False
    assert plugin._fbo_feedback_b is False

def test_acid_fractal_bypass():
    """Works cleanly when depth_in is not provided."""
    plugin = DepthAcidFractalPlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 444
        return None
        
    context.get_texture.side_effect = get_texture_mock
    
    plugin.initialize(context)
    plugin.process()
    
    # Assert video passed through unmodified
    context.set_texture.assert_called_with("video_out", 444)

def test_acid_fractal_processing_ping_pong():
    """Validates the FBO ping pong logic works with valid textures and clamps parameters."""
    plugin = DepthAcidFractalPlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 100
        if name == "depth_in": return 200
        return None
        
    def get_param_mock(name):
        if name == "acid_fractal.zoom_blur": return 5.0 # Overshoot
        if name == "acid_fractal.prism_split": return -1.0 # Undershoot
        return None
        
    context.get_texture.side_effect = get_texture_mock
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    
    # State 0 initially
    assert plugin._ping_pong_state == 0
    
    # Process Frame 1
    plugin.process()
    assert plugin._ping_pong_state == 1
    context.set_texture.assert_called_with("video_out", 10099) # 100 + 9999
    
    # Bound clamping verified
    assert plugin.params["zoom_blur"] == 1.0  # Clamped to max
    assert plugin.params["prism_split"] == 0.0 # Clamped to min
    
    # Process Frame 2 (Ping-Pong back)
    plugin.process()
    assert plugin._ping_pong_state == 0
    context.set_texture.assert_called_with("video_out", 9100) # 100 + 9000

def test_acid_fractal_missing_video():
    plugin = DepthAcidFractalPlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_acid_fractal_no_context():
    plugin = DepthAcidFractalPlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash
