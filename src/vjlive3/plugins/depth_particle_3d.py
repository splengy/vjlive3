"""
P3-VD41: Depth Effects (Particle 3D Effect) Plugin for VJLive3.
Ported from legacy VJlive-2 DepthParticle3DEffect.
Replaces 10,000 O(N) CPU physics loops per frame with a 100% GPGPU Ping-Pong Data Texture workflow.
"""

from typing import Dict, Any, Optional
import numpy as np
import OpenGL.GL as gl
import time
from .api import EffectPlugin, PluginContext

logger = __import__('logging').getLogger(__name__)

METADATA = {
    "name": "DepthParticle3D",
    "version": "3.0.0",
    "description": "3D Physics Particle Cloud driven by Depth Topology via Ping-Pong GPGPU.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "visual",
    "tags": ["depth", "particle", "3d", "physics", "gpgpu"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "camera_distance", "type": "float", "default": 5.0, "min": 0.5, "max": 10.0},
        {"name": "camera_angle_x", "type": "float", "default": 0.0, "min": -3.14159, "max": 3.14159},
        {"name": "camera_angle_y", "type": "float", "default": 0.0, "min": -3.14159, "max": 3.14159},
        {"name": "particleSize", "type": "float", "default": 0.5, "min": 0.0, "max": 1.0},     # maps to 0.5-10
        {"name": "particleLifetime", "type": "float", "default": 0.5, "min": 0.0, "max": 1.0}, # maps to 0.5-10
        {"name": "emissionRate", "type": "float", "default": 0.5, "min": 0.0, "max": 1.0},     # maps to 10-500
        {"name": "depthAttraction", "type": "float", "default": 0.5, "min": 0.0, "max": 1.0},  # maps to 0.0-1.0
        {"name": "damping", "type": "float", "default": 0.5, "min": 0.0, "max": 1.0},          # maps to 0.9-1.0
        {"name": "min_depth", "type": "float", "default": 0.1, "min": 0.0, "max": 10.0},
        {"name": "max_depth", "type": "float", "default": 5.0, "min": 0.0, "max": 20.0},
        {"name": "color_mode", "type": "str", "default": "depth", "options": ["depth", "velocity", "white"]}
    ]
}

# --- SHADERS FOR PHYSICS SIMULATION (Ping Pong) ---
# Executed across a 100x100 texture quad mimicking 10,000 particle threads

SIM_VERTEX_SHADER = """
#version 330 core
const vec2 quadVertices[4] = vec2[4](
    vec2(-1.0, -1.0),
    vec2( 1.0, -1.0),
    vec2(-1.0,  1.0),
    vec2( 1.0,  1.0)
);
out vec2 v_uv;
void main() {
    gl_Position = vec4(quadVertices[gl_VertexID], 0.0, 1.0);
    v_uv = quadVertices[gl_VertexID] * 0.5 + 0.5;
}
"""

