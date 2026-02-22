import pytest
import os
import sys
import json
import numpy as np
from unittest.mock import patch, MagicMock

# Force mock OpenGL before loading
sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = MagicMock()

import vjlive3.video.output_mapper as om
from vjlive3.video.output_mapper import ScreenSlice, OutputMapper, MeshWarper

@pytest.fixture(autouse=True)
def force_mock_no_gl(monkeypatch):
    monkeypatch.setattr('vjlive3.video.output_mapper.HAS_GL', False)

def test_output_mapper_add_slice(tmp_path):
    mapper = OutputMapper(1920, 1080)
    slice1 = ScreenSlice("main", 0.0, 0.0, 1.0, 1.0, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])
    mapper.add_slice(slice1)
    
    assert "main" in mapper.slices
    
    # Test update
    mapper.update_warp_points("main", [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)])
    assert mapper.slices["main"].warp_points[0] == (0.1, 0.1)
    
    # Test invalid update
    mapper.update_warp_points("unknown", [])
    
    filepath = os.path.join(tmp_path, "config.json")
    mapper.save_configuration(filepath)
    
    assert os.path.exists(filepath)
    
    mapper2 = OutputMapper(1920, 1080)
    mapper2.load_configuration(filepath)
    
    assert "main" in mapper2.slices
    assert mapper2.slices["main"].warp_points[0] == (0.1, 0.1)
    
def test_output_mapper_warp_clamping():
    # Self-intersecting bowtie
    bowtie_pts = [(0.0, 0.0), (1.0, 1.0), (1.0, 0.0), (0.0, 1.0)]
    mesh = MeshWarper.generate_quad_mesh(bowtie_pts)
    
    # Should clamp to unit rectangle
    expected = np.array([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)], dtype=np.float32)
    np.testing.assert_array_equal(mesh, expected)
    
    # Non-quad points
    mesh2 = MeshWarper.generate_quad_mesh([(0.0, 0.0), (1.0, 0.0)])
    np.testing.assert_array_equal(mesh2, expected)

def test_mesh_warper_generation():
    valid_pts = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    mesh = MeshWarper.generate_quad_mesh(valid_pts)
    assert mesh.shape == (4, 2)
    assert mesh.dtype == np.float32

def test_output_mapper_process_mock():
    mapper = OutputMapper(1920, 1080)
    mapper._mock_mode = True # Ensure mock
    
    # Return input directly
    assert mapper.process_frame(99) == 99
    
    mapper.shutdown()
    assert mapper._fbo is None

def test_invalid_load_config(tmp_path):
    mapper = OutputMapper(1920, 1080)
    mapper.load_configuration(str(tmp_path / "nonexistent_file.json"))
    
    # Create invalid json
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{ bad json ]")
    
    mapper.load_configuration(str(bad_json))

    # Trigger save failure
    mapper.save_configuration("/root/invalid_dir/no_access.json")

def test_output_mapper_gl_lifecycle(monkeypatch):
    """Test GL resource management manually bypassing the fixture"""
    mock_gl = MagicMock()
    mock_gl.glGenFramebuffers.return_value = 1
    mock_gl.glGenTextures.return_value = 2
    
    monkeypatch.setattr(om, 'gl', mock_gl, raising=False)
    monkeypatch.setattr(om, 'HAS_GL', True)
    
    gl_mapper = OutputMapper(1920, 1080)
    assert gl_mapper._mock_mode is False
    assert gl_mapper._fbo == 1
    assert gl_mapper._texture == 2
    
    res = gl_mapper.process_frame(100)
    assert res == 2
    
    gl_mapper.shutdown()
    mock_gl.glDeleteFramebuffers.assert_called_with(1, [1])
    mock_gl.glDeleteTextures.assert_called_with(1, [2])
    
    # Test exception handling on GL init natively
    mock_gl.glGenFramebuffers.side_effect = Exception("No Context")
    gl_mapper2 = OutputMapper(1920, 1080)
    assert gl_mapper2._mock_mode is True

    # Test exception handling on shutdown natively
    mock_gl.glGenFramebuffers.side_effect = None
    gl_mapper3 = OutputMapper(1920, 1080)
    gl_mapper3._mock_mode = False
    
    mock_gl.glDeleteFramebuffers.side_effect = Exception("No Context delete")
    gl_mapper3.shutdown()
    assert gl_mapper3._fbo is None
