"""
P3-EXT002: Adaptive Contrast Effect — Auto-leveling with local contrast stretching.

Adaptive contrast stretching with local detail enhancement, inspired by
Mutable Instruments Streams audio dynamics processor. Analyzes local
neighborhoods to automatically stretch luminance, revealing detail in both
dark and bright areas simultaneously.

Ported from VJLive-2: core/effects/video_effects.py (AdaptiveContrastEffect)
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
    "name": "Adaptive Contrast",
    "description": "Auto-leveling with local contrast stretching — audio dynamics for video.",
    "version": "1.0.0",
    "plugin_type": "effect",
    "category": "color",
    "tags": ["contrast", "adaptive", "dynamics", "auto-level", "hdr", "color"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "strength",    "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "locality",    "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "black_point", "type": "float", "default": 1.0, "min": 0.0, "max": 10.0},
        {"name": "white_point", "type": "float", "default": 9.0, "min": 0.0, "max": 10.0},
        {"name": "saturation",  "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "detail",      "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "mix",         "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
    ],
}

VERTEX_SHADER = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1), vec2(1,-1), vec2(-1,1), vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(verts[gl_VertexID], 0.0, 1.0); uv = verts[gl_VertexID]*0.5+0.5; }
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

uniform float strength;
uniform float locality;
uniform float black_point;
uniform float white_point;
uniform float saturation;
uniform float detail;

void main() {
    // Remap parameters
    float str = strength / 10.0;
    float rad = 1.0 + locality / 10.0 * 20.0;   // 1-21 pixel radius
    float bp  = black_point / 10.0 * 0.3;         // 0-0.3
    float wp  = 0.7 + white_point / 10.0 * 0.3;  // 0.7-1.0
    float sat = 0.5 + saturation / 10.0 * 1.5;   // 0.5-2.0
    float det = detail / 10.0 * 2.0;              // 0-2.0

    vec2 px = rad / 3.0 / resolution;

    // 7x7 local neighbourhood sample
    float localMin =  1.0;
    float localMax = -1.0;
    float localAvg =  0.0;
    float samples  =  0.0;
    for (float dx = -3.0; dx <= 3.0; dx += 1.0) {
        for (float dy = -3.0; dy <= 3.0; dy += 1.0) {
            vec3 s = texture(tex0, uv + vec2(dx, dy) * px).rgb;
            float l = dot(s, vec3(0.299, 0.587, 0.114));
            localMin = min(localMin, l);
            localMax = max(localMax, l);
            localAvg += l;
            samples += 1.0;
        }
    }
    localAvg /= samples;

    vec4 src = texture(tex0, uv);
    float lum = dot(src.rgb, vec3(0.299, 0.587, 0.114));

    // Adaptive stretch
    float normalized  = (lum - localMin) / max(0.01, localMax - localMin);
    float adaptedLum  = bp + normalized * (wp - bp);
    float finalLum    = mix(lum, adaptedLum, str);
    // Local detail boost
    finalLum += (lum - localAvg) * det;
    finalLum = clamp(finalLum, 0.0, 1.0);

    // Apply luminance ratio to color
    float ratio = finalLum / max(0.001, lum);
    vec3 result = src.rgb * ratio;

    // Saturation
    float newLum = dot(result, vec3(0.299, 0.587, 0.114));
    result = mix(vec3(newLum), result, sat);
    result = clamp(result, 0.0, 1.0);

    fragColor = mix(src, vec4(result, src.a), u_mix);
}
"""

_PARAM_NAMES = ["strength", "locality", "black_point", "white_point", "saturation", "detail"]
_PARAM_DEFAULTS = {"strength": 5.0, "locality": 5.0, "black_point": 1.0,
                   "white_point": 9.0, "saturation": 5.0, "detail": 3.0}

