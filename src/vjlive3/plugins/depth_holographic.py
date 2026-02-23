"""
P3-VD52: Depth Holographic Plugin for VJLive3.
Ported from legacy VJlive-2 DepthHolographicIridescenceEffect.
Single-Pass shader rendering physically-inspired thin-film optical interference 
equations against surface normal approximations calculated from depth gradients.
"""

from typing import Dict, Any, Optional
import numpy as np
import logging

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

# # from .api import EffectPlugin, PluginContext
logger = logging.getLogger(__name__)

METADATA = {
    "name": "DepthHolographic",
    "version": "3.0.0",
    "description": "Physically-inspired thin-film interference and diffraction grating holographic simulation.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "light",
    "tags": ["depth", "holographic", "iridescence", "fresnel", "diffraction", "rainbow"],
    "priority": 1,
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "filmThickness", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "filmDepthScale", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "interferenceOrder", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "fresnelPower", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "fresnelBias", "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "spectralSpread", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "spectralShift", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "gratingDensity", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "gratingAngle", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "gratingOrder", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "iridescenceAmount", "type": "float", "default": 6.0, "min": 0.0, "max": 10.0},
        {"name": "pearlescence", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "hologramNoise", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "colorMode", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "shimmerSpeed", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0}
    ]
}

VERTEX_SHADER_SOURCE = """
#version 330 core
const vec2 quadVertices[4] = vec2[4](
    vec2(-1.0, -1.0),
    vec2( 1.0, -1.0),
    vec2(-1.0,  1.0),
    vec2( 1.0,  1.0)
);

out vec2 uv;

void main() {
    gl_Position = vec4(quadVertices[gl_VertexID], 0.0, 1.0);
    uv = quadVertices[gl_VertexID] * 0.5 + 0.5;
}
"""

FRAGMENT_SHADER_SOURCE = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform float time;
uniform vec2 resolution;
uniform int has_depth;

uniform float film_thickness;        
uniform float film_depth_scale;      
uniform float interference_order;    

uniform float fresnel_power;         
uniform float fresnel_bias;          

uniform float spectral_spread;       
uniform float spectral_shift;        

uniform float grating_density;       
uniform float grating_angle;         
uniform float grating_order;         

uniform float iridescence_amount;    
uniform float pearlescence;          
uniform float hologram_noise;        
uniform float color_mode;            
uniform float shimmer_speed;         

float hash(vec2 p) {
    p = fract(p * vec2(443.897, 441.423));
    p += dot(p, p.yx + 19.19);
    return fract((p.x + p.y) * p.x);
}

vec3 wavelength_to_rgb(float lambda_nm) {
    float t;
    vec3 rgb = vec3(0.0);

    if (lambda_nm >= 380.0 && lambda_nm < 440.0) {
        t = (lambda_nm - 380.0) / (440.0 - 380.0);
        rgb = vec3(-(lambda_nm - 440.0) / (440.0 - 380.0), 0.0, 1.0);
    } else if (lambda_nm >= 440.0 && lambda_nm < 490.0) {
        rgb = vec3(0.0, (lambda_nm - 440.0) / (490.0 - 440.0), 1.0);
    } else if (lambda_nm >= 490.0 && lambda_nm < 510.0) {
        rgb = vec3(0.0, 1.0, -(lambda_nm - 510.0) / (510.0 - 490.0));
    } else if (lambda_nm >= 510.0 && lambda_nm < 580.0) {
        rgb = vec3((lambda_nm - 510.0) / (580.0 - 510.0), 1.0, 0.0);
    } else if (lambda_nm >= 580.0 && lambda_nm < 645.0) {
        rgb = vec3(1.0, -(lambda_nm - 645.0) / (645.0 - 580.0), 0.0);
    } else if (lambda_nm >= 645.0 && lambda_nm <= 780.0) {
        rgb = vec3(1.0, 0.0, 0.0);
    }

    float factor = 1.0;
    if (lambda_nm >= 380.0 && lambda_nm < 420.0)
        factor = 0.3 + 0.7 * (lambda_nm - 380.0) / (420.0 - 380.0);
    else if (lambda_nm >= 700.0 && lambda_nm <= 780.0)
        factor = 0.3 + 0.7 * (780.0 - lambda_nm) / (780.0 - 700.0);

    return rgb * factor;
}

