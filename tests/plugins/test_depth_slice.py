import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_slice import DepthSlicePlugin, METADATA
from vjlive3.plugins.api import PluginContext

def test_depth_slice_manifest():
    """Validates plugin manifest structure and expected parameters."""
    assert METADATA["name"] == "Depth Slice"
    assert "num_slices" in [p["name"] for p in METADATA["parameters"]]
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "video_out" in METADATA["outputs"]
    
    plugin = DepthSlicePlugin()
    assert plugin.name == "Depth Slice"
    assert plugin.params["num_slices"] == 8

def test_depth_slice_bypass():
    """Bypasses gracefully when depth texture is absent."""
    plugin = DepthSlicePlugin()
    context = MagicMock(spec=PluginContext)
    
    # Setup context returns: Video is present, Depth is NOT present
    def get_texture_mock(name):
        if name == "video_in":
            return 42 # Fake GL texture ID
        return None
        
    context.get_texture.side_effect = get_texture_mock
    plugin.initialize(context)
    plugin.process()
    
    # Should have called set_texture with video_out = 42 (passthrough)
    context.set_texture.assert_called_with("video_out", 42)

def test_depth_slice_processing_mock():
    """Tests normal execution when both textures are present."""
    plugin = DepthSlicePlugin()
    context = MagicMock(spec=PluginContext)
    
    # Setup context returns: Both are present
    def get_texture_mock(name):
        if name == "video_in": return 42
        if name == "depth_in": return 99
        return None
        
    def get_param_mock(name):
        if name == "depth_slice.num_slices": return 16
        if name == "depth_slice.slice_thickness": return 0.5
        return None
        
    context.get_texture.side_effect = get_texture_mock
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()
    
    # Verify params were read and clamped/updated
    assert plugin.params["num_slices"] == 16
    assert plugin.params["slice_thickness"] == 0.5
    
    # Should have emitted a new output texture
    context.set_texture.assert_called_with("video_out", 1042)

def test_depth_slice_missing_everything():
    plugin = DepthSlicePlugin()
    context = MagicMock(spec=PluginContext)
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    # process returns early, no texture outputs
    context.set_texture.assert_not_called()
    
def test_depth_slice_cleanup():
    plugin = DepthSlicePlugin()
    plugin.cleanup() # shouldn't crash
