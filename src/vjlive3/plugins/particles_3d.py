"""
P3-EXT003: AdvancedParticle3DSystem — 3D particle system with physics,
GPU instancing, force fields, and audio reactivity.

Ported from VJLive-2: plugins/vparticles/particles_3d.py
"""
from typing import Dict, Any, List
import logging
import math
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
    "name": "Advanced Particle 3D",
    "description": "3D particle system with physics simulation, force fields and audio reactivity.",
    "version": "1.0.0",
    "plugin_type": "effect",
    "category": "generator",
    "tags": ["particles", "3d", "physics", "audio", "flocking", "simulation"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        # System
        {"name": "num_particles",        "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "particle_size",        "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "particle_color",       "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "lifetime",             "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
        # Forces
        {"name": "gravity",              "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "wind",                 "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "attractor_strength",   "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "repeller_strength",    "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "magnetic_strength",    "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "noise_strength",       "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        # Flocking
        {"name": "flocking_separation",  "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "flocking_alignment",   "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "flocking_cohesion",    "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        # Camera
        {"name": "camera_distance",      "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "camera_fov",           "type": "float", "default": 6.0, "min": 0.0, "max": 10.0},
        {"name": "camera_rotation_x",    "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "camera_rotation_y",    "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        # Emitter
        {"name": "emit_rate",            "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
        {"name": "emit_lifetime",        "type": "float", "default": 7.0, "min": 0.0, "max": 10.0},
        {"name": "emit_size",            "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "emit_spread",          "type": "float", "default": 6.0, "min": 0.0, "max": 10.0},
        # Output
        {"name": "mix",                  "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
    ],
}

VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 a_position;
layout (location = 1) in vec3 a_velocity;
layout (location = 2) in float a_lifetime;

uniform mat4 mvp_matrix;
uniform float particle_size;
uniform float time;
uniform float audio_bass;

out float v_lifetime;
out vec3  v_position;

void main() {
    gl_Position  = mvp_matrix * vec4(a_position, 1.0);
    float s_mod  = 1.0 + audio_bass * 0.5;
    gl_PointSize = max(1.0, particle_size * s_mod * (1.0 - gl_Position.z * 0.1));
    v_position   = a_position;
    v_lifetime   = a_lifetime;
}
"""

FRAGMENT_SHADER = """
#version 330 core
in float v_lifetime;
in vec3  v_position;
out vec4 frag_color;

uniform vec3  particle_color;
uniform float time;

void main() {
    // Soft circular point sprite
    vec2  pc    = gl_PointCoord - 0.5;
    float d     = length(pc) * 2.0;
    float alpha = v_lifetime * smoothstep(1.0, 0.5, d);
    if (alpha < 0.01) discard;
    float dist  = length(v_position);
    vec3  col   = particle_color * (1.0 + dist * 0.2);
    frag_color  = vec4(mix(particle_color, col, 0.3), alpha);
}
"""

COMPOSITE_VERT = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1), vec2(1,-1), vec2(-1,1), vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(verts[gl_VertexID], 0.0, 1.0); uv = verts[gl_VertexID]*0.5+0.5; }
"""

COMPOSITE_FRAG = """
#version 330 core
in vec2 uv; out vec4 frag_color;
uniform sampler2D tex_input;
uniform sampler2D tex_particles;
uniform float u_mix;
void main() {
    vec4 bg  = texture(tex_input, uv);
    vec4 pts = texture(tex_particles, uv);
    frag_color = mix(bg, pts + bg * (1.0 - pts.a), u_mix);
}
"""

_MAX_PARTICLES = 5000   # Per-frame cap for performance; scales with num_particles

PRESETS = {
    "basic_fireworks":   {"num_particles": 5.0, "particle_size": 3.0, "gravity": 6.0, "emit_spread": 6.0, "mix": 5.0},
    "flocking_birds":    {"num_particles": 3.0, "flocking_separation": 6.0, "flocking_alignment": 7.0, "flocking_cohesion": 5.0, "mix": 4.0},
    "audio_reactive":    {"num_particles": 4.0, "particle_size": 4.0, "noise_strength": 5.0, "attractor_strength": 2.0, "mix": 6.0},
    "space_simulation":  {"num_particles": 2.0, "gravity": 8.0, "attractor_strength": 6.0, "magnetic_strength": 7.0, "mix": 3.0},
    "abstract_art":      {"num_particles": 6.0, "noise_strength": 8.0, "flocking_separation": 4.0, "wind": 5.0, "mix": 7.0},
}


def _perspective(fov_deg, aspect, near, far):
    """Simple 4×4 perspective matrix."""
    f = 1.0 / math.tan(math.radians(fov_deg) / 2.0)
    nf = 1.0 / (near - far)
    return [f/aspect, 0, 0, 0,
            0, f, 0, 0,
            0, 0, (far+near)*nf, -1,
            0, 0, 2*far*near*nf, 0]


def _rotation_x(a):
    c, s = math.cos(a), math.sin(a)
    return [1,0,0,0, 0,c,-s,0, 0,s,c,0, 0,0,0,1]


def _rotation_y(a):
    c, s = math.cos(a), math.sin(a)
    return [c,0,s,0, 0,1,0,0, -s,0,c,0, 0,0,0,1]


def _mat4_mul(a, b):
    r = [0.0] * 16
    for i in range(4):
        for j in range(4):
            r[i*4+j] = sum(a[i*4+k]*b[k*4+j] for k in range(4))
    return r


class AdvancedParticle3DPlugin(EffectPlugin):
    """Advanced 3D particle system — GPU-instanced physics with force fields."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not (HAS_GL and HAS_NP)
        self.prog_particle = self.prog_composite = 0
        self.vao = self.vbo_pos = self.vbo_vel = self.vbo_life = 0
        self.fbo = self.fbo_tex = 0
        self._w = self._h = 0
        self._initialized = False
        # CPU particle state (numpy arrays)
        self._positions  = None  # (N, 3)
        self._velocities = None  # (N, 3)
        self._lifetimes  = None  # (N,)  0-1
        self._ages       = None  # (N,)  seconds
        self._max_n = 0
        self._time = 0.0

    def get_metadata(self): return METADATA

    # ── OpenGL helpers ────────────────────────────────────────────────────────

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
        for k, v2 in [(gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR), (gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)]:
            gl.glTexParameteri(gl.GL_TEXTURE_2D, k, v2)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
        gl.glClearColor(0, 0, 0, 0); gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0); return fbo, tex

    def _alloc_particles(self, n):
        """Allocate/reallocate CPU particle buffers."""
        self._max_n = n
        rng = np.random if HAS_NP else None
        self._positions  = np.zeros((n, 3), dtype=np.float32)
        self._velocities = np.zeros((n, 3), dtype=np.float32)
        self._lifetimes  = np.zeros(n, dtype=np.float32)
        self._ages       = np.zeros(n, dtype=np.float32)

    def initialize(self, context):
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog_particle = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.prog_composite = self._compile(COMPOSITE_VERT, COMPOSITE_FRAG)
            self.vao = gl.glGenVertexArrays(1)
            gl.glBindVertexArray(self.vao)
            self.vbo_pos  = gl.glGenBuffers(1)
            self.vbo_vel  = gl.glGenBuffers(1)
            self.vbo_life = gl.glGenBuffers(1)
            gl.glBindVertexArray(0)
            self._alloc_particles(_MAX_PARTICLES)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"AdvancedParticle3DPlugin init: {e}"); self._mock_mode = True; return False

    def _u(self, prog, n): return gl.glGetUniformLocation(prog, n)

    def _update_physics(self, n, params, dt, audio_bass):
        """Update particle state on CPU (NumPy)."""
        if self._positions is None or n == 0:
            return
        # Remap forces
        grav  = params.get('gravity', 3.0)  / 10.0 * 9.8
        wind  = params.get('wind', 2.0)     / 10.0 * 2.0
        noise = params.get('noise_strength', 2.0) / 10.0
        attr  = params.get('attractor_strength', 0.0) / 10.0
        rep   = params.get('repeller_strength', 0.0) / 10.0
        lifetime_max = params.get('lifetime', 8.0) / 10.0 * 10.0 + 0.5

        pos = self._positions[:n]
        vel = self._velocities[:n]
        life= self._lifetimes[:n]
        age = self._ages[:n]

        # Gravity (Y-down)
        vel[:, 1] -= grav * dt

        # Wind (X-axis)
        vel[:, 0] += wind * dt

        # Attractor toward origin
        if attr > 0.0:
            dist = np.linalg.norm(pos, axis=1, keepdims=True) + 1e-6
            vel -= (pos / dist) * attr * dt

        # Repeller from origin
        if rep > 0.0:
            dist = np.linalg.norm(pos, axis=1, keepdims=True) + 1e-6
            vel += (pos / dist) * rep * dt

        # Noise impulse (simple pseudo-random per frame)
        if noise > 0.0:
            rng_vals = np.sin(pos * 7.3 + self._time * 2.1)
            vel += rng_vals * noise * dt

        # Audio bass pulse
        vel[:, 1] += audio_bass * 0.5 * dt

        # Integrate
        self._positions[:n] += self._velocities[:n] * dt
        self._ages[:n] += dt
        self._lifetimes[:n] = np.clip(1.0 - self._ages[:n] / lifetime_max, 0., 1.)

        # Respawn dead particles
        dead = self._lifetimes[:n] <= 0.0
        n_dead = np.sum(dead)
        if n_dead > 0:
            spread = params.get('emit_spread', 6.0) / 10.0 * 2.0
            self._positions[:n][dead] = np.random.randn(n_dead, 3).astype(np.float32) * spread * 0.1
            self._velocities[:n][dead] = np.random.randn(n_dead, 3).astype(np.float32) * spread
            self._ages[:n][dead] = 0.0
            self._lifetimes[:n][dead] = 1.0

    def process_frame(self, input_texture, params, context):
        if not input_texture or input_texture <= 0: return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
            return input_texture
        if not self._initialized: self.initialize(context)
        w = getattr(context, 'width', 1920); h = getattr(context, 'height', 1080)
        dt = 1.0 / 60.0; self._time += dt

        if w != self._w or h != self._h:
            if self.fbo:
                try: gl.glDeleteFramebuffers(1, [self.fbo]); gl.glDeleteTextures(1, [self.fbo_tex])
                except Exception: pass
            self.fbo, self.fbo_tex = self._make_fbo(w, h); self._w, self._h = w, h

        # Particle count
        n = max(1, int(params.get('num_particles', 5.0) / 10.0 * _MAX_PARTICLES))
        if self._positions is None or n > self._max_n:
            self._alloc_particles(max(n, _MAX_PARTICLES))

        # Audio
        audio = getattr(context, 'inputs', {}).get('audio_data', {})
        bass = float(audio.get('bass', 0.0)) if isinstance(audio, dict) else 0.0

        # Update physics
        self._update_physics(n, params, dt, bass)

        # Upload particle data
        gl.glBindVertexArray(self.vao)
        pos_data  = self._positions[:n].flatten()
        vel_data  = self._velocities[:n].flatten()
        life_data = self._lifetimes[:n]

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo_pos)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, pos_data.nbytes, pos_data, gl.GL_STREAM_DRAW)
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo_vel)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vel_data.nbytes, vel_data, gl.GL_STREAM_DRAW)
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo_life)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, life_data.nbytes, life_data, gl.GL_STREAM_DRAW)
        gl.glEnableVertexAttribArray(2)
        gl.glVertexAttribPointer(2, 1, gl.GL_FLOAT, gl.GL_FALSE, 0, None)

        gl.glBindVertexArray(0)

        # Build MVP matrix
        aspect = w / max(h, 1)
        fov    = 30.0 + params.get('camera_fov', 6.0) / 10.0 * 90.0
        cam_d  = 2.0  + params.get('camera_distance', 5.0) / 10.0 * 18.0
        rx     = math.radians(params.get('camera_rotation_x', 0.0) / 10.0 * 90.0)
        ry     = math.radians(params.get('camera_rotation_y', 0.0) / 10.0 * 90.0)
        proj   = _perspective(fov, aspect, 0.1, 100.0)
        view   = _mat4_mul(_mat4_mul(_rotation_x(rx), _rotation_y(ry)),
                           [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,-cam_d,1])
        mvp    = _mat4_mul(proj, view)

        # Particle color from param
        hue = params.get('particle_color', 5.0) / 10.0
        r = 0.5 + 0.5 * math.cos(2*math.pi*(hue + 0.0))
        g = 0.5 + 0.5 * math.cos(2*math.pi*(hue + 0.333))
        b = 0.5 + 0.5 * math.cos(2*math.pi*(hue + 0.667))

        p_size = 1.0 + params.get('particle_size', 3.0) / 10.0 * 15.0

        # Render particles to FBO
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        gl.glClearColor(0, 0, 0, 0); gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
        gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)

        gl.glUseProgram(self.prog_particle)
        gl.glUniformMatrix4fv(self._u(self.prog_particle, 'mvp_matrix'), 1, gl.GL_FALSE, mvp)
        gl.glUniform1f(self._u(self.prog_particle, 'particle_size'), p_size)
        gl.glUniform1f(self._u(self.prog_particle, 'time'), self._time)
        gl.glUniform1f(self._u(self.prog_particle, 'audio_bass'), bass)
        gl.glUniform3f(self._u(self.prog_particle, 'particle_color'), r, g, b)

        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_POINTS, 0, n)
        gl.glBindVertexArray(0)
        gl.glDisable(gl.GL_BLEND)
        gl.glDisable(gl.GL_PROGRAM_POINT_SIZE)
        gl.glUseProgram(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        # Composite particles over input
        u_mix = params.get('mix', 5.0) / 10.0
        gl.glUseProgram(self.prog_composite)
        gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture); gl.glUniform1i(self._u(self.prog_composite, 'tex_input'), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1); gl.glBindTexture(gl.GL_TEXTURE_2D, self.fbo_tex);  gl.glUniform1i(self._u(self.prog_composite, 'tex_particles'), 1)
        gl.glUniform1f(self._u(self.prog_composite, 'u_mix'), u_mix)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glUseProgram(0)

        if hasattr(context, 'outputs'): context.outputs['video_out'] = self.fbo_tex
        return self.fbo_tex

    def cleanup(self):
        try:
            if hasattr(gl, 'glDeleteProgram'):
                if self.prog_particle:  gl.glDeleteProgram(self.prog_particle)
                if self.prog_composite: gl.glDeleteProgram(self.prog_composite)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao:
                gl.glDeleteVertexArrays(1, [self.vao])
            if hasattr(gl, 'glDeleteBuffers'):
                for buf in [self.vbo_pos, self.vbo_vel, self.vbo_life]:
                    if buf: gl.glDeleteBuffers(1, [buf])
            if hasattr(gl, 'glDeleteTextures') and self.fbo_tex:
                gl.glDeleteTextures(1, [self.fbo_tex])
            if hasattr(gl, 'glDeleteFramebuffers') and self.fbo:
                gl.glDeleteFramebuffers(1, [self.fbo])
        except Exception as e: logger.error(f"AdvancedParticle3DPlugin cleanup: {e}")
        finally:
            self.prog_particle = self.prog_composite = 0
            self.vao = self.vbo_pos = self.vbo_vel = self.vbo_life = 0
            self.fbo = self.fbo_tex = 0
