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
    "name": "DepthAwareCompressionEffect",
    "version": "3.0.0",
    "description": "Compress video using depth-based region segmentation",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "compression",
    "tags": ["depth", "compression", "efficiency", "quality"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "compression_ratio", "type": "float", "default": 0.5, "min": 0.1, "max": 0.9},
        {"name": "depth_threshold", "type": "float", "default": 0.1, "min": 0.01, "max": 0.5},
        {"name": "block_size", "type": "int", "default": 8, "min": 4, "max": 32},
        {"name": "quality_preserve_edges", "type": "bool", "default": True},
        {"name": "adaptive_quality", "type": "bool", "default": True},
        {"name": "preserve_foreground", "type": "float", "default": 0.8, "min": 0.0, "max": 1.0},
        
        # Legacy mappings
        {"name": "depthRatio", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "blockDepth", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "intensityCurve", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "depthLayers", "type": "float", "default": 3.0, "min": 1.0, "max": 10.0},
        {"name": "blockSize_legacy", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "quality", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "motionBlocks", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "colorQuantize", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "u_mix", "type": "float", "default": 1.0, "min": 0.0, "max": 1.0}
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

DEPTH_AWARE_COMPRESSION_FRAGMENT = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Compression parameters modulated by depth
uniform float depth_compression_ratio;
uniform float block_size_by_depth;
uniform float artifact_intensity_curve;
uniform int depth_layers;

// Standard compression parameters
uniform float blockSize;     // Base DCT block size
uniform float quality;       // Base compression quality
uniform float motionBlocks;  // Motion block glitching
uniform float color_quantization; // Color levels

// VJLive3 spec parameters
uniform float compression_ratio;
uniform float depth_threshold;
uniform int block_size_spec;
uniform bool quality_preserve_edges;
uniform bool adaptive_quality;
uniform float preserve_foreground;

// Quantize color like JPEG/video compression
vec3 quantize(vec3 color, float levels) {
    return floor(color * levels) / levels;
}

// Get depth-based compression level
float get_depth_compression_level(float depth) {
    float depth_factor = clamp(depth, 0.0, 1.0);
    
    // Legacy calculation
    float legacy_level = pow(depth_factor, artifact_intensity_curve) * depth_compression_ratio;
    
    // New Adaptive depth scaling (assuming small depth = foreground)
    float new_level = 0.0;
    if (adaptive_quality) {
        float distance = depth; 
        new_level = distance * compression_ratio * (1.0 - preserve_foreground);
    } else {
        new_level = compression_ratio;
    }
    
    return mix(new_level, legacy_level, 0.5);
}

