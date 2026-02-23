"""
P4-AU05: Audio Kaleidoscope Plugin for VJLive3.
Ported from VJlive-2/plugins/vaudio_reactive/audio_reactive_effects.py::AudioKaleidoscope.

Kaleidoscope segmentation driven by audio. Bass triggers beat-reactive brightness.
Mid and treble modulate scale and mirror. All computation in fragment shader — zero CPU work.
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

METADATA = {
    "name": "Audio Kaleidoscope",
    "description": "Audio-reactive kaleidoscope segments with beat-driven brightness pulse.",
    "version": "1.0.0",
    "plugin_type": "audio_effect",
    "category": "geometry",
    "tags": ["audio", "kaleidoscope", "mirror", "psychedelic", "reactive", "beat"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "segments",         "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "angle_offset",     "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "scale",            "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "rotation_speed",   "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "mirror_effect",    "type": "float", "default": 10.0,"min": 0.0, "max": 10.0},
        {"name": "audio_sensitivity","type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
    ]
}

VERTEX_SHADER = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1), vec2(1,-1), vec2(-1,1), vec2(1,1));
out vec2 uv;
void main() {
    gl_Position = vec4(verts[gl_VertexID], 0.0, 1.0);
    uv = verts[gl_VertexID] * 0.5 + 0.5;
}
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform float time;
uniform float u_mix;
uniform int   segments;
uniform float angle_offset;
uniform float scale;
uniform float rotation_speed;
uniform float mirror_effect;
uniform float audio_sensitivity;
uniform float bass_level;
uniform float mid_level;
uniform float treble_level;
uniform float beat_phase;
uniform float beat_confidence;

const float PI = 3.14159265358979;

vec2 kaleidoscope(vec2 p) {
    float radius = length(p - 0.5);
    float angle  = atan(p.y - 0.5, p.x - 0.5);
    float rot = time * rotation_speed + angle_offset + bass_level * audio_sensitivity * 2.0;
    angle += rot;
    float seg_angle = (2.0 * PI) / float(segments);
    float seg_idx   = floor(angle / seg_angle);
    float local     = mod(angle - seg_idx * seg_angle, seg_angle);
    if (mod(seg_idx, 2.0) > 0.5) local = seg_angle - local;
    float audio_scale = scale * (1.0 + mid_level * audio_sensitivity * 0.5);
    radius *= audio_scale;
    float x = 0.5 + cos(local + seg_idx * seg_angle - rot) * radius;
    float y = 0.5 + sin(local + seg_idx * seg_angle - rot) * radius;
    return vec2(x, y);
}

void main() {
    vec2 k_uv = kaleidoscope(uv);

    if (mirror_effect > 0.0) {
        vec2 mirror_uv = k_uv;
        if (k_uv.x > 0.5) mirror_uv.x = 0.5 - (k_uv.x - 0.5);
        k_uv = mix(k_uv, mirror_uv, mirror_effect * treble_level);
    }

    vec4 k_color = texture(tex0, clamp(k_uv, 0.0, 1.0));
    vec3 color = k_color.rgb;

    // Beat pulse
    float pulse = pow(max(1.0 - beat_phase, 0.0), 4.0);
    color *= 1.0 + pulse * audio_sensitivity * 0.5 * beat_confidence;

    color.r *= (1.0 + bass_level   * audio_sensitivity * 0.3);
    color.g *= (1.0 + mid_level    * audio_sensitivity * 0.3);
    color.b *= (1.0 + treble_level * audio_sensitivity * 0.3);

    fragColor = mix(texture(tex0, uv), vec4(color, k_color.a), u_mix);
}
"""


def _map(val: float, out_min: float, out_max: float) -> float:
    t = max(0.0, min(10.0, float(val))) / 10.0
    return out_min + t * (out_max - out_min)


