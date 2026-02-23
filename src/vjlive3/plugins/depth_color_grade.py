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
    "name": "DepthColorGrade",
    "version": "3.0.0",
    "description": "Depth-based color grading and correction",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "color",
    "tags": ["depth", "color", "grade", "correction", "atmosphere"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "grade_curve", "type": "str", "default": "linear", "options": ["linear", "smooth", "stepped", "custom"]},
        {"name": "near_color", "type": "list", "default": [1.0, 1.0, 1.0]},
        {"name": "far_color", "type": "list", "default": [0.8, 0.9, 1.0]},
        {"name": "contrast_boost", "type": "float", "default": 0.0, "min": -1.0, "max": 1.0},
        {"name": "saturation_shift", "type": "float", "default": 0.0, "min": -1.0, "max": 1.0},
        {"name": "fog_density", "type": "float", "default": 0.0, "min": 0.0, "max": 1.0},
        {"name": "fog_color", "type": "list", "default": [0.7, 0.8, 1.0]},
        {"name": "transition_point", "type": "float", "default": 0.5, "min": 0.0, "max": 1.0}
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

DEPTH_COLOR_GRADE_FRAGMENT = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform vec2 resolution;

uniform int grade_curve; // 0=linear, 1=smooth, 2=stepped, 3=custom
uniform vec3 near_color;
uniform vec3 far_color;
uniform float contrast_boost;
uniform float saturation_shift;
uniform float fog_density;
uniform vec3 fog_color;
uniform float transition_point;

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0/3.0, 1.0/3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

float get_weight(float depth) {
    if (grade_curve == 1) { // smooth
        return smoothstep(0.0, 1.0, depth);
    } else if (grade_curve == 2) { // stepped
        return step(transition_point, depth);
    } 
    // linear or custom default
    return depth;
}

void main() {
    float depth = texture(depth_tex, uv).r;
    vec3 color = texture(tex0, uv).rgb;
    
    // Depth-lerped grade
    float w = get_weight(depth);
    vec3 grade_mult = mix(near_color, far_color, w);
    color *= grade_mult;
    
    // Saturation shift
    if (saturation_shift != 0.0) {
        vec3 hsv = rgb2hsv(clamp(color, 0.0, 1.0));
        hsv.y = clamp(hsv.y * (1.0 + saturation_shift), 0.0, 1.0);
        color = hsv2rgb(hsv);
    }
    
    // Contrast boost
    if (contrast_boost != 0.0) {
        color = mix(vec3(0.5), color, 1.0 + contrast_boost);
    }
    
    // Exponential fog
    if (fog_density > 0.0) {
        float fog_factor = 1.0 - exp(-depth * fog_density * 4.0); // 4.0 scales local scene space
        color = mix(color, fog_color, clamp(fog_factor, 0.0, 1.0));
    }
    
    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
"""


class DepthColorGradePlugin(EffectPlugin):
    """
    DepthColorGrade plugin port for VJLive3.
    """
    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.out_tex = None
        self.fbo = None
        self.vao = None
        self.vbo = None

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthColorGrade in Mock Mode (No OpenGL)")
            return

        try:
            self._compile_shader()
            self._setup_quad()
            self._setup_fbo(1920, 1080)
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthColorGrade: {e}")
            self._mock_mode = True

    def _compile_shader(self):
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"Vertex Shader Error: {gl.glGetShaderInfoLog(vs)}")

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, DEPTH_COLOR_GRADE_FRAGMENT)
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
        
        curve_map = {"linear": 0, "smooth": 1, "stepped": 2, "custom": 3}
        c_val = curve_map.get(params.get("grade_curve", "linear"), 0)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "grade_curve"), c_val)

        # Parse robust colors avoiding IndexErrors if user supplies empty arrays
        nc = params.get("near_color", [1.0, 1.0, 1.0])
        fc = params.get("far_color", [0.8, 0.9, 1.0])
        foc = params.get("fog_color", [0.7, 0.8, 1.0])
        
        gl.glUniform3f(gl.glGetUniformLocation(self.prog, "near_color"), 
                       nc[0] if len(nc)>0 else 1.0, nc[1] if len(nc)>1 else 1.0, nc[2] if len(nc)>2 else 1.0)
        gl.glUniform3f(gl.glGetUniformLocation(self.prog, "far_color"), 
                       fc[0] if len(fc)>0 else 0.8, fc[1] if len(fc)>1 else 0.9, fc[2] if len(fc)>2 else 1.0)
        gl.glUniform3f(gl.glGetUniformLocation(self.prog, "fog_color"), 
                       foc[0] if len(foc)>0 else 0.7, foc[1] if len(foc)>1 else 0.8, foc[2] if len(foc)>2 else 1.0)

        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "contrast_boost"), float(params.get("contrast_boost", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "saturation_shift"), float(params.get("saturation_shift", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fog_density"), float(params.get("fog_density", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "transition_point"), float(params.get("transition_point", 0.5)))

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        depth_texture = getattr(context, "inputs", {}).get("depth_in", input_texture)
        
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
            logger.error(f"Cleanup Error in DepthColorGrade: {e}")
