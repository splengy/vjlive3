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
    "name": "DepthBlur",
    "version": "3.0.0",
    "description": "Selective blur based on depth buffer values",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "blur",
    "tags": ["depth", "blur", "dof", "focus"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "blur_radius", "type": "int", "default": 5, "min": 1, "max": 50},
        {"name": "focus_start", "type": "float", "default": 0.3, "min": 0.0, "max": 1.0},
        {"name": "focus_end", "type": "float", "default": 0.7, "min": 0.0, "max": 1.0},
        {"name": "transition_smoothness", "type": "float", "default": 0.1, "min": 0.01, "max": 0.5},
        {"name": "blur_type", "type": "str", "default": "gaussian", "options": ["gaussian", "bokeh", "motion", "anisotropic"]},
        {"name": "bokeh_shape", "type": "str", "default": "circular", "options": ["circular", "hexagonal", "octagonal"]},
        {"name": "anisotropic_scale", "type": "float", "default": 1.0, "min": 0.1, "max": 5.0},
        
        # Legacy preset mappings
        {"name": "focalDistance", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "focalRange", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "blurAmount_legacy", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "fgBlur", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "bgBlur", "type": "float", "default": 7.0, "min": 0.0, "max": 10.0},
        {"name": "bokehBright", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "chromaticFringe", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "tiltShift", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "tiltAngle", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "aperture", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "quality", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "vignette", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "u_mix", "type": "float", "default": 1.0, "min": 0.0, "max": 1.0}
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

DEPTH_BLUR_FRAGMENT = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// VJLive3 new spec parameters
uniform float blur_radius;
uniform float focus_start;
uniform float focus_end;
uniform float transition_smoothness;
uniform int blur_type;         // 0=gaussian, 1=bokeh, 2=motion, 3=anisotropic
uniform int bokeh_shape;       // 0=circular, 1=hexagonal, 2=octagonal
uniform float anisotropic_scale;

// Legacy parameters
uniform float focal_distance;
uniform float focal_range;
uniform float blur_amount_legacy;
uniform float fg_blur;
uniform float bg_blur;
uniform float bokeh_bright;
uniform float chromatic_fringe;
uniform float tilt_shift;
uniform float tilt_angle;
uniform float aperture;
uniform float quality;
uniform float vignette;

#define PI 3.14159265

// Golden angle bokeh kernel
vec4 bokeh_blur(vec2 center, float radius, float bright_boost) {
    vec4 color = vec4(0.0);
    float total = 0.0;
    
    // Scale sample counts by quality
    int samples = int(mix(8.0, 32.0, quality));
    float golden = 2.399963;
    
    float active_aperture = aperture;
    if (bokeh_shape == 1) active_aperture = 6.0;
    else if (bokeh_shape == 2) active_aperture = 8.0;

    for (int i = 0; i < 32; i++) {
        if (i >= samples) break;
        float fi = float(i);

        float r = sqrt(fi / float(samples)) * radius;
        float theta = fi * golden;
        vec2 offset = vec2(cos(theta), sin(theta)) * r / resolution;

        if (active_aperture > 3.0) {
            float blade_count = mix(6.0, 8.0, clamp((active_aperture - 3.3) / 6.7, 0.0, 1.0));
            float blade_angle = atan(offset.y, offset.x);
            float blade = cos(blade_angle * blade_count);
            float shape = mix(1.0, smoothstep(0.3, 0.7, blade), clamp((active_aperture - 3.3) / 6.7 * 0.5, 0.0, 1.0));
            r *= shape;
            offset = vec2(cos(theta), sin(theta)) * r / resolution;
        }

        if (blur_type == 3) {
            // Anisotropic
            offset.x *= anisotropic_scale;
        }

        vec4 s = texture(tex0, center + offset);
        
        // Luminance weighting for bokeh bloom (higher on blur_type=1)
        float boost_factor = (blur_type == 1) ? bright_boost * 3.0 : 0.0;
        float luma = dot(s.rgb, vec3(0.299, 0.587, 0.114));
        float weight = 1.0 + luma * boost_factor;

        color += s * weight;
        total += weight;
    }

    return color / max(total, 1.0);
}

