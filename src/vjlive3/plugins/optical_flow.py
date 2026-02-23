"""
P3-VD44: Depth Effects (OpticalFlowEffect) Plugin for VJLive3.
Ported from legacy VJlive-2 OpticalFlowEffect tracking.
Pivoted from CPU-bound OpenCV Farneback calculations to a pure 100% GPGPU 
Spatial-Temporal Frame Differencing Fragment Shader to maintain 60 FPS constraint.
"""

from typing import Dict, Any, Optional
import OpenGL.GL as gl
from .api import EffectPlugin, PluginContext

logger = __import__('logging').getLogger(__name__)

METADATA = {
    "name": "OpticalFlow",
    "version": "3.0.0",
    "description": "GPU accelerated pseudo-Optical Flow visualization via Frame Differencing.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "visual",
    "tags": ["optical", "flow", "motion", "tracking", "gpu"],
    "priority": 1,
    "dependencies": [],
    "incompatible": [],
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "flowScale", "type": "float", "default": 1.0, "min": 0.1, "max": 5.0},
        {"name": "flowThreshold", "type": "float", "default": 0.1, "min": 0.0, "max": 1.0},
        {"name": "flowOpacity", "type": "float", "default": 0.8, "min": 0.0, "max": 1.0},
        {"name": "flowColorMode", "type": "int", "default": 0, "min": 0, "max": 2}
    ]
}

VERTEX_SHADER_SOURCE = """
#version 330 core
const vec2 quadVertices[4] = vec2[4](
    vec2(-1.0, -1.0),
    vec2( 1.0, -1.0),
    vec2(-1.0,  1.0),
    vec2( 1.0,  1.0)
);

out vec2 uv;

void main() {
    gl_Position = vec4(quadVertices[gl_VertexID], 0.0, 1.0);
    uv = quadVertices[gl_VertexID] * 0.5 + 0.5;
}
"""

FRAGMENT_SHADER_SOURCE = """
#version 330 core

in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex_current;
uniform sampler2D tex_prev;
uniform vec2 resolution;

uniform float flow_scale;
uniform float flow_threshold;
uniform float flow_opacity;
uniform int flow_color_mode;

#define PI 3.14159265359

// Fast HSV to RGB conversion
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    vec3 current = texture(tex_current, uv).rgb;
    vec3 prev = texture(tex_prev, uv).rgb;
    
    // Convert to grayscale intensity for spatial-temporal derivation
    float current_gray = dot(current, vec3(0.299, 0.587, 0.114));
    float prev_gray = dot(prev, vec3(0.299, 0.587, 0.114));
    
    // Finite difference approximations
    vec2 texel = 1.0 / resolution;
    
    // Spatial differences (Gradient)
    float dx = (dot(texture(tex_current, uv + vec2(texel.x, 0.0)).rgb, vec3(0.299, 0.587, 0.114)) - 
                dot(texture(tex_current, uv - vec2(texel.x, 0.0)).rgb, vec3(0.299, 0.587, 0.114))) * 0.5;
    float dy = (dot(texture(tex_current, uv + vec2(0.0, texel.y)).rgb, vec3(0.299, 0.587, 0.114)) - 
                dot(texture(tex_current, uv - vec2(0.0, texel.y)).rgb, vec3(0.299, 0.587, 0.114))) * 0.5;
                
    // Temporal difference
    float dt = current_gray - prev_gray;
    
    // Pseudo Horn-Schunck / Lucas-Kanade gradient vector field
    float gradient_mag_sq = dx*dx + dy*dy + 0.0001; 
    float u = -dx * dt / gradient_mag_sq;
    float v = -dy * dt / gradient_mag_sq;
    
    vec2 flow = vec2(u, v) * flow_scale;
    float mag = length(flow);
    
    if (mag > flow_threshold) {
        vec3 flow_rgb = vec3(0.0);
        float ang = atan(flow.y, flow.x); // Range [-PI, PI]
        
        if (flow_color_mode == 0) {
            // Magnitude only (grayscale)
            float norm_mag = clamp(mag, 0.0, 1.0);
            flow_rgb = vec3(norm_mag);
        } else if (flow_color_mode == 1) {
            // Direction HSV
            float hue = (ang + PI) / (2.0 * PI); // Normalized [0, 1]
            float val = clamp(mag, 0.0, 1.0);
            flow_rgb = hsv2rgb(vec3(hue, 1.0, val));
        } else {
            // Magnitude + Direction
            float hue = (ang + PI) / (2.0 * PI);
            float sat = clamp(mag, 0.0, 1.0);
            flow_rgb = hsv2rgb(vec3(hue, sat, 1.0));
        }
        
        fragColor = vec4(mix(current, flow_rgb, flow_opacity), 1.0);
    } else {
        fragColor = vec4(current, 1.0);
    }
}
"""

