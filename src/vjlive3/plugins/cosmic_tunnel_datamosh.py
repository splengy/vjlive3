"""
P4-AU06: Cosmic Tunnel Datamosh Plugin for VJLive3.
Ported from VJlive-2/plugins/vdatamosh/cosmic_tunnel_datamosh.py::CosmicTunnelDatamoshEffect.

Log-polar tunnel transform with fractal distortion, audio-reactive speed + wall warp,
and frame-feedback recursion composited through a trail FBO.
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
    "name": "Cosmic Tunnel Datamosh",
    "description": "Recursive fractal tunnel with datamosh pixel feedback and depth warp.",
    "version": "1.0.0",
    "plugin_type": "audio_effect",
    "category": "datamosh",
    "tags":  ["tunnel", "fractal", "datamosh", "psychedelic", "recursive", "audio"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "tunnel_speed",   "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "rotation",       "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "fractal_depth",  "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "recursion",      "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "center_pull",    "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "wall_warp",      "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "color_shift",    "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "aberration",     "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "grid_lines",     "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "depth_fov",      "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "eternity",       "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
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
uniform sampler2D prev_tex;

uniform float time;
uniform float u_mix;
uniform float tunnel_speed;
uniform float rotation;
uniform float fractal_depth;
uniform float recursion;
uniform float center_pull;
uniform float wall_warp;
uniform float color_shift;
uniform float aberration;
uniform float grid_lines;
uniform float depth_fov;
uniform float eternity;

// Audio
uniform float bass_level;
uniform float energy_level;

vec2 toTunnel(vec2 p) {
    vec2 c = p - 0.5;
    float r = max(length(c), 0.001);
    float a = atan(c.y, c.x);
    return vec2(0.5 / r, a / 3.14159);
}

void main() {
    vec2 tun = toTunnel(uv);
    tun.x += time * (tunnel_speed + energy_level * 1.5) * 0.5;
    tun.y += time * rotation * 0.1;

    float warp = sin(tun.y * 10.0 + time) * wall_warp * 0.01;
    tun.x += warp;

    // Simplified fractal distort (3 iterations)
    vec2 frac = tun;
    for (int i = 0; i < 3; i++) {
        frac = abs(frac) / max(dot(frac, frac), 0.001) - fractal_depth * 0.1;
    }

    vec2 mix_uv = mix(uv, fract(tun + frac * 0.05), depth_fov * 0.5);
    mix_uv = clamp(mix_uv, 0.0, 1.0);

    vec4 color = texture(tex0, mix_uv);

    // Feedback from previous frame
    vec2 prev_uv = (uv - 0.5) * (0.99 - center_pull * 0.02) + 0.5;
    float s = sin(rotation * 0.01);
    float c2 = cos(rotation * 0.01);
    prev_uv -= 0.5;
    prev_uv = vec2(prev_uv.x * c2 - prev_uv.y * s, prev_uv.x * s + prev_uv.y * c2);
    prev_uv += 0.5;
    vec4 prev = texture(prev_tex, prev_uv);
    color = mix(color, prev, recursion * 0.1);

    // Chromatic aberration
    if (aberration > 0.0) {
        float r_off = aberration * 0.01 * length(uv - 0.5);
        color.r = texture(tex0, clamp(mix_uv + vec2(r_off, 0), 0.0, 1.0)).r;
        color.b = texture(tex0, clamp(mix_uv - vec2(r_off, 0), 0.0, 1.0)).b;
    }

    // Grid lines overlay
    if (grid_lines > 0.5) {
        float grid = sin(tun.x * 20.0) * sin(tun.y * 20.0);
        color.rgb += vec3(smoothstep(0.9, 1.0, grid)) * 0.3 * grid_lines;
    }

    color.rgb += vec3(color_shift * 0.1, color_shift * 0.05, 0.0) * bass_level;

    // Eternity fade
    float inf_fade = abs(eternity - 5.0) * 0.1;
    float bright = eternity > 5.0 ? 1.0 : 0.0;
    color.rgb = mix(color.rgb, vec3(bright), smoothstep(0.0, 0.2, length(uv - 0.5)) * inf_fade);

    fragColor = mix(texture(tex0, uv), color, u_mix);
}
"""


def _map(val: float, out_min: float, out_max: float) -> float:
    t = max(0.0, min(10.0, float(val))) / 10.0
    return out_min + t * (out_max - out_min)