SIM_FRAGMENT_SHADER = """
#version 330 core
layout(location = 0) out vec4 out_pos_life;
layout(location = 1) out vec4 out_vel_seed;

in vec2 v_uv;

uniform sampler2D tex_pos;
uniform sampler2D tex_vel;
uniform sampler2D depth_tex;

uniform float dt;
uniform float time;
uniform vec2 depth_res;

uniform float particleLifetime;
uniform float emissionRate; // mapped 10-500 per second 
uniform float depthAttraction;
uniform float damping;
uniform float max_depth;
uniform float min_depth;

// Pseudo-random hash
float rand(vec2 co) {
    return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

void main() {
    vec4 pos_life = texture(tex_pos, v_uv);
    vec4 vel_seed = texture(tex_vel, v_uv);
    
    float life = pos_life.w;
    float seed = vel_seed.w;
    
    // Determine emission chance based on emission rate vs dt limits
    // If life < 0, check if we should spawn
    if (life <= 0.0) {
        float spawn_chance = (emissionRate / 10000.0) * dt * 60.0; 
        if (rand(vec2(seed, time)) < spawn_chance) {
            // Respawn!
            // Pick a random pixel on the depth texture
            float rx = rand(vec2(v_uv.x, time * 1.1));
            float ry = rand(vec2(v_uv.y, time * 1.2));
            vec2 spawn_uv = vec2(rx, ry);
            
            float base_depth = texture(depth_tex, spawn_uv).r;
            float world_z = base_depth * max_depth;
            
            if (world_z >= min_depth && world_z <= max_depth && base_depth > 0.0) {
                float focal_length = 570.0;
                float cx = depth_res.x * 0.5;
                float cy = depth_res.y * 0.5;
                
                float pix_x = rx * depth_res.x;
                float pix_y = ry * depth_res.y;
                
                float world_x = (pix_x - cx) * world_z / focal_length;
                float world_y = (pix_y - cy) * world_z / focal_length;
                
                // Add minor random noise burst
                float nx = (rand(vec2(v_uv.x + 1.0, time)) - 0.5) * 0.5;
                float ny = (rand(vec2(v_uv.y - 1.0, time)) - 0.5) * 0.5;
                float nz = (rand(vec2(seed + 0.1, time)) - 0.5) * 0.5;
                
                out_pos_life = vec4(world_x + nx, world_y + ny, world_z + nz, particleLifetime);
                out_vel_seed = vec4(nx, ny, nz, seed);
                return;
            }
        }
        
        // Remain dead
        out_pos_life = pos_life;
        out_vel_seed = vel_seed;
        return;
    }
    
    // Alive Physics
    vec3 pos = pos_life.xyz;
    vec3 vel = vel_seed.xyz;
    
    vec3 gravity = vec3(0.0, -0.001, 0.0);
    vel += gravity * dt;
    vel *= damping;
    pos += vel * dt;
    
    // Depth Attraction (Particle tries to snap back to the topological boundary)
    // Reverse pinhole to find which depth coordinate this particle covers
    float focal_length = 570.0;
    float cx = depth_res.x * 0.5;
    float cy = depth_res.y * 0.5;
    
    if (pos.z > 0.1) {
        float u_pix = cx + pos.x * focal_length / pos.z;
        float v_pix = cy + pos.y * focal_length / pos.z;
        vec2 sample_uv = vec2(u_pix / depth_res.x, v_pix / depth_res.y);
        
        if (sample_uv.x >= 0.0 && sample_uv.x <= 1.0 && sample_uv.y >= 0.0 && sample_uv.y <= 1.0) {
            float surface_depth = texture(depth_tex, sample_uv).r * max_depth;
            if (surface_depth > min_depth) {
                float attraction = (surface_depth - pos.z) * depthAttraction;
                vel.z += attraction * dt;
            }
        }
    }
    
    life -= dt;
    
    out_pos_life = vec4(pos, life);
    out_vel_seed = vec4(vel, seed);
}
"""

# --- SHADERS FOR VISUAL RENDERING ---

RENDER_VERTEX_SHADER = """
#version 330 core

uniform sampler2D tex_pos;
uniform sampler2D depth_tex; // just to sample matching colors if needed
uniform mat4 mvp;
uniform float min_depth;
uniform float max_depth;
uniform int color_mode;
uniform float particleSize;

out vec4 v_color;

void main() {
    // 100x100 texture array mapping 10k particles
    int tex_w = 100;
    int tex_h = 100;
    
    int x = gl_VertexID % tex_w;
    int y = gl_VertexID / tex_w;
    
    vec2 uv = vec2(float(x) / float(tex_w), float(y) / float(tex_h));
    
    vec4 pos_life = texture(tex_pos, uv);
    vec3 pos = pos_life.xyz;
    float life = pos_life.w;
    
    if (life <= 0.0) {
        gl_Position = vec4(2.0, 2.0, 2.0, 1.0); // Discard
        v_color = vec4(0.0);
        return;
    }
    
    gl_Position = mvp * vec4(pos, 1.0);
    gl_PointSize = particleSize;
    
    vec3 col = vec3(1.0, 1.0, 1.0);
    if (color_mode == 0) {
        float t = clamp((pos.z - min_depth) / (max_depth - min_depth), 0.0, 1.0);
        col = vec3(t, 0.5, 1.0 - t);
    } else if (color_mode == 1) {
        col = vec3(1.0, 0.5, 0.5);
    }
    
    // Fade alpha based on remaining life
    float alpha = clamp(life * 2.0, 0.0, 1.0); 
    v_color = vec4(col, alpha);
}
"""

RENDER_FRAGMENT_SHADER = """
#version 330 core
in vec4 v_color;
out vec4 fragColor;
void main() {
    fragColor = v_color;
}
"""

