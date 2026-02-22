import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_contour_datamosh import DepthContourDatamoshPlugin, METADATA

def test_contour_datamosh_manifest():
    """Verifies Pydantic/Dict manifest structure."""
    assert METADATA["name"] == "Depth Contour Datamosh"
    assert "video_in" in METADATA["inputs"]
    assert "video_b_in" in METADATA["inputs"]
    assert "contour_intervals" in [p["name"] for p in METADATA["parameters"]]
    assert "contour_glow" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthContourDatamoshPlugin()
    assert plugin.name == "Depth Contour Datamosh"

def test_contour_datamosh_fbo_lifecycle():
    """Ensures no textures are left dangling after on_unload/cleanup."""
    plugin = DepthContourDatamoshPlugin()
    context = MagicMock()
    
    plugin.initialize(context)
    assert plugin._fbo_feedback_a is True
    assert plugin._fbo_feedback_b is True
    
    plugin.cleanup()
    assert plugin._fbo_feedback_a is False
    assert plugin._fbo_feedback_b is False

def test_contour_datamosh_bypass():
    """Works cleanly when depth_in is not provided."""
    plugin = DepthContourDatamoshPlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 444
        return None  # Missing depth
        
    context.get_texture.side_effect = get_texture_mock
    
    plugin.initialize(context)
    plugin.process()
    
    # Assert video passed through unmodified
    context.set_texture.assert_called_with("video_out", 444)

def test_contour_datamosh_processing_ping_pong():
    """Validates the FBO ping pong logic works with valid textures and clamps parameters."""
    plugin = DepthContourDatamoshPlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 100
        if name == "video_b_in": return 150
        if name == "depth_in": return 200
        return None
        
    def get_param_mock(name):
        if name == "contour_mosh.contour_intervals": return 128 # Overshoot (max 64)
        if name == "contour_mosh.mosh_intensity": return -0.5 # Undershoot (min 0)
        return None
        
    context.get_texture.side_effect = get_texture_mock
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    
    # State 0 initially
    assert plugin._ping_pong_state == 0
    
    # Process Frame 1
    plugin.process()
    assert plugin._ping_pong_state == 1
    context.set_texture.assert_called_with("video_out", 4150) # video_b_in (150) + 4000
    
    # Bound clamping verified
    assert plugin.params["contour_intervals"] == 64  # Clamped to max
    assert plugin.params["mosh_intensity"] == 0.0 # Clamped to min
    
    # Process Frame 2 (Ping-Pong back)
    plugin.process()
    assert plugin._ping_pong_state == 0
    context.set_texture.assert_called_with("video_out", 3150) # video_b_in (150) + 3000
    
def test_contour_datamosh_fallback_to_video_a():
    """If video_b_in is empty, mosh self using video_in instead."""
    plugin = DepthContourDatamoshPlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 100
        if name == "depth_in": return 200
        return None # No video_b_in
        
    context.get_texture.side_effect = get_texture_mock
    
    plugin.initialize(context)
    plugin.process()
    
    # Picks video_in since B is missing
    context.set_texture.assert_called_with("video_out", 4100) # 100 + 4000

def test_contour_datamosh_missing_video():
    plugin = DepthContourDatamoshPlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_contour_datamosh_no_context():
    plugin = DepthContourDatamoshPlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash
