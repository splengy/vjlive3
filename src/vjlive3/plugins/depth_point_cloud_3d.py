import os
import math
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

BLIT_VERTEX = """
#version 330 core
layout(location=0) in vec2 pos;
layout(location=1) in vec2 uv;
out vec2 v_uv;
void main() {
    gl_Position = vec4(pos, 0.0, 1.0);
    v_uv = uv;
}
"""

BLIT_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;
uniform sampler2D tex0;
void main() {
    fragColor = texture(tex0, v_uv);
}
"""

POINT_3D_VERTEX = """
#version 330 core
uniform sampler2D depth_tex;
uniform int tex_width;
uniform int tex_height;
uniform float min_depth;
uniform float max_depth;
uniform float point_size;
uniform float point_density;
uniform mat4 mvp;

out vec4 v_color;

void main() {
    int x = gl_VertexID % tex_width;
    int y = gl_VertexID / tex_width;
    
    // Simulate density by culling
    if (point_density < 1.0) {
        int step = max(1, int(1.0 / max(point_density, 0.01)));
        if (x % step != 0 || y % step != 0) {
            gl_Position = vec4(2.0, 2.0, 2.0, 1.0); // Discard
            return;
        }
    }
    
    float raw_d = texelFetch(depth_tex, ivec2(x, y), 0).r;
    float depth = raw_d * (max_depth - min_depth) + min_depth;
    
    if (raw_d < 0.01 || depth < min_depth || depth > max_depth) {
        gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
        return;
    }
    
    float focal_length = 570.0;
    float cx = float(tex_width) / 2.0;
    float cy = float(tex_height) / 2.0;

    float world_x = (float(x) - cx) * depth / focal_length;
    float world_y = (float(y) - cy) * depth / focal_length;
    float world_z = depth;
    
    gl_Position = mvp * vec4(world_x, -world_y, world_z, 1.0);
    gl_PointSize = point_size;
    
    float t = clamp((depth - min_depth) / max(max_depth - min_depth, 0.001), 0.0, 1.0);
    v_color = vec4(t, 0.5, 1.0 - t, 1.0);
}
"""

POINT_3D_FRAGMENT = """
#version 330 core
in vec4 v_color;
out vec4 fragColor;
uniform float u_mix;