class DepthParticle3DPlugin(EffectPlugin):
    
    def __init__(self):
        super().__init__()
        self.sim_program = 0
        self.render_program = 0
        self.render_fbo = 0
        self.render_texture = 0
        self.width = 0
        self.height = 0
        self.empty_vao = 0
        
        # Ping Pong State (GPGPU Textures)
        # We need two pairs of textures attached to two Ping-Pong FBOs
        self.data_fbos = [0, 0]
        self.pos_textures = [0, 0]
        self.vel_textures = [0, 0]
        self.ping_idx = 0
        
        self.num_particles = 10000
        self.tex_w = 100
        self.tex_h = 100
        
        self.last_time = time.time()
        self._initialized = False

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def _compile_shader(self, vs_src: str, fs_src: str, name: str) -> int:
        vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vertex_shader, vs_src)
        gl.glCompileShader(vertex_shader)
        if not gl.glGetShaderiv(vertex_shader, gl.GL_COMPILE_STATUS):
            err = gl.glGetShaderInfoLog(vertex_shader)
            logger.error(f"{name} VS fail: {err}")
            return 0

        fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragment_shader, fs_src)
        gl.glCompileShader(fragment_shader)
        if not gl.glGetShaderiv(fragment_shader, gl.GL_COMPILE_STATUS):
            err = gl.glGetShaderInfoLog(fragment_shader)
            logger.error(f"{name} FS fail: {err}")
            return 0

        program = gl.glCreateProgram()
        gl.glAttachShader(program, vertex_shader)
        gl.glAttachShader(program, fragment_shader)
        gl.glLinkProgram(program)
        
        if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
            err = gl.glGetProgramInfoLog(program)
            logger.error(f"{name} link fail: {err}")
            return 0
            
        gl.glDeleteShader(vertex_shader)
        gl.glDeleteShader(fragment_shader)
        return program

    def initialize(self, context: PluginContext) -> bool:
        if not hasattr(gl, 'glCreateProgram'):
            logger.warning("Mock mode engaged. Skipping GL init.")
            return True

        try:
            self.sim_program = self._compile_shader(SIM_VERTEX_SHADER, SIM_FRAGMENT_SHADER, "SIM")
            if not self.sim_program: return False
            
            self.render_program = self._compile_shader(RENDER_VERTEX_SHADER, RENDER_FRAGMENT_SHADER, "RENDER")
            if not self.render_program: return False
            
            self.empty_vao = gl.glGenVertexArrays(1)
            
            # Setup Ping-Pong Data Textures (100x100 GL_RGBA32F)
            pos_data = np.zeros((self.tex_h, self.tex_w, 4), dtype=np.float32)
            vel_data = np.zeros((self.tex_h, self.tex_w, 4), dtype=np.float32)
            
            # Init lifetimes to -1.0 so they spawn immediately and seeds to random float.
            pos_data[..., 3] = -1.0 
            vel_data[..., 3] = np.random.rand(self.tex_h, self.tex_w) * 1000.0
            
            self.data_fbos = gl.glGenFramebuffers(2)
            self.pos_textures = gl.glGenTextures(2)
            self.vel_textures = gl.glGenTextures(2)
            
            for i in range(2):
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.data_fbos[i])
                
                # PosTexture Col0
                gl.glBindTexture(gl.GL_TEXTURE_2D, self.pos_textures[i])
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA32F, self.tex_w, self.tex_h, 0, gl.GL_RGBA, gl.GL_FLOAT, pos_data)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
                gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.pos_textures[i], 0)
                
                # VelTexture Col1
                gl.glBindTexture(gl.GL_TEXTURE_2D, self.vel_textures[i])
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA32F, self.tex_w, self.tex_h, 0, gl.GL_RGBA, gl.GL_FLOAT, vel_data)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
                gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT1, gl.GL_TEXTURE_2D, self.vel_textures[i], 0)
                
                # Assign DrawBuffers routing logic
                gl.glDrawBuffers(2, [gl.GL_COLOR_ATTACHMENT0, gl.GL_COLOR_ATTACHMENT1])
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
                
            self.last_time = time.time()
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize DepthParticle3DPlugin: {e}")
            return False

    def _setup_render_fbo(self, width: int, height: int):
        if self.width == width and self.height == height and self.render_fbo != 0:
            return

        if self.render_fbo != 0:
            gl.glDeleteFramebuffers(1, [self.render_fbo])
            gl.glDeleteTextures(1, [self.render_texture])

        self.width = width
        self.height = height
        
        self.render_fbo = gl.glGenFramebuffers(1)
        self.render_texture = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.render_texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.render_fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.render_texture, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

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
        
        mvp = projection_matrix @ view_matrix
        return mvp

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

        self._setup_render_fbo(w, h)
        
        depth_tex = context.inputs.get("depth_in", 0) if context and hasattr(context, 'inputs') else 0
        if depth_tex <= 0:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        current_time = time.time()
        dt = current_time - self.last_time
        if dt > 0.1: dt = 0.1 # Clamp extreme jumps
        self.last_time = current_time
        
        read_idx = self.ping_idx
        write_idx = 1 - self.ping_idx
        
        # --- PASS 1: GPGPU PHYSICS SIMULATION ---
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.data_fbos[write_idx])
        gl.glViewport(0, 0, self.tex_w, self.tex_h)
        gl.glUseProgram(self.sim_program)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.pos_textures[read_idx])
        gl.glUniform1i(gl.glGetUniformLocation(self.sim_program, "tex_pos"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.vel_textures[read_idx])
        gl.glUniform1i(gl.glGetUniformLocation(self.sim_program, "tex_vel"), 1)
        
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_tex)
        gl.glUniform1i(gl.glGetUniformLocation(self.sim_program, "depth_tex"), 2)
        
        gl.glUniform1f(gl.glGetUniformLocation(self.sim_program, "dt"), dt)
        gl.glUniform1f(gl.glGetUniformLocation(self.sim_program, "time"), current_time)
        gl.glUniform2f(gl.glGetUniformLocation(self.sim_program, "depth_res"), float(w), float(h))
        
        # Parameter Maps
        gl.glUniform1f(gl.glGetUniformLocation(self.sim_program, "particleLifetime"), max(0.5, float(params.get("particleLifetime", 0.5)) * 10.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.sim_program, "emissionRate"), float(params.get("emissionRate", 0.5)) * 500.0)
        gl.glUniform1f(gl.glGetUniformLocation(self.sim_program, "depthAttraction"), float(params.get("depthAttraction", 0.5)))
        
        d = float(params.get("damping", 0.5)) # 0-1 mapped to 0.9 - 1.0 multiplier
        gl.glUniform1f(gl.glGetUniformLocation(self.sim_program, "damping"), 0.9 + (d * 0.1))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.sim_program, "min_depth"), float(params.get("min_depth", 0.1)))
        gl.glUniform1f(gl.glGetUniformLocation(self.sim_program, "max_depth"), float(params.get("max_depth", 5.0)))
        
        # Draw Quad triggering Simulation
        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        
        # --- PASS 2: VISUAL RENDERING ---
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.render_fbo)
        gl.glViewport(0, 0, w, h)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        gl.glUseProgram(self.render_program)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.pos_textures[write_idx])
        gl.glUniform1i(gl.glGetUniformLocation(self.render_program, "tex_pos"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_tex)
        gl.glUniform1i(gl.glGetUniformLocation(self.render_program, "depth_tex"), 1)
        
        gl.glUniform1f(gl.glGetUniformLocation(self.render_program, "min_depth"), float(params.get("min_depth", 0.1)))
        gl.glUniform1f(gl.glGetUniformLocation(self.render_program, "max_depth"), float(params.get("max_depth", 5.0)))
        
        pSize = max(0.5, float(params.get("particleSize", 0.5)) * 10.0)
        gl.glUniform1f(gl.glGetUniformLocation(self.render_program, "particleSize"), pSize)
        
        color_mode_str = str(params.get("color_mode", "depth")).lower()
        cm = 0
        if color_mode_str == "velocity": cm = 1
        elif color_mode_str == "white": cm = 2
        gl.glUniform1i(gl.glGetUniformLocation(self.render_program, "color_mode"), cm)
        
        mvp = self._calculate_matrices(w, h, params)
        gl.glUniformMatrix4fv(gl.glGetUniformLocation(self.render_program, "mvp"), 1, gl.GL_FALSE, mvp.flatten())
        
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
        gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)
        
        # Draw 10,000 Particles exploiting VertexID Fetch natively reading the physics GPGPU data
        gl.glDrawArrays(gl.GL_POINTS, 0, self.num_particles)
        
        gl.glDisable(gl.GL_BLEND)
        gl.glDisable(gl.GL_PROGRAM_POINT_SIZE)
        gl.glBindVertexArray(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        self.ping_idx = write_idx
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.render_texture
            
        return self.render_texture

    def cleanup(self) -> None:
        try:
            if hasattr(gl, 'glDeleteProgram'):
                if self.sim_program != 0: gl.glDeleteProgram(self.sim_program)
                if self.render_program != 0: gl.glDeleteProgram(self.render_program)
            if hasattr(gl, 'glDeleteFramebuffers'):
                if self.render_fbo != 0: gl.glDeleteFramebuffers(1, [self.render_fbo])
                if self.data_fbos: gl.glDeleteFramebuffers(2, self.data_fbos)
            if hasattr(gl, 'glDeleteTextures'):
                if self.render_texture != 0: gl.glDeleteTextures(1, [self.render_texture])
                if self.pos_textures: gl.glDeleteTextures(2, self.pos_textures)
                if self.vel_textures: gl.glDeleteTextures(2, self.vel_textures)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao != 0:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Failed to cleanup DepthParticle3D plugin: {e}")
        finally:
            self.sim_program = 0
            self.render_program = 0
            self.render_fbo = 0
            self.render_texture = 0
            self.data_fbos = [0, 0]
            self.pos_textures = [0, 0]
            self.vel_textures = [0, 0]
            self.empty_vao = 0

