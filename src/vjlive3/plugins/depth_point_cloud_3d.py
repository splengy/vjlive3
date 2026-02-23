"""
P3-VD38: Depth Effects (Point Cloud 3D) Plugin for VJLive3.
Ported from legacy VJlive-2 DepthPointCloud3DEffect.
Translates O(N^2) CPU mapping loops into GPU Vertex Pulling.
"""

from typing import Dict, Any, Optional
import numpy as np
import OpenGL.GL as gl
# # from .api import EffectPlugin, PluginContext

logger = __import__('logging').getLogger(__name__)

METADATA = {
    "name": "DepthPointCloud3D",
    "version": "3.0.0",
    "description": "True 3D depth point cloud visualization using GPU Vertex Pulling.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "visual",
    "tags": ["depth", "3D", "point_cloud", "geometry", "gpu"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "camera_distance", "type": "float", "default": 5.0, "min": 0.5, "max": 10.0},
        {"name": "camera_angle_x", "type": "float", "default": 0.0, "min": -3.14159, "max": 3.14159},
        {"name": "camera_angle_y", "type": "float", "default": 0.0, "min": -3.14159, "max": 3.14159},
        {"name": "point_size", "type": "float", "default": 2.0, "min": 1.0, "max": 20.0},
        {"name": "point_density", "type": "float", "default": 1.0, "min": 0.01, "max": 1.0},
        {"name": "min_depth", "type": "float", "default": 0.1, "min": 0.0, "max": 10.0},
        {"name": "max_depth", "type": "float", "default": 5.0, "min": 0.0, "max": 20.0},
        {"name": "color_mode", "type": "str", "default": "depth", "options": ["depth", "velocity", "white"]}
    ]
}

VERTEX_SHADER_SOURCE = """
#version 330 core

uniform sampler2D depth_tex;
uniform vec2 resolution;
uniform mat4 mvp;
uniform float point_size;
uniform float min_depth;
uniform float max_depth;
uniform float point_density;
uniform int color_mode; 

out vec4 vertex_color;

void main() {
    int width = int(resolution.x);
    int height = int(resolution.y);
    
    // Handle edge case where width/height might be 0
    if (width <= 0 || height <= 0) {
        gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
        return;
    }
    
    int step_val = max(1, int(1.0 / max(0.01, point_density)));
    
    int points_per_row = width / step_val;
    int points_per_col = height / step_val;
    int max_points = points_per_row * points_per_col;
    
    if (gl_VertexID >= max_points) {
        gl_Position = vec4(2.0, 2.0, 2.0, 1.0); 
        return;
    }
    
    int grid_x = gl_VertexID % points_per_row;
    int grid_y = gl_VertexID / points_per_row;
    
    float x = float(grid_x * step_val);
    float y = float(grid_y * step_val);
    
    vec2 uv = vec2(x, y) / resolution;
    // Map strictly to legacy orientation
    
    // Scale depth linearly if it was stored as normalized float. 
    // As per VJLive3 standard depth_tex conventions, depth is frequently normalized 0-1, so we map it to max_depth.
    float base_depth = texture(depth_tex, uv).r;
    float depth = base_depth * max_depth; 
    
    if (depth >= min_depth && depth <= max_depth && depth > 0.0) {
        // Pinhole camera math from legacy
        float focal_length = 570.0;
        float cx = resolution.x / 2.0;
        float cy = resolution.y / 2.0;
        
        float world_x = (x - cx) * depth / focal_length;
        float world_y = (y - cy) * depth / focal_length;
        float world_z = depth;
        
        vec3 position = vec3(world_x, world_y, world_z);
        gl_Position = mvp * vec4(position, 1.0);
        gl_PointSize = point_size;
        
        vec3 col = vec3(1.0);
        if (color_mode == 0) {
            float t = clamp((depth - min_depth) / (max_depth - min_depth), 0.0, 1.0);
            col = vec3(t, 0.5, 1.0 - t);
        } else if (color_mode == 1) {
            col = vec3(1.0, 0.5, 0.5);
        }
        
        vertex_color = vec4(col, 1.0);
    } else {
        gl_Position = vec4(2.0, 2.0, 2.0, 1.0); 
    }
}
"""

FRAGMENT_SHADER_SOURCE = """
#version 330 core
in vec4 vertex_color;
out vec4 fragColor;

void main() {
    // Create circular points
    vec2 coord = gl_PointCoord - vec2(0.5);
    if (dot(coord, coord) > 0.25) discard;
    
    fragColor = vertex_color;
}
"""


