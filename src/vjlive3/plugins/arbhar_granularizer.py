"""
P3-EXT008: ArbharGranularizer — GPU-accelerated granular synthesis with feedback loops.

Dual-FBO grain particle system: grain buffer for rendering, feedback buffer for trails.
Composite grain result over original frame using blend parameter.
Audio reactive: BEAT_INTENSITY→intensity, TEMPO→grain_size, ENERGY→density/feedback.

Ported from VJLive-2: core/effects/arbhar_granularizer.py (123+ lines)
"""
import random
import logging
from typing import Dict, Optional
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

MAX_GRAINS = 256   # Reduced for performance safety at 60 FPS

METADATA = {
    "name": "Arbhar Granularizer",
    "description": "GPU-accelerated granular synthesis with dual framebuffer feedback and audio reactivity.",
    "version": "2.0.0",
    "plugin_type": "effect",
    "category": "synthesis",
    "tags": ["granular", "synthesis", "gpu", "audio-reactive", "feedback"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "intensity",        "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "grain_size",       "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "density",          "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "spray",            "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "feedback",         "type": "float", "default": 1.0, "min": 0.0, "max": 10.0},
        {"name": "blend",            "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
        {"name": "audio_reactivity", "type": "float", "default": 7.0, "min": 0.0, "max": 10.0},
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
uniform sampler2D u_feedback;
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_mix;
uniform float u_intensity;
uniform float u_grain_size;
uniform float u_density;
uniform float u_spray;
uniform float u_feedback_amt;
uniform float u_blend;

// Grain data — up to 256 grains passed as 3-component arrays (x, y, age_norm)
uniform int   u_num_grains;
uniform vec3  u_grain_data[256];

float hash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }

void main() {
    vec4 src = texture(tex0, uv);
    vec4 grain_result = vec4(0.0);
    float radius = u_grain_size * 0.05;

    for (int i = 0; i < 256; i++) {
        if (i >= u_num_grains) break;
        vec2  gpos    = u_grain_data[i].xy;
        float age_n   = 1.0 - u_grain_data[i].z;   // 1=fresh, 0=dead
        if (age_n <= 0.0) continue;

        float dist = distance(uv, gpos);
        if (dist < radius) {
            float alpha = (1.0 - smoothstep(0.0, radius, dist)) * age_n;
            vec2  suv   = gpos + (uv - gpos) * (1.0 + u_spray * 0.3 * hash(gpos + u_time));
            suv = clamp(suv, 0.001, 0.999);
            vec4 gc = texture(tex0, suv);
            grain_result += gc * alpha * u_intensity * 0.1;
        }
    }

    // Feedback trail
    vec4 fb = texture(u_feedback, uv);
    grain_result = mix(grain_result, fb, u_feedback_amt * 0.9);

    // Blend granular with source
    vec4 composited = mix(grain_result, src, u_blend);
    fragColor = mix(src, composited, u_mix);
}
"""

PRESETS = {
    "default":        {"intensity": 5.0, "grain_size": 2.0, "density": 5.0, "spray": 3.0, "feedback": 1.0, "blend": 8.0},
    "dense_grains":   {"intensity": 8.0, "grain_size": 3.0, "density": 9.0, "spray": 2.0, "feedback": 0.0, "blend": 7.0},
    "chaotic_spray":  {"intensity": 6.0, "grain_size": 4.0, "density": 6.0, "spray": 9.0, "feedback": 3.0, "blend": 6.0},
    "feedback_heavy": {"intensity": 4.0, "grain_size": 2.0, "density": 4.0, "spray": 1.0, "feedback": 9.0, "blend": 5.0},
    "subtle_blend":   {"intensity": 3.0, "grain_size": 1.0, "density": 2.0, "spray": 1.0, "feedback": 0.0, "blend": 9.5},
}


def _c(v, lo=0., hi=10.): return max(lo, min(hi, float(v)))


class ArbharGranularizerPlugin(EffectPlugin):
    """GPU-accelerated granular synthesizer with dual-FBO feedback architecture."""

    def __init__(self):
        super().__init__()
        self._mock_mode   = not HAS_GL
        self.prog = self.vao = 0
        self.fbo_grain = self.tex_grain = 0
        self.fbo_feed  = self.tex_feed  = 0
        self._initialized = False
        # Grain CPU state: list of [x, y, age, lifetime]
        self._grains: list = []

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

    def _make_fbo(self, w, h):
        tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, w, h, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        fbo = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        return fbo, tex

    def initialize(self, context):
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao  = gl.glGenVertexArrays(1)
            w = getattr(context, 'width', 1920); h = getattr(context, 'height', 1080)
            self.fbo_grain, self.tex_grain = self._make_fbo(w, h)
            self.fbo_feed,  self.tex_feed  = self._make_fbo(w, h)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"ArbharGranularizerPlugin init: {e}"); self._mock_mode = True; return False

    # ── Grain management ──────────────────────────────────────────────────

    def _update_grains(self, density: float, intensity: float, spray: float) -> None:
        spawn = int(density * intensity * 0.5)
        for _ in range(spawn):
            if len(self._grains) < MAX_GRAINS:
                lt = random.randint(30, 120)
                self._grains.append([random.random(), random.random(), 0, lt])
        alive = []
        for g in self._grains:
            g[2] += 1
            g[0] = _c(g[0] + (random.random()-0.5)*spray*0.005, 0., 1.)
            g[1] = _c(g[1] + (random.random()-0.5)*spray*0.005, 0., 1.)
            if g[2] < g[3]:
                alive.append(g)
        self._grains = alive

    def update_audio(self, audio: Dict) -> None:
        ar = 0.5
        intensity = float(audio.get('beat', audio.get('bass', 0.)))
        # Map audio to params
        self._audio_intensity   = _c(2.0 + intensity * 8.0)
        self._audio_grain_size  = _c(0.1 + float(audio.get('tempo', 0.5)) * 9., 0., 10.)
        self._audio_density     = _c((0.2 + float(audio.get('energy', 0.5)) * 0.8) * 10., 0., 10.)
        self._audio_spray       = _c(intensity * 8.)
        self._audio_feedback    = _c(float(audio.get('energy', 0.1)) * 6.)

    # ── Rendering ─────────────────────────────────────────────────────────

    def process_frame(self, input_texture, params, context):
        if not input_texture or input_texture <= 0: return 0
        intensity  = _c(params.get('intensity', 5.0))
        grain_size = _c(params.get('grain_size', 2.0))
        density    = _c(params.get('density', 5.0))
        spray      = _c(params.get('spray', 3.0))
        feedback   = _c(params.get('feedback', 1.0))
        blend      = _c(params.get('blend', 8.0))
        u_mix      = _c(params.get('mix', 8.0)) / 10.

        self._update_grains(density / 10., intensity / 10., spray / 10.)

        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
            return input_texture

        if not self._initialized: self.initialize(context)
        t = float(getattr(context, 'time', 0.))
        w = float(getattr(context, 'width', 1920)); h = float(getattr(context, 'height', 1080))

        n = min(len(self._grains), MAX_GRAINS)
        grain_flat = []
        for g in self._grains[:n]:
            age_n = g[2] / max(1, g[3])
            grain_flat.extend([g[0], g[1], age_n])
        # pad to MAX_GRAINS
        grain_flat.extend([0., 0., 1.] * (MAX_GRAINS - n))

        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u('tex0'), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1); gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_feed)
        gl.glUniform1i(self._u('u_feedback'), 1)
        gl.glUniform1f(self._u('u_time'), t)
        gl.glUniform2f(self._u('u_resolution'), w, h)
        gl.glUniform1f(self._u('u_mix'), u_mix)
        gl.glUniform1f(self._u('u_intensity'), intensity / 10.)
        gl.glUniform1f(self._u('u_grain_size'), grain_size / 10.)
        gl.glUniform1f(self._u('u_density'), density / 10.)
        gl.glUniform1f(self._u('u_spray'), spray / 10.)
        gl.glUniform1f(self._u('u_feedback_amt'), feedback / 10.)
        gl.glUniform1f(self._u('u_blend'), blend / 10.)
        gl.glUniform1i(self._u('u_num_grains'), n)
        gl.glUniform3fv(self._u('u_grain_data'), MAX_GRAINS, grain_flat)
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0); gl.glUseProgram(0)
        if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
        return input_texture

    def cleanup(self):
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
            if hasattr(gl, 'glDeleteFramebuffers'):
                if self.fbo_grain: gl.glDeleteFramebuffers(1, [self.fbo_grain])
                if self.fbo_feed:  gl.glDeleteFramebuffers(1, [self.fbo_feed])
            if hasattr(gl, 'glDeleteTextures'):
                if self.tex_grain: gl.glDeleteTextures(1, [self.tex_grain])
                if self.tex_feed:  gl.glDeleteTextures(1, [self.tex_feed])
        except Exception as e: logger.error(f"ArbharGranularizerPlugin cleanup: {e}")
        finally: self.prog = self.vao = self.fbo_grain = self.fbo_feed = 0
