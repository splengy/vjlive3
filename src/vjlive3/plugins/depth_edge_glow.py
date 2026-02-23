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
    "name": "Depth Edge Glow",
    "description": "Neon depth contour visualization.",
    "version": "1.0.0",
    "parameters": [
        {"name": "edge_threshold", "type": "float", "min": 0.0, "max": 1.0, "default": 0.1},
        {"name": "edge_thickness", "type": "float", "min": 0.0, "max": 10.0, "default": 2.0},
        {"name": "glow_radius", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "contour_intervals", "type": "int", "min": 1, "max": 64, "default": 8},
        {"name": "color_cycle_speed", "type": "float", "min": 0.0, "max": 5.0, "default": 1.0},
        {"name": "bg_dimming", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5}
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
uniform vec2 resolution;
uniform float time;

uniform float edge_threshold;
uniform float edge_thickness;
uniform float glow_radius;
uniform int contour_intervals;
uniform float color_cycle_speed;
uniform float bg_dimming;

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

float depth_edge(vec2 p, float rad) {
    vec2 t = vec2(rad / resolution.x, rad / resolution.y);

    float tl = texture(depthTex, p + vec2(-t.x, -t.y)).r;
    float tc = texture(depthTex, p + vec2( 0.0, -t.y)).r;
    float tr = texture(depthTex, p + vec2( t.x, -t.y)).r;
    float ml = texture(depthTex, p + vec2(-t.x,  0.0)).r;
    float mr = texture(depthTex, p + vec2( t.x,  0.0)).r;
    float bl = texture(depthTex, p + vec2(-t.x,  t.y)).r;
    float bc = texture(depthTex, p + vec2( 0.0,  t.y)).r;
    float br = texture(depthTex, p + vec2( t.x,  t.y)).r;

    float gx = -tl - 2.0 * ml - bl + tr + 2.0 * mr + br;
    float gy = -tl - 2.0 * tc - tr + bl + 2.0 * bc + br;
    return sqrt(gx * gx + gy * gy);
}

void main() {
    vec4 source = texture(tex0, uv);
    
    if (has_depth == 0) {
        fragColor = vec4(source.rgb * (1.0 - bg_dimming), source.a);
        return;
    }
    
    float depth = clamp(texture(depthTex, uv).r, 0.0, 1.0);

    // Bounded multi-scale Sobel edge detection (caps loop iterations to safe limits)
    float edge = 0.0;
    float thick = max(edge_thickness, 1.0);
    int passes = min(int(ceil(thick)), 3); // Max 3 passes to prevent GPU timeout (SAFETY RAIL #1)
    
    for (int i = 1; i <= 3; i++) {
        if (i > passes) break;
        edge = max(edge, depth_edge(uv, float(i)));
    }
    
    edge = smoothstep(edge_threshold * 0.1, edge_threshold * 0.1 + 0.05, edge);

    // Topographic contours
    float contour = 0.0;
    if (contour_intervals > 0) {
        float intervals = float(contour_intervals);
        float contour_val = fract(depth * intervals);
        contour = smoothstep(0.95, 1.0, contour_val) + (1.0 - smoothstep(0.0, 0.05, contour_val));
        contour *= 0.5;
    }
    float total_edge = max(edge, contour);

    // Bounded glow convolution limits checking strict loops organically natively correctly seamlessly (SAFETY RAIL #1)
    float glow = 0.0;
    if (glow_radius > 0.1) {
        int glow_samples = min(int(glow_radius), 3); // Limit to 3 max
        float gr = glow_radius * 2.0;

        for (int x = -3; x <= 3; x++) {
            for (int y = -3; y <= 3; y++) {
                if (abs(x) + abs(y) > glow_samples) continue;
                vec2 offset = vec2(float(x), float(y)) * gr / resolution;
                float e = depth_edge(uv + offset, 1.5);
                e = smoothstep(edge_threshold * 0.1, edge_threshold * 0.1 + 0.05, e);
                float dist = length(vec2(float(x), float(y)));
                glow += e * exp(-dist * 1.0);
            }
        }
        glow /= float((glow_samples * 2 + 1) * (glow_samples * 2 + 1));
        glow *= 3.0;
    }

    float final_glow = glow;

    // Rainbow color mapping
    float hue = fract(time * color_cycle_speed * 0.5 + depth);
    vec3 line_color = hsv2rgb(vec3(hue, 1.0, 1.0));

    vec3 result = source.rgb * (1.0 - bg_dimming);
    result += line_color * total_edge;
    result += line_color * final_glow * 0.5;

    fragColor = vec4(clamp(result, 0.0, 1.0), source.a);
}
"""

class DepthEdgeGlowPlugin(EffectPlugin):
    """Depth Edge Glow extracting bounding borders natively resolving topological loops safely."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.vao = None
        self.vbo = None
        self.fbo = None
        self.tex = None
        
        self._width = 0
        self._height = 0

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthEdgeGlow in Mock Mode")
            return

        try:
            self._compile_shader()
            self._setup_quad()
        except Exception as e:
            logger.error(f"Failed to config OpenGL in DepthEdgeGlow: {e}")
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
            if self.fbo is not None:
                gl.glDeleteFramebuffers(1, [self.fbo])
        except Exception:
            pass
        self.tex = None
        self.fbo = None

    def _allocate_buffer(self, w: int, h: int):
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
            
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), float(getattr(context, 'time', 0.0)))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "edge_threshold"), float(params.get("edge_threshold", 0.1)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "edge_thickness"), float(params.get("edge_thickness", 2.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "glow_radius"), float(params.get("glow_radius", 5.0)))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "contour_intervals"), int(params.get("contour_intervals", 8)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "color_cycle_speed"), float(params.get("color_cycle_speed", 1.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "bg_dimming"), float(params.get("bg_dimming", 0.5)))
        
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
            logger.error(f"Cleanup Error in DepthEdgeGlow: {e}")
