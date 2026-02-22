import pytest
import os
import tempfile
import time
from vjlive3.render.shader_compiler import ShaderCompiler, ShaderInfo
from vjlive3.render.program import PASSTHROUGH_FRAGMENT
from vjlive3.render.opengl_context import OpenGLContext

@pytest.fixture(scope="session")
def gl_context():
    os.environ['VJ_HEADLESS'] = 'true'
    ctx = OpenGLContext(800, 600, headless=True)
    ctx.make_current()
    yield ctx
    ctx.terminate()

def test_init_no_hardware():
    # Should not crash if dir does not exist initially
    sc = ShaderCompiler("/tmp/nonexistent_shader_dir_12345")
    assert sc.shader_dir == "/tmp/nonexistent_shader_dir_12345"
    sc.cleanup()

def test_glsl_compilation(gl_context):
    sc = ShaderCompiler()
    # Test successful compile
    prg = sc.compile_glsl(PASSTHROUGH_FRAGMENT, 'fragment', 'pass_test')
    assert prg is not None
    assert prg.name == "pass_test"
    
    info = sc.get_shader_info('pass_test')
    assert info is not None
    assert info.status == 'ok'
    assert info.type == 'glsl'
    
    cached = sc.get_shader('pass_test')
    assert cached is prg
    
    assert 'pass_test' in sc.list_shaders()
    
    sc.cleanup()

def test_error_handling(gl_context):
    sc = ShaderCompiler()
    
    # Intentionally bad glsl syntax
    bad_glsl = "in vec2 v; void main() { broken_syntax!!!! }"
    prg = sc.compile_glsl(bad_glsl, name='bad')
    
    # Should return None and log error info, gracefully swallowing the ShaderProgram crash
    assert prg is None
    info = sc.get_shader_info('bad')
    assert info is not None
    assert info.status == 'error'
    assert 'C5060' in info.error_message or 'GLSL Compiler failed' in info.error_message
    
    sc.cleanup()

def test_milkdrop_compilation(gl_context):
    sc = ShaderCompiler()
    
    # Empty preset rejection
    prg_empty = sc.compile_milkdrop("", "empty_milk")
    assert prg_empty is None
    
    # Valid syntax parses into wrapper glsl
    prg = sc.compile_milkdrop("[preset00]\nper_frame_1=wave_r=0.5", "milk_1")
    assert prg is not None
    
    info = sc.get_shader_info('milk_1')
    assert info.type == 'milkdrop'
    assert info.status == 'ok'
    
    sc.cleanup()
    
def test_shader_caching_and_hot_reload(gl_context):
    with tempfile.TemporaryDirectory() as td:
        sc = ShaderCompiler(td)
        
        file_path = os.path.join(td, "test_shader.glsl")
        with open(file_path, 'w') as f:
            f.write(PASSTHROUGH_FRAGMENT)
            
        # Register path
        success = sc.register_shader_path("live_test", file_path)
        assert success is True
        
        prg1 = sc.get_shader("live_test")
        assert prg1 is not None
        
        # Modify file with intentional bug to trigger reload failure
        with open(file_path, 'w') as f:
            f.write("INVALID GLSL")
            
        # Trigger reload manually (bypassing watchdog debounce for immediate test sync)
        success = sc.reload_shader("live_test")
        assert success is False
        
        info = sc.get_shader_info("live_test")
        assert info.status == 'error'
        
        # Fix file and reload
        modified_sz = PASSTHROUGH_FRAGMENT.replace("texture(tex0, v_uv)", "vec4(1.0, 0.0, 0.0, 1.0)")
        with open(file_path, 'w') as f:
            f.write(modified_sz)
            
        success = sc.reload_shader("live_test")
        assert success is True
        
        prg2 = sc.get_shader("live_test")
        assert prg2 is not None
        # Reference should swap cleanly on hot reload successfully
        assert prg1 is not prg2
        
        sc.cleanup()

def test_missing_shader_reload(gl_context):
    sc = ShaderCompiler()
    # Missing path fails gracefully
    sc.register_shader_path('ghost', '/tmp/does_not_exist.glsl')
    assert sc.reload_shader('ghost') is False
    info = sc.get_shader_info('ghost')
    assert info.status == 'error'
    sc.cleanup()
