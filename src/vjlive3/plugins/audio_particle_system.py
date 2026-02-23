"""
P4-AU02: Audio Particle System Plugin for VJLive3.
Ported from VJlive-2/plugins/vaudio_reactive/audio_reactive_effects.py::AudioParticleSystem
and VJlive-2/core/plugins/audio_particle_system.py.

CPU particle sim: up to 100 particles with audio-reactive velocity (bass/mid/treble/volume).
Fragment shader samples per-particle positions/energies via uniform arrays and renders
soft-edge circles with trails, composited over input video.
"""

from typing import Dict, Any
import numpy as np
import logging

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from .api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

MAX_PARTICLES = 100  # bound by GLSL uniform array size
FREQUENCY_BANDS = 8

METADATA = {
    "name": "Audio Particle System",
    "description": "Particles modulated by audio amplitude and frequency bands.",
    "version": "1.0.0",
    "plugin_type": "audio_effect",
    "category": "particles",
    "tags": ["audio", "particles", "reactive", "flow", "bass"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "num_particles",      "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "particle_size",      "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "particle_speed",     "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "trail_length",       "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
        {"name": "color_sensitivity",  "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
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

FRAGMENT_SHADER = f"""
#version 330 core

uniform vec2  resolution;
uniform float time;
uniform float u_mix;
uniform sampler2D tex0;

// Particle data (max {MAX_PARTICLES})
uniform int   num_particles;
uniform float particle_size;
uniform float trail_length;
uniform float color_sensitivity;
uniform vec2  particle_positions[{MAX_PARTICLES}];
uniform float particle_energies[{MAX_PARTICLES}];

// Audio levels (0-1)
uniform float bass_level;
uniform float mid_level;
uniform float treble_level;
uniform float volume_level;

out vec4 fragColor;
in vec2 uv;

void main() {{
    vec4 original = texture(tex0, uv);
    vec3 color = original.rgb;

    vec3 particle_color = vec3(0.0);  // declare before loop

    for (int i = 0; i < num_particles; i++) {{
        vec2 particle_pos = particle_positions[i];
        float energy = particle_energies[i];

        vec2 diff = uv - particle_pos;
        float dist = length(diff);

        float size = particle_size * (1.0 + energy * volume_level * 2.0);

        particle_color = vec3(
            bass_level   * color_sensitivity,
            mid_level    * color_sensitivity,
            treble_level * color_sensitivity
        );

        if (dist < size) {{
            float alpha = (1.0 - dist / size) * energy * u_mix;
            color = mix(color, particle_color, clamp(alpha, 0.0, 1.0));
        }}

        // Trail
        if (dist < size * trail_length) {{
            float trail_alpha = (1.0 - dist / (size * trail_length)) * energy * 0.3 * u_mix;
            color = mix(color, particle_color * 0.5, clamp(trail_alpha, 0.0, 1.0));
        }}
    }}

    fragColor = vec4(color, original.a);
}}
"""


def _map(val: float, out_min: float, out_max: float) -> float:
    t = max(0.0, min(10.0, float(val))) / 10.0
    return out_min + t * (out_max - out_min)


class AudioParticleSystemPlugin(EffectPlugin):
    """
    Audio-reactive particle system. CPU sim drives positions and energies;
    the fragment shader renders soft-edge circles with trails over video.
    """

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL

        self.prog = 0
        self.vao = 0
        self._initialized = False

        # CPU particle state — initialized on first frame
        self._n = 0
        self._positions:  np.ndarray = np.empty((0, 2), dtype=np.float32)
        self._velocities: np.ndarray = np.empty((0, 2), dtype=np.float32)
        self._energies:   np.ndarray = np.empty(0, dtype=np.float32)

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def _compile(self, vs_src: str, fs_src: str) -> int:
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, vs_src)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(gl.glGetShaderInfoLog(vs))
        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, fs_src)
        gl.glCompileShader(fs)
        if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(gl.glGetShaderInfoLog(fs))
        prog = gl.glCreateProgram()
        gl.glAttachShader(prog, vs)
        gl.glAttachShader(prog, fs)
        gl.glLinkProgram(prog)
        if not gl.glGetProgramiv(prog, gl.GL_LINK_STATUS):
            raise RuntimeError(gl.glGetProgramInfoLog(prog))
        gl.glDeleteShader(vs)
        gl.glDeleteShader(fs)
        return prog

    def initialize(self, context: PluginContext) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            logger.warning("AudioParticleSystem: mock mode (no GL).")
            self._initialized = True
            return True
        try:
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"AudioParticleSystem GL init failed: {e}")
            self._mock_mode = True
            return False

    def _allocate_particles(self, n: int) -> None:
        """Allocate (or reallocate) particle arrays — Safety Rail #1: bounded to MAX_PARTICLES."""
        n = max(10, min(MAX_PARTICLES, n))
        if n == self._n:
            return
        self._n = n
        rng = np.random.default_rng()
        self._positions  = rng.uniform(0.0, 1.0, (n, 2)).astype(np.float32)
        self._velocities = rng.uniform(-0.01, 0.01, (n, 2)).astype(np.float32)
        self._energies   = np.ones(n, dtype=np.float32) * 0.5

    def _simulate(self, audio: Dict[str, float], particle_speed: float, time: float) -> None:
        """CPU physics step. One call per frame, O(n) where n ≤ 100."""
        n = self._n
        if n == 0:
            return

        bass    = float(audio.get("bass",   0.0))
        volume  = float(audio.get("volume", 0.0))
        spectrum = audio.get("spectrum", None)

        dt = 1.0 / 60.0  # fixed step (Safety Rail #1: no unbounded dt)

        for i in range(n):
            band_idx = i % FREQUENCY_BANDS
            if spectrum is not None and len(spectrum) > 0:
                band_size = max(1, len(spectrum) // FREQUENCY_BANDS)
                start = band_idx * band_size
                end   = min(start + band_size, len(spectrum))
                band_energy = float(np.mean(spectrum[start:end]))
            else:
                band_energy = bass

            angle = time * particle_speed + i * 0.1
            audio_influence = band_energy * volume * 2.0
            self._velocities[i, 0] += np.cos(angle) * audio_influence * 0.01
            self._velocities[i, 1] += np.sin(angle) * audio_influence * 0.01

            self._velocities[i] *= 0.98
            self._positions[i]  += self._velocities[i]
            self._positions[i]   = np.mod(self._positions[i], 1.0)
            self._energies[i]    = band_energy * volume

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

        # ── Remap 0-10 params ──────────────────────────────────────────────
        num_p    = int(_map(params.get("num_particles",     5.0), 10, MAX_PARTICLES))
        p_size   = _map(params.get("particle_size",         5.0), 0.001, 0.1)
        p_speed  = _map(params.get("particle_speed",        5.0), 0.1, 2.0)
        trail    = _map(params.get("trail_length",          8.0), 0.1, 2.0)
        c_sens   = _map(params.get("color_sensitivity",     5.0), 0.1, 5.0)
        mix_v    = _map(params.get("mix",                   5.0), 0.0, 1.0)

        # ── Allocate particles ─────────────────────────────────────────────
        self._allocate_particles(num_p)

        # ── Pull audio from context ────────────────────────────────────────
        inputs = getattr(context, "inputs", {})
        audio_data = inputs.get("audio_data", {})
        if not isinstance(audio_data, dict):
            audio_data = {}

        bass    = float(audio_data.get("bass",    0.0))
        mid     = float(audio_data.get("mid",     0.0))
        treble  = float(audio_data.get("treble",  0.0))
        volume  = float(audio_data.get("volume",  0.0))
        time_v  = float(getattr(context, "time", 0.0))
        w       = getattr(context, "width",  1920)
        h       = getattr(context, "height", 1080)

        # ── CPU simulation ────────────────────────────────────────────────
        self._simulate(audio_data, p_speed, time_v)

        # ── Render FSQ ────────────────────────────────────────────────────
        gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.prog)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u("tex0"), 0)

        gl.glUniform2f(self._u("resolution"), float(w), float(h))
        gl.glUniform1f(self._u("time"),  time_v)
        gl.glUniform1f(self._u("u_mix"), mix_v)

        gl.glUniform1i(self._u("num_particles"),    self._n)
        gl.glUniform1f(self._u("particle_size"),    p_size)
        gl.glUniform1f(self._u("trail_length"),     trail)
        gl.glUniform1f(self._u("color_sensitivity"),c_sens)

        gl.glUniform1f(self._u("bass_level"),   bass)
        gl.glUniform1f(self._u("mid_level"),    mid)
        gl.glUniform1f(self._u("treble_level"), treble)
        gl.glUniform1f(self._u("volume_level"), volume)

        # Upload per-particle arrays
        for i in range(self._n):
            gl.glUniform2f(gl.glGetUniformLocation(self.prog, f"particle_positions[{i}]"),
                           float(self._positions[i, 0]), float(self._positions[i, 1]))
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, f"particle_energies[{i}]"),
                           float(self._energies[i]))

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
            logger.error(f"AudioParticleSystem cleanup error: {e}")
        finally:
            self.prog = 0
            self.vao  = 0
