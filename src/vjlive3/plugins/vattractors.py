"""
P3-EXT185-191: Chaotic Attractor Visualizers for VJLive3.
Ported from vjlive/plugins/vattractors/vattractors.py

All five attractors (Lorenz, Halvorsen, Thomas, Sakarya, Languor blend) in
a single plugin. CPU integrates the ODE each frame; a GPU point-cloud renders
the current trajectory window as neon trails over the video input.

Dreamer analysis: clean mathematical art — [DREAMER_GENIUS] — port faithfully.
"""
from __future__ import annotations

import logging
import math
from typing import Any

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

# # from .api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  METADATA
# ─────────────────────────────────────────────────────────────────────────────

METADATA: dict = {
    "name": "V-Attractors",
    "description": (
        "Five chaotic attractor visualizers in one plugin — Lorenz butterfly, "
        "Halvorsen spirals, Thomas grid, Sakarya cross-coupled 3D chaos, and "
        "Languor (all four blended). Each drives a neon point-cloud trail "
        "overlaid on your video. Select the attractor type with 'mode'."
    ),
    "version": "3.0.0",
    "api_version": "3.0",
    "origin": "vjlive:plugins/vattractors/vattractors.py",
    "dreamer_flag": True,
    "logic_purity": "genius",
    "role_assignment": "worker",
    "kitten_status": True,
    "plugin_type": "effect",
    "category": "generator",
    "tags": ["attractor", "chaos", "lorenz", "fractal", "modulation", "maths"],
    "performance_impact": "low",
    "parameters": {
        "mode":      {"type": "float", "default": 0.0,  "min": 0.0, "max": 4.0,
                      "description": "0=Lorenz 1=Halvorsen 2=Thomas 3=Sakarya 4=Languor"},
        "speed":     {"type": "float", "default": 5.0,  "min": 0.0, "max": 10.0},
        "amplitude": {"type": "float", "default": 5.0,  "min": 0.0, "max": 10.0},
        "trail":     {"type": "float", "default": 5.0,  "min": 0.0, "max": 10.0,
                      "description": "Point-cloud history length (0=1pt, 10=full trail)"},
        "point_size":{"type": "float", "default": 3.0,  "min": 1.0, "max": 10.0},
        "hue":       {"type": "float", "default": 0.0,  "min": 0.0, "max": 10.0,
                      "description": "Base hue offset for neon colour"},
        "mix":       {"type": "float", "default": 7.0,  "min": 0.0, "max": 10.0},
    },
}

# ─────────────────────────────────────────────────────────────────────────────
#  GLSL — fullscreen quad with overlay
# ─────────────────────────────────────────────────────────────────────────────

