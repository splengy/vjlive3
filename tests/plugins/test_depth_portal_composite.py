import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.plugins.depth_portal_composite as vdc
from vjlive3.plugins.depth_portal_composite import DepthPortalCompositePlugin, METADATA
from vjlive3.plugins.registry import PluginInfo

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.plugins.depth_portal_composite.HAS_GL', False)

class MockContext:
    def __init__(self, inputs=None, parameters=None):
        self.inputs = inputs or {}
        self.parameters = parameters or {}
        self.outputs = {}

def test_portal_composite_manifest():
    manifest = PluginInfo(**METADATA)
    assert manifest.name == "Depth Portal Composite"
    assert "slice_near" in [p["name"] for p in manifest.parameters]
    assert "video_out" in manifest.outputs

def test_portal_composite_split_clamp():
    plugin = DepthPortalCompositePlugin()
    ctx = MockContext(inputs={"depth_in": 200, "background_in": 300})
    plugin.initialize(ctx)
    
    params = {
        "slice_near": 5.0, # Invalid logic, near > far
        "slice_far": 2.0
    }
    plugin.process_frame(100, params, ctx)
    
    # Assert clamped boundaries inverted back to sanity
    assert params["_clamped_near"] == 2.0
    assert params["_clamped_far"] == 5.0

def test_portal_composite_missing_bg():
    plugin = DepthPortalCompositePlugin()
    ctx = MockContext(
        inputs={"video_in": 100, "depth_in": 200}, 
        parameters={}
    )
    plugin.initialize(ctx)
    val = plugin.process_frame(100, {}, ctx)
    
    # Needs to return video_in (100) safely
    assert val == 100
    assert ctx.outputs["video_out"] == 100

def test_portal_composite_missing_depth():
    plugin = DepthPortalCompositePlugin()
    ctx = MockContext(
        inputs={"video_in": 100, "background_in": 500}, 
        parameters={}
    ) # Missing depth completely
    plugin.initialize(ctx)
    val = plugin.process_frame(100, {}, ctx)
    
    # Needs to bypass entirely to 100
    assert val == 100
    assert ctx.outputs["video_out"] == 100

def test_portal_composite_empty():
    plugin = DepthPortalCompositePlugin()
    ctx = MockContext()
    plugin.initialize(ctx)
    val = plugin.process_frame(None, {}, ctx)
    
    # Missing everything returns 0
    assert val == 0

def test_portal_composite_success():
    plugin = DepthPortalCompositePlugin()
    ctx = MockContext(
        inputs={"video_in": 100, "depth_in": 200, "background_in": 500}, 
        parameters={}
    )
    plugin.initialize(ctx)
    
    val = plugin.process_frame(100, {"bg_opacity": 1.0}, ctx)
    assert val == 500 # Resolves Composite output layer for mocking
    assert ctx.outputs["video_out"] == 500