void main() {
    // Make points circular
    vec2 coord = gl_PointCoord - vec2(0.5);
    if (dot(coord, coord) > 0.25) {
        discard;
    }
    fragColor = vec4(v_color.rgb, u_mix);
}
"""

METADATA = {
    "name": "Depth Point Cloud 3D",
    "description": "True 3D point cloud rendering of depth data with a fully adjustable camera.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["depth", "pointcloud", "3D", "camera", "particles"],
    "status": "active",
    "parameters": [
        {"name": "pointSize", "type": "float", "min": 0.0, "max": 10.0, "default": 2.0},
        {"name": "pointDensity", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
        {"name": "minDepth", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
        {"name": "maxDepth", "type": "float", "min": 0.0, "max": 10.0, "default": 8.0},
        {"name": "cameraDistance", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "cameraAngleX", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "cameraAngleY", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}


class DepthPointCloud3DPlugin(EffectPlugin):
    """P3-VD38: Depth Effects Point Cloud 3D."""
    
    def __init__(self) -> None:
        super().__init__()
        self._mock_mode = not HAS_GL
        self.blit_prog = None
        self.prog = None
        
        self.texture: Optional[int] = None
        self.fbo: Optional[int] = None

    def _compile_shader(self, v_src, f_src):
        if not HAS_GL: return None
        try:
            vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
            gl.glShaderSource(vertex, v_src)
            gl.glCompileShader(vertex)
            
            fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fragment, f_src)
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

    def initialize(self, context: PluginContext) -> None:
        super().initialize(context)
        if self._mock_mode:
            return
            
        try:
            self.blit_prog = self._compile_shader(BLIT_VERTEX, BLIT_FRAGMENT)
            self.prog = self._compile_shader(POINT_3D_VERTEX, POINT_3D_FRAGMENT)
            if not self.prog or not self.blit_prog:
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
            
            # Point rendering empty VAO
            self.point_vao = gl.glGenVertexArrays(1)
            
        except Exception as e:
            logger.warning(f"Failed to initialize GL FBOs inside DepthPointCloud3D: {e}")
            self._mock_mode = True

    def _setup_camera_matrices(self, width: int, height: int, params: Dict[str, Any]) -> np.ndarray:
        # Perspective projection
        fov = 60.0 * np.pi / 180.0
        aspect = width / max(height, 1)
        near = 0.1
        far = 100.0

        f = 1.0 / np.tan(fov / 2.0)
        proj = np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), -1],
            [0, 0, (2 * far * near) / (near - far), 0]
        ], dtype=np.float32)

        cam_dist = 0.5 + (params.get("cameraDistance", 5.0) / 10.0) * 9.5
        cam_ax = -3.14159 + (params.get("cameraAngleX", 5.0) / 10.0) * 6.28318
        cam_ay = -3.14159 + (params.get("cameraAngleY", 5.0) / 10.0) * 6.28318

        camera_pos = np.array([
            cam_dist * np.sin(cam_ay) * np.cos(cam_ax),
            cam_dist * np.sin(cam_ax),
            cam_dist * np.cos(cam_ay) * np.cos(cam_ax)
        ], dtype=np.float32)

        target = np.array([0, 0, 2.0], dtype=np.float32)
        up = np.array([0, 1, 0], dtype=np.float32)

        forward = target - camera_pos
        norm_fw = np.linalg.norm(forward)
        if norm_fw > 0.0001:
            forward = forward / norm_fw
        else:
            forward = np.array([0, 0, -1], dtype=np.float32)

        right = np.cross(forward, up)
        norm_r = np.linalg.norm(right)
        if norm_r > 0.0001:
            right = right / norm_r
        else:
            right = np.array([1, 0, 0], dtype=np.float32)

        up = np.cross(right, forward)

        view = np.array([
            [right[0], up[0], -forward[0], 0],
            [right[1], up[1], -forward[1], 0],
            [right[2], up[2], -forward[2], 0],
            [-np.dot(right, camera_pos), -np.dot(up, camera_pos), np.dot(forward, camera_pos), 1]
        ], dtype=np.float32)

        model = np.eye(4, dtype=np.float32)
        
        # Matrix multiplication A x B
        # we can just use numpy matmul, but OpenGL expects column-major. 
        # By doing (proj @ view @ model).T flat, we get identical to view then proj if using row vectors
        mvp = model @ view @ proj
        return mvp.flatten()


    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
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
            
            # Resize FBO tex
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            tex_w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            if tex_w != w:
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
                gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.texture, 0)
                
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
            gl.glViewport(0, 0, w, h)
            gl.glClearColor(0, 0, 0, 1)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            
            # --- Pass 1: Blit Original Video ---
            gl.glUseProgram(self.blit_prog)
            gl.glDisable(gl.GL_DEPTH_TEST)
            
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            gl.glUniform1i(gl.glGetUniformLocation(self.blit_prog, "tex0"), 0)
            
            gl.glBindVertexArray(self.vao)
            gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
            gl.glBindVertexArray(0)
            
            # --- Pass 2: Render Point Cloud Over It ---
            gl.glUseProgram(self.prog)
            
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glDepthFunc(gl.GL_LESS)
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)
            
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex_width"), w)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex_height"), h)
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), params.get("u_mix", 1.0))
            
            psize = 0.1 + (params.get("pointSize", 2.0) / 10.0) * 19.9
            pdensity = 0.01 + (params.get("pointDensity", 1.0) / 10.0) * 0.99
            dmin = 0.0 + (params.get("minDepth", 1.0) / 10.0) * 5.0
            dmax = 0.0 + (params.get("maxDepth", 8.0) / 10.0) * 10.0
            
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "point_size"), psize)
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "point_density"), pdensity)
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "min_depth"), dmin)
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "max_depth"), dmax)
            
            mvp_flat = self._setup_camera_matrices(w, h, params)
            gl.glUniformMatrix4fv(gl.glGetUniformLocation(self.prog, "mvp"), 1, gl.GL_FALSE, mvp_flat)
            
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 0)
            
            gl.glBindVertexArray(self.point_vao)
            vertex_count = w * h
            gl.glDrawArrays(gl.GL_POINTS, 0, vertex_count)
            gl.glBindVertexArray(0)
            
            gl.glDisable(gl.GL_PROGRAM_POINT_SIZE)
            gl.glDisable(gl.GL_BLEND)
            gl.glDisable(gl.GL_DEPTH_TEST)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            
            context.outputs["video_out"] = self.texture
            return self.texture
            
        except Exception as e:
            logger.error(f"Render failed in Depth Point Cloud 3D: {e}")
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
                if hasattr(self, 'blit_prog') and self.blit_prog:
                    gl.glDeleteProgram(self.blit_prog)
                if hasattr(self, 'vao') and self.vao:
                    gl.glDeleteVertexArrays(1, [self.vao])
                if hasattr(self, 'point_vao') and self.point_vao:
                    gl.glDeleteVertexArrays(1, [self.point_vao])
                if hasattr(self, 'vbo') and self.vbo:
                    gl.glDeleteBuffers(1, [self.vbo])
            except Exception as e:
                logger.error(f"Error cleaning up FBOs/Textures during layout PointCloud3D unload: {e}")
                
        self.texture = None
        self.fbo = None
