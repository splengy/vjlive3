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

DEPTH_COLOR_GRADE_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Zone boundaries
uniform float zone_near;            // Near/mid boundary
uniform float zone_far;             // Mid/far boundary
uniform float zone_blend;           // Transition softness between zones

// Near zone grading
uniform float near_hue;             // Hue rotation
uniform float near_saturation;      // Saturation boost/cut
uniform float near_temperature;     // Warm/cool shift
uniform float near_exposure;        // Brightness

// Mid zone grading
uniform float mid_hue;
uniform float mid_saturation;
uniform float mid_temperature;
uniform float mid_exposure;

// Far zone grading
uniform float far_hue;
uniform float far_saturation;
uniform float far_temperature;
uniform float far_exposure;

// Global
uniform float contrast;
uniform float film_curve;           // 0=linear, 5=S-curve, 10=log

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

// Apply color grading to a pixel
vec3 grade(vec3 color, float hue_shift, float sat_mult, float temp, float exposure) {
    // Exposure
    color *= pow(2.0, (exposure - 0.5) * 2.0);

    // Temperature (orange-blue shift)
    float t = (temp - 0.5) * 0.3;
    color.r += t;
    color.b -= t;

    // Hue + saturation in HSV
    vec3 hsv = rgb2hsv(clamp(color, 0.0, 1.0));
    hsv.x = fract(hsv.x + hue_shift);
    hsv.y *= sat_mult;
    hsv.y = clamp(hsv.y, 0.0, 1.0);

    return hsv2rgb(hsv);
}

// Film emulation curves
vec3 apply_curve(vec3 color, float mode) {
    if (mode < 3.3) {
        // Linear (no change)
        return color;
    } else if (mode < 6.6) {
        // S-curve (cinematic contrast)
        return color * color * (3.0 - 2.0 * color);
    } else {
        // Log (flat, cinematic log encoding)
        return log(1.0 + color * 9.0) / log(10.0);
    }
}

void main() {
    float depth = texture(depth_tex, v_uv).r;
    vec4 source = texture(tex0, v_uv);
    vec3 color = source.rgb;

    // ====== ZONE MASKS ======
    float blend = zone_blend * 0.15 + 0.01;
    float near_mask = 1.0 - smoothstep(zone_near - blend, zone_near + blend, depth);
    float far_mask = smoothstep(zone_far - blend, zone_far + blend, depth);
    float mid_mask = 1.0 - near_mask - far_mask;
    mid_mask = max(mid_mask, 0.0);

    // ====== PER-ZONE GRADING ======
    vec3 near_graded = grade(color, near_hue, near_saturation * 2.0, near_temperature, near_exposure);
    vec3 mid_graded = grade(color, mid_hue, mid_saturation * 2.0, mid_temperature, mid_exposure);
    vec3 far_graded = grade(color, far_hue, far_saturation * 2.0, far_temperature, far_exposure);

    // Blend zones
    vec3 graded = near_graded * near_mask + mid_graded * mid_mask + far_graded * far_mask;

    // ====== GLOBAL CONTRAST ======
    if (contrast != 0.5) {
        float c = (contrast - 0.5) * 2.0;
        graded = mix(vec3(0.5), graded, 1.0 + c);
    }

    // ====== FILM CURVE ======
    graded = apply_curve(clamp(graded, 0.0, 1.0), film_curve);

    fragColor = mix(source, vec4(clamp(graded, 0.0, 1.0), 1.0), u_mix);
}
"""

METADATA = {
    "name": "Depth Color Grade",
    "description": "3-zone depth color grading — independent hue/saturation/temperature/exposure per depth band.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["grading", "color", "zones", "film"],
    "status": "active",
    "parameters": [
        # Zone boundaries
        {"name": "zoneNear", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "zoneFar", "type": "float", "min": 0.0, "max": 10.0, "default": 7.0},
        {"name": "zoneBlend", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        # Near
        {"name": "nearHue", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "nearSaturation", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "nearTemperature", "type": "float", "min": 0.0, "max": 10.0, "default": 6.0},
        {"name": "nearExposure", "type": "float", "min": 0.0, "max": 10.0, "default": 5.5},
        # Mid
        {"name": "midHue", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "midSaturation", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "midTemperature", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "midExposure", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        # Far
        {"name": "farHue", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "farSaturation", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "farTemperature", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "farExposure", "type": "float", "min": 0.0, "max": 10.0, "default": 4.5},
        # Global
        {"name": "contrast", "type": "float", "min": 0.0, "max": 10.0, "default": 5.5},
        {"name": "filmCurve", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthColorGradePlugin(EffectPlugin):
    """P3-VD30: Depth Color Grade effect port mapping VJlive-2 parameters."""
    
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
            gl.glShaderSource(fragment, DEPTH_COLOR_GRADE_FRAGMENT)
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
            logger.warning(f"Failed to initialize GL FBOs inside DepthColorGrade: {e}")
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
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), float(params.get("u_mix", 1.0)))

        # Zones
        zn = self._map_param(params, 'zoneNear', 0.0, 1.0, 3.0)
        zf = self._map_param(params, 'zoneFar', 0.0, 1.0, 7.0)
        if zn > zf:
            zn, zf = zf, zn # Soften edge case flip

        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "zone_near"), zn)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "zone_far"), zf)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "zone_blend"), self._map_param(params, 'zoneBlend', 0.0, 1.0, 4.0))

        # Near
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "near_hue"), self._map_param(params, 'nearHue', 0.0, 1.0, 0.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "near_saturation"), self._map_param(params, 'nearSaturation', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "near_temperature"), self._map_param(params, 'nearTemperature', 0.0, 1.0, 6.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "near_exposure"), self._map_param(params, 'nearExposure', 0.0, 1.0, 5.5))

        # Mid
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "mid_hue"), self._map_param(params, 'midHue', 0.0, 1.0, 0.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "mid_saturation"), self._map_param(params, 'midSaturation', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "mid_temperature"), self._map_param(params, 'midTemperature', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "mid_exposure"), self._map_param(params, 'midExposure', 0.0, 1.0, 5.0))

        # Far
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "far_hue"), self._map_param(params, 'farHue', 0.0, 1.0, 0.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "far_saturation"), self._map_param(params, 'farSaturation', 0.0, 1.0, 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "far_temperature"), self._map_param(params, 'farTemperature', 0.0, 1.0, 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "far_exposure"), self._map_param(params, 'farExposure', 0.0, 1.0, 4.5))

        # Global
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "contrast"), self._map_param(params, 'contrast', 0.0, 1.0, 5.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "film_curve"), self._map_param(params, 'filmCurve', 0.0, 10.0, 5.0))

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
                logger.error(f"Error cleaning up FBOs/Textures during DepthColorGrade unload: {e}")
                
        for k in self.textures:
            self.textures[k] = None
            self.fbos[k] = None