vec3 thin_film_color(float thickness_nm, float cos_theta) {
    float n = 1.5;
    float sin_theta_r = sin(acos(cos_theta)) / n;
    float cos_theta_r = sqrt(1.0 - sin_theta_r * sin_theta_r);
    float opd = 2.0 * n * thickness_nm * cos_theta_r;

    vec3 color = vec3(0.0);
    int orders = int(interference_order * 3.0) + 1;

    for (int i = 0; i < 12; i++) {
        float lambda = 380.0 + float(i) * (400.0 / 12.0) * spectral_spread;
        lambda += spectral_shift * 100.0;
        float phase = opd / lambda * 6.283;
        float intensity = 0.0;
        for (int order = 0; order < 4; order++) {
            if (order >= orders) break;
            float order_phase = phase * float(order + 1);
            intensity += pow(cos(order_phase * 0.5), 2.0) / float(order + 1);
        }
        vec3 spectral_color = wavelength_to_rgb(lambda);
        color += spectral_color * intensity;
    }
    return color / 6.0;  
}

vec2 depth_gradient(vec2 p) {
    if (has_depth == 0) return vec2(0.0);
    float t = 1.5 / resolution.x;
    float dL = texture(depth_tex, p + vec2(-t, 0.0)).r;
    float dR = texture(depth_tex, p + vec2( t, 0.0)).r;
    float dU = texture(depth_tex, p + vec2(0.0,  t)).r;
    float dD = texture(depth_tex, p + vec2(0.0, -t)).r;
    return vec2(dR - dL, dU - dD);
}

