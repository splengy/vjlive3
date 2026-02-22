import pytest
import os
import sys
from unittest.mock import MagicMock

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.plugins.depth_aware_compression as dac
from vjlive3.plugins.depth_aware_compression import DepthAwareCompressionPlugin, METADATA
from vjlive3.plugins.registry import PluginInfo

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.plugins.depth_aware_compression.HAS_GL', False)

class MockContext:
    def __init__(self, inputs=None, parameters=None):
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.outputs = {}

def test_depth_compression_manifest():
    manifest = PluginInfo(**METADATA)
    assert manifest.name == "Depth Aware Compression"
    assert "color_quantization" in [p["name"] for p in manifest.parameters]
    assert "video_in" in manifest.inputs

def test_depth_compression_bypass():
    """Checks behaviour when depth_in is offline."""
    plugin = DepthAwareCompressionPlugin()
    ctx = MockContext(inputs={"video_in": 123}) # ONLY video
    plugin.initialize(ctx)
    
    params = {}
    val = plugin.process_frame(123, params, ctx)
    
    assert val == 123
    assert params["_uniform_compression_fallback"] is True
    assert params["_clamped_depth_ratio"] == 0.0 # Force override flat

def test_depth_compression_valid_depth():
    """Checks normal operation when depth is provided."""
    plugin = DepthAwareCompressionPlugin()
    ctx = MockContext(inputs={"video_in": 123, "depth_in": 321}) # BOTH
    plugin.initialize(ctx)
    
    params = {"depth_compression_ratio": 0.5}
    val = plugin.process_frame(123, params, ctx)
    
    assert val == 123
    assert params["_uniform_compression_fallback"] is False
    assert params["_clamped_depth_ratio"] == 0.5 

def test_depth_compression_math_clamping():
    """Verifies that mathematical variables won't trigger / 0 exceptions in GLSL."""
    plugin = DepthAwareCompressionPlugin()
    ctx = MockContext(inputs={"video_in": 123, "depth_in": 321})
    plugin.initialize(ctx)
    
    # Try throwing invalid edge values natively
    params = {
        "color_quantization": -100.0, # Must not be <= 0
        "block_size": 1000.0,         # Must be clamped
        "quality": 5.0                # Max is 1.0
    }
    
    plugin.process_frame(123, params, ctx)
    
    assert params["_clamped_color_q"] == 2.0 # Fixed to strict min
    
def test_depth_compression_missing_video():
    plugin = DepthAwareCompressionPlugin()
    ctx = MockContext()
    plugin.initialize(ctx)
    val = plugin.process_frame(None, {}, ctx)
    assert val == 0
