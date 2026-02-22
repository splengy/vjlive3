import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_video_projection import DepthVideoProjectionPlugin, METADATA

def test_projection_manifest():
    """Verifies Pydantic manifest structure."""
    assert METADATA["name"] == "Depth Video Projection"
    assert "video_in" in METADATA["inputs"]
    assert "video_b_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "uv_scale" in [p["name"] for p in METADATA["parameters"]]
    assert "normal_lighting" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthVideoProjectionPlugin()
    assert plugin.name == "Depth Video Projection"

def test_projection_missing_depth():
    """Bypasses safely if depth is absent."""
    plugin = DepthVideoProjectionPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 99 if n == "video_in" else None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 99)

def test_projection_fallback_video_b():
    """Projects original video onto itself if video B is missing."""
    plugin = DepthVideoProjectionPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 100 if n == "video_in" else (500 if n == "depth_in" else None)
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 12100) # 100 + 12000

def test_projection_parameter_clamping():
    """Validates math clamping and dual texture inputs."""
    plugin = DepthVideoProjectionPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 100 if n == "video_in" else (200 if n == "video_b_in" else 300)
    
    def get_param_mock(name):
        if name == "video_projection.uv_scale": return 10.0 # Max is 5.0
        if name == "video_projection.hologram_glow": return -2.0 # Min is 0.0
        return None
        
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 12200) # video_b (200) + 12000
    
    assert plugin.params["uv_scale"] == 5.0
    assert plugin.params["hologram_glow"] == 0.0

def test_projection_missing_video():
    plugin = DepthVideoProjectionPlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_projection_no_context():
    plugin = DepthVideoProjectionPlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash
    
def test_projection_cleanup():
    plugin = DepthVideoProjectionPlugin()
    plugin.cleanup() # Ensure no trace
