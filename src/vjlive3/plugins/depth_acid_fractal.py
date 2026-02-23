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
uniform int fractal_type;            // 0 = Julia, 1 = Mandelbrot
uniform vec2 offset;                 // Fractal coordinate offset
uniform float fractal_intensity;     // How much fractal replaces the image
uniform float fractal_zoom;          // Fractal zoom level (0.01 - 10.0)
uniform float fractal_iterations;    // Iteration count (detail) (1 - 1000)
uniform float color_shift;           // Hue rotation based on depth (0-1)

// Datamosh & Pixelation
uniform float datamosh_strength;     // Temporal distortion intensity (0.0 - 1.0)
uniform float pixelation;            // Block size for pixelation effect (1-64)

// Prism
uniform float prism_split;           // Prismatic RGB separation amount
uniform float prism_rotate;          // Prism rotation angle
uniform float prism_faces;           // Number of prism faces / copies

// Film Alchemy
uniform float solarize;              // Sabattier solarization intensity
uniform float cross_process;         // Cross-processing color shift
uniform float film_burn;             // Neon light leak / film burn
uniform float posterize;             // Posterization band count

// Motion & Intensity
uniform float zoom_blur;             // Radial zoom blur (depth-controlled)
uniform float bass_throb;            // Bass-driven image pulse
uniform float neon_boost;            // Push everything to neon saturation
uniform float feedback;              // Temporal feedback blend

// --- Utility ---
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

// Mandelbrot/Julia set fractal
vec3 generate_fractal(vec2 p, float depth_val) {
    vec2 z;
    vec2 c;
    
    // Base coordinate space
    vec2 mapped = (p - 0.5) * 3.0 / max(0.01, fractal_zoom) + offset;
    
    if (fractal_type == 0) {
        // Julia: c is dynamic, z is coordinate
        z = mapped;
        float angle = time * 0.3 + depth_val * 6.283;
        float radius = 0.7885 + depth_val * 0.1;
        c = vec2(cos(angle), sin(angle)) * radius;
    } else {
        // Mandelbrot: c is coordinate, z starts at 0
        z = vec2(0.0);
        c = mapped;
    }

    int max_iter = max(4, int(fractal_iterations));
    float iter = 0.0;

    for (int i = 0; i < 1000; i++) {
        if (i >= max_iter) break;
        if (dot(z, z) > 4.0) break;
        z = vec2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
        iter += 1.0;
    }

    // Color the fractal
    float t = iter / float(max_iter);
    vec3 col;
    float hue_base = color_shift + depth_val * 0.5;
    
    col.r = 0.5 + 0.5 * sin(t * 6.283 * 3.0 + time * 0.5 + (hue_base * 6.28));
    col.g = 0.5 + 0.5 * sin(t * 6.283 * 3.0 + 2.094 + time * 0.7 + (hue_base * 6.28));
    col.b = 0.5 + 0.5 * sin(t * 6.283 * 3.0 + 4.189 + time * 0.3 + (hue_base * 6.28));

    col = pow(col, vec3(0.6)); // Make it neon
    
    if (dot(z, z) <= 4.0) {
        col = vec3(0.05, 0.0, 0.15); // Interior
    }

    return col;
}

