import pytest
import os
import sys
import numpy as np
from unittest.mock import patch, MagicMock

# Force mock OpenGL before loading
sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.video.projection_mapper as pm
from vjlive3.video.projection_mapper import BlendRegion, PolygonMask, ProjectionMapper

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.video.projection_mapper.HAS_GL', False)

def test_blend_region_clamping():
    mapper = ProjectionMapper(1920, 1080)
    
    # Test adding valid single blend
    mapper.set_blend(BlendRegion('left', 0.4))
    assert mapper.blends['left'].width == 0.4
    
    # Add right blend that pushes sum over 1.0 (0.4 + 0.7 = 1.1)
    mapper.set_blend(BlendRegion('right', 0.7))
    assert mapper.blends['left'].width == 0.5
    assert mapper.blends['right'].width == 0.5
    
    # Test top/bottom clamping
    mapper.set_blend(BlendRegion('top', 0.6))
    mapper.set_blend(BlendRegion('bottom', 0.8))
    assert mapper.blends['top'].width == 0.5
    assert mapper.blends['bottom'].width == 0.5

    # Test individual clamping
    mapper.set_blend(BlendRegion('left', 1.5))
    assert mapper.blends['left'].width == 0.5 # since right is 0.5, total is 1.0 this triggers clamp again! WAIT.
    # Ah, if left becomes 1.0 (from clamping 1.5), left(1.0) + right(0.5) = 1.5 -> clamps both to 0.5.
    
    # Clear right
    mapper.clear_blend('right')
    mapper.set_blend(BlendRegion('left', 1.5))
    assert mapper.blends['left'].width == 1.0 # Clamped max 1.0, no right overlap
    
    # Invalid edge
    mapper.set_blend(BlendRegion('center', 0.5))
    assert 'center' not in mapper.blends
    
    # Clear invalid/valid
    mapper.clear_blend('left')
    assert 'left' not in mapper.blends
    mapper.clear_blend('unknown')

def test_mask_validation():
    mapper = ProjectionMapper(1920, 1080)
    
    # < 3 points
    bad_mask = PolygonMask([(0.0, 0.0), (1.0, 1.0)])
    mask_id = mapper.add_mask(bad_mask)
    assert mask_id == -1
    assert len(mapper.masks) == 0
    
    # Valid mask
    good_mask = PolygonMask([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)])
    mask_id = mapper.add_mask(good_mask)
    assert mask_id == 0
    assert len(mapper.masks) == 1
    
    # Remove valid
    assert mapper.remove_mask(mask_id) is True
    assert len(mapper.masks) == 0
    
    # Remove invalid
    assert mapper.remove_mask(99) is False

def test_projection_mapper_pipeline():
    mapper = ProjectionMapper(1920, 1080)
    mapper._mock_mode = True
    
    assert mapper.process_slice(123) == 123
    
    mapper.shutdown()
    assert mapper._fbo is None

def test_projection_mapper_gl_lifecycle(monkeypatch):
    """Test GL resource management without autouse fixture overriding natively"""
    mock_gl = MagicMock()
    mock_gl.glGenFramebuffers.return_value = 1
    mock_gl.glGenTextures.return_value = 2
    
    monkeypatch.setattr(pm, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(pm, 'HAS_GL', True)
    
    gl_mapper = ProjectionMapper(1920, 1080)
    assert gl_mapper._mock_mode is False
    assert gl_mapper._fbo == 1
    assert gl_mapper._texture == 2
    
    res = gl_mapper.process_slice(100)
    assert res == 2
    
    gl_mapper.shutdown()
    mock_gl.glDeleteFramebuffers.assert_called_with(1, [1])
    mock_gl.glDeleteTextures.assert_called_with(1, [2])
    
    # Exceptions on GL bind
    mock_gl.glGenFramebuffers.side_effect = Exception("No Context Projection")
    gl_mapper2 = ProjectionMapper(1920, 1080)
    assert gl_mapper2._mock_mode is True

    # Exception on shutdown
    mock_gl.glGenFramebuffers.side_effect = None
    gl_mapper3 = ProjectionMapper(1920, 1080)
    gl_mapper3._mock_mode = False
    
    mock_gl.glDeleteFramebuffers.side_effect = Exception("Del Fail Projection")
    gl_mapper3.shutdown()
    assert gl_mapper3._fbo is None
