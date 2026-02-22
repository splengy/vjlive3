import os
import logging
from typing import Dict, Any, Optional
import numpy as np

from vjlive3.plugins.api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

# Mock GL for headless pytests via environment flag injection
try:
    if os.environ.get("PYTEST_MOCK_GL"):
        raise ImportError("Forced MOCK GL for pytest")
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
    gl = None

DEPTH_DISTANCE_FILTER_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform sampler2D tex_b;          // Optional secondary input for replacement
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Range
uniform float near_clip;            // Near distance threshold (0=camera, 1=far)
uniform float far_clip;             // Far distance threshold
uniform float edge_softness;        // Feathering at clip boundaries

// Mask behavior
uniform float invert;               // Invert the mask (show outside instead)
uniform float fill_mode;            // 0=transparent, 3.3=solid color, 6.6=blur, 10=input B
uniform vec3 fill_color;            // Fill color when mode=solid

// Mask refinement
uniform float edge_refine;          // Erode/dilate mask edges
uniform float smoothing;            // Temporal smoothing of the mask

// Output
uniform float show_mask;            // Preview mask as grayscale
uniform float depth_colorize;       // False-color the depth for visualization

void main() {
    float depth = texture(depth_tex, v_uv).r;
    vec4 source = texture(tex0, v_uv);

    // ====== DEPTH MASK ======
    // Compute mask based on near/far clip range
    float mask = 1.0;

    // Soft near clip
    mask *= smoothstep(near_clip - edge_softness * 0.1,
                       near_clip + edge_softness * 0.1, depth);

    // Soft far clip
    mask *= 1.0 - smoothstep(far_clip - edge_softness * 0.1,
                              far_clip + edge_softness * 0.1, depth);

    // ====== EDGE REFINEMENT ======
    if (abs(edge_refine) > 0.001) {
        // Sample neighbors for erode/dilate
        float texel = 2.0 / max(resolution.x, 1.0);
        float d_up = texture(depth_tex, v_uv + vec2(0, texel)).r;
        float d_dn = texture(depth_tex, v_uv - vec2(0, texel)).r;
        float d_lt = texture(depth_tex, v_uv - vec2(texel, 0)).r;
        float d_rt = texture(depth_tex, v_uv + vec2(texel, 0)).r;

        float m_up = smoothstep(near_clip, near_clip + 0.01, d_up)
                   * (1.0 - smoothstep(far_clip - 0.01, far_clip, d_up));
        float m_dn = smoothstep(near_clip, near_clip + 0.01, d_dn)
                   * (1.0 - smoothstep(far_clip - 0.01, far_clip, d_dn));
        float m_lt = smoothstep(near_clip, near_clip + 0.01, d_lt)
                   * (1.0 - smoothstep(far_clip - 0.01, far_clip, d_lt));
        float m_rt = smoothstep(near_clip, near_clip + 0.01, d_rt)
                   * (1.0 - smoothstep(far_clip - 0.01, far_clip, d_rt));

        if (edge_refine > 0.0) {
            // Dilate: take max of neighbors
            mask = max(mask, max(max(m_up, m_dn), max(m_lt, m_rt)) * edge_refine);
        } else {
            // Erode: take min of neighbors
            float neighbors_min = min(min(m_up, m_dn), min(m_lt, m_rt));
            mask = mix(mask, min(mask, neighbors_min), -edge_refine);
        }
    }

    // ====== INVERT ======
    if (invert > 0.5) {
        mask = 1.0 - mask;
    }

    // ====== FILL OUTSIDE MASK ======
    vec4 fill;
    if (fill_mode < 3.3) {
        // Transparent (black)
        fill = vec4(0.0, 0.0, 0.0, 0.0);
    } else if (fill_mode < 6.6) {
        // Solid color
        fill = vec4(fill_color, 1.0);
    } else if (fill_mode < 8.3) {
        // Blur: show blurred version outside mask
        vec4 blurred = vec4(0.0);
        float total = 0.0;
        
        // UNROLL SAFE: Limited loops to protect real-time constraint (SR1)
        for (int x = -2; x <= 2; x++) {
            for (int y = -2; y <= 2; y++) {
                vec2 offset = vec2(float(x), float(y)) * 4.0 / max(resolution, vec2(1.0));
                float w = 1.0 / (1.0 + float(abs(x) + abs(y)));
                blurred += texture(tex0, v_uv + offset) * w;
                total += w;
            }
        }
        fill = blurred / total;
    } else {
        // Input B (secondary video)
        fill = texture(tex_b, v_uv);
    }

    // ====== COMPOSE ======
    vec4 result = mix(fill, source, mask);

    // ====== VISUALIZATION MODES ======
    if (show_mask > 0.5) {
        // Show mask as grayscale
        result = vec4(vec3(mask), 1.0);
    }

    if (depth_colorize > 0.0) {
        // False-color depth visualization
        vec3 depth_color = vec3(depth); // Fallback monochrome 
        if (depth < 0.2)
            depth_color = mix(vec3(1,0,0), vec3(1,0.5,0), depth * 5.0);
        else if (depth < 0.4)
            depth_color = mix(vec3(1,0.5,0), vec3(1,1,0), (depth-0.2) * 5.0);
        else if (depth < 0.6)
            depth_color = mix(vec3(1,1,0), vec3(0,1,0), (depth-0.4) * 5.0);
        else if (depth < 0.8)
            depth_color = mix(vec3(0,1,0), vec3(0,0.5,1), (depth-0.6) * 5.0);
        else
            depth_color = mix(vec3(0,0.5,1), vec3(0.2,0,0.8), (depth-0.8) * 5.0);

        // Overlay mask boundary
        float mask_edge = abs(fract(mask * 4.0) - 0.5) < 0.05 ? 1.0 : 0.0;
        depth_color += vec3(mask_edge);

        result = mix(result, vec4(depth_color, 1.0), depth_colorize);
    }

    fragColor = mix(source, result, u_mix);
}
"""

METADATA = {
    "name": "Depth Distance Filter",
    "description": "Filter/mask video by depth range. Isolates pixels within a near/far depth window.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["mask", "distance", "filter", "depth"],
    "status": "active",
    "parameters": [
        {"name": "nearClip", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
        {"name": "farClip", "type": "float", "min": 0.0, "max": 10.0, "default": 8.0},
        {"name": "edgeSoftness", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "invert", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "fillMode", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "fillColorR", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "fillColorG", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "fillColorB", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "edgeRefine", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "smoothing", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "showMask", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "depthColorize", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in", "tex_b"],
    "outputs": ["video_out"]
}


class DepthDistanceFilterPlugin(EffectPlugin):
    """P3-VD33: Depth Distance Filter effect port mapped to VJLive3 standards."""
    
    def __init__(self) -> None:
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.ping_pong = 0
        self.time = 0.0
        
        self.textures: Dict[str, Optional[int]] = {"feedback_0": None, "feedback_1": None}
        self.fbos: Dict[str, Optional[int]] = {"feedback_0": None, "feedback_1": None}

    def _compile_shader(self):
        if not HAS_GL: return None
        try:
            vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
            gl.glShaderSource(vertex, "#version 330 core\\nlayout(location=0) in vec2 pos; layout(location=1) in vec2 uv; out vec2 v_uv; void main() { gl_Position = vec4(pos, 0.0, 1.0); v_uv = uv; }")
            gl.glCompileShader(vertex)
            
            fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fragment, DEPTH_DISTANCE_FILTER_FRAGMENT)
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
            self.prog = self._compile_shader()
            if not self.prog:
                self._mock_mode = True
                return

            tex_ids = gl.glGenTextures(2)
            fbo_ids = gl.glGenFramebuffers(2)
            if isinstance(tex_ids, int): tex_ids = [tex_ids, tex_ids+1]
            if isinstance(fbo_ids, int): fbo_ids = [fbo_ids, fbo_ids+1]
                
            for i, key in enumerate(self.textures.keys()):
                self.textures[key] = tex_ids[i]
                self.fbos[key] = fbo_ids[i]
                
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
            logger.warning(f"Failed to initialize GL FBOs inside DepthDistanceFilter: {e}")
            self._mock_mode = True

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if input_texture is None or input_texture == 0:
            return 0
            
        self.time += 0.016
            
        if self._mock_mode:
            context.outputs["video_out"] = input_texture
            return input_texture

        try:
            depth_in = context.inputs.get("depth_in", input_texture)
            tex_b_in = context.inputs.get("tex_b", input_texture)

            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            h = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_HEIGHT)
            
            # Use alternating FBOs to prevent read/write tearing when chained
            current_fbo = self.fbos[f"feedback_{1 - self.ping_pong}"]
            current_tex = self.textures[f"feedback_{1 - self.ping_pong}"]
            
            gl.glBindTexture(gl.GL_TEXTURE_2D, current_tex)
            tex_w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            if tex_w != w:
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, current_fbo)
                gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, current_tex, 0)
                
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, current_fbo)
            gl.glViewport(0, 0, w, h)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            
            gl.glUseProgram(self.prog)
            self._bind_uniforms(params, w, h)
            
            # Bind textures
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
            
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 1)
            
            gl.glActiveTexture(gl.GL_TEXTURE2)
            gl.glBindTexture(gl.GL_TEXTURE_2D, tex_b_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex_b"), 2)
            
            # Draw
            gl.glBindVertexArray(self.vao)
            gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
            gl.glBindVertexArray(0)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            
            self.ping_pong = 1 - self.ping_pong
            context.outputs["video_out"] = current_tex
            return current_tex
            
        except Exception as e:
            logger.error(f"Render failed: {e}")
            return input_texture

    def _map_param(self, params, name, out_min, out_max, default_val):
        val = params.get(name, default_val)
        return out_min + (val / 10.0) * (out_max - out_min)

    def _bind_uniforms(self, params, w, h):
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), float(self.time))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), params.get("u_mix", 1.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "near_clip"), self._map_param(params, 'nearClip', 0.0, 1.0, 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "far_clip"), self._map_param(params, 'farClip', 0.0, 1.0, 8.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "edge_softness"), self._map_param(params, 'edgeSoftness', 0.0, 1.0, 3.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "invert"), 1.0 if params.get('invert', 0.0) > 5.0 else 0.0)
        
        # Fill modes
        fill_mode_mapped = self._map_param(params, 'fillMode', 0.0, 10.0, 0.0)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fill_mode"), fill_mode_mapped)
        
        r = self._map_param(params, 'fillColorR', 0.0, 1.0, 0.0)
        g = self._map_param(params, 'fillColorG', 0.0, 1.0, 0.0)
        b = self._map_param(params, 'fillColorB', 0.0, 1.0, 0.0)
        gl.glUniform3f(gl.glGetUniformLocation(self.prog, "fill_color"), r, g, b)
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "edge_refine"), self._map_param(params, 'edgeRefine', -1.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "smoothing"), self._map_param(params, 'smoothing', 0.0, 1.0, 3.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "show_mask"), 1.0 if params.get('showMask', 0.0) > 5.0 else 0.0)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_colorize"), self._map_param(params, 'depthColorize', 0.0, 1.0, 0.0))

    def cleanup(self) -> None:
        if not self._mock_mode:
            try:
                textures_to_delete = [t for t in self.textures.values() if t is not None]
                if textures_to_delete:
                    gl.glDeleteTextures(len(textures_to_delete), textures_to_delete)
                fbos_to_delete = [f for f in self.fbos.values() if f is not None]
                if fbos_to_delete:
                    gl.glDeleteFramebuffers(len(fbos_to_delete), fbos_to_delete)
                if self.prog:
                    gl.glDeleteProgram(self.prog)
                if hasattr(self, 'vao') and self.vao:
                    gl.glDeleteVertexArrays(1, [self.vao])
                if hasattr(self, 'vbo') and self.vbo:
                    gl.glDeleteBuffers(1, [self.vbo])
            except Exception as e:
                logger.error(f"Error cleaning up FBOs/Textures during DepthDistanceFilter unload: {e}")
                
        for k in self.textures:
            self.textures[k] = None
            self.fbos[k] = None
