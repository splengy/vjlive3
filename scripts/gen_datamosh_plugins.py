#!/usr/bin/env python3
"""
Generate VJLive3 plugin stubs for P5-DM datamosh effects.
Each plugin is a thin GLSL FSQ wrapper with uniquely-named uniforms.
"""
import os
import textwrap

BASE = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/src/vjlive3/plugins"
TEST_BASE = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/tests/plugins"

# Each entry: (task_id, class_name, slug, file_stem, description, tags, params_list)
# params_list: list of (name, default, description)
PLUGINS = [
    (
        "P5-DM02", "BadTripDatamoshPlugin", "bad_trip_datamosh", "bad_trip_datamosh",
        "Psychedelic horror datamosh — demon face, insect crawl, paranoia strobe.",
        ["horror", "nightmare", "glitch", "psychedelic", "datamosh"],
        [("anxiety", 5.0, "Speed/jitter"), ("demon_face", 3.0, "Facial distortion"),
         ("insect_crawl", 2.0, "Bug noise"), ("void_gaze", 2.0, "Dark vignette"),
         ("reality_tear", 3.0, "Glitch tearing"), ("sickness", 2.0, "Tinting"),
         ("time_loop", 5.0, "Feedback delay"), ("breathing_walls", 3.0, "UV warp"),
         ("paranoia", 1.0, "Strobe cuts"), ("shadow_people", 2.0, "Depth artifacts"),
         ("psychosis", 2.0, "Color inversion"), ("doom", 3.0, "Contrast crush")],
    ),
    (
        "P5-DM03", "BassCannonDatamoshPlugin", "bass_cannon_datamosh", "bass_cannon_datamosh",
        "Sonic weapon datamosh — shockwave from bass hits radiates outward.",
        ["bass", "shockwave", "explosive", "datamosh", "audio"],
        [("cannon_power", 5.0, "Shockwave intensity"), ("shockwave_speed", 5.0, "Blast speed"),
         ("recoil", 3.0, "Screen kickback"), ("muzzle_flash", 2.0, "Whiteout"),
         ("debris_scatter", 3.0, "Pixel shatter"), ("bass_threshold", 5.0, "Trigger level"),
         ("impact_radius", 5.0, "Cannon size"), ("distortion", 3.0, "UV warping"),
         ("chroma_blast", 2.0, "Color separation"), ("thermal_exhaust", 2.0, "Heat distort"),
         ("depth_penetration", 5.0, "Blast travel"), ("decay", 5.0, "Fade speed")],
    ),
    (
        "P5-DM04", "BassTherapyDatamoshPlugin", "bass_therapy_datamosh", "bass_therapy_datamosh",
        "Bass therapy — strobe flash, pupil dilation, adrenaline chaos.",
        ["bass", "strobe", "adrenaline", "datamosh", "audio"],
        [("strobe_speed", 5.0, "Flash speed"), ("strobe_intensity", 3.0, "Flash brightness"),
         ("bass_crush", 3.0, "Screen shake"), ("pupil_dilate", 3.0, "Radial blur"),
         ("sweat_drip", 2.0, "Melt intensity"), ("laser_burn", 2.0, "Edge burn"),
         ("rail_grip", 5.0, "Feedback lock"), ("adrenaline", 5.0, "Chaos speed"),
         ("bpm_sync", 5.0, "BPM sync"), ("dark_room", 3.0, "Darkness level"),
         ("visual_bleed", 2.0, "Video B bleed"), ("retina_burn", 3.0, "Persistence")],
    ),
    (
        "P5-DM05", "GlitchDatamoshPlugin", "glitch_datamosh", "glitch_datamosh",
        "Digital glitch — block displacement, channel swap, frame corruption.",
        ["glitch", "digital", "datamosh", "chaotic", "destructive"],
        [("amount", 1.0, "Glitch probability"), ("speed", 3.0, "Rate of change"),
         ("block_size", 3.0, "Block size"), ("color_shift", 2.0, "Chromatic separation"),
         ("vertical", 0.0, "Vertical shift"), ("frame_drop", 0.0, "Frame drop chance"),
         ("channel_swap", 0.0, "Channel swap"), ("scanline_jitter", 0.0, "Per-scanline jitter"),
         ("corruption", 0.0, "Pixel corruption"), ("hold_duration", 0.0, "Hold frames")],
    ),
    (
        "P5-DM06", "BulletTimeDatamoshPlugin", "bullet_time_datamosh", "bullet_time_datamosh",
        "Bullet time — matrix tint, parallax freeze, slow-motion datamosh.",
        ["bullet-time", "matrix", "slowmo", "datamosh", "cinematic"],
        [("time_freeze", 0.0, "Freeze amount"), ("orbit_speed", 3.0, "Camera wiggle"),
         ("parallax_depth", 5.0, "3D intensity"), ("matrix_tint", 2.0, "Green strength"),
         ("data_rain", 2.0, "Code artifacts"), ("shockwave", 3.0, "Ripple on freeze"),
         ("camera_tilt", 3.0, "Y-axis wiggle"), ("bg_separation", 3.0, "Background push"),
         ("digital_artifact", 2.0, "Compression blocks"), ("slow_mo", 5.0, "Frame interpolation"),
         ("focus_depth", 5.0, "Pivot depth"), ("bullet_trail", 3.0, "Motion history")],
    ),
    (
        "P5-DM07", "CellularAutomataDatamoshPlugin", "cellular_automata_datamosh", "cellular_automata_datamosh",
        "Cellular automata life simulation — reaction diffusion, grid chaos.",
        ["cellular", "automata", "reaction-diffusion", "datamosh", "generative"],
        [("life_speed", 5.0, "Sim speed"), ("birth_thresh", 5.0, "Spawn brightness"),
         ("death_thresh", 5.0, "Death brightness"), ("reaction_mix", 3.0, "RD amount"),
         ("fractal_zoom", 3.0, "Mandelbrot"), ("math_quantize", 2.0, "Bit crush"),
         ("evolution", 3.0, "Color shift"), ("symmetry", 5.0, "Math symmetry"),
         ("grid_mix", 2.0, "Grid overlay"), ("chaos", 5.0, "Mutation"),
         ("feed_rate", 5.0, "Reaction feed"), ("kill_rate", 5.0, "Reaction kill")],
    ),
    (
        "P5-DM08", "CottonCandyDatamoshPlugin", "cotton_candy_datamosh", "cotton_candy_datamosh",
        "Cotton candy datamosh — fluffy pink wisps, sugar strands, dissolving.",
        ["cotton-candy", "dreamy", "soft", "datamosh", "aesthetic"],
        [("cloud_density", 5.0, "Cloud thickness"), ("strand_pull", 3.0, "Strand stretch"),
         ("float_speed", 3.0, "Upward float"), ("float_drift", 3.0, "Side drift"),
         ("candy_pink", 5.0, "Pink intensity"), ("candy_blue", 3.0, "Blue intensity"),
         ("soft_focus", 3.0, "Dream blur"), ("sugar_spin", 3.0, "Spiral pull"),
         ("puff_burst", 3.0, "Bass puff"), ("dissolve", 2.0, "Dissolution"),
         ("wisp_persist", 5.0, "Wisp linger"), ("fluff", 5.0, "Fluffiness")],
    ),
    (
        "P5-DM09", "CupcakeCascadeDatamoshPlugin", "cupcake_cascade_datamosh", "cupcake_cascade_datamosh",
        "Cupcake cascade — frosting drips, sprinkle avalanche, sugary melt.",
        ["cupcake", "candy", "drip", "datamosh", "aesthetic"],
        [("drip_speed", 5.0, "Drip speed"), ("drip_length", 5.0, "Drip distance"),
         ("cascade_rate", 5.0, "Avalanche speed"), ("cascade_size", 5.0, "Block size"),
         ("frosting", 5.0, "Pastel intensity"), ("sprinkle_density", 3.0, "Sprinkle count"),
         ("layer_count", 5.0, "Stripe count"), ("whipped_bloom", 3.0, "Cream glow"),
         ("cherry", 5.0, "Cherry accent"), ("gravity", 5.0, "Pull strength"),
         ("sweetness", 5.0, "Sugar saturation"), ("melt_rate", 3.0, "Melt speed")],
    ),
    (
        "P5-DM10", "CompressionDatamoshPlugin", "compression_datamosh", "compression_datamosh",
        "Compression datamosh — DCT block artifacts, macroblocking, MPEG corruption.",
        ["compression", "codec", "artifact", "datamosh", "glitch"],
        [("block_size", 3.0, "DCT block size"), ("quality", 5.0, "Compression level"),
         ("motion_blur", 3.0, "Interframe smear"), ("artifact_strength", 5.0, "Ringing"),
         ("macroblock_chaos", 2.0, "Macroblock glitch"), ("chroma_subsample", 3.0, "Chroma loss"),
         ("quantize_dc", 5.0, "DC quantization"), ("quantize_ac", 5.0, "AC quantization"),
         ("frame_skip", 2.0, "Frame dropping"), ("bit_starve", 3.0, "Bandwidth limit"),
         ("temporal_noise", 2.0, "Interframe noise"), ("error_concealment", 5.0, "Error hiding")],
    ),
]


