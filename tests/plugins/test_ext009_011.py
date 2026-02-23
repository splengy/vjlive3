"""Tests for P3-EXT009-011: Raymarched Scenes, Spectrum Trails, Background Subtraction."""
import sys, pytest
from unittest.mock import MagicMock, patch

_g = MagicMock()
_g.glGetShaderiv.return_value   = 1
_g.glGetProgramiv.return_value  = 1
_g.glCreateProgram.return_value = 99
_g.glGenVertexArrays.return_value = 44
_g.glGenFramebuffers.return_value = 55
_g.glGenTextures.return_value   = 101
for attr in ("GL_VERTEX_SHADER","GL_FRAGMENT_SHADER","GL_COMPILE_STATUS","GL_LINK_STATUS",
             "GL_TEXTURE_2D","GL_TRIANGLE_STRIP","GL_TEXTURE0","GL_TEXTURE1",
             "GL_RGB","GL_UNSIGNED_BYTE","GL_LINEAR","GL_CLAMP_TO_EDGE","GL_RED","GL_FLOAT",
             "GL_TEXTURE_MIN_FILTER","GL_TEXTURE_MAG_FILTER","GL_TEXTURE_WRAP_S","GL_TEXTURE_WRAP_T",
             "GL_FRAMEBUFFER","GL_COLOR_ATTACHMENT0","GL_R32F","GL_RG32F"):
    setattr(_g, attr, MagicMock())

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = _g



@pytest.fixture(autouse=True)
def reset_gl():
    _g.reset_mock()
    _g.glGetShaderiv.return_value   = 1
    _g.glGetProgramiv.return_value  = 1
    _g.glCreateProgram.return_value = 99
    _g.glGenVertexArrays.return_value = 44
    _g.glGenTextures.return_value = 101


@pytest.fixture
def ctx():
    c = MagicMock()(MagicMock())
    c.width = 64; c.height = 48; c.time = 0.0
    c.inputs = {"video_in": 10}; c.outputs = {}
    return c


# ══════════════════════════════════════════════════════════════════════════════
# EXT009: AudioReactiveRaymarchedScenes
# ══════════════════════════════════════════════════════════════════════════════

from vjlive3.plugins.audio_reactive_raymarched_scenes import (
    AudioReactiveRaymarchedScenesPlugin, METADATA as RM_META, PRESETS as RM_PRESETS
)

@pytest.fixture
def rm_plugin(): return AudioReactiveRaymarchedScenesPlugin()

def test_rm_metadata_name():    assert RM_META["name"] == "Audio Reactive Raymarched Scenes"
def test_rm_metadata_params():  assert len(RM_META["parameters"]) == 14
def test_rm_presets():          assert len(RM_PRESETS) == 5
def test_rm_scene_type_mapping():
    # scene_type=0 → int(0)/10*2=0, 3.5→int(3.5/10*2)=0... really int is 0
    from vjlive3.plugins.audio_reactive_raymarched_scenes import _c
    v = _c(3.5); assert 0 <= int(v/10.*2.) <= 2

@patch('vjlive3.plugins.audio_reactive_raymarched_scenes.gl', _g)
def test_rm_initialize(rm_plugin, ctx): assert rm_plugin.initialize(ctx) is True

@patch('vjlive3.plugins.audio_reactive_raymarched_scenes.gl', _g)
def test_rm_zero_texture(rm_plugin, ctx): assert rm_plugin.process_frame(0, {}, ctx) == 0

@patch('vjlive3.plugins.audio_reactive_raymarched_scenes.gl', _g)
def test_rm_draw_called(rm_plugin, ctx):
    rm_plugin.initialize(ctx); rm_plugin.process_frame(10, {}, ctx)
    _g.glDrawArrays.assert_called()

@patch('vjlive3.plugins.audio_reactive_raymarched_scenes.gl', _g)
def test_rm_all_params(rm_plugin, ctx):
    rm_plugin.initialize(ctx)
    params = {p["name"]: p["default"] for p in RM_META["parameters"]}
    assert rm_plugin.process_frame(10, params, ctx) is not None

@patch('vjlive3.plugins.audio_reactive_raymarched_scenes.gl', _g)
def test_rm_fractal_preset(rm_plugin, ctx):
    rm_plugin.initialize(ctx)
    assert rm_plugin.process_frame(10, RM_PRESETS["fractal_zoom"], ctx) is not None

@patch('vjlive3.plugins.audio_reactive_raymarched_scenes.gl', _g)
def test_rm_compile_failure(rm_plugin, ctx):
    _g.glGetShaderiv.return_value = 0; _g.glGetShaderInfoLog.return_value = b"err"
    assert rm_plugin.initialize(ctx) is False

def test_rm_mock_mode(rm_plugin, ctx):
    rm_plugin._mock_mode = True
    assert rm_plugin.process_frame(10, {}, ctx) == 10

@patch('vjlive3.plugins.audio_reactive_raymarched_scenes.gl', _g)
def test_rm_cleanup(rm_plugin, ctx):
    rm_plugin.initialize(ctx); rm_plugin.prog = 99; rm_plugin.cleanup()
    _g.glDeleteProgram.assert_called_with(99)


# ══════════════════════════════════════════════════════════════════════════════
# EXT010: AudioSpectrumTrails
# ══════════════════════════════════════════════════════════════════════════════

from vjlive3.plugins.audio_spectrum_trails import (
    AudioSpectrumTrailsPlugin, METADATA as ST_META, PRESETS as ST_PRESETS,
    _trail_decay, _spec_height, _freq_bands, _color_mode, _opacity
)

@pytest.fixture
def st_plugin(): return AudioSpectrumTrailsPlugin()

