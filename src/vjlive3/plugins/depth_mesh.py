"""
P3-VD39: Depth Effects (Mesh Effect) Plugin for VJLive3.
Ported from legacy VJlive-2 DepthMeshEffect.
Replaces O(N log N) CPU Delaunay triangulation with an O(1) dynamic GPU Geometry Shader grid.
"""

from typing import Dict, Any, Optional
import numpy as np
import OpenGL.GL as gl
import ctypes
# # from .api import EffectPlugin, PluginContext

logger = __import__('logging').getLogger(__name__)

METADATA = {
    "name": "DepthMesh",
    "version": "3.0.0",
    "description": "3D Depth mesh visualization using a dynamic GPU Geometry Shader grid.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "visual",
    "tags": ["depth", "3D", "mesh", "geometry", "gpu", "wireframe"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "camera_distance", "type": "float", "default": 5.0, "min": 0.5, "max": 10.0},
        {"name": "camera_angle_x", "type": "float", "default": 0.0, "min": -3.14159, "max": 3.14159},
        {"name": "camera_angle_y", "type": "float", "default": 0.0, "min": -3.14159, "max": 3.14159},
        {"name": "mesh_resolution", "type": "float", "default": 0.05, "min": 0.005, "max": 0.1},
        {"name": "mesh_smoothing", "type": "bool", "default": False},
        {"name": "mesh_wireframe", "type": "bool", "default": False},
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
uniform mat4 model;
uniform float min_depth;
uniform float max_depth;
uniform int color_mode; 
uniform int cols;

out vec3 v_position;
out vec4 v_color;
out float v_depth_valid;

void main() {
    int x_grid = gl_VertexID % cols;
    int y_grid = gl_VertexID / cols;
    
    // Convert grid coordinate to UV
    vec2 uv = vec2(float(x_grid) / float(cols - 1), float(y_grid) / float(cols - 1));
    // We assume the grid rows/cols aspect ratio is maintained or the step scales appropriately
    // Actually, step is applied evenly in width/height, so rows and cols might differ.
    // Let's pass 'step' and 'cols' directly.
    // wait, uv should be strictly mapped to grid.
}
"""

# Let me rewrite the Vertex Shader to handle grid correctly.
VERTEX_SHADER_SOURCE = """
#version 330 core

uniform sampler2D depth_tex;
uniform vec2 resolution;
uniform mat4 mvp;
uniform mat4 model;
uniform float min_depth;
uniform float max_depth;
uniform int color_mode; 
uniform int cols;
uniform int step_val;

out vec3 v_position;
out vec4 v_color;
out float v_depth_valid;

void main() {
    int grid_x = gl_VertexID % cols;
    int grid_y = gl_VertexID / cols;
    
    float x = float(grid_x * step_val);
    float y = float(grid_y * step_val);
    
    vec2 uv = vec2(x, y) / resolution;
    
    float base_depth = texture(depth_tex, uv).r;
    float depth = base_depth * max_depth; 
    
    if (depth >= min_depth && depth <= max_depth && depth > 0.0) {
        float focal_length = 570.0;
        float cx = resolution.x / 2.0;
        float cy = resolution.y / 2.0;
        
        float world_x = (x - cx) * depth / focal_length;
        float world_y = (y - cy) * depth / focal_length;
        float world_z = depth;
        
        vec3 position = vec3(world_x, world_y, world_z);
        v_position = position;
        
        vec3 col = vec3(1.0);
        if (color_mode == 0) {
            float t = clamp((depth - min_depth) / (max_depth - min_depth), 0.0, 1.0);
            col = vec3(t, 0.5, 1.0 - t);
        } else if (color_mode == 1) {
            col = vec3(1.0, 0.5, 0.5);
        }
        
        v_color = vec4(col, 1.0);
        v_depth_valid = 1.0;
    } else {
        v_position = vec3(0.0);
        v_color = vec4(0.0);
        v_depth_valid = 0.0;
    }
}
"""

GEOMETRY_SHADER_SOURCE = """
#version 330 core
layout(triangles) in;
layout(triangle_strip, max_vertices = 3) out;

in vec3 v_position[];
in vec4 v_color[];
in float v_depth_valid[];

uniform mat4 mvp;
uniform mat4 model;

out vec4 geom_color;
out vec3 geom_normal;
out vec3 geom_frag_pos;

void main() {
    // If any vertex is invalid, cull the entire triangle (acts as Depth Mask)
    if (v_depth_valid[0] < 0.5 || v_depth_valid[1] < 0.5 || v_depth_valid[2] < 0.5) {
        return;
    }
    
    // Tearing prevention (Discard triangles bridging huge depth gaps)
    float tear_limit = 0.5; // Configurable tearing depth bound
    if (abs(v_position[0].z - v_position[1].z) > tear_limit || 
        abs(v_position[1].z - v_position[2].z) > tear_limit || 
        abs(v_position[2].z - v_position[0].z) > tear_limit) {
        return;
    }
    
    // Flat normal calculation
    vec3 u = v_position[1] - v_position[0];
    vec3 v = v_position[2] - v_position[0];
    vec3 normal = normalize(cross(u, v));
    // Mat3 orientation mapping for normal 
    vec3 world_normal = normalize(mat3(model) * normal);
    
    for(int i = 0; i < 3; i++) {
        gl_Position = mvp * vec4(v_position[i], 1.0);
        geom_color = v_color[i];
        geom_normal = world_normal;
        geom_frag_pos = vec3(model * vec4(v_position[i], 1.0));
        EmitVertex();
    }
    EndPrimitive();
}
"""

FRAGMENT_SHADER_SOURCE = """
#version 330 core
in vec4 geom_color;
in vec3 geom_normal;
in vec3 geom_frag_pos;

uniform vec3 light_dir;
uniform bool wireframe;
uniform bool enable_lighting;

out vec4 fragColor;

void main() {
    if (wireframe) {
        fragColor = vec4(1.0, 1.0, 1.0, 1.0);
        return;
    }

    vec3 color = geom_color.rgb;

    if (enable_lighting) {
        // Simple Phong lighting
        vec3 norm = normalize(geom_normal);
        vec3 light_dir_norm = normalize(light_dir);
        float diff = max(dot(norm, light_dir_norm), 0.0);
        vec3 diffuse = diff * vec3(1.0, 1.0, 1.0);

        // Ambient
        vec3 ambient = 0.3 * color;

        color = (ambient + diffuse) * color;
    }

    fragColor = vec4(color, geom_color.a);
}
"""

class DepthMeshEffectPlugin(object):
    
    def __init__(self):
        super().__init__()
        self.program = 0
        self.fbo = 0
        self.target_texture = 0
        self.vao = 0
        self.ebo = 0
        self.width = 0
        self.height = 0
        
        # Grid state tracking
        self.last_step = 0
        self.last_w = 0
        self.last_h = 0
        self.num_indices = 0
        
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
                logger.error(f"VS fail: {err}")
                return False

            geometry_shader = gl.glCreateShader(gl.GL_GEOMETRY_SHADER)
            gl.glShaderSource(geometry_shader, GEOMETRY_SHADER_SOURCE)
            gl.glCompileShader(geometry_shader)
            if not gl.glGetShaderiv(geometry_shader, gl.GL_COMPILE_STATUS):
                err = gl.glGetShaderInfoLog(geometry_shader)
                logger.error(f"GS fail: {err}")
                return False

            fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fragment_shader, FRAGMENT_SHADER_SOURCE)
            gl.glCompileShader(fragment_shader)
            if not gl.glGetShaderiv(fragment_shader, gl.GL_COMPILE_STATUS):
                err = gl.glGetShaderInfoLog(fragment_shader)
                logger.error(f"FS fail: {err}")
                return False

            self.program = gl.glCreateProgram()
            gl.glAttachShader(self.program, vertex_shader)
            gl.glAttachShader(self.program, geometry_shader)
            gl.glAttachShader(self.program, fragment_shader)
            gl.glLinkProgram(self.program)
            
            if not gl.glGetProgramiv(self.program, gl.GL_LINK_STATUS):
                err = gl.glGetProgramInfoLog(self.program)
                logger.error(f"Shader link fail: {err}")
                return False
                
            gl.glDeleteShader(vertex_shader)
            gl.glDeleteShader(geometry_shader)
            gl.glDeleteShader(fragment_shader)
            
            # Generate VAO/EBO
            self.vao = gl.glGenVertexArrays(1)
            self.ebo = gl.glGenBuffers(1)

            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize DepthMeshEffect: {e}")
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
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _setup_grid(self, w: int, h: int, step: int) -> int:
        """Regenerates the GPU Indices Buffer representing the 2D surface mesh topology."""
        if w == self.last_w and h == self.last_h and step == self.last_step and self.ebo != 0 and self.num_indices > 0:
            return int(w / max(1, step))  # Return cols
            
        cols = int(w / max(1, step))
        rows = int(h / max(1, step))
        
        if cols < 2 or rows < 2:
            return cols
            
        # Standard Grid Element Generation block mapped correctly in NumPy
        col_indices = np.arange(cols - 1)
        row_indices = np.arange(rows - 1)[:, np.newaxis]
        
        top_left = row_indices * cols + col_indices
        top_right = top_left + 1
        bottom_left = (row_indices + 1) * cols + col_indices
        bottom_right = bottom_left + 1
        
        # Tri 1: TL, TR, BL
        tri1 = np.stack([top_left, top_right, bottom_left], axis=-1)
        # Tri 2: BL, TR, BR
        tri2 = np.stack([bottom_left, top_right, bottom_right], axis=-1)
        
        indices = np.concatenate([tri1[..., np.newaxis, :], tri2[..., np.newaxis, :]], axis=-2).flatten().astype(np.uint32)
        self.num_indices = len(indices)
        
        if hasattr(gl, 'glCreateProgram'):
            gl.glBindVertexArray(self.vao)
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
            gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)
            gl.glBindVertexArray(0)
            
        self.last_w = w
        self.last_h = h
        self.last_step = step
        return cols

    def _calculate_matrices(self, w: int, h: int, params: Dict[str, Any]) -> np.ndarray:
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
        
        mvp = projection_matrix @ view_matrix # Model is identity in local
        return mvp, np.eye(4, dtype=np.float32)

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
        if depth_tex <= 0:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        res_val = float(params.get("mesh_resolution", 0.5))
        # Ensure mapping scales nicely from 100 pixel grids down to 2 pixel grids
        step = max(2, int(100.0 - (res_val * 98.0)))
        
        cols = self._setup_grid(w, h, step)
            
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        gl.glUseProgram(self.program)
        
        # Inject Uniforms
        gl.glUniform2f(gl.glGetUniformLocation(self.program, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "min_depth"), float(params.get("min_depth", 0.1)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "max_depth"), float(params.get("max_depth", 5.0)))
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "cols"), cols)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "step_val"), step)
        gl.glUniform3f(gl.glGetUniformLocation(self.program, "light_dir"), 0.0, 0.0, -1.0)
        
        wireframe = 1 if bool(params.get("mesh_wireframe", False)) else 0
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "wireframe"), wireframe)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "enable_lighting"), 1)
        
        color_mode_str = str(params.get("color_mode", "depth")).lower()
        cm = 0
        if color_mode_str == "velocity": cm = 1
        elif color_mode_str == "white": cm = 2
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "color_mode"), cm)
        
        mvp, model = self._calculate_matrices(w, h, params)
        gl.glUniformMatrix4fv(gl.glGetUniformLocation(self.program, "mvp"), 1, gl.GL_FALSE, mvp.flatten())
        gl.glUniformMatrix4fv(gl.glGetUniformLocation(self.program, "model"), 1, gl.GL_FALSE, model.flatten())
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_tex)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "depth_tex"), 0)
        
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LESS)
        
        # Draw Mesh Using EBO mapped Grid array
        gl.glBindVertexArray(self.vao)
        
        if wireframe == 1:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            
        gl.glDrawElements(gl.GL_TRIANGLES, self.num_indices, gl.GL_UNSIGNED_INT, None)
        
        if wireframe == 1:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
        
        gl.glBindVertexArray(0)
        gl.glDisable(gl.GL_DEPTH_TEST)
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
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao != 0:
                gl.glDeleteVertexArrays(1, [self.vao])
            if hasattr(gl, 'glDeleteBuffers') and self.ebo != 0:
                gl.glDeleteBuffers(1, [self.ebo])
        except Exception as e:
            logger.error(f"Failed to cleanup DepthMesh plugin: {e}")
        finally:
            self.program = 0
            self.fbo = 0
            self.target_texture = 0
            self.vao = 0
            self.ebo = 0
            self.num_indices = 0
