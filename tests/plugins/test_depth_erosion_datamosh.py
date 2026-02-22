import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_erosion_datamosh import DepthErosionDatamoshPlugin, METADATA

def test_erosion_datamosh_manifest():
    """Verifies Pydantic/Dict manifest structure."""
    assert METADATA["name"] == "Depth Erosion Datamosh"
    assert "video_in" in METADATA["inputs"]
    assert "video_b_in" in METADATA["inputs"]
    assert "morph_mode" in [p["name"] for p in METADATA["parameters"]]
    assert "feedback_decay" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthErosionDatamoshPlugin()
    assert plugin.name == "Depth Erosion Datamosh"

def test_erosion_datamosh_missing_inputs():
    """Verifies that missing video_b or depth_in does not crash."""
    plugin = DepthErosionDatamoshPlugin()
    context = MagicMock()
    
    # 1. Missing depth_in (should bypass with video_in)
    context.get_texture.side_effect = lambda n: 100 if n == "video_in" else None
    plugin.initialize(context)
    plugin.process()
    context.set_texture.assert_called_with("video_out", 100)
    
    # 2. Missing video_b_in but has depth (should self-mosh video_in)
    context.get_texture.side_effect = lambda n: 100 if n == "video_in" else (200 if n == "depth_in" else None)
    plugin.process()
    # Ping-pong starts at 0 -> flips to 1 -> returns 100 + 8000
    context.set_texture.assert_called_with("video_out", 8100)

def test_erosion_datamosh_processing_ping_pong():
    """Validates ping-pong logic and param clamping."""
    plugin = DepthErosionDatamoshPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 100 if n == "video_in" else (150 if n == "video_b_in" else 200)
    
    def get_param_mock(name):
        if name == "erosion_mosh.morph_mode": return 5 # Overshoot (max 3)
        if name == "erosion_mosh.feedback_decay": return -0.5 # Undershoot (min 0)
        return None
        
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    
    # Process Frame 1
    plugin.process()
    assert plugin._ping_pong_state == 1
    context.set_texture.assert_called_with("video_out", 8150) # video_b_in (150) + 8000
    
    # Clamping verified
    assert plugin.params["morph_mode"] == 3
    assert plugin.params["feedback_decay"] == 0.0
    
    # Process Frame 2
    plugin.process()
    assert plugin._ping_pong_state == 0
    context.set_texture.assert_called_with("video_out", 7150) # video_b_in (150) + 7000

def test_erosion_datamosh_fbo_lifecycle():
    """Ensures FBOs are destroyed explicitly on cleanup."""
    plugin = DepthErosionDatamoshPlugin()
    context = MagicMock()
    
    plugin.initialize(context)
    assert plugin._fbo_feedback_a is True
    
    plugin.cleanup()
    assert plugin._fbo_feedback_a is False

def test_erosion_datamosh_missing_video():
    plugin = DepthErosionDatamoshPlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_erosion_datamosh_no_context():
    plugin = DepthErosionDatamoshPlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash
