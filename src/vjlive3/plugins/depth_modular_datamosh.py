"""
P3-VD55: Depth Modular Datamosh Plugin for VJLive3.
Ported from legacy VJlive-2 DepthModularDatamoshEffect.
Dual-Pass Send/Return framework processing I-Frame corruptions around an 
external FX loop sequence mapping 14 disparate input parameters.
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
    "name": "DepthModularDatamosh",
    "version": "3.0.0",
    "description": "Datamosh with built-in effects insert points wrapping external loops inside corruption.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "glitch",
    "tags": ["depth", "datamosh", "modular", "send", "return", "distortion"],
    "priority": 1,
    "inputs": ["video_in", "depth_in", "video_b_in"],
    "outputs": ["video_out", "video_out_b"],
    "parameters": [
        {"name": "mvIntensity", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "blockSize", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "depthEdgeThresh", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "chromaSplit", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "preWarp", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "preGlitch", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},

        {"name": "corruption", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "feedback", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "feedbackDecay", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "colorCorrupt", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "quantize", "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "scanCorrupt", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "loopWetDry", "type": "float", "default": 7.0, "min": 0.0, "max": 10.0},
        {"name": "depthComposite", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0}
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

STAGE1_FRAGMENT_SOURCE = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;           
uniform sampler2D depth_tex;      
uniform float time;
uniform vec2 resolution;
uniform int has_depth;

uniform float mv_intensity;        
uniform float block_size;          
uniform float depth_edge_thresh;   
uniform float chroma_split;        
uniform float pre_warp;            
uniform float pre_glitch;          

float hash(vec2 p) {
    p = fract(p * vec2(443.897, 441.423));
    p += dot(p, p.yx + 19.19);
    return fract((p.x + p.y) * p.x);
}

void main() {
    float t = 2.0 / resolution.x;
    float dl = 0.0, dr = 0.0, du = 0.0, dd = 0.0;
    
    if (has_depth == 1) {
        dl = texture(depth_tex, uv + vec2(-t, 0)).r;
        dr = texture(depth_tex, uv + vec2( t, 0)).r;
        du = texture(depth_tex, uv + vec2(0, -t)).r;
        dd = texture(depth_tex, uv + vec2(0,  t)).r;
    }

    vec2 depth_grad = vec2(dr - dl, dd - du);
    float edge = length(depth_grad);
    float is_edge = smoothstep(depth_edge_thresh * 0.05, depth_edge_thresh * 0.05 + 0.05, edge);

    vec2 mv = depth_grad * mv_intensity * 0.1;

    float bs = block_size * 8.0 + 4.0;
    vec2 block_uv = floor(uv * resolution / bs) * bs / resolution;
    float block_hash = hash(block_uv + floor(time * 2.0));

    if (is_edge > 0.3 && block_hash > 0.4) {
        mv *= (1.0 + block_hash * 2.0);
    } else {
        mv *= 0.1;
    }

    vec2 displaced_uv = uv + mv;
    displaced_uv = clamp(displaced_uv, 0.001, 0.999);

    if (pre_warp > 0.0) {
        vec2 warp = depth_grad * pre_warp * 0.05;
        displaced_uv += warp;
        displaced_uv = clamp(displaced_uv, 0.001, 0.999);
    }

    vec4 result = texture(tex0, displaced_uv);

    if (chroma_split > 0.0 && is_edge > 0.2) {
        float cs = chroma_split * edge * 0.02;
        result.r = texture(tex0, displaced_uv + vec2(cs, 0.0)).r;
        result.b = texture(tex0, displaced_uv - vec2(cs, 0.0)).b;
    }

    if (pre_glitch > 0.0) {
        float glitch_trigger = step(0.95 - pre_glitch * 0.05, hash(block_uv + time));
        if (glitch_trigger > 0.5) {
            vec2 glitch_offset = (vec2(hash(block_uv * 3.1), hash(block_uv * 7.3)) - 0.5) * 0.1;
            result = texture(tex0, uv + glitch_offset);
        }
    }

    fragColor = result;
}
"""

STAGE2_FRAGMENT_SOURCE = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;           
uniform sampler2D texPrev;        
uniform sampler2D depth_tex;      
uniform sampler2D loop_return;    
uniform float time;
uniform vec2 resolution;
uniform int has_depth;

uniform float corruption;          
uniform float feedback;            
uniform float feedback_decay;      
uniform float color_corrupt;       
uniform float quantize;            
uniform float scan_corrupt;        
uniform float loop_wetdry;         
uniform float depth_composite;     

