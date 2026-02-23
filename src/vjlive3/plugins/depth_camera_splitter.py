import numpy as np
import logging

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from typing import Dict, Any
from vjlive3.plugins.api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

METADATA = {
    "name": "DepthCameraSplitter",
    "version": "3.0.0",
    "description": "Split video into multiple camera views by depth range",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "camera",
    "tags": ["depth", "camera", "split", "parallax", "multi-view"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "num_splits", "type": "int", "default": 3, "min": 2, "max": 8},
        {"name": "split_method", "type": "str", "default": "uniform", "options": ["uniform", "adaptive", "custom"]},
        {"name": "custom_depths", "type": "list", "default": []},
        {"name": "camera_offsets", "type": "list", "default": []},
        {"name": "blend_edges", "type": "bool", "default": True},
        {"name": "blend_width", "type": "float", "default": 0.05, "min": 0.0, "max": 0.2}
    ]
}

VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 position;
layout(location = 1) in vec2 texcoord;
out vec2 uv;
void main() {
    uv = texcoord;
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

DEPTH_CAMERA_SPLITTER_FRAGMENT = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform vec2 resolution;

uniform int num_splits;
uniform float depth_bounds[8]; 
uniform vec4 split_transforms[8]; // x: offset_x, y: offset_y, z: zoom, w: rotation
uniform bool blend_edges;
uniform float blend_width;

// Helper to apply 2D affine transform to UV
vec2 apply_transform(vec2 uv_in, vec4 trans) {
    vec2 offset = trans.xy;
    float zoom = trans.z;
    float rot = trans.w;
    
    // Zoom around center
    vec2 coords = uv_in - 0.5;
    coords /= max(zoom, 0.001); // Avoid division by zero
    
    // Rotate
    float s = sin(rot);
    float c = cos(rot);
    vec2 rotated = vec2(
        coords.x * c - coords.y * s,
        coords.x * s + coords.y * c
    );
    
    // Apply panning
    rotated += offset;
    
    return rotated + 0.5;
}

void main() {
    float depth = texture(depth_tex, uv).r;
    
    // Determine the primary split index for the current fragment
    int best_split = 0;
    for (int i = 0; i < 8; i++) {
        if(i >= num_splits) break;
        if(depth <= depth_bounds[i]) {
            best_split = i;
            break;
        }
    }
    
    vec2 final_uv = apply_transform(uv, split_transforms[best_split]);
    vec4 primary_color = texture(tex0, final_uv);
    
    vec4 result = primary_color;
    
    // Optional edge blending
    if (blend_edges && blend_width > 0.0) {
        float dist_to_upper = 1000.0;
        float dist_to_lower = 1000.0;
        
        if (best_split < num_splits - 1) {
            dist_to_upper = depth_bounds[best_split] - depth;
        }
        if (best_split > 0) {
            dist_to_lower = depth - depth_bounds[best_split - 1];
        }
        
        if (dist_to_upper < blend_width) {
            float blend_factor = min(1.0, (blend_width - dist_to_upper) / blend_width) * 0.5;
            vec2 adj_uv = apply_transform(uv, split_transforms[best_split + 1]);
            vec4 adj_color = texture(tex0, adj_uv);
            result = mix(result, adj_color, blend_factor);
        }
        else if (dist_to_lower < blend_width) {
            float blend_factor = min(1.0, (blend_width - dist_to_lower) / blend_width) * 0.5;
            vec2 adj_uv = apply_transform(uv, split_transforms[best_split - 1]);
            vec4 adj_color = texture(tex0, adj_uv);
            result = mix(result, adj_color, blend_factor);
        }
    }
    
    fragColor = result;
}
"""


class DepthCameraSplitterPlugin(EffectPlugin):
    """
    DepthCameraSplitter plugin port for VJLive3.
    """
    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.out_tex = None
        self.fbo = None
        self.vao = None
        self.vbo = None

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthCameraSplitter in Mock Mode (No OpenGL)")
            return

        try:
            self._compile_shader()
            self._setup_quad()
            self._setup_fbo(1920, 1080)
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthCameraSplitter: {e}")
            self._mock_mode = True

    def _compile_shader(self):
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"Vertex Shader Error: {gl.glGetShaderInfoLog(vs)}")

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, DEPTH_CAMERA_SPLITTER_FRAGMENT)
        gl.glCompileShader(fs)
        if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"Fragment Shader Error: {gl.glGetShaderInfoLog(fs)}")

        self.prog = gl.glCreateProgram()
        gl.glAttachShader(self.prog, vs)
        gl.glAttachShader(self.prog, fs)
        gl.glLinkProgram(self.prog)
        if not gl.glGetProgramiv(self.prog, gl.GL_LINK_STATUS):
            raise RuntimeError(f"Program Link Error: {gl.glGetProgramInfoLog(self.prog)}")
            
        gl.glDeleteShader(vs)
        gl.glDeleteShader(fs)

    def _setup_quad(self):
        vertices = np.array([
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 1.0,
             1.0,  1.0,  1.0, 1.0,
        ], dtype=np.float32)
        
        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        
        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
        
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(8))
        gl.glBindVertexArray(0)

    def _setup_fbo(self, w: int, h: int):
        self.fbo = gl.glGenFramebuffers(1)
        self.out_tex = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.out_tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.out_tex, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _bind_uniforms(self, params: Dict[str, Any], w: int, h: int):
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        
        n_splits = max(2, min(8, int(params.get("num_splits", 3))))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "num_splits"), n_splits)
        
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "blend_edges"), int(params.get("blend_edges", True)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "blend_width"), float(params.get("blend_width", 0.05)))
        
        split_m = params.get("split_method", "uniform")
        bounds = np.zeros(8, dtype=np.float32)

        if split_m == "custom":
            custom_d = params.get("custom_depths", [])
            limit = min(n_splits, len(custom_d))
            for i in range(limit):
                bounds[i] = custom_d[i]
            for i in range(limit, 8):
                bounds[i] = 1.0
        else: # uniform + adaptive (fallback maps to uniform without histo pass)
            step = 1.0 / n_splits
            for i in range(n_splits):
                bounds[i] = step * (i + 1)
            for i in range(n_splits, 8): bounds[i] = 1.0

        gl.glUniform1fv(gl.glGetUniformLocation(self.prog, "depth_bounds"), 8, bounds)

        raw_offsets = params.get("camera_offsets", [])
        if not isinstance(raw_offsets, list):
            raw_offsets = []

        transforms = np.zeros(32, dtype=np.float32)
        for i in range(8):
            base_idx = i * 4
            if i < len(raw_offsets) and isinstance(raw_offsets[i], dict):
                d = raw_offsets[i]
                transforms[base_idx + 0] = float(d.get("offset_x", 0.0))
                transforms[base_idx + 1] = float(d.get("offset_y", 0.0))
                transforms[base_idx + 2] = float(d.get("zoom", 1.0))
                transforms[base_idx + 3] = float(d.get("rotation", 0.0))
            else:
                transforms[base_idx + 0] = 0.0
                transforms[base_idx + 1] = 0.0
                transforms[base_idx + 2] = 1.0 # default zoom
                transforms[base_idx + 3] = 0.0

        gl.glUniform4fv(gl.glGetUniformLocation(self.prog, "split_transforms"), 8, transforms)


    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        depth_texture = getattr(context, "inputs", {}).get("depth_in", input_texture)
        
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        gl.glUseProgram(self.prog)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 1)
        
        self._bind_uniforms(params, w, h)
        
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.out_tex
            
        return self.out_tex

    def cleanup(self) -> None:
        if self._mock_mode:
            return
            
        try:
            if self.out_tex:
                gl.glDeleteTextures(1, [self.out_tex])
                self.out_tex = None
            if self.fbo:
                gl.glDeleteFramebuffers(1, [self.fbo])
                self.fbo = None
            if self.vbo:
                gl.glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.vao:
                gl.glDeleteVertexArrays(1, [self.vao])
                self.vao = None
            if self.prog:
                gl.glDeleteProgram(self.prog)
                self.prog = None
        except Exception as e:
            logger.error(f"Cleanup Error in DepthCameraSplitter: {e}")
