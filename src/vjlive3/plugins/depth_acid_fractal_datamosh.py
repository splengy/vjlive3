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

DEPTH_ACID_FRACTAL_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Fractals
uniform float fractal_intensity;
uniform float fractal_zoom;
uniform float fractal_iterations;
uniform float fractal_morph;

// Prism
uniform float prism_split;
uniform float prism_rotate;
uniform float prism_faces;

// Film Alchemy
uniform float solarize;
uniform float cross_process;
uniform float film_burn;
uniform float posterize;

// Motion
uniform float zoom_blur;
uniform float bass_throb;

// Intensity
uniform float neon_boost;
uniform float feedback;

float hash(vec2 p) {
    p = fract(p * vec2(443.897, 441.423));
    p += dot(p, p.yx + 19.19);
    return fract((p.x + p.y) * p.x);
}

vec3 hsv2rgb(vec3 c) {
    vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0/3.0, 1.0/3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

float depth_edge(vec2 p) {
    float t = 2.0 / resolution.x;
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

vec3 julia_fractal(vec2 p, float depth_val, float adjusted_time) {
    vec2 z = (p - 0.5) * 3.0 / max(0.1, fractal_zoom);
    float angle = adjusted_time * fractal_morph * 0.3 + depth_val * 6.283;
    float radius = 0.7885 + depth_val * 0.1;
    vec2 c = vec2(cos(angle), sin(angle)) * radius;

    int max_iter = int(fractal_iterations * 20.0) + 4;
    float iter = 0.0;
    
    // SAFETY RAIL 1: Protect 60FPS by hard-capping max loop iteration regardless of uniform
    max_iter = min(max_iter, 16);

    for (int i = 0; i < 16; i++) {
        if (i >= max_iter) break;
        if (dot(z, z) > 4.0) break;
        z = vec2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
        iter += 1.0;
    }

    float t_val = iter / float(max_iter);
    vec3 col;
    col.r = 0.5 + 0.5 * sin(t_val * 6.283 * 3.0 + adjusted_time * 0.5);
    col.g = 0.5 + 0.5 * sin(t_val * 6.283 * 3.0 + 2.094 + adjusted_time * 0.7);
    col.b = 0.5 + 0.5 * sin(t_val * 6.283 * 3.0 + 4.189 + adjusted_time * 0.3);

    col = pow(col, vec3(0.6));

    if (dot(z, z) <= 4.0) {
        col = vec3(0.05, 0.0, 0.15);
    }
    return col;
}

void main() {
    float depth = texture(depth_tex, v_uv).r;
    vec2 coord = v_uv;

    // We can't use Python's time easily in the shader without passing it down correctly per-frame.
    // However, time comes via uniform time.
    float adjusted_time = time;
    
    float bass = pow(abs(sin(adjusted_time * 2.5)), 4.0);

    // ====== STAGE 1: BASS THROB ======
    if (bass_throb > 0.0) {
        vec2 center = coord - 0.5;
        float zoom = 1.0 - bass_throb * 0.04 * bass;
        coord = center * zoom + 0.5;
    }

    // ====== STAGE 2: PRISM SPLITTING ======
    vec4 result;
    if (prism_split > 0.0) {
        float angle = prism_rotate * 6.283 + adjusted_time * 0.3;
        float spread = prism_split * 0.03;

        vec2 r_offset = vec2(cos(angle), sin(angle)) * spread;
        vec2 g_offset = vec2(cos(angle + 2.094), sin(angle + 2.094)) * spread * 0.6;
        vec2 b_offset = vec2(cos(angle + 4.189), sin(angle + 4.189)) * spread;

        float depth_mod = 1.0 + (1.0 - depth) * 1.5;
        r_offset *= depth_mod;
        g_offset *= depth_mod;
        b_offset *= depth_mod;

        result.r = texture(tex0, coord + r_offset).r;
        result.g = texture(tex0, coord + g_offset).g;
        result.b = texture(tex0, coord + b_offset).b;

        if (prism_faces > 0.0) {
            int faces = int(prism_faces * 4.0) + 1;
            for (int i = 1; i < 5; i++) {
                if (i >= faces) break;
                float face_angle = float(i) * 6.283 / float(faces) + adjusted_time * 0.1;
                vec2 face_offset = vec2(cos(face_angle), sin(face_angle)) * spread * 2.0 * depth_mod;
                vec4 ghost = texture(tex0, coord + face_offset);
                result.rgb += ghost.rgb * 0.15;
            }
        }
        result.a = 1.0;
    } else {
        result = texture(tex0, coord);
    }

    // ====== STAGE 3: ZOOM BLUR ======
    if (zoom_blur > 0.0) {
        float blur_amount = zoom_blur * depth * 0.015;
        vec2 center = coord - 0.5;

        vec4 blurred = result;
        int samples = 8;
        for (int i = 1; i < 8; i++) {
            float t_val = float(i) / float(samples);
            vec2 sample_uv = coord - center * blur_amount * t_val;
            blurred += texture(tex0, sample_uv);
        }
        blurred /= float(samples);
        result = mix(result, blurred, depth * zoom_blur);
    }

    // ====== STAGE 4: FRACTAL OVERLAY ======
    if (fractal_intensity > 0.0) {
        vec3 fractal = julia_fractal(coord, depth, adjusted_time);
        float edge = depth_edge(coord) * 4.0;
        float fractal_mask = mix(0.2, 1.0, smoothstep(0.1, 0.5, edge));

        vec3 screened = 1.0 - (1.0 - result.rgb) * (1.0 - fractal * fractal_mask);
        result.rgb = mix(result.rgb, screened, fractal_intensity * 0.7);
        result.rgb += fractal * edge * fractal_intensity * 0.3;
    }

    // ====== STAGE 5: SOLARIZATION ======
    if (solarize > 0.0) {
        vec3 solar = result.rgb;
        for (int ch = 0; ch < 3; ch++) {
            float v = result.rgb[ch];
            float curves = solarize * 2.0;
            solar[ch] = abs(sin(v * 3.14159 * curves));
        }

        float depth_band = 0.5 + 0.5 * sin(depth * 6.283 * 2.0 + adjusted_time * 0.5);
        float solar_mask = depth_band * solarize;
        result.rgb = mix(result.rgb, solar, solar_mask * 0.6);
    }

    // ====== STAGE 6: CROSS-PROCESSING ======
    if (cross_process > 0.0) {
        vec3 xpro = result.rgb;
        float band = fract(depth * 3.0 + adjusted_time * 0.1);

        if (band < 0.33) {
            xpro.r = pow(xpro.r, 0.8);
            xpro.g = pow(xpro.g, 0.6) * 1.2;
            xpro.b = pow(xpro.b, 1.5) * 0.7;
        } else if (band < 0.66) {
            xpro.r = pow(xpro.r, 1.3) * 0.9;
            xpro.g = pow(xpro.g, 0.7) * 1.1;
            xpro.b = pow(xpro.b, 0.6) * 1.3;
        } else {
            float ir = dot(xpro, vec3(0.1, 0.9, 0.0));
            xpro = vec3(xpro.r * 0.5 + ir * 0.5, ir * 0.3, xpro.b * 1.4);
        }

        result.rgb = mix(result.rgb, clamp(xpro, 0.0, 1.0), cross_process);
    }

    // ====== STAGE 7: FILM BURN ======
    if (film_burn > 0.0) {
        float edge = depth_edge(coord);
        float burn_noise = hash(floor(coord * 8.0) + vec2(floor(adjusted_time * 0.5)));
        float burn_spot = smoothstep(0.6, 0.9, burn_noise) * film_burn;

        burn_spot += edge * 4.0 * film_burn * 0.3;
        burn_spot *= 0.7 + 0.3 * bass;

        float burn_hue = fract(adjusted_time * 0.15 + depth * 0.5);
        vec3 burn_color = hsv2rgb(vec3(burn_hue, 0.8, 1.0));

        result.rgb += burn_color * burn_spot * 0.8;

        float streak = exp(-abs(coord.y - 0.5 - sin(adjusted_time * 0.3) * 0.2) * 20.0);
        streak *= burn_spot * 0.3;
        result.rgb += burn_color * streak;
    }

    // ====== STAGE 8: POSTERIZATION ======
    if (posterize > 0.0) {
        float bands = mix(16.0, 3.0, depth) / (1.0 + posterize);
        bands = max(2.0, bands);

        vec3 poster = floor(result.rgb * bands + 0.5) / bands;
        result.rgb = mix(result.rgb, poster, posterize * 0.7);
    }

    // ====== STAGE 9: NEON BOOST ======
    if (neon_boost > 0.0) {
        float luma = dot(result.rgb, vec3(0.299, 0.587, 0.114));
        vec3 chroma = result.rgb - luma;
        result.rgb = luma + chroma * (1.0 + neon_boost * 4.0);
        result.r *= 1.0 + neon_boost * 0.1;
        result.rgb = clamp(result.rgb, 0.0, 1.5);
    }

    // ====== STAGE 10: FEEDBACK ======
    vec4 previous = texture(texPrev, coord);
    if (feedback > 0.0) {
        float fb = feedback * (0.3 + depth * 0.5);
        result = mix(result, previous, clamp(fb, 0.0, 0.9));
    }

    fragColor = mix(texture(tex0, v_uv), result, u_mix);
}
"""

METADATA = {
    "name": "Depth Acid Fractal Datamosh",
    "description": "Neon fractal mayhem! Julia sets meet Sabattier solarization on depth contours.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["fractal", "acid", "neon", "solarize", "datamosh"],
    "status": "active",
    "parameters": [
        {"name": "fractalIntensity", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "fractalZoom", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "fractalIterations", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "fractalMorph", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "prismSplit", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "prismRotate", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "prismFaces", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "solarize", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "crossProcess", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "filmBurn", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "posterize", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "zoomBlur", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "bassThrob", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "neonBoost", "type": "float", "min": 0.0, "max": 10.0, "default": 6.0},
        {"name": "feedback", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthAcidFractalDatamoshPlugin(EffectPlugin):
    """P3-VD26: Depth Acid Fractal effect port mapping 1:1 visually matching parameters mapped to shaders."""
    
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
            gl.glShaderSource(fragment, DEPTH_ACID_FRACTAL_FRAGMENT)
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
            logger.warning(f"Failed to initialize GL FBOs inside DepthAcidFractal: {e}")
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
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fractal_intensity"), self._map_param(params, 'fractalIntensity', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fractal_zoom"), self._map_param(params, 'fractalZoom', 0.5, 4.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fractal_iterations"), self._map_param(params, 'fractalIterations', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fractal_morph"), self._map_param(params, 'fractalMorph', 0.0, 1.0, 4.0))

        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "prism_split"), self._map_param(params, 'prismSplit', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "prism_rotate"), self._map_param(params, 'prismRotate', 0.0, 1.0, 3.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "prism_faces"), self._map_param(params, 'prismFaces', 0.0, 1.0, 3.0))

        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "solarize"), self._map_param(params, 'solarize', 0.0, 1.0, 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "cross_process"), self._map_param(params, 'crossProcess', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "film_burn"), self._map_param(params, 'filmBurn', 0.0, 1.0, 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "posterize"), self._map_param(params, 'posterize', 0.0, 1.0, 3.0))

        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "zoom_blur"), self._map_param(params, 'zoomBlur', 0.0, 1.0, 3.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "bass_throb"), self._map_param(params, 'bassThrob', 0.0, 1.0, 5.0))

        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "neon_boost"), self._map_param(params, 'neonBoost', 0.0, 1.0, 6.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "feedback"), self._map_param(params, 'feedback', 0.0, 1.0, 4.0))


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
                logger.error(f"Error cleaning up FBOs/Textures during DepthAcidFractal unload: {e}")
                
        for k in self.textures:
            self.textures[k] = None
            self.fbos[k] = None

