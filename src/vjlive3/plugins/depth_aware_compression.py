import numpy as np
import logging

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from typing import Dict, Any

logger = logging.getLogger(__name__)

METADATA = {
    "name": "Depth Aware Compression",
    "description": "Video compression artifacts modulated by depth layers.",
    "version": "1.0.0",
    "parameters": [
        {"name": "block_size", "type": "float", "min": 1.0, "max": 64.0, "default": 16.0},
        {"name": "quality", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "color_quantization", "type": "float", "min": 2.0, "max": 256.0, "default": 16.0},
        {"name": "depth_compression_ratio", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "block_size_by_depth", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5}
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
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depthTex;

uniform int has_depth;
uniform vec2 resolution;

uniform float block_size;
uniform float quality;
uniform float color_quantization;
uniform float depth_compression_ratio;
uniform float block_size_by_depth;

// Color quantization limiting
vec3 quantize(vec3 color, float levels) {
    if (levels <= 1.0) return color;
    return floor(color * levels) / levels;
}

void main() {
    vec4 current = texture(tex0, uv);

    float depth = 1.0; 
    if (has_depth == 1) {
        depth = clamp(texture(depthTex, uv).r, 0.0, 1.0);
    }
    
    // Calculate effective block size scaling by depth natively securely properly
    float depth_factor = has_depth == 1 ? (depth * depth_compression_ratio) : 1.0;
    float current_block_size = max(block_size + (block_size_by_depth * depth_factor * 64.0), 1.0);
    
    // Macroblocking: pixelate UV map correctly snapping to grid natively
    vec2 block_coord = floor(uv * resolution / current_block_size);
    vec2 block_uv = (block_coord + 0.5) * current_block_size / resolution;
    
    vec4 block_avg = texture(tex0, block_uv);
    
    // Calculate color depth limits natively safely preventing division by 0 natively properly bounds safely
    float effective_quality = clamp(quality * (1.0 - depth_factor), 0.0, 1.0);
    float levels = max(color_quantization + (effective_quality * 200.0), 2.0);
    
    // Quantize base limits gracefully smoothly accurately
    vec3 block_quantized = quantize(block_avg.rgb, levels);
    vec3 sharp_quantized = quantize(current.rgb, max(levels * 2.0, 4.0));
    
    // Mix macro blocks inversely with effective quality
    float block_mix = clamp((1.0 - effective_quality) * depth_factor * 1.5, 0.0, 1.0);
    vec3 result_rgb = mix(sharp_quantized, block_quantized, block_mix);
    
    fragColor = vec4(result_rgb, current.a);
}
"""

class DepthAwareCompressionPlugin(object):
    """Depth Aware Compression mapping discrete scaling artifact arrays securely."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.vao = None
        self.vbo = None
        self.fbo = None
        self.tex = None
        
        self._width = 0
        self._height = 0

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthAwareCompression in Mock Mode")
            return

        try:
            self._compile_shader()
            self._setup_quad()
        except Exception as e:
            logger.error(f"Failed to config OpenGL in DepthAwareCompression: {e}")
            self._mock_mode = True

    def _compile_shader(self):
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(gl.glGetShaderInfoLog(vs))

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, FRAGMENT_SHADER)
        gl.glCompileShader(fs)
        if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(gl.glGetShaderInfoLog(fs))

        self.prog = gl.glCreateProgram()
        gl.glAttachShader(self.prog, vs)
        gl.glAttachShader(self.prog, fs)
        gl.glLinkProgram(self.prog)
        if not gl.glGetProgramiv(self.prog, gl.GL_LINK_STATUS):
            raise RuntimeError(gl.glGetProgramInfoLog(self.prog))
            
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

    def _free_fbo(self):
        try:
            if self.tex is not None:
                gl.glDeleteTextures(1, [self.tex])
            if self.fbo is not None:
                gl.glDeleteFramebuffers(1, [self.fbo])
        except Exception:
            pass
        self.tex = None
        self.fbo = None

    def _allocate_buffer(self, w: int, h: int):
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

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        inputs = getattr(context, "inputs", {})
        depth_in = inputs.get("depth_in", 0)
        
        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        if w != self._width or h != self._height or self.fbo is None:
            self._allocate_buffer(w, h)
            
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glUseProgram(self.prog)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        if depth_in > 0:
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depthTex"), 1)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), 1)
        else:
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), 0)
            
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "block_size"), float(params.get("block_size", 16.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "quality"), float(params.get("quality", 0.5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "color_quantization"), float(params.get("color_quantization", 16.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_compression_ratio"), float(params.get("depth_compression_ratio", 0.8)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "block_size_by_depth"), float(params.get("block_size_by_depth", 0.5)))
        
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
            if self.vbo is not None:
                gl.glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.vao is not None:
                gl.glDeleteVertexArrays(1, [self.vao])
                self.vao = None
            if self.prog is not None:
                gl.glDeleteProgram(self.prog)
                self.prog = None
        except Exception as e:
            logger.error(f"Cleanup Error in DepthAwareCompression: {e}")
