"""
P3-VD73: Depth Echo Effect Plugin for VJLive3.
BOARD entry: "datamosh_3d (DepthEchoEffect)"
No direct legacy source — implementing as a clean depth-modulated multi-echo trail.
Multi-sample temporal accumulation: current depth drives echo intensity per pixel.
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
    "name": "Depth Echo",
    "description": "Depth-modulated temporal echo trails — deeper zones produce longer echoes.",
    "version": "1.0.0",
    "plugin_type": "depth_effect",
    "category": "temporal",
    "tags": ["depth", "echo", "trail", "feedback", "temporal"],
    "priority": 1,
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "echo_strength",   "type": "float", "min": 0.0, "max": 1.0,  "default": 0.8},
        {"name": "decay",           "type": "float", "min": 0.8, "max": 0.99, "default": 0.92},
        {"name": "depth_scale",     "type": "float", "min": 0.0, "max": 2.0,  "default": 1.0},
        {"name": "near_boost",      "type": "float", "min": 0.0, "max": 1.0,  "default": 0.0},
        {"name": "tint_shift",      "type": "float", "min": 0.0, "max": 1.0,  "default": 0.2},
    ]
}

VERTEX_SRC = """
#version 330 core
const vec2 v[4] = vec2[4](vec2(-1,-1),vec2(1,-1),vec2(-1,1),vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(v[gl_VertexID],0,1); uv = v[gl_VertexID]*0.5+0.5; }
"""

ECHO_FRAG = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D u_prev;
uniform sampler2D u_depth_tex;
uniform int has_depth;
uniform float echo_strength;
uniform float decay;
uniform float depth_scale;
uniform float near_boost;
uniform float tint_shift;

void main() {
    vec3 current = texture(tex0, uv).rgb;
    vec3 prev    = texture(u_prev, uv).rgb;

    float depth  = has_depth == 1 ? texture(u_depth_tex, uv).r : 0.5;
    float d_norm = clamp(depth * depth_scale, 0.0, 1.0);

    // Near boost: close objects echo MORE (invert depth)
    float echo_weight = mix(d_norm, 1.0-d_norm, near_boost);
    echo_weight *= echo_strength;

    vec3 echo = prev * decay;
    vec3 tint = mix(vec3(1.0), vec3(0.6, 0.8, 1.0), depth * tint_shift);
    echo *= tint;

    vec3 result = mix(current, max(current, echo), echo_weight);
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


class DepthEchoPlugin(object):
    """Depth Echo — depth-weighted temporal trail accumulation."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = 0; self.empty_vao = 0
        self.fbo_a = self.tex_a = 0
        self.fbo_b = self.tex_b = 0
        self._w = self._h = 0
        self._initialized = False

    def get_metadata(self): return METADATA

    def initialize(self, context) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = _compile(VERTEX_SRC, ECHO_FRAG)
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"depth_echo init failed: {e}")
            self._mock_mode = True; return False

    def _free(self):
        try:
            fbos = [f for f in [self.fbo_a, self.fbo_b] if f]
            texs = [t for t in [self.tex_a, self.tex_b] if t]
            if fbos: gl.glDeleteFramebuffers(len(fbos), fbos)
            if texs: gl.glDeleteTextures(len(texs), texs)
        except Exception: pass
        self.fbo_a = self.tex_a = self.fbo_b = self.tex_b = 0

    def _alloc(self, w, h):
        self._free(); self._w, self._h = w, h
        self.fbo_a, self.tex_a = _make_fbo(w, h)
        self.fbo_b, self.tex_b = _make_fbo(w, h)

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

        gl.glViewport(0, 0, w, h)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_a)
        gl.glUseProgram(self.prog)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u("tex0"), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_b)
        gl.glUniform1i(self._u("u_prev"), 1)
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in if has_d else 0)
        gl.glUniform1i(self._u("u_depth_tex"), 2)

        gl.glUniform1i(self._u("has_depth"),    has_d)
        gl.glUniform1f(self._u("echo_strength"),float(params.get("echo_strength", 0.8)))
        gl.glUniform1f(self._u("decay"),        float(params.get("decay",        0.92)))
        gl.glUniform1f(self._u("depth_scale"),  float(params.get("depth_scale",  1.0)))
        gl.glUniform1f(self._u("near_boost"),   float(params.get("near_boost",   0.0)))
        gl.glUniform1f(self._u("tint_shift"),   float(params.get("tint_shift",   0.2)))

        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        self.fbo_a, self.fbo_b = self.fbo_b, self.fbo_a
        self.tex_a, self.tex_b = self.tex_b, self.tex_a

        if hasattr(context, "outputs"): context.outputs["video_out"] = self.tex_b
        return self.tex_b

    def cleanup(self) -> None:
        try:
            self._free()
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup error depth_echo: {e}")
        finally:
            self.prog = self.empty_vao = 0
