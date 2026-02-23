"""
P3-VD70: Depth Video Projection Plugin for VJLive3.
Ported from legacy VJlive-2 DepthVideoProjectionEffect.

Clean Single-Pass FSQ architecture. Depth drives surface normals.
Normal-based lighting + Fresnel edge glow. No CPU depth upload needed —
depth_in is a VJLive3 standard texture input.
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
    "name": "Depth Video Projection",
    "description": "Projects video onto performer's depth surface via normal-mapped UV distortion.",
    "version": "1.0.0",
    "plugin_type": "depth_effect",
    "category": "projection",
    "tags": ["depth", "projection", "normals", "hologram", "surface"],
    "priority": 1,
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "projection",    "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "depth_contour", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "uv_scale",      "type": "float", "min": 0.2, "max": 3.0, "default": 1.0},
        {"name": "uv_scroll_x",   "type": "float", "min":-1.0, "max": 1.0, "default": 0.0},
        {"name": "uv_scroll_y",   "type": "float", "min":-1.0, "max": 1.0, "default": 0.0},
        {"name": "normal_light",  "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "mask_tight",    "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "hologram_glow", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
    ]
}

VERTEX_SRC = """
#version 330 core
const vec2 v[4] = vec2[4](vec2(-1,-1),vec2(1,-1),vec2(-1,1),vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(v[gl_VertexID],0,1); uv = v[gl_VertexID]*0.5+0.5; }
"""

PROJECTION_FRAG = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D u_depth_tex;
uniform int has_depth;
uniform vec2 resolution;
uniform float projection;
uniform float depth_contour;
uniform float uv_scale;
uniform vec2  uv_scroll;
uniform float normal_light;
uniform float mask_tight;
uniform float hologram_glow;

vec3 computeNormal(vec2 coord) {
    vec2 pixel = 1.0 / resolution;
    float dl = texture(u_depth_tex, coord + vec2(-pixel.x, 0)).r;
    float dr = texture(u_depth_tex, coord + vec2( pixel.x, 0)).r;
    float du = texture(u_depth_tex, coord + vec2(0,  pixel.y)).r;
    float dd = texture(u_depth_tex, coord + vec2(0, -pixel.y)).r;
    return normalize(vec3(-(dr-dl)*5.0, -(du-dd)*5.0, 1.0));
}

float performerMask(float depth) {
    if (depth < 0.01) return 0.0;
    float far_cutoff = mix(1.0, 0.6, mask_tight);
    return smoothstep(0.01, 0.08, depth) * smoothstep(far_cutoff, far_cutoff-0.1, depth);
}

void main() {
    vec3 video = texture(tex0, uv).rgb;
    if (has_depth == 0) { fragColor = vec4(video, 1.0); return; }

    float depth = texture(u_depth_tex, uv).r;
    float mask  = performerMask(depth);

    if (mask < 0.01) { fragColor = vec4(video * 0.2, 1.0); return; }

    vec3 normal = computeNormal(uv);
    vec2 proj_uv = fract((uv + normal.xy * depth_contour * 0.2) * uv_scale + uv_scroll);
    vec3 projected = texture(tex0, proj_uv).rgb;

    vec3 light_dir = normalize(vec3(0.2, -0.3, 1.0));
    float ndotl = max(dot(normal, light_dir), 0.0);
    projected *= mix(1.0, 0.3 + 0.7*ndotl, normal_light);

    float fresnel = pow(1.0 - abs(normal.z), 3.0);
    vec3 holo = vec3(0.2, 0.6, 1.0) * fresnel * hologram_glow * 2.0;

    vec3 result = projected * projection + holo;
    result = mix(video * 0.15, result, smoothstep(0.0, 0.15, mask));
    result = mix(video, result, 1.0);

    fragColor = vec4(result, 1.0);
}
"""

def _compile(vs, fs):
    v = gl.glCreateShader(gl.GL_VERTEX_SHADER)
    gl.glShaderSource(v, vs); gl.glCompileShader(v)
    if not gl.glGetShaderiv(v, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(v))
    f = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
    gl.glShaderSource(f, fs); gl.glCompileShader(f)
    if not gl.glGetShaderiv(f, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(f))
    p = gl.glCreateProgram()
    gl.glAttachShader(p, v); gl.glAttachShader(p, f); gl.glLinkProgram(p)
    if not gl.glGetProgramiv(p, gl.GL_LINK_STATUS): raise RuntimeError(gl.glGetProgramInfoLog(p))
    gl.glDeleteShader(v); gl.glDeleteShader(f)
    return p

def _make_fbo(w, h):
    fbo = gl.glGenFramebuffers(1); tex = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
    gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
    gl.glClearColor(0,0,0,0); gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
    return fbo, tex


class DepthVideoProjectionPlugin(object):
    """Depth Video Projection — normal-mapped video projection onto performer surface."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = 0; self.empty_vao = 0
        self.fbo = self.tex = 0
        self._w = self._h = 0
        self._initialized = False

    def get_metadata(self): return METADATA

    def initialize(self, context) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = _compile(VERTEX_SRC, PROJECTION_FRAG)
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"depth_video_projection init failed: {e}")
            self._mock_mode = True; return False

    def _free(self):
        try:
            if self.tex: gl.glDeleteTextures(1, [self.tex])
            if self.fbo: gl.glDeleteFramebuffers(1, [self.fbo])
        except Exception: pass
        self.fbo = self.tex = 0

    def _alloc(self, w, h):
        self._free(); self._w, self._h = w, h
        self.fbo, self.tex = _make_fbo(w, h)

    def _u(self, name): return gl.glGetUniformLocation(self.prog, name)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0: return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"): context.outputs["video_out"] = input_texture
            return input_texture
        if not self._initialized: self.initialize(context)
        w = getattr(context, 'width', 1920); h = getattr(context, 'height', 1080)
        if w != self._w or h != self._h: self._alloc(w, h)

        inputs   = getattr(context, "inputs", {})
        depth_in = inputs.get("depth_in", 0)
        has_d    = 1 if depth_in > 0 else 0

        proj     = float(params.get("projection",    0.8))
        contour  = float(params.get("depth_contour", 0.5))
        uv_scale = float(params.get("uv_scale",      1.0))
        scroll_x = float(params.get("uv_scroll_x",   0.0))
        scroll_y = float(params.get("uv_scroll_y",   0.0))
        n_light  = float(params.get("normal_light",  0.4))
        mask     = float(params.get("mask_tight",    0.6))
        holo     = float(params.get("hologram_glow", 0.3))

        gl.glViewport(0, 0, w, h)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glUseProgram(self.prog)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u("tex0"), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in if has_d else 0)
        gl.glUniform1i(self._u("u_depth_tex"), 1)

        gl.glUniform1i(self._u("has_depth"),    has_d)
        gl.glUniform2f(self._u("resolution"),   float(w), float(h))
        gl.glUniform1f(self._u("projection"),   proj)
        gl.glUniform1f(self._u("depth_contour"),contour)
        gl.glUniform1f(self._u("uv_scale"),     uv_scale)
        gl.glUniform2f(self._u("uv_scroll"),    scroll_x, scroll_y)
        gl.glUniform1f(self._u("normal_light"), n_light)
        gl.glUniform1f(self._u("mask_tight"),   mask)
        gl.glUniform1f(self._u("hologram_glow"),holo)

        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        if hasattr(context, "outputs"): context.outputs["video_out"] = self.tex
        return self.tex

    def cleanup(self) -> None:
        try:
            self._free()
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup error depth_video_projection: {e}")
        finally:
            self.prog = self.empty_vao = 0
