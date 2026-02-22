import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_color_grade import DepthColorGradePlugin, METADATA

def test_depth_color_grade_manifest():
    """Verifies Pydantic/Dict manifest structure."""
    assert METADATA["name"] == "Depth Color Grade"
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "zone_near" in [p["name"] for p in METADATA["parameters"]]
    assert "zone_far" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthColorGradePlugin()
    assert plugin.name == "Depth Color Grade"

def test_depth_color_grade_missing_depth():
    """Validates fallback to Mid zone grading if depth is omitted."""
    plugin = DepthColorGradePlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 100
        return None
        
    context.get_texture.side_effect = get_texture_mock
    
    plugin.initialize(context)
    plugin.process()
    
    assert plugin._missing_depth is True
    context.set_texture.assert_called_with("video_out", 655) # 100 + 555

def test_depth_color_grade_zone_swap():
    """Prevents math errors if zone_near is pushed past zone_far."""
    plugin = DepthColorGradePlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 100
        if name == "depth_in": return 200
        return None
        
    def get_param_mock(name):
        # Deliberately setting Near > Far
        if name == "color_grade.zone_near": return 0.8
        if name == "color_grade.zone_far": return 0.2
        if name == "color_grade.mid_saturation": return 3.0 # Overshoot max 2.0
        return None
        
    context.get_texture.side_effect = get_texture_mock
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()
    
    assert plugin._missing_depth is False
    assert plugin.params["zone_near"] == 0.2
    assert plugin.params["zone_far"] == 0.8
    assert plugin.params["mid_saturation"] == 2.0 # Saturation clamp
    
    context.set_texture.assert_called_with("video_out", 1099) # 100 + 999

def test_depth_color_grade_missing_video():
    plugin = DepthColorGradePlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_depth_color_grade_no_context():
    plugin = DepthColorGradePlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash

def test_depth_color_grade_cleanup():
    plugin = DepthColorGradePlugin()
    plugin.cleanup()
