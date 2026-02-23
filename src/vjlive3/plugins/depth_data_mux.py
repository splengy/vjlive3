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
    "name": "DepthDataMux",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Combines up to 4 depth sources into a single composite depth stream",
    "plugin_type": "depth_effect",
    "category": "Depth Effects",
    "tags": ["depth", "mux", "composite", "multi-source"],
    "priority": 100,  # Run late to composite processed inputs
    "dependencies": [],
    "incompatible": [],
    "inputs": ["depth1", "depth2", "depth3", "depth4"],
    "outputs": ["composite_depth"],
    "parameters": [
        {"name": "blend_mode", "type": "str", "default": "average", "options": ["average", "max", "min", "priority1", "priority2", "priority3", "priority4"]},
        {"name": "priority_order", "type": "list", "default": [1, 2, 3, 4]},
        {"name": "weight1", "type": "float", "default": 0.25, "min": 0.0, "max": 1.0},
        {"name": "weight2", "type": "float", "default": 0.25, "min": 0.0, "max": 1.0},
        {"name": "weight3", "type": "float", "default": 0.25, "min": 0.0, "max": 1.0},
        {"name": "weight4", "type": "float", "default": 0.25, "min": 0.0, "max": 1.0},
        {"name": "normalize", "type": "bool", "default": True},
        {"name": "fallback_depth", "type": "float", "default": 0.5, "min": 0.0, "max": 1.0}
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

DEPTH_MUX_FRAGMENT = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D depth1;
uniform sampler2D depth2;
uniform sampler2D depth3;
uniform sampler2D depth4;

uniform bvec4 has_source;
uniform int blend_mode; // 0=avg, 1=max, 2=min, 3=priority
uniform int p_winning_idx; // 1, 2, 3, 4
uniform vec4 weights;
uniform bool normalize_w;
uniform float fallback_depth;

void main() {
    float d1 = has_source.x ? texture(depth1, uv).r : 0.0;
    float d2 = has_source.y ? texture(depth2, uv).r : 0.0;
    float d3 = has_source.z ? texture(depth3, uv).r : 0.0;
    float d4 = has_source.w ? texture(depth4, uv).r : 0.0;
    
    int active_cts = int(has_source.x) + int(has_source.y) + int(has_source.z) + int(has_source.w);
    
    if (active_cts == 0) {
        fragColor = vec4(vec3(fallback_depth), 1.0);
        return;
    }
    
    float result = fallback_depth;
    
    if (blend_mode == 0) { // Average
        vec4 w = weights;
        if (normalize_w) {
            float sum = dot(w, vec4(has_source));
            if (sum > 0.0) {
                w /= sum;
            } else {
                w = vec4(1.0) / float(active_cts);
            }
        }
        result = d1 * w.x * float(has_source.x) + 
                 d2 * w.y * float(has_source.y) + 
                 d3 * w.z * float(has_source.z) + 
                 d4 * w.w * float(has_source.w);
        
        if (!normalize_w) {
            float sum = dot(w, vec4(has_source));
            if (sum > 0.0) result /= sum;
        }     
    } 
    else if (blend_mode == 1) { // Max
        result = 0.0;
        if (has_source.x) result = max(result, d1);
        if (has_source.y) result = max(result, d2);
        if (has_source.z) result = max(result, d3);
        if (has_source.w) result = max(result, d4);
    } 
    else if (blend_mode == 2) { // Min
        result = 1.0;
        if (has_source.x) result = min(result, d1);
        if (has_source.y) result = min(result, d2);
        if (has_source.z) result = min(result, d3);
        if (has_source.w) result = min(result, d4);
    } 
    else if (blend_mode == 3) { // Priority
        if (p_winning_idx == 1) result = d1;
        else if (p_winning_idx == 2) result = d2;
        else if (p_winning_idx == 3) result = d3;
        else if (p_winning_idx == 4) result = d4;
    }
    
    fragColor = vec4(vec3(clamp(result, 0.0, 1.0)), 1.0);
}
"""

class DepthDataMuxPlugin(EffectPlugin):
    """
    DepthDataMux composite node for VJLive3.
    Extracts up to 4 input streams and dynamically multiplexes via hardware equations.
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
            logger.error(f"Failed to initialize OpenGL in DepthDataMux: {e}")
            self._mock_mode = True

    def _compile_shader(self):
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"VS Error: {gl.glGetShaderInfoLog(vs)}")

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, DEPTH_MUX_FRAGMENT)
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

    def _bind_uniforms(self, params: Dict[str, Any], has_src: list):
        bm_str = params.get("blend_mode", "average")
        bmode_int = 0
        p_index = 0
        
        if bm_str == "max":
            bmode_int = 1
        elif bm_str == "min":
            bmode_int = 2
        elif bm_str.startswith("priority"):
            bmode_int = 3
            p_order = params.get("priority_order", [1, 2, 3, 4])
            if not isinstance(p_order, list): p_order = [1, 2, 3, 4]
            # find first active
            for p in p_order:
                try:
                    idx = int(p) - 1
                    if 0 <= idx < 4 and has_src[idx]:
                        p_index = idx + 1
                        break
                except (ValueError, TypeError):
                    continue

        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "blend_mode"), bmode_int)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "p_winning_idx"), p_index)
        
        # Array of 4 booleans
        gl.glUniform4i(gl.glGetUniformLocation(self.prog, "has_source"), 
                       1 if has_src[0] else 0,
                       1 if has_src[1] else 0,
                       1 if has_src[2] else 0,
                       1 if has_src[3] else 0)

        gl.glUniform4f(gl.glGetUniformLocation(self.prog, "weights"), 
                       float(params.get("weight1", 0.25)),
                       float(params.get("weight2", 0.25)),
                       float(params.get("weight3", 0.25)),
                       float(params.get("weight4", 0.25)))

        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "normalize_w"), 1 if params.get("normalize", True) else 0)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fallback_depth"), float(params.get("fallback_depth", 0.5)))

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        inputs = getattr(context, "inputs", {})
        
        # Mux takes 4 depth sources. The default `input_texture` is ignored unless mapped in context.inputs.
        tex1 = inputs.get("depth1", 0)
        tex2 = inputs.get("depth2", 0)
        tex3 = inputs.get("depth3", 0)
        tex4 = inputs.get("depth4", 0)
        
        has_src = [
            bool(tex1 and tex1 > 0),
            bool(tex2 and tex2 > 0),
            bool(tex3 and tex3 > 0),
            bool(tex4 and tex4 > 0)
        ]
        
        if self._mock_mode:
            # Fallback output logic simply passes the first active texture in priority mock
            out_tex = 0
            for t in [tex1, tex2, tex3, tex4]:
                if t and t > 0:
                    out_tex = t
                    break
            
            if hasattr(context, "outputs"):
                context.outputs["composite_depth"] = out_tex
            return out_tex

        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        gl.glUseProgram(self.prog)
        
        # Bind safely - 1x1 black generic bind over 0 error to prevent GL crash
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex1 if has_src[0] else 0)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth1"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex2 if has_src[1] else 0)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth2"), 1)

        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex3 if has_src[2] else 0)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth3"), 2)

        gl.glActiveTexture(gl.GL_TEXTURE3)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex4 if has_src[3] else 0)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth4"), 3)
        
        self._bind_uniforms(params, has_src)
        
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["composite_depth"] = self.out_tex
            
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
            logger.error(f"Cleanup Error in DepthDataMux: {e}")
