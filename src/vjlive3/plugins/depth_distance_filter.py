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
    "name": "DepthDistanceFilter",
    "version": "3.0.0",
    "description": "Distance-based filtering using depth buffer",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "filter",
    "tags": ["depth", "distance", "filter", "fog", "atmosphere"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "filter_type", "type": "str", "default": "fog", "options": ["fog", "blur", "contrast", "saturation", "brightness"]},
        {"name": "near_distance", "type": "float", "default": 0.0, "min": 0.0, "max": 1.0},
        {"name": "far_distance", "type": "float", "default": 1.0, "min": 0.0, "max": 1.0},
        {"name": "filter_strength", "type": "float", "default": 0.5, "min": 0.0, "max": 1.0},
        {"name": "fog_color", "type": "list", "default": [0.7, 0.8, 1.0]},
        {"name": "blur_radius", "type": "int", "default": 5, "min": 1, "max": 20},
        {"name": "contrast_shift", "type": "float", "default": 0.0, "min": -1.0, "max": 1.0},
        {"name": "saturation_shift", "type": "float", "default": 0.0, "min": -1.0, "max": 1.0},
        {"name": "brightness_shift", "type": "float", "default": 0.0, "min": -1.0, "max": 1.0}
    ]
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

DEPTH_DISTANCE_FILTER_FRAGMENT = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform vec2 resolution;

uniform int filter_type; // 0=fog, 1=blur, 2=contrast, 3=sat, 4=bright
uniform float near_distance;
uniform float far_distance;
uniform float filter_strength;

uniform vec3 fog_color;
uniform int blur_radius;
uniform float contrast_shift;
uniform float saturation_shift;
uniform float brightness_shift;

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
    float depth = texture(depth_tex, uv).r;
    vec3 color = texture(tex0, uv).rgb;
    
    // clamp denom to prevent extreme bleeding
    float denom = far_distance - near_distance;
    float w = 0.0;
    if (abs(denom) > 0.0001) {
        w = clamp((depth - near_distance) / denom, 0.0, 1.0);
    } else {
        w = depth >= near_distance ? 1.0 : 0.0;
    }
    
    float intensity = w * filter_strength;
    
    if (intensity > 0.0) {
        if (filter_type == 0) { // fog
            color = mix(color, fog_color, intensity);
        }
        else if (filter_type == 1) { // blur
            int r = int(round(float(blur_radius) * intensity));
            if (r > 0) {
                vec3 blurred = vec3(0.0);
                float total = 0.0;
                for (int x = -r; x <= r; x++) {
                    for (int y = -r; y <= r; y++) {
                        vec2 offset = vec2(float(x), float(y)) / resolution;
                        float w_blur = 1.0 / (1.0 + float(abs(x) + abs(y)));
                        blurred += texture(tex0, clamp(uv + offset, 0.0, 1.0)).rgb * w_blur;
                        total += w_blur;
                    }
                }
                color = blurred / total;
            }
        }
        else if (filter_type == 2) { // contrast
            float cs = contrast_shift * intensity;
            color = mix(vec3(0.5), color, 1.0 + cs);
        }
        else if (filter_type == 3) { // sat
            float ss = saturation_shift * intensity;
            vec3 hsv = rgb2hsv(clamp(color, 0.0, 1.0));
            hsv.y = clamp(hsv.y * (1.0 + ss), 0.0, 1.0);
            color = hsv2rgb(hsv);
        }
        else if (filter_type == 4) { // bright
            float bs = brightness_shift * intensity;
            color = clamp(color + vec3(bs), 0.0, 1.0);
        }
    }
    
    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
"""

class DepthDistanceFilterPlugin(EffectPlugin):
    """
    DepthDistanceFilter implementation for VJLive3.
    """
    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.out_tex = None
        self.fbo = None
        self.vao = None
        self.vbo = None

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            return

        try:
            self._compile_shader()
            self._setup_quad()
            self._setup_fbo(1920, 1080)
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthDistanceFilter: {e}")
            self._mock_mode = True

    def _compile_shader(self):
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"VS Error: {gl.glGetShaderInfoLog(vs)}")

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, DEPTH_DISTANCE_FILTER_FRAGMENT)
        gl.glCompileShader(fs)
        if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"FS Error: {gl.glGetShaderInfoLog(fs)}")

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

    def _setup_fbo(self, w: int, h: int):
        self.fbo = gl.glGenFramebuffers(1)
        self.out_tex = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.out_tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.out_tex, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _bind_uniforms(self, params: Dict[str, Any], w: int, h: int):
        f_type = params.get("filter_type", "fog")
        type_idx = 0
        if f_type == "blur": type_idx = 1
        elif f_type == "contrast": type_idx = 2
        elif f_type == "saturation": type_idx = 3
        elif f_type == "brightness": type_idx = 4
        
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "filter_type"), type_idx)
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "near_distance"), float(params.get("near_distance", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "far_distance"), float(params.get("far_distance", 1.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "filter_strength"), float(params.get("filter_strength", 0.5)))
        
        fc = params.get("fog_color", [0.7, 0.8, 1.0])
        if not isinstance(fc, list) or len(fc) < 3:
            fc = [0.7, 0.8, 1.0]
        gl.glUniform3f(gl.glGetUniformLocation(self.prog, "fog_color"), float(fc[0]), float(fc[1]), float(fc[2]))
        
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "blur_radius"), int(params.get("blur_radius", 5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "contrast_shift"), float(params.get("contrast_shift", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "saturation_shift"), float(params.get("saturation_shift", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "brightness_shift"), float(params.get("brightness_shift", 0.0)))

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        depth_texture = getattr(context, "inputs", {}).get("depth_in", input_texture)
        
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        gl.glUseProgram(self.prog)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 1)
        
        self._bind_uniforms(params, w, h)
        
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.out_tex
            
        return self.out_tex

    def cleanup(self) -> None:
        if self._mock_mode:
            return
            
        try:
            if self.out_tex:
                gl.glDeleteTextures(1, [self.out_tex])
                self.out_tex = None
            if self.fbo:
                gl.glDeleteFramebuffers(1, [self.fbo])
                self.fbo = None
            if self.vbo:
                gl.glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.vao:
                gl.glDeleteVertexArrays(1, [self.vao])
                self.vao = None
            if self.prog:
                gl.glDeleteProgram(self.prog)
                self.prog = None
        except Exception as e:
            logger.error(f"Cleanup Error: {e}")