void main() {
    vec4 current = texture(tex0, uv);
    float depth = texture(depth_tex, uv).r;
    depth = clamp(depth, 0.0, 1.0);

    float compression_level = get_depth_compression_level(depth);

    // Edge Detection (Sobel-ish variant)
    float edge_protection = 0.0;
    if (quality_preserve_edges) {
        float dx = abs(texture(depth_tex, uv + vec2(1.0/resolution.x, 0.0)).r - depth);
        float dy = abs(texture(depth_tex, uv + vec2(0.0, 1.0/resolution.y)).r - depth);
        float max_grad = max(dx, dy);
        
        if (max_grad > depth_threshold) {
             edge_protection = 1.0; 
        }
    }
    
    // Preserve edges by decreasing local compression level
    compression_level *= (1.0 - edge_protection);

    // Variable block size based on depth and compression
    float base_block_size = float(block_size_spec) * 0.5 + blockSize;
    float depth_block_size = base_block_size + compression_level * block_size_by_depth;
    
    // Safety clamp
    depth_block_size = max(1.0, depth_block_size);
    vec2 block_coord = floor(uv * resolution / depth_block_size);

    vec2 block_uv = (block_coord + 0.5) * depth_block_size / resolution;
    vec4 block_avg = texture(tex0, block_uv);

    // Quantization levels based on combined quality
    float effective_quality = quality * (1.0 - compression_level);
    float levels = color_quantization + effective_quality * 250.0;
    levels = max(levels, 4.0);

    vec3 quantized = quantize(current.rgb, levels);

    // Mix color block
    float block_mix = (1.0 - effective_quality) * 0.5 * compression_level;
    quantized = mix(quantized, quantize(block_avg.rgb, levels), block_mix);

    // Micro noise artifact injection
    vec2 noise_uv = uv * resolution / depth_block_size;
    float noise = sin(noise_uv.x * 123.456 + noise_uv.y * 789.012 + time * 10.0 + depth * 50.0) * 0.02;
    quantized += noise * compression_level * artifact_intensity_curve;

    // Macroblock dropout (motion)
    if (motionBlocks > 0.0 && compression_level > 0.3) {
        float motion_noise = sin(time * 20.0 + block_coord.x + block_coord.y) * 0.5 + 0.5;
        if (motion_noise > motionBlocks) {
            vec2 wrong_block = block_coord + vec2(sin(time * 5.0) * 2.0, cos(time * 5.0) * 2.0);
            vec2 wrong_uv = (wrong_block + 0.5) * depth_block_size / resolution;
            vec4 wrong_block_color = texture(tex0, clamp(wrong_uv, vec2(0.0), vec2(1.0)));
            quantized = mix(quantized, quantize(wrong_block_color.rgb, levels * 0.5), 0.3);
        }
    }

    if (depth_layers > 1) {
        float depth_step = 3.7 / float(depth_layers);
        float depth_quantized = floor(depth / depth_step) * depth_step;
        float depth_error = abs(depth - depth_quantized) / depth_step;
        float banding = sin(uv.y * resolution.y * 0.1 + depth_quantized * 10.0) * 0.01;
        quantized += banding * depth_error * compression_level;
    }

    fragColor = mix(current, vec4(quantized, current.a), u_mix);
}
"""

class DepthAwareCompressionPlugin(EffectPlugin):
    """
    DepthAwareCompressionEffect plugin port.
    Compresses video based on depth, matching VJLive3 spec parameters.
    """
    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.out_tex = None
        self.fbo = None
        self.vao = None
        self.vbo = None
        self.time = 0.0

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            logger.warning("Mock Mode - Skipping GL setup")
            return

        try:
            self._compile_shader()
            self._setup_quad()
            self._setup_fbo(1920, 1080)
        except Exception as e:
            logger.error(f"GL Error: {e}")
            self._mock_mode = True

    def _compile_shader(self):
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"VS Error: {gl.glGetShaderInfoLog(vs)}")

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, DEPTH_AWARE_COMPRESSION_FRAGMENT)
        gl.glCompileShader(fs)
        if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"FS Error: {gl.glGetShaderInfoLog(fs)}")

        self.prog = gl.glCreateProgram()
        gl.glAttachShader(self.prog, vs)
        gl.glAttachShader(self.prog, fs)
        gl.glLinkProgram(self.prog)
        if not gl.glGetProgramiv(self.prog, gl.GL_LINK_STATUS):
            raise RuntimeError(f"Link Error: {gl.glGetProgramInfoLog(self.prog)}")
            
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
        def map_p(key, max_val=1.0):
            idx = [x["name"] for x in METADATA["parameters"]].index(key)
            default = METADATA["parameters"][idx]["default"]
            v = params.get(key, default)
            return (v / 10.0) * max_val

        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), self.time)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), params.get("u_mix", 1.0))
        
        # New spec params
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "compression_ratio"), params.get("compression_ratio", 0.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_threshold"), params.get("depth_threshold", 0.1))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "block_size_spec"), int(params.get("block_size", 8)))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "quality_preserve_edges"), int(params.get("quality_preserve_edges", True)))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "adaptive_quality"), int(params.get("adaptive_quality", True)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "preserve_foreground"), params.get("preserve_foreground", 0.8))

        # Legacy mapped params
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_compression_ratio"), map_p("depthRatio", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "block_size_by_depth"), map_p("blockDepth", 32.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "artifact_intensity_curve"), map_p("intensityCurve", 1.0))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_layers"), int(map_p("depthLayers", 10.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "blockSize"), map_p("blockSize_legacy", 64.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "quality"), map_p("quality", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "motionBlocks"), map_p("motionBlocks", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "color_quantization"), map_p("colorQuantize", 256.0))

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        # Fallback to input_texture if depth is missing
        depth_texture = getattr(context, "inputs", {}).get("depth_in", input_texture)
        
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        self.time += context.delta_time
        
        w, h = 1920, 1080
        
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
            logger.error(f"Cleanup Error: {e}")
