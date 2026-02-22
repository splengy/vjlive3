import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_blur import DepthBlurPlugin, METADATA

def test_depth_blur_manifest():
    """Verifies Pydantic/Dict manifest structure."""
    assert METADATA["name"] == "Depth Blur"
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "tilt_shift" in [p["name"] for p in METADATA["parameters"]]
    assert "focal_distance" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthBlurPlugin()
    assert plugin.name == "Depth Blur"

def test_depth_blur_tilt_shift_fallback():
    """Validates that missing depth input auto-engages tilt-shift mode without error."""
    plugin = DepthBlurPlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 100
        return None
        
    context.get_texture.side_effect = get_texture_mock
    
    plugin.initialize(context)
    plugin.process()
    
    assert plugin._is_tilt_shift_active is True
    context.set_texture.assert_called_with("video_out", 1110) # 100 + 1010

def test_depth_blur_normal_execution():
    """Validates processing with depth input avoids fallback mode and clamps parameters."""
    plugin = DepthBlurPlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 100
        if name == "depth_in": return 200
        return None
        
    def get_param_mock(name):
        if name == "depth_blur.focal_distance": return 5.0 # Overshoot > 1.0
        if name == "depth_blur.bokeh_bright": return -1.0 # Undershoot < 0.0
        return None
        
    context.get_texture.side_effect = get_texture_mock
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()
    
    assert plugin._is_tilt_shift_active is False
    assert plugin.params["focal_distance"] == 1.0
    assert plugin.params["bokeh_bright"] == 0.0
    
    context.set_texture.assert_called_with("video_out", 2120) # 100 + 2020

def test_depth_blur_missing_video():
    plugin = DepthBlurPlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_depth_blur_no_context():
    plugin = DepthBlurPlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash

def test_depth_blur_cleanup():
    plugin = DepthBlurPlugin()
    plugin.cleanup()
