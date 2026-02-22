import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_temporal_strat import DepthTemporalStratPlugin, METADATA

def test_strat_manifest():
    """Verifies Pydantic manifest compatibility structure with heavy parameters."""
    assert METADATA["name"] == "Depth Temporal Stratification"
    assert "video_in" in METADATA["inputs"]
    assert "video_b_in" in METADATA["inputs"]
    assert "depth_in" in METADATA["inputs"]
    assert "num_strata" in [p["name"] for p in METADATA["parameters"]]
    assert "color_shift" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthTemporalStratPlugin()
    assert plugin.name == "Depth Temporal Stratification"

def test_strat_missing_depth():
    """Validates missing depth passthrough logic."""
    plugin = DepthTemporalStratPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 116 if n == "video_in" else None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 116)

def test_strat_processing():
    """Validates math clamping and generic temporal accumulation simulation layout (base video)."""
    plugin = DepthTemporalStratPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 200 if n == "video_in" else (300 if n == "depth_in" else None)
    
    def get_param_mock(name):
        if name == "temporal_strat.num_strata": return 500.0 # Max is 12.0
        if name == "temporal_strat.seam_width": return -2.0 # Min is 0.0
        return None
        
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 16200) # 200 + 16000
    
    assert plugin.params["num_strata"] == 12.0
    assert plugin.params["seam_width"] == 0.0

def test_strat_fallback_video_b():
    """Validates it processes correctly with video b present"""
    plugin = DepthTemporalStratPlugin()
    context = MagicMock()
    
    context.get_texture.side_effect = lambda n: 200 if n == "video_in" else (300 if n == "depth_in" else 400) # 400 is video_b_in
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_called_with("video_out", 16400) # video_b (400) + 16000

def test_strat_missing_video():
    plugin = DepthTemporalStratPlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_strat_no_context():
    plugin = DepthTemporalStratPlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash
    
def test_strat_cleanup():
    plugin = DepthTemporalStratPlugin()
    plugin.cleanup() # Ensure no trace
