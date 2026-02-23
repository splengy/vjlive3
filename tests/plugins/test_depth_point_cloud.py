"""
Unit tests for P3-VD37: DepthPointCloudEffect
"""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from vjlive3.plugins.depth_point_cloud import DepthPointCloudPlugin, create_plugin
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    return create_plugin()

@pytest.fixture
def context():
    ctx = MagicMock(spec=PluginContext)
    ctx.textures = {"depth_map": 42}
    return ctx

def test_plugin_metadata(plugin):
    """Test metadata reporting adheres rigorously to standard."""
    meta = plugin.get_metadata()
    assert meta["name"] == "DepthPointCloud"
    assert "depth_in" in meta["inputs"]
    assert len(meta["parameters"]) == 5

@patch('vjlive3.plugins.depth_point_cloud.gl')
@patch('vjlive3.plugins.depth_point_cloud.hasattr')
def test_plugin_initialization_mock_mode(mock_hasattr, mock_gl, plugin, context):
    """Test shader compiling fallbacks correctly."""
    mock_hasattr.return_value = True
    context.engine = None
    mock_gl.glCreateProgram.return_value = 1
    mock_gl.glCreateShader.return_value = 2
    mock_gl.glGetShaderiv.return_value = 1
    mock_gl.glGetProgramiv.return_value = 1
    
    assert plugin.initialize(context) is True
    assert plugin._initialized is True
    assert plugin.program == 1

def test_process_frame_empty_input(plugin, context):
    """Ensure unmodified frames pass through safely when OpenGL is unavailable."""
    # Force _initialized false
    res = plugin.process_frame(123, {}, context)
    assert res == 123
    
@patch('vjlive3.plugins.depth_point_cloud.gl')
def test_process_frame_mock_mode(mock_gl, plugin, context):
    """Test texture binding and uniform assignment correctly channels inputs."""
    plugin._initialized = True
    plugin.program = 99
    plugin.width = 1920
    plugin.height = 1080
    plugin.fbo = 12
    plugin.target_texture = 13
    
    # Overwrite `has_gl` internally dynamically
    with patch('vjlive3.plugins.depth_point_cloud.hasattr') as mock_hasattr:
        # We need mock_hasattr to return True when checking gl.glBindFramebuffer 
        # but the test runner runs code, we must ensure it doesn't fail on missing attributes
        mock_hasattr.return_value = True 
        
        # We also mock ctypes to prevent quad draw from attempting real buffers on mock
        with patch('vjlive3.plugins.depth_point_cloud.ctypes'):
            # Basic mapping test
            params = {
                "mix_amount": 0.5,
                "point_size": 10.0,
                "min_depth": 1.0, 
                "max_depth": 5.0
            }
            res = plugin.process_frame(777, params, context)
            
            # Assert return texture
            assert res == 13
            
            # Assert depth variables injected accurately
            mock_gl.glUseProgram.assert_any_call(99)
            mock_gl.glBindTexture.assert_any_call(mock_gl.GL_TEXTURE_2D, 777)
            mock_gl.glBindTexture.assert_any_call(mock_gl.GL_TEXTURE_2D, 42)
            
            # Ensure quad drawing mechanism functioned
            mock_gl.glDrawArrays.assert_called()

def test_gl_compile_failure(plugin):
    """Ensure plugin refuses initialization if gl compilation fails bounds"""
    with patch('vjlive3.plugins.depth_point_cloud.hasattr') as mock_hasattr:
        mock_hasattr.return_value = False
        assert plugin.initialize(MagicMock()) is False

@patch('vjlive3.plugins.depth_point_cloud.gl')
def test_plugin_cleanup(mock_gl, plugin):
    """Validate systematic memory destruction on garbage collection closure."""
    plugin._initialized = True
    plugin.program = 1
    plugin.fbo = 2
    plugin.target_texture = 3
    
    # Needs mock_hasattr to bypass OpenGL limitations in raw pytest
    with patch('vjlive3.plugins.depth_point_cloud.hasattr', return_value=True):
        plugin.cleanup()
        
    mock_gl.glDeleteProgram.assert_called_once_with(1)
    mock_gl.glDeleteFramebuffers.assert_called_once_with(1, [2])
    mock_gl.glDeleteTextures.assert_called_once_with(1, [3])
    assert plugin._initialized is False
