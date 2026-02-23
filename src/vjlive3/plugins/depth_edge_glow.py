import numpy as np
import logging

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from typing import Dict, Any
from vjlive3.plugins.api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

METADATA = {
    "name": "DepthEdgeGlow",
    "version": "3.0.0",
    "description": "Glow effects on depth edges using separable blur",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "glow",
    "tags": ["depth", "edge", "glow", "rim", "highlight"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "glow_intensity", "type": "float", "default": 0.5, "min": 0.0, "max": 2.0},
        {"name": "glow_radius", "type": "int", "default": 3, "min": 1, "max": 15},
        {"name": "edge_threshold", "type": "float", "default": 0.1, "min": 0.01, "max": 0.5},
        {"name": "glow_color", "type": "list", "default": [1.0, 0.8, 0.2]},
        {"name": "glow_falloff", "type": "str", "default": "linear", "options": ["linear", "exponential", "gaussian"]},
        {"name": "glow_only", "type": "bool", "default": False},
        {"name": "edge_smoothness", "type": "int", "default": 2, "min": 0, "max": 5}
    ]
}

VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 position;
layout(location = 1) in vec2 texcoord;
out vec2 uv;
void main() {
    uv = texcoord;
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

EDGE_FRAGMENT_SHADER = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D depth_tex;
uniform vec2 resolution;
uniform float edge_threshold;
uniform int edge_smoothness;

void main() {
    float t_x = 1.0 / resolution.x;
    float t_y = 1.0 / resolution.y;
    
    // Sobel operator
    float tl = texture(depth_tex, uv + vec2(-t_x, -t_y)).r;
    float tc = texture(depth_tex, uv + vec2( 0.0, -t_y)).r;
    float tr = texture(depth_tex, uv + vec2( t_x, -t_y)).r;
    float ml = texture(depth_tex, uv + vec2(-t_x,  0.0)).r;
    float mr = texture(depth_tex, uv + vec2( t_x,  0.0)).r;
    float bl = texture(depth_tex, uv + vec2(-t_x,  t_y)).r;
    float bc = texture(depth_tex, uv + vec2( 0.0,  t_y)).r;
    float br = texture(depth_tex, uv + vec2( t_x,  t_y)).r;

    float gx = -tl - 2.0*ml - bl + tr + 2.0*mr + br;
    float gy = -tl - 2.0*tc - tr + bl + 2.0*bc + br;
    float edge = sqrt(gx*gx + gy*gy);
    
    float smooth_span = max(0.01, float(edge_smoothness) * 0.02);
    edge = smoothstep(edge_threshold - smooth_span, edge_threshold + smooth_span, edge);
    
    fragColor = vec4(edge, edge, edge, 1.0);
}
"""

BLUR_H_FRAGMENT_SHADER = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex_in;
uniform vec2 resolution;
uniform int glow_radius;
uniform int glow_falloff; // 0=linear, 1=exponential, 2=gaussian

float get_weight(float offset, float radius) {
    if (radius <= 0.0) return 0.0;
    float x = abs(offset) / radius;
    if (x > 1.0) return 0.0;
    
    if (glow_falloff == 0) return 1.0 - x;
    if (glow_falloff == 1) return exp(-x * 3.0);
    if (glow_falloff == 2) return exp(-(x*x) * 4.0);
    
    return 1.0;
}

void main() {
    float sum_edge = 0.0;
    float sum_weight = 0.0;
    float t_x = 1.0 / resolution.x;
    
    for(int x = -glow_radius; x <= glow_radius; x++) {
        float w = get_weight(float(x), float(glow_radius));
        if (w > 0.0) {
            sum_edge += texture(tex_in, clamp(uv + vec2(float(x) * t_x, 0.0), 0.0, 1.0)).r * w;
            sum_weight += w;
        }
    }
    
    float final_edge = (sum_weight > 0.0) ? (sum_edge / sum_weight) : texture(tex_in, uv).r;
    fragColor = vec4(final_edge, final_edge, final_edge, 1.0);
}
"""

BLUR_V_COMP_FRAGMENT_SHADER = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D tex_in;
uniform vec2 resolution;

uniform int glow_radius;
uniform int glow_falloff; // 0=linear, 1=exponential, 2=gaussian
uniform float glow_intensity;
uniform vec3 glow_color;
uniform bool glow_only;

float get_weight(float offset, float radius) {
    if (radius <= 0.0) return 0.0;
    float x = abs(offset) / radius;
    if (x > 1.0) return 0.0;
    
    if (glow_falloff == 0) return 1.0 - x;
    if (glow_falloff == 1) return exp(-x * 3.0);
    if (glow_falloff == 2) return exp(-(x*x) * 4.0);
    
    return 1.0;
}

void main() {
    float sum_edge = 0.0;
    float sum_weight = 0.0;
    float t_y = 1.0 / resolution.y;
    
    for(int y = -glow_radius; y <= glow_radius; y++) {
        float w = get_weight(float(y), float(glow_radius));
        if (w > 0.0) {
            sum_edge += texture(tex_in, clamp(uv + vec2(0.0, float(y) * t_y), 0.0, 1.0)).r * w;
            sum_weight += w;
        }
    }
    
    float final_edge = (sum_weight > 0.0) ? (sum_edge / sum_weight) : texture(tex_in, uv).r;
    
    vec4 source = texture(tex0, uv);
    vec3 glow_pixel = glow_color * final_edge * glow_intensity * 2.0; 
    
    if (glow_only) {
        fragColor = vec4(clamp(glow_pixel, 0.0, 1.0), 1.0);
    } else {
        vec3 comp = source.rgb + glow_pixel;
        fragColor = vec4(clamp(comp, 0.0, 1.0), 1.0);
    }
}
"""


class DepthEdgeGlowPlugin(EffectPlugin):
    """
    DepthEdgeGlow compositing node for VJLive3.
    Replaces brute force O(N^2) 2D loop with a highly scalable 3-Pass Separable kernel array retaining native 60 FPS speeds.
    """
    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog_edge = None
        self.prog_blur_h = None
        self.prog_blur_v = None
        
        self.fbo_edge = None
        self.tex_edge = None
        self.fbo_blur_h = None
        self.tex_blur_h = None
        
        self.fbo_out = None
        self.tex_out = None
        
        self.vao = None
        self.vbo = None

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            return

        try:
            self._compile_shaders()
            self._setup_quad()
            w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
            self.fbo_edge, self.tex_edge = self._create_fbo(w, h)
            self.fbo_blur_h, self.tex_blur_h = self._create_fbo(w, h)
            self.fbo_out, self.tex_out = self._create_fbo(w, h)
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthEdgeGlow: {e}")
            self._mock_mode = True

    def _compile_program(self, fs_source: str) -> int:
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, fs_source)
        gl.glCompileShader(fs)
        
        if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"FS Error: {gl.glGetShaderInfoLog(fs)}")

        prog = gl.glCreateProgram()
        gl.glAttachShader(prog, vs)
        gl.glAttachShader(prog, fs)
        gl.glLinkProgram(prog)
        
        gl.glDeleteShader(vs)
        gl.glDeleteShader(fs)
        return prog

    def _compile_shaders(self):
        self.prog_edge = self._compile_program(EDGE_FRAGMENT_SHADER)
        self.prog_blur_h = self._compile_program(BLUR_H_FRAGMENT_SHADER)
        self.prog_blur_v = self._compile_program(BLUR_V_COMP_FRAGMENT_SHADER)

    def _create_fbo(self, w: int, h: int) -> tuple[int, int]:
        fbo = gl.glGenFramebuffers(1)
        tex = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        return fbo, tex

    def _setup_quad(self):
        vertices = np.array([
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 1.0,
             1.0,  1.0,  1.0, 1.0,
        ], dtype=np.float32)
        
        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        
        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
        
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(8))
        gl.glBindVertexArray(0)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        depth_texture = getattr(context, "inputs", {}).get("depth_in", input_texture)
        
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        gl.glViewport(0, 0, w, h)
        gl.glBindVertexArray(self.vao)
        
        # Mapping Parameters
        e_thresh = float(params.get("edge_threshold", 0.1))
        e_smooth = int(params.get("edge_smoothness", 2))
        g_rad = int(params.get("glow_radius", 3))
        g_int = float(params.get("glow_intensity", 0.5))
        g_color = params.get("glow_color", [1.0, 0.8, 0.2])
        if not isinstance(g_color, list) or len(g_color) < 3: g_color = [1.0, 0.8, 0.2]
        
        falloff_str = params.get("glow_falloff", "linear")
        falloff_idx = 0
        if falloff_str == "exponential": falloff_idx = 1
        elif falloff_str == "gaussian": falloff_idx = 2
        
        glow_only = 1 if params.get("glow_only", False) else 0

        # PASS 1: Edge Detection (depth_tex -> tex_edge)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_edge)
        gl.glUseProgram(self.prog_edge)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_edge, "depth_tex"), 0)
        gl.glUniform2f(gl.glGetUniformLocation(self.prog_edge, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_edge, "edge_threshold"), e_thresh)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_edge, "edge_smoothness"), e_smooth)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)

        # PASS 2: Horizontal Blur (tex_edge -> tex_blur_h)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_blur_h)
        gl.glUseProgram(self.prog_blur_h)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_edge)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_blur_h, "tex_in"), 0)
        gl.glUniform2f(gl.glGetUniformLocation(self.prog_blur_h, "resolution"), float(w), float(h))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_blur_h, "glow_radius"), g_rad)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_blur_h, "glow_falloff"), falloff_idx)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)

        # PASS 3: Vertical Blur & Composite (tex_blur_h + tex0 -> tex_out)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_out)
        gl.glUseProgram(self.prog_blur_v)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_blur_v, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_blur_h)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_blur_v, "tex_in"), 1)
        
        gl.glUniform2f(gl.glGetUniformLocation(self.prog_blur_v, "resolution"), float(w), float(h))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_blur_v, "glow_radius"), g_rad)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_blur_v, "glow_falloff"), falloff_idx)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_blur_v, "glow_intensity"), g_int)
        gl.glUniform3f(gl.glGetUniformLocation(self.prog_blur_v, "glow_color"), float(g_color[0]), float(g_color[1]), float(g_color[2]))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_blur_v, "glow_only"), glow_only)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        
        # Reset and output
        gl.glBindVertexArray(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.tex_out
            
        return self.tex_out

    def cleanup(self) -> None:
        if self._mock_mode:
            return
            
        try:
            # Delete output FBO
            if self.tex_out: gl.glDeleteTextures(1, [self.tex_out])
            if self.fbo_out: gl.glDeleteFramebuffers(1, [self.fbo_out])
            self.tex_out, self.fbo_out = None, None
            
            # Delete blur FBO
            if self.tex_blur_h: gl.glDeleteTextures(1, [self.tex_blur_h])
            if self.fbo_blur_h: gl.glDeleteFramebuffers(1, [self.fbo_blur_h])
            self.tex_blur_h, self.fbo_blur_h = None, None
            
            # Delete edge FBO
            if self.tex_edge: gl.glDeleteTextures(1, [self.tex_edge])
            if self.fbo_edge: gl.glDeleteFramebuffers(1, [self.fbo_edge])
            self.tex_edge, self.fbo_edge = None, None

            # Delete geometry
            if self.vbo: gl.glDeleteBuffers(1, [self.vbo])
            if self.vao: gl.glDeleteVertexArrays(1, [self.vao])
            self.vbo, self.vao = None, None
            
            # Delete programs
            if self.prog_edge: gl.glDeleteProgram(self.prog_edge)
            if self.prog_blur_h: gl.glDeleteProgram(self.prog_blur_h)
            if self.prog_blur_v: gl.glDeleteProgram(self.prog_blur_v)
            self.prog_edge, self.prog_blur_h, self.prog_blur_v = None, None, None
        except Exception as e:
            logger.error(f"Cleanup Error in DepthEdgeGlow: {e}")
