import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_fracture_datamosh import DepthFractureDatamoshPlugin, METADATA

def test_fracture_datamosh_manifest():
    """Verifies Pydantic/Dict manifest structure."""
    assert METADATA["name"] == "Depth Fracture Datamosh"
    assert "video_in" in METADATA["inputs"]
    assert "video_b_in" in METADATA["inputs"]
    assert "fracture_sensitivity" in [p["name"] for p in METADATA["parameters"]]
    assert "fracture_decay" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthFractureDatamoshPlugin()
    assert plugin.name == "Depth Fracture Datamosh"

def test_fracture_datamosh_fbo_lifecycle():
    """Validates that dual ping-pong FBOs are created and destroyed cleanly without VRAM leaks."""
    plugin = DepthFractureDatamoshPlugin()
    context = MagicMock()
    
    plugin.initialize(context)
    assert plugin._fbo_cracks_a is True
    assert plugin._fbo_mosh_b is True
    
    plugin.cleanup()
    assert plugin._fbo_cracks_a is False
    assert plugin._fbo_cracks_b is False
    assert plugin._fbo_mosh_a is False
    assert plugin._fbo_mosh_b is False

def test_fracture_datamosh_missing_inputs():
    """Verifies missing depth and video_b bypass rules."""
    plugin = DepthFractureDatamoshPlugin()
    context = MagicMock()
    
    # Missing Depth: Pass video_in -> 100
    context.get_texture.side_effect = lambda n: 100 if n == "video_in" else None
    plugin.initialize(context)
    plugin.process()
    context.set_texture.assert_called_with("video_out", 100)
    
    # Missing video_b: Self-Moshes video_in (100) -> 100 + 9999
    context.get_texture.side_effect = lambda n: 100 if n == "video_in" else (200 if n == "depth_in" else None)
    plugin.process()
    context.set_texture.assert_called_with("video_out", 10099)

def test_fracture_datamosh_processing_ping_pong():
    """Test ping pong simulation and clamping on valid dual input."""
    plugin = DepthFractureDatamoshPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 100 if n == "video_in" else (150 if n == "video_b_in" else 200)
    
    def get_param_mock(name):
        if name == "fracture.fracture_decay": return 5.0 # Overshoot
        if name == "fracture.displacement_strength": return -0.5 # Undershoot
        return None
        
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    
    plugin.process()
    assert plugin._ping_pong_state == 1
    context.set_texture.assert_called_with("video_out", 10149) # 150 + 9999
    
    # Verify bounds control
    assert plugin.params["fracture_decay"] == 1.0
    assert plugin.params["displacement_strength"] == 0.0
    
    plugin.process()
    assert plugin._ping_pong_state == 0
    context.set_texture.assert_called_with("video_out", 9150) # 150 + 9000

def test_fracture_datamosh_missing_video():
    plugin = DepthFractureDatamoshPlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_fracture_datamosh_no_context():
    plugin = DepthFractureDatamoshPlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash
