"""
P3-VD53: Depth Liquid Refraction Plugin for VJLive3.
Ported from legacy VJlive-2 DepthLiquidRefractionEffect.
Single-Pass shader rendering depth-driven liquid displacements creating 
refractive caustics mapped against 8 mathematical displacement limits.
"""

from typing import Dict, Any, Optional
import numpy as np
import logging

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from .api import EffectPlugin, PluginContext
logger = logging.getLogger(__name__)

METADATA = {
    "name": "DepthLiquidRefraction",
    "version": "3.0.0",
    "description": "Depth-driven glass and liquid distortion simulating refractive caustics.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "distortion",
    "tags": ["depth", "liquid", "refraction", "glass", "caustics", "displacement"],
    "priority": 1,
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "refractionStrength", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "chromaticSpread", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "rippleSpeed", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "rippleScale", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "edgeGlow", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "depthBlur", "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "frostedGlass", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "invertDepth", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0}
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
uniform sampler2D u_depth_tex;    
uniform float time;
uniform vec2 resolution;
uniform int has_depth;

uniform float u_refraction;       
uniform float u_chromatic;        
uniform float u_ripple_speed;     
uniform float u_ripple_scale;     
uniform float u_edge_glow;        
uniform float u_depth_blur;       
uniform float u_frost;            
uniform float u_invert;           

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    vec2 shift = vec2(100.0);
    for (int i = 0; i < 4; i++) {
        v += a * noise(p);
        p = p * 2.0 + shift;
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 pixel = 1.0 / resolution;

    float d_c = 0.0, d_l = 0.0, d_r = 0.0, d_u = 0.0, d_d = 0.0, d_tl = 0.0, d_tr = 0.0, d_bl = 0.0, d_br = 0.0;
    
    if (has_depth == 1) {
        d_c  = texture(u_depth_tex, uv).r;
        d_l  = texture(u_depth_tex, uv + vec2(-pixel.x, 0.0)).r;
        d_r  = texture(u_depth_tex, uv + vec2( pixel.x, 0.0)).r;
        d_u  = texture(u_depth_tex, uv + vec2(0.0,  pixel.y)).r;
        d_d  = texture(u_depth_tex, uv + vec2(0.0, -pixel.y)).r;
        d_tl = texture(u_depth_tex, uv + vec2(-pixel.x,  pixel.y)).r;
        d_tr = texture(u_depth_tex, uv + vec2( pixel.x,  pixel.y)).r;
        d_bl = texture(u_depth_tex, uv + vec2(-pixel.x, -pixel.y)).r;
        d_br = texture(u_depth_tex, uv + vec2( pixel.x, -pixel.y)).r;
    }

    float gx = (-d_tl - 2.0*d_l - d_bl + d_tr + 2.0*d_r + d_br);
    float gy = (-d_tl - 2.0*d_u - d_tr + d_bl + 2.0*d_d + d_br);
    vec2 depth_gradient = vec2(gx, gy);
    float edge_strength = length(depth_gradient);

    float depth = mix(d_c, 1.0 - d_c, u_invert);

    float ripple_time = time * u_ripple_speed * 2.0;
    vec2 ripple_uv = uv * u_ripple_scale * 10.0;
    float ripple_x = fbm(ripple_uv + vec2(ripple_time, 0.0));
    float ripple_y = fbm(ripple_uv + vec2(0.0, ripple_time * 0.7));
    vec2 ripple_offset = (vec2(ripple_x, ripple_y) - 0.5) * 2.0;

    vec2 frost_offset = vec2(0.0);
    if (u_frost > 0.01) {
        float frost_noise = fbm(uv * 50.0 + time * 0.5);
        frost_offset = vec2(frost_noise - 0.5) * u_frost * 0.02;
    }

    float refract_amount = u_refraction * 0.05;
    vec2 displacement = depth_gradient * refract_amount
                      + ripple_offset * refract_amount * depth * 0.3
                      + frost_offset;

    displacement *= (1.0 - depth + 0.2);

    float chroma = u_chromatic * 0.5;
    vec2 uv_r = uv + displacement * (1.0 + chroma);
    vec2 uv_g = uv + displacement;
    vec2 uv_b = uv + displacement * (1.0 - chroma);

    float blur_radius = u_depth_blur * depth * 3.0;
    vec3 color;
    if (blur_radius > 0.5) {
        vec2 blur_step = pixel * blur_radius;
        float r = 0.0, g = 0.0, b = 0.0;
        for (float dx = -2.0; dx <= 2.0; dx += 1.0) {
            for (float dy = -2.0; dy <= 2.0; dy += 1.0) {
                vec2 offset = vec2(dx, dy) * blur_step * 0.5;
                r += texture(tex0, clamp(uv_r + offset, 0.001, 0.999)).r;
                g += texture(tex0, clamp(uv_g + offset, 0.001, 0.999)).g;
                b += texture(tex0, clamp(uv_b + offset, 0.001, 0.999)).b;
            }
        }
        color = vec3(r, g, b) / 25.0;
    } else {
        color.r = texture(tex0, clamp(uv_r, 0.001, 0.999)).r;
        color.g = texture(tex0, clamp(uv_g, 0.001, 0.999)).g;
        color.b = texture(tex0, clamp(uv_b, 0.001, 0.999)).b;
    }

    float caustic = edge_strength * u_edge_glow * 5.0;
    vec3 caustic_color = vec3(0.6, 0.8, 1.0) * caustic;  
    color += caustic_color;

    vec3 depth_tint = mix(vec3(1.0), vec3(0.8, 0.9, 1.1), depth * 0.15);
    color *= depth_tint;

    fragColor = vec4(clamp(color, 0.0, 1.5), 1.0);
}
"""

class DepthLiquidRefractionPlugin(EffectPlugin):
    """Depth Liquid Refraction single-pass spatial displacement and caustic highlight simulation."""

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

    def initialize(self, context: PluginContext) -> bool:
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
            logger.error(f"Failed to config OpenGL in depth_liquid_refraction: {e}")
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

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
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
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "u_depth_tex"), 1)

        gl.glUniform1i(gl.glGetUniformLocation(self.program, "has_depth"), 1 if depth_in > 0 else 0)
        gl.glUniform2f(gl.glGetUniformLocation(self.program, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "time"), float(time_val))

        gl.glUniform1f(gl.glGetUniformLocation(self.program, "u_refraction"), self._map_norm(params.get("refractionStrength", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "u_chromatic"), self._map_norm(params.get("chromaticSpread", 3.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "u_ripple_speed"), self._map_norm(params.get("rippleSpeed", 4.0), 2.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "u_ripple_scale"), self._map_norm(params.get("rippleScale", 5.0), 2.0, 0.1))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "u_edge_glow"), self._map_norm(params.get("edgeGlow", 4.0)))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "u_depth_blur"), self._map_norm(params.get("depthBlur", 2.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "u_frost"), self._map_norm(params.get("frostedGlass", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "u_invert"), self._map_norm(params.get("invertDepth", 0.0)))

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
            logger.error(f"Cleanup Error in DepthLiquidRefraction: {e}")
        finally:
            self.program = 0
            self.empty_vao = 0