_VERT_PASS = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1),vec2(1,-1),vec2(-1,1),vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(verts[gl_VertexID],0,1); uv=verts[gl_VertexID]*.5+.5; }
"""

_FRAG_PASS = """
#version 330 core
in vec2 uv; out vec4 fragColor;
uniform sampler2D tex0;
uniform float u_mix;
void main() { fragColor = texture(tex0, uv); }
"""

_VERT_POINTS = """
#version 330 core
layout(location=0) in vec3 pos;
uniform vec2  resolution;
uniform float point_size;
out vec3 v_pos;
void main() {
    // Map attractor output (0-1 each axis) to NDC
    vec2 ndc = pos.xy * 2.0 - 1.0;
    gl_Position = vec4(ndc, 0.0, 1.0);
    gl_PointSize = point_size;
    v_pos = pos;
}
"""

_FRAG_POINTS = """
#version 330 core
in vec3 v_pos; out vec4 fragColor;
uniform float hue_base;
uniform float u_mix;
// HSV→RGB inline
vec3 hsv2rgb(vec3 c) {
    vec3 p = abs(fract(c.xxx + vec3(1, 2.0/3.0, 1.0/3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1), clamp(p-1.0, 0.0, 1.0), c.y);
}
void main() {
    // Soft circle
    vec2 d = gl_PointCoord - 0.5;
    float r = dot(d, d) * 4.0;
    if (r > 1.0) discard;

    float hue = fract(hue_base + v_pos.z * 0.4);
    vec3 col = hsv2rgb(vec3(hue, 0.85, 1.0));
    float alpha = (1.0 - r) * u_mix;
    fragColor = vec4(col * alpha, alpha);
}
"""

# ─────────────────────────────────────────────────────────────────────────────
#  Attractor CPU integrators (ported faithfully from legacy)
# ─────────────────────────────────────────────────────────────────────────────

class _Lorenz:
    def __init__(self): self.x, self.y, self.z = 1.0, 1.0, 1.0; self.sigma=10.0; self.beta=8/3; self.rho=28.0; self.speed=0.5
    def step(self, dt):
        s = self.speed**2
        dx = self.sigma*(self.y-self.x); dy = self.x*(self.rho-self.z)-self.y; dz = self.x*self.y-self.beta*self.z
        self.x+=dx*dt*s; self.y+=dy*dt*s; self.z+=dz*dt*s

class _Halvorsen:
    def __init__(self): self.x, self.y, self.z = 1.0, 0.0, 0.0; self.a=1.43; self.speed=0.5
    def step(self, dt):
        s = self.speed**2
        dx=(-self.a*self.x)-(4*self.y)-(4*self.z)-(self.y**2)
        dy=(-self.a*self.y)-(4*self.z)-(4*self.x)-(self.z**2)
        dz=(-self.a*self.z)-(4*self.x)-(4*self.y)-(self.x**2)
        self.x+=dx*dt*s; self.y+=dy*dt*s; self.z+=dz*dt*s

class _Thomas:
    def __init__(self): self.x, self.y, self.z = 0.1, 0.0, 0.0; self.b=0.188; self.speed=0.5
    def step(self, dt):
        s = self.speed**2
        self.x+=(-self.b*self.x+math.sin(self.y))*dt*s
        self.y+=(-self.b*self.y+math.sin(self.z))*dt*s
        self.z+=(-self.b*self.z+math.sin(self.x))*dt*s

class _Sakarya:
    def __init__(self): self.x, self.y, self.z = 1.0, -1.0, 1.0; self.a=0.398; self.b=0.3; self.speed=0.5
    def step(self, dt):
        s = self.speed**2
        dx=-self.x+self.y+self.y*self.z; dy=-self.x-self.y+self.a*self.x*self.z; dz=self.z-self.b*self.x*self.y
        self.x+=dx*dt*s; self.y+=dy*dt*s; self.z+=dz*dt*s

def _normalize(v: float, scale: float = 30.0) -> float:
    return max(0.0, min(1.0, (v / scale + 1.0) * 0.5))

# ─────────────────────────────────────────────────────────────────────────────
#  Plugin
# ─────────────────────────────────────────────────────────────────────────────

_MAX_TRAIL = 2048


class VAttractorsPlugin(object):
#     """All five chaotic attractor visualizers packaged in a single VJLive3 EffectPlugin."""

    def get_metadata(self) -> dict: return METADATA

    def __init__(self) -> None:
        super().__init__()
        self._lor = _Lorenz()
        self._hal = _Halvorsen()
        self._tho = _Thomas()
        self._sak = _Sakarya()
        self._trail: list[tuple[float, float, float]] = []
        self._prog_pass = self._prog_pts = 0
        self._vao_pass = self._vao_pts = self._vbo_pts = 0
        self._initialized = False

    # ── GL helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _compile(vs: str, fs: str) -> int:
        def _sh(src, kind):
            s = gl.glCreateShader(kind)
            gl.glShaderSource(s, src)
            gl.glCompileShader(s)
            if not gl.glGetShaderiv(s, gl.GL_COMPILE_STATUS):
                raise RuntimeError(gl.glGetShaderInfoLog(s))
            return s
        v, f = _sh(vs, gl.GL_VERTEX_SHADER), _sh(fs, gl.GL_FRAGMENT_SHADER)
        p = gl.glCreateProgram()
        gl.glAttachShader(p, v); gl.glAttachShader(p, f); gl.glLinkProgram(p)
        if not gl.glGetProgramiv(p, gl.GL_LINK_STATUS):
            raise RuntimeError(gl.glGetProgramInfoLog(p))
        gl.glDeleteShader(v); gl.glDeleteShader(f)
        return p

    def _u(self, prog: int, name: str) -> int:
        return gl.glGetUniformLocation(prog, name)

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def initialize(self, context) -> bool:
        if not HAS_GL or not hasattr(gl, 'glCreateProgram'):
            self._initialized = True
            return True
        try:
            self._prog_pass = self._compile(_VERT_PASS, _FRAG_PASS)
            self._prog_pts  = self._compile(_VERT_POINTS, _FRAG_POINTS)

            # Passthrough VAO
            self._vao_pass = gl.glGenVertexArrays(1)

            # Points VAO + VBO
            self._vao_pts = gl.glGenVertexArrays(1)
            self._vbo_pts = gl.glGenBuffers(1)
            gl.glBindVertexArray(self._vao_pts)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo_pts)
            # Pre-allocate for max trail
            import ctypes
            gl.glBufferData(gl.GL_ARRAY_BUFFER, _MAX_TRAIL * 3 * 4, None, gl.GL_DYNAMIC_DRAW)
            gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, ctypes.c_void_p(0))
            gl.glEnableVertexAttribArray(0)
            gl.glBindVertexArray(0)
            self._initialized = True
            return True
        except Exception as exc:
            logger.error("VAttractorsPlugin init: %s", exc)
            return False

    def _step_attractor(self, mode: int, speed: float, dt: float) -> tuple[float, float, float]:
        """Integrate one frame and return normalised (x,y,z) in [0,1]."""
        for att in (self._lor, self._hal, self._tho, self._sak):
            att.speed = speed
        if mode == 0:
            self._lor.step(dt); a = self._lor
            return _normalize(a.x), _normalize(a.y), _normalize(a.z)
        elif mode == 1:
            self._hal.step(dt); a = self._hal
            return _normalize(a.x), _normalize(a.y), _normalize(a.z)
        elif mode == 2:
            self._tho.step(dt); a = self._tho
            return _normalize(a.x, 5.0), _normalize(a.y, 5.0), _normalize(a.z, 5.0)
        elif mode == 3:
            self._sak.step(dt); a = self._sak
            return _normalize(a.x), _normalize(a.y), _normalize(a.z)
        else:  # Languor blend (mode 4)
            for att in (self._lor, self._hal, self._tho, self._sak):
                att.step(dt)
            x = (_normalize(self._lor.x) + _normalize(self._hal.x) +
                 _normalize(self._tho.x, 5.0) + _normalize(self._sak.x)) / 4.0
            y = (_normalize(self._lor.y) + _normalize(self._hal.y) +
                 _normalize(self._tho.y, 5.0) + _normalize(self._sak.y)) / 4.0
            z = (_normalize(self._lor.z) + _normalize(self._hal.z) +
                 _normalize(self._tho.z, 5.0) + _normalize(self._sak.z)) / 4.0
            return x, y, z

    def process_frame(self, input_texture: int, params: dict[str, Any], context) -> int:
        if not input_texture:
            return 0

        # ── Parse params ─────────────────────────────────────────────────────
        def _p(k, d): return float(params.get(k, d))
        mode       = int(min(4, max(0, _p('mode', 0.0))))
        speed      = 0.01 + _p('speed', 5.0) / 10.0 * 4.99
        amplitude  = _p('amplitude', 5.0) / 5.0
        trail_len  = max(1, int(_p('trail', 5.0) / 10.0 * _MAX_TRAIL))
        pt_size    = _p('point_size', 3.0)
        hue        = _p('hue', 0.0) / 10.0
        mix        = _p('mix', 7.0) / 10.0

        dt = 0.01  # Fixed integration step

        # ── CPU: step attractor & update trail ───────────────────────────────
        x, y, z = self._step_attractor(mode, speed, dt)
        self._trail.append((x * amplitude, y * amplitude, z))
        if len(self._trail) > trail_len:
            self._trail = self._trail[-trail_len:]

        # ── Mock / headless pass-through ─────────────────────────────────────
        if not self._initialized or not HAS_GL or not hasattr(gl, 'glCreateProgram'):
            if hasattr(context, 'outputs'):
                context.outputs['video_out'] = input_texture
            return input_texture

        # ── Pass 1: blit input texture ────────────────────────────────────────
        gl.glUseProgram(self._prog_pass)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u(self._prog_pass, 'tex0'), 0)
        gl.glUniform1f(self._u(self._prog_pass, 'u_mix'), 1.0)
        gl.glBindVertexArray(self._vao_pass)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)

        # ── Pass 2: draw attractor point cloud ────────────────────────────────
        import ctypes, array as _arr
        flat: list[float] = []
        for px, py, pz in self._trail:
            flat.extend([px, py, pz])
        if flat:
            data = _arr.array('f', flat)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo_pts)
            gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, len(data) * 4,
                               (ctypes.c_float * len(data))(*data))

            w = float(getattr(context, 'width', 1920))
            h = float(getattr(context, 'height', 1080))

            gl.glUseProgram(self._prog_pts)
            gl.glUniform2f(self._u(self._prog_pts, 'resolution'), w, h)
            gl.glUniform1f(self._u(self._prog_pts, 'point_size'), pt_size)
            gl.glUniform1f(self._u(self._prog_pts, 'hue_base'), hue)
            gl.glUniform1f(self._u(self._prog_pts, 'u_mix'), mix)

            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
            gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)

            gl.glBindVertexArray(self._vao_pts)
            gl.glDrawArrays(gl.GL_POINTS, 0, len(self._trail))
            gl.glDisable(gl.GL_BLEND)
            gl.glBindVertexArray(0)

        gl.glUseProgram(0)

        if hasattr(context, 'outputs'):
            context.outputs['video_out'] = input_texture
        return input_texture

    def cleanup(self) -> None:
        try:
            if HAS_GL and hasattr(gl, 'glDeleteProgram'):
                if self._prog_pass: gl.glDeleteProgram(self._prog_pass)
                if self._prog_pts:  gl.glDeleteProgram(self._prog_pts)
            if HAS_GL and hasattr(gl, 'glDeleteVertexArrays'):
                if self._vao_pass: gl.glDeleteVertexArrays(1, [self._vao_pass])
                if self._vao_pts:  gl.glDeleteVertexArrays(1, [self._vao_pts])
            if HAS_GL and hasattr(gl, 'glDeleteBuffers'):
                if self._vbo_pts: gl.glDeleteBuffers(1, [self._vbo_pts])
        except Exception as exc:
            logger.error("VAttractorsPlugin cleanup: %s", exc)
        finally:
            self._prog_pass = self._prog_pts = 0
            self._vao_pass = self._vao_pts = self._vbo_pts = 0


# ── Legacy compat aliases ────────────────────────────────────────────────────
VLorenzPlugin    = VAttractorsPlugin
VHalvorsenPlugin = VAttractorsPlugin
VThomasPlugin    = VAttractorsPlugin
VSakaryaPlugin   = VAttractorsPlugin
