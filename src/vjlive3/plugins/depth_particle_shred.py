"""
P3-VD61: Depth Particle Shred Plugin for VJLive3.
Ported from legacy VJlive-2 DepthParticleShredEffect.

Legacy used a CPU numpy particle sim (50k particles, Sobel gradients, 
GLBufferSubData every frame). In VJLive3 we replace the CPU sim with a
GPGPU approach: the depth texture IS the particle field — each texel maps
to a GL_POINTS vertex rendered via the vertex shader. The 'shred' 
displacement is computed entirely in GLSL using noise + depth.
"""

from typing import Dict, Any
import logging

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

# # from .api import EffectPlugin, PluginContext
logger = logging.getLogger(__name__)

METADATA = {
    "name": "Depth Particle Shred",
    "description": "Converts depth data into a point cloud that explodes and reassembles.",
    "version": "1.0.0",
    "plugin_type": "depth_effect",
    "category": "3d",
    "tags": ["depth", "particles", "point-cloud", "shred", "explosion", "3d"],
    "priority": 1,
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "shred_amount",    "type": "float", "min": 0.0,  "max": 1.0,  "default": 0.0},
        {"name": "particle_size",   "type": "float", "min": 1.0,  "max": 12.0, "default": 3.0},
        {"name": "velocity_scale",  "type": "float", "min": 0.0,  "max": 3.0,  "default": 1.0},
        {"name": "turbulence",      "type": "float", "min": 0.0,  "max": 2.0,  "default": 0.3},
        {"name": "trail_length",    "type": "float", "min": 0.0,  "max": 0.95, "default": 0.4},
        {"name": "color_shift",     "type": "float", "min": 0.0,  "max": 1.0,  "default": 0.2},
        {"name": "gravity",         "type": "float", "min": 0.0,  "max": 2.0,  "default": 0.1},
    ]
}

# Particle pass — each "vertex" is a UV coordinate sampled from depth texture
PARTICLE_VERT = """
#version 330 core

// We draw a regular grid of points; each corresponds to one depth sample
layout(location = 0) in vec2 a_uv;   // grid UV (0-1)

uniform sampler2D depth_tex;
uniform float time;
uniform vec2  resolution;
uniform float shred_amount;
uniform float velocity_scale;
uniform float turbulence;
uniform float gravity;
uniform float particle_size;
uniform int   has_depth;

out float v_life;
out float v_depth;
out vec2  v_uv;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
vec3  hash3(vec2 p) { return vec3(hash(p), hash(p*1.3), hash(p*2.7)); }

void main() {
    v_uv = a_uv;
    float depth = (has_depth == 1) ? texture(depth_tex, a_uv).r : 0.0;
    v_depth = depth;

    // Discard pixels with no depth
    if (depth < 0.01) { gl_Position = vec4(10.0, 10.0, 10.0, 1.0); return; }

    v_life = clamp(1.0 - shred_amount * 0.5, 0.1, 1.0);

    // Base position (centered, depth-scaled)
    float z = max(depth, 0.1);
    vec2 ndc = (a_uv * 2.0 - 1.0) * vec2(1.0, -1.0);
    ndc.x /= (resolution.x / resolution.y);
    ndc *= (1.0 / z) * 0.5;

    // Explosion displacement driven by noise + shred
    vec3 seed = hash3(a_uv * 17.3);
    vec3 vel_dir = (seed * 2.0 - 1.0);  // [-1,1]
    float explosion = shred_amount * velocity_scale;
    vec2 disp = vel_dir.xy * explosion * 0.3;

    // Turbulence
    float turb = hash(a_uv + vec2(time * 0.1)) * turbulence * shred_amount * 0.1;
    disp += vec2(turb, -turb * 0.5);

    // Gravity pulls y down
    disp.y -= gravity * shred_amount * 0.2;

    gl_Position = vec4(ndc + disp, 0.0, 1.0);
    gl_PointSize = particle_size * (1.0 / z) * (1.0 + shred_amount * 0.5);
}
"""

