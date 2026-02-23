import numpy as np
import logging
import time

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from typing import Dict, Any

logger = logging.getLogger(__name__)

METADATA = {
    "name": "Depth Blur",
    "description": "Cinematic bokeh depth-of-field using real depth data.",
    "version": "1.0.0",
    "parameters": [
        {"name": "focal_distance", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "focal_range", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "blur_amount", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "fg_blur", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0},
        {"name": "bg_blur", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0},
        {"name": "bokeh_bright", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "chromatic_fringe", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "tilt_shift", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0}
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

uniform float focal_distance;
uniform float focal_range;
uniform float blur_amount;
uniform float fg_blur;
uniform float bg_blur;
uniform float bokeh_bright;
uniform float chromatic_fringe;
uniform float tilt_shift;

vec2 safe_uv(vec2 coords) {
    return clamp(coords, 0.001, 0.999);
}

// Bounded bokeh sampling to prevent timeout loops natively checking iterations structurally (Strictly 32)
vec4 bokeh_blur(vec2 center, float radius, float bright_boost) {
    vec4 color = vec4(0.0);
    float total = 0.0;
    float golden = 2.399963;
    
    // Bounds check ensuring no infinite processing
    for (int i = 0; i < 32; i++) {
        float fi = float(i);
        float r = sqrt(fi / 32.0) * radius;
        float theta = fi * golden;
        vec2 offset = vec2(cos(theta), sin(theta)) * r / resolution;

        vec4 s = texture(tex0, safe_uv(center + offset));
        float luma = dot(s.rgb, vec3(0.299, 0.587, 0.114));
        float weight = 1.0 + luma * bright_boost * 3.0;

        color += s * weight;
        total += weight;
    }

    return color / max(total, 1.0);
}

void main() {
    vec4 source = texture(tex0, uv);
    
    float depth = 0.0;
    float active_tilt = tilt_shift;

    if (has_depth == 1) {
        depth = texture(depthTex, uv).r;
    } else {
        // Fallback safely to strong explicit spatial blur mapped globally
        active_tilt = max(0.5, tilt_shift); 
    }

    float coc = 0.0;

    if (active_tilt < 0.1 && has_depth == 1) {
        float dist_from_focal = abs(depth - focal_distance);
        coc = smoothstep(0.0, focal_range, dist_from_focal);

        if (depth < focal_distance) {
            coc *= fg_blur;
        } else {
            coc *= bg_blur;
        }
    } else {
        float projected = (uv.y - 0.5) * 2.0;
        coc = smoothstep(0.0, focal_range * 0.3 + 0.1, abs(projected) - focal_distance * 0.3);
        coc *= active_tilt;
    }

    float radius = coc * blur_amount * 15.0;

    vec4 result = vec4(0.0);
    if (radius < 0.5) {
        result = source;
    } else {
        result = bokeh_blur(uv, radius, bokeh_bright);

        if (chromatic_fringe > 0.0 && radius > 1.0) {
            float fringe = chromatic_fringe * radius * 0.002;
            result.r = bokeh_blur(uv + vec2(fringe, 0.0), radius, bokeh_bright).r;
            result.b = bokeh_blur(uv - vec2(fringe, 0.0), radius, bokeh_bright).b;
        }
    }

    fragColor = clamp(result, 0.0, 1.0);
}
"""

class DepthBlurPlugin(object):
    """Cinematic depth-of-field simulator modeling lens focal optics via PyOpenGL."""

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

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthBlur in Mock Mode (No OpenGL)")
            return

        try:
            self._compile_shader()
            self._setup_quad()
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthBlur: {e}")
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
            if self.tex is not None:
                gl.glDeleteTextures(1, [self.tex])
            if self.fbo is not None:
                gl.glDeleteFramebuffers(1, [self.fbo])
            self.tex = None
            self.fbo = None
        except Exception as e:
            logger.debug(f"Safely catching cleanup exception on FBO: {e}")

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
        if w != self._width or h != self._height:
            self._allocate_buffers(w, h)
            
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glUseProgram(self.prog)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depthTex"), 2)
        
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), 1 if depth_in > 0 else 0)
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "focal_distance"), float(params.get("focal_distance", 0.5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "focal_range"), float(params.get("focal_range", 0.2)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "blur_amount"), float(params.get("blur_amount", 0.5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fg_blur"), float(params.get("fg_blur", 1.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "bg_blur"), float(params.get("bg_blur", 1.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "bokeh_bright"), float(params.get("bokeh_bright", 0.5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "chromatic_fringe"), float(params.get("chromatic_fringe", 0.2)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "tilt_shift"), float(params.get("tilt_shift", 0.0)))
        
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
            logger.error(f"Cleanup Error in DepthBlur: {e}")
