import pytest
from unittest.mock import MagicMock, patch

from vjlive3.plugins.api import PluginContext
from vjlive3.plugins.depth_neural_quantum_hyper_tunnel import DepthNeuralQuantumHyperTunnelPlugin

def test_quantum_tunnel_manifest():
    plugin = DepthNeuralQuantumHyperTunnelPlugin()
    meta = plugin.get_metadata()
    
    assert meta["name"] == "Neural Quantum Hyper Tunnel"
    assert "video_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    assert "video_out" in meta["outputs"]
    
    param_names = [p["name"] for p in meta["parameters"]]
    assert "tunnel_speed" in param_names
    assert "depth_influence" in param_names
    assert "quantum_jitter" in param_names
    assert "neural_color_shift" in param_names
    assert "feedback_decay" in param_names

def test_quantum_tunnel_mock_bypass():
    plugin = DepthNeuralQuantumHyperTunnelPlugin()
    plugin._mock_mode = True
    
    ctx = PluginContext(MagicMock())
    ctx.inputs = {"video_in": 77, "depth_in": 99}
    ctx.outputs = {}
    
    res = plugin.process_frame(77, {}, ctx)
    assert res == 77
    assert ctx.outputs["video_out"] == 77
    
def test_quantum_tunnel_empty_input():
    plugin = DepthNeuralQuantumHyperTunnelPlugin()
    ctx = PluginContext(MagicMock())
    res = plugin.process_frame(0, {}, ctx)
    assert res == 0

def test_quantum_tunnel_gl_failure():
    plugin = DepthNeuralQuantumHyperTunnelPlugin()
    
    with patch("vjlive3.plugins.depth_neural_quantum_hyper_tunnel.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 0 # GL_FALSE
        plugin.initialize(PluginContext(MagicMock()))
        
        # Shader failed, safely entered mock isolated mode.
        assert plugin._mock_mode is True

def test_quantum_tunnel_fbo_cleanup():
    plugin = DepthNeuralQuantumHyperTunnelPlugin()
    
    with patch("vjlive3.plugins.depth_neural_quantum_hyper_tunnel.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fboA = 50
        plugin.fboB = 51
        plugin.texA = 40
        plugin.texB = 41
        plugin.vao = 22
        plugin.vbo = 33
        plugin.prog = 44
        
        plugin.cleanup()
        
        mock_gl.glDeleteTextures.assert_any_call(1, [40])
        mock_gl.glDeleteTextures.assert_any_call(1, [41])
        mock_gl.glDeleteFramebuffers.assert_any_call(1, [50])
        mock_gl.glDeleteFramebuffers.assert_any_call(1, [51])
        mock_gl.glDeleteVertexArrays.assert_called_with(1, [22])
        mock_gl.glDeleteProgram.assert_called_with(44)
        
        assert plugin.texA is None
        assert plugin.texB is None

def test_quantum_tunnel_resolution_change():
    """Verify that buffer allocation recreates textures properly when height/width drifts mid-frame lifecycle."""
    plugin = DepthNeuralQuantumHyperTunnelPlugin()
    ctx = PluginContext(MagicMock())
    
    with patch("vjlive3.plugins.depth_neural_quantum_hyper_tunnel.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.prog = 99
        
        # Frame 1 uses dimensions 1920x1080
        ctx.width = 1920
        ctx.height = 1080
        plugin.process_frame(1, {}, ctx)
        
        assert plugin._width == 1920
        assert mock_gl.glGenFramebuffers.call_count == 2
        
        mock_gl.glGenFramebuffers.reset_mock()
        mock_gl.glGenTextures.reset_mock()
        
        # Frame 2 resize resolution dynamically to 1280x720 
        ctx.width = 1280
        ctx.height = 720
        plugin.process_frame(1, {}, ctx)
        
        # It should trigger `_allocate_buffers` natively again natively allocating new FBOs 
        assert mock_gl.glGenFramebuffers.call_count == 2
        assert mock_gl.glGenTextures.call_count == 2
        assert plugin._width == 1280

def test_quantum_tunnel_bypass():
    """Missing depth passes uniformly as standard mapping to 0 natively."""
    plugin = DepthNeuralQuantumHyperTunnelPlugin()
    
    with patch("vjlive3.plugins.depth_neural_quantum_hyper_tunnel.gl") as mock_gl:
        plugin._mock_mode = False
        plugin.fboA = 1
        plugin.prog = 2
        plugin.texA = 9
        plugin.vao = 1
        
        ctx = PluginContext(MagicMock())
        ctx.inputs = {"video_in": 5}
        ctx.outputs = {}
        
        mock_gl.glGetUniformLocation.side_effect = lambda prog, name: name
        
        plugin.process_frame(5, {}, ctx)
        
        mock_gl.glUniform1i.assert_any_call("has_depth", 0)

def test_quantum_tunnel_full_pipeline():
    plugin = DepthNeuralQuantumHyperTunnelPlugin()
    ctx = PluginContext(MagicMock())
    ctx.inputs = {"video_in": 1, "depth_in": 2}
    ctx.outputs = {}
    
    with patch("vjlive3.plugins.depth_neural_quantum_hyper_tunnel.gl") as mock_gl:
        mock_gl.glGetShaderiv.return_value = 1 # GL_TRUE
        mock_gl.glGetProgramiv.return_value = 1 # GL_TRUE
        mock_gl.glGenTextures.return_value = 15 
        
        plugin._mock_mode = False
        plugin.initialize(ctx)
        
        res = plugin.process_frame(1, {"tunnel_speed": 1.0}, ctx)
        
        assert plugin._mock_mode is False
        assert mock_gl.glDrawArrays.called
        assert ctx.outputs["video_out"] == 15
