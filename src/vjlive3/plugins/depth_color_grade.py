import numpy as np
import logging

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from typing import Dict, Any
from vjlive3.plugins.api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

METADATA = {
    "name": "Depth Color Grade",
    "description": "Per-depth-band color grading (near, mid, far zones).",
    "version": "1.0.0",
    "parameters": [
        {"name": "zone_near", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "zone_far", "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "zone_blend", "type": "float", "min": 0.0, "max": 0.5, "default": 0.1},
        
        {"name": "near_hue", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "near_saturation", "type": "float", "min": 0.0, "max": 2.0, "default": 1.0},
        {"name": "near_temperature", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "near_exposure", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        
        {"name": "mid_hue", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "mid_saturation", "type": "float", "min": 0.0, "max": 2.0, "default": 1.0},
        {"name": "mid_temperature", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "mid_exposure", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        
        {"name": "far_hue", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "far_saturation", "type": "float", "min": 0.0, "max": 2.0, "default": 1.0},
        {"name": "far_temperature", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "far_exposure", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        
        {"name": "contrast", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "film_curve", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 position;
layout(location = 1) in vec2 texcoord;
out vec2 uv;
void main() {
    uv = texcoord;
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depthTex;

uniform int has_depth;

uniform float zone_near;
uniform float zone_far;
uniform float zone_blend;

uniform float near_hue;
uniform float near_saturation;
uniform float near_temperature;
uniform float near_exposure;

uniform float mid_hue;
uniform float mid_saturation;
uniform float mid_temperature;
uniform float mid_exposure;

uniform float far_hue;
uniform float far_saturation;
uniform float far_temperature;
uniform float far_exposure;

uniform float contrast;
uniform float film_curve;

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

vec3 grade(vec3 color, float hue_shift, float sat_mult, float temp, float exposure) {
    color *= pow(2.0, (exposure - 0.5) * 2.0);
    
    float t = (temp - 0.5) * 0.3;
    color.r += t;
    color.b -= t;
    
    vec3 hsv = rgb2hsv(clamp(color, 0.0, 1.0));
    hsv.x = fract(hsv.x + hue_shift);
    hsv.y *= sat_mult;
    hsv.y = clamp(hsv.y, 0.0, 1.0);
    
    return hsv2rgb(hsv);
}

vec3 apply_curve(vec3 color, float mode) {
    if (mode < 3.3) {
        return color;
    } else if (mode < 6.6) {
        return color * color * (3.0 - 2.0 * color);
    } else {
        return log(1.0 + color * 9.0) / log(10.0);
    }
}

void main() {
    float depth = 0.5; // Default mapping aligns to MID structure safely globally
    if (has_depth == 1) {
        depth = texture(depthTex, uv).r;
    }
    
    vec4 source = texture(tex0, uv);
    vec3 color = source.rgb;
    
    float blend = zone_blend * 0.15 + 0.01;
    float near_mask = 1.0 - smoothstep(zone_near - blend, zone_near + blend, depth);
    float far_mask = smoothstep(zone_far - blend, zone_far + blend, depth);
    float mid_mask = max(1.0 - near_mask - far_mask, 0.0);
    
    vec3 near_graded = grade(color, near_hue, near_saturation, near_temperature, near_exposure);
    vec3 mid_graded = grade(color, mid_hue, mid_saturation, mid_temperature, mid_exposure);
    vec3 far_graded = grade(color, far_hue, far_saturation, far_temperature, far_exposure);
    
    vec3 graded = near_graded * near_mask + mid_graded * mid_mask + far_graded * far_mask;
    
    if (contrast != 0.5) {
        float c = (contrast - 0.5) * 2.0;
        graded = mix(vec3(0.5), graded, 1.0 + c);
    }
    
    graded = apply_curve(clamp(graded, 0.0, 1.0), film_curve);
    fragColor = vec4(clamp(graded, 0.0, 1.0), 1.0);
}
"""

class DepthColorGradePlugin(EffectPlugin):
    """3-Zone Depth Spatial Color Corrector mapped to real-time depth boundaries."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.fbo = None
        self.tex = None
        self.vao = None
        self.vbo = None
        self._width = 0
        self._height = 0

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthColorGrade in Mock Mode (No OpenGL)")
            return

        try:
            self._compile_shader()
            self._setup_quad()
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthColorGrade: {e}")
            self._mock_mode = True

    def _compile_shader(self):
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"Vertex Shader Error: {gl.glGetShaderInfoLog(vs)}")

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, FRAGMENT_SHADER)
        gl.glCompileShader(fs)
        if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"Fragment Shader Error: {gl.glGetShaderInfoLog(fs)}")

        self.prog = gl.glCreateProgram()
        gl.glAttachShader(self.prog, vs)
        gl.glAttachShader(self.prog, fs)
        gl.glLinkProgram(self.prog)
        if not gl.glGetProgramiv(self.prog, gl.GL_LINK_STATUS):
            raise RuntimeError(f"Program Link Error: {gl.glGetProgramInfoLog(self.prog)}")
            
        gl.glDeleteShader(vs)
        gl.glDeleteShader(fs)

    def _setup_quad(self):
        vertices = np.array([
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 1.0,
             1.0,  1.0,  1.0, 1.0,
        ], dtype=np.float32)
        
        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        
        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
        
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(8))
        gl.glBindVertexArray(0)

    def _allocate_buffers(self, w: int, h: int):
        self._free_fbo()
        self._width = w
        self._height = h
        
        self.fbo = gl.glGenFramebuffers(1)
        self.tex = gl.glGenTextures(1)
            
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.tex, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _free_fbo(self):
        try:
            if self.tex is not None:
                gl.glDeleteTextures(1, [self.tex])
            if self.fbo is not None:
                gl.glDeleteFramebuffers(1, [self.fbo])
            self.tex = None
            self.fbo = None
        except Exception as e:
            logger.debug(f"Safely catching cleanup exception on FBO: {e}")

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        inputs = getattr(context, "inputs", {})
        depth_in = inputs.get("depth_in", 0)
        
        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        if w != self._width or h != self._height:
            self._allocate_buffers(w, h)
            
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glUseProgram(self.prog)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depthTex"), 2)
        
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), 1 if depth_in > 0 else 0)
        
        # Explicit bounding logic ensuring zone validity mapping seamlessly structurally
        z_near = float(params.get("zone_near", 0.3))
        z_far = float(params.get("zone_far", 0.6))
        if z_near > z_far:
            z_near, z_far = z_far, z_near
            
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "zone_near"), z_near)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "zone_far"), z_far)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "zone_blend"), float(params.get("zone_blend", 0.1)))
        
        # Load Color Controls per Zone
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "near_hue"), float(params.get("near_hue", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "near_saturation"), float(params.get("near_saturation", 1.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "near_temperature"), float(params.get("near_temperature", 0.5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "near_exposure"), float(params.get("near_exposure", 0.5)))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "mid_hue"), float(params.get("mid_hue", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "mid_saturation"), float(params.get("mid_saturation", 1.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "mid_temperature"), float(params.get("mid_temperature", 0.5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "mid_exposure"), float(params.get("mid_exposure", 0.5)))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "far_hue"), float(params.get("far_hue", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "far_saturation"), float(params.get("far_saturation", 1.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "far_temperature"), float(params.get("far_temperature", 0.5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "far_exposure"), float(params.get("far_exposure", 0.5)))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "contrast"), float(params.get("contrast", 0.5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "film_curve"), float(params.get("film_curve", 0.0)))
        
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.tex
            
        return self.tex

    def cleanup(self) -> None:
        if self._mock_mode:
            return
            
        try:
            self._free_fbo()
            if self.vbo is not None:
                gl.glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.vao is not None:
                gl.glDeleteVertexArrays(1, [self.vao])
                self.vao = None
            if self.prog is not None:
                gl.glDeleteProgram(self.prog)
                self.prog = None
        except Exception as e:
            logger.error(f"Cleanup Error in DepthColorGrade: {e}")
