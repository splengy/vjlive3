"""
P3-VD42: Depth Effects (Distortion Effect) Plugin for VJLive3.
Ported from legacy VJlive-2 DepthDistortionEffect.
Maintains pure 2D Fragment processing utilizing topology maps for 4 distortion modes.
"""

from typing import Dict, Any, Optional
import OpenGL.GL as gl
import time
# # from .api import EffectPlugin, PluginContext

logger = __import__('logging').getLogger(__name__)

METADATA = {
    "name": "DepthDistortion",
    "version": "3.0.0",
    "description": "Applies Fragment topological 2D distortions (Wave, Pinch, Bulge, Twist) driven by Depth.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "visual",
    "tags": ["depth", "distortion", "wave", "pinch", "bulge", "twist"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "distortionStrength", "type": "float", "default": 0.1, "min": 0.0, "max": 1.0},
        {"name": "distortionType", "type": "int", "default": 0, "min": 0, "max": 3},
        {"name": "depthThreshold", "type": "float", "default": 2.0, "min": 0.5, "max": 10.0},
        {"name": "distortionRadius", "type": "float", "default": 0.5, "min": 0.1, "max": 1.0}
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
uniform float time;
uniform float has_depth;

uniform float distortion_strength;
uniform int distortion_type;
uniform float depth_threshold;
uniform float distortion_radius;

// Depth-based distortion functions
vec2 depth_wave_distortion(vec2 uv_pos, float depth) {
    float wave = sin(uv_pos.y * 10.0 + time * 2.0) * distortion_strength * depth;
    return uv_pos + vec2(wave * 0.01, 0.0);
}

vec2 depth_pinch_distortion(vec2 uv_pos, float depth, vec2 center) {
    vec2 dir = uv_pos - center;
    float dist = length(dir);
    if (dist < distortion_radius && depth < depth_threshold) {
        float factor = 1.0 - (distortion_radius - dist) / distortion_radius;
        factor *= distortion_strength * (1.0 - depth / depth_threshold);
        dir = normalize(dir) * dist * (1.0 - factor);
        return center + dir;
    }
    return uv_pos;
}

vec2 depth_bulge_distortion(vec2 uv_pos, float depth, vec2 center) {
    vec2 dir = uv_pos - center;
    float dist = length(dir);
    if (dist < distortion_radius && depth < depth_threshold) {
        float factor = 1.0 - (distortion_radius - dist) / distortion_radius;
        factor *= distortion_strength * (1.0 - depth / depth_threshold);
        dir = normalize(dir) * dist * (1.0 + factor);
        return center + dir;
    }
    return uv_pos;
}

vec2 depth_twist_distortion(vec2 uv_pos, float depth, vec2 center) {
    vec2 dir = uv_pos - center;
    float dist = length(dir);
    if (dist < distortion_radius && depth < depth_threshold) {
        float angle = atan(dir.y, dir.x) + distortion_strength * (1.0 - depth / depth_threshold) * 5.0;
        return center + vec2(cos(angle), sin(angle)) * dist;
    }
    return uv_pos;
}

void main() {
    vec4 original = texture(tex0, uv);

    if (has_depth > 0.0) {
        // Sample depth at this pixel
        float depth = texture(depth_tex, uv).r * 4.0; // Simulated normalization bounds 
        
        vec2 distorted_uv = uv;

        // Apply selected distortion based on depth
        if (distortion_type == 0) {
            distorted_uv = depth_wave_distortion(uv, depth);
        } else if (distortion_type == 1) {
            distorted_uv = depth_pinch_distortion(uv, depth, vec2(0.5, 0.5));
        } else if (distortion_type == 2) {
            distorted_uv = depth_bulge_distortion(uv, depth, vec2(0.5, 0.5));
        } else if (distortion_type == 3) {
            distorted_uv = depth_twist_distortion(uv, depth, vec2(0.5, 0.5));
        }

        // Sample distorted texture
        vec4 distorted = texture(tex0, distorted_uv);

        // Blend based on depth scaling factor bridging legacy mix behavior
        float depth_factor = 1.0 - min(depth / depth_threshold, 1.0);
        fragColor = mix(original, distorted, depth_factor);
    } else {
        fragColor = original;
    }
}
"""

class DepthDistortionPlugin(object):
    def __init__(self):
        super().__init__()
        self.program = 0
        self.target_fbo = 0
        self.target_texture = 0
        self.width = 0
        self.height = 0
        self.empty_vao = 0
        self.start_time = time.time()
        self._initialized = False

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def _compile_shader(self, vs_src: str, fs_src: str) -> int:
        vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vertex_shader, vs_src)
        gl.glCompileShader(vertex_shader)
        if not gl.glGetShaderiv(vertex_shader, gl.GL_COMPILE_STATUS):
            err = gl.glGetShaderInfoLog(vertex_shader)
            logger.error(f"Distortion VS fail: {err}")
            return 0

        fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragment_shader, fs_src)
        gl.glCompileShader(fragment_shader)
        if not gl.glGetShaderiv(fragment_shader, gl.GL_COMPILE_STATUS):
            err = gl.glGetShaderInfoLog(fragment_shader)
            logger.error(f"Distortion FS fail: {err}")
            return 0

        program = gl.glCreateProgram()
        gl.glAttachShader(program, vertex_shader)
        gl.glAttachShader(program, fragment_shader)
        gl.glLinkProgram(program)
        
        if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
            err = gl.glGetProgramInfoLog(program)
            logger.error(f"Distortion link fail: {err}")
            return 0
            
        gl.glDeleteShader(vertex_shader)
        gl.glDeleteShader(fragment_shader)
        return program

    def initialize(self, context) -> bool:
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
            logger.error(f"Failed to init DepthDistortionPlugin: {e}")
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

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
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
            
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "time"), time.time() - self.start_time)
        
        # Mapped Params
        st = float(params.get("distortionStrength", 0.1))
        dt = int(params.get("distortionType", 0))
        dth = float(params.get("depthThreshold", 2.0))
        rad = float(params.get("distortionRadius", 0.5))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "distortion_strength"), st)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "distortion_type"), dt)
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "depth_threshold"), dth)
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "distortion_radius"), rad)
        
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
            logger.error(f"Failed to cleanup DepthDistortion plugin: {e}")
        finally:
            self.program = 0
            self.target_fbo = 0
            self.target_texture = 0
            self.empty_vao = 0