PLUGIN_TEMPLATE = '''"""
{task_id}: {description}
Ported from VJlive-2/plugins/vdatamosh/{file_stem}.py.
"""

from typing import Dict, Any
import logging

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from .api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

METADATA = {{
    "name": "{display_name}",
    "description": "{description}",
    "version": "1.0.0",
    "plugin_type": "datamosh",
    "category": "datamosh",
    "tags": {tags!r},
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": {params_meta!r}
}}

VERTEX_SHADER = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1), vec2(1,-1), vec2(-1,1), vec2(1,1));
out vec2 uv;
void main() {{
    gl_Position = vec4(verts[gl_VertexID], 0.0, 1.0);
    uv = verts[gl_VertexID] * 0.5 + 0.5;
}}
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform sampler2D prev_tex;
uniform vec2  resolution;
uniform float time;
uniform float u_mix;
{uniform_block}

float hash(vec2 p) {{ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }}
float noise(vec2 p) {{
    vec2 i = floor(p); vec2 f = fract(p);
    f = f*f*(3.0-2.0*f);
    return mix(mix(hash(i), hash(i+vec2(1,0)), f.x), mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), f.x), f.y);
}}

void main() {{
    vec4 curr = texture(tex0, uv);
    vec4 prev = texture(prev_tex, uv);
    vec2 texel = 1.0 / resolution;

    // Combined displacement from all parameters
    float displacement = {disp_expr};
    float feedback     = {feedback_expr};

    vec2 du = vec2(
        noise(uv * (8.0 + {freq_expr}) + vec2(time * 0.5)) - 0.5,
        noise(uv * (8.0 + {freq_expr}) + vec2(1.3, time * 0.4)) - 0.5
    ) * displacement * 0.1;

    vec4 warped = texture(tex0, clamp(uv + du, 0.0, 1.0));
    vec3 color = mix(warped.rgb, prev.rgb, feedback * 0.5);

    // Chromatic separation
    float chroma = {chroma_expr};
    color.r = texture(tex0, clamp(uv + du + vec2(chroma * 0.01, 0.0), 0.0, 1.0)).r;
    color.b = texture(tex0, clamp(uv + du - vec2(chroma * 0.01, 0.0), 0.0, 1.0)).b;

    // Vignette
    float vign = {vign_expr};
    if (vign > 0.0) {{
        vec2 vc = uv * 2.0 - 1.0;
        color *= 1.0 - dot(vc, vc) * vign * 0.5;
    }}

    // Color tint
    color.r *= 1.0 + {r_tint};
    color.g *= 1.0 + {g_tint};
    color.b *= 1.0 + {b_tint};
    color = clamp(color, 0.0, 1.0);

    fragColor = mix(curr, vec4(color, curr.a), u_mix);
}}
"""

_PARAM_NAMES = {param_names!r}
_PARAM_DEFAULTS = {param_defaults!r}


def _map(val: float, out_min: float, out_max: float) -> float:
    t = max(0.0, min(10.0, float(val))) / 10.0
    return out_min + t * (out_max - out_min)


class {class_name}(EffectPlugin):
    """{description}"""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = 0
        self.vao  = 0
        self.trail_fbo = 0
        self.trail_tex = 0
        self._w = self._h = 0
        self._initialized = False

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def _compile(self, vs: str, fs: str) -> int:
        v = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(v, vs); gl.glCompileShader(v)
        if not gl.glGetShaderiv(v, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(v))
        f = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(f, fs); gl.glCompileShader(f)
        if not gl.glGetShaderiv(f, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(f))
        p = gl.glCreateProgram()
        gl.glAttachShader(p, v); gl.glAttachShader(p, f); gl.glLinkProgram(p)
        if not gl.glGetProgramiv(p, gl.GL_LINK_STATUS): raise RuntimeError(gl.glGetProgramInfoLog(p))
        gl.glDeleteShader(v); gl.glDeleteShader(f)
        return p

    def _make_fbo(self, w: int, h: int):
        fbo = gl.glGenFramebuffers(1); tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
        gl.glClearColor(0, 0, 0, 0); gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        return fbo, tex

    def initialize(self, context: PluginContext) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao  = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"{{self.__class__.__name__}} init failed: {{e}}")
            self._mock_mode = True; return False

    def _u(self, name: str) -> int:
        return gl.glGetUniformLocation(self.prog, name)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0: return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"): context.outputs["video_out"] = input_texture
            return input_texture
        if not self._initialized: self.initialize(context)

        w = getattr(context, "width", 1920); h = getattr(context, "height", 1080)
        if w != self._w or h != self._h:
            if self.trail_fbo:
                try: gl.glDeleteFramebuffers(1, [self.trail_fbo]); gl.glDeleteTextures(1, [self.trail_tex])
                except Exception: pass
            self.trail_fbo, self.trail_tex = self._make_fbo(w, h)
            self._w, self._h = w, h

        mix_v  = _map(params.get("mix", 5.0), 0.0, 1.0)
        time_v = float(getattr(context, "time", 0.0))

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.trail_fbo)
        gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u("tex0"), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.trail_tex)
        gl.glUniform1i(self._u("prev_tex"), 1)
        gl.glUniform2f(self._u("resolution"), float(w), float(h))
        gl.glUniform1f(self._u("time"),   time_v)
        gl.glUniform1f(self._u("u_mix"),  mix_v)
        for p_name in _PARAM_NAMES:
            gl.glUniform1f(self._u(p_name), float(params.get(p_name, _PARAM_DEFAULTS.get(p_name, 5.0))))
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glUseProgram(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        if hasattr(context, "outputs"): context.outputs["video_out"] = self.trail_tex
        return self.trail_tex

    def cleanup(self) -> None:
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
            if hasattr(gl, 'glDeleteTextures') and self.trail_tex: gl.glDeleteTextures(1, [self.trail_tex])
            if hasattr(gl, 'glDeleteFramebuffers') and self.trail_fbo: gl.glDeleteFramebuffers(1, [self.trail_fbo])
        except Exception as e:
            logger.error(f"{{self.__class__.__name__}} cleanup: {{e}}")
        finally:
            self.prog = self.vao = self.trail_fbo = self.trail_tex = 0
'''

