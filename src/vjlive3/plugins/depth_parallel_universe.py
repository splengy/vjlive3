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
    "name": "Depth Parallel Universe",
    "description": "Splits signal into 3 depth-based universes with independent FX chains.",
    "version": "1.0.0",
    "parameters": [
        {"name": "depth_split_near", "type": "float", "min": 0.0, "max": 1.0, "default": 0.33},
        {"name": "depth_split_far", "type": "float", "min": 0.0, "max": 1.0, "default": 0.66},
        {"name": "universe_a_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "universe_b_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "universe_c_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
    ],
    "inputs": ["video_in", "depth_in", "universe_a_return", "universe_b_return", "universe_c_return"],
    "outputs": ["video_out", "universe_a_send", "universe_b_send", "universe_c_send"]
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
layout(location = 0) out vec4 fragColor_main;
layout(location = 1) out vec4 fragColor_a;
layout(location = 2) out vec4 fragColor_b;
layout(location = 3) out vec4 fragColor_c;

in vec2 uv;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform sampler2D universe_a_return;
uniform sampler2D universe_b_return;
uniform sampler2D universe_c_return;

uniform int has_return_a;
uniform int has_return_b;
uniform int has_return_c;

uniform float time;
uniform vec2 resolution;

uniform float depth_split_near;
uniform float depth_split_far;
uniform float universe_a_intensity;
uniform float universe_b_intensity;
uniform float universe_c_intensity;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(443.897, 441.423))) * 43758.5453);
}

vec4 process_universe_a(vec4 current, vec4 previous, float depth, vec2 p) {
    float block = 20.0;
    vec2 block_uv = floor(p * resolution / block) * block / resolution;
    
    vec4 block_prev = texture(texPrev, block_uv);
    vec3 diff = current.rgb - block_prev.rgb;
    float motion = length(diff);
    
    float block_chaos = hash(block_uv + time);
    vec2 chaos_offset = (vec2(hash(block_uv + 1.1), hash(block_uv + 2.2)) - 0.5);
    chaos_offset *= 0.05;
    
    vec2 displacement = diff.rg * universe_a_intensity * 0.1 + chaos_offset * universe_a_intensity;
    vec2 mosh_uv = clamp(p + displacement, 0.001, 0.999);
    
    vec4 result = texture(texPrev, mosh_uv);
    float blend = smoothstep(0.05, 0.15, motion) * universe_a_intensity;
    
    return mix(current, result, blend);
}

vec4 process_universe_b(vec4 current, vec4 previous, float depth, vec2 p) {
    vec4 blended = mix(current, previous, universe_b_intensity);
    
    vec4 blur_accum = vec4(0.0);
    float blur_radius = universe_b_intensity * 0.05;
    int samples = int(universe_b_intensity * 10.0) + 1;
    
    for (int i = 0; i < 16; i++) {
        if (i >= samples) break;
        float angle = float(i) * 0.3926991;
        float radius = sqrt(float(i) / float(samples)) * blur_radius;
        vec2 offset = vec2(cos(angle), sin(angle)) * radius;
        blur_accum += texture(texPrev, clamp(p + offset, 0.001, 0.999)) / float(samples);
    }
    
    float blend_mult = (samples > 1) ? 0.8 : 0.0;
    return mix(blended, blur_accum, universe_b_intensity * blend_mult);
}

vec4 process_universe_c(vec4 current, vec4 previous, float depth, vec2 p) {
    float glitch_trigger = hash(vec2(floor(time * 5.0), depth));
    
    vec4 result = current;
    
    if (glitch_trigger > 1.0 - universe_c_intensity) {
        vec2 r_offset = vec2(0.02 * universe_c_intensity, 0.0);
        vec2 b_offset = vec2(-0.02 * universe_c_intensity, 0.0);
        
        result.r = texture(tex0, clamp(p + r_offset, 0.001, 0.999)).r;
        result.b = texture(tex0, clamp(p + b_offset, 0.001, 0.999)).b;
        
        float corrupt = hash(p * 100.0 + time);
        if (corrupt > 0.8) {
            result.rgb = mix(result.rgb, vec3(corrupt), universe_c_intensity);
        }
    }
    return result;
}