float hash(vec2 p) {
    p = fract(p * vec2(443.897, 441.423));
    p += dot(p, p.yx + 19.19);
    return fract((p.x + p.y) * p.x);
}

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
    vec4 prev = texture(texPrev, uv);
    float depth = 0.0;
    
    if (has_depth == 1) depth = texture(depth_tex, uv).r;
    
    vec4 looped = texture(loop_return, uv);

    vec3 working = mix(source.rgb, looped.rgb, loop_wetdry);

    if (corruption > 0.0) {
        float bs = 16.0;
        vec2 block_uv = floor(uv * resolution / bs) * bs / resolution;
        float block_h = hash(block_uv + floor(time * 3.0));

        if (block_h > 1.0 - corruption * 0.15) {
            vec2 wrong_block = block_uv + (vec2(
                hash(block_uv * 2.1 + time),
                hash(block_uv * 3.7 + time)
            ) - 0.5) * corruption * 0.2;
            working = texture(loop_return, clamp(wrong_block, 0.001, 0.999)).rgb;
        }
    }

    if (color_corrupt > 0.0) {
        vec2 block_uv = floor(uv * resolution / 8.0) * 8.0 / resolution;
        float ch = hash(block_uv + time * 1.7);

        if (ch > 1.0 - color_corrupt * 0.1) {
            float swap = fract(ch * 7.0);
            if (swap < 0.33) working = working.grb;
            else if (swap < 0.66) working = working.brg;
            else working = working.gbr;
        }

        if (ch > 0.7) {
            vec3 hsv = rgb2hsv(clamp(working, 0.0, 1.0));
            hsv.x = fract(hsv.x + color_corrupt * ch * 0.2);
            working = hsv2rgb(hsv);
        }
    }

    if (quantize > 0.0) {
        float levels = mix(256.0, 4.0, quantize);
        working = floor(working * levels) / levels;
    }

    if (scan_corrupt > 0.0) {
        float line = floor(uv.y * resolution.y);
        float line_h = hash(vec2(line, floor(time * 5.0)));

        if (line_h > 1.0 - scan_corrupt * 0.08) {
            float shift = (line_h - 0.5) * scan_corrupt * 0.1;
            working = texture(loop_return, clamp(vec2(uv.x + shift, uv.y), 0.001, 0.999)).rgb;
        }
    }

    if (feedback > 0.0) {
        vec3 fb = prev.rgb * (1.0 - feedback_decay * 0.1);
        working = mix(working, max(working, fb), feedback * 0.6);
    }

    if (depth_composite > 0.0) {
        float depth_weight = mix(1.0, depth, depth_composite);
        working = mix(source.rgb, working, depth_weight);
    }

    fragColor = vec4(clamp(working, 0.0, 1.5), 1.0);
}
"""


class DepthModularDatamoshPlugin(object):
    """
    Depth Modular Datamosh Dual-Pass Send/Return framework 
    processing external injection matrices cleanly.
    """

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        
        self.prog_stage1 = 0
        self.prog_stage2 = 0
        self.empty_vao = 0
        
        self.fbo_send = 0
        self.tex_send = 0
        
        self.fbo_return = 0
        self.tex_return = 0
        
        self.fbo_prev = 0
        self.tex_prev = 0

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
            self.prog_stage1 = self._compile_shader(VERTEX_SHADER_SOURCE, STAGE1_FRAGMENT_SOURCE)
            self.prog_stage2 = self._compile_shader(VERTEX_SHADER_SOURCE, STAGE2_FRAGMENT_SOURCE)
            
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to config OpenGL in depth_modular_datamosh: {e}")
            self._mock_mode = True
            return False

    def _free_fbos(self):
        try:
            textures_to_delete = []
            if self.tex_send != 0: textures_to_delete.append(self.tex_send)
            if self.tex_return != 0: textures_to_delete.append(self.tex_return)
            if self.tex_prev != 0: textures_to_delete.append(self.tex_prev)
            if textures_to_delete:
                gl.glDeleteTextures(len(textures_to_delete), textures_to_delete)
                
            fbos_to_delete = []
            if self.fbo_send != 0: fbos_to_delete.append(self.fbo_send)
            if self.fbo_return != 0: fbos_to_delete.append(self.fbo_return)
            if self.fbo_prev != 0: fbos_to_delete.append(self.fbo_prev)
            if fbos_to_delete:
                gl.glDeleteFramebuffers(len(fbos_to_delete), fbos_to_delete)
        except Exception:
            pass
            
        self.tex_send = self.tex_return = self.tex_prev = 0
        self.fbo_send = self.fbo_return = self.fbo_prev = 0


    def _create_fbo_pair(self, w: int, h: int) -> tuple:
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
        
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        return fbo, tex

    def _allocate_buffers(self, w: int, h: int):
        self._free_fbos()
        self._width = w
        self._height = h
        
        self.fbo_send, self.tex_send = self._create_fbo_pair(w, h)
        self.fbo_return, self.tex_return = self._create_fbo_pair(w, h)
        self.fbo_prev, self.tex_prev = self._create_fbo_pair(w, h)

    def _map_norm(self, val: float, max_v: float = 1.0, min_v: float = 0.0) -> float:
        return min_v + (max(0.0, min(10.0, float(val))) / 10.0) * (max_v - min_v)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0:
            return 0
             
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"):
                context.outputs["video_out_b"] = input_texture
                context.outputs["video_out"] = input_texture
            return input_texture
            
        if not self._initialized:
            self.initialize(context)
            
        w = getattr(context, 'width', 1920)
        h = getattr(context, 'height', 1080)
        
        if w != self._width or h != self._height:
            self._allocate_buffers(w, h)
            
        inputs = getattr(context, "inputs", {})
        depth_in = inputs.get("depth_in", 0)
        video_b_in = inputs.get("video_b_in", 0)
        time_val = getattr(context, 'time', 0.0)
        
        has_depth_val = 1 if depth_in > 0 else 0
        
        gl.glViewport(0, 0, w, h)
        
        # --- PASS 1: STAGE 1 (SEND) ---
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_send)
        gl.glUseProgram(self.prog_stage1)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_stage1, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_stage1, "depth_tex"), 1)

        gl.glUniform1i(gl.glGetUniformLocation(self.prog_stage1, "has_depth"), has_depth_val)
        gl.glUniform2f(gl.glGetUniformLocation(self.prog_stage1, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage1, "time"), float(time_val))

        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage1, "mv_intensity"), self._map_norm(params.get("mvIntensity", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage1, "block_size"), self._map_norm(params.get("blockSize", 4.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage1, "depth_edge_thresh"), self._map_norm(params.get("depthEdgeThresh", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage1, "chroma_split"), self._map_norm(params.get("chromaSplit", 4.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage1, "pre_warp"), self._map_norm(params.get("preWarp", 3.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage1, "pre_glitch"), self._map_norm(params.get("preGlitch", 3.0)))

        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        
        # --- PASS 2: STAGE 2 (RETURN/MAIN) ---
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_return)
        gl.glUseProgram(self.prog_stage2)
        
        # tex0 = video_in
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_stage2, "tex0"), 0)
        
        # texPrev = self.tex_prev
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_prev)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_stage2, "texPrev"), 1)
        
        # depth_tex = depth_in
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_stage2, "depth_tex"), 2)

        # loop_return = video_b_in (External Loop injection)
        gl.glActiveTexture(gl.GL_TEXTURE3)
        loop_target = video_b_in if video_b_in > 0 else self.tex_send
        gl.glBindTexture(gl.GL_TEXTURE_2D, loop_target)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog_stage2, "loop_return"), 3)

        gl.glUniform1i(gl.glGetUniformLocation(self.prog_stage2, "has_depth"), has_depth_val)
        gl.glUniform2f(gl.glGetUniformLocation(self.prog_stage2, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage2, "time"), float(time_val))

        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage2, "corruption"), self._map_norm(params.get("corruption", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage2, "feedback"), self._map_norm(params.get("feedback", 4.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage2, "feedback_decay"), self._map_norm(params.get("feedbackDecay", 3.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage2, "color_corrupt"), self._map_norm(params.get("colorCorrupt", 3.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage2, "quantize"), self._map_norm(params.get("quantize", 2.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage2, "scan_corrupt"), self._map_norm(params.get("scanCorrupt", 3.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage2, "loop_wetdry"), self._map_norm(params.get("loopWetDry", 7.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog_stage2, "depth_composite"), self._map_norm(params.get("depthComposite", 4.0)))

        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        # Ping-Pong buffers for temporal state loop retention locally
        self.tex_return, self.tex_prev = self.tex_prev, self.tex_return
        self.fbo_return, self.fbo_prev = self.fbo_prev, self.fbo_return
        
        if hasattr(context, "outputs"):
            context.outputs["video_out_b"] = self.tex_send
            context.outputs["video_out"] = self.tex_prev # It is named tex_prev due to swap
            
        return self.tex_prev

    def cleanup(self) -> None:
        try:
            self._free_fbos()
            if hasattr(gl, 'glDeleteProgram'):
                if self.prog_stage1 != 0: gl.glDeleteProgram(self.prog_stage1)
                if self.prog_stage2 != 0: gl.glDeleteProgram(self.prog_stage2)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao != 0:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup Error in DepthModularDatamosh: {e}")
        finally:
            self.prog_stage1 = 0
            self.prog_stage2 = 0
            self.empty_vao = 0