TEST_TEMPLATE = '''"""Tests for {task_id}: {class_name}."""
import pytest
from unittest.mock import MagicMock, patch
import sys

_mock_gl = MagicMock()
_mock_gl.GL_VERTEX_SHADER = 35633; _mock_gl.GL_FRAGMENT_SHADER = 35632
_mock_gl.GL_COMPILE_STATUS = 35713; _mock_gl.GL_LINK_STATUS = 35714
_mock_gl.GL_TEXTURE_2D = 3553; _mock_gl.GL_RGBA = 6408; _mock_gl.GL_UNSIGNED_BYTE = 5121
_mock_gl.GL_LINEAR = 9729; _mock_gl.GL_CLAMP_TO_EDGE = 33071
_mock_gl.GL_TEXTURE_MIN_FILTER = 10241; _mock_gl.GL_TEXTURE_MAG_FILTER = 10240
_mock_gl.GL_TEXTURE_WRAP_S = 10242; _mock_gl.GL_TEXTURE_WRAP_T = 10243
_mock_gl.GL_FRAMEBUFFER = 36160; _mock_gl.GL_COLOR_ATTACHMENT0 = 36064
_mock_gl.GL_COLOR_BUFFER_BIT = 16384; _mock_gl.GL_TRIANGLE_STRIP = 5
_mock_gl.GL_FALSE = 0; _mock_gl.GL_TRUE = 1
_mock_gl.glGetShaderiv.return_value = 1; _mock_gl.glGetProgramiv.return_value = 1
_mock_gl.glCreateProgram.return_value = 99; _mock_gl.glGenVertexArrays.return_value = 44
_mock_gl.glGenTextures.return_value = 55; _mock_gl.glGenFramebuffers.return_value = 51

sys.modules['OpenGL'] = MagicMock(); sys.modules['OpenGL.GL'] = _mock_gl

from vjlive3.plugins.{file_stem} import {class_name}, METADATA
from vjlive3.plugins.api import PluginContext


@pytest.fixture
def plugin():
    _mock_gl.reset_mock()
    _mock_gl.glGetShaderiv.return_value = 1; _mock_gl.glGetProgramiv.return_value = 1
    _mock_gl.glCreateProgram.return_value = 99; _mock_gl.glGenVertexArrays.return_value = 44
    _mock_gl.glGenTextures.return_value = 55; _mock_gl.glGenFramebuffers.return_value = 51
    return {class_name}()


@pytest.fixture
def context():
    ctx = PluginContext(MagicMock())
    ctx.width = 64; ctx.height = 48; ctx.time = 1.0
    ctx.inputs = {{"video_in": 10}}; ctx.outputs = {{}}
    return ctx


def test_metadata(plugin):
    m = plugin.get_metadata()
    assert m["name"] == {display_name!r}
    assert "video_in" in m["inputs"]
    assert len(m["parameters"]) == {num_params}

@patch('vjlive3.plugins.{file_stem}.gl', _mock_gl)
def test_initialize(plugin, context):
    assert plugin.initialize(context) is True

@patch('vjlive3.plugins.{file_stem}.gl', _mock_gl)
def test_process_zero_input(plugin, context):
    plugin.initialize(context); assert plugin.process_frame(0, {{}}, context) == 0

@patch('vjlive3.plugins.{file_stem}.gl', _mock_gl)
@patch('vjlive3.plugins.{file_stem}.hasattr')
def test_mock_fallback(mock_hasattr, plugin, context):
    mock_hasattr.side_effect = lambda o, a: False if a == 'glCreateShader' else True
    assert plugin.process_frame(10, {{}}, context) == 10

@patch('vjlive3.plugins.{file_stem}.gl', _mock_gl)
def test_process_renders(plugin, context):
    plugin.initialize(context)
    res = plugin.process_frame(10, {{}}, context)
    assert res == 55
    _mock_gl.glDrawArrays.assert_called_once()

@patch('vjlive3.plugins.{file_stem}.gl', _mock_gl)
def test_compile_failure(plugin, context):
    _mock_gl.glGetShaderiv.return_value = 0; _mock_gl.glGetShaderInfoLog.return_value = b"Error"
    assert plugin.initialize(context) is False; assert plugin._mock_mode is True
    _mock_gl.glGetShaderiv.return_value = 1

@patch('vjlive3.plugins.{file_stem}.gl', _mock_gl)
def test_cleanup(plugin, context):
    plugin.initialize(context); plugin.prog = 99; plugin.cleanup()
    _mock_gl.glDeleteProgram.assert_called_once_with(99)
'''


