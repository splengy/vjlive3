"""
P3-VD48: Depth Fog Plugin for VJLive3.
Ported from legacy VJlive-2 DepthFogEffect.
Implements atmospheric distance fog mapped to depth calculations
computed completely natively on a Single-Pass geometric quad.
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
    "name": "DepthFog",
    "version": "3.0.0",
    "description": "Atmospheric distance fog controlled by depth mapping.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "visual",
    "tags": ["depth", "fog", "environment", "fbm", "distance"],
    "priority": 1,
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "fogDensity", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "fogStart", "type": "float", "default": 1.0, "min": 0.0, "max": 10.0},
        {"name": "fogEnd", "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
        {"name": "fogMode", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0}, # 0.0-3.3 linear, 3.3-6.6 exp, >6.6 exp2
        {"name": "fogColorR", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "fogColorG", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "fogColorB", "type": "float", "default": 6.0, "min": 0.0, "max": 10.0},
        {"name": "fogHeight", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "fogAnimate", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "fogScatter", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "fogOpacity", "type": "float", "default": 7.0, "min": 0.0, "max": 10.0}
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
uniform int has_depth;

uniform float time;
uniform vec2 resolution;
uniform float u_mix;

uniform float fog_density;
uniform float fog_start;
uniform float fog_end;
uniform float fog_mode;          
uniform vec3 fog_color;
uniform float fog_height;        
uniform float fog_animate;       
uniform float fog_scatter;       
uniform float fog_opacity;       

float hash(vec2 p) {
    p = fract(p * vec2(443.897, 441.423));
    p += dot(p, p.yx + 19.19);
    return fract((p.x + p.y) * p.x);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1, 0));
    float c = hash(i + vec2(0, 1));
    float d = hash(i + vec2(1, 1));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 4; i++) {
        v += a * noise(p);
        p *= 2.0;
        a *= 0.5;
    }
    return v;
}

void main() {
    vec4 source = texture(tex0, uv);

    if (has_depth == 0) {
        fragColor = source;
        return;
    }

    float depth = texture(depth_tex, uv).r;
    depth = clamp((depth - 0.3) / 3.7, 0.0, 1.0); // Normalize legacy limits

    float fog_factor = 0.0;
    float dist = clamp((depth - fog_start) / max(fog_end - fog_start, 0.001), 0.0, 1.0);

    if (fog_mode < 3.3) {
        // Linear
        fog_factor = dist;
    } else if (fog_mode < 6.6) {
        // Exponential
        fog_factor = 1.0 - exp(-fog_density * dist * 3.0);
    } else {
        // Exponential squared
        float d = fog_density * dist * 2.0;
        fog_factor = 1.0 - exp(-d * d);
    }

    // Height gradient (ground fog)
    if (fog_height > 0.0) {
        float y = uv.y;
        float height_mask = smoothstep(1.0 - fog_height, 1.0, y);
        fog_factor *= mix(1.0, height_mask, fog_height);
    }

    // Animated fog swirl
    vec3 final_fog = fog_color;
    if (fog_animate > 0.0) {
        float swirl = fbm(uv * 4.0 + vec2(time * 0.1, time * 0.05)) * fog_animate;
        fog_factor += (swirl - 0.3) * 0.2 * fog_animate;
        final_fog += vec3(swirl * 0.1, 0.0, -swirl * 0.05); // Color variation logic
    }

    // Light scattering
    if (fog_scatter > 0.0) {
        float scatter_glow = pow(max(fog_factor, 0.0), 2.0) * fog_scatter;
        final_fog += scatter_glow * 0.2;
    }

    fog_factor = clamp(fog_factor * fog_opacity, 0.0, 1.0);

    vec4 result = mix(source, vec4(final_fog, 1.0), fog_factor);
    fragColor = mix(source, result, u_mix);
}
"""

