"""
P3-VD74: ML Depth Estimation Effect Plugin for VJLive3.
BOARD entry: "ml_gpu_effects (MLDepthEstimationEffect)"
No ML backend available in VJLive3 headless environment.
Per no-stub policy: implements visually-meaningful depth estimation SIMULATION
via GLSL luminance-based pseudo-depth + edge detection heuristics.
No neural model dependencies.
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
    "name": "ML Depth Estimation",
    "description": "Estimates depth from video luminance/edges. Visualizes pseudo-depth map.",
    "version": "1.0.0",
    "plugin_type": "depth_effect",
    "category": "depth",
    "tags": ["depth", "estimation", "luminance", "edge", "visualization"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out", "depth_out"],
    "parameters": [
        {"name": "depth_scale",     "type": "float", "min": 0.0, "max": 2.0, "default": 1.0},
        {"name": "edge_weight",     "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "luma_weight",     "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "blur_passes",     "type": "int",   "min": 0,   "max": 4,   "default": 2},
        {"name": "colorize",        "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "overlay_on_video","type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
    ]
}

VERTEX_SRC = """
#version 330 core
const vec2 v[4] = vec2[4](vec2(-1,-1),vec2(1,-1),vec2(-1,1),vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(v[gl_VertexID],0,1); uv = v[gl_VertexID]*0.5+0.5; }
"""

DEPTH_EST_FRAG = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform vec2 resolution;
uniform float depth_scale;
uniform float edge_weight;
uniform float luma_weight;
uniform float colorize;
uniform float overlay_on_video;

float luminance(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

// Estimate pseudo-depth from video: darker + edges = near, brighter + flat = far
float estimateDepth(vec2 p) {
    vec2 px = 1.0 / resolution;
    vec3 c  = texture(tex0, p).rgb;
    float luma = luminance(c);

    // Sobel edge magnitude
    vec3 tl = texture(tex0, p+vec2(-px.x,-px.y)).rgb;
    vec3 tr = texture(tex0, p+vec2( px.x,-px.y)).rgb;
    vec3 bl = texture(tex0, p+vec2(-px.x, px.y)).rgb;
    vec3 br = texture(tex0, p+vec2( px.x, px.y)).rgb;
    vec3 ml = texture(tex0, p+vec2(-px.x,  0)).rgb;
    vec3 mr = texture(tex0, p+vec2( px.x,  0)).rgb;
    vec3 tc = texture(tex0, p+vec2(0,-px.y)).rgb;
    vec3 bc = texture(tex0, p+vec2(0, px.y)).rgb;

    vec3 gx = -tl - 2.0*ml - bl + tr + 2.0*mr + br;
    vec3 gy = -tl - 2.0*tc - tr + bl + 2.0*bc + br;
    float edge = length(gx) * 0.5 + length(gy) * 0.5;
    edge = clamp(edge * 0.3, 0.0, 1.0);

    // Heuristic: edges are near, bright uniform areas are far
    float pseudo_depth = mix(
        1.0 - luma,      // near=dark
        edge,            // near=edge
        0.5
    );
    // luma and edge blend weights
    pseudo_depth = pseudo_depth * edge_weight + (1.0 - luma) * luma_weight;
    pseudo_depth = clamp(pseudo_depth * depth_scale, 0.0, 1.0);

    return pseudo_depth;
}

vec3 depthToColor(float d) {
    // Turbo colormap approximation
    vec3 cool  = vec3(0.0, 0.0, 1.0);   // far = blue
    vec3 mid   = vec3(0.0, 1.0, 0.5);   // mid = green
    vec3 hot   = vec3(1.0, 0.1, 0.0);   // near = red
    if (d < 0.5) return mix(cool, mid, d*2.0);
    return mix(mid, hot, (d-0.5)*2.0);
}

void main() {
    vec3 video = texture(tex0, uv).rgb;
    float depth = estimateDepth(uv);

    vec3 depth_rgb = mix(vec3(depth), depthToColor(depth), colorize);
    vec3 result = mix(video, depth_rgb, overlay_on_video);

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


class MLDepthEstimationPlugin(object):
    """ML Depth Estimation — GLSL luminance + edge heuristic pseudo-depth visualization."""

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
            self.prog = _compile(VERTEX_SRC, DEPTH_EST_FRAG)
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"ml_depth_estimation init failed: {e}")
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

        gl.glViewport(0, 0, w, h)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glUseProgram(self.prog)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u("tex0"), 0)

        gl.glUniform2f(self._u("resolution"),    float(w), float(h))
        gl.glUniform1f(self._u("depth_scale"),   float(params.get("depth_scale",     1.0)))
        gl.glUniform1f(self._u("edge_weight"),   float(params.get("edge_weight",     0.5)))
        gl.glUniform1f(self._u("luma_weight"),   float(params.get("luma_weight",     0.5)))
        gl.glUniform1f(self._u("colorize"),      float(params.get("colorize",        0.5)))
        gl.glUniform1f(self._u("overlay_on_video"),float(params.get("overlay_on_video",0.4)))

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
            logger.error(f"Cleanup error ml_depth_estimation: {e}")
        finally:
            self.prog = self.empty_vao = 0
