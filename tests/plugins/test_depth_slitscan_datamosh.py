import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_slitscan_datamosh import DepthSlitscanDatamoshPlugin, METADATA

def test_slitscan_manifest():
    """Verifies Pydantic manifest compatibility structure with heavy parameters."""
    assert METADATA["name"] == "Depth Slitscan Datamosh"
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "video_b_in" in METADATA["inputs"]
    assert "mosh_intensity" in [p["name"] for p in METADATA["parameters"]]
    assert "scan_direction" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthSlitscanDatamoshPlugin()
    assert plugin.name == "Depth Slitscan Datamosh"

def test_slitscan_missing_depth():
    """Validates missing depth passthrough logic."""
    plugin = DepthSlitscanDatamoshPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 112 if n == "video_in" else None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 112)

def test_slitscan_processing():
    """Validates math clamping and generic temporal accumulation simulation layout."""
    plugin = DepthSlitscanDatamoshPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 200 if n == "video_in" else (300 if n == "depth_in" else None)
    
    def get_param_mock(name):
        if name == "slitscan_datamosh.scan_direction": return 10.0 # Max is 3.0
        if name == "slitscan_datamosh.mosh_intensity": return -2.0 # Min is 0.0
        return None
        
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 14200) # 200 + 14000
    
    assert plugin.params["scan_direction"] == 3.0
    assert plugin.params["mosh_intensity"] == 0.0

def test_slitscan_fallback_b_in():
    """Validates it processes correctly with video b present"""
    plugin = DepthSlitscanDatamoshPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 200 if n == "video_in" else (300 if n == "depth_in" else 400) # 400 is video_b_in
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 14400) # video_b (400) + 14000

def test_slitscan_missing_video():
    plugin = DepthSlitscanDatamoshPlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_slitscan_no_context():
    plugin = DepthSlitscanDatamoshPlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash
    
def test_slitscan_cleanup():
    plugin = DepthSlitscanDatamoshPlugin()
    plugin.cleanup() # Ensure no trace
