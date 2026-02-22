import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_vector_field_datamosh import DepthVectorFieldDatamoshPlugin, METADATA

def test_vfd_manifest():
    """Verifies Pydantic manifest compatibility structure with heavy parameters."""
    assert METADATA["name"] == "Depth Vector Field Datamosh"
    assert "video_in" in METADATA["inputs"]
    assert "video_b_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "vector_scale" in [p["name"] for p in METADATA["parameters"]]
    assert "accumulation" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthVectorFieldDatamoshPlugin()
    assert plugin.name == "Depth Vector Field Datamosh"

def test_vfd_missing_depth():
    """Validates missing depth passthrough logic."""
    plugin = DepthVectorFieldDatamoshPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 118 if n == "video_in" else None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 118)

def test_vfd_processing():
    """Validates math clamping and generic vector accumulation simulation layout (base video)."""
    plugin = DepthVectorFieldDatamoshPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 200 if n == "video_in" else (300 if n == "depth_in" else None)
    
    def get_param_mock(name):
        if name == "vector_field.vector_scale": return 500.0 # Max is 1.0
        if name == "vector_field.accumulation": return -2.0 # Min is 0.0
        return None
        
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 18200) # 200 + 18000
    
    assert plugin.params["vector_scale"] == 1.0
    assert plugin.params["accumulation"] == 0.0

def test_vfd_fallback_video_b():
    """Validates it processes correctly with video b present"""
    plugin = DepthVectorFieldDatamoshPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 200 if n == "video_in" else (300 if n == "depth_in" else 400) # 400 is video_b_in
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 18400) # video_b (400) + 18000

def test_vfd_missing_video():
    plugin = DepthVectorFieldDatamoshPlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_vfd_no_context():
    plugin = DepthVectorFieldDatamoshPlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash
    
def test_vfd_cleanup():
    plugin = DepthVectorFieldDatamoshPlugin()
    plugin.cleanup() # Ensure no trace
