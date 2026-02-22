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

DEPTH_BLUR_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

uniform float focal_distance;       // Depth plane that's in focus
uniform float focal_range;          // Width of the in-focus zone
uniform float blur_amount;          // Maximum blur radius
uniform float fg_blur;              // Foreground blur multiplier
uniform float bg_blur;              // Background blur multiplier
uniform float bokeh_bright;         // Bright spot bloom boost
uniform float chromatic_fringe;     // Chromatic aberration at bokeh edges
uniform float tilt_shift;           // 0=depth-based, >0=spatial tilt-shift
uniform float tilt_angle;           // Tilt-shift angle (when mode active)
uniform float aperture;             // Bokeh shape: 0=circle, 5=hex, 10=star
uniform float quality;              // Sample count quality (perf vs quality)
uniform float vignette;             // Darken corners with depth-aware vignette

#define PI 3.14159265

// Bokeh kernel — weighted disc with optional shape
vec4 bokeh_blur(vec2 center, float radius, float bright_boost) {
    vec4 color = vec4(0.0);
    float total = 0.0;

    int samples = int(mix(8.0, 32.0, quality));
    float golden = 2.399963;  // Golden angle in radians
    
    // SAFETY RAIL 1: Protect 60FPS by hard-capping max loop iteration regardless of uniform
    samples = min(samples, 32);

    for (int i = 0; i < 32; i++) {
        if (i >= samples) break;
        float fi = float(i);

        // Disc distribution using golden angle
        float r = sqrt(fi / float(samples)) * radius;
        float theta = fi * golden;
        vec2 offset = vec2(cos(theta), sin(theta)) * r / resolution;

        // Shape aperture (hexagonal when aperture > 3)
        if (aperture > 3.0) {
            float blade_count = mix(6.0, 8.0, (aperture - 3.3) / 6.7);
            float blade_angle = atan(offset.y, offset.x);
            float blade = cos(blade_angle * blade_count);
            float shape = mix(1.0, smoothstep(0.3, 0.7, blade), (aperture - 3.3) / 6.7 * 0.5);
            r *= shape;
            offset = vec2(cos(theta), sin(theta)) * r / resolution;
        }

        vec4 s = texture(tex0, center + offset);

        // Bokeh brightness: brighter samples get more weight
        float luma = dot(s.rgb, vec3(0.299, 0.587, 0.114));
        float weight = 1.0 + luma * bright_boost * 3.0;

        color += s * weight;
        total += weight;
    }

    return color / max(total, 1.0);
}

void main() {
    float depth = texture(depth_tex, v_uv).r;
    vec4 source = texture(tex0, v_uv);

    // ====== CIRCLE OF CONFUSION ======
    float coc;  // Circle of confusion radius

    if (tilt_shift < 0.1) {
        // Depth-based DOF
        float dist_from_focal = abs(depth - focal_distance);
        coc = smoothstep(0.0, focal_range, dist_from_focal);

        // Separate fg/bg weighting
        if (depth < focal_distance) {
            coc *= fg_blur;
        } else {
            coc *= bg_blur;
        }
    } else {
        // Tilt-shift mode — spatial gradient
        float angle = tilt_angle * PI;
        vec2 center = v_uv - 0.5;
        float projected = center.x * sin(angle) + center.y * cos(angle);
        coc = smoothstep(0.0, focal_range * 0.3, abs(projected) - focal_distance * 0.3);
        coc *= tilt_shift;
    }

    float radius = coc * blur_amount * 15.0;

    // ====== BOKEH BLUR ======
    vec4 result;
    if (radius < 0.5) {
        result = source;
    } else {
        result = bokeh_blur(v_uv, radius, bokeh_bright);

        // Chromatic fringe at edges of bokeh
        if (chromatic_fringe > 0.0 && radius > 1.0) {
            float fringe = chromatic_fringe * radius * 0.002;
            result.r = bokeh_blur(v_uv + vec2(fringe, 0.0), radius, bokeh_bright).r;
            result.b = bokeh_blur(v_uv - vec2(fringe, 0.0), radius, bokeh_bright).b;
        }
    }

    // ====== VIGNETTE ======
    if (vignette > 0.0) {
        float dist = length(v_uv - 0.5) * 2.0;
        float vig = 1.0 - smoothstep(0.5, 1.4, dist) * vignette * 0.5;
        // Heavier vignette on blurred areas
        vig -= coc * vignette * 0.15;
        result.rgb *= max(vig, 0.0);
    }

    fragColor = mix(source, result, u_mix);
}
"""

METADATA = {
    "name": "Depth Blur",
    "description": "Cinematic bokeh depth-of-field using real depth data.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["blur", "dof", "bokeh", "cinematic"],
    "status": "active",
    "parameters": [
        {"name": "focalDistance", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "focalRange", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "blurAmount", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "fgBlur", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "bgBlur", "type": "float", "min": 0.0, "max": 10.0, "default": 7.0},
        {"name": "bokehBright", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "chromaticFringe", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "tiltShift", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "tiltAngle", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "aperture", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "quality", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "vignette", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthBlurPlugin(EffectPlugin):
    """P3-VD28: Depth Blur effect port matching VJlive-2 parameters."""
    
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
            gl.glShaderSource(fragment, DEPTH_BLUR_FRAGMENT)
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
            logger.warning(f"Failed to initialize GL FBOs inside DepthBlur: {e}")
            self._mock_mode = True

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if input_texture is None or input_texture == 0:
            return 0
            
        self.time += 0.016 # simulate advancing time if not passed
            
        if self._mock_mode:
            context.outputs["video_out"] = input_texture
            return input_texture

        try:
            depth_in = context.inputs.get("depth_in", input_texture) # Fallback to input if missing depth

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
                
                prev_tex = self.textures[f"feedback_{self.ping_pong}"]
                gl.glBindTexture(gl.GL_TEXTURE_2D, prev_tex)
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, current_fbo)
            gl.glViewport(0, 0, w, h)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            
            gl.glUseProgram(self.prog)
            self._bind_uniforms(params, w, h, context)
            
            # Bind textures
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
            
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.textures[f"feedback_{self.ping_pong}"])
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrev"), 1)
            
            gl.glActiveTexture(gl.GL_TEXTURE2)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 2)
            
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

    def _bind_uniforms(self, params, w, h, context):
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), float(self.time))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), params.get("u_mix", 1.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "focal_distance"), self._map_param(params, 'focalDistance', 0.0, 1.0, 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "focal_range"), self._map_param(params, 'focalRange', 0.01, 0.5, 3.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "blur_amount"), self._map_param(params, 'blurAmount', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fg_blur"), self._map_param(params, 'fgBlur', 0.0, 1.5, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "bg_blur"), self._map_param(params, 'bgBlur', 0.0, 1.5, 7.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "bokeh_bright"), self._map_param(params, 'bokehBright', 0.0, 1.0, 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "chromatic_fringe"), self._map_param(params, 'chromaticFringe', 0.0, 1.0, 3.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "tilt_shift"), self._map_param(params, 'tiltShift', 0.0, 1.0, 0.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "tilt_angle"), self._map_param(params, 'tiltAngle', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "aperture"), self._map_param(params, 'aperture', 0.0, 10.0, 0.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "quality"), self._map_param(params, 'quality', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "vignette"), self._map_param(params, 'vignette', 0.0, 1.0, 3.0))

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
                logger.error(f"Error cleaning up FBOs/Textures during DepthBlur unload: {e}")
                
        for k in self.textures:
            self.textures[k] = None
            self.fbos[k] = None

