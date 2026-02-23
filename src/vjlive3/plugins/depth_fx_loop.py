"""
P3-VD50: Depth Fx Loop Plugin for VJLive3.
Ported from legacy VJlive-2 DepthFXLoopEffect.
Implements a modular send/return bus resolving two isolated Fragment Shaders
to emit an external effects pipeline while maintaining internal depth-gated 
temporal feedbacks.
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
    "name": "DepthFxLoop",
    "version": "3.0.0",
    "description": "Effects Send/Return bus with Depth-gated temporal feedback.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "utility",
    "tags": ["depth", "routing", "loop", "feedback", "send", "return"],
    "priority": 1,
    "inputs": ["video_in", "depth_in", "video_b_in"], # video_b_in acts as the FX Return
    "outputs": ["video_out", "video_out_b"],           # video_out_b acts as the FX Send
    "parameters": [
        {"name": "sendMode", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "wetDry", "type": "float", "default": 6.0, "min": 0.0, "max": 10.0},
        {"name": "depthGateMin", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "depthGateMax", "type": "float", "default": 10.0, "min": 0.0, "max": 10.0},
        {"name": "gateSoftness", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "feedbackAmount", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "feedbackDecay", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "feedbackHueDrift", "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "sendBrightness", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "sendSaturation", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "returnBlendMode", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "returnOpacity", "type": "float", "default": 7.0, "min": 0.0, "max": 10.0}
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

SEND_FRAGMENT_SOURCE = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform int has_depth;
uniform float time;
uniform vec2 resolution;

uniform float send_mode;
uniform float send_brightness;
uniform float send_saturation;

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
    vec4 source = texture(tex0, uv);
    if (has_depth == 0) {
        fragColor = source;
        return;
    }

    float depth = texture(depth_tex, uv).r;
    depth = clamp((depth - 0.3) / 3.7, 0.0, 1.0);

    vec3 result = source.rgb;

    if (send_mode < 3.3) {
        result *= pow(2.0, (send_brightness - 0.5) * 2.0);
    }
    else if (send_mode < 6.6) {
        float mask = smoothstep(0.2, 0.4, depth) * (1.0 - smoothstep(0.6, 0.8, depth));
        result *= mask;
    }
    else {
        vec2 grad;
        float t = 2.0 / resolution.x;
        grad.x = texture(depth_tex, uv + vec2(t, 0)).r - texture(depth_tex, uv - vec2(t, 0)).r;
        grad.y = texture(depth_tex, uv + vec2(0, t)).r - texture(depth_tex, uv - vec2(0, t)).r;
        vec2 displaced_uv = uv + grad * 0.05;
        result = texture(tex0, clamp(displaced_uv, 0.001, 0.999)).rgb;
    }

    vec3 hsv = rgb2hsv(clamp(result, 0.0, 1.0));
    hsv.y *= send_saturation * 2.0;
    hsv.y = clamp(hsv.y, 0.0, 1.0);
    result = hsv2rgb(hsv);

    fragColor = vec4(result, 1.0);
}
"""

LOOP_FRAGMENT_SOURCE = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;           
uniform sampler2D texPrev;        
uniform sampler2D depth_tex;      
uniform sampler2D fx_return_tex;  
uniform int has_depth;

uniform float time;
uniform vec2 resolution;
uniform float wet_dry;             
uniform float depth_gate_min;      
uniform float depth_gate_max;      
uniform float gate_softness;       

uniform float feedback_amount;     
uniform float feedback_decay;      
uniform float feedback_hue_drift;  

uniform float return_blend_mode;   
uniform float return_opacity;      

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

vec3 blend(vec3 base, vec3 layer, float mode) {
    vec3 result;
    if (mode < 3.3) {
        result = layer;
    } else if (mode < 6.6) {
        result = 1.0 - (1.0 - base) * (1.0 - layer);
    } else if (mode < 8.3) {
        result = base * layer;
    } else {
        result = abs(base - layer);
    }
    return result;
}