PRESETS = {
    "auto_level":    {"strength": 8.0, "locality": 9.0, "black_point": 0.0, "white_point": 10.0, "saturation": 5.0, "detail": 2.0},
    "hdr_detail":    {"strength": 7.0, "locality": 4.0, "black_point": 1.0, "white_point": 9.0,  "saturation": 6.0, "detail": 6.0},
    "flat_grade":    {"strength": 4.0, "locality": 8.0, "black_point": 2.0, "white_point": 8.0,  "saturation": 4.0, "detail": 1.0},
    "punchy":        {"strength": 7.0, "locality": 3.0, "black_point": 0.0, "white_point": 10.0, "saturation": 8.0, "detail": 5.0},
    "cinema_grade":  {"strength": 5.0, "locality": 7.0, "black_point": 1.5, "white_point": 8.5,  "saturation": 4.5, "detail": 3.0},
}


def _map(val, lo, hi): return lo + (max(0., min(10., float(val))) / 10.) * (hi - lo)


class AdaptiveContrastPlugin(EffectPlugin):
    """Adaptive contrast effect — local luminance stretching with detail enhancement."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = self.vao = 0
        self.trail_fbo = self.trail_tex = 0
        self._w = self._h = 0
        self._initialized = False

    def get_metadata(self): return METADATA

    def _compile(self, vs, fs):
        v = gl.glCreateShader(gl.GL_VERTEX_SHADER); gl.glShaderSource(v, vs); gl.glCompileShader(v)
        if not gl.glGetShaderiv(v, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(v))
        f = gl.glCreateShader(gl.GL_FRAGMENT_SHADER); gl.glShaderSource(f, fs); gl.glCompileShader(f)
        if not gl.glGetShaderiv(f, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(f))
        p = gl.glCreateProgram(); gl.glAttachShader(p, v); gl.glAttachShader(p, f); gl.glLinkProgram(p)
        if not gl.glGetProgramiv(p, gl.GL_LINK_STATUS): raise RuntimeError(gl.glGetProgramInfoLog(p))
        gl.glDeleteShader(v); gl.glDeleteShader(f); return p

    def _make_fbo(self, w, h):
        fbo = gl.glGenFramebuffers(1); tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        for k, v2 in [(gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR), (gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR),
                      (gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE), (gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)]:
            gl.glTexParameteri(gl.GL_TEXTURE_2D, k, v2)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
        gl.glClearColor(0, 0, 0, 0); gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0); return fbo, tex

    def initialize(self, context):
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"AdaptiveContrastPlugin init: {e}"); self._mock_mode = True; return False

    def _u(self, n): return gl.glGetUniformLocation(self.prog, n)

    def process_frame(self, input_texture, params, context):
        if not input_texture or input_texture <= 0: return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
            return input_texture
        if not self._initialized: self.initialize(context)
        w = getattr(context, 'width', 1920); h = getattr(context, 'height', 1080)
        if w != self._w or h != self._h:
            if self.trail_fbo:
                try: gl.glDeleteFramebuffers(1, [self.trail_fbo]); gl.glDeleteTextures(1, [self.trail_tex])
                except Exception: pass
            self.trail_fbo, self.trail_tex = self._make_fbo(w, h); self._w, self._h = w, h
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.trail_fbo); gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u('tex0'), 0)
        gl.glUniform2f(self._u('resolution'), float(w), float(h))
        gl.glUniform1f(self._u('time'), float(getattr(context, 'time', 0.)))
        gl.glUniform1f(self._u('u_mix'), _map(params.get('mix', 8.), 0., 1.))
        for p in _PARAM_NAMES:
            gl.glUniform1f(self._u(p), float(params.get(p, _PARAM_DEFAULTS.get(p, 5.))))
        gl.glBindVertexArray(self.vao); gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0); gl.glUseProgram(0); gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        if hasattr(context, 'outputs'): context.outputs['video_out'] = self.trail_tex
        return self.trail_tex

    def cleanup(self):
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
            if hasattr(gl, 'glDeleteTextures') and self.trail_tex: gl.glDeleteTextures(1, [self.trail_tex])
            if hasattr(gl, 'glDeleteFramebuffers') and self.trail_fbo: gl.glDeleteFramebuffers(1, [self.trail_fbo])
        except Exception as e: logger.error(f"AdaptiveContrastPlugin cleanup: {e}")
        finally: self.prog = self.vao = self.trail_fbo = self.trail_tex = 0
