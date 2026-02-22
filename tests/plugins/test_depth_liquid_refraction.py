import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_liquid_refraction import DepthLiquidRefractionPlugin, METADATA

def test_liquid_manifest():
    """Verifies Pydantic manifest compatibility structure."""
    assert METADATA["name"] == "Depth Liquid Refraction"
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "chromatic_spread" in [p["name"] for p in METADATA["parameters"]]
    assert "frosted_glass" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthLiquidRefractionPlugin()
    assert plugin.name == "Depth Liquid Refraction"

def test_liquid_missing_depth():
    """Validates missing depth passthrough logic."""
    plugin = DepthLiquidRefractionPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 111 if n == "video_in" else None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 111)

def test_liquid_processing():
    """Validates math clamping and generic UV displacement simulation layout."""
    plugin = DepthLiquidRefractionPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 200 if n == "video_in" else (300 if n == "depth_in" else None)
    
    def get_param_mock(name):
        if name == "liquid_refraction.chromatic_spread": return 10.0 # Max is 1.0
        if name == "liquid_refraction.ripple_speed": return -2.0 # Min is 0.0
        return None
        
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 13200) # 200 + 13000
    
    assert plugin.params["chromatic_spread"] == 1.0
    assert plugin.params["ripple_speed"] == 0.0

def test_liquid_missing_video():
    plugin = DepthLiquidRefractionPlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_liquid_no_context():
    plugin = DepthLiquidRefractionPlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash
    
def test_liquid_cleanup():
    plugin = DepthLiquidRefractionPlugin()
    plugin.cleanup() # Ensure no trace
