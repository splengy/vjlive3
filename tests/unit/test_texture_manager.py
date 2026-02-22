"""
Unit tests for P1-R4 Texture Manager.
"""
import pytest
import os
import tempfile
import numpy as np
from unittest.mock import patch, MagicMock

from vjlive3.render.texture_manager import TextureManager, TextureStats
from vjlive3.render.opengl_context import OpenGLContext

@pytest.fixture(scope="session")
def gl_context():
    ctx = OpenGLContext(1280, 720, headless=True)
    ctx.make_current()
    yield ctx
    ctx.terminate()

def test_init_no_hardware():
    # Attempting to initialize without a context raises ValueError
    with pytest.raises(ValueError):
        TextureManager(ctx=None)
        
    # Invalid max limits
    ctx = MagicMock()
    with pytest.raises(ValueError):
        TextureManager(ctx=ctx, max_textures=0)

def test_create_texture(gl_context):
    ctx = gl_context.ctx
    if not ctx:
        pytest.skip("No modernGL context")
        
    manager = TextureManager(ctx)
    
    # Valid allocation
    tex = manager.create_texture("test1", (256, 256), 3)
    assert tex is not None
    assert tex.width == 256
    assert tex.height == 256
    assert tex.components == 3
    
    stats = manager.get_stats()
    assert stats.active_textures == 1
    assert stats.memory_used_bytes == 256 * 256 * 3
    
    # Invalid validations
    with pytest.raises(ValueError):
        manager.create_texture("", (1, 1), 1)
    with pytest.raises(ValueError):
        manager.create_texture("bad", (-1, 1), 1)
    with pytest.raises(ValueError):
        manager.create_texture("bad", (1, 1), 5)
        
    manager.cleanup()

def test_texture_reuse(gl_context):
    ctx = gl_context.ctx
    if not ctx:
        pytest.skip("No modernGL context")
        
    manager = TextureManager(ctx)
    
    tex1 = manager.create_texture("reused", (128, 128), 1)
    
    # Fetch existing
    tex2 = manager.get_texture("reused")
    assert tex1 is tex2
    
    stats = manager.get_stats()
    assert stats.cache_hits == 1
    
    # Missing fetch
    miss = manager.get_texture("missing")
    assert miss is None
    assert stats.cache_misses == 1
    
    manager.cleanup()
    
def test_texture_update(gl_context):
    ctx = gl_context.ctx
    if not ctx:
        pytest.skip("No modernGL context")
        
    manager = TextureManager(ctx)
    data = np.zeros((64 * 64 * 3), dtype=np.uint8).tobytes()
    tex = manager.create_from_buffer("buffer", data, (64, 64), 3)
    assert tex is not None
    
    new_data = np.ones((64 * 64 * 3), dtype=np.uint8).tobytes()
    manager.update_texture(tex, new_data)
    
    # Invalid payloads
    with pytest.raises(ValueError):
        manager.update_texture(tex, b"toosmall")
        
    manager.cleanup()

def test_release_texture(gl_context):
    ctx = gl_context.ctx
    if not ctx:
        pytest.skip("No modernGL context")
        
    manager = TextureManager(ctx)
    manager.create_texture("tmp", (10, 10), 1)
    
    assert manager.get_stats().active_textures == 1
    
    # Successful release
    res = manager.release_texture("tmp")
    assert res is True
    assert manager.get_stats().active_textures == 0
    
    # Missing release
    res2 = manager.release_texture("nonexistent")
    assert res2 is False
    
def test_clear_all(gl_context):
    ctx = gl_context.ctx
    if not ctx:
        pytest.skip("No modernGL context")
        
    manager = TextureManager(ctx)
    manager.create_texture("1", (10, 10), 1)
    manager.create_texture("2", (10, 10), 1)
    
    assert manager.get_stats().active_textures == 2
    
    manager.clear_all()
    assert manager.get_stats().active_textures == 0
    
def test_memory_limit(gl_context):
    ctx = gl_context.ctx
    if not ctx:
        pytest.skip("No modernGL context")
        
    manager = TextureManager(ctx, max_textures=2)
    manager.create_texture("1", (10, 10), 1)
    manager.create_texture("2", (10, 10), 1)
    
    # Limit hit
    with pytest.raises(MemoryError):
        manager.create_texture("3", (10, 10), 1)
        
    manager.cleanup()

@patch('vjlive3.render.texture_manager.Image')    
@patch('vjlive3.render.texture_manager._PIL_AVAILABLE', True)
@patch('vjlive3.render.texture_manager._CV2_AVAILABLE', False)
@patch('os.path.exists', return_value=True)
def test_create_from_image_mocked(mock_exists, mock_pil, gl_context):
    ctx = gl_context.ctx
    if not ctx:
        pytest.skip("No modernGL context")
        
    manager = TextureManager(ctx)
    
    img_mock = MagicMock()
    # Mock valid PIL shape
    img_mock.convert.return_value = img_mock
    img_mock.transpose.return_value = img_mock
    img_mock.size = (200, 100)
    img_mock.getbands.return_value = ('R', 'G', 'B')
    img_mock.tobytes.return_value = np.zeros((100, 200, 3), dtype=np.uint8).tobytes()
    
    mock_pil.open.return_value = img_mock
    
    tex = manager.create_from_image("img1", "fake.jpg")
    
    assert tex is not None
    assert tex.width == 200
    assert tex.height == 100
    assert tex.components == 3
    
    manager.cleanup()
    
def test_error_cases(gl_context):
    ctx = gl_context.ctx
    if not ctx:
        pytest.skip("No modernGL context")
        
    manager = TextureManager(ctx)
    
    # Invalid buffer payload dimension mismatch
    with pytest.raises(ValueError):
        manager.create_from_buffer("bad", b"123", (10, 10), 3)
        
    # Bad image path
    res = manager.create_from_image("bad", "/tmp/does_not_exist_99.png")
    assert res is None
    
    # Empty unallocated update ignores payload instead of crashing
    manager.update_texture(None, b"123")
    
    manager.cleanup()
    
def test_reserve_texture(gl_context):
    ctx = gl_context.ctx
    if not ctx:
        pytest.skip("No modernGL context")
        
    manager = TextureManager(ctx)
    
    # Create baseline reserve
    t1 = manager.reserve_texture("stream", (100, 100), 3)
    assert t1.width == 100
    
    # Re-reserve with same size yields cache
    t2 = manager.reserve_texture("stream", (100, 100), 3)
    assert t1 is t2
    
    # Re-reserve with modified constraints forces eviction and re-alloc
    t3 = manager.reserve_texture("stream", (200, 200), 4)
    assert t1 is not t3
    assert t3.components == 4
    
    manager.cleanup()