def test_st_metadata_name():   assert ST_META["name"] == "Audio Spectrum Trails"
def test_st_metadata_params(): assert len(ST_META["parameters"]) == 6
def test_st_presets():         assert len(ST_PRESETS) == 5

# Param mappings
def test_trail_decay_0():   assert abs(_trail_decay(0.0)  - 0.80) < 0.001
def test_trail_decay_10():  assert abs(_trail_decay(10.0) - 0.99) < 0.001
def test_spec_height_0():   assert abs(_spec_height(0.0)  - 0.10) < 0.001
def test_spec_height_10():  assert abs(_spec_height(10.0) - 1.00) < 0.001
def test_freq_bands_0():    assert _freq_bands(0.0)  ==  16
def test_freq_bands_10():   assert _freq_bands(10.0) == 256
def test_color_mode_0():    assert _color_mode(0.0)  == 0
def test_color_mode_5():    assert _color_mode(5.0)  == 1
def test_color_mode_10():   assert _color_mode(10.0) == 2
def test_opacity_0():       assert abs(_opacity(0.0)  - 0.1) < 0.001
def test_opacity_10():      assert abs(_opacity(10.0) - 1.0) < 0.001

@patch('vjlive3.plugins.audio_spectrum_trails.gl', _g)
def test_st_initialize(st_plugin, ctx): assert st_plugin.initialize(ctx) is True

@patch('vjlive3.plugins.audio_spectrum_trails.gl', _g)
def test_st_zero_texture(st_plugin, ctx): assert st_plugin.process_frame(0, {}, ctx) == 0

@patch('vjlive3.plugins.audio_spectrum_trails.gl', _g)
def test_st_draw_called(st_plugin, ctx):
    st_plugin.initialize(ctx); st_plugin.process_frame(10, {}, ctx)
    _g.glDrawArrays.assert_called()

@patch('vjlive3.plugins.audio_spectrum_trails.gl', _g)
def test_st_update_audio(st_plugin, ctx):
    st_plugin.update_audio({"bass": 0.8, "volume": 0.5})
    assert st_plugin._bass   == 0.8
    assert st_plugin._volume == 0.5

def test_st_update_audio_spectrum(st_plugin):
    st_plugin.update_audio({"spectrum": [0.5]*256})
    assert len(st_plugin._spectrum) == 512

@patch('vjlive3.plugins.audio_spectrum_trails.gl', _g)
def test_st_compile_failure(st_plugin, ctx):
    _g.glGetShaderiv.return_value = 0; _g.glGetShaderInfoLog.return_value = b"err"
    assert st_plugin.initialize(ctx) is False

def test_st_mock_mode(st_plugin, ctx):
    st_plugin._mock_mode = True
    assert st_plugin.process_frame(10, {}, ctx) == 10

@patch('vjlive3.plugins.audio_spectrum_trails.gl', _g)
def test_st_cleanup(st_plugin, ctx):
    st_plugin.initialize(ctx); st_plugin.spec_tex = 101; st_plugin.cleanup()
    _g.glDeleteTextures.assert_called()


# ══════════════════════════════════════════════════════════════════════════════
# EXT011: BackgroundSubtraction
# ══════════════════════════════════════════════════════════════════════════════

from vjlive3.plugins.background_subtraction import (
    BackgroundSubtractionPlugin, METADATA as BS_META, PRESETS as BS_PRESETS,
    _effect_mode, _blur_kernel
)

@pytest.fixture
def bs_plugin(): return BackgroundSubtractionPlugin()

def test_bs_metadata_name():   assert BS_META["name"] == "Background Subtraction"
def test_bs_metadata_params(): assert len(BS_META["parameters"]) == 8
def test_bs_presets():         assert len(BS_PRESETS) == 5

# Helpers
def test_effect_mode_0():    assert _effect_mode(0.0)  == 0
def test_effect_mode_5():    assert _effect_mode(5.0)  == 1
def test_effect_mode_10():   assert _effect_mode(10.0) == 2
def test_blur_kernel_0():    assert _blur_kernel(0.)   == 1   # 0|1 = 1 (odd)
def test_blur_kernel_5():    ks = _blur_kernel(5.);  assert ks % 2 == 1   # Always odd

@patch('vjlive3.plugins.background_subtraction.gl', _g)
def test_bs_initialize(bs_plugin, ctx): assert bs_plugin.initialize(ctx) is True

@patch('vjlive3.plugins.background_subtraction.gl', _g)
def test_bs_zero_texture(bs_plugin, ctx): assert bs_plugin.process_frame(0, {}, ctx) == 0

@patch('vjlive3.plugins.background_subtraction.gl', _g)
def test_bs_draw_called(bs_plugin, ctx):
    bs_plugin.initialize(ctx); bs_plugin.process_frame(10, {}, ctx)
    _g.glDrawArrays.assert_called()

@patch('vjlive3.plugins.background_subtraction.gl', _g)
def test_bs_compile_failure(bs_plugin, ctx):
    _g.glGetShaderiv.return_value = 0; _g.glGetShaderInfoLog.return_value = b"err"
    assert bs_plugin.initialize(ctx) is False

def test_bs_mock_mode(bs_plugin, ctx):
    bs_plugin._mock_mode = True
    assert bs_plugin.process_frame(10, {}, ctx) == 10

@patch('vjlive3.plugins.background_subtraction.gl', _g)
def test_bs_all_presets(bs_plugin, ctx):
    bs_plugin.initialize(ctx)
    for preset in BS_PRESETS.values():
        assert bs_plugin.process_frame(10, preset, ctx) is not None

@patch('vjlive3.plugins.background_subtraction.gl', _g)
def test_bs_cleanup(bs_plugin, ctx):
    bs_plugin.initialize(ctx); bs_plugin.prog = 99; bs_plugin.cleanup()
    _g.glDeleteProgram.assert_called_with(99)
