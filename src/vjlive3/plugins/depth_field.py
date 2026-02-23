"""
P3-VD43: Depth Effects (DepthFieldEffect) Plugin for VJLive3.
Ported from legacy VJlive-2 DepthFieldEffect.
Maintains pure 2D Fragment processing utilizing depth maps to simulate Optical Depth of Field.
"""

from typing import Dict, Any, Optional
import OpenGL.GL as gl
import time
from .api import EffectPlugin, PluginContext

logger = __import__('logging').getLogger(__name__)

METADATA = {
    "name": "DepthField",
    "version": "3.0.0",
    "description": "Applies Fragment-level Gaussian Depth of Field (DoF) driven by Depth maps.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "visual",
    "tags": ["depth", "dof", "field", "blur", "gaussian"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "focusDistance", "type": "float", "default": 2.0, "min": 0.5, "max": 10.0},
        {"name": "aperture", "type": "float", "default": 0.1, "min": 0.01, "max": 1.0},
        {"name": "maxBlur", "type": "float", "default": 0.02, "min": 0.001, "max": 0.1},
        {"name": "blurSamples", "type": "int", "default": 16, "min": 4, "max": 32}
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

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform vec2 resolution;
uniform float has_depth;

uniform float focus_distance;
uniform float aperture;
uniform float max_blur;
uniform int blur_samples;

// Gaussian blur function
vec4 gaussian_blur(sampler2D tex, vec2 uv_pos, float blur_amount) {
    vec4 result = vec4(0.0);
    float total_weight = 0.0;

    int samples = int(clamp(float(blur_samples), 4.0, 32.0));
    float sigma = blur_amount * 10.0;
    
    // Prevent division by zero if blur is exactly 0
    if (sigma <= 0.0001) {
        return texture(tex, uv_pos);
    }

    for (int i = -samples/2; i <= samples/2; i++) {
        for (int j = -samples/2; j <= samples/2; j++) {
            vec2 offset = vec2(float(i), float(j)) * blur_amount / resolution;
            float weight = exp(-(float(i*i) + float(j*j)) / (2.0 * sigma * sigma));
            result += texture(tex, uv_pos + offset) * weight;
            total_weight += weight;
        }
    }

    return result / max(total_weight, 0.0001);
}

void main() {
    vec4 original = texture(tex0, uv);

    if (has_depth > 0.0) {
        // Sample depth
        float depth = texture(depth_tex, uv).r * 4.0; // Assume linear mapping scale factor
        if (depth <= 0.01) { 
            depth = 10.0; // Infinite plane if unregistered
        }

        // Calculate blur amount based on depth difference from focus plane
        float depth_diff = abs(depth - focus_distance);
        float blur_amount = min(depth_diff * aperture, max_blur);

        // Apply gaussian blur directly into frambuffer mapping
        vec4 blurred = gaussian_blur(tex0, uv, blur_amount);

        // Native legacy mix removed; DoF explicitly returns fully-resolved fragment
        fragColor = blurred;
    } else {
        fragColor = original;
    }
}
"""

class DepthFieldPlugin(EffectPlugin):
    def __init__(self):
        super().__init__()
        self.program = 0
        self.target_fbo = 0
        self.target_texture = 0
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
            logger.error(f"Field VS fail: {err}")
            return 0

        fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragment_shader, fs_src)
        gl.glCompileShader(fragment_shader)
        if not gl.glGetShaderiv(fragment_shader, gl.GL_COMPILE_STATUS):
            err = gl.glGetShaderInfoLog(fragment_shader)
            logger.error(f"Field FS fail: {err}")
            return 0

        program = gl.glCreateProgram()
        gl.glAttachShader(program, vertex_shader)
        gl.glAttachShader(program, fragment_shader)
        gl.glLinkProgram(program)
        
        if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
            err = gl.glGetProgramInfoLog(program)
            logger.error(f"Field link fail: {err}")
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
            logger.error(f"Failed to init DepthFieldPlugin: {e}")
            return False

    def _setup_fbo(self, width: int, height: int):
        if self.width == width and self.height == height and self.target_fbo != 0:
            return

        if self.target_fbo != 0:
            gl.glDeleteFramebuffers(1, [self.target_fbo])
            gl.glDeleteTextures(1, [self.target_texture])

        self.width = width
        self.height = height
        
        self.target_fbo = gl.glGenFramebuffers(1)
        self.target_texture = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.target_texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.target_fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.target_texture, 0)
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

        self._setup_fbo(w, h)
        
        depth_tex = context.inputs.get("depth_in", 0) if context and hasattr(context, 'inputs') else 0
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.target_fbo)
        gl.glViewport(0, 0, w, h)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        gl.glUseProgram(self.program)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "tex0"), 0)
        
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "has_depth"), 1.0 if depth_tex > 0 else 0.0)
        
        if depth_tex > 0:
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_tex)
            gl.glUniform1i(gl.glGetUniformLocation(self.program, "depth_tex"), 1)
            
        gl.glUniform2f(gl.glGetUniformLocation(self.program, "resolution"), float(w), float(h))
        
        # Mapped Params
        fd = float(params.get("focusDistance", 2.0))
        ap = float(params.get("aperture", 0.1))
        mb = float(params.get("maxBlur", 0.02))
        bs = int(params.get("blurSamples", 16))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "focus_distance"), fd)
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "aperture"), ap)
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "max_blur"), mb)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "blur_samples"), bs)
        
        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        
        gl.glBindVertexArray(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.target_texture
            
        return self.target_texture

    def cleanup(self) -> None:
        try:
            if hasattr(gl, 'glDeleteProgram') and self.program != 0:
                gl.glDeleteProgram(self.program)
            if hasattr(gl, 'glDeleteFramebuffers') and self.target_fbo != 0:
                gl.glDeleteFramebuffers(1, [self.target_fbo])
            if hasattr(gl, 'glDeleteTextures') and self.target_texture != 0:
                gl.glDeleteTextures(1, [self.target_texture])
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao != 0:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Failed to cleanup DepthField plugin: {e}")
        finally:
            self.program = 0
            self.target_fbo = 0
            self.target_texture = 0
            self.empty_vao = 0

