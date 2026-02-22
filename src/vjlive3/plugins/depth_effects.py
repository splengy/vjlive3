import os
import logging
from typing import Dict, Any, Optional
import numpy as np

from vjlive3.plugins.api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

try:
    if os.environ.get("PYTEST_MOCK_GL"):
        raise ImportError("Forced MOCK GL for pytest")
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
    gl = None

# We use two shaders: ONE for converting the depth into an internal 3D point cloud, 
# and TWO to composite the generated point cloud onto the video frame.

PC_VERTEX_SHADER = """
#version 330 core
layout(location=0) in vec2 uv_in;

uniform sampler2D depth_in;
uniform mat4 mvp;
uniform float point_size;
uniform float min_depth;
uniform float max_depth;

out vec4 v_color;

void main() {
    float raw_depth = texture(depth_in, uv_in).r; // 0..1 generally
    
    // Project UV to -1..1 X/Y
    float x = uv_in.x * 2.0 - 1.0;
    float y = uv_in.y * 2.0 - 1.0;
    
    // Map depth to depth scale limits. If out of bounds, push completely away
    float real_depth = raw_depth * 10.0; // scale up to 10 meters roughly representing standard hardware bounds
    
    if (real_depth < min_depth || real_depth > max_depth || raw_depth == 0.0) {
        gl_Position = vec4(0.0, 0.0, 2000.0, 1.0); // Sent far behind clipping plane
        gl_PointSize = 0.0;
    } else {
        // Perspective translation offset
        vec3 pos = vec3(x, y, (raw_depth * 2.0 - 1.0));
        gl_Position = mvp * vec4(pos, 1.0);
        gl_PointSize = point_size;
        
        float t = clamp((real_depth - min_depth) / (max_depth - min_depth + 0.0001), 0.0, 1.0);
        vec3 color = mix(vec3(0.0, 0.0, 1.0), vec3(1.0, 0.0, 0.0), t);
        v_color = vec4(color, 1.0);
    }
}
"""

PC_FRAGMENT_SHADER = """
#version 330 core
in vec4 v_color;
out vec4 fragColor;

void main() {
    // Generate soft circular point
    vec2 coord = gl_PointCoord - vec2(0.5);
    if (dot(coord, coord) > 0.25) discard;
    fragColor = v_color;
}
"""

COMPOSITE_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D point_cloud_tex;
uniform float u_mix;

