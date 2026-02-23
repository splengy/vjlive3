import pytest
import os
import math

# Force GL mock before import to bypass need for active context during CI
os.environ["PYTEST_MOCK_GL"] = "1"


def test_blend_region_clamping():
    mapper = ProjectionMapper(1920, 1080)
    
    mapper.set_blend(BlendRegion(edge="left", width=0.6))
    mapper.set_blend(BlendRegion(edge="right", width=0.6))
    
    # Should clamp to 0.5 each proportionally
    assert math.isclose(mapper.blends["left"].width, 0.5)
    assert math.isclose(mapper.blends["right"].width, 0.5)
    
    # Test setting top/bottom
    mapper.set_blend(BlendRegion(edge="top", width=0.8))
    mapper.set_blend(BlendRegion(edge="bottom", width=0.4))
    
    # Total = 1.2
    # top should become 0.8 * (1.0/1.2) = 0.666...
    # bottom should become 0.4 * (1.0/1.2) = 0.333...
    assert math.isclose(mapper.blends["top"].width, 0.6666666666666666)
    assert math.isclose(mapper.blends["bottom"].width, 0.3333333333333333)

def test_mask_validation():
    mapper = ProjectionMapper(1920, 1080)
    
    # Too few points
    mask_id_fail = mapper.add_mask(PolygonMask(points=[(0.0, 0.0), (1.0, 1.0)]))
    assert mask_id_fail == -1
    assert len(mapper.masks) == 0
    
    # Valid mask
    mask_id_success = mapper.add_mask(PolygonMask(points=[(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)]))
    assert mask_id_success != -1
    assert len(mapper.masks) == 1
    
    # Remove mask
    assert mapper.remove_mask(mask_id_success) is True
    assert len(mapper.masks) == 0
    
    # Remove non-existent
    assert mapper.remove_mask(999) is False

def test_projection_mapper_pipeline():
    mapper = ProjectionMapper(1920, 1080)
    
    # In mock mode, it just returns the input texture id
    tex_in = 42
    tex_out = mapper.process_slice(tex_in)
    
    assert tex_in == tex_out
    
    # Also test invalid edge clears
    mapper.set_blend(BlendRegion(edge="left", width=0.1))
    assert "left" in mapper.blends
    mapper.clear_blend("left")
    assert "left" not in mapper.blends
    mapper.clear_blend("invalid")  # should not crash
    
    # Ensure invalid edge returns none
    mapper.set_blend(BlendRegion(edge="center", width=0.5))
    assert "center" not in mapper.blends

def test_shutdown():
    mapper = ProjectionMapper(1920, 1080)
    mapper.shutdown()
    assert mapper._fbo is None
    assert mapper._texture is None

def test_invalid_blend():
    mapper = ProjectionMapper(1920, 1080)
    # This should be ignored
    mapper.set_blend(BlendRegion(edge="diagonal", width=0.5))
    assert "diagonal" not in mapper.blends

def test_gl_paths():
    mapper = ProjectionMapper(1920, 1080)
    mapper._mock_mode = False
    
    # Inject a fake 'gl' into the module
    pm.gl = type("MockGL", (), {
        "glGenFramebuffers": lambda x: 1,
        "glGenTextures": lambda x: 2,
        "glBindTexture": lambda x,y: None,
        "glTexImage2D": lambda *args: None,
        "glDeleteFramebuffers": lambda x,y: None,
        "glDeleteTextures": lambda x,y: None,
        "GL_TEXTURE_2D": 3553,
        "GL_RGBA": 6408,
        "GL_UNSIGNED_BYTE": 5121
    })
    
    mapper._init_gl_resources()
    assert mapper._fbo == 1
    assert mapper._texture == 2
    
    # Test valid return from process_slice when FBO is present
    tex_out = mapper.process_slice(42)
    assert tex_out == 2
    
    # Test shutdown
    mapper.shutdown()
    assert mapper._fbo is None
    assert mapper._texture is None
    
    # Test init failure
    def fail_gen(*args):
        raise Exception("Mock GL Failure")
    pm.gl.glGenFramebuffers = fail_gen
    
    mapper2 = ProjectionMapper(1920, 1080)
    mapper2._mock_mode = False
    mapper2._init_gl_resources()
    assert mapper2._mock_mode is True
    
    # Now process_slice with NO fbo
    assert mapper2.process_slice(42) == 42
    
    # Let's test shutdown failure catching
    mapper3 = ProjectionMapper(1920, 1080)
    mapper3._mock_mode = False
    mapper3._fbo = 1
    mapper3._texture = 2
    pm.gl.glDeleteFramebuffers = fail_gen
    # This should swallow the exception cleanly
    mapper3.shutdown()
    assert mapper3._fbo is None