void main() {
    vec4 current = texture(tex0, uv);
    vec4 previous = texture(texPrev, uv);
    float depth = texture(depth_tex, uv).r;
    
    vec4 uni_a = process_universe_a(current, previous, depth, uv);
    vec4 uni_b = process_universe_b(current, previous, depth, uv);
    vec4 uni_c = process_universe_c(current, previous, depth, uv);
    
    fragColor_a = uni_a;
    fragColor_b = uni_b;
    fragColor_c = uni_c;
    
    if (has_return_a == 1) uni_a = texture(universe_a_return, uv);
    if (has_return_b == 1) uni_b = texture(universe_b_return, uv);
    if (has_return_c == 1) uni_c = texture(universe_c_return, uv);
    
    float safe_far = max(depth_split_near, depth_split_far);
    float safe_near = min(depth_split_near, depth_split_far);
    
    float weight_a = 1.0 - smoothstep(safe_near - 0.1, safe_near + 0.1, depth);
    float weight_b = smoothstep(safe_near - 0.1, safe_near + 0.1, depth) * (1.0 - smoothstep(safe_far - 0.1, safe_far + 0.1, depth));
    float weight_c = smoothstep(safe_far - 0.1, safe_far + 0.1, depth);
    
    float total = weight_a + weight_b + weight_c + 0.001;
    weight_a /= total;
    weight_b /= total;
    weight_c /= total;
    
    fragColor_main = uni_a * weight_a + uni_b * weight_b + uni_c * weight_c;
}
"""

class DepthParallelUniversePlugin(EffectPlugin):
    """Multi-universe routing effect."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.fbo = None
        self.out_textures = []
        self.prev_tex = None
        self.vao = None
        self.vbo = None
        self.start_time = time.time()

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthParallelUniverse in Mock Mode (No OpenGL)")
            return

        try:
            self._compile_shader()
            self._setup_quad()
            self._setup_fbo(1920, 1080)
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthParallelUniverse: {e}")
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

    def _setup_fbo(self, w: int, h: int):
        self.fbo = gl.glGenFramebuffers(1)
        self.out_textures = gl.glGenTextures(4)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        draw_buffers = []
        for i in range(4):
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.out_textures[i])
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            
            attachment = gl.GL_COLOR_ATTACHMENT0 + i
            gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, attachment, gl.GL_TEXTURE_2D, self.out_textures[i], 0)
            draw_buffers.append(attachment)
            
        gl.glDrawBuffers(4, draw_buffers)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        self.prev_tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.prev_tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        inputs = getattr(context, "inputs", {})
        depth_texture = inputs.get("depth_in", input_texture)
        ret_a = inputs.get("universe_a_return", 0)
        ret_b = inputs.get("universe_b_return", 0)
        ret_c = inputs.get("universe_c_return", 0)
        
        # Override values and enforce bounds
        depth_split_near = float(params.get("depth_split_near", 0.33))
        depth_split_far = float(params.get("depth_split_far", 0.66))
        
        # Invert if crossed
        if depth_split_near > depth_split_far:
            depth_split_near, depth_split_far = depth_split_far, depth_split_near

        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
                context.outputs["universe_a_send"] = input_texture
                context.outputs["universe_b_send"] = input_texture
                context.outputs["universe_c_send"] = input_texture
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
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.prev_tex)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrev"), 1)
        
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 2)
        
        gl.glActiveTexture(gl.GL_TEXTURE3)
        gl.glBindTexture(gl.GL_TEXTURE_2D, ret_a)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "universe_a_return"), 3)
        
        gl.glActiveTexture(gl.GL_TEXTURE4)
        gl.glBindTexture(gl.GL_TEXTURE_2D, ret_b)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "universe_b_return"), 4)
        
        gl.glActiveTexture(gl.GL_TEXTURE5)
        gl.glBindTexture(gl.GL_TEXTURE_2D, ret_c)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "universe_c_return"), 5)
        
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_return_a"), 1 if ret_a > 0 else 0)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_return_b"), 1 if ret_b > 0 else 0)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_return_c"), 1 if ret_c > 0 else 0)
        
        current_time = time.time() - self.start_time
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), current_time)
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_split_near"), depth_split_near)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_split_far"), depth_split_far)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_a_intensity"), float(params.get("universe_a_intensity", 0.8)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_b_intensity"), float(params.get("universe_b_intensity", 0.5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_c_intensity"), float(params.get("universe_c_intensity", 0.2)))
        
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        gl.glReadBuffer(gl.GL_COLOR_ATTACHMENT0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.prev_tex)
        gl.glCopyTexSubImage2D(gl.GL_TEXTURE_2D, 0, 0, 0, 0, 0, w, h)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.out_textures[0]
            context.outputs["universe_a_send"] = self.out_textures[1]
            context.outputs["universe_b_send"] = self.out_textures[2]
            context.outputs["universe_c_send"] = self.out_textures[3]
            
        return self.out_textures[0]

    def cleanup(self) -> None:
        if self._mock_mode:
            return
            
        try:
            if len(self.out_textures) > 0:
                gl.glDeleteTextures(len(self.out_textures), self.out_textures)
                self.out_textures = []
            if self.prev_tex:
                gl.glDeleteTextures(1, [self.prev_tex])
                self.prev_tex = None
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
            logger.error(f"Cleanup Error in DepthParallelUniverse: {e}")
