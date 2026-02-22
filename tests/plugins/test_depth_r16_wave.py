import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.depth_r16_wave import DepthR16WavePlugin, METADATA
from vjlive3.plugins.api import PluginContext

def test_r16_wave_manifest():
    """Verifies Pydantic/Dict manifest structure and dual-output configuration."""
    assert METADATA["name"] == "R16 Depth Wave"
    assert "video_in" in METADATA["inputs"]
    assert "depth_raw_in" in METADATA["inputs"]
    assert "video_out" in METADATA["outputs"]
    assert "depth_raw_out" in METADATA["outputs"]
    assert "wave_amplitude" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthR16WavePlugin()
    assert plugin.name == "R16 Depth Wave"

def test_r16_texture_allocation():
    """Verifies that the plugin allocates an FBO capable of 16-bit rendering."""
    plugin = DepthR16WavePlugin()
    context = MagicMock()
    
    plugin.initialize(context)
    assert plugin._fbo_r16_allocated is True
    
    plugin.cleanup()
    assert plugin._fbo_r16_allocated is False

def test_r16_wave_bypass_missing_depth():
    """Works cleanly and outputs a default blank texture when depth_raw_in is not provided."""
    plugin = DepthR16WavePlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 100
        return None
        
    context.get_texture.side_effect = get_texture_mock
    
    plugin.initialize(context)
    plugin.process()
    
    # Assert video passed through unmodified
    context.set_texture.assert_any_call("video_out", 100)
    # Output empty R16 texture (0)
    context.set_texture.assert_any_call("depth_raw_out", 0)

def test_r16_wave_processing():
    """Validates the dual-output generation and parameter clamping."""
    plugin = DepthR16WavePlugin()
    context = MagicMock()
    
    def get_texture_mock(name):
        if name == "video_in": return 100
        if name == "depth_raw_in": return 200
        return None
        
    def get_param_mock(name):
        if name == "r16_wave.wave_amplitude": return 5.0 # Overshoot > 1.0
        if name == "r16_wave.wave_frequency": return -1.0 # Undershoot < 0.0
        return None
        
    context.get_texture.side_effect = get_texture_mock
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    plugin.process()
    
    # Bound clamping verified
    assert plugin.params["wave_amplitude"] == 1.0
    assert plugin.params["wave_frequency"] == 0.0
    
    context.set_texture.assert_any_call("video_out", 8988) # 100 + 8888 
    context.set_texture.assert_any_call("depth_raw_out", 1816) # 200 + 1616

def test_r16_wave_missing_video():
    plugin = DepthR16WavePlugin()
    context = MagicMock()
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_r16_wave_no_context():
    plugin = DepthR16WavePlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash
