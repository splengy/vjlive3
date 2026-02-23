"""
P3-VD37: Depth Point Cloud Effect (2D Pseudo-Cloud)
Ported from VJlive-2 legacy implementation.

Maps depth values to a blue-to-red color gradient while adding
synthetic sinusoidal noise.
"""

from typing import Dict, Any, Optional
import ctypes
import OpenGL.GL as gl
from .api import EffectPlugin, PluginContext

METADATA = {
    "name": "DepthPointCloud",
    "version": "3.0.0",
    "description": "2D pseudo-point cloud effect mapping depth to gradient and noise",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "visual",
    "tags": ["depth", "point_cloud", "false_color", "noise"],
    "priority": 10,
    "dependencies": [],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "point_size", "type": "float", "default": 2.0, "min": 0.1, "max": 20.0},
        {"name": "point_density", "type": "float", "default": 1.0, "min": 0.01, "max": 1.0},
        {"name": "min_depth", "type": "float", "default": 1.0, "min": 0.0, "max": 5.0},
        {"name": "max_depth", "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
        {"name": "mix_amount", "type": "float", "default": 1.0, "min": 0.0, "max": 1.0}
    ]
}

FRAGMENT_SOURCE = """#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;        // Original video
uniform sampler2D depth_tex;   // Depth data
uniform float u_mix;           // mix_amount
uniform float point_size;      // Inherited from legacy (unused in fragment but preserved for interface compatibility)
uniform float min_depth;
uniform float max_depth;
uniform float has_depth;
uniform vec2 resolution;

// Depth-based color mapping
vec3 depth_to_color(float depth_val) {
    float safe_diff = max(max_depth - min_depth, 0.0001);
    float t = clamp((depth_val - min_depth) / safe_diff, 0.0, 1.0);
    return mix(vec3(0.0, 0.0, 1.0), vec3(1.0, 0.0, 0.0), t);
}

void main() {
    vec4 original = texture(tex0, uv);

    if (has_depth > 0.0) {
        // Evaluate native distance representation dynamically bounded
        float safe_diff = max(max_depth - min_depth, 0.0001);
        float depth = texture(depth_tex, uv).r * safe_diff + min_depth;

        if (depth > min_depth && depth < max_depth) {
            // Create depth-based visualization gradient
            vec3 depth_color = depth_to_color(depth);

            // Add synthetic sinusoidal noise/interference effect based on depth
            float noise = sin(uv.x * 100.0 + depth * 10.0) * 0.1;
            depth_color += vec3(noise);

            // Blend with original video
            fragColor = vec4(mix(original.rgb, depth_color, u_mix * 0.5), original.a);
        } else {
            fragColor = original;
        }
    } else {
        fragColor = original;
    }
}
"""

class DepthPointCloudPlugin(EffectPlugin):
    """
    Depth Point Cloud Effect for VJLive3.
    Applies a colorized noise pass over standard video guided by a depth texture.
    """
    def __init__(self):
        super().__init__()
        self.program = 0
        self.fbo = 0
        self.target_texture = 0
        self.width = 0
        self.height = 0
        self._initialized = False

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> bool:
        """Compile internal shader and generate FBO."""
        if not hasattr(gl, 'glCreateProgram'):
            return False
            
        try:
            # Vertex shader (Standard passthrough)
            vs_source = """#version 330 core
            layout (location = 0) in vec3 aPos;
            layout (location = 1) in vec2 aTexCoords;
            out vec2 uv;
            void main() {
                uv = aTexCoords;
                gl_Position = vec4(aPos.x, aPos.y, 0.0, 1.0);
            }
            """
            
            # Use shader compiler from context if available, otherwise manual compile
            if context and hasattr(context, 'engine') and context.engine:
                try:
                    self.program = context.engine.compilers['shader'].compile(vs_source, FRAGMENT_SOURCE)
                except Exception:
                    self.program = self._compile_shader_fallback(vs_source, FRAGMENT_SOURCE)
            else:
                self.program = self._compile_shader_fallback(vs_source, FRAGMENT_SOURCE)
                
            if self.program == 0:
                return False

            self._initialized = True
            return True
            
        except Exception:
            return False

    def _compile_shader_fallback(self, vs: str, fs: str) -> int:
        """Fallback compiler for direct OpenGL loading"""
        vs_id = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs_id, vs)
        gl.glCompileShader(vs_id)
        if not gl.glGetShaderiv(vs_id, gl.GL_COMPILE_STATUS):
            gl.glDeleteShader(vs_id)
            return 0
            
        fs_id = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs_id, fs)
        gl.glCompileShader(fs_id)
        if not gl.glGetShaderiv(fs_id, gl.GL_COMPILE_STATUS):
            gl.glDeleteShader(vs_id)
            gl.glDeleteShader(fs_id)
            return 0
            
        prog = gl.glCreateProgram()
        gl.glAttachShader(prog, vs_id)
        gl.glAttachShader(prog, fs_id)
        gl.glLinkProgram(prog)
        
        gl.glDeleteShader(vs_id)
        gl.glDeleteShader(fs_id)
        
        if not gl.glGetProgramiv(prog, gl.GL_LINK_STATUS):
            gl.glDeleteProgram(prog)
            return 0
            
        return prog

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        """Render the depth point cloud false color mapping."""
        if not self._initialized or self.program == 0:
            return input_texture

        has_gl = hasattr(gl, 'glBindFramebuffer')
        if not has_gl:
            return input_texture
            
        # 1. Update Resolution
        w = params.get("width", 1920)
        h = params.get("height", 1080)
        self._ensure_fbo(w, h)
        
        # 2. Get the depth map from context
        depth_tex = 0
        if context and hasattr(context, 'textures') and "depth_map" in context.textures:
            depth_tex = context.textures["depth_map"]
            
        # 3. Render Pass
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        gl.glUseProgram(self.program)
        
        # Bind Texture 0: Original Video
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "tex0"), 0)
        
        # Bind Texture 1: Depth Map 
        has_depth_val = 0.0
        if depth_tex > 0:
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_tex)
            gl.glUniform1i(gl.glGetUniformLocation(self.program, "depth_tex"), 1)
            has_depth_val = 1.0
            
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "has_depth"), has_depth_val)
        
        # Mapping Uniforms
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "u_mix"), float(params.get("mix_amount", 1.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "point_size"), float(params.get("point_size", 2.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "min_depth"), float(params.get("min_depth", 1.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "max_depth"), float(params.get("max_depth", 8.0)))
        gl.glUniform2f(gl.glGetUniformLocation(self.program, "resolution"), float(w), float(h))
        
        # Draw Quad (assumes global quad is available or we bypass inside standard pipeline)
        self._draw_quad()
        
        # Restore State
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glUseProgram(0)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        
        return self.target_texture

    def _ensure_fbo(self, w: int, h: int):
        """Create or resize FBO."""
        if self.width == w and self.height == h and self.fbo != 0:
            return
            
        self.width = w
        self.height = h
        
        if self.fbo != 0:
            gl.glDeleteFramebuffers(1, [self.fbo])
            gl.glDeleteTextures(1, [self.target_texture])
            
        self.fbo = gl.glGenFramebuffers(1)
        self.target_texture = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.target_texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.target_texture, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _draw_quad(self):
        """Draw fullscreen quad avoiding VAO dependencies for raw test harnesses"""
        quad_vao = gl.glGenVertexArrays(1)
        quad_vbo = gl.glGenBuffers(1)
        
        gl.glBindVertexArray(quad_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, quad_vbo)
        
        # x, y, z, u, v
        vertices = (gl.GLfloat * 20)(
            -1.0, -1.0, 0.0, 0.0, 0.0,
             1.0, -1.0, 0.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 0.0, 1.0,
             1.0,  1.0, 0.0, 1.0, 1.0
        )
        
        gl.glBufferData(gl.GL_ARRAY_BUFFER, ctypes.sizeof(vertices), vertices, gl.GL_STATIC_DRAW)
        
        # Position
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 5 * ctypes.sizeof(gl.GLfloat), ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        # TexCoords
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 5 * ctypes.sizeof(gl.GLfloat), ctypes.c_void_p(3 * ctypes.sizeof(gl.GLfloat)))
        gl.glEnableVertexAttribArray(1)
        
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        
        gl.glDeleteBuffers(1, [quad_vbo])
        gl.glDeleteVertexArrays(1, [quad_vao])

    def cleanup(self):
        """Release OpenGL resources."""
        if hasattr(gl, 'glDeleteProgram') and self.program != 0:
            gl.glDeleteProgram(self.program)
            self.program = 0
            
        if hasattr(gl, 'glDeleteFramebuffers') and self.fbo != 0:
            gl.glDeleteFramebuffers(1, [self.fbo])
            self.fbo = 0
            
        if hasattr(gl, 'glDeleteTextures') and self.target_texture != 0:
            gl.glDeleteTextures(1, [self.target_texture])
            self.target_texture = 0
            
        self._initialized = False

def create_plugin() -> EffectPlugin:
    return DepthPointCloudPlugin()
