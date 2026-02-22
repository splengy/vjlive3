import os
import logging
from typing import Dict, Any, Optional
import numpy as np

from vjlive3.plugins.api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

# Mock GL for headless pytests via environment flag injection
try:
    if os.environ.get("PYTEST_MOCK_GL"):
        raise ImportError("Forced MOCK GL for pytest")
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
    gl = None

DEPTH_PARALLEL_UNIVERSE_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform vec2 resolution;
uniform float u_mix;

// We use 3 separate textures for pingpong. They represent the previous state of each universe.
uniform sampler2D texPrevA;
uniform sampler2D texPrevB;
uniform sampler2D texPrevC;
uniform sampler2D depth_tex;

uniform sampler2D universe_a_return;
uniform sampler2D universe_b_return;
uniform sampler2D universe_c_return;

uniform float time;

// Universe A: Near-field aggressive
uniform float universe_a_depth_min;
uniform float universe_a_depth_max;
uniform float universe_a_mosh_intensity;
uniform float universe_a_block_size;
uniform float universe_a_chaos;
uniform int universe_a_enable_loop;
uniform float universe_a_loop_mix;

// Universe B: Mid-field smooth
uniform float universe_b_depth_min;
uniform float universe_b_depth_max;
uniform float universe_b_mosh_intensity;
uniform float universe_b_temporal_blend;
uniform float universe_b_blur;
uniform int universe_b_enable_loop;
uniform float universe_b_loop_mix;

// Universe C: Far-field glitch
uniform float universe_c_depth_min;
uniform float universe_c_depth_max;
uniform float universe_c_glitch_freq;
uniform float universe_c_rgb_split;
uniform float universe_c_corruption;
uniform int universe_c_enable_loop;
uniform float universe_c_loop_mix;

// Reality merging
uniform int merge_mode;
uniform float crossbleed;
uniform float reality_threshold;
uniform float quantum_uncertainty;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(443.897, 441.423))) * 43758.5453);
}

// ==== Universe A ====
vec4 process_universe_a(vec4 current, vec4 previous, float depth, vec2 p) {
    if (universe_a_mosh_intensity < 0.01) return current;
    
    float block = max(4.0, universe_a_block_size * 40.0 + 4.0);
    vec2 block_uv = floor(p * resolution / block) * block / resolution;
    
    vec4 block_prev = texture(texPrevA, block_uv);
    vec3 diff = current.rgb - block_prev.rgb;
    float motion = length(diff);
    
    float block_chaos = hash(block_uv + time);
    vec2 chaos_offset = (vec2(hash(block_uv + 1.1), hash(block_uv + 2.2)) - 0.5) * universe_a_chaos * 0.05;
    
    vec2 displacement = diff.rg * universe_a_mosh_intensity * 0.05 + chaos_offset;
    vec2 mosh_uv = clamp(p + displacement, 0.001, 0.999);
    
    vec4 result = texture(texPrevA, mosh_uv);
    float blend = smoothstep(0.05, 0.15, motion) * universe_a_mosh_intensity;
    return mix(current, result, blend);
}

// ==== Universe B ====
vec4 process_universe_b(vec4 current, vec4 previous, float depth, vec2 p) {
    vec4 blended = mix(current, previous, universe_b_temporal_blend * 0.5);
    if (universe_b_blur < 0.01) return blended;
    
    vec4 blur_accum = vec4(0.0);
    float blur_radius = universe_b_blur * 0.02;
    int samples = int(universe_b_blur * 5.0) + 1;
    
    for (int i = 0; i < 16; i++) {
        if (i >= samples) break;
        float angle = float(i) * 0.3926991;
        float radius = sqrt(float(i) / float(samples)) * blur_radius;
        vec2 offset = vec2(cos(angle), sin(angle)) * radius;
        blur_accum += texture(texPrevB, clamp(p + offset, 0.001, 0.999)) / float(samples);
    }
    
    return mix(blended, blur_accum, universe_b_blur * 0.5);
}

// ==== Universe C ====
vec4 process_universe_c(vec4 current, vec4 previous, float depth, vec2 p) {
    float glitch_trigger = hash(vec2(floor(time * universe_c_glitch_freq * 10.0), depth));
    vec4 result = current;
    
    if (glitch_trigger > 0.7) {
        vec2 r_offset = vec2(universe_c_rgb_split * 0.02, 0.0);
        vec2 b_offset = vec2(-universe_c_rgb_split * 0.02, 0.0);
        result.r = texture(tex0, clamp(p + r_offset, 0.001, 0.999)).r;
        result.b = texture(tex0, clamp(p + b_offset, 0.001, 0.999)).b;
        
        float corrupt = hash(p * 100.0 + time);
        if (corrupt > 1.0 - universe_c_corruption * 0.3) {
            result.rgb = mix(result.rgb, vec3(corrupt), universe_c_corruption * 0.5);
        }
    }
    return mix(result, previous, 0.5); // Provide some trailing artifacts for glitch
}

