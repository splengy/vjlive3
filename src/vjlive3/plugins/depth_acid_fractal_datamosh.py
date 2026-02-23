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
    "name": "DepthAcidFractalDatamoshEffect",
    "version": "3.0.0",
    "description": "Acid fractal datamosh effect with depth buffer integration",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "datamosh",
    "tags": ["depth", "datamosh", "fractal", "acid", "glitch"],
    "priority": 1,
    "dependencies": ["DepthBuffer", "FractalGenerator"],
    "incompatible": ["NoDepthSupport"],
    "parameters": [
        {"name": "fractal_scale", "type": "float", "min": 0.1, "max": 10.0, "default": 2.0},
        {"name": "datamosh_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "depth_influence", "type": "float", "min": 0.0, "max": 1.0, "default": 0.7},
        {"name": "color_shift", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "glitch_probability", "type": "float", "min": 0.0, "max": 1.0, "default": 0.1},
        {"name": "preserve_luminance", "type": "bool", "default": True}
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
uniform sampler2D prevTex;

uniform int has_depth;
uniform vec2 resolution;
uniform float time;
uniform float beat_phase;

uniform float fractal_scale;
uniform float datamosh_intensity;
uniform float depth_influence;
uniform float color_shift;
uniform float glitch_probability;
uniform int preserve_luminance;

// Bounded fractals protecting GPU timeout (safety rail #1)
vec2 julia(vec2 z, vec2 c) {
    return vec2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y) + c;
}

// Pseudo-random generator
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453123);
}

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    float depth = 0.5;
    if (has_depth == 1) {
        depth = texture(depthTex, uv).r;
    }

    // Datamosh Disruption Coordinate mapping
    float prob = hash(uv * time);
    vec2 smosh_uv = uv;
    bool is_glitch = prob < glitch_probability * datamosh_intensity;

    if (is_glitch) {
        float bSize = max(5.0, 50.0 * (1.0 - datamosh_intensity)); // block size
        vec2 block = floor(uv * resolution / bSize) * bSize / resolution;
        
        // Motion vectors approximated from texture gradient
        float dx = texture(prevTex, block + vec2(1.0/resolution.x, 0)).r - texture(prevTex, block).r;
        float dy = texture(prevTex, block + vec2(0, 1.0/resolution.y)).r - texture(prevTex, block).r;
        
        vec2 m_vec = vec2(dx, dy) * 10.0 * datamosh_intensity;
        smosh_uv = block - m_vec;
        
        // Use prev frame pixel block to smear out motion
        if (hash(block * time) < 0.8) {
             fragColor = texture(prevTex, smosh_uv);
             return;
        }
    }

    // Fractal evaluation
    vec2 z = (uv - 0.5) * fractal_scale;
    float depthMod = depth * depth_influence * 2.0;
    vec2 c = vec2(sin(time * 0.3 + depthMod), cos(time * 0.4 + beat_phase));
    
    int iterations = 0;
    int maxIter = 15; // Strictly bounded iterations (SAFETY RAIL #1)
    for (int i = 0; i < 15; i++) {
        z = julia(z, c);
        if (length(z) > 4.0) break;
        iterations++;
    }

    float frac = float(iterations) / float(maxIter);

    // Color mappings
    vec4 current_src = texture(tex0, uv);
    vec3 hsv = rgb2hsv(current_src.rgb);
    
    // Applying acid color warp to fractal map
    hsv.x = fract(hsv.x + frac * color_shift + time * 0.1);
    hsv.y = clamp(hsv.y + frac * 0.5, 0.0, 1.0);
    
    vec3 out_col = hsv2rgb(hsv);
    
    if (preserve_luminance == 1) {
        float src_luma = dot(current_src.rgb, vec3(0.299, 0.587, 0.114));
        float new_luma = dot(out_col, vec3(0.299, 0.587, 0.114));
        out_col *= (src_luma / (new_luma + 0.0001));
    }
    
    fragColor = vec4(clamp(out_col, 0.0, 1.0), current_src.a);
}
"""

class DepthAcidFractalDatamoshEffectPlugin(EffectPlugin):
    """
    Implements a datamosh effect that combines acid fractal patterns with depth buffer manipulation. 
    Maintains 60 FPS safety bounds and strictly enforces memory management.
    """

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.vao = None
        self.vbo = None
        
        self.fbo = None
        self.tex = None
        self.prev_tex = None  # Buffer for temporal datamoshing
        
        self._width = 0
        self._height = 0

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthAcidFractalDatamoshEffect in Mock Mode")
            return

        try:
            self._compile_shader()
            self._setup_quad()
            # Explicitly set width to 0 to trigger allocation on first frame.
            self._width = 0 
        except Exception as e:
            logger.error(f"Failed to config OpenGL in DepthAcidFractalDatamoshEffect: {e}")
            self._mock_mode = True

    def _compile_shader(self):
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(gl.glGetShaderInfoLog(vs))

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, FRAGMENT_SHADER)
        gl.glCompileShader(fs)
        if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(gl.glGetShaderInfoLog(fs))

        self.prog = gl.glCreateProgram()
        gl.glAttachShader(self.prog, vs)
        gl.glAttachShader(self.prog, fs)
        gl.glLinkProgram(self.prog)
        if not gl.glGetProgramiv(self.prog, gl.GL_LINK_STATUS):
            raise RuntimeError(gl.glGetProgramInfoLog(self.prog))
            
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

    def _free_fbo(self):
        try:
            if self.tex is not None:
                gl.glDeleteTextures(1, [self.tex])
            if self.prev_tex is not None:
                gl.glDeleteTextures(1, [self.prev_tex])
            if self.fbo is not None:
                gl.glDeleteFramebuffers(1, [self.fbo])
        except Exception:
            pass
        self.tex = None
        self.prev_tex = None
        self.fbo = None

    def _allocate_buffer(self, w: int, h: int):
        self._free_fbo()
        self._width = w
        self._height = h
        
        self.fbo = gl.glGenFramebuffers(1)
        
        # Primary working texture
        self.tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        # Datamoshing temporal state memory
        self.prev_tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.prev_tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.tex, 0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

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
        if w != self._width or h != self._height or self.fbo is None:
            self._allocate_buffer(w, h)
            
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.tex, 0)
        
        gl.glViewport(0, 0, w, h)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glUseProgram(self.prog)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        if depth_in > 0:
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depthTex"), 1)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), 1)
        else:
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), 0)
            
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.prev_tex)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "prevTex"), 2)     
            
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), float(getattr(context, 'time', 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "beat_phase"), float(getattr(context, 'beat_phase', 0.0)))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fractal_scale"), float(params.get("fractal_scale", 2.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "datamosh_intensity"), float(params.get("datamosh_intensity", 0.5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_influence"), float(params.get("depth_influence", 0.7)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "color_shift"), float(params.get("color_shift", 0.3)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "glitch_probability"), float(params.get("glitch_probability", 0.1)))
        
        preserve = 1 if params.get("preserve_luminance", True) else 0
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "preserve_luminance"), preserve)
        
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        # Ping-Pong Temporal state for active datamoshing accumulation
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.prev_tex)
        gl.glCopyTexSubImage2D(gl.GL_TEXTURE_2D, 0, 0, 0, 0, 0, w, h)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        
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
            logger.error(f"Cleanup Error in DepthAcidFractalDatamoshEffect: {e}")