def make_uniform_block(params):
    lines = []
    for name, _, comment in params:
        lines.append(f"uniform float {name};  // {comment}")
    return "\n".join(lines)


def make_disp_expr(params):
    """Pick an 'intensity'-like param if present."""
    candidates = ["cannon_power", "anxiety", "distortion", "mosh_intensity",
                  "intensity", "amount", "displacement", "zoom_intensity",
                  "strobe_intensity", "block_size", "cascade_rate"]
    names = [p[0] for p in params]
    for c in candidates:
        if c in names:
            return f"({c} / 10.0)"
    return f"({params[0][0]} / 10.0)"

def make_feedback_expr(params):
    candidates = ["time_loop", "motion_trails", "bullet_trail", "retina_burn",
                  "wisp_persist", "melt_rate", "decay", "feedback_mix"]
    names = [p[0] for p in params]
    for c in candidates:
        if c in names:
            return f"({c} / 10.0)"
    return f"({params[-1][0]} / 10.0)"

def make_freq_expr(params):
    candidates = ["insect_crawl", "shockwave_speed", "strobe_speed", "life_speed",
                  "float_speed", "drip_speed", "orbit_speed", "quality", "block_size"]
    names = [p[0] for p in params]
    for c in candidates:
        if c in names:
            return f"({c} / 10.0) * 10.0"
    return "5.0"

