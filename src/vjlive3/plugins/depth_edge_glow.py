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

DEPTH_EDGE_GLOW_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

uniform float edge_threshold;       // Sensitivity of edge detection
uniform float edge_thickness;       // Line thickness
uniform float glow_radius;          // Bloom/glow falloff around edges
uniform float glow_intensity;       // Brightness of the glow
uniform float contour_lines;        // Number of depth contour intervals
uniform float contour_width;        // Width of contour lines
uniform float hue_mode;             // 0=fixed, 3.3=depth-mapped, 6.6=rainbow cycle
uniform vec3 edge_color;            // Base edge color (when hue_mode=fixed)
uniform float pulse_speed;          // Breathing/pulse animation speed
uniform float pulse_amount;         // Pulse intensity
uniform float source_dim;           // How much to dim the source image
uniform float inner_glow;           // Inner glow vs outer glow balance

vec3 hsv2rgb(vec3 c) {
    vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0/3.0, 1.0/3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

float depth_edge_multi(vec2 p, float scale) {
    float t = scale / max(resolution.x, 1.0);

    float tl = texture(depth_tex, p + vec2(-t, -t)).r;
    float tc = texture(depth_tex, p + vec2( 0, -t)).r;
    float tr = texture(depth_tex, p + vec2( t, -t)).r;
    float ml = texture(depth_tex, p + vec2(-t,  0)).r;
    float mr = texture(depth_tex, p + vec2( t,  0)).r;
    float bl = texture(depth_tex, p + vec2(-t,  t)).r;
    float bc = texture(depth_tex, p + vec2( 0,  t)).r;
    float br = texture(depth_tex, p + vec2( t,  t)).r;

    float gx = -tl - 2.0*ml - bl + tr + 2.0*mr + br;
    float gy = -tl - 2.0*tc - tr + bl + 2.0*bc + br;
    return sqrt(gx*gx + gy*gy);
}

void main() {
    float depth = texture(depth_tex, v_uv).r;
    vec4 source = texture(tex0, v_uv);

    // ====== MULTI-SCALE EDGE DETECTION ======
    float edge = 0.0;
    float thick = edge_thickness * 3.0 + 1.0;
    // UNROLL SAFE: Max 4 scales
    for (float s = 1.0; s <= 4.0; s += 1.0) {
        if (s > thick) break;
        edge = max(edge, depth_edge_multi(v_uv, s));
    }

    edge = smoothstep(edge_threshold * 0.05, edge_threshold * 0.05 + 0.05, edge);

    // ====== CONTOUR LINES ======
    float contour = 0.0;
    if (contour_lines > 0.0) {
        float intervals = contour_lines * 10.0 + 2.0;
        float contour_val = fract(depth * intervals);
        contour = 1.0 - smoothstep(0.0, contour_width * 0.1, contour_val)
                + smoothstep(1.0 - contour_width * 0.1, 1.0, contour_val);
        contour *= 0.7;  // Contours slightly dimmer than edges
    }

    float total_edge = max(edge, contour);

    // ====== GLOW ======
    float glow = 0.0;
    if (glow_radius > 0.0) {
        int glow_samples = int(glow_radius * 3.0) + 2;
        float glow_r = glow_radius * 5.0;

        for (int x = -2; x <= 2; x++) {
            for (int y = -2; y <= 2; y++) {
                if (abs(x) + abs(y) > glow_samples) continue;
                vec2 offset = vec2(float(x), float(y)) * glow_r / max(resolution, vec2(1.0));
                float e = depth_edge_multi(v_uv + offset, 1.5);
                e = smoothstep(edge_threshold * 0.05, edge_threshold * 0.05 + 0.05, e);
                float dist = length(vec2(float(x), float(y)));
                glow += e * exp(-dist * 0.5);
            }
        }
        glow /= float((2 * 2 + 1) * (2 * 2 + 1));
        glow *= glow_intensity * 4.0;
    }

    float final_glow = mix(glow, glow * (1.0 - total_edge), inner_glow);

    // ====== PULSE ANIMATION ======
    float pulse = 1.0;
    if (pulse_amount > 0.0) {
        pulse = 1.0 + sin(time * pulse_speed * 3.0) * pulse_amount * 0.3;
        pulse += sin(time * pulse_speed * 2.0 + depth * 6.283) * pulse_amount * 0.15;
    }

    // ====== COLOR ======
    vec3 line_color;
    if (hue_mode < 3.3) {
        line_color = edge_color;
    } else if (hue_mode < 6.6) {
        float hue = depth + time * 0.05;
        line_color = hsv2rgb(vec3(hue, 0.9, 1.0));
    } else {
        float hue = time * 0.3 + v_uv.x * 0.5 + depth;
        line_color = hsv2rgb(vec3(hue, 1.0, 1.0));
    }

    // ====== COMPOSE ======
    vec3 dimmed_source = source.rgb * (1.0 - source_dim * 0.9);
    vec3 result = dimmed_source;
    result += line_color * total_edge * pulse * glow_intensity;
    result += line_color * final_glow * pulse * 0.5;

    fragColor = mix(source, vec4(result, 1.0), u_mix);
}
"""

METADATA = {
    "name": "Depth Edge Glow",
    "description": "Neon depth contour visualization. Turns depth boundaries into glowing contours with bloom and multi-scale Sobel.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["glow", "edge", "neon", "sobel", "contour"],
    "status": "active",
    "parameters": [
        {"name": "edgeThreshold", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "edgeThickness", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "glowRadius", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "glowIntensity", "type": "float", "min": 0.0, "max": 10.0, "default": 6.0},
        {"name": "contourLines", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "contourWidth", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "hueMode", "type": "float", "min": 0.0, "max": 10.0, "default": 3.3},
        {"name": "edgeColorR", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "edgeColorG", "type": "float", "min": 0.0, "max": 10.0, "default": 10.0},
        {"name": "edgeColorB", "type": "float", "min": 0.0, "max": 10.0, "default": 8.0},
        {"name": "pulseSpeed", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "pulseAmount", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "sourceDim", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "innerGlow", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}


class DepthEdgeGlowPlugin(EffectPlugin):
    """P3-VD35: Depth Edge Glow effect port mapping VJlive-2 to VJLive3."""
    
    def __init__(self) -> None:
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.time = 0.0
        
        self.texture: Optional[int] = None
        self.fbo: Optional[int] = None

    def _compile_shader(self):
        if not HAS_GL: return None
        try:
            vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
            gl.glShaderSource(vertex, "#version 330 core\\nlayout(location=0) in vec2 pos; layout(location=1) in vec2 uv; out vec2 v_uv; void main() { gl_Position = vec4(pos, 0.0, 1.0); v_uv = uv; }")
            gl.glCompileShader(vertex)
            
            fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fragment, DEPTH_EDGE_GLOW_FRAGMENT)
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
            logger.warning(f"Failed to initialize GL FBOs inside DepthEdgeGlowPlugin: {e}")
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
            self._bind_uniforms(params, w, h)
            
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
            logger.error(f"Render failed in Depth Edge Glow: {e}")
            return input_texture

    def _map_param(self, params, name, out_min, out_max, default_val):
        val = params.get(name, default_val)
        return out_min + (val / 10.0) * (out_max - out_min)

    def _bind_uniforms(self, params, w, h):
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), float(self.time))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), params.get("u_mix", 1.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "edge_threshold"), self._map_param(params, 'edgeThreshold', 0.0, 1.0, 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "edge_thickness"), self._map_param(params, 'edgeThickness', 0.0, 1.0, 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "glow_radius"), self._map_param(params, 'glowRadius', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "glow_intensity"), self._map_param(params, 'glowIntensity', 0.0, 1.0, 6.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "contour_lines"), self._map_param(params, 'contourLines', 0.0, 1.0, 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "contour_width"), self._map_param(params, 'contourWidth', 0.0, 1.0, 3.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "hue_mode"), self._map_param(params, 'hueMode', 0.0, 10.0, 3.3))
        
        r = self._map_param(params, 'edgeColorR', 0.0, 1.0, 0.0)
        g = self._map_param(params, 'edgeColorG', 0.0, 1.0, 1.0)
        b = self._map_param(params, 'edgeColorB', 0.0, 1.0, 0.8)
        gl.glUniform3f(gl.glGetUniformLocation(self.prog, "edge_color"), r, g, b)
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "pulse_speed"), self._map_param(params, 'pulseSpeed', 0.0, 1.0, 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "pulse_amount"), self._map_param(params, 'pulseAmount', 0.0, 1.0, 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "source_dim"), self._map_param(params, 'sourceDim', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "inner_glow"), self._map_param(params, 'innerGlow', 0.0, 1.0, 3.0))

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
                logger.error(f"Error cleaning up FBOs/Textures during DepthEdgeGlow unload: {e}")
                
        self.texture = None
        self.fbo = None
