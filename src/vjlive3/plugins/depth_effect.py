import os
import logging
from typing import Dict, Any, Optional
import numpy as np


logger = logging.getLogger(__name__)

try:
    if os.environ.get("PYTEST_MOCK_GL"):
        raise ImportError("Forced MOCK GL for pytest")
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
    gl = None

DEPTH_EFFECT_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;        // Original video
uniform sampler2D depth_tex;   // Depth data
uniform float u_mix;
uniform float min_depth;
uniform float max_depth;
uniform vec2 resolution;

// Depth-based color mapping
vec3 depth_to_color(float depth) {
    float t = clamp((depth - min_depth) / max(max_depth - min_depth, 0.001), 0.0, 1.0);
    return mix(vec3(0.0, 0.0, 1.0), vec3(1.0, 0.0, 0.0), t);
}

void main() {
    vec4 original = texture(tex0, v_uv);
    float depth = texture(depth_tex, v_uv).r * (max_depth - min_depth) + min_depth;

    if (depth > min_depth && depth < max_depth) {
        // Create depth-based visualization
        vec3 depth_color = depth_to_color(depth);

        // Add some noise/interference effect based on depth
        float noise = sin(v_uv.x * 100.0 + depth * 10.0) * 0.1;
        depth_color += vec3(noise);

        // Blend with original
        fragColor = vec4(mix(original.rgb, depth_color, u_mix * 0.5), original.a);
    } else {
        fragColor = original;
    }
}
"""

METADATA = {
    "name": "Depth Effects",
    "description": "Base depth visualization effect. Renders depth data as a colored interferance overlay.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["depth", "effects", "base"],
    "status": "active",
    "parameters": [
        {"name": "minDepth", "type": "float", "min": 0.0, "max": 10.0, "default": 2.0},
        {"name": "maxDepth", "type": "float", "min": 0.0, "max": 10.0, "default": 8.0},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}


class DepthEffectPlugin(object):
    """P3-VD36: Depth Effects base class ported to a pure GPU VJLive3 plugin."""
    
    def __init__(self) -> None:
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.texture: Optional[int] = None
        self.fbo: Optional[int] = None

    def _compile_shader(self):
        if not HAS_GL: return None
        try:
            vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
            gl.glShaderSource(vertex, "#version 330 core\\nlayout(location=0) in vec2 pos; layout(location=1) in vec2 uv; out vec2 v_uv; void main() { gl_Position = vec4(pos, 0.0, 1.0); v_uv = uv; }")
            gl.glCompileShader(vertex)
            
            fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fragment, DEPTH_EFFECT_FRAGMENT)
            gl.glCompileShader(fragment)
            
            if gl.glGetShaderiv(fragment, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
                logger.error(f"Fragment compile failed: {gl.glGetShaderInfoLog(fragment)}")
                return None
                
            prog = gl.glCreateProgram()
            gl.glAttachShader(prog, vertex)
            gl.glAttachShader(prog, fragment)
            gl.glLinkProgram(prog)
            return prog
        except Exception as e:
            logger.error(f"Failed to compile shader locally: {e}")
            return None

    def initialize(self, context) -> None:
        super().initialize(context)
        if self._mock_mode:
            return
            
        try:
            self.prog = self._compile_shader()
            if not self.prog:
                self._mock_mode = True
                return

            tex_id = gl.glGenTextures(1)
            fbo_id = gl.glGenFramebuffers(1)
            if isinstance(tex_id, list): tex_id = tex_id[0]
            if isinstance(fbo_id, list): fbo_id = fbo_id[0]
                
            self.texture = tex_id
            self.fbo = fbo_id
                
            self.vao = gl.glGenVertexArrays(1)
            self.vbo = gl.glGenBuffers(1)
            gl.glBindVertexArray(self.vao)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
            
            quad_data = np.array([
                -1.0, -1.0,  0.0, 0.0,
                 1.0, -1.0,  1.0, 0.0,
                -1.0,  1.0,  0.0, 1.0,
                 1.0,  1.0,  1.0, 1.0
            ], dtype=np.float32)
            
            gl.glBufferData(gl.GL_ARRAY_BUFFER, quad_data.nbytes, quad_data, gl.GL_STATIC_DRAW)
            gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(0))
            gl.glEnableVertexAttribArray(0)
            gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(8))
            gl.glEnableVertexAttribArray(1)
            gl.glBindVertexArray(0)
            
        except Exception as e:
#             logger.warning(f"Failed to initialize GL FBOs inside DepthEffectPlugin: {e}")
            self._mock_mode = True

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if input_texture is None or input_texture == 0:
            return 0
            
        if self._mock_mode:
            context.outputs["video_out"] = input_texture
            return input_texture

        try:
            depth_in = context.inputs.get("depth_in", input_texture)

            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            h = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_HEIGHT)
            
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            tex_w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            if tex_w != w:
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
                gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.texture, 0)
                
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
            gl.glViewport(0, 0, w, h)
            
            gl.glUseProgram(self.prog)
            
            gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), params.get("u_mix", 1.0))
            
            # Map parameters
            min_depth_val = 0.0 + (params.get('minDepth', 2.0) / 10.0) * 5.0
            max_depth_val = 0.0 + (params.get('maxDepth', 8.0) / 10.0) * 10.0
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "min_depth"), min_depth_val)
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "max_depth"), max_depth_val)
            
            # Textures
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
            
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 1)
            
            gl.glBindVertexArray(self.vao)
            gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
            gl.glBindVertexArray(0)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            
            context.outputs["video_out"] = self.texture
            return self.texture
            
        except Exception as e:
            logger.error(f"Render failed in Depth Effect: {e}")
            return input_texture

    def cleanup(self) -> None:
        if not self._mock_mode:
            try:
                if self.texture is not None:
                    gl.glDeleteTextures(1, [self.texture])
                if self.fbo is not None:
                    gl.glDeleteFramebuffers(1, [self.fbo])
                if self.prog:
                    gl.glDeleteProgram(self.prog)
                if hasattr(self, 'vao') and self.vao:
                    gl.glDeleteVertexArrays(1, [self.vao])
                if hasattr(self, 'vbo') and self.vbo:
                    gl.glDeleteBuffers(1, [self.vbo])
            except Exception as e:
                logger.error(f"Error cleaning up FBOs/Textures during DepthEffect unload: {e}")
                
        self.texture = None
        self.fbo = None
