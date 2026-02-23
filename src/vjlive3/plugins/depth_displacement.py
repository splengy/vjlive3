"""
P3-VD72: Depth Displacement Effect Plugin for VJLive3.
BOARD entry: "datamosh_3d (DepthDisplacementEffect)"
No direct legacy source — implementing as a clean depth-driven UV displacement map.
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
    "name": "Depth Displacement",
    "description": "Depth map drives UV displacement — near objects warp texture space.",
    "version": "1.0.0",
    "plugin_type": "depth_effect",
    "category": "displacement",
    "tags": ["depth", "displacement", "UV", "warp", "refraction"],
    "priority": 1,
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "displace_scale",  "type": "float", "min": 0.0, "max": 0.2, "default": 0.05},
        {"name": "depth_invert",    "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "displace_x",     "type": "float", "min":-1.0, "max": 1.0, "default": 1.0},
        {"name": "displace_y",     "type": "float", "min":-1.0, "max": 1.0, "default": 1.0},
        {"name": "edge_detect",    "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "chromatic",      "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
    ]
}

VERTEX_SRC = """
#version 330 core
const vec2 v[4] = vec2[4](vec2(-1,-1),vec2(1,-1),vec2(-1,1),vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(v[gl_VertexID],0,1); uv = v[gl_VertexID]*0.5+0.5; }
"""

DISPLACE_FRAG = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D u_depth_tex;
uniform int has_depth;
uniform vec2  resolution;
uniform float displace_scale;
uniform float depth_invert;
uniform vec2  displace_dir;
uniform float edge_detect;
uniform float chromatic;

void main() {
    vec3 video = texture(tex0, uv).rgb;
    if (has_depth == 0) { fragColor = vec4(video, 1.0); return; }

    float depth = texture(u_depth_tex, uv).r;
    if (depth_invert > 0.5) depth = 1.0 - depth;

    // Edge detection via Sobel on depth
    vec2 px = 1.0 / resolution;
    float dl = texture(u_depth_tex, uv + vec2(-px.x, 0)).r;
    float dr = texture(u_depth_tex, uv + vec2( px.x, 0)).r;
    float du = texture(u_depth_tex, uv + vec2(0, -px.y)).r;
    float dd = texture(u_depth_tex, uv + vec2(0,  px.y)).r;
    float edge = length(vec2(dr-dl, dd-du)) * edge_detect * 5.0;

    // UV displacement
    vec2 disp = displace_dir * depth * displace_scale;
    disp += vec2(dr-dl, dd-du) * edge_detect * displace_scale * 0.5;

    vec2 displaced = clamp(uv + disp, 0.0, 1.0);

    vec3 color;
    if (chromatic > 0.01) {
        vec2 ch = disp * chromatic;
        color.r = texture(tex0, clamp(displaced + ch, 0.0, 1.0)).r;
        color.g = texture(tex0, displaced).g;
        color.b = texture(tex0, clamp(displaced - ch, 0.0, 1.0)).b;
    } else {
        color = texture(tex0, displaced).rgb;
    }

    // Bright edge flash
    color += vec3(edge) * 0.2;

    fragColor = vec4(color, 1.0);
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


class DepthDisplacementPlugin(object):
    """Depth Displacement — depth as UV displacement map with chromatic aberration."""

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
            self.prog = _compile(VERTEX_SRC, DISPLACE_FRAG)
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"depth_displacement init failed: {e}")
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

        gl.glViewport(0, 0, w, h)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glUseProgram(self.prog)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u("tex0"), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in if has_d else 0)
        gl.glUniform1i(self._u("u_depth_tex"), 1)

        gl.glUniform1i(self._u("has_depth"),       has_d)
        gl.glUniform2f(self._u("resolution"),      float(w), float(h))
        gl.glUniform1f(self._u("displace_scale"),  float(params.get("displace_scale", 0.05)))
        gl.glUniform1f(self._u("depth_invert"),    float(params.get("depth_invert",   0.0)))
        gl.glUniform2f(self._u("displace_dir"),    float(params.get("displace_x", 1.0)),
                                                    float(params.get("displace_y", 1.0)))
        gl.glUniform1f(self._u("edge_detect"),     float(params.get("edge_detect", 0.5)))
        gl.glUniform1f(self._u("chromatic"),       float(params.get("chromatic",   0.3)))

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
            logger.error(f"Cleanup error depth_displacement: {e}")
        finally:
            self.prog = self.empty_vao = 0