class CosmicTunnelDatamoshPlugin(object):
    """Cosmic tunnel with fractal datamosh feedback. Trail FBO gives persistence."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = 0
        self.vao = 0
        self.trail_fbo = 0
        self.trail_tex = 0
        self._w = self._h = 0
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

    def _make_fbo(self, w: int, h: int):
        fbo = gl.glGenFramebuffers(1)
        tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0,
                        gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0,
                                   gl.GL_TEXTURE_2D, tex, 0)
        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        return fbo, tex

    def initialize(self, context) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True
            return True
        try:
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao  = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"CosmicTunnelDatamosh init failed: {e}")
            self._mock_mode = True
            return False

    def _u(self, name: str) -> int:
        return gl.glGetUniformLocation(self.prog, name)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0:
            return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
        if not self._initialized:
            self.initialize(context)

        w = getattr(context, "width",  1920)
        h = getattr(context, "height", 1080)
        if w != self._w or h != self._h:
            if self.trail_fbo:
                try:
                    gl.glDeleteFramebuffers(1, [self.trail_fbo])
                    gl.glDeleteTextures(1, [self.trail_tex])
                except Exception:
                    pass
            self.trail_fbo, self.trail_tex = self._make_fbo(w, h)
            self._w, self._h = w, h

        # Remap params
        t_speed   = _map(params.get("tunnel_speed",  4.0), 0.0, 5.0)
        rot       = _map(params.get("rotation",      2.0), -3.0, 3.0)
        frac_d    = _map(params.get("fractal_depth", 3.0), 0.0, 1.0)
        recurs    = _map(params.get("recursion",     5.0), 0.0, 1.0)
        c_pull    = _map(params.get("center_pull",   4.0), 0.0, 2.0)
        w_warp    = _map(params.get("wall_warp",     3.0), 0.0, 5.0)
        c_shift   = _map(params.get("color_shift",   2.0), 0.0, 5.0)
        aberr     = _map(params.get("aberration",    3.0), 0.0, 5.0)
        g_lines   = _map(params.get("grid_lines",    2.0), 0.0, 1.0)
        d_fov     = _map(params.get("depth_fov",     5.0), 0.0, 1.0)
        etern     = _map(params.get("eternity",      5.0), 0.0, 10.0)
        mix_v     = _map(params.get("mix",           5.0), 0.0, 1.0)

        inputs = getattr(context, "inputs", {})
        audio  = inputs.get("audio_data", {})
        if not isinstance(audio, dict):
            audio = {}
        bass   = float(audio.get("bass",   0.0))
        energy = float(audio.get("volume", 0.0))
        time_v = float(getattr(context, "time", 0.0))

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.trail_fbo)
        gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.prog)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u("tex0"), 0)

        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.trail_tex)
        gl.glUniform1i(self._u("prev_tex"), 1)

        gl.glUniform1f(self._u("time"),         time_v)
        gl.glUniform1f(self._u("u_mix"),        mix_v)
        gl.glUniform1f(self._u("tunnel_speed"), t_speed)
        gl.glUniform1f(self._u("rotation"),     rot)
        gl.glUniform1f(self._u("fractal_depth"),frac_d)
        gl.glUniform1f(self._u("recursion"),    recurs)
        gl.glUniform1f(self._u("center_pull"),  c_pull)
        gl.glUniform1f(self._u("wall_warp"),    w_warp)
        gl.glUniform1f(self._u("color_shift"),  c_shift)
        gl.glUniform1f(self._u("aberration"),   aberr)
        gl.glUniform1f(self._u("grid_lines"),   g_lines)
        gl.glUniform1f(self._u("depth_fov"),    d_fov)
        gl.glUniform1f(self._u("eternity"),     etern)
        gl.glUniform1f(self._u("bass_level"),   bass)
        gl.glUniform1f(self._u("energy_level"), energy)

        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glUseProgram(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.trail_tex
        return self.trail_tex

    def cleanup(self) -> None:
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog:
                gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao:
                gl.glDeleteVertexArrays(1, [self.vao])
            if hasattr(gl, 'glDeleteTextures') and self.trail_tex:
                gl.glDeleteTextures(1, [self.trail_tex])
            if hasattr(gl, 'glDeleteFramebuffers') and self.trail_fbo:
                gl.glDeleteFramebuffers(1, [self.trail_fbo])
        except Exception as e:
            logger.error(f"CosmicTunnelDatamosh cleanup: {e}")
        finally:
            self.prog = self.vao = self.trail_fbo = self.trail_tex = 0
