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
    "name": "Depth Erosion Datamosh",
    "description": "Morphological depth-driven organic feedback datamosh.",
    "version": "1.0.0",
    "parameters": [
        {"name": "morph_radius", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5, "description": "Size of morphology kernel"},
        {"name": "morph_mode", "type": "int", "min": 0, "max": 3, "default": 0, "description": "0=Erode, 1=Dilate, 2=Open, 3=Close"},
        {"name": "mosh_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "feedback_decay", "type": "float", "min": 0.0, "max": 1.0, "default": 0.95}
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

uniform float morph_radius;
uniform int morph_mode;
uniform float mosh_intensity;
uniform float feedback_decay;

// Optimized 3x3 morphological kernel bounds to prevent GPU Timeout loops (Safety Rail 1)
float morph_min(vec2 p, vec2 texel) {
    float v = 1.0;
    for(int i=-1; i<=1; i++) {
        for(int j=-1; j<=1; j++) {
            v = min(v, texture(depthTex, p + vec2(i, j)*texel).r);
        }
    }
    return v;
}

float morph_max(vec2 p, vec2 texel) {
    float v = 0.0;
    for(int i=-1; i<=1; i++) {
        for(int j=-1; j<=1; j++) {
            v = max(v, texture(depthTex, p + vec2(i, j)*texel).r);
        }
    }
    return v;
}

void main() {
    if (has_depth == 0) {
        fragColor = texture(tex0, uv);
        return;
    }
    
    vec4 current = texture(tex0, uv);
    vec4 source_mosh = has_video_b == 1 ? texture(tex1, uv) : texture(tex0, uv);
    float depth_original = texture(depthTex, uv).r;
    
    vec2 texel = vec2(max(morph_radius, 0.001) / max(resolution.x, 1.0), 
                      max(morph_radius, 0.001) / max(resolution.y, 1.0));
    texel *= 5.0; 
    
    float depth_morphed = depth_original;
    if (morph_mode == 0) {
        depth_morphed = morph_min(uv, texel);
    } else if (morph_mode == 1) {
        depth_morphed = morph_max(uv, texel);
    } else if (morph_mode == 2) {
        // Fast approx open
        float eroded = morph_min(uv, texel);
        depth_morphed = mix(eroded, morph_max(uv, texel), 0.5); 
    } else if (morph_mode == 3) {
        // Fast approx close
        float dilated = morph_max(uv, texel);
        depth_morphed = mix(dilated, morph_min(uv, texel), 0.5);
    }
    
    float morph_diff = abs(depth_morphed - depth_original);
    float boundary = smoothstep(0.01, 0.05, morph_diff);
    
    vec2 displacement = vec2(0.0);
    if (boundary > 0.05) {
        float dx = texture(depthTex, uv + vec2(1.0/resolution.x, 0.0)).r - 
                   texture(depthTex, uv - vec2(1.0/resolution.x, 0.0)).r;
        float dy = texture(depthTex, uv + vec2(0.0, 1.0/resolution.y)).r - 
                   texture(depthTex, uv - vec2(0.0, 1.0/resolution.y)).r;
        
        vec2 grad = vec2(dx, dy);
        if (length(grad) > 0.001) {
            vec2 grad_dir = normalize(grad);
            displacement = grad_dir * boundary * mosh_intensity * 0.05;
        }
    }
    
    vec2 displaced_uv = clamp(uv + displacement, 0.001, 0.999);
    vec4 displaced_color = texture(texPrev, displaced_uv);
    
    // Safety check: if video B is missing, we still mosh video A from texPrev mapping
    vec4 mosh_source = mix(current, displaced_color, boundary * mosh_intensity);
    
    vec4 previous = texture(texPrev, uv);
    vec4 feedback_color = mix(mosh_source, previous, boundary * 0.5 * mosh_intensity);
    
    float decay_factor = 1.0 - (feedback_decay * 0.1);
    vec4 final_color = mix(feedback_color, current, 1.0 - decay_factor);
    
    fragColor = clamp(final_color, 0.0, 1.0);
}
"""

class DepthErosionDatamoshPlugin(object):
    """Morphological Depth Erosion Mosh leveraging Ping-Pong buffers safely."""

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

    def initialize(self, context) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthErosionDatamosh in Mock Mode")
            return

        try:
            self._compile_shader()
            self._setup_quad()
        except Exception as e:
            logger.error(f"Failed to config OpenGL in DepthErosionDatamosh: {e}")
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

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
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
        gl.glBindTexture(gl.GL_TEXTURE_2D, video_b_in if video_b_in > 0 else read_fbo)
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
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "morph_radius"), float(params.get("morph_radius", 0.5)))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "morph_mode"), int(params.get("morph_mode", 0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "mosh_intensity"), float(params.get("mosh_intensity", 0.8)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "feedback_decay"), float(params.get("feedback_decay", 0.95)))
        
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
            logger.error(f"Cleanup Error in DepthErosionDatamosh: {e}")
