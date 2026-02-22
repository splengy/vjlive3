import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_temporal_echo import DepthTemporalEchoPlugin, METADATA

def test_echo_manifest():
    """Verifies Pydantic manifest compatibility structure with heavy parameters."""
    assert METADATA["name"] == "Depth Temporal Echo"
    assert "video_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "echo_depth" in [p["name"] for p in METADATA["parameters"]]
    assert "blend_mode" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthTemporalEchoPlugin()
    assert plugin.name == "Depth Temporal Echo"

def test_echo_missing_depth():
    """Validates missing depth passthrough logic."""
    plugin = DepthTemporalEchoPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 115 if n == "video_in" else None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 115)

def test_echo_processing():
    """Validates math clamping and generic temporal history accumulation layout."""
    plugin = DepthTemporalEchoPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 200 if n == "video_in" else (300 if n == "depth_in" else None)
    
    def get_param_mock(name):
        if name == "temporal_echo.echo_depth": return 500.0 # Max is 120.0
        if name == "temporal_echo.near_delay": return -2.0 # Min is 0.0
        return None
        
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 15200) # 200 + 15000
    
    assert plugin.params["echo_depth"] == 120.0
    assert plugin.params["near_delay"] == 0.0

def test_echo_missing_video():
    plugin = DepthTemporalEchoPlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_echo_no_context():
    plugin = DepthTemporalEchoPlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash
    
def test_echo_cleanup():
    plugin = DepthTemporalEchoPlugin()
    plugin.cleanup() # Ensure no trace
