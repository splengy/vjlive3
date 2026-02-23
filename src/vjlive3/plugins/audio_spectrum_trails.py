"""
P3-EXT010: AudioSpectrumTrails — Persistent spectrum bars overlay with audio-reactive trails.

Renders frequency bands at the bottom of screen with 3 color modes (rainbow/grayscale/blue-orange)
and bass glow. Trail effect via audio analyzer temporal smoothing.

Ported from VJLive-2: plugins/core/audio_reactive/audio_reactive.py (lines 290-404)
"""
import logging
try:
    import numpy as np
    HAS_NP = True
except ImportError:
    HAS_NP = False
try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
from .api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

METADATA = {
    "name": "Audio Spectrum Trails",
    "description": "Spectrum bars overlay at the bottom of screen — 3 color modes, bass glow, configurable bands and decay.",
    "version": "2.0.0",
    "plugin_type": "effect",
    "category": "audio-reactive",
    "tags": ["spectrum", "audio-reactive", "overlay", "visualization"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "trail_decay",      "type": "float", "default": 7.5, "min": 0.0, "max": 10.0},
        {"name": "spectrum_height",  "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "frequency_bands",  "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "color_mode",       "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "trail_opacity",    "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
        {"name": "mix",              "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
    ],
}

VERTEX_SHADER = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1),vec2(1,-1),vec2(-1,1),vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(verts[gl_VertexID],0.0,1.0); uv=verts[gl_VertexID]*0.5+0.5; }
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv; out vec4 fragColor;
uniform sampler2D tex0;
uniform sampler2D spectrum_tex;
uniform vec2  resolution;
uniform float u_mix;
uniform float trail_decay;
uniform float spectrum_height;
uniform int   frequency_bands;
uniform int   color_mode;
uniform float trail_opacity;
uniform int   spectrum_size;
uniform float bass_level;
uniform float volume_level;

vec3 get_spectrum_color(float freq, float intensity) {
    if (color_mode == 0) {
        return vec3(sin(freq*3.0)*0.5+0.5,
                    sin(freq*3.0+2.09)*0.5+0.5,
                    sin(freq*3.0+4.18)*0.5+0.5) * intensity;
    } else if (color_mode == 1) {
        return vec3(intensity);
    } else {
        return vec3(freq, 1.0-freq, intensity*0.5);
    }
}

