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

MESH_VERTEX = """
#version 330 core
// Grid vertices from 0..GRID_W, 0..GRID_H
layout(location=0) in vec2 grid_pos; 

uniform sampler2D depth_tex;
uniform int tex_width;
uniform int tex_height;
uniform float min_depth;
uniform float max_depth;
uniform float grid_w;
uniform float grid_h;
uniform mat4 mvp;

out vec4 v_color;
out vec3 v_normal;
out vec3 v_frag_pos;

vec3 get_world_pos(vec2 uv) {
    float raw_d = texture(depth_tex, uv).r;
    float depth = raw_d * (max_depth - min_depth) + min_depth;
    
    float focal_length = 570.0;
    float cx = float(tex_width) / 2.0;
    float cy = float(tex_height) / 2.0;

    float px = uv.x * float(tex_width);
    float py = uv.y * float(tex_height);
    
    float world_x = (px - cx) * depth / focal_length;
    float world_y = (py - cy) * depth / focal_length;
    
    return vec3(world_x, -world_y, depth);
}

void main() {
    vec2 uv = vec2(grid_pos.x / grid_w, grid_pos.y / grid_h);
    float raw_d = texture(depth_tex, uv).r;
    float depth = raw_d * (max_depth - min_depth) + min_depth;

    if (raw_d < 0.01 || depth < min_depth || depth > max_depth) {
        // Discard by pushing out of frustum
        gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
        return;
    }
    
    vec3 pC = get_world_pos(uv);
    vec3 pR = get_world_pos(uv + vec2(1.0/grid_w, 0.0));
    vec3 pU = get_world_pos(uv + vec2(0.0, 1.0/grid_h));
    
    vec3 normal = normalize(cross(pR - pC, pU - pC));
    if (dot(normal, vec3(0,0,-1)) < 0.0) {
        normal = -normal;
    }

    gl_Position = mvp * vec4(pC, 1.0);
    
    float t = clamp((depth - min_depth) / max(max_depth - min_depth, 0.001), 0.0, 1.0);
    v_color = vec4(t, 0.5, 1.0 - t, 1.0);
    v_normal = normal;
    v_frag_pos = pC;
}
"""

MESH_FRAGMENT = """
#version 330 core
in vec4 v_color;
in vec3 v_normal;
in vec3 v_frag_pos;

out vec4 fragColor;

uniform float u_mix;
uniform int wireframe;

void main() {
    if (wireframe > 0) {
        fragColor = vec4(v_color.rgb, u_mix);
        return;
    }

    // Simple Phong lighting with a fixed light from the camera
    vec3 light_dir = normalize(vec3(0.0, 0.0, -1.0));
    vec3 norm = normalize(v_normal);
    
    float diff = max(dot(norm, light_dir), 0.0);
    vec3 diffuse = diff * vec3(1.0, 1.0, 1.0);
    vec3 ambient = 0.3 * v_color.rgb;
    
    vec3 result = (ambient + diffuse) * v_color.rgb;
    fragColor = vec4(result, u_mix);
}
"""

