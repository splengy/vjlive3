import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.plugins.depth_parallel_universe as dpu
from vjlive3.plugins.depth_parallel_universe import DepthParallelUniversePlugin, METADATA
from vjlive3.plugins.registry import PluginInfo

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.plugins.depth_parallel_universe.HAS_GL', False)

class MockContext:
    def __init__(self, inputs=None, parameters=None):
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.outputs = {}
        self.delta_time = 0.016

def test_parallel_universe_manifest():
    manifest = PluginInfo(**METADATA)
    assert manifest.name == "Depth Parallel Universe"
    assert "universe_a_intensity" in [p["name"] for p in manifest.parameters]
    assert "universe_c_send" in manifest.outputs

def test_parallel_universe_bypassed():
    plugin = DepthParallelUniversePlugin()
    ctx_empty = MockContext()
    plugin.initialize(ctx_empty)
    
    val = plugin.process_frame(100, {}, ctx_empty)
    assert val == 100
    
    ctx = MockContext(
        inputs={"video_in": 100}, 
        parameters={}
    )
    res = plugin.process_frame(100, {"universe_a_intensity": 1.0, "universe_b_intensity": 1.0, "universe_c_intensity": 1.0}, ctx)
    assert res == 100
    assert ctx.outputs["universe_a_send"] == 100

def test_parallel_universe_processing_mock_injection():
    plugin = DepthParallelUniversePlugin()
    ctx = MockContext(
        inputs={"video_in": 100, "universe_a_return": 200, "universe_b_return": 300},
        parameters={}
    )
    plugin.initialize(ctx)
    
    res = plugin.process_frame(100, {"universe_a_intensity": 1.0, "universe_b_intensity": 1.0, "universe_c_intensity": 0.0}, ctx)
    assert res == 200 # Universe A return
    assert ctx.outputs["universe_b_send"] == 100

def setup_mock_gl(monkeypatch):
    mock_gl = MagicMock()
    mock_gl.glGenTextures.return_value = [1, 2, 3, 4, 5, 6, 7, 8]
    mock_gl.glGenFramebuffers.return_value = [10, 20]
    mock_gl.GL_TRUE = 1
    mock_gl.glGetShaderiv.return_value = 1
    mock_gl.glGetTexLevelParameteriv.return_value = 1920
    monkeypatch.setattr(dpu, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(dpu, 'HAS_GL', True)
    return mock_gl

def test_parallel_universe_fbo_cleanup_headless(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    
    plugin = DepthParallelUniversePlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    assert plugin.textures["mrt_a_0"] == 1
    assert plugin.fbos["pong_0"] == 10
    
    plugin.cleanup()
    mock_gl.glDeleteTextures.assert_called_once_with(8, [1, 2, 3, 4, 5, 6, 7, 8])
    mock_gl.glDeleteFramebuffers.assert_called_once_with(2, [10, 20])
    
def test_parallel_universe_fbo_cleanup_single_ints(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGenTextures.return_value = 99
    mock_gl.glGenFramebuffers.return_value = 100
    
    plugin = DepthParallelUniversePlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    assert plugin.textures["mrt_a_0"] == 99

def test_parallel_universe_gl_exception_handling(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGenTextures.side_effect = Exception("Out of Memory")
    
    plugin = DepthParallelUniversePlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    
    plugin.initialize(ctx)
    assert plugin._mock_mode is True
    
    mock_gl.glGenTextures.side_effect = None
    mock_gl.glGenTextures.return_value = 1
    mock_gl.glGenFramebuffers.return_value = 2
    
    plugin2 = DepthParallelUniversePlugin()
    plugin2._mock_mode = False
    plugin2.initialize(ctx)
    
    mock_gl.glDeleteTextures.side_effect = Exception("Segmentation Fault")
    plugin2.cleanup()
    assert plugin2.textures["mrt_a_0"] is None

def test_parallel_universe_render_frame(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthParallelUniversePlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    assert plugin.prog is not None
    
    params = {
        "depth_split_near": 0.8, # Intentional inversion to trigger clamping
        "depth_split_far": 0.2,
        "universe_a_intensity": 1.0,
        "universe_b_intensity": 1.0,
        "universe_c_intensity": 1.0,
        "universe_a_block_size": 0.5,
        "universe_a_chaos": 0.5,
        "uniBTemporalBlend": 0.5,
        "uniBBlur": 0.5,
        "uniCGlitchFreq": 0.5,
        "uniCRgbSplit": 0.5,
        "uniCCorruption": 0.5,
        "merge_mode": 1.0,
        "crossbleed": 0.5,
        "reality_threshold": 0.5,
        "quantum_uncertainty": 0.5,
        "u_mix": 1.0
    }
    
    res1 = plugin.process_frame(100, params, ctx)
    assert res1 == 8 # mrt_out_1 is texture 8 (first flip writes to 1)
    assert plugin.ping_pong == 1
    
    mock_gl.glGetTexLevelParameteriv.return_value = 1920
    res2 = plugin.process_frame(100, params, ctx)
    assert res2 == 4 # mrt_out_0 is texture 4 (second flip writes to 0)

    # Texture resize
    mock_gl.glGetTexLevelParameteriv.return_value = 800
    res3 = plugin.process_frame(100, params, ctx)
    assert res3 == 8

    res4 = plugin.process_frame(0, params, ctx)
    assert res4 == 0

def test_compile_shader_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    mock_gl.glGetShaderiv.return_value = 0
    mock_gl.glGetShaderInfoLog.return_value = "ERROR"
    
    plugin = DepthParallelUniversePlugin()
    res = plugin._compile_shader()
    assert res is None

def test_process_frame_render_fail(monkeypatch):
    mock_gl = setup_mock_gl(monkeypatch)
    plugin = DepthParallelUniversePlugin()
    plugin._mock_mode = False
    ctx = MockContext()
    plugin.initialize(ctx)
    
    mock_gl.glBindTexture.side_effect = Exception("Render fail")
    res = plugin.process_frame(100, {}, ctx)
    assert res == 100