class DepthPointCloud3DEffectPlugin(object):
    
    def __init__(self):
        super().__init__()
        self.program = 0
        self.fbo = 0
        self.target_texture = 0
        self.empty_vao = 0
        self.width = 0
        self.height = 0
        self._initialized = False

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context) -> bool:
        if not hasattr(gl, 'glCreateProgram'):
            logger.warning("Mock mode engaged. Skipping GL init.")
            return True

        try:
            vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
            gl.glShaderSource(vertex_shader, VERTEX_SHADER_SOURCE)
            gl.glCompileShader(vertex_shader)
            
            if not gl.glGetShaderiv(vertex_shader, gl.GL_COMPILE_STATUS):
                err = gl.glGetShaderInfoLog(vertex_shader)
                logger.error(f"Vertex Shader compilation failed: {err}")
                return False

            fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fragment_shader, FRAGMENT_SHADER_SOURCE)
            gl.glCompileShader(fragment_shader)
            
            if not gl.glGetShaderiv(fragment_shader, gl.GL_COMPILE_STATUS):
                err = gl.glGetShaderInfoLog(fragment_shader)
                logger.error(f"Fragment Shader compilation failed: {err}")
                return False

            self.program = gl.glCreateProgram()
            gl.glAttachShader(self.program, vertex_shader)
            gl.glAttachShader(self.program, fragment_shader)
            gl.glLinkProgram(self.program)
            
            if not gl.glGetProgramiv(self.program, gl.GL_LINK_STATUS):
                err = gl.glGetProgramInfoLog(self.program)
                logger.error(f"Shader program linking failed: {err}")
                return False

            gl.glDeleteShader(vertex_shader)
            gl.glDeleteShader(fragment_shader)
            
            # Generate empty VAO for Vertex Pulling
            self.empty_vao = gl.glGenVertexArrays(1)

            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize DepthPointCloud3DEffect: {e}")
            return False

    def _setup_fbo(self, width: int, height: int):
        if self.width == width and self.height == height and self.fbo != 0:
            return

        if self.fbo != 0:
            gl.glDeleteFramebuffers(1, [self.fbo])
            gl.glDeleteTextures(1, [self.target_texture])

        self.width = width
        self.height = height
        
        self.fbo = gl.glGenFramebuffers(1)
        self.target_texture = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.target_texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.target_texture, 0)
        
        status = gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER)
        if status != gl.GL_FRAMEBUFFER_COMPLETE:
            logger.error(f"FBO initialization failed with status {status}")
            
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _calculate_matrices(self, w: int, h: int, params: Dict[str, Any]) -> np.ndarray:
        # Legacy pinhole equivalent transforms
        fov = 60.0 * np.pi / 180.0
        aspect = float(w) / max(1.0, float(h))
        near, far = 0.1, 10.0
        
        f = 1.0 / np.tan(fov / 2.0)
        projection_matrix = np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), (2 * far * near) / (near - far)],
            [0, 0, -1, 0]
        ], dtype=np.float32)
        
        c_dist = float(params.get("camera_distance", 5.0))
        c_ax = float(params.get("camera_angle_x", 0.0))
        c_ay = float(params.get("camera_angle_y", 0.0))
        
        camera_pos = np.array([
            c_dist * np.sin(c_ay) * np.cos(c_ax),
            c_dist * np.sin(c_ax),
            c_dist * np.cos(c_ay) * np.cos(c_ax)
        ], dtype=np.float32)
        
        target = np.array([0, 0, 2.0], dtype=np.float32)
        up = np.array([0, 1, 0], dtype=np.float32)
        
        forward = target - camera_pos
        n_forward = np.linalg.norm(forward)
        if n_forward > 0.0001: forward /= n_forward
        else: forward = np.array([0, 0, -1], dtype=np.float32)
        
        right = np.cross(forward, up)
        n_right = np.linalg.norm(right)
        if n_right > 0.0001: right /= n_right
        else: right = np.array([1, 0, 0], dtype=np.float32)
        
        up = np.cross(right, forward)
        
        view_matrix = np.array([
            [right[0], up[0], -forward[0], 0],
            [right[1], up[1], -forward[1], 0],
            [right[2], up[2], -forward[2], 0],
            [-np.dot(right, camera_pos), -np.dot(up, camera_pos), np.dot(forward, camera_pos), 1]
        ], dtype=np.float32)
        
        # Identity model matrix
        model_matrix = np.eye(4, dtype=np.float32)
        
        mvp = projection_matrix @ view_matrix @ model_matrix
        return mvp

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
        
        depth_tex = 0
        if context and hasattr(context, 'inputs'):
            depth_tex = context.inputs.get("depth_in", 0)
            
        if depth_tex <= 0:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        
        # Clear background since 3D point cloud doesn't cover whole screen by default
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        gl.glUseProgram(self.program)
        
        # Inject Uniforms
        gl.glUniform2f(gl.glGetUniformLocation(self.program, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "point_size"), float(params.get("point_size", 2.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "point_density"), float(params.get("point_density", 1.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "min_depth"), float(params.get("min_depth", 0.1)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "max_depth"), float(params.get("max_depth", 5.0)))
        
        color_mode_str = str(params.get("color_mode", "depth")).lower()
        cm = 0
        if color_mode_str == "velocity": cm = 1
        elif color_mode_str == "white": cm = 2
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "color_mode"), cm)
        
        # Calculate matrices manually in Python and pass to GPU globally
        mvp = self._calculate_matrices(w, h, params)
        gl.glUniformMatrix4fv(gl.glGetUniformLocation(self.program, "mvp"), 1, gl.GL_FALSE, mvp.flatten())
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_tex)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "depth_tex"), 0)
        
        # Enable rendering flags mimicking legacy 3D state
        gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LESS)
        
        # Bind empty VAO to trigger hardware iterations without CPU data transfer
        gl.glBindVertexArray(self.empty_vao)
        
        # Draw precisely w * h points. VertexID calculates mapping inside the shader.
        gl.glDrawArrays(gl.GL_POINTS, 0, w * h)
        
        # Revert state
        gl.glBindVertexArray(0)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glDisable(gl.GL_PROGRAM_POINT_SIZE)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.target_texture
            
        return self.target_texture

    def cleanup(self) -> None:
        try:
            if hasattr(gl, 'glDeleteProgram') and self.program != 0:
                gl.glDeleteProgram(self.program)
            if hasattr(gl, 'glDeleteFramebuffers') and self.fbo != 0:
                gl.glDeleteFramebuffers(1, [self.fbo])
            if hasattr(gl, 'glDeleteTextures') and self.target_texture != 0:
                gl.glDeleteTextures(1, [self.target_texture])
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao != 0:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Failed to cleanup DepthPointCloud3D plugin: {e}")
        finally:
            self.program = 0
            self.fbo = 0
            self.target_texture = 0
            self.empty_vao = 0