METADATA = {
    "name": "Depth Mesh",
    "description": "Renders depth data as a lit 3D mesh surface with dynamic topography.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["depth", "mesh", "3D", "surface"],
    "status": "active",
    "parameters": [
        {"name": "minDepth", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
        {"name": "maxDepth", "type": "float", "min": 0.0, "max": 10.0, "default": 8.0},
        {"name": "meshWireframe", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "cameraDistance", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "cameraAngleX", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "cameraAngleY", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}


class DepthMeshPlugin(EffectPlugin):
    """P3-VD39: Depth Effects Mesh rebuilt for purely GPU operations."""
    
    GRID_W = 160
    GRID_H = 120

    def __init__(self) -> None:
        super().__init__()
        self._mock_mode = not HAS_GL
        self.blit_prog = None
        self.prog = None
        
        self.texture: Optional[int] = None
        self.fbo: Optional[int] = None
        
        self.index_count = 0

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
            self.prog = self._compile_shader(MESH_VERTEX, MESH_FRAGMENT)
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
            
            # Create Grid VBO and EBO
            self.mesh_vao = gl.glGenVertexArrays(1)
            self.mesh_vbo = gl.glGenBuffers(1)
            self.mesh_ebo = gl.glGenBuffers(1)
            
            y, x = np.mgrid[0:self.GRID_H, 0:self.GRID_W]
            vertices = np.stack([x.ravel(), y.ravel()], axis=1).astype(np.float32)
            
            idx = np.arange(self.GRID_W * self.GRID_H).reshape(self.GRID_H, self.GRID_W)
            q1 = idx[:-1, :-1].ravel()
            q2 = idx[1:, :-1].ravel()
            q3 = idx[1:, 1:].ravel()
            q4 = idx[:-1, 1:].ravel()
            
            tris1 = np.stack([q1, q2, q3], axis=1)
            tris2 = np.stack([q1, q3, q4], axis=1)
            indices = np.vstack([tris1, tris2]).ravel().astype(np.uint32)
            self.index_count = len(indices)
            
            gl.glBindVertexArray(self.mesh_vao)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.mesh_vbo)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
            
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.mesh_ebo)
            gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)
            
            gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 8, gl.ctypes.c_void_p(0))
            gl.glEnableVertexAttribArray(0)
            
            gl.glBindVertexArray(0)
            
        except Exception as e:
            logger.warning(f"Failed to initialize GL FBOs inside DepthMeshEffect: {e}")
            self._mock_mode = True

    def _setup_camera_matrices(self, width: int, height: int, params: Dict[str, Any]) -> np.ndarray:
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
            
            # Pass 1: Blit Original Video
            gl.glUseProgram(self.blit_prog)
            gl.glDisable(gl.GL_DEPTH_TEST)
            
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            gl.glUniform1i(gl.glGetUniformLocation(self.blit_prog, "tex0"), 0)
            
            gl.glBindVertexArray(self.vao)
            gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
            gl.glBindVertexArray(0)
            
            # Pass 2: Render Mesh
            gl.glUseProgram(self.prog)
            
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glDepthFunc(gl.GL_LESS)
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            
            is_wireframe = params.get("meshWireframe", 0.0) >= 5.0
            if is_wireframe:
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex_width"), w)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex_height"), h)
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), params.get("u_mix", 1.0))
            
            dmin = 0.0 + (params.get("minDepth", 1.0) / 10.0) * 5.0
            dmax = 0.0 + (params.get("maxDepth", 8.0) / 10.0) * 10.0
            
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "grid_w"), float(self.GRID_W))
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "grid_h"), float(self.GRID_H))
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "min_depth"), dmin)
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "max_depth"), dmax)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "wireframe"), 1 if is_wireframe else 0)
            
            mvp_flat = self._setup_camera_matrices(w, h, params)
            gl.glUniformMatrix4fv(gl.glGetUniformLocation(self.prog, "mvp"), 1, gl.GL_FALSE, mvp_flat)
            
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 0)
            
            gl.glBindVertexArray(self.mesh_vao)
            gl.glDrawElements(gl.GL_TRIANGLES, self.index_count, gl.GL_UNSIGNED_INT, None)
            gl.glBindVertexArray(0)
            
            if is_wireframe:
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
                
            gl.glDisable(gl.GL_BLEND)
            gl.glDisable(gl.GL_DEPTH_TEST)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            
            context.outputs["video_out"] = self.texture
            return self.texture
            
        except Exception as e:
            logger.error(f"Render failed in Depth Mesh: {e}")
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
                if hasattr(self, 'vbo') and self.vbo:
                    gl.glDeleteBuffers(1, [self.vbo])
                if hasattr(self, 'mesh_vao') and self.mesh_vao:
                    gl.glDeleteVertexArrays(1, [self.mesh_vao])
                if hasattr(self, 'mesh_vbo') and self.mesh_vbo:
                    gl.glDeleteBuffers(1, [self.mesh_vbo])
                if hasattr(self, 'mesh_ebo') and self.mesh_ebo:
                    gl.glDeleteBuffers(1, [self.mesh_ebo])
            except Exception as e:
                logger.error(f"Error cleaning up FBOs/Textures during layout DepthMesh unload: {e}")
                
        self.texture = None
        self.fbo = None
