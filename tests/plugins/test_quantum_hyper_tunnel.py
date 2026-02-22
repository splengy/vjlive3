import pytest
from unittest.mock import MagicMock

from vjlive3.plugins.quantum_hyper_tunnel import DepthNeuralQuantumHyperTunnelPlugin, METADATA
from vjlive3.plugins.api import PluginContext

def test_quantum_tunnel_manifest():
    """Verifies Pydantic/Dict manifest structure."""
    assert METADATA["name"] == "Neural Quantum Hyper Tunnel"
    assert "video_in" in METADATA["inputs"]
    assert "tunnel_speed" in [p["name"] for p in METADATA["parameters"]]
    assert "feedback_decay" in [p["name"] for p in METADATA["parameters"]]
    
    plugin = DepthNeuralQuantumHyperTunnelPlugin()
    assert plugin.name == "Neural Quantum Hyper Tunnel"

def test_quantum_tunnel_fbo_cleanup():
    """Ensures no textures are left dangling after on_unload/cleanup."""
    plugin = DepthNeuralQuantumHyperTunnelPlugin()
    context = MagicMock(spec=PluginContext)
    
    plugin.initialize(context)
    assert plugin._fbo_a_active is True
    assert plugin._fbo_b_active is True
    
    plugin.cleanup()
    assert plugin._fbo_a_active is False
    assert plugin._fbo_b_active is False

def test_quantum_tunnel_bypass():
    """Works cleanly when depth_in is not provided."""
    plugin = DepthNeuralQuantumHyperTunnelPlugin()
    context = MagicMock(spec=PluginContext)
    
    def get_texture_mock(name):
        if name == "video_in":
            return 999
        return None
        
    context.get_texture.side_effect = get_texture_mock
    
    plugin.initialize(context)
    plugin.process()
    
    # Assert video passed through unmodified
    context.set_texture.assert_called_with("video_out", 999)

def test_quantum_tunnel_processing_ping_pong():
    """Validates the FBO ping pong logic works with valid textures and clamps parameters."""
    plugin = DepthNeuralQuantumHyperTunnelPlugin()
    context = MagicMock(spec=PluginContext)
    
    def get_texture_mock(name):
        if name == "video_in": return 100
        if name == "depth_in": return 200
        return None
        
    def get_param_mock(name):
        if name == "quantum_tunnel.tunnel_speed": return 5.0 # Overshoot
        if name == "quantum_tunnel.depth_influence": return -1.0 # Undershoot
        return None
        
    context.get_texture.side_effect = get_texture_mock
    context.get_parameter.side_effect = get_param_mock
    
    plugin.initialize(context)
    
    # State 0 initially
    assert plugin._ping_pong_state == 0
    
    # Process Frame 1
    plugin.process()
    assert plugin._ping_pong_state == 1
    context.set_texture.assert_called_with("video_out", 3100) # 100 + 3000
    
    # Bound clamping verified
    assert plugin.params["tunnel_speed"] == 2.0  # Clamped to max
    assert plugin.params["depth_influence"] == 0.0 # Clamped to min
    
    # Process Frame 2 (Ping-Pong back)
    plugin.process()
    assert plugin._ping_pong_state == 0
    context.set_texture.assert_called_with("video_out", 2100) # 100 + 2000

def test_quantum_tunnel_missing_video():
    plugin = DepthNeuralQuantumHyperTunnelPlugin()
    context = MagicMock(spec=PluginContext)
    context.get_texture.return_value = None
    
    plugin.initialize(context)
    plugin.process()
    
    context.set_texture.assert_not_called()
    
def test_quantum_tunnel_no_context():
    plugin = DepthNeuralQuantumHyperTunnelPlugin()
    plugin.process() # should not crash
    plugin._read_params_from_context() # should not crash
