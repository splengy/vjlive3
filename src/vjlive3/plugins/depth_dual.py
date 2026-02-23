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
    "name": "DepthDual",
    "version": "3.0.0",
    "description": "Composite two depth effects with blending",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "composite",
    "tags": ["depth", "dual", "composite", "blend"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "effect_a_type", "type": "str", "default": "blur", "options": ["blur", "color_grade", "distortion", "none"]},
        {"name": "effect_b_type", "type": "str", "default": "color_grade", "options": ["blur", "color_grade", "distortion", "none"]},
        {"name": "blend_mode", "type": "str", "default": "depth", "options": ["depth", "uniform", "radial", "custom"]},
        {"name": "blend_threshold", "type": "float", "default": 0.5, "min": 0.0, "max": 1.0},
        {"name": "blend_transition", "type": "float", "default": 0.2, "min": 0.0, "max": 0.5},
        {"name": "effect_a_params", "type": "dict", "default": {}},
        {"name": "effect_b_params", "type": "dict", "default": {}},
        {"name": "invert_blend", "type": "bool", "default": False}
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

DEPTH_DUAL_FRAGMENT = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform vec2 resolution;

uniform int effect_a_type; // 0=none, 1=blur, 2=color_grade, 3=distortion
uniform int effect_b_type;
uniform int blend_mode; // 0=depth, 1=uniform, 2=radial, 3=custom (maps to uniform)
uniform float blend_threshold;
uniform float blend_transition;
uniform bool invert_blend;

uniform vec4 params_a;
uniform vec4 params_b;

vec3 hsv2rgb(vec3 c) {
    vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0/3.0, 1.0/3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 apply_effect(int type, vec3 color, vec4 params, vec2 uv_coord) {
    if (type == 0) return color; // none
    
    if (type == 1) { // blur (params_x = radius proxy 0-1)
        int r = int(params.x * 20.0);
        if (r <= 0) return color;
        vec3 blurred = vec3(0.0);
        float total = 0.0;
        for (int x = -r; x <= r; x++) {
            for (int y = -r; y <= r; y++) {
                vec2 offset = vec2(float(x), float(y)) / resolution;
                float w = 1.0 / (1.0 + float(abs(x) + abs(y)));
                blurred += texture(tex0, clamp(uv_coord + offset, 0.0, 1.0)).rgb * w;
                total += w;
            }
        }
        return blurred / total;
    }
    
    if (type == 2) { // color_grade (xyz = tint, w = intensity)
        vec3 tint = params.xyz;
        if(length(tint) < 0.001) tint = vec3(1.0);
        return mix(color, color * tint * 1.5, params.w);
    }
    
    if (type == 3) { // distortion (x = freq, y = amplitude)
        vec2 d = vec2(sin(uv_coord.y * params.x * 20.0), cos(uv_coord.x * params.x * 20.0)) * params.y * 0.05;
        return texture(tex0, clamp(uv_coord + d, 0.0, 1.0)).rgb;
    }
    
    return color;
}

void main() {
    float depth = texture(depth_tex, uv).r;
    vec3 color = texture(tex0, uv).rgb;
    
    // Calculate blend weight
    float weight = 0.0;
    float trans = max(blend_transition, 0.001); // Prevent div-by-zero
    
    if (blend_mode == 0) { // depth
        weight = smoothstep(blend_threshold - trans, blend_threshold + trans, depth);
    } else if (blend_mode == 1 || blend_mode == 3) { // uniform / custom
        weight = blend_threshold;
    } else if (blend_mode == 2) { // radial
        float dist = length(uv - 0.5) * 2.0; // 0 at center, 1 at edges
        weight = smoothstep(blend_threshold - trans, blend_threshold + trans, dist);
    }
    
    if (invert_blend) {
        weight = 1.0 - weight;
    }
    
    vec3 result_a = apply_effect(effect_a_type, color, params_a, uv);
    vec3 result_b = apply_effect(effect_b_type, color, params_b, uv);
    
    vec3 composite = mix(result_a, result_b, weight);
    fragColor = vec4(clamp(composite, 0.0, 1.0), 1.0);
}
"""

class DepthDualPlugin(EffectPlugin):
    """
    DepthDual compositing node for VJLive3.
    Applies up to two distinct nested VFX configurations (A and B) and maps them topographically using a unified fragment shader evaluating smoothstep distributions safely.
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
            logger.error(f"Failed to initialize OpenGL in DepthDual: {e}")
            self._mock_mode = True

    def _compile_shader(self):
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"VS Error: {gl.glGetShaderInfoLog(vs)}")

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, DEPTH_DUAL_FRAGMENT)
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

    def _parse_params_to_vec4(self, e_type: str, p_dict: dict) -> list[float]:
        if not isinstance(p_dict, dict):
            p_dict = {}
            
        if e_type == "blur":
            r = float(p_dict.get("radius", 0.5))
            return [r, 0.0, 0.0, 0.0]
        elif e_type == "color_grade":
            tint = p_dict.get("tint", [1.0, 1.0, 1.0])
            if not isinstance(tint, list) or len(tint) < 3: tint = [1.0, 1.0, 1.0]
            intensity = float(p_dict.get("intensity", 0.5))
            return [float(tint[0]), float(tint[1]), float(tint[2]), intensity]
        elif e_type == "distortion":
            f = float(p_dict.get("frequency", 0.5))
            a = float(p_dict.get("amplitude", 0.2))
            return [f, a, 0.0, 0.0]
            
        return [0.0, 0.0, 0.0, 0.0]

    def _bind_uniforms(self, params: Dict[str, Any], w: int, h: int):
        # Type A mapping
        ea_str = params.get("effect_a_type", "blur")
        ea_idx = 0
        if ea_str == "blur": ea_idx = 1
        elif ea_str == "color_grade": ea_idx = 2
        elif ea_str == "distortion": ea_idx = 3
        
        # Type B mapping
        eb_str = params.get("effect_b_type", "color_grade")
        eb_idx = 0
        if eb_str == "blur": eb_idx = 1
        elif eb_str == "color_grade": eb_idx = 2
        elif eb_str == "distortion": eb_idx = 3
        
        # Blending mode mapping
        b_mode_str = params.get("blend_mode", "depth")
        b_idx = 0
        if b_mode_str == "uniform": b_idx = 1
        elif b_mode_str == "radial": b_idx = 2
        elif b_mode_str == "custom": b_idx = 3
        
        # Map sub dictionaries to static arrays
        dict_a = params.get("effect_a_params", {})
        dict_b = params.get("effect_b_params", {})
        v4_a = self._parse_params_to_vec4(ea_str, dict_a)
        v4_b = self._parse_params_to_vec4(eb_str, dict_b)
        
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "effect_a_type"), ea_idx)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "effect_b_type"), eb_idx)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "blend_mode"), b_idx)
        
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "blend_threshold"), float(params.get("blend_threshold", 0.5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "blend_transition"), float(params.get("blend_transition", 0.2)))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "invert_blend"), 1 if params.get("invert_blend", False) else 0)
        
        gl.glUniform4f(gl.glGetUniformLocation(self.prog, "params_a"), v4_a[0], v4_a[1], v4_a[2], v4_a[3])
        gl.glUniform4f(gl.glGetUniformLocation(self.prog, "params_b"), v4_b[0], v4_b[1], v4_b[2], v4_b[3])

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
            logger.error(f"Cleanup Error in DepthDual: {e}")
