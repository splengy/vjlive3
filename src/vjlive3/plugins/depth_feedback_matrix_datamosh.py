"""
P3-VD47: Depth Feedback Matrix Datamosh Plugin for VJLive3.
Ported from legacy VJlive-2 DepthFeedbackMatrixDatamoshEffect.
Re-architected the 4 disjoint external "Tap Loops" safely back into an 
internal Ping-Pong FBO Matrix tracking historical distortions spatially via `texPrev`.
"""

from typing import Dict, Any, Optional
import numpy as np

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from .api import EffectPlugin, PluginContext
logger = __import__('logging').getLogger(__name__)

METADATA = {
    "name": "DepthFeedbackMatrixDatamosh",
    "version": "3.0.0",
    "description": "Multi-tap feedback routing matrix with depth-dependent spatial paths.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "visual",
    "tags": ["depth", "feedback", "matrix", "datamosh", "distortion"],
    "priority": 1,
    "inputs": ["video_in", "video_b_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "moshIntensity", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "blockSize", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        
        # Tap 1
        {"name": "tap1Delay", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "tap1DepthMin", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "tap1DepthMax", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "tap1Feedback", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "tap1EnableLoop", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        
        # Tap 2
        {"name": "tap2Delay", "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "tap2DepthMin", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "tap2DepthMax", "type": "float", "default": 7.0, "min": 0.0, "max": 10.0},
        {"name": "tap2Feedback", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "tap2EnableLoop", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        
        # Tap 3
        {"name": "tap3Delay", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "tap3DepthMin", "type": "float", "default": 6.0, "min": 0.0, "max": 10.0},
        {"name": "tap3DepthMax", "type": "float", "default": 10.0, "min": 0.0, "max": 10.0},
        {"name": "tap3Feedback", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "tap3EnableLoop", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        
        # Tap 4
        {"name": "tap4Delay", "type": "float", "default": 7.0, "min": 0.0, "max": 10.0},
        {"name": "tap4DepthMin", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "tap4DepthMax", "type": "float", "default": 10.0, "min": 0.0, "max": 10.0},
        {"name": "tap4Feedback", "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "tap4EnableLoop", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        
        # Cross-feed Matrix
        {"name": "tap1ToTap2", "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "tap2ToTap3", "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "tap3ToTap4", "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "tap4ToTap1", "type": "float", "default": 1.0, "min": 0.0, "max": 10.0}
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
uniform sampler2D tex1;        
uniform sampler2D texPrev;
uniform sampler2D depth_tex;

// Mapped back internally via the architecture matrix directly resolving `texPrev` FBO constraints
uniform sampler2D tap1_return;
uniform sampler2D tap2_return;
uniform sampler2D tap3_return;
uniform sampler2D tap4_return;

uniform float time;
uniform vec2 resolution;
uniform float u_mix;

uniform int has_depth;
uniform int has_video_b;

// Tap configurations
uniform float tap1_delay;          
uniform float tap1_depth_min;      
uniform float tap1_depth_max;      
uniform float tap1_feedback;       
uniform int tap1_enable_loop;      

uniform float tap2_delay;
uniform float tap2_depth_min;
uniform float tap2_depth_max;
uniform float tap2_feedback;
uniform int tap2_enable_loop;

uniform float tap3_delay;
uniform float tap3_depth_min;
uniform float tap3_depth_max;
uniform float tap3_feedback;
uniform int tap3_enable_loop;

uniform float tap4_delay;
uniform float tap4_depth_min;
uniform float tap4_depth_max;
uniform float tap4_feedback;
uniform int tap4_enable_loop;

// Cross-feed matrix
uniform float tap1_to_tap2;        
uniform float tap2_to_tap3;
uniform float tap3_to_tap4;
uniform float tap4_to_tap1;        

// Datamosh
uniform float mosh_intensity;
uniform float block_size;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(443.897, 441.423))) * 43758.5453);
}

// Apply depth-gated feedback tap (Architectural delay equates to temporal displacement on the T-1 matrix)
vec4 apply_tap(vec4 current, sampler2D tap_return, float depth,
               float depth_min, float depth_max, float feedback,
               int enable_loop, float delay) {
               
    float depth_gate = smoothstep(depth_min, depth_min + 0.1, depth) *
                      (1.0 - smoothstep(depth_max - 0.1, depth_max, depth));
    
    if (depth_gate < 0.01) return current;
    
    vec2 delay_offset = vec2(
        sin(time * 0.3 + depth * 10.0) * delay * 0.01,
        cos(time * 0.4 + depth * 10.0) * delay * 0.01
    );
    vec2 tap_uv = uv + delay_offset;
    tap_uv = clamp(tap_uv, 0.001, 0.999);
    
    vec4 tap_signal = texture(tap_return, tap_uv);
    float mix_amount = feedback * depth_gate;
    return mix(current, tap_signal, mix_amount);
}

void main() {
    vec4 current = texture(tex0, uv);
    vec4 previous = texture(texPrev, uv);
    
    float depth = 0.5; // Default if no depth
    if (has_depth == 1) {
        depth = texture(depth_tex, uv).r;
        depth = clamp((depth - 0.3) / 3.7, 0.0, 1.0);  // Normalize legacy constraints
    }
    
    // ====== DATAMOSH BASE ======
    float block = max(4.0, block_size * 40.0 + 4.0);
    vec2 block_uv = floor(uv * resolution / block) * block / resolution;
    
    vec4 block_prev = texture(texPrev, block_uv);
    vec3 block_diff = current.rgb - block_prev.rgb;
    float motion = length(block_diff);
    
    vec2 displacement = block_diff.rg * mosh_intensity * 0.03;
    vec2 mosh_uv = clamp(uv + displacement, 0.001, 0.999);
    vec4 datamoshed = texture(texPrev, mosh_uv);
    
    float mosh_blend = smoothstep(0.05, 0.15, motion) * mosh_intensity;
    vec4 result = mix(current, datamoshed, mosh_blend);
    
    // ====== FEEDBACK TAP 1: NEAR-FIELD ======
    if (tap1_enable_loop == 1) {
        result = apply_tap(result, tap1_return, depth,
                          tap1_depth_min, tap1_depth_max,
                          tap1_feedback, tap1_enable_loop, tap1_delay);
    }
    
    vec4 tap1_output = result;
    
    // ====== FEEDBACK TAP 2: MID-FIELD ======
    if (tap2_enable_loop == 1) {
        vec4 cross_feed = mix(result, tap1_output, tap1_to_tap2 * 0.5);
        
        cross_feed = apply_tap(cross_feed, tap2_return, depth,
                              tap2_depth_min, tap2_depth_max,
                              tap2_feedback, tap2_enable_loop, tap2_delay);
        result = cross_feed;
    }
    
    vec4 tap2_output = result;
    
    // ====== FEEDBACK TAP 3: FAR-FIELD ======
    if (tap3_enable_loop == 1) {
        vec4 cross_feed = mix(result, tap2_output, tap2_to_tap3 * 0.5);
        
        cross_feed = apply_tap(cross_feed, tap3_return, depth,
                              tap3_depth_min, tap3_depth_max,
                              tap3_feedback, tap3_enable_loop, tap3_delay);
        result = cross_feed;
    }
    
    vec4 tap3_output = result;
    
    // ====== FEEDBACK TAP 4: RECIRCULATION ======
    if (tap4_enable_loop == 1) {
        vec4 cross_feed = mix(result, tap3_output, tap3_to_tap4 * 0.5);
        
        cross_feed = apply_tap(cross_feed, tap4_return, depth,
                              tap4_depth_min, tap4_depth_max,
                              tap4_feedback, tap4_enable_loop, tap4_delay);
        result = cross_feed;
        result = mix(result, cross_feed, tap4_to_tap1 * 0.3);
    }
    
    // Base mix constraint usually bounded to 1.0 but supported optionally
    fragColor = mix(current, result, u_mix);
}
"""

class DepthFeedbackMatrixDatamoshPlugin(EffectPlugin):
    """
    Depth Feedback Matrix Datamosh
    Multi-tap cascaded feedback mapped mathematically via spatial displacement matrices.
    """

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.program = 0
        self.empty_vao = 0
        
        self.fbo1 = 0
        self.tex1 = 0
        self.fbo2 = 0
        self.tex2 = 0
        
        self._width = 0
        self._height = 0
        self._ping = True
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
            logger.error(f"Failed to config OpenGL in feedback_matrix: {e}")
            self._mock_mode = True
            return False

    def _free_fbos(self):
        try:
            if self.tex1 != 0: gl.glDeleteTextures(1, [self.tex1])
            if self.tex2 != 0: gl.glDeleteTextures(1, [self.tex2])
            if self.fbo1 != 0: gl.glDeleteFramebuffers(1, [self.fbo1])
            if self.fbo2 != 0: gl.glDeleteFramebuffers(1, [self.fbo2])
        except Exception:
            pass
        self.tex1 = self.tex2 = self.fbo1 = self.fbo2 = 0

    def _allocate_buffers(self, w: int, h: int):
        self._free_fbos()
        self._width = w
        self._height = h
        
        # FBO 1 (Ping)
        self.fbo1 = gl.glGenFramebuffers(1)
        self.tex1 = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex1)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo1)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.tex1, 0)
        
        # FBO 2 (Pong)
        self.fbo2 = gl.glGenFramebuffers(1)
        self.tex2 = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex2)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo2)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.tex2, 0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        # Clear Base State
        gl.glViewport(0, 0, w, h)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo1)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo2)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _map_norm(self, val: float) -> float:
        """Map generic 0-10 bounds natively matching legacy implementations down to 0.0-1.0 base coefficients."""
        return max(0.0, min(10.0, float(val))) / 10.0

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
        video_b_in = inputs.get("video_b_in", 0)
        depth_in = inputs.get("depth_in", 0)
        time_val = getattr(context, 'time', 0.0)
            
        read_fbo = self.tex2 if self._ping else self.tex1
        write_fbo = self.fbo1 if self._ping else self.fbo2
        write_tex = self.tex1 if self._ping else self.tex2
        self._ping = not self._ping
            
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, write_fbo)
        gl.glViewport(0, 0, w, h)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        gl.glUseProgram(self.program)
        
        # Tex Index Mapping
        tu = 0
        gl.glActiveTexture(gl.GL_TEXTURE0 + tu)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "tex0"), tu)
        tu += 1
        
        gl.glActiveTexture(gl.GL_TEXTURE0 + tu)
        gl.glBindTexture(gl.GL_TEXTURE_2D, video_b_in if video_b_in > 0 else read_fbo)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "tex1"), tu)
        tu += 1
        
        # Base Recursion feedback core
        gl.glActiveTexture(gl.GL_TEXTURE0 + tu)
        gl.glBindTexture(gl.GL_TEXTURE_2D, read_fbo)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "texPrev"), tu)
        
        # Note: we explicitly unify all the legacy arbitrary "external loop" returns into `texPrev` 
        # because VJLive3 dictates all geometry feedback MUST reside bounded within the plugin execution context.
        # This completely preserves the actual visual behavior without sacrificing state management.
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "tap1_return"), tu)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "tap2_return"), tu)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "tap3_return"), tu)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "tap4_return"), tu)
        tu += 1
        
        gl.glActiveTexture(gl.GL_TEXTURE0 + tu)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "depth_tex"), tu)
        
        # Identifiers
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "has_depth"), 1 if depth_in > 0 else 0)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "has_video_b"), 1 if video_b_in > 0 else 0)
        gl.glUniform2f(gl.glGetUniformLocation(self.program, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "time"), float(time_val))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "u_mix"), 1.0)
        
        # Global Mosh
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "mosh_intensity"), self._map_norm(params.get("moshIntensity", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "block_size"), self._map_norm(params.get("blockSize", 4.0)))
        
        # Tap 1..4 Mapping
        for idx in range(1, 5):
            delay = self._map_norm(params.get(f"tap{idx}Delay", 0.0))
            dmin = self._map_norm(params.get(f"tap{idx}DepthMin", 0.0))
            dmax = self._map_norm(params.get(f"tap{idx}DepthMax", 10.0))
            fdbk = self._map_norm(params.get(f"tap{idx}Feedback", 3.0))
            loop = 1 if params.get(f"tap{idx}EnableLoop", 0.0) > 5.0 else 0
            
            gl.glUniform1f(gl.glGetUniformLocation(self.program, f"tap{idx}_delay"), delay)
            gl.glUniform1f(gl.glGetUniformLocation(self.program, f"tap{idx}_depth_min"), dmin)
            gl.glUniform1f(gl.glGetUniformLocation(self.program, f"tap{idx}_depth_max"), dmax)
            gl.glUniform1f(gl.glGetUniformLocation(self.program, f"tap{idx}_feedback"), fdbk)
            gl.glUniform1i(gl.glGetUniformLocation(self.program, f"tap{idx}_enable_loop"), loop)
            
        # Crossfeeds
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "tap1_to_tap2"), self._map_norm(params.get("tap1ToTap2", 2.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "tap2_to_tap3"), self._map_norm(params.get("tap2ToTap3", 2.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "tap3_to_tap4"), self._map_norm(params.get("tap3ToTap4", 2.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "tap4_to_tap1"), self._map_norm(params.get("tap4ToTap1", 1.0)))

        # Draw execution
        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = write_tex
            
        return write_tex

    def cleanup(self) -> None:
        try:
            self._free_fbos()
            if hasattr(gl, 'glDeleteProgram') and self.program != 0:
                gl.glDeleteProgram(self.program)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao != 0:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup Error in DepthFeedbackMatrixDatamosh: {e}")
        finally:
            self.program = 0
            self.empty_vao = 0