void main() {
    float depth = texture(depth_tex, uv).r;
    vec4 source = texture(tex0, uv);

    float coc = 0.0;

    // Use legacy DOF algorithm if transition_smoothness spec isn't overriding
    if (tilt_shift < 0.1) {
        // Mixed logic bridging legacy and modern
        float center_focus = mix(focal_distance, (focus_start + focus_end) * 0.5, 0.5);
        float dist_from_focal = abs(depth - center_focus);
        
        float final_focus_range = max(focal_range, focus_end - focus_start);
        coc = smoothstep(0.0, max(final_focus_range, 0.001), dist_from_focal);

        if (depth < center_focus) {
            coc *= fg_blur;
        } else {
            coc *= bg_blur;
        }
    } else {
        // Tilt shift
        float angle = tilt_angle * PI;
        vec2 center = uv - 0.5;
        float projected = center.x * sin(angle) + center.y * cos(angle);
        coc = smoothstep(0.0, focal_range * 0.3, abs(projected) - focal_distance * 0.3);
        coc *= tilt_shift;
    }

    // Radius computed combining legacy and new params
    float radius = coc * max(blur_amount_legacy * 15.0, blur_radius);

    vec4 result;
    if (radius < 0.5) {
        result = source;
    } else {
        result = bokeh_blur(uv, radius, bokeh_bright);

        if (chromatic_fringe > 0.0 && radius > 1.0) {
            float fringe = chromatic_fringe * radius * 0.002;
            result.r = bokeh_blur(uv + vec2(fringe, 0.0), radius, bokeh_bright).r;
            result.b = bokeh_blur(uv - vec2(fringe, 0.0), radius, bokeh_bright).b;
        }
    }

    if (vignette > 0.0) {
        float dist = length(uv - 0.5) * 2.0;
        float vig = 1.0 - smoothstep(0.5, 1.4, dist) * vignette * 0.5;
        vig -= coc * vignette * 0.15;
        result.rgb *= max(vig, 0.0);
    }

    fragColor = mix(source, result, u_mix);
}
"""

class DepthBlurPlugin(EffectPlugin):
    """
    DepthBlurEffect plugin port for VJLive3.
    """
    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.out_tex = None
        self.fbo = None
        self.vao = None
        self.vbo = None
        self.time = 0.0

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthBlur in Mock Mode (No OpenGL)")
            return

        try:
            self._compile_shader()
            self._setup_quad()
            self._setup_fbo(1920, 1080)
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthBlur: {e}")
            self._mock_mode = True

    def _compile_shader(self):
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"Vertex Shader Error: {gl.glGetShaderInfoLog(vs)}")

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, DEPTH_BLUR_FRAGMENT)
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
        def map_p(key, max_val=1.0):
            idx = [x["name"] for x in METADATA["parameters"]].index(key)
            default = METADATA["parameters"][idx].get("default", 0.0)
            v = params.get(key, default)
            return (v / 10.0) * max_val

        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), self.time)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), params.get("u_mix", 1.0))
        
        # New spec mappings
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "blur_radius"), float(params.get("blur_radius", 5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "focus_start"), params.get("focus_start", 0.3))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "focus_end"), params.get("focus_end", 0.7))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "transition_smoothness"), params.get("transition_smoothness", 0.1))
        
        b_type = params.get("blur_type", "gaussian")
        blur_type_int = 0
        if b_type == "bokeh": blur_type_int = 1
        elif b_type == "motion": blur_type_int = 2
        elif b_type == "anisotropic": blur_type_int = 3
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "blur_type"), blur_type_int)

        b_shape = params.get("bokeh_shape", "circular")
        shape_int = 0
        if b_shape == "hexagonal": shape_int = 1
        elif b_shape == "octagonal": shape_int = 2
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "bokeh_shape"), shape_int)
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "anisotropic_scale"), params.get("anisotropic_scale", 1.0))

        # Legacy mapped parameters
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "focal_distance"), map_p("focalDistance", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "focal_range"), map_p("focalRange", 0.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "blur_amount_legacy"), map_p("blurAmount_legacy", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fg_blur"), map_p("fgBlur", 1.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "bg_blur"), map_p("bgBlur", 1.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "bokeh_bright"), map_p("bokehBright", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "chromatic_fringe"), map_p("chromaticFringe", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "tilt_shift"), map_p("tiltShift", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "tilt_angle"), map_p("tiltAngle", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "aperture"), map_p("aperture", 10.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "quality"), map_p("quality", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "vignette"), map_p("vignette", 1.0))

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        depth_texture = getattr(context, "inputs", {}).get("depth_in", input_texture)
        
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        self.time += context.delta_time
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
            logger.error(f"Cleanup Error in DepthBlur: {e}")
