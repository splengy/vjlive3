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
    "name": "R16 Depth Wave",
    "description": "Sinusoidal wave distortions for high-precision depth maps.",
    "version": "1.0.0",
    "parameters": [
        {"name": "wave_amplitude", "type": "float", "min": 0.0, "max": 1.0, "default": 0.1},
        {"name": "wave_frequency", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "wave_speed", "type": "float", "min": -5.0, "max": 5.0, "default": 1.0},
        {"name": "phase_offset", "type": "float", "min": 0.0, "max": 3.14159, "default": 0.0}
    ],
    "inputs": ["video_in", "depth_raw_in"],
    "outputs": ["video_out", "depth_raw_out"]
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

// Dual MRT outputs for Framebuffer
layout(location = 0) out vec4 fragColor_video;
layout(location = 1) out float fragColor_depth;

uniform sampler2D tex0;
uniform sampler2D depthRawTex;
uniform int has_depth;
uniform float time;

uniform float wave_amplitude;
uniform float wave_frequency;
uniform float wave_speed;
uniform float phase_offset;

// Triangle wave to fold UVs safely wrapping seamlessly back
vec2 safe_uv(vec2 coords) {
    return vec2(1.0) - abs(vec2(1.0) - mod(coords, 2.0));
}

void main() {
    float amp = clamp(wave_amplitude, 0.0, 1.0);
    float freq = clamp(wave_frequency, 0.0, 10.0);
    float spd = clamp(wave_speed, -5.0, 5.0);
    
    // Calculate primary sinusoidal structure
    float wave_time = time * spd + phase_offset;
    
    // Wave on X coordinates
    float wave_x = sin(uv.y * freq + wave_time) * amp;
    // Wave on Y coordinates
    float wave_y = cos(uv.x * freq + wave_time) * amp;
    
    vec2 displacement = vec2(wave_x, wave_y);
    vec2 distorted_uv = safe_uv(uv + displacement);
    
    // Output 0: Standard video color bleeding/distortion mapped to safe UV boundaries
    fragColor_video = texture(tex0, distorted_uv);
    
    // Output 1: Pass the raw 16-bit depth output using the distorted UV mapping seamlessly
    if (has_depth == 1) {
        fragColor_depth = texture(depthRawTex, distorted_uv).r;
    } else {
        fragColor_depth = 0.0;
    }
}
"""

class DepthR16WavePlugin(object):
    """High-precision depth map wave distorter utilizing MRT architecture."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.fbo = None
        
        # Dual texture outputs
        self.tex_video = None
        self.tex_depth = None
        
        self.vao = None
        self.vbo = None
        self._width = 0
        self._height = 0
        self.start_time = time.time()

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthR16Wave in Mock Mode (No OpenGL)")
            return

        try:
            self._compile_shader()
            self._setup_quad()
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthR16Wave: {e}")
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
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        
        textures = gl.glGenTextures(2)
        self.tex_video = textures[0]
        self.tex_depth = textures[1]
        
        # Attachment 0: Standard 8-bit RGBA texture for Video Output
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_video)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.tex_video, 0)
        
        # Attachment 1: High-precision 16-bit float Red texture for Depth map output
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_depth)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_R16F, w, h, 0, gl.GL_RED, gl.GL_FLOAT, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT1, gl.GL_TEXTURE_2D, self.tex_depth, 0)
        
        # Enable MRT architecture natively via glDrawBuffers allowing our single fragment to output to both attachments
        buffers = [gl.GL_COLOR_ATTACHMENT0, gl.GL_COLOR_ATTACHMENT1]
        gl.glDrawBuffers(2, buffers)
        
        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            logger.error("Failed to construct complete dual-MRT FBO in DepthR16Wave.")

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _free_fbo(self):
        try:
            tex_list = []
            if self.tex_video is not None: tex_list.append(self.tex_video)
            if self.tex_depth is not None: tex_list.append(self.tex_depth)
            
            if tex_list:
                gl.glDeleteTextures(len(tex_list), tex_list)
                
            self.tex_video = None
            self.tex_depth = None
                
            if self.fbo is not None:
                gl.glDeleteFramebuffers(1, [self.fbo])
                self.fbo = None
        except Exception as e:
            logger.debug(f"Safely catching cleanup exception on FBO: {e}")

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        inputs = getattr(context, "inputs", {})
        depth_raw_in = inputs.get("depth_raw_in", 0)
             
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
                # Emulate missing depth logic passing 0 through outputs natively without crashing downstream components
                context.outputs["depth_raw_out"] = depth_raw_in if depth_raw_in > 0 else 0
            return input_texture
             
        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        if w != self._width or h != self._height:
            self._allocate_buffers(w, h)
            
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        gl.glUseProgram(self.prog)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_raw_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depthRawTex"), 1)
        
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), 1 if depth_raw_in > 0 else 0)
        
        current_time = time.time() - self.start_time
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), current_time)
        
        # Shader parameters
        amp = float(params.get("wave_amplitude", 0.1))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "wave_amplitude"), amp)
        
        freq = float(params.get("wave_frequency", 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "wave_frequency"), freq)
        
        spd = float(params.get("wave_speed", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "wave_speed"), spd)
        
        pha = float(params.get("phase_offset", 0.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "phase_offset"), pha)
        
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.tex_video
            context.outputs["depth_raw_out"] = self.tex_depth
            
        return self.tex_video

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
            logger.error(f"Cleanup Error in DepthR16Wave: {e}")