void main() {
    vec4 original = texture(tex0, uv);
    vec3 color = original.rgb;

    if (uv.y < spectrum_height) {
        float band_pos = uv.x * float(frequency_bands);
        int band_idx = int(band_pos);
        float spectrum_value = 0.0;
        if (spectrum_size > 0 && band_idx < frequency_bands) {
            float sp = float(band_idx) / float(frequency_bands) * float(spectrum_size);
            int si = int(sp);
            if (si < spectrum_size) {
                spectrum_value = texelFetch(spectrum_tex, ivec2(si, 0), 0).r;
            }
        }
        spectrum_value *= volume_level * 2.0;
        float trail_height = spectrum_value * spectrum_height;
        if (uv.y < trail_height) {
            float freq = float(band_idx) / float(frequency_bands);
            vec3 sc = get_spectrum_color(freq, 1.0);
            color = mix(color, sc, trail_opacity * u_mix);
        }
        float bass_glow = bass_level * 0.3 * (1.0 - uv.y / spectrum_height);
        color += vec3(bass_glow, bass_glow*0.5, bass_glow*0.2) * u_mix;
    }

    fragColor = vec4(color, original.a);
}
"""

PRESETS = {
    "spectrum_default":   {"trail_decay": 7.5, "spectrum_height": 5.0, "frequency_bands": 5.0, "color_mode": 0.0, "trail_opacity": 8.0},
    "spectrum_tall":      {"spectrum_height": 9.0, "trail_opacity": 9.0, "color_mode": 0.0},
    "spectrum_wide":      {"frequency_bands": 9.0, "trail_decay": 5.0},
    "spectrum_subtle":    {"trail_opacity": 3.0, "spectrum_height": 3.0, "color_mode": 3.5},
    "spectrum_aggressive":{"trail_decay": 2.0, "spectrum_height": 8.0, "color_mode": 7.0},
}

# Param mappings
def _trail_decay(v): return 0.8 + (v/10.)*0.19
def _spec_height(v): return 0.1 + (v/10.)*0.9
def _freq_bands(v):  return int(16 + (v/10.)*240)
def _color_mode(v):  return int(min(2, int(v/10.*2.)))
def _opacity(v):     return 0.1 + (v/10.)*0.9
def _c(v):           return max(0., min(10., float(v)))


class AudioSpectrumTrailsPlugin(EffectPlugin):
    """Audio spectrum bars overlay with 3 color modes and bass glow."""

    def __init__(self):
        super().__init__()
        self._mock_mode   = not HAS_GL
        self.prog = self.vao = 0
        self.spec_tex = 0
        self._initialized = False
        # Internal audio state
        self._bass  = 0.0
        self._volume = 0.0
        self._spectrum: list = [0.0] * 512

    def get_metadata(self): return METADATA

    def _compile(self, vs, fs):
        v = gl.glCreateShader(gl.GL_VERTEX_SHADER);  gl.glShaderSource(v, vs); gl.glCompileShader(v)
        if not gl.glGetShaderiv(v, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(v))
        f = gl.glCreateShader(gl.GL_FRAGMENT_SHADER); gl.glShaderSource(f, fs); gl.glCompileShader(f)
        if not gl.glGetShaderiv(f, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(f))
        p = gl.glCreateProgram(); gl.glAttachShader(p, v); gl.glAttachShader(p, f); gl.glLinkProgram(p)
        if not gl.glGetProgramiv(p, gl.GL_LINK_STATUS): raise RuntimeError(gl.glGetProgramInfoLog(p))
        gl.glDeleteShader(v); gl.glDeleteShader(f); return p

    def _u(self, n): return gl.glGetUniformLocation(self.prog, n)

    def initialize(self, context):
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog     = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao      = gl.glGenVertexArrays(1)
            # Create spectrum texture
            self.spec_tex = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.spec_tex)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            try:
                import numpy as _np
                data = _np.zeros(512, dtype=_np.float32)
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_R32F, 512, 1, 0, gl.GL_RED, gl.GL_FLOAT, data)
            except Exception:
                pass
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"AudioSpectrumTrailsPlugin init: {e}"); self._mock_mode = True; return False

    def update_audio(self, audio: dict) -> None:
        self._bass   = float(audio.get('bass', 0.))
        self._volume = float(audio.get('volume', audio.get('rms', 0.5)))
        if 'spectrum' in audio:
            sp = list(audio['spectrum'])
            self._spectrum = sp[:512] + [0.0] * max(0, 512-len(sp))

    def process_frame(self, input_texture, params, context):
        if not input_texture or input_texture <= 0: return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
            return input_texture
        if not self._initialized: self.initialize(context)
        w = float(getattr(context, 'width', 1920)); h = float(getattr(context, 'height', 1080))
        td   = _trail_decay(_c(params.get('trail_decay', 7.5)))
        sh   = _spec_height(_c(params.get('spectrum_height', 5.0)))
        fb   = _freq_bands(_c(params.get('frequency_bands', 5.0)))
        cm   = _color_mode(_c(params.get('color_mode', 0.0)))
        op   = _opacity(_c(params.get('trail_opacity', 8.0)))
        u_mix= _c(params.get('mix', 8.0)) / 10.

        # Upload spectrum texture
        if self.spec_tex and HAS_NP:
            import numpy as _np
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.spec_tex)
            data = _np.array(self._spectrum[:512], dtype=_np.float32)
            gl.glTexSubImage2D(gl.GL_TEXTURE_2D, 0, 0, 0, 512, 1, gl.GL_RED, gl.GL_FLOAT, data)

        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u('tex0'), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1); gl.glBindTexture(gl.GL_TEXTURE_2D, self.spec_tex)
        gl.glUniform1i(self._u('spectrum_tex'), 1)
        gl.glUniform2f(self._u('resolution'), w, h)
        gl.glUniform1f(self._u('u_mix'), u_mix)
        gl.glUniform1f(self._u('trail_decay'), td)
        gl.glUniform1f(self._u('spectrum_height'), sh)
        gl.glUniform1i(self._u('frequency_bands'), fb)
        gl.glUniform1i(self._u('color_mode'), cm)
        gl.glUniform1f(self._u('trail_opacity'), op)
        gl.glUniform1i(self._u('spectrum_size'), 512)
        gl.glUniform1f(self._u('bass_level'), self._bass)
        gl.glUniform1f(self._u('volume_level'), max(0.1, self._volume))
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0); gl.glUseProgram(0)
        if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
        return input_texture

    def cleanup(self):
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
            if hasattr(gl, 'glDeleteTextures') and self.spec_tex: gl.glDeleteTextures(1, [self.spec_tex])
        except Exception as e: logger.error(f"AudioSpectrumTrailsPlugin cleanup: {e}")
        finally: self.prog = self.vao = self.spec_tex = 0
