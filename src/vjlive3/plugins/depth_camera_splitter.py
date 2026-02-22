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

DEPTH_SPLITTER_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;           // Source video (color from depth cam)
uniform sampler2D depth_tex;      // Depth data
uniform sampler2D ir_tex;         // IR data (if available)
uniform float time;
uniform vec2 resolution;

uniform float output_select;       // Which output to render
uniform float depth_min;           // Near clip for depth normalization
uniform float depth_max;           // Far clip for depth normalization
uniform float depth_gamma;         // Gamma curve on depth (compress/expand ranges)
uniform float ir_brightness;       // IR feed brightness boost
uniform float ir_contrast;        // IR contrast
uniform float color_exposure;      // Color feed exposure adjustment
uniform float color_saturation;    // Color feed saturation
uniform float colorize_palette;    // False-color palette selection
uniform float depth_smooth;        // Bilateral smoothing on depth output

// False color palettes
vec3 turbo_colormap(float t) {
    t = clamp(t, 0.0, 1.0);
    if (t < 0.25) return mix(vec3(0.18, 0.0, 0.85), vec3(0.0, 0.7, 0.9), t * 4.0);
    if (t < 0.5)  return mix(vec3(0.0, 0.7, 0.9), vec3(0.2, 0.9, 0.1), (t - 0.25) * 4.0);
    if (t < 0.75) return mix(vec3(0.2, 0.9, 0.1), vec3(1.0, 0.85, 0.0), (t - 0.5) * 4.0);
    return mix(vec3(1.0, 0.85, 0.0), vec3(0.9, 0.1, 0.0), (t - 0.75) * 4.0);
}

vec3 thermal_colormap(float t) {
    t = clamp(t, 0.0, 1.0);
    if (t < 0.33) return mix(vec3(0.0, 0.0, 0.1), vec3(0.5, 0.0, 0.8), t * 3.0);
    if (t < 0.66) return mix(vec3(0.5, 0.0, 0.8), vec3(1.0, 0.5, 0.0), (t - 0.33) * 3.0);
    return mix(vec3(1.0, 0.5, 0.0), vec3(1.0, 1.0, 0.8), (t - 0.66) * 3.0);
}

vec3 ocean_colormap(float t) {
    t = clamp(t, 0.0, 1.0);
    if (t < 0.5) return mix(vec3(0.0, 0.02, 0.15), vec3(0.0, 0.4, 0.6), t * 2.0);
    return mix(vec3(0.0, 0.4, 0.6), vec3(0.6, 0.9, 1.0), (t - 0.5) * 2.0);
}

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0/3.0, 1.0/3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