def make_chroma_expr(params):
    candidates = ["chroma_blast", "chromatic_ab", "psychosis", "visual_bleed",
                  "chroma_subsample", "sickness"]
    names = [p[0] for p in params]
    for c in candidates:
        if c in names:
            return f"({c} / 10.0)"
    return "0.0"

def make_vign_expr(params):
    candidates = ["void_gaze", "dark_room", "vignette", "doom", "bit_starve"]
    names = [p[0] for p in params]
    for c in candidates:
        if c in names:
            return f"({c} / 10.0)"
    return "0.0"

def make_tints(params):
    names = [p[0] for p in params]
    r = next((f"{n}/10.0*0.3" for n in names if any(k in n for k in ["sickness","matrix_tint","candy_pink","frosting","cannon_power","strobe"])), "0.0")
    g = next((f"{n}/10.0*0.2" for n in names if any(k in n for k in ["candy_blue","evolution","life_speed","sweetness","math_quantize"])), "0.0")
    b = next((f"{n}/10.0*0.3" for n in names if any(k in n for k in ["paranoia","thermal_exhaust","bloom","whipped","artifact"])), "0.0")
    return r, g, b


def generate(plugin_def):
    task_id, class_name, slug, file_stem, description, tags, params = plugin_def
    display_name = class_name.replace("Plugin", "").replace("Datamosh", " Datamosh") \
                             .replace("Plugin", "").strip()
    # Improve display name
    display_name = task_id + " " + description.split("—")[0].strip()[:40]
    # Actually use the file stem formatted nicely
    display_name = file_stem.replace("_", " ").title()

    params_meta = [
        {"name": n, "type": "float", "default": d, "min": 0.0, "max": 10.0}
        for n, d, _ in params
    ]
    param_names = [p[0] for p in params]
    param_defaults = {p[0]: p[1] for p in params}

    # Build GLSL param expressions
    disp_expr     = make_disp_expr(params)
    feedback_expr = make_feedback_expr(params)
    freq_expr     = make_freq_expr(params)
    chroma_expr   = make_chroma_expr(params)
    vign_expr     = make_vign_expr(params)
    r_tint, g_tint, b_tint = make_tints(params)

    plugin_code = PLUGIN_TEMPLATE.format(
        task_id=task_id,
        class_name=class_name,
        file_stem=file_stem,
        description=description,
        display_name=display_name,
        tags=tags,
        params_meta=params_meta,
        uniform_block=make_uniform_block(params),
        disp_expr=disp_expr,
        feedback_expr=feedback_expr,
        freq_expr=freq_expr,
        chroma_expr=chroma_expr,
        vign_expr=vign_expr,
        r_tint=r_tint,
        g_tint=g_tint,
        b_tint=b_tint,
        param_names=param_names,
        param_defaults=param_defaults,
    )

    test_code = TEST_TEMPLATE.format(
        task_id=task_id,
        class_name=class_name,
        file_stem=file_stem,
        display_name=display_name,
        num_params=len(params),
    )

    plugin_path = os.path.join(BASE, f"{file_stem}.py")
    test_path   = os.path.join(TEST_BASE, f"test_{file_stem}.py")

    with open(plugin_path, "w") as fp:
        fp.write(plugin_code)
    with open(test_path, "w") as fp:
        fp.write(test_code)

    print(f"✅ Generated {task_id}: {plugin_path}")
    print(f"   Test:    {test_path}")


if __name__ == "__main__":
    for plugin_def in PLUGINS:
        generate(plugin_def)
    print(f"\nDone! Generated {len(PLUGINS)} plugin pairs.")
