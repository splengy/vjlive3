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
    "name": "Depth Slice",
    "description": "Slices video into discrete depth bands with distinct visual treatments.",
    "version": "1.0.0",
    "parameters": [
        {"name": "num_slices", "type": "int", "min": 1, "max": 32, "default": 8, "description": "Number of depth bands"},
        {"name": "slice_thickness", "type": "float", "min": 0.01, "max": 1.0, "default": 0.1, "description": "Thickness of each band"},
        {"name": "color_shift", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5, "description": "Hue shift per slice"},
        {"name": "glitch_amount", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0, "description": "Glitch intensity applied to alternating slices"}
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
uniform int num_slices;
uniform float slice_thickness;
uniform float color_shift;
uniform float glitch_amount;
uniform float time;

// RGB <-> HSV Conversion
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

float hash(float n) { 
    return fract(sin(n) * 43758.5453123); 
}

void main() {
    if (has_depth == 0) {
        fragColor_main = texture(tex0, uv);
        return;
    }
    
    float depth = texture(depth_tex, uv).r;
    if (depth < 0.001) {
        fragColor_main = texture(tex0, uv);
        return;
    }
    
    float scaled_depth = depth * float(num_slices);
    float slice_idx = floor(scaled_depth);
    float slice_pos = fract(scaled_depth);
    
    vec2 current_uv = uv;
    
    // Glitch displacement based on slice index
    if (glitch_amount > 0.0) {
        float time_seed = floor(time * 15.0); // 15 fps flicker
        float glitch_rnd = hash(slice_idx + time_seed);
        if (glitch_rnd < 0.3) {
            float offset = (hash(slice_idx * 1.3 + time_seed) - 0.5) * glitch_amount * 0.15;
            current_uv.x += offset;
        }
    }
    
    vec4 col = texture(tex0, current_uv);
    
    // Topographical slicing
    if (slice_pos < slice_thickness) {
        if (color_shift > 0.0) {
            vec3 hsv = rgb2hsv(col.rgb);
            float shift = (slice_idx / float(num_slices)) * color_shift;
            hsv.x = fract(hsv.x + shift + time * 0.1);
            hsv.y = clamp(hsv.y * 1.5, 0.0, 1.0);
            col.rgb = hsv2rgb(hsv);
        }
    } else {
        // Between slices (dimmed for topographical appearance)
        col.rgb *= 0.2;
    }
    
    fragColor_main = vec4(col.rgb, 1.0);
}
"""

class DepthSlicePlugin(EffectPlugin):
    """Depth Slice Plugin."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.fbo = None
        self.out_tex = None
        self.vao = None
        self.vbo = None
        self.start_time = time.time()

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthSlice in Mock Mode (No OpenGL)")
            return

        try:
            self._compile_shader()
            self._setup_quad()
            self._setup_fbo(1920, 1080)
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthSlice: {e}")
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
        self.out_tex = gl.glGenTextures(1)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.out_tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.out_tex, 0)
        gl.glDrawBuffers(1, [gl.GL_COLOR_ATTACHMENT0])
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

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
        
        # Read parameters efficiently
        num_slices = int(params.get("num_slices", 8))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "num_slices"), num_slices)
        
        s_thick = float(params.get("slice_thickness", 0.1))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "slice_thickness"), s_thick)
        
        c_shift = float(params.get("color_shift", 0.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "color_shift"), c_shift)
        
        glitch = float(params.get("glitch_amount", 0.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "glitch_amount"), glitch)
        
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
            logger.error(f"Cleanup Error in DepthSlice: {e}")