void main() {
    float depth = 0.0;
    if (has_depth == 1) depth = texture(depth_tex, uv).r;
    
    vec4 source = texture(tex0, uv);
    vec2 grad = depth_gradient(uv);
    float grad_mag = length(grad);

    float surface_angle = clamp(grad_mag * 20.0, 0.0, 1.0);
    float cos_theta = 1.0 - surface_angle;

    float fresnel = fresnel_bias + (1.0 - fresnel_bias) * pow(1.0 - cos_theta, fresnel_power);
    fresnel = clamp(fresnel, 0.0, 1.0);

    float base_thickness = film_thickness * 400.0 + 100.0;  
    float thickness = base_thickness + depth * film_depth_scale * 300.0;
    thickness += sin(time * shimmer_speed + depth * 8.0) * 20.0;

    vec3 interference_color = thin_film_color(thickness, cos_theta);

    vec3 grating_color = vec3(0.0);
    if (grating_density > 0.0) {
        float grad_angle = atan(grad.y, grad.x);
        float grating_a = grating_angle * 6.283;
        float angle_diff = grad_angle - grating_a;

        float d = 1000.0 / (grating_density * 500.0 + 100.0); 
        int m = int(grating_order * 3.0) + 1;  

        for (int i = 0; i < 8; i++) {
            float lambda_um = 0.38 + float(i) * 0.05;  
            float sin_theta = float(m) * lambda_um / d;
            if (abs(sin_theta) < 1.0) {
                float diff_angle = asin(sin_theta);
                float match = exp(-pow(angle_diff - diff_angle, 2.0) * 50.0);
                match += exp(-pow(angle_diff + diff_angle, 2.0) * 50.0);
                grating_color += wavelength_to_rgb(lambda_um * 1000.0) * match;
            }
        }
        grating_color *= grating_density * surface_angle * 0.5;
    }

    vec3 holo_color = interference_color + grating_color;
    holo_color *= fresnel;

    if (pearlescence > 0.0) {
        float luminance = dot(source.rgb, vec3(0.299, 0.587, 0.114));
        float pearl_mask = smoothstep(0.4, 0.8, luminance);
        float pearl_hue = fract(surface_angle * 0.5 + depth * 0.3 + time * shimmer_speed * 0.05);
        vec3 pearl = wavelength_to_rgb(420.0 + pearl_hue * 200.0);
        holo_color += pearl * pearl_mask * pearlescence * 0.3;
    }

    if (hologram_noise > 0.0) {
        float noise = hash(uv * resolution * 2.0 + vec2(time * 30.0));
        float sparkle = step(0.95 - hologram_noise * 0.1, noise);
        vec3 sparkle_color = thin_film_color(thickness + noise * 100.0, cos_theta);
        holo_color += sparkle_color * sparkle * hologram_noise * 0.5;

        float grain = (hash(uv * resolution + vec2(time)) - 0.5) * hologram_noise * 0.1;
        holo_color += vec3(grain);
    }

    vec3 final_rgb;
    if (color_mode < 3.3) {
        final_rgb = source.rgb + holo_color * iridescence_amount;
    } else if (color_mode < 6.6) {
        vec3 overlay;
        for (int i = 0; i < 3; i++) {
            float base = source.rgb[i];
            float blend = holo_color[i] * iridescence_amount;
            overlay[i] = base < 0.5 ? 2.0 * base * blend : 1.0 - 2.0 * (1.0 - base) * (1.0 - blend);
        }
        final_rgb = mix(source.rgb, overlay, iridescence_amount);
    } else {
        final_rgb = mix(source.rgb, holo_color, iridescence_amount);
    }

    fragColor = vec4(clamp(final_rgb, 0.0, 1.5), 1.0);
}
"""

class DepthHolographicPlugin(object):
    """Depth Holographic Iridescence single-pass thin-film physics simulation."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.program = 0
        self.empty_vao = 0
        
        self.fbo = 0
        self.texture = 0
        self._width = 0
        self._height = 0
        self._initialized = False

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def _compile_shader(self, vs_src: str, fs_src: str) -> int:
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, vs_src)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(gl.glGetShaderInfoLog(vs))

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, fs_src)
        gl.glCompileShader(fs)
        if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(gl.glGetShaderInfoLog(fs))

        prog = gl.glCreateProgram()
        gl.glAttachShader(prog, vs)
        gl.glAttachShader(prog, fs)
        gl.glLinkProgram(prog)
        if not gl.glGetProgramiv(prog, gl.GL_LINK_STATUS):
            raise RuntimeError(gl.glGetProgramInfoLog(prog))
            
        gl.glDeleteShader(vs)
        gl.glDeleteShader(fs)
        return prog

    def initialize(self, context) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            logger.warning("Mock mode engaged. Skipping GL initialization.")
            self._initialized = True
            return True

        try:
            self.program = self._compile_shader(VERTEX_SHADER_SOURCE, FRAGMENT_SHADER_SOURCE)
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to config OpenGL in depth_holographic: {e}")
            self._mock_mode = True
            return False

    def _free_fbo(self):
        try:
            if self.texture != 0: gl.glDeleteTextures(1, [self.texture])
            if self.fbo != 0: gl.glDeleteFramebuffers(1, [self.fbo])
        except Exception:
            pass
        self.fbo = 0
        self.texture = 0

    def _allocate_buffers(self, w: int, h: int):
        self._free_fbo()
        self._width = w
        self._height = h
        self.fbo = gl.glGenFramebuffers(1)
        self.texture = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.texture, 0)
        
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _map_norm(self, val: float, max_v: float = 1.0, min_v: float = 0.0) -> float:
        return min_v + (max(0.0, min(10.0, float(val))) / 10.0) * (max_v - min_v)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0:
            return 0
             
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        if not self._initialized:
            self.initialize(context)
            
        w = getattr(context, 'width', 1920)
        h = getattr(context, 'height', 1080)
        
        if w != self._width or h != self._height:
            self._allocate_buffers(w, h)
            
        inputs = getattr(context, "inputs", {})
        depth_in = inputs.get("depth_in", 0)
        time_val = getattr(context, 'time', 0.0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.program)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "depth_tex"), 1)

        gl.glUniform1i(gl.glGetUniformLocation(self.program, "has_depth"), 1 if depth_in > 0 else 0)
        gl.glUniform2f(gl.glGetUniformLocation(self.program, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "time"), float(time_val))

        gl.glUniform1f(gl.glGetUniformLocation(self.program, "film_thickness"), self._map_norm(params.get("filmThickness", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "film_depth_scale"), self._map_norm(params.get("filmDepthScale", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "interference_order"), self._map_norm(params.get("interferenceOrder", 4.0)))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "fresnel_power"), self._map_norm(params.get("fresnelPower", 5.0), 8.0, 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "fresnel_bias"), self._map_norm(params.get("fresnelBias", 2.0), 0.5, 0.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "spectral_spread"), self._map_norm(params.get("spectralSpread", 5.0), 2.0, 0.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "spectral_shift"), self._map_norm(params.get("spectralShift", 0.0)))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "grating_density"), self._map_norm(params.get("gratingDensity", 4.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "grating_angle"), self._map_norm(params.get("gratingAngle", 3.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "grating_order"), self._map_norm(params.get("gratingOrder", 3.0)))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "iridescence_amount"), self._map_norm(params.get("iridescenceAmount", 6.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "pearlescence"), self._map_norm(params.get("pearlescence", 4.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "hologram_noise"), self._map_norm(params.get("hologramNoise", 3.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "color_mode"), self._map_norm(params.get("colorMode", 0.0), 10.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "shimmer_speed"), self._map_norm(params.get("shimmerSpeed", 4.0), 2.0))

        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.texture
            
        return self.texture

    def cleanup(self) -> None:
        try:
            self._free_fbo()
            if hasattr(gl, 'glDeleteProgram') and self.program != 0:
                gl.glDeleteProgram(self.program)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao != 0:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup Error in DepthHolographic: {e}")
        finally:
            self.program = 0
            self.empty_vao = 0

