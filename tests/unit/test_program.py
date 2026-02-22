import pytest
from vjlive3.render.program import ShaderProgram, BASE_VERTEX_SHADER, PASSTHROUGH_FRAGMENT
from vjlive3.render.opengl_context import OpenGLContext
import os
import numpy as np

@pytest.fixture(scope="session")
def gl_context():
    os.environ['VJ_HEADLESS'] = 'true'
    ctx = OpenGLContext(800, 600, headless=True)
    ctx.make_current()
    yield ctx
    ctx.terminate()

def test_shader_compile_passthrough(gl_context):
    sp = ShaderProgram(BASE_VERTEX_SHADER, PASSTHROUGH_FRAGMENT)
    assert sp.program > 0
    assert sp.name == "unnamed"
    assert "tex0" in sp.uniforms
    sp.delete()

def test_shader_bad_vertex_raises(gl_context):
    with pytest.raises(RuntimeError):
        ShaderProgram("invalid glsl", PASSTHROUGH_FRAGMENT)

def test_shader_bad_fragment_raises(gl_context):
    with pytest.raises(RuntimeError):
        ShaderProgram(BASE_VERTEX_SHADER, "invalid glsl")

def test_shader_set_uniform_int(gl_context):
    sp = ShaderProgram(BASE_VERTEX_SHADER, PASSTHROUGH_FRAGMENT)
    sp.set_uniform("tex0", 1)
    # ModernGL uniform representation evaluation
    assert sp._mgl_program['tex0'].value == 1
    sp.delete()

def test_shader_set_uniform_float(gl_context):
    sp = ShaderProgram(
        BASE_VERTEX_SHADER, 
        """#version 330 core\nuniform float test_float;\nout vec4 color; void main() { color = vec4(test_float); }"""
    )
    sp.set_uniform("test_float", 5.5)
    assert sp._mgl_program['test_float'].value == 5.5
    sp.delete()

def test_shader_set_unknown_uniform(gl_context):
    sp = ShaderProgram(BASE_VERTEX_SHADER, PASSTHROUGH_FRAGMENT)
    sp.set_uniform("does_not_exist", 42) # Should not raise
    sp.delete()
    
def test_shader_set_uniform_vectors(gl_context):
    # Validates tuple[2], ndarray combinations
    sp = ShaderProgram(
        BASE_VERTEX_SHADER, 
        """#version 330 core\nuniform vec3 test_vec;\nout vec4 color; void main() { color = vec4(test_vec, 1.0); }"""
    )
    sp.set_uniform("test_vec", [1.0, 2.0, 3.0])
    v = sp._mgl_program['test_vec'].value
    assert list(v) == [1.0, 2.0, 3.0]
    sp.delete()