class OpticalFlowPlugin(EffectPlugin):
    def __init__(self):
        super().__init__()
        self.program = 0
        self.target_fbo = 0
        self.target_texture = 0
        
        self.prev_fbo = 0
        self.prev_texture = 0
        
        self.width = 0
        self.height = 0
        self.empty_vao = 0
        self._initialized = False

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def _compile_shader(self, vs_src: str, fs_src: str) -> int:
        vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vertex_shader, vs_src)
        gl.glCompileShader(vertex_shader)
        if not gl.glGetShaderiv(vertex_shader, gl.GL_COMPILE_STATUS):
            err = gl.glGetShaderInfoLog(vertex_shader)
            logger.error(f"Flow VS fail: {err}")
            return 0

        fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragment_shader, fs_src)
        gl.glCompileShader(fragment_shader)
        if not gl.glGetShaderiv(fragment_shader, gl.GL_COMPILE_STATUS):
            err = gl.glGetShaderInfoLog(fragment_shader)
            logger.error(f"Flow FS fail: {err}")
            return 0

        program = gl.glCreateProgram()
        gl.glAttachShader(program, vertex_shader)
        gl.glAttachShader(program, fragment_shader)
        gl.glLinkProgram(program)
        
        if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
            err = gl.glGetProgramInfoLog(program)
            logger.error(f"Flow link fail: {err}")
            return 0
            
        gl.glDeleteShader(vertex_shader)
        gl.glDeleteShader(fragment_shader)
        return program

    def initialize(self, context: PluginContext) -> bool:
        if not hasattr(gl, 'glCreateProgram'):
            logger.warning("Mock mode engaged. Skipping GL init.")
            return True

        try:
            self.program = self._compile_shader(VERTEX_SHADER_SOURCE, FRAGMENT_SHADER_SOURCE)
            if not self.program: return False
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to init OpticalFlowPlugin: {e}")
            return False

    def _setup_target_fbos(self, width: int, height: int):
        if self.width == width and self.height == height and self.target_fbo != 0:
            return

        if self.target_fbo != 0:
            gl.glDeleteFramebuffers(1, [self.target_fbo])
            gl.glDeleteTextures(1, [self.target_texture])
            gl.glDeleteFramebuffers(1, [self.prev_fbo])
            gl.glDeleteTextures(1, [self.prev_texture])

        self.width = width
        self.height = height
        
        # Target Render FBO
        self.target_fbo = gl.glGenFramebuffers(1)
        self.target_texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.target_texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.target_fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.target_texture, 0)
        
        # Persistant Prev History FBO (Frame Buffer T-1)
        self.prev_fbo = gl.glGenFramebuffers(1)
        self.prev_texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.prev_texture)
        # Initialize entirely blank
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.prev_fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.prev_texture, 0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
            return 0
            
        w = getattr(context, 'width', 1920)
        h = getattr(context, 'height', 1080)
        
        if not hasattr(gl, 'glCreateProgram'):
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture

        if not self._initialized:
            self.initialize(context)

        self._setup_target_fbos(w, h)
        
        # Phase 1: Render Flow Field
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.target_fbo)
        gl.glViewport(0, 0, w, h)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        gl.glUseProgram(self.program)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "tex_current"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.prev_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "tex_prev"), 1)
            
        gl.glUniform2f(gl.glGetUniformLocation(self.program, "resolution"), float(w), float(h))
        
        # Mapped Params
        fs = float(params.get("flowScale", 1.0))
        ft = float(params.get("flowThreshold", 0.1))
        fo = float(params.get("flowOpacity", 0.8))
        fm = int(params.get("flowColorMode", 0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "flow_scale"), fs)
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "flow_threshold"), ft)
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "flow_opacity"), fo)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "flow_color_mode"), fm)
        
        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        
        # Phase 2: Copy input texture to prev_texture for T-1 evaluation on next frame
        # VJLive3 standard specifies Core Profile. We map a quick glBlitFramebuffer operation 
        # reading directly off the implicit FBO attachment if possible. To be absolutely certain in 
        # Python GL wrapper chains, we bind an FBO holding the input mapping to read from:
        
        tmp_fbo = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_READ_FRAMEBUFFER, tmp_fbo)
        gl.glFramebufferTexture2D(gl.GL_READ_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, input_texture, 0)
        
        gl.glBindFramebuffer(gl.GL_DRAW_FRAMEBUFFER, self.prev_fbo)
        gl.glBlitFramebuffer(0, 0, w, h, 0, 0, w, h, gl.GL_COLOR_BUFFER_BIT, gl.GL_NEAREST)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glDeleteFramebuffers(1, [tmp_fbo])
        
        gl.glBindVertexArray(0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.target_texture
            
        return self.target_texture

    def cleanup(self) -> None:
        try:
            if hasattr(gl, 'glDeleteProgram') and self.program != 0:
                gl.glDeleteProgram(self.program)
            if hasattr(gl, 'glDeleteFramebuffers'): 
                if self.target_fbo != 0: gl.glDeleteFramebuffers(1, [self.target_fbo])
                if self.prev_fbo != 0: gl.glDeleteFramebuffers(1, [self.prev_fbo])
            if hasattr(gl, 'glDeleteTextures'):
                if self.target_texture != 0: gl.glDeleteTextures(1, [self.target_texture])
                if self.prev_texture != 0: gl.glDeleteTextures(1, [self.prev_texture])
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao != 0:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Failed to cleanup OpticalFlow plugin: {e}")
        finally:
            self.program = 0
            self.target_fbo = 0
            self.target_texture = 0
            self.prev_fbo = 0
            self.prev_texture = 0
            self.empty_vao = 0

