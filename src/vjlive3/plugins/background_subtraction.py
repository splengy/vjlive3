"""
P3-VD45: Depth Effects (BackgroundSubtractionEffect) Plugin for VJLive3.
Ported from legacy VJlive-2 BackgroundSubtractionEffect.
Pivoted from CPU-bound OpenCV MOG2 calculations to a pure 100% GPGPU 
Exponential Moving Average (EMA) Fractional differencing.
"""

from typing import Dict, Any, Optional
import OpenGL.GL as gl
from .api import EffectPlugin, PluginContext

logger = __import__('logging').getLogger(__name__)

METADATA = {
    "name": "BackgroundSubtraction",
    "version": "3.0.0",
    "description": "GPU accelerated Exponential Moving Average background differencing.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "visual",
    "tags": ["background", "subtraction", "silhouette", "masking", "gpu"],
    "priority": 1,
    "dependencies": [],
    "incompatible": [],
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "history", "type": "float", "default": 500, "min": 1, "max": 1000},
        {"name": "varThreshold", "type": "float", "default": 16.0, "min": 1.0, "max": 100.0},
        {"name": "detectShadows", "type": "float", "default": 1.0, "min": 0.0, "max": 1.0},
        {"name": "silhouetteColor_0", "type": "float", "default": 1.0, "min": 0.0, "max": 1.0},
        {"name": "silhouetteColor_1", "type": "float", "default": 1.0, "min": 0.0, "max": 1.0},
        {"name": "silhouetteColor_2", "type": "float", "default": 1.0, "min": 0.0, "max": 1.0},
        {"name": "silhouetteColor_3", "type": "float", "default": 1.0, "min": 0.0, "max": 1.0},
        {"name": "backgroundColor_0", "type": "float", "default": 0.0, "min": 0.0, "max": 1.0},
        {"name": "backgroundColor_1", "type": "float", "default": 0.0, "min": 0.0, "max": 1.0},
        {"name": "backgroundColor_2", "type": "float", "default": 0.0, "min": 0.0, "max": 1.0},
        {"name": "backgroundColor_3", "type": "float", "default": 1.0, "min": 0.0, "max": 1.0}
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

UPDATE_BG_FRAGMENT_SHADER = """
#version 330 core

in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex_current;
uniform sampler2D tex_bg_old;
uniform float learning_rate;

void main() {
    vec3 current = texture(tex_current, uv).rgb;
    vec3 bg_old = texture(tex_bg_old, uv).rgb;
    
    // Exponential Moving Average (EMA) update
    vec3 new_bg = mix(bg_old, current, learning_rate);
    fragColor = vec4(new_bg, 1.0);
}
"""

RENDER_SILHOUETTE_FRAGMENT_SHADER = """
#version 330 core

in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex_current;
uniform sampler2D tex_bg;

uniform float u_mix; // Legacy Global blending signal context assumption
uniform float threshold;
uniform vec4 silhouette_color;
uniform vec4 background_color;
uniform float detect_shadows; // Reserved for luminance check modifiers if desired natively

void main() {
    vec4 current = texture(tex_current, uv);
    vec4 bg = texture(tex_bg, uv);
    
    // Convert to grayscale for robust color-distance
    float cur_gray = dot(current.rgb, vec3(0.299, 0.587, 0.114));
    float bg_gray = dot(bg.rgb, vec3(0.299, 0.587, 0.114));
    
    float luma_diff = abs(cur_gray - bg_gray);
    float color_dist = distance(current.rgb, bg.rgb);
    
    // Synthesized difference tracking metric
    float diff = mix(color_dist, luma_diff, 0.5);
    
    // Base mask determination mapping the threshold (mapped from legacy 1.0-100.0 against 0.0-1.0 normalization)
    float mask_value = step(threshold, diff); 
    
    vec4 silhouette = silhouette_color * mask_value;
    vec4 bg_result = background_color;
    vec4 result = mix(bg_result, silhouette, mask_value);
    
    // Mix with raw input frame linearly (often passed as u_mix 1.0 for full coverage)
    fragColor = mix(current, result, 1.0);
}
"""