layout(location = 0) out vec4 out_UniverseA;
layout(location = 1) out vec4 out_UniverseB;
layout(location = 2) out vec4 out_UniverseC;
layout(location = 3) out vec4 out_Merged;

void main() {
    vec4 current = texture(tex0, v_uv);
    vec4 prevA = texture(texPrevA, v_uv);
    vec4 prevB = texture(texPrevB, v_uv);
    vec4 prevC = texture(texPrevC, v_uv);
    
    float depth = texture(depth_tex, v_uv).r;
    depth = clamp((depth - 0.3) / 3.7, 0.0, 1.0);
    
    float uncertain_depth = clamp(depth + (hash(v_uv * 100.0 + time) - 0.5) * quantum_uncertainty * 0.1, 0.0, 1.0);
    
    // Process base universes
    vec4 universe_a = process_universe_a(current, prevA, uncertain_depth, v_uv);
    if (universe_a_enable_loop == 1) {
        universe_a = mix(universe_a, texture(universe_a_return, v_uv), universe_a_loop_mix);
    }
    out_UniverseA = universe_a; // FBO output for pingpong
    
    vec4 universe_b = process_universe_b(current, prevB, uncertain_depth, v_uv);
    if (universe_b_enable_loop == 1) {
        universe_b = mix(universe_b, texture(universe_b_return, v_uv), universe_b_loop_mix);
    }
    out_UniverseB = universe_b; // FBO output for pingpong
    
    vec4 universe_c = process_universe_c(current, prevC, uncertain_depth, v_uv);
    if (universe_c_enable_loop == 1) {
        universe_c = mix(universe_c, texture(universe_c_return, v_uv), universe_c_loop_mix);
    }
    out_UniverseC = universe_c; // FBO output for pingpong
    
    if (crossbleed > 0.0) {
        universe_a = mix(universe_a, universe_b * 0.5 + universe_c * 0.5, crossbleed * 0.3);
        universe_b = mix(universe_b, universe_a * 0.5 + universe_c * 0.5, crossbleed * 0.3);
        universe_c = mix(universe_c, universe_a * 0.5 + universe_b * 0.5, crossbleed * 0.3);
    }
    
    // Merging
    float weight_a = smoothstep(universe_a_depth_min - reality_threshold * 0.1, universe_a_depth_min + reality_threshold * 0.1, uncertain_depth) *
                    (1.0 - smoothstep(universe_a_depth_max - reality_threshold * 0.1, universe_a_depth_max + reality_threshold * 0.1, uncertain_depth));
    float weight_b = smoothstep(universe_b_depth_min - reality_threshold * 0.1, universe_b_depth_min + reality_threshold * 0.1, uncertain_depth) *
                    (1.0 - smoothstep(universe_b_depth_max - reality_threshold * 0.1, universe_b_depth_max + reality_threshold * 0.1, uncertain_depth));
    float weight_c = smoothstep(universe_c_depth_min - reality_threshold * 0.1, universe_c_depth_min + reality_threshold * 0.1, uncertain_depth) *
                    (1.0 - smoothstep(universe_c_depth_max - reality_threshold * 0.1, universe_c_depth_max + reality_threshold * 0.1, uncertain_depth));
                    
    float total_weight = weight_a + weight_b + weight_c + 0.001;
    weight_a /= total_weight; weight_b /= total_weight; weight_c /= total_weight;
    
    vec4 merged;
    if (merge_mode == 0) merged = universe_a * weight_a + universe_b * weight_b + universe_c * weight_c;
    else if (merge_mode == 1) merged = (universe_a * weight_a + universe_b * weight_b + universe_c * weight_c) * 1.2;
    else if (merge_mode == 2) merged = universe_a * universe_b * universe_c * 2.0;
    else merged = max(max(universe_a * weight_a, universe_b * weight_b), universe_c * weight_c);
    
    out_Merged = mix(current, merged, u_mix);
}
"""

METADATA = {
    "name": "Depth Parallel Universe",
    "description": "Splits signal into 3 depth-based universes with independent FX chains.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["datamosh", "split", "universe"],
    "status": "active",
    "parameters": [
        {"name": "depth_split_near", "type": "float", "min": 0.0, "max": 1.0, "default": 0.33},
        {"name": "depth_split_far", "type": "float", "min": 0.0, "max": 1.0, "default": 0.66},
        {"name": "universe_a_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "universe_b_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "universe_c_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        # Expanded routing options matching the legacy schema semantics precisely
        {"name": "merge_mode", "type": "float", "min": 0.0, "max": 3.0, "default": 0.0},
        {"name": "crossbleed", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "reality_threshold", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "quantum_uncertainty", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in", "universe_a_return", "universe_b_return", "universe_c_return"],
    "outputs": ["video_out", "universe_a_send", "universe_b_send", "universe_c_send"]
}

class DepthParallelUniversePlugin(EffectPlugin):
    """3-Way multi-universe routing effect."""
    
    def __init__(self) -> None:
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.ping_pong = 0
        self.time_val = 0.0
        
        self.textures: Dict[str, Optional[int]] = {
            "mrt_a_0": None, "mrt_b_0": None, "mrt_c_0": None, "mrt_out_0": None,
            "mrt_a_1": None, "mrt_b_1": None, "mrt_c_1": None, "mrt_out_1": None
        }
        self.fbos: Dict[str, Optional[int]] = {
            "pong_0": None,
            "pong_1": None,
        }

    def _compile_shader(self):
        if not HAS_GL: return None
        try:
            vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
            gl.glShaderSource(vertex, "#version 330 core\\nlayout(location=0) in vec2 pos; layout(location=1) in vec2 uv; out vec2 v_uv; void main() { gl_Position = vec4(pos, 0.0, 1.0); v_uv = uv; }")
            gl.glCompileShader(vertex)
            
            fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fragment, DEPTH_PARALLEL_UNIVERSE_FRAGMENT)
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

    def initialize(self, context: PluginContext) -> None:
        super().initialize(context)
        if self._mock_mode: return
            
        try:
            self.prog = self._compile_shader()
            if not self.prog:
                self._mock_mode = True
                return

            tex_ids = gl.glGenTextures(8)
            fbo_ids = gl.glGenFramebuffers(2)
            if isinstance(tex_ids, int): tex_ids = [tex_ids]
            if isinstance(fbo_ids, int): fbo_ids = [fbo_ids]
                
            keys = list(self.textures.keys())
            for i, key in enumerate(keys):
                self.textures[key] = tex_ids[i]
                
            self.fbos["pong_0"] = fbo_ids[0]
            if len(fbo_ids) > 1:
                self.fbos["pong_1"] = fbo_ids[1]
                
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
            logger.warning(f"Failed to initialize GL FBOs inside ParallelUniverse: {e}")
            self._mock_mode = True

    def _setup_mrt_fbo(self, fbo_id, w, h, tex_a, tex_b, tex_c, tex_out):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo_id)
        
        for i, tex in enumerate([tex_a, tex_b, tex_c, tex_out]):
            gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0 + i, gl.GL_TEXTURE_2D, tex, 0)
        
        draw_buffers = [
            gl.GL_COLOR_ATTACHMENT0, gl.GL_COLOR_ATTACHMENT1, 
            gl.GL_COLOR_ATTACHMENT2, gl.GL_COLOR_ATTACHMENT3
        ]
        gl.glDrawBuffers(4, draw_buffers)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        near = params.get("depth_split_near", 0.33)
        far = params.get("depth_split_far", 0.66)
        
        intensity_a = params.get("universe_a_intensity", 0.8)
        intensity_b = params.get("universe_b_intensity", 0.5)
        intensity_c = params.get("universe_c_intensity", 0.2)
        
        if near > far:
            near, far = far, near
            
        if input_texture is None or input_texture == 0: return 0 
            
        if self._mock_mode:
            return self._mock_passthrough(context, input_texture, intensity_a, intensity_b, intensity_c)
            
        try:
            self.time_val += context.delta_time if hasattr(context, 'delta_time') else 0.016
            
            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            h = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_HEIGHT)
            
            current_fbo = self.fbos[f"pong_{1 - self.ping_pong}"]
            tex_a = self.textures[f"mrt_a_{1 - self.ping_pong}"]
            tex_b = self.textures[f"mrt_b_{1 - self.ping_pong}"]
            tex_c = self.textures[f"mrt_c_{1 - self.ping_pong}"]
            tex_out = self.textures[f"mrt_out_{1 - self.ping_pong}"]
            
            prev_a = self.textures[f"mrt_a_{self.ping_pong}"]
            prev_b = self.textures[f"mrt_b_{self.ping_pong}"]
            prev_c = self.textures[f"mrt_c_{self.ping_pong}"]
            
            gl.glBindTexture(gl.GL_TEXTURE_2D, tex_a)
            tex_w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            if tex_w != w:
                prev_fbo = self.fbos[f"pong_{self.ping_pong}"]
                self._setup_mrt_fbo(current_fbo, w, h, tex_a, tex_b, tex_c, tex_out)
                self._setup_mrt_fbo(prev_fbo, w, h, prev_a, prev_b, prev_c, self.textures[f"mrt_out_{self.ping_pong}"])
            
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, current_fbo)
            
            draw_buffers = [
                gl.GL_COLOR_ATTACHMENT0, gl.GL_COLOR_ATTACHMENT1, 
                gl.GL_COLOR_ATTACHMENT2, gl.GL_COLOR_ATTACHMENT3
            ]
            gl.glDrawBuffers(4, draw_buffers)
            
            gl.glViewport(0, 0, w, h)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            
            gl.glUseProgram(self.prog)
            
            self._bind_uniforms(params, w, h, near, far, intensity_a, intensity_b, intensity_c)
            
            # Bind textures
            gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
            gl.glActiveTexture(gl.GL_TEXTURE1); gl.glBindTexture(gl.GL_TEXTURE_2D, prev_a)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrevA"), 1)
            gl.glActiveTexture(gl.GL_TEXTURE2); gl.glBindTexture(gl.GL_TEXTURE_2D, prev_b)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrevB"), 2)
            gl.glActiveTexture(gl.GL_TEXTURE3); gl.glBindTexture(gl.GL_TEXTURE_2D, prev_c)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrevC"), 3)
            
            # Draw
            gl.glBindVertexArray(self.vao)
            gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
            gl.glBindVertexArray(0)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            
            # Context delivery of routed sends
            context.outputs["universe_a_send"] = tex_a
            context.outputs["universe_b_send"] = tex_b
            context.outputs["universe_c_send"] = tex_c
            context.outputs["video_out"] = tex_out
            
            self.ping_pong = 1 - self.ping_pong
            return tex_out
            
        except Exception as e:
            logger.error(f"Render failed: {e}")
            return input_texture

    def _bind_uniforms(self, p, w, h, near, far, i_a, i_b, i_c):
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), self.time_val)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), p.get("u_mix", 1.0))
        
        # A
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_a_depth_min"), 0.0)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_a_depth_max"), near)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_a_mosh_intensity"), i_a)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_a_block_size"), p.get("universe_a_block_size", 0.4))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_a_chaos"), p.get("universe_a_chaos", 0.3))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "universe_a_enable_loop"), 1 if p.get("universe_a_intensity", 0)>0 else 0)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_a_loop_mix"), p.get("universe_a_intensity", 0.0))

        # B
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_b_depth_min"), near)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_b_depth_max"), far)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_b_temporal_blend"), p.get("uniBTemporalBlend", 0.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_b_blur"), p.get("uniBBlur", 0.3))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "universe_b_enable_loop"), 1 if p.get("universe_b_intensity", 0)>0 else 0)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_b_loop_mix"), p.get("universe_b_intensity", 0.0))

        # C
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_c_depth_min"), far)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_c_depth_max"), 1.0)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_c_glitch_freq"), p.get("uniCGlitchFreq", 0.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_c_rgb_split"), p.get("uniCRgbSplit", 0.4))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_c_corruption"), p.get("uniCCorruption", 0.4))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "universe_c_enable_loop"), 1 if p.get("universe_c_intensity", 0)>0 else 0)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "universe_c_loop_mix"), p.get("universe_c_intensity", 0.0))

        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "merge_mode"), int(p.get('merge_mode', 0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "crossbleed"), p.get('crossbleed', 0.2))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "reality_threshold"), p.get('reality_threshold', 0.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "quantum_uncertainty"), p.get('quantum_uncertainty', 0.2))

    def _mock_passthrough(self, context, current_tex, int_a, int_b, int_c):
        context.outputs["universe_a_send"] = current_tex
        mock_a = context.inputs.get("universe_a_return")
        current_a = mock_a if mock_a and int_a > 0.0 else current_tex
        
        context.outputs["universe_b_send"] = current_tex
        mock_b = context.inputs.get("universe_b_return")
        current_b = mock_b if mock_b and int_b > 0.0 else current_tex
        
        context.outputs["universe_c_send"] = current_tex
        mock_c = context.inputs.get("universe_c_return")
        current_c = mock_c if mock_c and int_c > 0.0 else current_tex
        
        context.outputs["video_out"] = current_a
        return current_a

    def cleanup(self) -> None:
        if not self._mock_mode:
            try:
                textures_to_delete = [t for t in self.textures.values() if t is not None]
                if textures_to_delete: gl.glDeleteTextures(len(textures_to_delete), textures_to_delete)
                fbos_to_delete = [f for f in self.fbos.values() if f is not None]
                if fbos_to_delete: gl.glDeleteFramebuffers(len(fbos_to_delete), fbos_to_delete)
                if self.prog: gl.glDeleteProgram(self.prog)
                if hasattr(self, 'vao') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
                if hasattr(self, 'vbo') and self.vbo: gl.glDeleteBuffers(1, [self.vbo])
            except Exception as e:
                logger.error(f"Error cleaning up FBOs/Textures during ParallelUniverse unload: {e}")
                
        for k in self.textures: self.textures[k] = None
        for k in self.fbos: self.fbos[k] = None
