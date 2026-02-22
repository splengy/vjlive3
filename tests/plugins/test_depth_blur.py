import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.plugins.depth_blur as db
from vjlive3.plugins.depth_blur import DepthBlurPlugin, METADATA
from vjlive3.plugins.registry import PluginInfo

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.plugins.depth_blur.HAS_GL', False)

class MockContext:
    def __init__(self, inputs=None, parameters=None):
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.outputs = {}

def test_depth_blur_manifest():
    manifest = PluginInfo(**METADATA)
    assert manifest.name == "Depth Blur"
    assert "tilt_shift" in [p["name"] for p in manifest.parameters]
    assert "video_out" in manifest.outputs

def test_depth_blur_tilt_shift_fallback():
    plugin = DepthBlurPlugin()
    ctx = MockContext(inputs={"video_in": 100}) # Note: depth_in is excluded
    plugin.initialize(ctx)
    
    params = {"tilt_shift": 0.0} # Even if user requested 0.0, we force override it without depth
    val = plugin.process_frame(100, params, ctx)
    
    assert val == 100
    assert params["_clamped_tilt_shift"] == 1.0 # The system forced Tilt-Shift Fallback

def test_depth_blur_normal_with_depth():
    plugin = DepthBlurPlugin()
    ctx = MockContext(inputs={"video_in": 100, "depth_in": 200})
    plugin.initialize(ctx)
    
    params = {"tilt_shift": 0.25} 
    plugin.process_frame(100, params, ctx)
    
    assert params["_clamped_tilt_shift"] == 0.25 # Custom params allowed if depth exists

def test_depth_blur_missing_video():
    plugin = DepthBlurPlugin()
    ctx = MockContext() 
    plugin.initialize(ctx)
    
    val = plugin.process_frame(None, {}, ctx)
    assert val == 0
