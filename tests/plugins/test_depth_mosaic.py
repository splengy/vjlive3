import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_mosaic import DepthMosaicPlugin, METADATA

def test_mosaic_manifest():
    """Verifies Pydantic/Dict manifest structure."""
    assert METADATA["name"] == "Depth Mosaic"
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "cell_size_min" in [p["name"] for p in METADATA["parameters"]]
    assert "gap_width" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthMosaicPlugin()
    assert plugin.name == "Depth Mosaic"

def test_mosaic_missing_depth():
    """Works cleanly by bypassing when depth_in is not provided."""
    plugin = DepthMosaicPlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 444
        return None  # Missing depth
        
    context.get_texture.side_effect = get_texture_mock
    
    plugin.initialize(context)
    plugin.process()
    
    # Assert video passed through unmodified
    context.set_texture.assert_called_with("video_out", 444)

def test_mosaic_processing_valid_inputs():
    """Validates the mosaic shader logic offset and parameter clamping."""
    plugin = DepthMosaicPlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 100
        if name == "depth_in": return 200
        return None
        
    def get_param_mock(name):
        if name == "mosaic.cell_size_min": return 80.0 # Overshoot (max 20)
        if name == "mosaic.gap_width": return -2.0 # Undershoot (min 0)
        return None
        
    context.get_texture.side_effect = get_texture_mock
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()
    
    # Check texture transformation offset
    context.set_texture.assert_called_with("video_out", 11100) # 100 + 11000
    
    # Check bound clamping
    assert plugin.params["cell_size_min"] == 20.0
    assert plugin.params["gap_width"] == 0.0

def test_mosaic_missing_video():
    plugin = DepthMosaicPlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_mosaic_no_context():
    plugin = DepthMosaicPlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash
    
def test_mosaic_cleanup():
    plugin = DepthMosaicPlugin()
    plugin.cleanup() # Ensure no errors
