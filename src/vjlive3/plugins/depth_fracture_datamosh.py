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
    "name": "Depth Fracture Datamosh",
    "description": "Shattered glass datamosh driven by depth discontinuities.",
    "version": "1.0.0",
    "parameters": [
        {"name": "fracture_sensitivity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.1, "description": "Edge detection threshold"},
        {"name": "fracture_width", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "fracture_decay", "type": "float", "min": 0.0, "max": 1.0, "default": 0.95, "description": "Temporal persistence of cracks"},
        {"name": "bleed_amount", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5, "description": "How far datamosh bleeds from cracks"},
        {"name": "displacement_strength", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5}
    ],
    "inputs": ["video_in", "video_b_in", "depth_in"],
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
uniform sampler2D tex1;
uniform sampler2D texPrev;
uniform sampler2D depthTex;

uniform int has_depth;
uniform int has_video_b;
uniform vec2 resolution;

uniform float fracture_sensitivity;
uniform float fracture_width;
uniform float fracture_decay;
uniform float bleed_amount;
uniform float displacement_strength;

// Simplified edge detection
float depth_edge(vec2 p, float radius) {
    vec2 texel = vec2(radius / resolution.x, radius / resolution.y);
    float c = texture(depthTex, p).r;
    float l = texture(depthTex, p + vec2(-texel.x, 0.0)).r;
    float r = texture(depthTex, p + vec2( texel.x, 0.0)).r;
    float u = texture(depthTex, p + vec2(0.0, texel.y)).r;
    float d = texture(depthTex, p + vec2(0.0, -texel.y)).r;
    float edge = abs(l - r) + abs(u - d);
    return edge;
}

vec2 depth_gradient(vec2 p, float radius) {
    vec2 texel = vec2(radius / resolution.x, radius / resolution.y);
    float dx = texture(depthTex, p + vec2(texel.x, 0.0)).r - texture(depthTex, p - vec2(texel.x, 0.0)).r;
    float dy = texture(depthTex, p + vec2(0.0, texel.y)).r - texture(depthTex, p - vec2(0.0, texel.y)).r;
    return vec2(dx, dy);
}

void main() {
    if (has_depth == 0) {
        fragColor = texture(tex0, uv);
        return;
    }
    
    vec4 current = texture(tex0, uv);
    vec4 datamosh_source = has_video_b == 1 ? texture(tex1, uv) : current;
    
    // Scale width parameters
    float width_px = max(fracture_width * 5.0, 1.0);
    float edge = depth_edge(uv, width_px);
    
    // Fracture Map detection
    float thresh = 1.0 - fracture_sensitivity;
    float fracture_map = smoothstep(thresh * 0.1, thresh * 0.2 + 0.01, edge);
    
    vec2 grad = depth_gradient(uv, width_px);
    vec2 fracture_normal = length(grad) > 0.001 ? normalize(grad) : vec2(0.0);
    
    float displace_dist = fracture_map * displacement_strength * 0.05;
    vec2 displaced_uv = clamp(uv + fracture_normal * displace_dist, 0.001, 0.999);
    
    vec4 datamoshed = texture(texPrev, displaced_uv);
    
    float bleed = 0.0;
    if (bleed_amount > 0.0) {
        // Fast 4-tap bleed sampling
        vec2 btex = vec2(bleed_amount * 10.0 / resolution.x, bleed_amount * 10.0 / resolution.y);
        bleed += depth_edge(uv + vec2(-btex.x, 0.0), width_px);
        bleed += depth_edge(uv + vec2( btex.x, 0.0), width_px);
        bleed += depth_edge(uv + vec2(0.0, -btex.y), width_px);
        bleed += depth_edge(uv + vec2(0.0,  btex.y), width_px);
        bleed = smoothstep(0.05, 0.2, bleed * 0.25);
    }
    
    float total_fracture = clamp(fracture_map + bleed * 0.5, 0.0, 1.0);
    
    vec4 result = mix(datamosh_source, datamoshed, total_fracture * 0.8);
    
    vec4 composited = mix(current, result, total_fracture);
    
    vec4 previous = texture(texPrev, uv);
    composited = mix(composited, previous, total_fracture * fracture_decay);
    
    fragColor = clamp(composited, 0.0, 1.0);
}
"""

class DepthFractureDatamoshPlugin(EffectPlugin):
    """Depth Fracture Datamosh computing edge extraction natively over ping-pong buffers."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.vao = None
        self.vbo = None
        
        self.fbo1 = None
        self.tex1 = None
        self.fbo2 = None
        self.tex2 = None
        
        self._width = 0
        self._height = 0
        self._ping = True

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthFractureDatamosh in Mock Mode")
            return

        try:
            self._compile_shader()
            self._setup_quad()
        except Exception as e:
            logger.error(f"Failed to config OpenGL in DepthFractureDatamosh: {e}")
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

    def _free_fbos(self):
        try:
            if self.tex1 is not None:
                gl.glDeleteTextures(1, [self.tex1])
            if self.tex2 is not None:
                gl.glDeleteTextures(1, [self.tex2])
            if self.fbo1 is not None:
                gl.glDeleteFramebuffers(1, [self.fbo1])
            if self.fbo2 is not None:
                gl.glDeleteFramebuffers(1, [self.fbo2])
        except Exception:
            pass
        self.tex1, self.tex2 = None, None
        self.fbo1, self.fbo2 = None, None

    def _allocate_buffers(self, w: int, h: int):
        self._free_fbos()
        self._width = w
        self._height = h
        
        # Ping
        self.fbo1 = gl.glGenFramebuffers(1)
        self.tex1 = gl.glGenTextures(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex1)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.tex1, 0)
        
        # Pong
        self.fbo2 = gl.glGenFramebuffers(1)
        self.tex2 = gl.glGenTextures(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex2)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.tex2, 0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        self._clear_buffers(w, h)

    def _clear_buffers(self, w, h):
        gl.glViewport(0, 0, w, h)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo1)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo2)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        inputs = getattr(context, "inputs", {})
        video_b_in = inputs.get("video_b_in", 0)
        depth_in = inputs.get("depth_in", 0)
        
        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        if w != self._width or h != self._height:
            self._allocate_buffers(w, h)
            
        read_fbo = self.tex2 if self._ping else self.tex1
        write_fbo = self.fbo1 if self._ping else self.fbo2
        write_tex = self.tex1 if self._ping else self.tex2
        self._ping = not self._ping
            
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, write_fbo)
        gl.glViewport(0, 0, w, h)
        
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glUseProgram(self.prog)
        
        # tex0 -> Base video
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        # tex1 -> Source B if active
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, video_b_in if video_b_in > 0 else input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex1"), 1)
        
        # texPrev -> Ping Pong loop feedback
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, read_fbo)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrev"), 2)
        
        # depthTex -> Depth map geometry
        gl.glActiveTexture(gl.GL_TEXTURE3)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depthTex"), 3)
        
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), 1 if depth_in > 0 else 0)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_video_b"), 1 if video_b_in > 0 else 0)
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fracture_sensitivity"), float(params.get("fracture_sensitivity", 0.1)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fracture_width"), float(params.get("fracture_width", 0.2)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fracture_decay"), float(params.get("fracture_decay", 0.95)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "bleed_amount"), float(params.get("bleed_amount", 0.5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "displacement_strength"), float(params.get("displacement_strength", 0.5)))
        
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = write_tex
            
        return write_tex

    def cleanup(self) -> None:
        if self._mock_mode:
            return
            
        try:
            self._free_fbos()
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
            logger.error(f"Cleanup Error in DepthFractureDatamosh: {e}")