void main() {
    vec4 source = texture(tex0, uv);
    vec4 prev = texture(texPrev, uv);
    vec4 fx_ret = texture(fx_return_tex, uv);

    if (has_depth == 0) {
        fragColor = source;
        return;
    }

    float depth = texture(depth_tex, uv).r;
    depth = clamp((depth - 0.3) / 3.7, 0.0, 1.0);

    float gate = smoothstep(depth_gate_min - gate_softness * 0.1,
                           depth_gate_min + gate_softness * 0.1, depth) *
                 (1.0 - smoothstep(depth_gate_max - gate_softness * 0.1,
                                   depth_gate_max + gate_softness * 0.1, depth));

    vec3 feedback = prev.rgb;
    if (feedback_amount > 0.0) {
        feedback *= (1.0 - feedback_decay * 0.1);
        if (feedback_hue_drift > 0.0) {
            vec3 fb_hsv = rgb2hsv(clamp(feedback, 0.0, 1.0));
            fb_hsv.x = fract(fb_hsv.x + feedback_hue_drift * 0.02);
            feedback = hsv2rgb(fb_hsv);
        }
    }

    vec3 returned = fx_ret.rgb;
    vec3 blended = blend(source.rgb, returned, return_blend_mode);
    blended = mix(source.rgb, blended, gate * return_opacity);
    
    vec3 result = mix(source.rgb, blended, wet_dry);

    if (feedback_amount > 0.0) {
        result = mix(result, feedback, feedback_amount * 0.5);
    }

    fragColor = vec4(clamp(result, 0.0, 1.5), 1.0);
}
"""

class DepthFxLoopPlugin(object):
    """Depth FX Loop mapping Send/Return matrices safely within internal FBOs."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.send_program = 0
        self.loop_program = 0
        self.empty_vao = 0
        
        self.fbo1 = 0
        self.tex1 = 0
        self.fbo2 = 0
        self.tex2 = 0
        
        self.send_fbo = 0
        self.send_texture = 0
        
        self.is_fbo1_active = True
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
            self.send_program = self._compile_shader(VERTEX_SHADER_SOURCE, SEND_FRAGMENT_SOURCE)
            self.loop_program = self._compile_shader(VERTEX_SHADER_SOURCE, LOOP_FRAGMENT_SOURCE)
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to config OpenGL in depth_fx_loop: {e}")
            self._mock_mode = True
            return False

    def _free_fbo(self):
        try:
            if self.tex1 != 0: gl.glDeleteTextures(1, [self.tex1])
            if self.tex2 != 0: gl.glDeleteTextures(1, [self.tex2])
            if self.send_texture != 0: gl.glDeleteTextures(1, [self.send_texture])
            if self.fbo1 != 0: gl.glDeleteFramebuffers(1, [self.fbo1])
            if self.fbo2 != 0: gl.glDeleteFramebuffers(1, [self.fbo2])
            if self.send_fbo != 0: gl.glDeleteFramebuffers(1, [self.send_fbo])
        except Exception:
            pass
        self.fbo1 = self.fbo2 = self.send_fbo = 0
        self.tex1 = self.tex2 = self.send_texture = 0

    def _create_fbo_tex(self, w: int, h: int):
        fbo = gl.glGenFramebuffers(1)
        tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
        
        # Initialize black
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        return fbo, tex

    def _allocate_buffers(self, w: int, h: int):
        self._free_fbo()
        self._width = w
        self._height = h
        self.fbo1, self.tex1 = self._create_fbo_tex(w, h)
        self.fbo2, self.tex2 = self._create_fbo_tex(w, h)
        self.send_fbo, self.send_texture = self._create_fbo_tex(w, h)

    def _map_norm(self, val: float, max_v: float = 1.0) -> float:
        """Map generic 0-10 bounds to a safe GLSL multiplier."""
        return (max(0.0, min(10.0, float(val))) / 10.0) * max_v

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0:
            return 0
             
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
                context.outputs["video_out_b"] = input_texture
            return input_texture
            
        if not self._initialized:
            self.initialize(context)
            
        w = getattr(context, 'width', 1920)
        h = getattr(context, 'height', 1080)
        
        if w != self._width or h != self._height:
            self._allocate_buffers(w, h)
            
        inputs = getattr(context, "inputs", {})
        depth_in = inputs.get("depth_in", 0)
        
        # If no explicit return connected, fallback loop return to standard video
        video_b_in = inputs.get("video_b_in", input_texture)
        if video_b_in <= 0:
            video_b_in = input_texture
            
        time_val = getattr(context, 'time', 0.0)
        
        read_fbo = self.tex1 if self.is_fbo1_active else self.tex2
        write_fbo = self.fbo2 if self.is_fbo1_active else self.fbo1
        write_texture = self.tex2 if self.is_fbo1_active else self.tex1
        
        # ================================
        # PASS 1: Generate SEND Signal
        # ================================
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.send_fbo)
        gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.send_program)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.send_program, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.send_program, "depth_tex"), 1)
        
        gl.glUniform1i(gl.glGetUniformLocation(self.send_program, "has_depth"), 1 if depth_in > 0 else 0)
        gl.glUniform2f(gl.glGetUniformLocation(self.send_program, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.send_program, "time"), float(time_val))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.send_program, "send_mode"), self._map_norm(params.get("sendMode", 0.0), 10.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.send_program, "send_brightness"), self._map_norm(params.get("sendBrightness", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.send_program, "send_saturation"), self._map_norm(params.get("sendSaturation", 5.0)))

        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)

        # ================================
        # PASS 2: COMPOSITE (Loop Return)
        # ================================
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, write_fbo)
        gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.loop_program)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.loop_program, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.loop_program, "depth_tex"), 1)
        
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, read_fbo)
        gl.glUniform1i(gl.glGetUniformLocation(self.loop_program, "texPrev"), 2)

        gl.glActiveTexture(gl.GL_TEXTURE3)
        gl.glBindTexture(gl.GL_TEXTURE_2D, video_b_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.loop_program, "fx_return_tex"), 3)

        gl.glUniform1i(gl.glGetUniformLocation(self.loop_program, "has_depth"), 1 if depth_in > 0 else 0)
        gl.glUniform2f(gl.glGetUniformLocation(self.loop_program, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.loop_program, "time"), float(time_val))

        gl.glUniform1f(gl.glGetUniformLocation(self.loop_program, "wet_dry"), self._map_norm(params.get("wetDry", 6.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.loop_program, "depth_gate_min"), self._map_norm(params.get("depthGateMin", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.loop_program, "depth_gate_max"), self._map_norm(params.get("depthGateMax", 10.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.loop_program, "gate_softness"), self._map_norm(params.get("gateSoftness", 3.0)))

        gl.glUniform1f(gl.glGetUniformLocation(self.loop_program, "feedback_amount"), self._map_norm(params.get("feedbackAmount", 4.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.loop_program, "feedback_decay"), self._map_norm(params.get("feedbackDecay", 3.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.loop_program, "feedback_hue_drift"), self._map_norm(params.get("feedbackHueDrift", 2.0)))

        gl.glUniform1f(gl.glGetUniformLocation(self.loop_program, "return_blend_mode"), self._map_norm(params.get("returnBlendMode", 0.0), 10.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.loop_program, "return_opacity"), self._map_norm(params.get("returnOpacity", 7.0)))

        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        self.is_fbo1_active = not self.is_fbo1_active

        if hasattr(context, "outputs"):
            context.outputs["video_out"] = write_texture
            context.outputs["video_out_b"] = self.send_texture
            
        return write_texture

    def cleanup(self) -> None:
        try:
            self._free_fbo()
            if hasattr(gl, 'glDeleteProgram'):
                if self.send_program != 0: gl.glDeleteProgram(self.send_program)
                if self.loop_program != 0: gl.glDeleteProgram(self.loop_program)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao != 0:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup Error in DepthFxLoop: {e}")
        finally:
            self.send_program = self.loop_program = 0
            self.empty_vao = 0

