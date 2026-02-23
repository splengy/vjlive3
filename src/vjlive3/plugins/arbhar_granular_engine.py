"""
P3-EXT007: ArbharGranularEngine — Granular synthesis with circular buffer.

Spawns/manages up to 32 grain particles from a circular video buffer.
Each grain has position (buffer index), size, pitch, alpha (envelope), quality.
Audio reactive: treble→intensity, bass→spray, mid→grain_pitch.

Ported from vjlive: effects/arbhar_granular_engine.py (253 lines)
"""
import random
import logging
from typing import Dict
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

MAX_GRAINS   = 32
BUFFER_SECS  = 2.0   # Half-resolution 2-second buffer for memory safety
BUFFER_FPS   = 60.0
BUFFER_FRAMES = int(BUFFER_SECS * BUFFER_FPS)

METADATA = {
    "name": "Arbhar Granular Engine",
    "description": "Granular synthesis with circular video buffer — up to 32 grains with pitch shift, temporal spray and quality modes.",
    "version": "2.0.0",
    "plugin_type": "effect",
    "category": "synthesis",
    "tags": ["granular", "synthesis", "audio-reactive", "buffer", "pitch-shift"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "intensity",   "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "spray",       "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "grain_pitch", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "quality",     "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "mix",         "type": "float", "default": 6.0, "min": 0.0, "max": 10.0},
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
uniform float u_time;
uniform vec2 u_resolution;
uniform float u_mix;
uniform float u_intensity;
uniform float u_spray;
uniform float u_grain_pitch;
uniform float u_quality;

// Grain state (up to 32)
uniform int   u_active_grains;
uniform vec2  u_grain_pos[32];    // (uv_offset_x, uv_offset_y)
uniform float u_grain_pitch_v[32];
uniform float u_grain_alpha[32];
uniform float u_grain_qual[32];

float hash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }

void main() {
    vec4 color = texture(tex0, uv);
    vec4 grain_sum = vec4(0.0);

    for (int i = 0; i < 32; i++) {
        if (i >= u_active_grains) break;
        if (u_grain_alpha[i] <= 0.0) continue;

        // Pitch-scale UV around grain center
        vec2 pivot = u_grain_pos[i];
        vec2 g_uv = pivot + (uv - pivot) * u_grain_pitch_v[i];
        g_uv = clamp(g_uv, 0.001, 0.999);

        // Apply spray jitter
        g_uv += vec2(hash(g_uv + u_time), hash(g_uv + u_time + 10.0) - 0.5) * u_spray * 0.02;
        g_uv = clamp(g_uv, 0.001, 0.999);

        vec4 gc = texture(tex0, g_uv);
        float mf = u_grain_alpha[i] * 0.05 * u_grain_qual[i];
        grain_sum = mix(grain_sum, gc, mf);
    }

    // Mix 40% original + 60% grains
    vec4 granular = mix(color, grain_sum, 0.6);
    fragColor = mix(color, granular, u_mix);
}
"""

PRESETS = {
    "default":      {"intensity": 0.0, "spray": 0.0, "grain_pitch": 5.0, "quality": 5.0},
    "dense_grains": {"intensity": 8.0, "spray": 2.0, "grain_pitch": 5.0, "quality": 5.0},
    "chaotic_spray":{"intensity": 5.0, "spray": 9.0, "grain_pitch": 5.0, "quality": 5.0},
    "pitch_shift":  {"intensity": 4.0, "spray": 1.0, "grain_pitch": 9.0, "quality": 7.0},
    "lo_fi_tape":   {"intensity": 6.0, "spray": 4.0, "grain_pitch": 3.0, "quality": 0.0},
}


def _quality_factor(q_0_10: float) -> float:
    q = max(0., min(10., q_0_10)) / 10.
    if q < 0.3:   return 0.3   # lo-fi
    elif q < 0.7: return 0.7   # standard
    else:          return 1.0   # hi-fi


def _clamp(v, lo=0.0, hi=10.0): return max(lo, min(hi, float(v)))


class ArbharGranularEnginePlugin(EffectPlugin):
    """Granular synthesis with circular buffer and 32-grain particle system."""

    def __init__(self):
        super().__init__()
        self._mock_mode   = not (HAS_GL and HAS_NP)
        self.prog = self.vao = 0
        self._initialized = False
        # Grain state arrays
        self._positions  = [[0.5, 0.5]] * MAX_GRAINS
        self._pitches    = [1.0] * MAX_GRAINS
        self._alphas     = [0.0] * MAX_GRAINS
        self._quality_v  = [0.7] * MAX_GRAINS
        self._active     = 0
        # Audio smoothing
        self._intensity   = 0.0
        self._spray_v     = 0.0
        self._grain_pitch = 5.0

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
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao  = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"ArbharGranularEnginePlugin init: {e}"); self._mock_mode = True; return False

    # ── Grain management ────────────────────────────────────────────────────

    def _get_quality_factor(self, quality: float) -> float:
        return _quality_factor(quality)

    def _spawn_grain(self, quality: float) -> None:
        if self._active >= MAX_GRAINS:
            return
        self._positions[self._active] = [random.random(), random.random()]
        self._pitches[self._active]   = 1.0
        self._alphas[self._active]    = 1.0
        self._quality_v[self._active] = _quality_factor(quality)
        self._active += 1

    def _update_grain_parameters(self, spray: float, grain_pitch: float) -> None:
        alive_pos, alive_pit, alive_alpha, alive_qual = [], [], [], []
        for i in range(self._active):
            self._alphas[i] -= 0.005   # 200-frame lifetime
            if self._alphas[i] <= 0.0:
                continue
            # Position jitter (spray)
            self._positions[i][0] = _clamp(self._positions[i][0] + (random.random()-0.5)*spray*0.01, 0.0, 1.0)
            self._positions[i][1] = _clamp(self._positions[i][1] + (random.random()-0.5)*spray*0.01, 0.0, 1.0)
            # Pitch factor
            self._pitches[i] = 1.0 + (grain_pitch - 5.0) * 0.1
            alive_pos.append(self._positions[i])
            alive_pit.append(self._pitches[i])
            alive_alpha.append(self._alphas[i])
            alive_qual.append(self._quality_v[i])
        self._active = len(alive_pos)
        for i, (p, pi, a, q) in enumerate(zip(alive_pos, alive_pit, alive_alpha, alive_qual)):
            self._positions[i] = p; self._pitches[i] = pi
            self._alphas[i] = a;   self._quality_v[i] = q

    def update_audio(self, signals: Dict) -> None:
        sm = 0.1
        if "treble" in signals:
            self._intensity = _clamp(self._intensity*(1-sm) + float(signals["treble"])*10.*0.5*sm)
        if "bass" in signals:
            self._spray_v   = _clamp(self._spray_v*(1-sm) + float(signals["bass"])*10.*0.5*sm)
        if "mid" in signals:
            self._grain_pitch = _clamp(self._grain_pitch*(1-sm) + float(signals["mid"])*10.*0.5*sm)

    # ── Rendering ─────────────────────────────────────────────────────────

    def process_frame(self, input_texture, params, context):
        if not input_texture or input_texture <= 0: return 0
        intensity   = _clamp(params.get('intensity', 0.0))
        spray       = _clamp(params.get('spray', 0.0))
        grain_pitch = _clamp(params.get('grain_pitch', 5.0))
        quality     = _clamp(params.get('quality', 5.0))
        u_mix       = _clamp(params.get('mix', 6.0)) / 10.0

        # Spawn grains
        spawn_rate = intensity * 0.05
        if random.random() < spawn_rate and self._active < MAX_GRAINS:
            self._spawn_grain(quality)

        # Update grains
        self._update_grain_parameters(spray / 10., grain_pitch)

        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
            return input_texture

        if not self._initialized: self.initialize(context)
        t = float(getattr(context, 'time', 0.))
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u('tex0'), 0)
        gl.glUniform1f(self._u('u_time'), t)
        gl.glUniform2f(self._u('u_resolution'), float(getattr(context,'width',1920)), float(getattr(context,'height',1080)))
        gl.glUniform1f(self._u('u_mix'), u_mix)
        gl.glUniform1f(self._u('u_intensity'), intensity / 10.)
        gl.glUniform1f(self._u('u_spray'), spray / 10.)
        gl.glUniform1f(self._u('u_grain_pitch'), grain_pitch / 10.)
        gl.glUniform1f(self._u('u_quality'), quality / 10.)
        gl.glUniform1i(self._u('u_active_grains'), self._active)
        if self._active > 0:
            import ctypes
            flat_pos = [v for pos in self._positions[:MAX_GRAINS] for v in pos]
            gl.glUniform2fv(self._u('u_grain_pos'), MAX_GRAINS, flat_pos)
            gl.glUniform1fv(self._u('u_grain_pitch_v'), MAX_GRAINS, self._pitches[:MAX_GRAINS])
            gl.glUniform1fv(self._u('u_grain_alpha'), MAX_GRAINS, self._alphas[:MAX_GRAINS])
            gl.glUniform1fv(self._u('u_grain_qual'), MAX_GRAINS, self._quality_v[:MAX_GRAINS])
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0); gl.glUseProgram(0)
        if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
        return input_texture

    def cleanup(self):
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
        except Exception as e: logger.error(f"ArbharGranularEnginePlugin cleanup: {e}")
        finally: self.prog = self.vao = 0