void main() {
    vec4 video = texture(tex0, v_uv);
    vec4 pcloud = texture(point_cloud_tex, v_uv);
    
    // Additive blending for the point cloud over the video
    fragColor = mix(video, video + pcloud, pcloud.a * u_mix);
}
"""

METADATA = {
    "name": "Depth Effects",
    "description": "Advanced 3D point cloud visualization composited over the original video stream.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["3d", "point-cloud", "depth", "composite"],
    "status": "active",
    "parameters": [
        {"name": "pointSize", "type": "float", "min": 0.0, "max": 10.0, "default": 2.0},
        {"name": "pointDensity", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
        {"name": "minDepth", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
        {"name": "maxDepth", "type": "float", "min": 0.0, "max": 10.0, "default": 8.0},
        {"name": "cameraDistance", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthEffectsPlugin(EffectPlugin):
    """P3-VD36: Depth Effects port for 3D point cloud visualization."""
    
    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        
        self.pc_prog = None
        self.comp_prog = None
        
        self.fbo = None
        self.texture = None
        
        self.pc_vao = None
        self.pc_vbo = None
        self.num_points = 0
        
        self.quad_vao = None
        self.quad_vbo = None

    def _compile_shader(self, vs_src, fs_src):
        if not HAS_GL: return None
        try:
            vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
            gl.glShaderSource(vertex, vs_src)
            gl.glCompileShader(vertex)
            
            fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fragment, fs_src)
            gl.glCompileShader(fragment)
            
            if gl.glGetShaderiv(fragment, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
                logger.error(f"Fragment compile failed: {gl.glGetShaderInfoLog(fragment)}")
                return None
            if gl.glGetShaderiv(vertex, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
                logger.error(f"Vertex compile failed: {gl.glGetShaderInfoLog(vertex)}")
                return None
                
            prog = gl.glCreateProgram()
            gl.glAttachShader(prog, vertex)
            gl.glAttachShader(prog, fragment)
            gl.glLinkProgram(prog)
            return prog
        except Exception as e:
            logger.error(f"Compile error: {e}")
            return None

    def initialize(self, context: PluginContext) -> None:
        super().initialize(context)
        if self._mock_mode: return

        try:
            # 1. Point Cloud Shader (3D)
            self.pc_prog = self._compile_shader(PC_VERTEX_SHADER, PC_FRAGMENT_SHADER)
            # 2. Composite Shader (2D)
            quad_vs = "#version 330 core\\nlayout(location=0) in vec2 pos; layout(location=1) in vec2 uv; out vec2 v_uv; void main() { gl_Position = vec4(pos, 0.0, 1.0); v_uv = uv; }"
            self.comp_prog = self._compile_shader(quad_vs, COMPOSITE_FRAGMENT)
            
            if not self.pc_prog or not self.comp_prog:
                self._mock_mode = True
                return

            # Setup FBO for point cloud render
            self.texture = gl.glGenTextures(1)
            self.fbo = gl.glGenFramebuffers(1)

            # Setup Quad VAO for final composite
            self.quad_vao = gl.glGenVertexArrays(1)
            self.quad_vbo = gl.glGenBuffers(1)
            gl.glBindVertexArray(self.quad_vao)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.quad_vbo)
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
            
            # Setup Point VAO grid
            # Generate a 320x240 UV grid for sampling the depth map.
            w_pts, h_pts = 320, 240
            self.num_points = w_pts * h_pts
            uv_grid = []
            for y in range(h_pts):
                for x in range(w_pts):
                    uv_grid.extend([x / float(w_pts), y / float(h_pts)])
            
            pts_data = np.array(uv_grid, dtype=np.float32)
            self.pc_vao = gl.glGenVertexArrays(1)
            self.pc_vbo = gl.glGenBuffers(1)
            gl.glBindVertexArray(self.pc_vao)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.pc_vbo)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, pts_data.nbytes, pts_data, gl.GL_STATIC_DRAW)
            gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 8, gl.ctypes.c_void_p(0))
            gl.glEnableVertexAttribArray(0)

            gl.glBindVertexArray(0)

        except Exception as e:
            logger.warning(f"Failed GL boot in DepthEffects: {e}")
            self._mock_mode = True

    def _map_param(self, params, name, out_min, out_max, default_val):
        val = params.get(name, default_val)
        return out_min + (val / 10.0) * (out_max - out_min)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if input_texture is None or input_texture == 0:
            return 0
        if self._mock_mode:
            context.outputs["video_out"] = input_texture
            return input_texture

        try:
            depth_in = context.inputs.get("depth_in", input_texture)

            # Get target dimensions
            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            h = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_HEIGHT)

            # Reallocate FBO if needed
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            tex_w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            if tex_w != w:
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
                gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.texture, 0)
                
            # ------ PASS 1: Render Point Cloud into FBO ------
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
            gl.glViewport(0, 0, w, h)
            gl.glClearColor(0.0, 0.0, 0.0, 0.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            
            gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE) # Additive
            
            gl.glUseProgram(self.pc_prog)
            
            # Map parameters
            point_size = self._map_param(params, 'pointSize', 0.1, 20.0, 2.0)
            min_depth = self._map_param(params, 'minDepth', 0.0, 5.0, 1.0)
            max_depth = self._map_param(params, 'maxDepth', 0.0, 10.0, 8.0)
            cam_dist = self._map_param(params, 'cameraDistance', 0.5, 10.0, 5.0)

            gl.glUniform1f(gl.glGetUniformLocation(self.pc_prog, "point_size"), point_size)
            gl.glUniform1f(gl.glGetUniformLocation(self.pc_prog, "min_depth"), min_depth)
            gl.glUniform1f(gl.glGetUniformLocation(self.pc_prog, "max_depth"), max_depth)
            
            # Simple Ortho scaling MVP equivalent for 3D point array translation
            scale = 2.0 / max(cam_dist, 0.1)
            mvp = np.array([
                scale, 0, 0, 0,
                0, scale, 0, 0,
                0, 0, scale, 0,
                0, 0, 0, 1
            ], dtype=np.float32)
            gl.glUniformMatrix4fv(gl.glGetUniformLocation(self.pc_prog, "mvp"), 1, gl.GL_FALSE, mvp)
            
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.pc_prog, "depth_in"), 0)

            gl.glBindVertexArray(self.pc_vao)
            
            # Density slider scales number of rendered points
            density = self._map_param(params, 'pointDensity', 0.01, 1.0, 1.0)
            render_points = int(self.num_points * density)
            gl.glDrawArrays(gl.GL_POINTS, 0, render_points)
            
            gl.glBindVertexArray(0)
            gl.glDisable(gl.GL_PROGRAM_POINT_SIZE)
            gl.glDisable(gl.GL_BLEND)
            
            # ------ PASS 2: Composite Point Cloud FBO over Video into FBO (or we could just return FBO if it's additive, but spec requires composite) ------
            # We will use the same texture by rendering the quad back into a new buffer, or since EffectPlugin chaining usually accepts the output texture, we can return a new texture... Wait, if we return self.texture, it only has the point cloud. We want point cloud OVER video!
            # Let's read from input_texture and self.texture and write to the output. We need a secondary FBO for this.
            # However, standard VJLive3 effect plugins modify self.texture and return it. Let's create an output_fbo.
            if not hasattr(self, 'out_tex'):
                self.out_tex = gl.glGenTextures(1)
                self.out_fbo = gl.glGenFramebuffers(1)
                
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.out_tex)
            o_w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            if o_w != w:
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.out_fbo)
                gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.out_tex, 0)
                
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.out_fbo)
            gl.glViewport(0, 0, w, h)
            gl.glUseProgram(self.comp_prog)
            
            gl.glUniform1f(gl.glGetUniformLocation(self.comp_prog, "u_mix"), params.get("u_mix", 1.0))
            
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            gl.glUniform1i(gl.glGetUniformLocation(self.comp_prog, "tex0"), 0)
            
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            gl.glUniform1i(gl.glGetUniformLocation(self.comp_prog, "point_cloud_tex"), 1)
            
            gl.glBindVertexArray(self.quad_vao)
            gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
            gl.glBindVertexArray(0)
            
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            
            context.outputs["video_out"] = self.out_tex
            return self.out_tex
            
        except Exception as e:
            logger.error(f"Render failed: {e}")
            return input_texture

    def cleanup(self) -> None:
        if not self._mock_mode:
            try:
                for t in [self.texture, getattr(self, 'out_tex', None)]:
                    if t: gl.glDeleteTextures(1, [t])
                for f in [self.fbo, getattr(self, 'out_fbo', None)]:
                    if f: gl.glDeleteFramebuffers(1, [f])
                for vao in [self.pc_vao, self.quad_vao]:
                    if vao: gl.glDeleteVertexArrays(1, [vao])
                for vbo in [self.pc_vbo, self.quad_vbo]:
                    if vbo: gl.glDeleteBuffers(1, [vbo])
                if self.pc_prog: gl.glDeleteProgram(self.pc_prog)
                if self.comp_prog: gl.glDeleteProgram(self.comp_prog)
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                
        self.texture = None
        self.fbo = None
