import pytest
import os
import tempfile
import numpy as np

from vjlive3.core.output_mapper import ScreenSlice, OutputMapper, MeshWarper


def test_output_mapper_add_slice():
    mapper = OutputMapper(1920, 1080)
    
    slice1 = ScreenSlice("main", 0.0, 0.0, 1.0, 1.0, [(0, 1), (1, 1), (1, 0), (0, 0)])
    mapper.add_slice(slice1)
    
    # Verify addition
    assert "main" in mapper.slices
    assert mapper.slices["main"].width == 1.0
    
    # Overwrite check
    slice1_over = ScreenSlice("main", 0.0, 0.0, 0.5, 0.5, [(0, 0.5), (0.5, 0.5), (0.5, 0), (0, 0)])
    mapper.add_slice(slice1_over)
    assert mapper.slices["main"].width == 0.5


def test_output_mapper_warp_clamping():
    mapper = OutputMapper(1920, 1080)
    slice1 = ScreenSlice("S1", 0.0, 0.0, 1.0, 1.0, [(0, 1), (1, 1), (1, 0), (0, 0)])
    mapper.add_slice(slice1)
    
    # Try updating with invalid amount of points (should reject)
    mapper.update_warp_points("S1", [(0, 0)])
    assert len(mapper.slices["S1"].warp_points) == 4
    
    # Try updating out-of-bounds extremely far away
    mapper.update_warp_points("S1", [(-5.0, 1.0), (1.0, 3.0), (1.0, 0.0), (0.0, 0.0)])
    pts = mapper.slices["S1"].warp_points
    
    # Expected clamping to [-1.0, 2.0] range
    assert pts[0] == (-1.0, 1.0)
    assert pts[1] == (1.0, 2.0)
    
    # Calling on non-existent slice
    mapper.update_warp_points("GHOST", [(0, 0), (1, 1), (1, 0), (0, 0)])


def test_mesh_warper_generation():
    # Valid setup
    warp_points = [(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
    mesh = MeshWarper.generate_quad_mesh(warp_points)
    
    assert isinstance(mesh, np.ndarray)
    assert mesh.dtype == np.float32
    assert len(mesh) == 16  # 4 verts * (x,y,u,v) = 16 floats
    
    # First vertex should correlate to warp_points[0] (0.0, 1.0) and uvs[0] (0.0, 1.0)
    assert mesh[0] == 0.0
    assert mesh[1] == 1.0
    assert mesh[2] == 0.0
    assert mesh[3] == 1.0
    
    # Invalid length input fallback test
    mesh_bad = MeshWarper.generate_quad_mesh([(0, 0)])
    assert len(mesh_bad) == 16


def test_output_mapper_serialization():
    mapper = OutputMapper(1920, 1080)
    slice1 = ScreenSlice("S1", 0.0, 0.5, 0.5, 0.5, [(0, 1), (1, 1), (1, 0), (0, 0)])
    mapper.add_slice(slice1)
    
    with tempfile.TemporaryDirectory() as td:
        filepath = os.path.join(td, "config.json")
        mapper.save_configuration(filepath)
        assert os.path.exists(filepath)
        
        # Create a new mapper and load
        mapper2 = OutputMapper(1920, 1080)
        mapper2.load_configuration(filepath)
        
        assert "S1" in mapper2.slices
        s = mapper2.slices["S1"]
        assert s.y == 0.5
        assert s.width == 0.5


def test_output_mapper_serialization_errors():
    mapper = OutputMapper(1920, 1080)
    # Give it an invalid directory to catch error cleanly
    mapper.save_configuration("/root/invalid_dir/no_access.json") 
    mapper.load_configuration("/root/invalid_dir/no_access.json")


def test_output_mapper_process_and_destroy():
    mapper = OutputMapper(1920, 1080)
    # Without FBO it passes through input
    assert mapper.process_frame(88) == 88
    
    # Fake FBO for coverage of cleanup logic
    mapper._fbo_id = 12
    assert mapper.process_frame(88) == 12 
    
    mapper.destroy()
    assert mapper._fbo_id == -1