class BackgroundSubtractionPlugin(EffectPlugin):
    def __init__(self):
        super().__init__()
        self.update_program = 0
        self.render_program = 0
        
        self.target_fbo = 0
        self.target_texture = 0
        
        # Ping-pong background storage
        self.bg_fbos = [0, 0]
        self.bg_textures = [0, 0]
        self.current_bg_idx = 0
        
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
            logger.error(f"BgSub VS fail: {err}")
            return 0

        fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragment_shader, fs_src)
        gl.glCompileShader(fragment_shader)
        if not gl.glGetShaderiv(fragment_shader, gl.GL_COMPILE_STATUS):
            err = gl.glGetShaderInfoLog(fragment_shader)
            logger.error(f"BgSub FS fail: {err}")
            return 0

        program = gl.glCreateProgram()
        gl.glAttachShader(program, vertex_shader)
        gl.glAttachShader(program, fragment_shader)
        gl.glLinkProgram(program)
        
        if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
            err = gl.glGetProgramInfoLog(program)
            logger.error(f"BgSub link fail: {err}")
            return 0
            
        gl.glDeleteShader(vertex_shader)
        gl.glDeleteShader(fragment_shader)
        return program

    def initialize(self, context: PluginContext) -> bool:
        if not hasattr(gl, 'glCreateProgram'):
            logger.warning("Mock mode engaged. Skipping GL init.")
            return True

        try:
            self.update_program = self._compile_shader(VERTEX_SHADER_SOURCE, UPDATE_BG_FRAGMENT_SHADER)
            self.render_program = self._compile_shader(VERTEX_SHADER_SOURCE, RENDER_SILHOUETTE_FRAGMENT_SHADER)
            
            if not self.update_program or not self.render_program: return False
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to init BackgroundSubtractionPlugin: {e}")
            return False

    def _setup_target_fbos(self, width: int, height: int):
        if self.width == width and self.height == height and self.target_fbo != 0:
            return

        if self.target_fbo != 0:
            gl.glDeleteFramebuffers(1, [self.target_fbo])
            gl.glDeleteTextures(1, [self.target_texture])
            
            gl.glDeleteFramebuffers(1, [self.bg_fbos[0]])
            gl.glDeleteTextures(1, [self.bg_textures[0]])
            gl.glDeleteFramebuffers(1, [self.bg_fbos[1]])
            gl.glDeleteTextures(1, [self.bg_textures[1]])

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
        
        # Ping Pong BG FBOs
        for i in range(2):
            self.bg_fbos[i] = gl.glGenFramebuffers(1)
            self.bg_textures[i] = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.bg_textures[i])
            # Blank initialization 
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.bg_fbos[i])
            gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.bg_textures[i], 0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        self.current_bg_idx = 0

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
        
        read_idx = self.current_bg_idx
        write_idx = 1 - self.current_bg_idx
        
        # Mapped Params
        history = float(params.get("history", 500))
        var_threshold = float(params.get("varThreshold", 16.0))
        detect_shadows = float(params.get("detectShadows", 1.0))
        
        # Parameter normalizing mapping
        # History (1..1000) mapped to learning rate (1.0..0.001)
        learning_rate = 1.0 / max(1.0, history) 
        
        # VarThreshold (1..100) mapped to distance (0.001..0.5) roughly
        threshold = (var_threshold / 100.0) * 0.5 
        
        sc0 = float(params.get("silhouetteColor_0", 1.0))
        sc1 = float(params.get("silhouetteColor_1", 1.0))
        sc2 = float(params.get("silhouetteColor_2", 1.0))
        sc3 = float(params.get("silhouetteColor_3", 1.0))
        
        bc0 = float(params.get("backgroundColor_0", 0.0))
        bc1 = float(params.get("backgroundColor_1", 0.0))
        bc2 = float(params.get("backgroundColor_2", 0.0))
        bc3 = float(params.get("backgroundColor_3", 1.0))
        
        # ------------------------------------------------------------------------
        # PASS 1: Calculate and Update Persistent Background Matrix (EMA Tracker)
        # ------------------------------------------------------------------------
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.bg_fbos[write_idx])
        gl.glViewport(0, 0, w, h)
        
        gl.glUseProgram(self.update_program)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.update_program, "tex_current"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.bg_textures[read_idx])
        gl.glUniform1i(gl.glGetUniformLocation(self.update_program, "tex_bg_old"), 1)
        
        gl.glUniform1f(gl.glGetUniformLocation(self.update_program, "learning_rate"), learning_rate)
        
        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        
        # ------------------------------------------------------------------------
        # PASS 2: Render Subtracted Mask onto final Viewport Target
        # ------------------------------------------------------------------------
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.target_fbo)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        gl.glUseProgram(self.render_program)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.render_program, "tex_current"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        # Use our newly evaluated background!
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.bg_textures[write_idx])
        gl.glUniform1i(gl.glGetUniformLocation(self.render_program, "tex_bg"), 1)
        
        gl.glUniform1f(gl.glGetUniformLocation(self.render_program, "threshold"), threshold)
        gl.glUniform1f(gl.glGetUniformLocation(self.render_program, "detect_shadows"), detect_shadows)
        
        gl.glUniform4f(gl.glGetUniformLocation(self.render_program, "silhouette_color"), sc0, sc1, sc2, sc3)
        gl.glUniform4f(gl.glGetUniformLocation(self.render_program, "background_color"), bc0, bc1, bc2, bc3)
        
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        
        gl.glBindVertexArray(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        self.current_bg_idx = write_idx
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.target_texture
            
        return self.target_texture

    def cleanup(self) -> None:
        try:
            if hasattr(gl, 'glDeleteProgram'):
                if self.update_program != 0: gl.glDeleteProgram(self.update_program)
                if self.render_program != 0: gl.glDeleteProgram(self.render_program)
            if hasattr(gl, 'glDeleteFramebuffers'): 
                if self.target_fbo != 0: gl.glDeleteFramebuffers(1, [self.target_fbo])
                if self.bg_fbos[0] != 0: gl.glDeleteFramebuffers(1, [self.bg_fbos[0]])
                if self.bg_fbos[1] != 0: gl.glDeleteFramebuffers(1, [self.bg_fbos[1]])
            if hasattr(gl, 'glDeleteTextures'):
                if self.target_texture != 0: gl.glDeleteTextures(1, [self.target_texture])
                if self.bg_textures[0] != 0: gl.glDeleteTextures(1, [self.bg_textures[0]])
                if self.bg_textures[1] != 0: gl.glDeleteTextures(1, [self.bg_textures[1]])
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao != 0:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Failed to cleanup BackgroundSubtraction plugin: {e}")
        finally:
            self.update_program = 0
            self.render_program = 0
            self.target_fbo = 0
            self.target_texture = 0
            self.bg_fbos = [0, 0]
            self.bg_textures = [0, 0]
            self.empty_vao = 0