class AudioKaleidoscopePlugin(EffectPlugin):
    """Pure-shader audio kaleidoscope — no CPU work each frame."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = 0
        self.vao  = 0
        self._initialized = False

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def _compile(self, vs: str, fs: str) -> int:
        v = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(v, vs)
        gl.glCompileShader(v)
        if not gl.glGetShaderiv(v, gl.GL_COMPILE_STATUS):
            raise RuntimeError(gl.glGetShaderInfoLog(v))
        f = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(f, fs)
        gl.glCompileShader(f)
        if not gl.glGetShaderiv(f, gl.GL_COMPILE_STATUS):
            raise RuntimeError(gl.glGetShaderInfoLog(f))
        p = gl.glCreateProgram()
        gl.glAttachShader(p, v)
        gl.glAttachShader(p, f)
        gl.glLinkProgram(p)
        if not gl.glGetProgramiv(p, gl.GL_LINK_STATUS):
            raise RuntimeError(gl.glGetProgramInfoLog(p))
        gl.glDeleteShader(v)
        gl.glDeleteShader(f)
        return p

    def initialize(self, context: PluginContext) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True
            return True
        try:
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao  = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"AudioKaleidoscope init failed: {e}")
            self._mock_mode = True
            return False

    def _u(self, name: str) -> int:
        return gl.glGetUniformLocation(self.prog, name)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
            return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
        if not self._initialized:
            self.initialize(context)

        import math
        segs    = int(_map(params.get("segments",          3.0), 3, 32))
        ang_off = _map(params.get("angle_offset",          0.0), 0.0, math.pi * 2)
        scl     = _map(params.get("scale",                 5.0), 0.1, 3.0)
        rot_spd = _map(params.get("rotation_speed",        5.0), -5.0, 5.0)
        mirror  = _map(params.get("mirror_effect",        10.0), 0.0, 1.0)
        sens    = _map(params.get("audio_sensitivity",     5.0), 0.1, 3.0)
        mix_v   = _map(params.get("mix",                   5.0), 0.0, 1.0)

        inputs  = getattr(context, "inputs", {})
        audio   = inputs.get("audio_data", {})
        if not isinstance(audio, dict):
            audio = {}

        bass       = float(audio.get("bass",             0.0))
        mid        = float(audio.get("mid",              0.0))
        treble     = float(audio.get("treble",           0.0))
        beat_phase = float(audio.get("beat_phase",      0.0))
        beat_conf  = float(audio.get("beat_confidence", 0.0))
        time_v     = float(getattr(context, "time", 0.0))
        w = getattr(context, "width",  1920)
        h = getattr(context, "height", 1080)

        gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u("tex0"), 0)

        gl.glUniform1f(self._u("time"),             time_v)
        gl.glUniform1f(self._u("u_mix"),            mix_v)
        gl.glUniform1i(self._u("segments"),         segs)
        gl.glUniform1f(self._u("angle_offset"),     ang_off)
        gl.glUniform1f(self._u("scale"),            scl)
        gl.glUniform1f(self._u("rotation_speed"),   rot_spd)
        gl.glUniform1f(self._u("mirror_effect"),    mirror)
        gl.glUniform1f(self._u("audio_sensitivity"),sens)
        gl.glUniform1f(self._u("bass_level"),       bass)
        gl.glUniform1f(self._u("mid_level"),        mid)
        gl.glUniform1f(self._u("treble_level"),     treble)
        gl.glUniform1f(self._u("beat_phase"),       beat_phase)
        gl.glUniform1f(self._u("beat_confidence"),  beat_conf)

        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glUseProgram(0)

        if hasattr(context, "outputs"):
            context.outputs["video_out"] = input_texture
        return input_texture

    def cleanup(self) -> None:
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog:
                gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao:
                gl.glDeleteVertexArrays(1, [self.vao])
        except Exception as e:
            logger.error(f"AudioKaleidoscope cleanup: {e}")
        finally:
            self.prog = self.vao = 0