PARTICLE_FRAG = """
#version 330 core

in float v_life;
in float v_depth;
in vec2  v_uv;

uniform float shred_amount;
uniform float color_shift;
uniform float time;
uniform sampler2D video_tex;

out vec4 fragColor;

void main() {
    vec2 pc = gl_PointCoord * 2.0 - 1.0;
    float dist = dot(pc, pc);
    if (dist > 1.0) discard;

    float depth_norm = clamp(v_depth, 0.0, 1.0);
    float alpha = (1.0 - dist) * v_life;

    // Sample video texture at particle UV for color
    vec3 color = texture(video_tex, v_uv).rgb;

    // Chromatic shift during explosion
    if (color_shift > 0.01 && shred_amount > 0.01) {
        float r_shift = sin(v_life * 6.28 + time) * color_shift * shred_amount;
        float b_shift = sin(v_life * 6.28 + time + 4.18) * color_shift * shred_amount;
        color.r += r_shift * 0.3;
        color.b += b_shift * 0.3;
    }

    // Edge glow
    float edge_glow = smoothstep(0.6, 1.0, dist) * shred_amount * 0.5;
    color += vec3(edge_glow * 0.15, edge_glow * 0.05, edge_glow * 0.25);

    fragColor = vec4(color * alpha, alpha * 0.9);
}
"""

# Composite: blend particles + trail over video
COMPOSITE_FRAG = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D u_particle_tex;
uniform sampler2D u_trail_tex;
uniform float trail_length;

void main() {
    vec3 video     = texture(tex0, uv).rgb;
    vec4 particles = texture(u_particle_tex, uv);
    vec3 trail     = texture(u_trail_tex, uv).rgb;

    vec3 with_trail = max(particles.rgb, trail * trail_length);
    float composite_alpha = clamp(particles.a + length(with_trail) * 0.5, 0.0, 1.0);
    vec3 result = mix(video, with_trail, composite_alpha);
    fragColor = vec4(result, 1.0);
}
"""

COMPOSITE_VERT = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1),vec2(1,-1),vec2(-1,1),vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(verts[gl_VertexID],0,1); uv = verts[gl_VertexID]*0.5+0.5; }
"""

GRID_RESOLUTION = 256  # sqrt(particle count) ~ 65536 particles at full res


def _compile(vs, fs):
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


