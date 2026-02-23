import os
import logging
from typing import Dict, Any, Optional
import numpy as np


logger = logging.getLogger(__name__)

try:
    if os.environ.get("PYTEST_MOCK_GL"):
        raise ImportError("Forced MOCK GL for pytest")
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
    gl = None

DEPTH_LOOP_INJECTION_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;

uniform sampler2D pre_loop_return;
uniform sampler2D depth_loop_return;
uniform sampler2D mosh_loop_return;
uniform sampler2D post_loop_return;

uniform vec2 resolution;
uniform float u_mix;

uniform int enable_pre_loop;
uniform float pre_loop_mix;
uniform int enable_depth_loop;
uniform float depth_loop_mix;
uniform int enable_mosh_loop;
uniform float mosh_loop_mix;
uniform int enable_post_loop;
uniform float post_loop_mix;

uniform float depth_modulation;
uniform float depth_threshold;
uniform int invert_depth;
uniform float mosh_intensity;
uniform float mosh_threshold;
uniform float block_size;
uniform float feedback_amount;

void main() {
    vec4 signal = texture(tex0, v_uv);
    vec4 previous = texture(texPrev, v_uv);
    float depth = texture(depth_tex, v_uv).r;
    
    vec4 stage1_output = signal;
    if (enable_pre_loop == 1) {
        vec4 loop_return = texture(pre_loop_return, v_uv);
        stage1_output = mix(stage1_output, loop_return, pre_loop_mix);
    }
    
    float depth_factor = clamp((depth - 0.3) / 3.7, 0.0, 1.0);
    if (invert_depth == 1) depth_factor = 1.0 - depth_factor;
    float modulated_intensity = mix(0.3, 1.0, depth_factor * depth_modulation);
    
    vec4 stage2_output = stage1_output;
    if (enable_depth_loop == 1) {
        vec4 loop_return = texture(depth_loop_return, v_uv);
        stage2_output = mix(stage2_output, loop_return, depth_loop_mix);
    }
    
    float block = max(4.0, block_size * 40.0 + 4.0);
    vec2 block_uv = floor(v_uv * resolution / block) * block / resolution;
    
    vec3 block_diff = texture(tex0, block_uv).rgb - texture(texPrev, block_uv).rgb;
    float motion = length(block_diff);
    
    vec2 displacement = vec2(0.0);
    if (motion > mosh_threshold * 0.1) {
        displacement = block_diff.rg * modulated_intensity * mosh_intensity * 0.05;
    }
    
    vec2 mosh_uv = clamp(v_uv + displacement, 0.001, 0.999);
    vec4 datamoshed = texture(texPrev, mosh_uv);
    
    float blend_factor = smoothstep(mosh_threshold * 0.05, mosh_threshold * 0.15, motion) * modulated_intensity;
    vec4 mosh_result = mix(stage2_output, datamoshed, blend_factor);
    
    vec4 stage3_output = mosh_result;
    if (enable_mosh_loop == 1) {
        vec4 loop_return = texture(mosh_loop_return, v_uv);
        stage3_output = mix(stage3_output, loop_return, mosh_loop_mix);
    }
    
    vec4 with_feedback = mix(stage3_output, previous, feedback_amount * 0.5);
    
    vec4 stage4_output = with_feedback;
    if (enable_post_loop == 1) {
        vec4 loop_return = texture(post_loop_return, v_uv);
        stage4_output = mix(stage4_output, loop_return, post_loop_mix);
    }
    
    fragColor = mix(signal, stage4_output, u_mix);
}
"""

METADATA = {
    "name": "Depth Loop Injection",
    "description": "Routeable datamosh with explicit send/return loops.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["datamosh", "loop"],
    "status": "active",
    "parameters": [
        {"name": "pre_loop_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "depth_loop_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "mosh_loop_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "post_loop_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "datamosh_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "feedback_amount", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "depth_modulation", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "mosh_threshold", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "block_size", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "invert_depth", "type": "bool", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0},
    ],
    "inputs": ["video_in", "depth_in", "pre_return", "depth_return", "mosh_return", "post_return"],
    "outputs": ["video_out", "pre_send", "depth_send", "mosh_send", "post_send"]
}

class DepthLoopInjectionPlugin(object):
    """Modular routing hub effect providing 4 distinct send/return loops for datamoshing via depths."""
    
    def __init__(self) -> None:
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.ping_pong = 0
        
        self.textures: Dict[str, Optional[int]] = {
            "pre_send": None, "depth_send": None, "mosh_send": None, "post_send": None,
            "feedback_0": None, "feedback_1": None
        }
        self.fbos: Dict[str, Optional[int]] = {
            "pre_send": None, "depth_send": None, "mosh_send": None, "post_send": None,
            "feedback_0": None, "feedback_1": None
        }

    def _compile_shader(self):
        if not HAS_GL: return None
        try:
            vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
            gl.glShaderSource(vertex, "#version 330 core\\nlayout(location=0) in vec2 pos; layout(location=1) in vec2 uv; out vec2 v_uv; void main() { gl_Position = vec4(pos, 0.0, 1.0); v_uv = uv; }")
            gl.glCompileShader(vertex)
            
            fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fragment, DEPTH_LOOP_INJECTION_FRAGMENT)
            gl.glCompileShader(fragment)
            
            if gl.glGetShaderiv(fragment, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
                logger.error(f"Fragment compile failed: {gl.glGetShaderInfoLog(fragment)}")
                return None
                
            prog = gl.glCreateProgram()
            gl.glAttachShader(prog, vertex)
            gl.glAttachShader(prog, fragment)
            gl.glLinkProgram(prog)
            return prog
        except Exception as e:
            logger.error(f"Failed to compile shader locally: {e}")
            return None

    def initialize(self, context) -> None:
        super().initialize(context)
        if self._mock_mode:
            return
            
        try:
            self.prog = self._compile_shader()
            if not self.prog:
                self._mock_mode = True
                return

            tex_ids = gl.glGenTextures(6)
            fbo_ids = gl.glGenFramebuffers(6)
            if isinstance(tex_ids, int): tex_ids = [tex_ids]
            if isinstance(fbo_ids, int): fbo_ids = [fbo_ids]
                
            keys = list(self.textures.keys())
            for i, key in enumerate(keys):
                self.textures[key] = tex_ids[i]
                self.fbos[key] = fbo_ids[i]
                
            # Initialize geometry for drawing
            self.vao = gl.glGenVertexArrays(1)
            self.vbo = gl.glGenBuffers(1)
            gl.glBindVertexArray(self.vao)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
            
            quad_data = np.array([
                -1.0, -1.0,  0.0, 0.0,
                 1.0, -1.0,  1.0, 0.0,
                -1.0,  1.0,  0.0, 1.0,
                 1.0,  1.0,  1.0, 1.0
            ], dtype=np.float32)
            
            gl.glBufferData(gl.GL_ARRAY_BUFFER, quad_data.nbytes, quad_data, gl.GL_STATIC_DRAW)
            gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(0))
            gl.glEnableVertexAttribArray(0)
            gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(8))
            gl.glEnableVertexAttribArray(1)
            gl.glBindVertexArray(0)
            
        except Exception as e:
            logger.warning(f"Failed to initialize GL FBOs inside DepthLoopInjection: {e}")
            self._mock_mode = True

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if input_texture is None or input_texture == 0:
            return 0
            
        pre_mix = params.get("pre_loop_mix", 0.0)
        depth_mix = params.get("depth_loop_mix", 0.0)
        mosh_mix = params.get("mosh_loop_mix", 0.0)
        post_mix = params.get("post_loop_mix", 0.0)
        
        if self._mock_mode:
            return self._mock_passthrough(context, input_texture, pre_mix, depth_mix, mosh_mix, post_mix)

        # Draw call
        try:
            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            h = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_HEIGHT)
            
            # Setup FBOs dynamically if sizes change
            current_fbo = self.fbos[f"feedback_{1 - self.ping_pong}"]
            current_tex = self.textures[f"feedback_{1 - self.ping_pong}"]
            
            gl.glBindTexture(gl.GL_TEXTURE_2D, current_tex)
            tex_w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            if tex_w != w:
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, current_fbo)
                gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, current_tex, 0)
                
                # Setup previous frame texture similarly
                prev_tex = self.textures[f"feedback_{self.ping_pong}"]
                gl.glBindTexture(gl.GL_TEXTURE_2D, prev_tex)
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, current_fbo)
            gl.glViewport(0, 0, w, h)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            
            gl.glUseProgram(self.prog)
            
            self._bind_uniforms(params, w, h, context)
            
            # Bind textures
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
            
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.textures[f"feedback_{self.ping_pong}"])
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrev"), 1)
            
            # Draw
            gl.glBindVertexArray(self.vao)
            gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
            gl.glBindVertexArray(0)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            
            self.ping_pong = 1 - self.ping_pong
            return current_tex
            
        except Exception as e:
            logger.error(f"Render failed: {e}")
            return input_texture

    def _bind_uniforms(self, params, w, h, context):
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), params.get("u_mix", 1.0))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "enable_pre_loop"), 1 if params.get("pre_loop_mix", 0)>0 else 0)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "pre_loop_mix"), params.get("pre_loop_mix", 0.0))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "enable_depth_loop"), 1 if params.get("depth_loop_mix", 0)>0 else 0)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_loop_mix"), params.get("depth_loop_mix", 0.0))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "enable_mosh_loop"), 1 if params.get("mosh_loop_mix", 0)>0 else 0)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "mosh_loop_mix"), params.get("mosh_loop_mix", 0.0))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "enable_post_loop"), 1 if params.get("post_loop_mix", 0)>0 else 0)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "post_loop_mix"), params.get("post_loop_mix", 0.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_modulation"), params.get("depth_modulation", 0.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_threshold"), params.get("depth_threshold", 0.5))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "invert_depth"), 1 if params.get("invert_depth", 0.0) else 0)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "mosh_intensity"), params.get("datamosh_intensity", 0.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "mosh_threshold"), params.get("mosh_threshold", 0.3))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "block_size"), params.get("block_size", 0.4))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "feedback_amount"), params.get("feedback_amount", 0.8))

    def _mock_passthrough(self, context, current_tex, pre_mx, depth_mx, mosh_mx, post_mx):
        context.outputs["pre_send"] = current_tex
        mock_pre = context.inputs.get("pre_return")
        current_tex = mock_pre if mock_pre and pre_mx > 0.0 else current_tex
        
        context.outputs["depth_send"] = current_tex
        mock_depth = context.inputs.get("depth_return")
        current_tex = mock_depth if mock_depth and depth_mx > 0.0 else current_tex
        
        context.outputs["mosh_send"] = current_tex
        mock_mosh = context.inputs.get("mosh_return")
        current_tex = mock_mosh if mock_mosh and mosh_mx > 0.0 else current_tex
        
        context.outputs["post_send"] = current_tex
        mock_post = context.inputs.get("post_return")
        current_tex = mock_post if mock_post and post_mx > 0.0 else current_tex
        
        context.outputs["video_out"] = current_tex
        return current_tex

    def cleanup(self) -> None:
        if not self._mock_mode:
            try:
                textures_to_delete = [t for t in self.textures.values() if t is not None]
                if textures_to_delete:
                    gl.glDeleteTextures(len(textures_to_delete), textures_to_delete)
                fbos_to_delete = [f for f in self.fbos.values() if f is not None]
                if fbos_to_delete:
                    gl.glDeleteFramebuffers(len(fbos_to_delete), fbos_to_delete)
                if self.prog:
                    gl.glDeleteProgram(self.prog)
                if hasattr(self, 'vao') and self.vao:
                    gl.glDeleteVertexArrays(1, [self.vao])
                if hasattr(self, 'vbo') and self.vbo:
                    gl.glDeleteBuffers(1, [self.vbo])
            except Exception as e:
                logger.error(f"Error cleaning up FBOs/Textures during DepthLoop unload: {e}")
                
        for k in self.textures:
            self.textures[k] = None
            self.fbos[k] = None

