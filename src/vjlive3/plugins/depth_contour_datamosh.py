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
    "name": "DepthContourDatamosh",
    "version": "3.0.0",
    "description": "Contour-based datamosh using depth edges",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "datamosh",
    "tags": ["depth", "contour", "datamosh", "glitch", "edge"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "contour_threshold", "type": "float", "default": 0.1, "min": 0.01, "max": 0.5},
        {"name": "contour_smoothness", "type": "int", "default": 2, "min": 0, "max": 10},
        {"name": "datamosh_intensity", "type": "float", "default": 0.5, "min": 0.0, "max": 1.0},
        {"name": "fragment_size", "type": "int", "default": 8, "min": 2, "max": 32},
        {"name": "glitch_probability", "type": "float", "default": 0.1, "min": 0.0, "max": 1.0},
        {"name": "preserve_edges", "type": "bool", "default": True},
        {"name": "color_shift", "type": "float", "default": 0.2, "min": 0.0, "max": 1.0}
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

DEPTH_CONTOUR_DATAMOSH_FRAGMENT = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform vec2 resolution;
uniform float time;

uniform float contour_threshold;
uniform int contour_smoothness;
uniform float datamosh_intensity;
uniform int fragment_size;
uniform float glitch_probability;
uniform int preserve_edges;
uniform float color_shift;

// Simple PRNG
float hash12(vec2 p) {
    vec3 p3  = fract(vec3(p.xyx) * .1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

vec2 hash22(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
}

float detect_contour(vec2 p) {
    float dx = 1.0 / resolution.x;
    float dy = 1.0 / resolution.y;
    
    // Multi-tap gradient detection based on contour_smoothness
    int taps = max(1, contour_smoothness);
    float grad_mag = 0.0;
    
    for(int i = 1; i <= taps; i++) {
        float ox = dx * float(i);
        float oy = dy * float(i);
        
        float d1 = texture(depth_tex, p + vec2(ox, 0.0)).r;
        float d2 = texture(depth_tex, p - vec2(ox, 0.0)).r;
        float d3 = texture(depth_tex, p + vec2(0.0, oy)).r;
        float d4 = texture(depth_tex, p - vec2(0.0, oy)).r;
        
        grad_mag += abs(d1 - d2) + abs(d3 - d4);
    }
    
    return step(contour_threshold, grad_mag / float(taps));
}

void main() {
    float depth = texture(depth_tex, uv).r;
    
    // Calculate block coordinates
    vec2 frag_dims = vec2(float(fragment_size)) / resolution;
    vec2 block_uv = floor(uv / frag_dims) * frag_dims;
    
    float contour_active = detect_contour(block_uv);
    
    vec2 sample_uv = uv;
    float chroma_shift = 0.0;
    
    if (contour_active > 0.0 && datamosh_intensity > 0.0 && glitch_probability > 0.0) {
        float glitch_hash = hash12(block_uv + fract(time * 0.1));
        
        if (glitch_hash < glitch_probability) {
            vec2 displacement = (hash22(block_uv + time) - 0.5) * datamosh_intensity * 0.5;
            
            if (preserve_edges == 1) {
                float local_contour = detect_contour(uv);
                displacement *= (1.0 - local_contour);
            }
            
            sample_uv = clamp(uv + displacement, 0.001, 0.999);
            chroma_shift = color_shift * datamosh_intensity * 0.05;
        }
    }
    
    vec4 result = texture(tex0, sample_uv);
    
    if (chroma_shift > 0.0) {
        result.r = texture(tex0, clamp(sample_uv + vec2(chroma_shift, 0.0), 0.0, 1.0)).r;
        result.b = texture(tex0, clamp(sample_uv - vec2(chroma_shift, 0.0), 0.0, 1.0)).b;
    }
    
    fragColor = result;
}
"""


class DepthContourDatamoshPlugin(EffectPlugin):
    """
    DepthContourDatamosh plugin port for VJLive3.
    """
    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.out_tex = None
        self.fbo = None
        self.vao = None
        self.vbo = None
        self.time_val = 0.0

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthContourDatamosh in Mock Mode (No OpenGL)")
            return

        try:
            self._compile_shader()
            self._setup_quad()
            self._setup_fbo(1920, 1080)
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthContourDatamosh: {e}")
            self._mock_mode = True

    def _compile_shader(self):
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"Vertex Shader Error: {gl.glGetShaderInfoLog(vs)}")

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, DEPTH_CONTOUR_DATAMOSH_FRAGMENT)
        gl.glCompileShader(fs)
        if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"Fragment Shader Error: {gl.glGetShaderInfoLog(fs)}")

        self.prog = gl.glCreateProgram()
        gl.glAttachShader(self.prog, vs)
        gl.glAttachShader(self.prog, fs)
        gl.glLinkProgram(self.prog)
        if not gl.glGetProgramiv(self.prog, gl.GL_LINK_STATUS):
            raise RuntimeError(f"Program Link Error: {gl.glGetProgramInfoLog(self.prog)}")
            
        gl.glDeleteShader(vs)
        gl.glDeleteShader(fs)

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

    def _setup_fbo(self, w: int, h: int):
        self.fbo = gl.glGenFramebuffers(1)
        self.out_tex = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.out_tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.out_tex, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _bind_uniforms(self, params: Dict[str, Any], w: int, h: int):
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), float(self.time_val))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "contour_threshold"), float(params.get("contour_threshold", 0.1)))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "contour_smoothness"), int(params.get("contour_smoothness", 2)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "datamosh_intensity"), float(params.get("datamosh_intensity", 0.5)))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "fragment_size"), int(params.get("fragment_size", 8)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "glitch_probability"), float(params.get("glitch_probability", 0.1)))
        
        pe = params.get("preserve_edges", True)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "preserve_edges"), 1 if pe else 0)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "color_shift"), float(params.get("color_shift", 0.2)))

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        depth_texture = getattr(context, "inputs", {}).get("depth_in", input_texture)
        self.time_val += 0.016 # 60fps increments
        
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        gl.glUseProgram(self.prog)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 1)
        
        self._bind_uniforms(params, w, h)
        
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.out_tex
            
        return self.out_tex

    def cleanup(self) -> None:
        if self._mock_mode:
            return
            
        try:
            if self.out_tex:
                gl.glDeleteTextures(1, [self.out_tex])
                self.out_tex = None
            if self.fbo:
                gl.glDeleteFramebuffers(1, [self.fbo])
                self.fbo = None
            if self.vbo:
                gl.glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.vao:
                gl.glDeleteVertexArrays(1, [self.vao])
                self.vao = None
            if self.prog:
                gl.glDeleteProgram(self.prog)
                self.prog = None
        except Exception as e:
            logger.error(f"Cleanup Error in DepthContourDatamosh: {e}")
