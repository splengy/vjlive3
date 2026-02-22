import pytest
import numpy as np
from vjlive3.render.chain import EffectChain
from vjlive3.render.effect import Effect
from vjlive3.render.opengl_context import OpenGLContext
import os

@pytest.fixture(scope="session")
def gl_context():
    os.environ['VJ_HEADLESS'] = 'true'
    ctx = OpenGLContext(800, 600, headless=True)
    ctx.make_current()
    yield ctx
    ctx.terminate()

def test_effect_chain_create(gl_context):
    chain = EffectChain(1920, 1080)
    assert chain.fbo_a is not None
    assert chain.fbo_b is not None
    assert chain.vbo is not None
    assert chain.vao is not None
    chain.delete()

def test_effect_chain_add_remove(gl_context):
    chain = EffectChain()
    e = Effect("test_eff", "void main() {}")
    chain.add_effect(e)
    assert "test_eff" in chain.get_available_effects()
    chain.remove_effect("test_eff")
    assert "test_eff" not in chain.get_available_effects()

def test_effect_chain_no_effects(gl_context):
    chain = EffectChain()
    out = chain.render(42)
    # If no effects, returns the input texture unmodified
    assert out == 42
    chain.delete()

def test_effect_chain_render_passthrough(gl_context):
    chain = EffectChain(256, 256)
    e = Effect("passthrough", "#version 330 core\nin vec2 v_uv; out vec4 f; uniform sampler2D tex0; void main() { f = texture(tex0, v_uv); }")
    chain.add_effect(e)
    # Create a dummy native texture to pass in
    dummy = np.zeros((256, 256, 3), dtype=np.uint8)
    tex_id = chain.upload_texture(dummy)
    out = chain.render(tex_id, extra_textures=[tex_id], audio_reactor=True, semantic_layer=True)
    assert out > 0
    assert out != tex_id # Rendered to a new FBO texture
    chain.delete()

def test_effect_chain_delete(gl_context):
    chain = EffectChain()
    chain.delete()
    assert chain.fbo_a._mgl_fbo is None
    
def test_effect_chain_context_manager(gl_context):
    with EffectChain(10, 10) as chain:
        assert chain.fbo_a is not None
    assert chain.fbo_a._mgl_fbo is None
    
def test_effect_chain_readback(gl_context):
    chain = EffectChain(64, 64)
    dummy = np.ones((64, 64, 3), dtype=np.uint8) * 255
    tex_id = chain.upload_texture(dummy)
    e = Effect("passthrough", "#version 330 core\nin vec2 v_uv; out vec4 f; uniform sampler2D tex0; void main() { f = texture(tex0, v_uv); }")
    chain.add_effect(e)
    chain.render(tex_id)
    
    # Sync readback
    arr = chain.readback_last_output()
    assert arr is not None
    assert arr.shape == (64, 64, 3)
    
    # Async PBO readback N-1 frame
    # Frame 1: Reads Nothing
    arr_pbo = chain.readback_texture_async(tex_id, 'rgb')
    assert arr_pbo is None
    # Frame 2: Reads Frame 1
    arr_pbo = chain.readback_texture_async(tex_id, 'rgb')
    assert arr_pbo is not None
    assert arr_pbo.shape == (64, 64, 3)
    
    chain.delete()

def test_spatial_view(gl_context):
    chain = EffectChain(128, 128)
    chain.set_spatial_view([0.5, 0.5], [1.0, 1.0])
    assert chain.view_offset == [0.5, 0.5]
    chain.delete()

def test_projection_mapping(gl_context):
    chain = EffectChain()
    # 8 length list representing 4 corners xy
    corners = [0.0]*8
    chain.set_projection_mapping(warp_mode=1, corners=corners)
    assert chain.post_processing_shader is not None
    # Program bound state tests automatically verified above without raising
    chain.delete()
    
def test_effect_chain_upload_texture(gl_context):
    chain = EffectChain()
    dummy = np.zeros((720, 1280, 3), dtype=np.uint8)
    tex_id = chain.upload_texture(dummy)
    assert tex_id > 0
    
    chain.update_texture(tex_id, np.ones((720, 1280, 3), dtype=np.uint8)*255)
    
    
    # Hit the resize path in update_texture
    chain.update_texture(tex_id, np.ones((1080, 1920, 3), dtype=np.uint8)*255)
    
    tex_float = chain.upload_float_texture(np.zeros((64, 64, 4), dtype=np.float32))
    assert tex_float > 0
    chain.update_float_texture(tex_float, np.ones((64, 64, 4), dtype=np.float32))
    
    chain.delete()

def test_effect_pre_process_hook(gl_context):
    chain = EffectChain(128, 128)
    class HookEffect(Effect):
        def pre_process(self, chain, input_tex):
            # return the same texture or an artificial bypass int
            return input_tex + 1
            
    e = HookEffect("hook", "#version 330 core\nin vec2 v_uv; out vec4 f; uniform sampler2D tex0; void main() { f = texture(tex0, v_uv); }")
    chain.add_effect(e)
    chain.render(42) # Intentionally pass dummy integer to see if it survives tracking bypasses
    chain.delete()

def test_chain_render_to_screen_and_downsample(gl_context):
    chain = EffectChain(128, 128)
    dummy = np.zeros((128, 128, 3), dtype=np.uint8)
    tex_id = chain.upload_texture(dummy)
    
    # Hit render_to_screen
    chain.render_to_screen(tex_id, (0, 0, 128, 128))
    
    # Hit downsampled fbo logic
    dfbo = chain.create_downsampled_fbo(64, 64)
    assert dfbo is not None
    chain.render_to_downsampled_fbo(tex_id, dfbo)
    
    dfbo.delete()
    chain.delete()
