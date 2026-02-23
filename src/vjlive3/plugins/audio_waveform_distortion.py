"""
P4-AU03: Audio Waveform Distortion Plugin for VJLive3.
Ported from VJlive-2/plugins/vaudio_reactive/audio_reactive_effects.py::AudioWaveformDistortion.

Applies horizontal + vertical UV warping driven by the audio waveform.
Waveform is uploaded as a 1D GL_R32F texture each frame.
Bass and volume modulate distortion depth and chromatic color shifting.
"""

from typing import Dict, Any, Optional
import numpy as np
import logging

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from .api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

METADATA = {
    "name": "Audio Waveform Distortion",
    "description": "Screen warping driven by real-time audio waveform data.",
    "version": "1.0.0",
    "plugin_type": "audio_effect",
    "category": "distort",
    "tags": ["audio", "waveform", "glitch", "distortion", "wave", "reactive"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "distortion_strength", "type": "float", "default": 1.0, "min": 0.0, "max": 10.0},
        {"name": "frequency_scale",     "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "smoothing",           "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
        {"name": "color_shift",         "type": "float", "default": 1.0, "min": 0.0, "max": 10.0},
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
uniform sampler2D waveform_tex;

uniform float distortion_strength;
uniform float frequency_scale;
uniform float color_shift;
uniform int   waveform_size;
uniform float bass_level;
uniform float volume_level;
uniform float time;
uniform float u_mix;

void main() {
    // Sample waveform at current vertical position
    float waveform_value = 0.0;
    if (waveform_size > 0) {
        float wave_pos = uv.y * float(waveform_size);
        int   sample_idx = int(wave_pos);
        float frac = fract(wave_pos);
        float v1 = texelFetch(waveform_tex, ivec2(sample_idx, 0), 0).r;
        int   next_idx = min(sample_idx + 1, waveform_size - 1);
        float v2 = texelFetch(waveform_tex, ivec2(next_idx, 0), 0).r;
        waveform_value = mix(v1, v2, frac);
    }

    float distortion = waveform_value * distortion_strength * volume_level;
    vec2 dist_uv = uv;

    dist_uv.x += sin(uv.y * frequency_scale * 10.0 + time * 2.0) * distortion;
    dist_uv.y += cos(uv.x * frequency_scale *  8.0 + time * 1.5) * distortion * 0.5;
    dist_uv = clamp(dist_uv, 0.0, 1.0);

    vec4 distorted = texture(tex0, dist_uv);
    vec3 color = distorted.rgb;

    // Chromatic shift driven by bass
    color.r += sin(time * bass_level * 5.0) * color_shift * volume_level;
    color.b += cos(time * bass_level * 3.0) * color_shift * volume_level;

    // Mix distorted vs original
    fragColor = mix(texture(tex0, uv), vec4(color, distorted.a), u_mix);
}
"""


def _map(val: float, out_min: float, out_max: float) -> float:
    t = max(0.0, min(10.0, float(val))) / 10.0
    return out_min + t * (out_max - out_min)


class AudioWaveformDistortionPlugin(EffectPlugin):
    """Audio Waveform Distortion — real-time waveform uploads drive UV warping."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = 0
        self.vao  = 0
        self.wave_tex: int = 0
        self._wave_len: int = 0
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

    def _make_wave_tex(self) -> int:
        tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        return tex

    def initialize(self, context: PluginContext) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True
            return True
        try:
            self.prog     = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao      = gl.glGenVertexArrays(1)
            self.wave_tex = self._make_wave_tex()
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"AudioWaveformDistortion init failed: {e}")
            self._mock_mode = True
            return False

    def _upload_waveform(self, waveform: np.ndarray) -> None:
        """Upload float32 waveform as 1D texture (GL_R32F, single row)."""
        data = waveform.astype(np.float32)
        n = len(data)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.wave_tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_R32F, n, 1, 0,
                        gl.GL_RED, gl.GL_FLOAT, data)
        self._wave_len = n

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

        # ── Remap params ──────────────────────────────────────────────────
        dist   = _map(params.get("distortion_strength", 1.0), 0.0, 0.5)
        freq   = _map(params.get("frequency_scale",     5.0), 0.1, 5.0)
        c_sh   = _map(params.get("color_shift",         1.0), 0.0, 1.0)
        mix_v  = _map(params.get("mix",                 5.0), 0.0, 1.0)

        # ── Audio data ────────────────────────────────────────────────────
        inputs = getattr(context, "inputs", {})
        audio  = inputs.get("audio_data", {})
        if not isinstance(audio, dict):
            audio = {}

        bass    = float(audio.get("bass",   0.0))
        volume  = float(audio.get("volume", 0.0))
        waveform = audio.get("waveform", None)
        time_v   = float(getattr(context, "time", 0.0))
        w = getattr(context, "width",  1920)
        h = getattr(context, "height", 1080)

        # ── Waveform texture upload ───────────────────────────────────────
        if waveform is not None and len(waveform) > 0:
            wave_arr = np.asarray(waveform, dtype=np.float32)
            self._upload_waveform(wave_arr)
        else:
            self._wave_len = 0

        # ── Render FSQ ────────────────────────────────────────────────────
        gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.prog)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u("tex0"), 0)

        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.wave_tex)
        gl.glUniform1i(self._u("waveform_tex"), 1)

        gl.glUniform1f(self._u("distortion_strength"), dist)
        gl.glUniform1f(self._u("frequency_scale"),     freq)
        gl.glUniform1f(self._u("color_shift"),         c_sh)
        gl.glUniform1i(self._u("waveform_size"),       self._wave_len)
        gl.glUniform1f(self._u("bass_level"),          bass)
        gl.glUniform1f(self._u("volume_level"),        volume)
        gl.glUniform1f(self._u("time"),                time_v)
        gl.glUniform1f(self._u("u_mix"),               mix_v)

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
            if hasattr(gl, 'glDeleteTextures') and self.wave_tex:
                gl.glDeleteTextures(1, [self.wave_tex])
        except Exception as e:
            logger.error(f"AudioWaveformDistortion cleanup: {e}")
        finally:
            self.prog = self.vao = self.wave_tex = 0
