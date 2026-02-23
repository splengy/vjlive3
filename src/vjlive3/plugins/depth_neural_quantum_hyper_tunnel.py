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
    "name": "Neural Quantum Hyper Tunnel",
    "description": "Infinite depth-modulated feedback tunnel with non-linear color routing.",
    "version": "1.0.0",
    "parameters": [
        {"name": "tunnel_speed", "type": "float", "min": -2.0, "max": 2.0, "default": 0.5},
        {"name": "depth_influence", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "quantum_jitter", "type": "float", "min": 0.0, "max": 1.0, "default": 0.1},
        {"name": "neural_color_shift", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "feedback_decay", "type": "float", "min": 0.0, "max": 1.0, "default": 0.95}
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

uniform sampler2D tex0;         // current video
uniform sampler2D texPrev;      // feedback buffer
uniform sampler2D depth_tex;    // depth
uniform float time;
uniform int has_depth;

uniform float tunnel_speed;
uniform float depth_influence;
uniform float quantum_jitter;
uniform float neural_color_shift;
uniform float feedback_decay;
uniform vec2 resolution;

// Pseudo-random hash
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

// 2D Noise
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    vec2 u = f*f*(3.0-2.0*f);
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

// RGB to HSV
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

// HSV to RGB
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    float safe_tunnel_speed = clamp(tunnel_speed, -2.0, 2.0);
    float safe_quantum_jitter = clamp(quantum_jitter, 0.0, 1.0);
    
    // Convert Cartesian to Polar logic mapping 
    vec2 center = vec2(0.5, 0.5);
    vec2 p = uv - center;
    p.y *= resolution.y / resolution.x;
    
    float radius = length(p);
    float angle = atan(p.y, p.x);
    
    // Base geometry transform mapping infinite depth forwarding
    float tunnel_z = 0.5 / (radius + 0.01) + time * safe_tunnel_speed;
    float tunnel_angle = angle / 6.28318530718;
    
    // Inject Quantum Jitter (Noise deformation on radius/angle)
    if (safe_quantum_jitter > 0.0) {
        float jx = noise(vec2(tunnel_z, time * 10.0));
        float jy = noise(vec2(tunnel_angle * 10.0, time * 5.0));
        tunnel_z += (jx - 0.5) * safe_quantum_jitter * 0.2;
        tunnel_angle += (jy - 0.5) * safe_quantum_jitter * 0.2;
    }
    
    // Inject Depth Modulations
    vec2 sample_uv = uv; // fallback if no depth
    if (has_depth == 1) { // Apply wall mapping
        float d = texture(depth_tex, uv).r;
        tunnel_z += d * depth_influence;
    }
    
    // Modulate back to Cartesian sampling for feedback buffer
    vec2 final_uv = fract(vec2(tunnel_z, tunnel_angle));
    
    // Read previous iteration
    vec4 prev_color = texture(texPrev, final_uv);
    
    // Apply simulated neural color shifting
    if (neural_color_shift > 0.0) {
        vec3 hsv = rgb2hsv(prev_color.rgb);
        // Non-linear color transformation based on spatial bounds
        hsv.x = fract(hsv.x + (radius * neural_color_shift) + (noise(uv * 5.0) * neural_color_shift * 0.2));
        prev_color.rgb = hsv2rgb(hsv);
    }
    
    // Current frame logic mapping 
    vec4 current_color = texture(tex0, uv);
    
    // Attenuate tunnel wall persistence
    vec4 mixed_color = mix(current_color, prev_color, feedback_decay);
    
    fragColor_main = vec4(mixed_color.rgb, 1.0);
}
"""

class DepthNeuralQuantumHyperTunnelPlugin(object):
    """Neural Quantum Hyper Tunnel Plugin."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.fboA = None
        self.fboB = None
        self.texA = None
        self.texB = None
        self.vao = None
        self.vbo = None
        self._width = 0
        self._height = 0
        self._ping_pong = True
        self.start_time = time.time()

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context) -> None:
        if self._mock_mode:
            logger.warning("Initializing HyperTunnel in Mock Mode (No OpenGL)")
            return

        try:
            self._compile_shader()
            self._setup_quad()
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in HyperTunnel: {e}")
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
        
        self.fboA = gl.glGenFramebuffers(1)
        self.texA = gl.glGenTextures(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fboA)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texA)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.texA, 0)
        
        self.fboB = gl.glGenFramebuffers(1)
        self.texB = gl.glGenTextures(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fboB)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texB)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.texB, 0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        # Clear buffers with black
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fboA)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fboB)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _free_fbo(self):
        try:
            if self.texA:
                gl.glDeleteTextures(1, [self.texA])
                self.texA = None
            if self.fboA:
                gl.glDeleteFramebuffers(1, [self.fboA])
                self.fboA = None
            if self.texB:
                gl.glDeleteTextures(1, [self.texB])
                self.texB = None
            if self.fboB:
                gl.glDeleteFramebuffers(1, [self.fboB])
                self.fboB = None
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
        depth_tex = inputs.get("depth_in", 0)
        
        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        if w != self._width or h != self._height:
            self._allocate_buffers(w, h)
            
        fbo_out = self.fboA if self._ping_pong else self.fboB
        tex_in = self.texB if self._ping_pong else self.texA
        tex_out = self.texA if self._ping_pong else self.texB
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo_out)
        gl.glViewport(0, 0, w, h)
        
        gl.glUseProgram(self.prog)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrev"), 1)
        
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_tex)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 2)
        
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), 1 if depth_tex > 0 else 0)
        
        current_time = time.time() - self.start_time
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), current_time)
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        
        # Shader parameters
        speed = float(params.get("tunnel_speed", 0.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "tunnel_speed"), speed)
        
        d_infl = float(params.get("depth_influence", 0.8))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_influence"), d_infl)
        
        jitter = float(params.get("quantum_jitter", 0.1))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "quantum_jitter"), jitter)
        
        color_shift = float(params.get("neural_color_shift", 0.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "neural_color_shift"), color_shift)
        
        decay = float(params.get("feedback_decay", 0.95))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "feedback_decay"), decay)
        
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        self._ping_pong = not self._ping_pong
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = tex_out
            
        return tex_out

    def cleanup(self) -> None:
        if self._mock_mode:
            return
            
        try:
            self._free_fbo()
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
            logger.error(f"Cleanup Error in HyperTunnel: {e}")
