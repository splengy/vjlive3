import numpy as np
import logging
import time

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from typing import Dict, Any
from vjlive3.plugins.api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

METADATA = {
    "name": "Reality Distortion",
    "description": "Quantum reality manipulation via depth-mapped UV distortion.",
    "version": "1.0.0",
    "parameters": [
        {"name": "distortion_amount", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "warp_frequency", "type": "float", "min": 0.0, "max": 10.0, "default": 2.0},
        {"name": "depth_threshold", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "chromatic_aberration", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
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

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv;
out vec4 fragColor_main;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform int has_depth;
uniform float time;

uniform float distortion_amount;
uniform float warp_frequency;
uniform float depth_threshold;
uniform float chromatic_aberration;

// Pseudo-random hash for noise
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

// 2D Noise
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    vec2 u = f*f*(3.0-2.0*f);
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

// Mirroring UVs gracefully beyond boundaries
vec2 safe_uv(vec2 coords) {
    // Triangle wave to fold UVs safely wrapping seamlessly back
    return vec2(1.0) - abs(vec2(1.0) - mod(coords, 2.0));
}

void main() {
    float safe_distortion = clamp(distortion_amount, 0.0, 1.0);
    float safe_freq = clamp(warp_frequency, 0.0, 10.0);
    float safe_thresh = clamp(depth_threshold, 0.0, 1.0);
    float safe_chroma = clamp(chromatic_aberration, 0.0, 1.0);
    
    // Depth isolation scalar
    float multiplier = 1.0;
    if (has_depth == 1) {
        float d = texture(depth_tex, uv).r;
        if (d < safe_thresh && safe_thresh > 0.0) {
            multiplier = 1.0; 
        } else {
            // Logarithmic dropoff outside the threshold mapping
            multiplier = max(0.0, 1.0 - (d - safe_thresh) * 5.0);
        }
    }
    
    // Scale spatial UV deformations
    float nx = noise(uv * safe_freq + time);
    float ny = noise(uv * safe_freq - time);
    
    vec2 displace = vec2(nx - 0.5, ny - 0.5) * safe_distortion * multiplier * 0.2;
    vec2 center_uv = safe_uv(uv + displace);
    
    // Chromatic separation based on proximity map
    vec2 offset_r = displace * safe_chroma * 1.5;
    vec2 offset_b = -displace * safe_chroma * 1.5;
    
    float r = texture(tex0, safe_uv(uv + offset_r)).r;
    float g = texture(tex0, center_uv).g;
    float b = texture(tex0, safe_uv(uv + offset_b)).b;
    
    fragColor_main = vec4(r, g, b, 1.0);
}
"""

class RealityDistortionPlugin(EffectPlugin):
    """Reality Distortion plugin applying spatial warp and chromatic bleeding."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.fbo = None
        self.tex = None
        self.vao = None
        self.vbo = None
        self._width = 0
        self._height = 0
        self.start_time = time.time()

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            logger.warning("Initializing RealityDistortion in Mock Mode (No OpenGL)")
            return

        try:
            self._compile_shader()
            self._setup_quad()
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in RealityDistortion: {e}")
            self._mock_mode = True

    def _compile_shader(self):
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"Vertex Shader Error: {gl.glGetShaderInfoLog(vs)}")

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, FRAGMENT_SHADER)
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

    def _allocate_buffers(self, w: int, h: int):
        self._free_fbo()
        self._width = w
        self._height = h
        
        self.fbo = gl.glGenFramebuffers(1)
        self.tex = gl.glGenTextures(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex)
        
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.tex, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _free_fbo(self):
        try:
            if self.tex:
                gl.glDeleteTextures(1, [self.tex])
                self.tex = None
            if self.fbo:
                gl.glDeleteFramebuffers(1, [self.fbo])
                self.fbo = None
        except Exception as e:
            logger.debug(f"Safely catching cleanup exception on FBO: {e}")

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
             
        inputs = getattr(context, "inputs", {})
        depth_tex = inputs.get("depth_in", 0)
        
        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        if w != self._width or h != self._height:
            self._allocate_buffers(w, h)
            
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        
        gl.glUseProgram(self.prog)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_tex)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 1)
        
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), 1 if depth_tex > 0 else 0)
        
        current_time = time.time() - self.start_time
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), current_time)
        
        # Shader parameters
        distortion = float(params.get("distortion_amount", 0.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "distortion_amount"), distortion)
        
        freq = float(params.get("warp_frequency", 2.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "warp_frequency"), freq)
        
        thresh = float(params.get("depth_threshold", 0.3))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_threshold"), thresh)
        
        chroma = float(params.get("chromatic_aberration", 0.2))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "chromatic_aberration"), chroma)
        
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.tex
            
        return self.tex

    def cleanup(self) -> None:
        if self._mock_mode:
            return
            
        try:
            self._free_fbo()
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
            logger.error(f"Cleanup Error in RealityDistortion: {e}")
