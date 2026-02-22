import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_data_mux import DepthDataMuxEffect, METADATA
from vjlive3.plugins.api import PluginContext

def test_data_mux_manifest():
    """Verifies Pydantic/Dict manifest structure."""
    assert METADATA["name"] == "Depth Data Mux"
    assert "depth_in" in METADATA["inputs"]
    assert len(METADATA["outputs"]) >= 3
    assert "num_outputs" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthDataMuxEffect()
    assert plugin.name == "Depth Data Mux"

def test_data_mux_bypass():
    """Works cleanly when depth input is not provided."""
    plugin = DepthDataMuxEffect()
    context = MagicMock()
    
    def get_texture_mock(name):
        return None
        
    context.get_texture.side_effect = get_texture_mock
    
    plugin.initialize(context)
    plugin.process()
    
    # Assert nothing output
    context.set_texture.assert_not_called()

def test_data_mux_default_fanout():
    """Validates data fans out to exactly 3 textures by default."""
    plugin = DepthDataMuxEffect()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "depth_in": return 200
        return None
    
    def get_param_mock(name):
        return None
        
    context.get_texture.side_effect = get_texture_mock
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()
    
    assert context.set_texture.call_count == 3
    context.set_texture.assert_any_call("depth_out_1", 200)
    context.set_texture.assert_any_call("depth_out_2", 200)
    context.set_texture.assert_any_call("depth_out_3", 200)

def test_data_mux_dynamic_fanout():
    """Validates the output_select logic can dynamically grow the outputs."""
    plugin = DepthDataMuxEffect()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "depth_in": return 200
        return None
        
    def get_param_mock(name):
        if name == "depth_data_mux.num_outputs": return 8.0 # Growth!
        return None
        
    context.get_texture.side_effect = get_texture_mock
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()

    assert plugin.params["num_outputs"] == 8
    
    assert context.set_texture.call_count == 8
    context.set_texture.assert_any_call("depth_out_8", 200)

def test_data_mux_clamp_safety():
    plugin = DepthDataMuxEffect()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "depth_in": return 200
        return None
        
    def get_param_mock(name):
        if name == "depth_data_mux.num_outputs": return -5.0 # Underflow!
        return None
        
    context.get_texture.side_effect = get_texture_mock
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()

    assert plugin.params["num_outputs"] == 1 # Clamped to min 1
    
def test_data_mux_no_context():
    plugin = DepthDataMuxEffect()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash
    plugin.cleanup() # covers cleanup edge without throwing
