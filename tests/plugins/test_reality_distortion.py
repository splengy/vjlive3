import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.reality_distortion import RealityDistortionPlugin, METADATA
from vjlive3.plugins.api import PluginContext

def test_reality_distortion_manifest():
    """Verifies Pydantic/Dict manifest structure."""
    assert METADATA["name"] == "Reality Distortion"
    assert "video_in" in METADATA["inputs"]
    assert "distortion_amount" in [p["name"] for p in METADATA["parameters"]]
    assert "chromatic_aberration" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = RealityDistortionPlugin()
    assert plugin.name == "Reality Distortion"

def test_reality_distortion_execution_with_depth():
    """Processing a frame completes without GL errors when depth is present."""
    plugin = RealityDistortionPlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 100
        if name == "depth_in": return 200
        return None
        
    def get_param_mock(name):
        if name == "reality_distortion.distortion_amount": return 2.0 # Overshoot
        if name == "reality_distortion.warp_frequency": return -5.0 # Undershoot
        return None
        
    context.get_texture.side_effect = get_texture_mock
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()
    
    # Bound clamping verified
    assert plugin.params["distortion_amount"] == 1.0  # Clamped to max
    assert plugin.params["warp_frequency"] == 0.0 # Clamped to min
    
    # Assert output texture
    context.set_texture.assert_called_with("video_out", 7877) # 100 + 7777

def test_reality_distortion_execution_without_depth():
    """Processing a frame completes and falls back to uniform distortion."""
    plugin = RealityDistortionPlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 100
        return None
        
    context.get_texture.side_effect = get_texture_mock
    
    plugin.initialize(context)
    plugin.process()
    
    # Assert output texture (different ID simulating uniform mapping)
    context.set_texture.assert_called_with("video_out", 7100) # 100 + 7000

def test_reality_distortion_missing_video():
    plugin = RealityDistortionPlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_reality_distortion_cleanup():
    plugin = RealityDistortionPlugin()
    plugin.cleanup() # shouldn't crash