void main() {
    float safe_output = min(output_select, 3.0);

    vec3 color = texture(tex0, v_uv).rgb;
    float depth_raw = texture(depth_tex, v_uv).r;
    float ir_raw = texture(ir_tex, v_uv).r;

    // ====== DEPTH NORMALIZATION ======
    float safe_depth_max = max(depth_max, depth_min + 0.001);
    float depth_norm = (depth_raw - depth_min) / max(safe_depth_max - depth_min, 0.001);
    depth_norm = clamp(depth_norm, 0.0, 1.0);
    // Gamma
    depth_norm = pow(depth_norm, max(depth_gamma, 0.001));

    // Smoothing
    if (depth_smooth > 0.0 && safe_output == 1.0 || safe_output == 3.0) {
        float t = depth_smooth * 3.0 / max(resolution.x, 1.0);
        float sum = depth_norm;
        float weight = 1.0;
        
        // SAFETY RAIL 1: Limit unrolled iterations for minimum FPS bounds
        for (int x = -1; x <= 1; x++) {
            for (int y = -1; y <= 1; y++) {
                if (x == 0 && y == 0) continue;
                vec2 off = vec2(float(x), float(y)) * t;
                float s = texture(depth_tex, v_uv + off).r;
                s = clamp((s - depth_min) / max(safe_depth_max - depth_min, 0.001), 0.0, 1.0);
                float color_sim = 1.0 - length(texture(tex0, v_uv + off).rgb - color) * 2.0;
                color_sim = max(color_sim, 0.1);
                sum += s * color_sim;
                weight += color_sim;
            }
        }
        depth_norm = sum / weight;
    }

    if (safe_output < 1.0) {
        // COLOR OUT — enhanced color feed
        vec3 enhanced = color * pow(2.0, (color_exposure - 0.5) * 2.0);
        vec3 hsv = rgb2hsv(clamp(enhanced, 0.0, 1.0));
        hsv.y *= color_saturation * 2.0;
        hsv.y = clamp(hsv.y, 0.0, 1.0);
        fragColor = vec4(hsv2rgb(hsv), 1.0);
    }
    else if (safe_output < 2.0) {
        // DEPTH OUT — normalized grayscale depth
        fragColor = vec4(vec3(depth_norm), 1.0);
    }
    else if (safe_output < 3.0) {
        // IR OUT — enhanced infrared
        float ir = ir_raw * ir_brightness * 2.0;
        ir = (ir - 0.5) * (1.0 + ir_contrast * 3.0) + 0.5;
        fragColor = vec4(vec3(clamp(ir, 0.0, 1.0)), 1.0);
    }
    else {
        // DEPTH COLORIZED — false color visualization
        vec3 colorized;
        if (colorize_palette < 3.3) {
            colorized = turbo_colormap(depth_norm);
        } else if (colorize_palette < 6.6) {
            colorized = thermal_colormap(depth_norm);
        } else {
            colorized = ocean_colormap(depth_norm);
        }
        fragColor = vec4(colorized, 1.0);
    }
}
"""

METADATA = {
    "name": "Depth Camera Splitter",
    "description": "Gateway node for depth camera setups. Splits a depth camera into independent output streams.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["split", "camera", "color", "depth", "ir"],
    "status": "active",
    "parameters": [
        {"name": "depthMin", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
        {"name": "depthMax", "type": "float", "min": 0.0, "max": 10.0, "default": 8.0},
        {"name": "depthGamma", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "irBrightness", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "irContrast", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "colorExposure", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "colorSaturation", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "colorizePalette", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "depthSmooth", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "outputSelect", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0}
    ],
    "inputs": ["video_in", "depth_in", "ir_in"],
    "outputs": ["video_out"]
}

class DepthCameraSplitterPlugin(EffectPlugin):
    """P3-VD29: Depth Camera Splitter effect port mapping VJlive-2 parameters."""
    
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
            gl.glShaderSource(fragment, DEPTH_SPLITTER_FRAGMENT)
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
            logger.warning(f"Failed to initialize GL FBOs inside DepthCameraSplitter: {e}")
            self._mock_mode = True

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if input_texture is None or input_texture == 0:
            return 0
            
        self.time += 0.016 # simulate advancing time if not passed
            
        if self._mock_mode:
            context.outputs["video_out"] = input_texture
            return input_texture

        try:
            depth_in = context.inputs.get("depth_in", input_texture)
            ir_in = context.inputs.get("ir_in", input_texture)

            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            h = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_HEIGHT)
            
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
            gl.glBindTexture(gl.GL_TEXTURE_2D, ir_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "ir_tex"), 2)
            
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
        
        # Output select behaves via round stepping
        out_sel_raw = params.get('outputSelect', 0.0)
        mapped_out_sel = min(3.0, (out_sel_raw / 10.0) * 3.99)
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "output_select"), float(int(mapped_out_sel)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_min"), self._map_param(params, 'depthMin', 0.0, 1.0, 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_max"), self._map_param(params, 'depthMax', 0.0, 1.0, 8.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_gamma"), self._map_param(params, 'depthGamma', 0.2, 3.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "ir_brightness"), self._map_param(params, 'irBrightness', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "ir_contrast"), self._map_param(params, 'irContrast', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "color_exposure"), self._map_param(params, 'colorExposure', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "color_saturation"), self._map_param(params, 'colorSaturation', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "colorize_palette"), self._map_param(params, 'colorizePalette', 0.0, 10.0, 0.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_smooth"), self._map_param(params, 'depthSmooth', 0.0, 1.0, 3.0))

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
                logger.error(f"Error cleaning up FBOs/Textures during DepthCameraSplitter unload: {e}")
                
        for k in self.textures:
            self.textures[k] = None
            self.fbos[k] = None

