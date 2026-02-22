import os
import logging
from typing import Dict, Any, Optional
import numpy as np

from vjlive3.plugins.api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

# Mock GL for headless pytests via environment flag injection
try:
    if os.environ.get("PYTEST_MOCK_GL"):
        raise ImportError("Forced MOCK GL for pytest")
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
    gl = None

DEPTH_AWARE_COMPRESSION_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
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

// Quantize color like JPEG/video compression
vec3 quantize(vec3 color, float levels) {
    return floor(color * levels) / levels;
}

// Get depth-based compression level
float get_depth_compression_level(float depth) {
    float depth_factor = clamp(depth, 0.0, 1.0);
    return pow(depth_factor, artifact_intensity_curve) * depth_compression_ratio;
}

void main() {
    float adjusted_time = time;
    vec2 uv = v_uv;
    vec4 current = texture(tex0, uv);

    // Sample depth
    float depth = texture(depth_tex, uv).r;
    depth = clamp(depth, 0.0, 1.0); // Valid depth range

    // Calculate depth-based compression level
    float compression_level = get_depth_compression_level(depth);

    // Variable block size based on depth and compression level
    float base_block_size = blockSize;
    float depth_block_size = base_block_size + compression_level * block_size_by_depth;
    vec2 block_coord = floor(uv * resolution / max(1.0, depth_block_size));

    // Sample block average (simulates DCT)
    vec2 block_uv = (block_coord + 0.5) * depth_block_size / resolution;
    vec4 block_avg = texture(tex0, block_uv);

    // Quantization levels based on quality and depth compression
    float effective_quality = quality * (1.0 - compression_level);
    float levels = color_quantization + effective_quality * 250.0; // 4-256 levels
    levels = max(levels, 4.0);

    // Apply block quantization
    vec3 quantized = quantize(current.rgb, levels);

    // Mix block color with quantized color based on compression level
    float block_mix = (1.0 - effective_quality) * 0.5 * compression_level;
    quantized = mix(quantized, quantize(block_avg.rgb, levels), block_mix);

    // Add macroblocking noise based on depth layers
    vec2 noise_uv = uv * resolution / max(1.0, depth_block_size);
    float noise = sin(noise_uv.x * 123.456 + noise_uv.y * 789.012 + adjusted_time * 10.0 + depth * 50.0) * 0.02;
    quantized += noise * compression_level * artifact_intensity_curve;

    // Motion-based block corruption
    if (motionBlocks > 0.0 && compression_level > 0.3) {
        // Simulate dropped macroblocks
        float motion_noise = sin(adjusted_time * 20.0 + block_coord.x + block_coord.y) * 0.5 + 0.5;
        if (motion_noise > motionBlocks) {
            // Replace with wrong block
            vec2 wrong_block = block_coord + vec2(sin(adjusted_time * 5.0) * 2.0, cos(adjusted_time * 5.0) * 2.0);
            vec2 wrong_uv = (wrong_block + 0.5) * depth_block_size / resolution;
            vec4 wrong_block_color = texture(tex0, clamp(wrong_uv, vec2(0.0), vec2(1.0)));
            quantized = mix(quantized, quantize(wrong_block_color.rgb, levels * 0.5), 0.3);
        }
    }

    // Depth layer artifacts - add banding based on depth quantization
    if (depth_layers > 1) {
        float depth_step = 3.7 / float(depth_layers); // Total depth range
        float depth_quantized = floor(depth / depth_step) * depth_step;
        float depth_error = abs(depth - depth_quantized) / depth_step;

        // Add banding artifacts
        float banding = sin(uv.y * resolution.y * 0.1 + depth_quantized * 10.0) * 0.01;
        quantized += banding * depth_error * compression_level;
    }

    fragColor = mix(current, vec4(quantized, current.a), u_mix);
}
"""

METADATA = {
    "name": "Depth Aware Compression",
    "description": "Video compression artifacts modulated by depth layers.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["compression", "glitch", "artifacts", "quantization"],
    "status": "active",
    "parameters": [
        {"name": "depthRatio", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "blockDepth", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "intensityCurve", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "depthLayers", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "blockSize", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "quality", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "motionBlocks", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "colorQuantize", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthAwareCompressionPlugin(EffectPlugin):
    """P3-VD27: Depth Aware Compression effect port."""
    
    def __init__(self) -> None:
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.ping_pong = 0
        self.time = 0.0
        
        self.textures: Dict[str, Optional[int]] = {"feedback_0": None, "feedback_1": None}
        self.fbos: Dict[str, Optional[int]] = {"feedback_0": None, "feedback_1": None}

    def _compile_shader(self):
        if not HAS_GL: return None
        try:
            vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
            gl.glShaderSource(vertex, "#version 330 core\\nlayout(location=0) in vec2 pos; layout(location=1) in vec2 uv; out vec2 v_uv; void main() { gl_Position = vec4(pos, 0.0, 1.0); v_uv = uv; }")
            gl.glCompileShader(vertex)
            
            fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fragment, DEPTH_AWARE_COMPRESSION_FRAGMENT)
            gl.glCompileShader(fragment)
            
            if gl.glGetShaderiv(fragment, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
                logger.error(f"Fragment compile failed: {gl.glGetShaderInfoLog(fragment)}")
                return None
                
            prog = gl.glCreateProgram()
            gl.glAttachShader(prog, vertex)
            gl.glAttachShader(prog, fragment)
            gl.glLinkProgram(prog)
            return prog
        except Exception as e:
            logger.error(f"Failed to compile shader locally: {e}")
            return None

    def initialize(self, context: PluginContext) -> None:
        super().initialize(context)
        if self._mock_mode:
            return
            
        try:
            self.prog = self._compile_shader()
            if not self.prog:
                self._mock_mode = True
                return

            tex_ids = gl.glGenTextures(2)
            fbo_ids = gl.glGenFramebuffers(2)
            if isinstance(tex_ids, int): tex_ids = [tex_ids, tex_ids+1]
            if isinstance(fbo_ids, int): fbo_ids = [fbo_ids, fbo_ids+1]
                
            for i, key in enumerate(self.textures.keys()):
                self.textures[key] = tex_ids[i]
                self.fbos[key] = fbo_ids[i]
                
            self.vao = gl.glGenVertexArrays(1)
            self.vbo = gl.glGenBuffers(1)
            gl.glBindVertexArray(self.vao)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
            
            quad_data = np.array([
                -1.0, -1.0,  0.0, 0.0,
                 1.0, -1.0,  1.0, 0.0,
                -1.0,  1.0,  0.0, 1.0,
                 1.0,  1.0,  1.0, 1.0
            ], dtype=np.float32)
            
            gl.glBufferData(gl.GL_ARRAY_BUFFER, quad_data.nbytes, quad_data, gl.GL_STATIC_DRAW)
            gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(0))
            gl.glEnableVertexAttribArray(0)
            gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(8))
            gl.glEnableVertexAttribArray(1)
            gl.glBindVertexArray(0)
            
        except Exception as e:
            logger.warning(f"Failed to initialize GL FBOs inside DepthAwareCompression: {e}")
            self._mock_mode = True

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if input_texture is None or input_texture == 0:
            return 0
            
        self.time += 0.016 # simulate advancing time if not passed
            
        if self._mock_mode:
            context.outputs["video_out"] = input_texture
            return input_texture

        try:
            depth_in = context.inputs.get("depth_in", input_texture) # Fallback to input if missing depth

            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            h = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_HEIGHT)
            
            current_fbo = self.fbos[f"feedback_{1 - self.ping_pong}"]
            current_tex = self.textures[f"feedback_{1 - self.ping_pong}"]
            
            gl.glBindTexture(gl.GL_TEXTURE_2D, current_tex)
            tex_w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            if tex_w != w:
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, current_fbo)
                gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, current_tex, 0)
                
                prev_tex = self.textures[f"feedback_{self.ping_pong}"]
                gl.glBindTexture(gl.GL_TEXTURE_2D, prev_tex)
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, current_fbo)
            gl.glViewport(0, 0, w, h)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            
            gl.glUseProgram(self.prog)
            self._bind_uniforms(params, w, h, context)
            
            # Bind textures
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
            
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.textures[f"feedback_{self.ping_pong}"])
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrev"), 1)
            
            gl.glActiveTexture(gl.GL_TEXTURE2)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 2)
            
            # Draw
            gl.glBindVertexArray(self.vao)
            gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
            gl.glBindVertexArray(0)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            
            self.ping_pong = 1 - self.ping_pong
            context.outputs["video_out"] = current_tex
            return current_tex
            
        except Exception as e:
            logger.error(f"Render failed: {e}")
            return input_texture

    def _map_param(self, params, name, out_min, out_max, default_val):
        val = params.get(name, default_val)
        return out_min + (val / 10.0) * (out_max - out_min)

    def _bind_uniforms(self, params, w, h, context):
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), float(self.time))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), params.get("u_mix", 1.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_compression_ratio"), self._map_param(params, 'depthRatio', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "block_size_by_depth"), self._map_param(params, 'blockDepth', 1.0, 32.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "artifact_intensity_curve"), self._map_param(params, 'intensityCurve', 0.0, 1.0, 5.0))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_layers"), int(self._map_param(params, 'depthLayers', 1.0, 10.0, 3.0)))

        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "blockSize"), self._map_param(params, 'blockSize', 2.0, 64.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "quality"), self._map_param(params, 'quality', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "motionBlocks"), self._map_param(params, 'motionBlocks', 0.0, 1.0, 3.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "color_quantization"), self._map_param(params, 'colorQuantize', 4.0, 256.0, 5.0))


    def cleanup(self) -> None:
        if not self._mock_mode:
            try:
                textures_to_delete = [t for t in self.textures.values() if t is not None]
                if textures_to_delete:
                    gl.glDeleteTextures(len(textures_to_delete), textures_to_delete)
                fbos_to_delete = [f for f in self.fbos.values() if f is not None]
                if fbos_to_delete:
                    gl.glDeleteFramebuffers(len(fbos_to_delete), fbos_to_delete)
                if self.prog:
                    gl.glDeleteProgram(self.prog)
                if hasattr(self, 'vao') and self.vao:
                    gl.glDeleteVertexArrays(1, [self.vao])
                if hasattr(self, 'vbo') and self.vbo:
                    gl.glDeleteBuffers(1, [self.vbo])
            except Exception as e:
                logger.error(f"Error cleaning up FBOs/Textures during DepthAwareCompression unload: {e}")
                
        for k in self.textures:
            self.textures[k] = None
            self.fbos[k] = None