def _make_fbo(w, h):
    fbo = gl.glGenFramebuffers(1)
    tex = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
    gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
    gl.glClearColor(0, 0, 0, 0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
    return fbo, tex


class DepthParticleShredPlugin(object):
    """Depth Particle Shred — GPGPU point cloud explosion via GL_POINTS."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog_particle  = 0
        self.prog_composite = 0
        self.grid_vao = 0
        self.grid_vbo = 0
        self.fbo_particle = self.tex_particle = 0
        self.fbo_trail_a  = self.tex_trail_a  = 0
        self.fbo_trail_b  = self.tex_trail_b  = 0
        self.fbo_out = self.tex_out = 0
        self._w = self._h = 0
        self._particle_count = 0
        self._initialized = False

    def get_metadata(self):
        return METADATA

    def initialize(self, context) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True
            return True
        try:
            self.prog_particle  = _compile(PARTICLE_VERT,  PARTICLE_FRAG)
            self.prog_composite = _compile(COMPOSITE_VERT, COMPOSITE_FRAG)
            self._build_grid()
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"depth_particle_shred init failed: {e}")
            self._mock_mode = True
            return False

    def _build_grid(self):
        """Build a NxN grid of UV coords as GL_POINTS vertex data."""
        import ctypes, struct
        N = GRID_RESOLUTION
        uvs = []
        for j in range(N):
            for i in range(N):
                uvs.append(i / (N - 1))
                uvs.append(j / (N - 1))
        self._particle_count = N * N
        data = (ctypes.c_float * len(uvs))(*uvs)
        self.grid_vao = gl.glGenVertexArrays(1)
        self.grid_vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(self.grid_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.grid_vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, len(uvs) * 4, data, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
        gl.glEnableVertexAttribArray(0)
        gl.glBindVertexArray(0)

    def _free(self):
        try:
            fbos = [f for f in [self.fbo_particle, self.fbo_trail_a, self.fbo_trail_b, self.fbo_out] if f]
            texs = [t for t in [self.tex_particle, self.tex_trail_a, self.tex_trail_b, self.tex_out] if t]
            if fbos: gl.glDeleteFramebuffers(len(fbos), fbos)
            if texs: gl.glDeleteTextures(len(texs), texs)
            if self.grid_vao: gl.glDeleteVertexArrays(1, [self.grid_vao])
            if self.grid_vbo: gl.glDeleteBuffers(1, [self.grid_vbo])
        except Exception:
            pass
        (self.fbo_particle, self.tex_particle,
         self.fbo_trail_a,  self.tex_trail_a,
         self.fbo_trail_b,  self.tex_trail_b,
         self.fbo_out,      self.tex_out,
         self.grid_vao, self.grid_vbo) = (0,) * 10

    def _alloc(self, w, h):
        self._free()
        self._w, self._h = w, h
        self.fbo_particle, self.tex_particle = _make_fbo(w, h)
        self.fbo_trail_a,  self.tex_trail_a  = _make_fbo(w, h)
        self.fbo_trail_b,  self.tex_trail_b  = _make_fbo(w, h)
        self.fbo_out,      self.tex_out      = _make_fbo(w, h)

    def _u(self, prog, name):
        return gl.glGetUniformLocation(prog, name)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0:
            return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
        if not self._initialized:
            self.initialize(context)
        w = getattr(context, 'width', 1920)
        h = getattr(context, 'height', 1080)
        if w != self._w or h != self._h:
            self._alloc(w, h)

        inputs   = getattr(context, "inputs", {})
        depth_in = inputs.get("depth_in", 0)
        time_val = getattr(context, 'time', 0.0)
        has_d    = 1 if depth_in > 0 else 0

        shred    = float(params.get("shred_amount",   0.0))
        p_size   = float(params.get("particle_size",  3.0))
        vel_s    = float(params.get("velocity_scale", 1.0))
        turb     = float(params.get("turbulence",     0.3))
        trail    = float(params.get("trail_length",   0.4))
        c_shift  = float(params.get("color_shift",    0.2))
        grav     = float(params.get("gravity",        0.1))

        gl.glViewport(0, 0, w, h)

        # ── Pass 1: Render particles to FBO ──────────────────────────────
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_particle)
        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
        gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)

        gl.glUseProgram(self.prog_particle)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in if has_d else 0)
        gl.glUniform1i(self._u(self.prog_particle, "depth_tex"), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u(self.prog_particle, "video_tex"), 1)
        gl.glUniform1i(self._u(self.prog_particle, "has_depth"),    has_d)
        gl.glUniform2f(self._u(self.prog_particle, "resolution"),   float(w), float(h))
        gl.glUniform1f(self._u(self.prog_particle, "time"),         float(time_val))
        gl.glUniform1f(self._u(self.prog_particle, "shred_amount"), shred)
        gl.glUniform1f(self._u(self.prog_particle, "velocity_scale"), vel_s)
        gl.glUniform1f(self._u(self.prog_particle, "turbulence"),   turb)
        gl.glUniform1f(self._u(self.prog_particle, "gravity"),      grav)
        gl.glUniform1f(self._u(self.prog_particle, "particle_size"),p_size)
        gl.glUniform1f(self._u(self.prog_particle, "color_shift"),  c_shift)
        gl.glUniform1f(self._u(self.prog_particle, "shred_amount"), shred)

        gl.glBindVertexArray(self.grid_vao)
        gl.glDrawArrays(gl.GL_POINTS, 0, self._particle_count)
        gl.glBindVertexArray(0)
        gl.glDisable(gl.GL_PROGRAM_POINT_SIZE)
        gl.glDisable(gl.GL_BLEND)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        # ── Pass 2: Composite particles + trail over video ────────────────
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_out)
        gl.glUseProgram(self.prog_composite)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u(self.prog_composite, "tex0"), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_particle)
        gl.glUniform1i(self._u(self.prog_composite, "u_particle_tex"), 1)
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_trail_b)
        gl.glUniform1i(self._u(self.prog_composite, "u_trail_tex"), 2)
        gl.glUniform1f(self._u(self.prog_composite, "trail_length"), trail)

        # draw FSQ
        vao_tmp = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(vao_tmp)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glDeleteVertexArrays(1, [vao_tmp])
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        # Trail update: trail_a receives current output for next frame
        self.fbo_trail_a, self.fbo_trail_b = self.fbo_trail_b, self.fbo_trail_a
        self.tex_trail_a, self.tex_trail_b = self.tex_trail_b, self.tex_trail_a

        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.tex_out
        return self.tex_out

    def cleanup(self) -> None:
        try:
            self._free()
            if hasattr(gl, 'glDeleteProgram'):
                if self.prog_particle:  gl.glDeleteProgram(self.prog_particle)
                if self.prog_composite: gl.glDeleteProgram(self.prog_composite)
        except Exception as e:
            logger.error(f"Cleanup error depth_particle_shred: {e}")
        finally:
            self.prog_particle = self.prog_composite = 0
