import pytest
import os
import sys
from unittest.mock import MagicMock

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.plugins.depth_edge_glow as deg
from vjlive3.plugins.depth_edge_glow import DepthEdgeGlowPlugin, METADATA
from vjlive3.plugins.registry import PluginInfo

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.plugins.depth_edge_glow.HAS_GL', False)

class MockContext:
    def __init__(self, inputs=None, parameters=None):
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.outputs = {}

def test_edge_glow_manifest():
    manifest = PluginInfo(**METADATA)
    assert manifest.name == "Depth Edge Glow"
    assert "bg_dimming" in [p["name"] for p in manifest.parameters]
    assert "depth_in" in manifest.inputs

def test_edge_glow_missing_depth():
    """Checks behaviour when depth_in is offline - prevents shader crash."""
    plugin = DepthEdgeGlowPlugin()
    ctx = MockContext(inputs={"video_in": 123}) # ONLY video
    plugin.initialize(ctx)
    
    params = {}
    val = plugin.process_frame(123, params, ctx)
    
    assert val == 123
    assert params["_edge_bypass_triggered"] is True

def test_edge_glow_valid_depth():
    """Checks normal operation when depth is provided."""
    plugin = DepthEdgeGlowPlugin()
    ctx = MockContext(inputs={"video_in": 123, "depth_in": 321}) # BOTH
    plugin.initialize(ctx)
    
    params = {}
    val = plugin.process_frame(123, params, ctx)
    
    assert val == 123
    assert params["_edge_bypass_triggered"] is False

def test_edge_glow_math_clamping():
    """Verifies that mathematical variables won't trigger / 0 bounds in GLSL kernels."""
    plugin = DepthEdgeGlowPlugin()
    ctx = MockContext(inputs={"video_in": 123, "depth_in": 321})
    plugin.initialize(ctx)
    
    # Try throwing invalid edge values natively
    params = {
        "contour_intervals": -10, # Must not be < 1
        "edge_threshold": 5.0,    # Max is 1.0
    }
    
    plugin.process_frame(123, params, ctx)
    
    assert params["_clamped_intervals"] == 1 # Fixed to strict min
    
def test_edge_glow_missing_video():
    plugin = DepthEdgeGlowPlugin()
    ctx = MockContext()
    plugin.initialize(ctx)
    val = plugin.process_frame(None, {}, ctx)
    assert val == 0
