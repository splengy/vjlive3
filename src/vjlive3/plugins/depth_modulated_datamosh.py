"""
P3-VD56: Depth Modulated Datamosh Plugin for VJLive3.
Ported from legacy VJlive-2 DepthModulatedDatamoshEffect.
Single-Pass Dual-Input Pipeline resolving I-Frame datamosh matrices 
mapped to physical depth boundaries handling 11 static parametric bounds.
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
    "name": "DepthModulatedDatamosh",
    "version": "3.0.0",
    "description": "Datamosh with depth-controlled glitch intensity.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "glitch",
    "tags": ["depth", "datamosh", "modulated", "motion", "intensity"],
    "priority": 1,
    "inputs": ["video_in", "depth_in", "video_b_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "depthCurve", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "modStrength", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "minMosh", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "maxMosh", "type": "float", "default": 10.0, "min": 0.0, "max": 10.0},
        {"name": "invertDepth", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "intensity", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "threshold", "type": "float", "default": 1.0, "min": 0.0, "max": 10.0},
        {"name": "blend", "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
        {"name": "blockSize", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "speed", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "feedback", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
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
uniform float time;
uniform vec2 resolution;
uniform int has_depth;

uniform float depth_intensity_curve;  
uniform float modulation_strength;    
uniform float min_datamosh;           
uniform float max_datamosh;           
uniform int invert_depth;             

uniform float intensity;       
uniform float threshold;       
uniform float blend;           
uniform float blockSize;       
uniform float speed;           
uniform float feedback_amount; 

void main() {
    vec4 testB = texture(tex1, vec2(0.5));
    bool hasDualInput = (testB.r + testB.g + testB.b) > 0.01;

    vec4 pixelSource = hasDualInput ? texture(tex1, uv) : texture(tex0, uv);

    float depth = 0.0;
    if (has_depth == 1) depth = texture(depth_tex, uv).r;

    if (invert_depth == 1) depth = 1.0 - depth;
    
    depth = pow(clamp(depth, 0.0, 1.0), max(0.1, 1.0 + depth_intensity_curve * 2.0));
    float moshStrength = mix(min_datamosh, max_datamosh, clamp(depth * modulation_strength, 0.0, 1.0));

    float bs = max(blockSize, 1.0);
    vec2 blockUV = floor(uv * resolution / bs) * bs / resolution;

    vec3 blockCurrent = texture(tex0, blockUV).rgb;
    vec3 blockPrev = texture(texPrev, blockUV).rgb;
    vec3 motionVec = blockCurrent - blockPrev;
    float motion = length(motionVec);

    vec2 displacement = motionVec.rg * intensity * moshStrength * 2.0;
    vec2 moshUV = clamp(uv + displacement, 0.0, 1.0);

    vec4 moshed = hasDualInput ? texture(tex1, moshUV) : texture(texPrev, moshUV);

    float moshFactor = smoothstep(threshold, threshold + 0.05, motion);
    moshFactor *= moshStrength;

    float fb = feedback_amount * moshStrength;

    float totalMosh = clamp(moshFactor * blend + fb, 0.0, 0.95);
    vec4 result = mix(pixelSource, moshed, totalMosh);

    float noise = fract(sin(dot(blockUV * time * speed, vec2(12.9898, 78.233))) * 43758.5453);
    result.rgb += (noise - 0.5) * 0.01 * moshStrength;

    fragColor = vec4(clamp(result.rgb, 0.0, 1.5), 1.0);
}
"""

class DepthModulatedDatamoshPlugin(object):
    """
    Depth Modulated Datamosh single-pass ping-pong feedback loop 
    evaluating dual-video pixel inputs tracking temporal depth constraints natively.
    """

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        
        self.prog = 0
        self.empty_vao = 0
        
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
            self.prog = self._compile_shader(VERTEX_SHADER_SOURCE, FRAGMENT_SHADER_SOURCE)
            
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to config OpenGL in depth_modulated_datamosh: {e}")
            self._mock_mode = True
            return False

    def _free_fbos(self):
        try:
            textures_to_delete = []
            if self.tex_return != 0: textures_to_delete.append(self.tex_return)
            if self.tex_prev != 0: textures_to_delete.append(self.tex_prev)
            if textures_to_delete:
                gl.glDeleteTextures(len(textures_to_delete), textures_to_delete)
                
            fbos_to_delete = []
            if self.fbo_return != 0: fbos_to_delete.append(self.fbo_return)
            if self.fbo_prev != 0: fbos_to_delete.append(self.fbo_prev)
            if fbos_to_delete:
                gl.glDeleteFramebuffers(len(fbos_to_delete), fbos_to_delete)
        except Exception:
            pass
            
        self.tex_return = self.tex_prev = 0
        self.fbo_return = self.fbo_prev = 0

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
        
        self.fbo_return, self.tex_return = self._create_fbo_pair(w, h)
        self.fbo_prev, self.tex_prev = self._create_fbo_pair(w, h)

    def _map_norm(self, val: float, max_v: float = 1.0, min_v: float = 0.0) -> float:
        return min_v + (max(0.0, min(10.0, float(val))) / 10.0) * (max_v - min_v)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
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
        depth_in = inputs.get("depth_in", 0)
        video_b_in = inputs.get("video_b_in", 0)
        time_val = getattr(context, 'time', 0.0)
        
        has_depth_val = 1 if depth_in > 0 else 0
        
        gl.glViewport(0, 0, w, h)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_return)
        gl.glUseProgram(self.prog)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, video_b_in if video_b_in > 0 else input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex1"), 1)

        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_prev)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrev"), 2)

        gl.glActiveTexture(gl.GL_TEXTURE3)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 3)

        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), has_depth_val)
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), float(time_val))

        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_intensity_curve"), self._map_norm(params.get("depthCurve", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "modulation_strength"), self._map_norm(params.get("modStrength", 5.0), max_v=2.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "min_datamosh"), self._map_norm(params.get("minMosh", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "max_datamosh"), self._map_norm(params.get("maxMosh", 10.0)))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "invert_depth"), 1 if params.get("invertDepth", 0.0) > 5.0 else 0)

        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "intensity"), self._map_norm(params.get("intensity", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "threshold"), self._map_norm(params.get("threshold", 1.0), max_v=0.5))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "blend"), self._map_norm(params.get("blend", 8.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "blockSize"), self._map_norm(params.get("blockSize", 5.0), min_v=2.0, max_v=32.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "speed"), self._map_norm(params.get("speed", 5.0), max_v=3.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "feedback_amount"), self._map_norm(params.get("feedback", 0.0)))

        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        
        gl.glBindVertexArray(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        self.tex_return, self.tex_prev = self.tex_prev, self.tex_return
        self.fbo_return, self.fbo_prev = self.fbo_prev, self.fbo_return
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.tex_prev 
            
        return self.tex_prev

    def cleanup(self) -> None:
        try:
            self._free_fbos()
            if hasattr(gl, 'glDeleteProgram') and self.prog != 0:
                gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao != 0:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup Error in DepthModulatedDatamosh: {e}")
        finally:
            self.prog = 0
            self.empty_vao = 0