void main() {
    float depth = texture(depth_tex, v_uv).r;
    vec2 coord = v_uv;

    // Pixelation Stage
    if (pixelation > 1.0) {
        float px = floor(pixelation);
        coord = floor(v_uv * resolution / px) * px / resolution;
    }

    // Bass pulse
    float bass = pow(abs(sin(time * 2.5)), 4.0);

    // BASS THROB
    if (bass_throb > 0.0) {
        vec2 center = coord - 0.5;
        float zoom = 1.0 - bass_throb * 0.04 * bass;
        coord = center * zoom + 0.5;
    }

    // DATAMOSH STAGE
    vec4 previous = texture(texPrev, coord);
    vec2 mosh_coord = coord;
    if (datamosh_strength > 0.0) {
        vec2 flow = texture(tex0, coord).rg - previous.rg;
        if (length(flow) > (1.0 - datamosh_strength) * 0.2) {
            mosh_coord -= flow * datamosh_strength * 0.1;
        }
    }
    
    // PRISM SPLITTING
    vec4 result;
    if (prism_split > 0.0) {
        float angle = prism_rotate * 6.283 + time * 0.3;
        float spread = prism_split * 0.03;

        vec2 r_offset = vec2(cos(angle), sin(angle)) * spread;
        vec2 g_offset = vec2(cos(angle + 2.094), sin(angle + 2.094)) * spread * 0.6;
        vec2 b_offset = vec2(cos(angle + 4.189), sin(angle + 4.189)) * spread;

        float depth_mod = 1.0 + (1.0 - depth) * 1.5;
        r_offset *= depth_mod;
        g_offset *= depth_mod;
        b_offset *= depth_mod;

        result.r = texture(tex0, mosh_coord + r_offset).r;
        result.g = texture(tex0, mosh_coord + g_offset).g;
        result.b = texture(tex0, mosh_coord + b_offset).b;

        if (prism_faces > 0.0) {
            int faces = int(prism_faces * 4.0) + 1;
            for (int i = 1; i < 5; i++) {
                if (i >= faces) break;
                float face_angle = float(i) * 6.283 / float(faces) + time * 0.1;
                vec2 face_offset = vec2(cos(face_angle), sin(face_angle)) * spread * 2.0 * depth_mod;
                result.rgb += texture(tex0, mosh_coord + face_offset).rgb * 0.15;
            }
        }
        result.a = 1.0;
    } else {
        result = texture(tex0, mosh_coord);
    }
    
    // DATAMOSH FEEDBACK BLEND
    if (datamosh_strength > 0.0) {
        result = mix(result, texture(texPrev, mosh_coord), datamosh_strength * 0.8 * depth);
    }

    // ZOOM BLUR
    if (zoom_blur > 0.0) {
        float blur_amount = zoom_blur * depth * 0.015;
        vec2 center = coord - 0.5;
        vec4 blurred = result;
        int samples = 8;
        for (int i = 1; i < 8; i++) {
            float t = float(i) / float(samples);
            vec2 sample_uv = coord - center * blur_amount * t;
            blurred += texture(tex0, sample_uv);
        }
        blurred /= float(samples);
        result = mix(result, blurred, depth * zoom_blur);
    }

    // FRACTAL OVERLAY
    if (fractal_intensity > 0.0) {
        vec3 fractal = generate_fractal(coord, depth);
        float edge = depth_edge(coord) * 4.0;
        float fractal_mask = mix(0.2, 1.0, smoothstep(0.1, 0.5, edge));

        vec3 screened = 1.0 - (1.0 - result.rgb) * (1.0 - fractal * fractal_mask);
        result.rgb = mix(result.rgb, screened, fractal_intensity * 0.7);
        result.rgb += fractal * edge * fractal_intensity * 0.3;
    }

    // SOLARIZATION
    if (solarize > 0.0) {
        vec3 solar = result.rgb;
        for (int ch = 0; ch < 3; ch++) {
            float v = result.rgb[ch];
            float curves = solarize * 2.0;
            solar[ch] = abs(sin(v * 3.14159 * curves));
        }
        float depth_band = 0.5 + 0.5 * sin(depth * 6.283 * 2.0 + time * 0.5);
        result.rgb = mix(result.rgb, solar, depth_band * solarize * 0.6);
    }

    // CROSS-PROCESSING
    if (cross_process > 0.0) {
        vec3 xpro = result.rgb;
        float band = fract(depth * 3.0 + time * 0.1);

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

    // FILM BURN
    if (film_burn > 0.0) {
        float edge = depth_edge(coord);
        float burn_noise = hash(floor(coord * 8.0) + vec2(floor(time * 0.5)));
        float burn_spot = smoothstep(0.6, 0.9, burn_noise) * film_burn;
        burn_spot += edge * 4.0 * film_burn * 0.3;
        burn_spot *= 0.7 + 0.3 * bass;
        float burn_hue = fract(time * 0.15 + depth * 0.5);
        vec3 burn_color = hsv2rgb(vec3(burn_hue, 0.8, 1.0));
        result.rgb += burn_color * burn_spot * 0.8;
        
        float streak = exp(-abs(coord.y - 0.5 - sin(time * 0.3) * 0.2) * 20.0);
        streak *= burn_spot * 0.3;
        result.rgb += burn_color * streak;
    }

    // POSTERIZATION
    if (posterize > 0.0) {
        float bands = mix(16.0, 3.0, depth) / (1.0 + posterize);
        bands = max(2.0, bands);
        vec3 poster = floor(result.rgb * bands + 0.5) / bands;
        result.rgb = mix(result.rgb, poster, posterize * 0.7);
    }

    // NEON BOOST
    if (neon_boost > 0.0) {
        float luma = dot(result.rgb, vec3(0.299, 0.587, 0.114));
        vec3 chroma = result.rgb - luma;
        result.rgb = luma + chroma * (1.0 + neon_boost * 4.0);
        result.r *= 1.0 + neon_boost * 0.1;
        result.rgb = clamp(result.rgb, 0.0, 1.5);
    }

    // FEEDBACK
    if (feedback > 0.0) {
        float fb = feedback * (0.3 + depth * 0.5);
        result = mix(result, previous, clamp(fb, 0.0, 0.9));
    }

    fragColor = mix(texture(tex0, v_uv), result, u_mix);
}
"""

METADATA = {
    "name": "DepthAcidFractalDatamoshEffect",
    "version": "3.0.0",
    "description": "Acid fractal datamosh effect with depth buffer integration.",
    "author": "VJLive3 Team",
    "category": "datamosh",
    "tags": ["depth", "datamosh", "fractal", "acid", "glitch"],
    "parameters": [
        # New P3-P3-VD26 specification parameters:
        {"name": "fractal_type", "type": "int", "min": 0, "max": 1, "default": 0},  # 0=Julia, 1=Mandelbrot
        {"name": "iterations", "type": "float", "min": 1.0, "max": 1000.0, "default": 64.0},
        {"name": "zoom", "type": "float", "min": 0.01, "max": 10.0, "default": 1.0},
        {"name": "offset_x", "type": "float", "min": -5.0, "max": 5.0, "default": 0.0},
        {"name": "offset_y", "type": "float", "min": -5.0, "max": 5.0, "default": 0.0},
        {"name": "color_shift", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "datamosh_strength", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "pixelation", "type": "float", "min": 1.0, "max": 64.0, "default": 1.0},
        
        # Legacy preserved parameters for soul retention:
        {"name": "fractal_intensity", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "prism_split", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "prism_rotate", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "prism_faces", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "solarize", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "cross_process", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "film_burn", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "posterize", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "zoom_blur", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "bass_throb", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "neon_boost", "type": "float", "min": 0.0, "max": 10.0, "default": 6.0},
        {"name": "feedback", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0},
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthAcidFractalDatamoshPlugin(EffectPlugin):
    """
    Depth Acid Fractal Datamosh — neon fractal mayhem.
    Julia and Mandelbrot fractals combined with recursive datamoshing,
    Sabattier solarization, prismatic RGB splits, and bass reactivity.
    """
    
    def __init__(self) -> None:
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.ping_pong = 0
        
        self.textures: Dict[str, Optional[int]] = {
            "feedback_0": None, "feedback_1": None
        }
        self.fbos: Dict[str, Optional[int]] = {
            "feedback_0": None, "feedback_1": None
        }
        self.time = 0.0

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
            if isinstance(tex_ids, int): tex_ids = [tex_ids]
            if isinstance(fbo_ids, int): fbo_ids = [fbo_ids]
                
            for i, key in enumerate(["feedback_0", "feedback_1"]):
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
            logger.warning(f"Failed to initialize GL resources inside task: {e}")
            self._mock_mode = True

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if input_texture is None or input_texture == 0:
            return 0
            
        self.time += 1.0 / 60.0
            
        if self._mock_mode:
            context.outputs["video_out"] = input_texture
            return input_texture

        try:
            depth_texture = context.inputs.get("depth_in", 0)
            
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
            
            self._bind_uniforms(params, w, h)
            
            # Bind textures
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
            
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.textures[f"feedback_{self.ping_pong}"])
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrev"), 1)
            
            if depth_texture:
                gl.glActiveTexture(gl.GL_TEXTURE2)
                gl.glBindTexture(gl.GL_TEXTURE_2D, depth_texture)
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
            context.outputs["video_out"] = input_texture
            return input_texture

    def _bind_uniforms(self, params, w, h):
        def map_p(key, max_val=1.0):
            # Map legacy 0-10 scale down to 0-1.0 ranges for uniform delivery
            v = params.get(key, METADATA["parameters"][[x["name"] for x in METADATA["parameters"]].index(key)]["default"])
            return (v / 10.0) * max_val

        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), self.time)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), params.get("u_mix", 1.0))
        
        # New spec params
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "fractal_type"), int(params.get("fractal_type", 0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fractal_zoom"), params.get("zoom", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fractal_iterations"), params.get("iterations", 64.0))
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "offset"), params.get("offset_x", 0.0), params.get("offset_y", 0.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "color_shift"), params.get("color_shift", 0.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "datamosh_strength"), params.get("datamosh_strength", 0.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "pixelation"), params.get("pixelation", 1.0))
        
        # Legacy mapped params
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fractal_intensity"), map_p("fractal_intensity", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "prism_split"), map_p("prism_split", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "prism_rotate"), map_p("prism_rotate", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "prism_faces"), map_p("prism_faces", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "solarize"), map_p("solarize", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "cross_process"), map_p("cross_process", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "film_burn"), map_p("film_burn", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "posterize"), map_p("posterize", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "zoom_blur"), map_p("zoom_blur", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "bass_throb"), map_p("bass_throb", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "neon_boost"), map_p("neon_boost", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "feedback"), map_p("feedback", 1.0))

    def cleanup(self) -> None:
        if not self._mock_mode:
            try:
                texs = [t for t in self.textures.values() if t is not None]
                if texs: gl.glDeleteTextures(len(texs), texs)
                fbos = [f for f in self.fbos.values() if f is not None]
                if fbos: gl.glDeleteFramebuffers(len(fbos), fbos)
                if self.prog: gl.glDeleteProgram(self.prog)
                if hasattr(self, 'vao') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
                if hasattr(self, 'vbo') and self.vbo: gl.glDeleteBuffers(1, [self.vbo])
            except Exception:
                pass
                
        for k in self.textures:
            self.textures[k] = None
            self.fbos[k] = None
