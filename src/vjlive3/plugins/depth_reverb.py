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
    "name": "Depth Reverb",
    "description": "Visual reverb where depth controls echo persistence.",
    "version": "1.0.0",
    "parameters": [
        {"name": "room_size", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5, "description": "Global wetness scalar"},
        {"name": "decay_time", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8, "description": "Feedback persistence"},
        {"name": "diffusion", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2, "description": "Spatial blur in reverb tail"},
        {"name": "damping", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5, "description": "High frequency loss"}
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
layout(location = 0) out vec4 fragColor;

uniform sampler2D tex0;         // current video
uniform sampler2D texPrev;      // previous feedback frame
uniform sampler2D depth_tex;    // depth map

uniform float time;
uniform vec2 resolution;

// Reverb core
uniform float room_size;
uniform float decay;
uniform float diffusion;
uniform float damping;

uniform int has_depth;

float hash(vec2 p) {
    p = fract(p * vec2(443.897, 441.423));
    p += dot(p, p.yx + 19.19);
    return fract((p.x + p.y) * p.x);
}

void main() {
    vec4 current = texture(tex0, uv);
    vec4 previous = texture(texPrev, uv);
    
    // Default fallback if no depth connected
    float depth = 0.5;
    if (has_depth == 1) {
        depth = texture(depth_tex, uv).r;
    }

    // Amount of reverb based on depth
    // Near = 0.0, Far = 1.0. We use room_size to scale how far out the reverb extends.
    float reverb_amount = smoothstep(0.1, 0.1 + room_size + 0.01, depth);
    reverb_amount = clamp(reverb_amount, 0.0, 1.0);

    // Diffusion (spatial blur in reverb tail)
    vec4 diffused = previous;
    if (diffusion > 0.0 && reverb_amount > 0.0) {
        // Box blur sized by diffusion and depth
        float blur_size = diffusion * reverb_amount * 3.0;
        vec4 blur_sum = vec4(0.0);
        float blur_weight = 0.0;
        int samples = int(blur_size * 2.0) + 1;
        samples = min(samples, 7);

        for (int x = -3; x <= 3; x++) {
            for (int y = -3; y <= 3; y++) {
                if (abs(x) + abs(y) > samples) continue;
                vec2 offset = vec2(float(x), float(y)) * blur_size / resolution;
                vec4 s = texture(texPrev, clamp(uv + offset, 0.001, 0.999));
                float w = 1.0 / (1.0 + float(abs(x) + abs(y)));
                blur_sum += s * w;
                blur_weight += w;
            }
        }
        diffused = blur_sum / max(blur_weight, 1.0);
    }

    // Damping (high-freq loss)
    if (damping > 0.0 && reverb_amount > 0.0) {
        float luma = dot(diffused.rgb, vec3(0.299, 0.587, 0.114));
        float damp = damping * reverb_amount * 0.5;
        diffused.rgb = mix(diffused.rgb, vec3(luma), damp);
    }

    // Apply temporal decay
    float fb = decay * reverb_amount;
    fb = clamp(fb, 0.0, 0.95);

    // Final mix
    vec4 reverbed = mix(current, diffused, fb);
    
    // Output
    fragColor = reverbed;
}
"""

class DepthReverbPlugin(object):
    """Depth Reverb Plugin."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        
        self.fbo = None
        self.tex_out = None
        self.tex_prev = None
        self.current_size = (0, 0)
        
        self.vao = None
        self.vbo = None

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthReverb in Mock Mode (No OpenGL)")
            return

        try:
            self._compile_shader()
            self._setup_quad()
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthReverb: {e}")
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
        """Dynamic reallocation for resolution changes."""
        
        # Cleanup old
        if self.tex_out:
            gl.glDeleteTextures(1, [self.tex_out])
            self.tex_out = None
        if self.tex_prev:
            gl.glDeleteTextures(1, [self.tex_prev])
            self.tex_prev = None
        if self.fbo:
            gl.glDeleteFramebuffers(1, [self.fbo])
            self.fbo = None
            
        self.tex_out = gl.glGenTextures(1)
        self.tex_prev = gl.glGenTextures(1)
        self.fbo = gl.glGenFramebuffers(1)
        
        # Allocate Ping
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_out)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

        # Allocate Pong
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_prev)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

        # Setup FBO
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.tex_out, 0)
        gl.glDrawBuffers(1, [gl.GL_COLOR_ATTACHMENT0])
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        self.current_size = (w, h)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
             
        inputs = getattr(context, "inputs", {})
        depth_tex = inputs.get("depth_in", 0)
        
        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        if (w, h) != self.current_size:
            self._allocate_buffers(w, h)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        
        gl.glUseProgram(self.prog)
        
        # Unit 0: Current Frame
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        # Unit 1: Previous Reverbed Frame
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_prev)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrev"), 1)
        
        # Unit 2: Depth Matte
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_tex)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 2)
        
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), 1 if depth_tex > 0 else 0)
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        
        # Spec defines values natively as 0.0 - 1.0! 
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "room_size"), float(params.get("room_size", 0.5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "decay"), float(params.get("decay_time", 0.8)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "diffusion"), float(params.get("diffusion", 0.2)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "damping"), float(params.get("damping", 0.5)))
        
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        # Manually swap/copy 'ping' to 'pong' 
        # Since tex_out is bound to GL_COLOR_ATTACHMENT0, we read from there into tex_prev
        gl.glReadBuffer(gl.GL_COLOR_ATTACHMENT0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_prev)
        gl.glCopyTexSubImage2D(gl.GL_TEXTURE_2D, 0, 0, 0, 0, 0, w, h)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.tex_out
            
        return self.tex_out

    def cleanup(self) -> None:
        if self._mock_mode:
            return
            
        try:
            if self.tex_out:
                gl.glDeleteTextures(1, [self.tex_out])
            if self.tex_prev:
                gl.glDeleteTextures(1, [self.tex_prev])
            if self.fbo:
                gl.glDeleteFramebuffers(1, [self.fbo])
            if self.vbo:
                gl.glDeleteBuffers(1, [self.vbo])
            if self.vao:
                gl.glDeleteVertexArrays(1, [self.vao])
            if self.prog:
                gl.glDeleteProgram(self.prog)
                
            self.tex_out = None
            self.tex_prev = None
            self.fbo = None
            self.vbo = None
            self.vao = None
            self.prog = None
        except Exception as e:
            logger.error(f"Cleanup Error in DepthReverb: {e}")