class DepthFogPlugin(EffectPlugin):
    """Depth Fog atmospheric generator relying on distance approximations and FBM noise swirls."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.program = 0
        self.empty_vao = 0
        self.fbo = 0
        self.target_texture = 0
        self._width = 0
        self._height = 0
        self._initialized = False

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            logger.warning("Mock mode engaged. Skipping GL initialization.")
            self._initialized = True
            return True

        try:
            vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
            gl.glShaderSource(vs, VERTEX_SHADER_SOURCE)
            gl.glCompileShader(vs)
            if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
                raise RuntimeError(gl.glGetShaderInfoLog(vs))

            fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fs, FRAGMENT_SHADER_SOURCE)
            gl.glCompileShader(fs)
            if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
                raise RuntimeError(gl.glGetShaderInfoLog(fs))

            self.program = gl.glCreateProgram()
            gl.glAttachShader(self.program, vs)
            gl.glAttachShader(self.program, fs)
            gl.glLinkProgram(self.program)
            if not gl.glGetProgramiv(self.program, gl.GL_LINK_STATUS):
                raise RuntimeError(gl.glGetProgramInfoLog(self.program))
                
            gl.glDeleteShader(vs)
            gl.glDeleteShader(fs)

            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to config OpenGL in depth_fog: {e}")
            self._mock_mode = True
            return False

    def _free_fbo(self):
        try:
            if self.target_texture != 0:
                gl.glDeleteTextures(1, [self.target_texture])
            if self.fbo != 0:
                gl.glDeleteFramebuffers(1, [self.fbo])
        except Exception:
            pass
        self.target_texture = 0
        self.fbo = 0

    def _allocate_buffers(self, w: int, h: int):
        self._free_fbo()
        self._width = w
        self._height = h
        
        self.fbo = gl.glGenFramebuffers(1)
        self.target_texture = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.target_texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.target_texture, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _map_norm(self, val: float, max_v: float = 1.0) -> float:
        """Map generic 0-10 bounds natively matching legacy implementations down to 0.0-1.0 base coefficients."""
        return (max(0.0, min(10.0, float(val))) / 10.0) * max_v

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
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        gl.glUseProgram(self.program)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "depth_tex"), 1)
        
        # Identifiers
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "has_depth"), 1 if depth_in > 0 else 0)
        gl.glUniform2f(gl.glGetUniformLocation(self.program, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "time"), float(time_val))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "u_mix"), 1.0)

        # Mappings matching legacy out_min + (val/10)*(out_max - out_min)
        # For fogMode, it was mapped out_max=10.0, out_min=0.0 meaning we evaluate exactly 0.0 - 10.0
        
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "fog_density"), self._map_norm(params.get("fogDensity", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "fog_start"), self._map_norm(params.get("fogStart", 1.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "fog_end"), self._map_norm(params.get("fogEnd", 8.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "fog_mode"), self._map_norm(params.get("fogMode", 0.0), 10.0))
        
        col = (
            self._map_norm(params.get("fogColorR", 3.0)),
            self._map_norm(params.get("fogColorG", 4.0)),
            self._map_norm(params.get("fogColorB", 6.0))
        )
        gl.glUniform3f(gl.glGetUniformLocation(self.program, "fog_color"), col[0], col[1], col[2])
        
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "fog_height"), self._map_norm(params.get("fogHeight", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "fog_animate"), self._map_norm(params.get("fogAnimate", 3.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "fog_scatter"), self._map_norm(params.get("fogScatter", 3.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "fog_opacity"), self._map_norm(params.get("fogOpacity", 7.0)))

        # Draw execution
        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.target_texture
            
        return self.target_texture

    def cleanup(self) -> None:
        try:
            self._free_fbo()
            if hasattr(gl, 'glDeleteProgram') and self.program != 0:
                gl.glDeleteProgram(self.program)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao != 0:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup Error in DepthFog: {e}")
        finally:
            self.program = 0
            self.empty_vao = 0

