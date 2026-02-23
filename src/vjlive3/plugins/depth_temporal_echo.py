"""
P3-VD67: Depth Temporal Echo Plugin for VJLive3.
Ported from legacy VJlive-2 DepthTemporalEchoEffect.

Architecture: The legacy used CPU frame capture via glGetTexImage + numpy.
In VJLive3 we use 4-FBO history ring buffer — each frame the oldest slot
is overwritten. The shader samples depth-indexed history slots.
"""

from typing import Dict, Any
import logging

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

# # from .api import EffectPlugin, PluginContext
logger = logging.getLogger(__name__)

METADATA = {
    "name": "Depth Temporal Echo",
    "description": "Depth zones see different moments in time — near=now, far=past.",
    "version": "1.0.0",
    "plugin_type": "depth_effect",
    "category": "temporal",
    "tags": ["depth", "temporal", "echo", "ghost", "time", "delay"],
    "priority": 1,
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "ghost_opacity", "type": "float", "min": 0.0, "max": 1.0,  "default": 0.7},
        {"name": "color_decay",   "type": "float", "min": 0.0, "max": 1.0,  "default": 0.3},
        {"name": "blend_mode",    "type": "float", "min": 0.0, "max": 1.0,  "default": 0.0},
        {"name": "near_delay",    "type": "float", "min": 0.0, "max": 1.0,  "default": 0.0},
        {"name": "far_delay",     "type": "float", "min": 0.0, "max": 1.0,  "default": 0.8},
        {"name": "edge_bleed",    "type": "float", "min": 0.0, "max": 1.0,  "default": 0.4},
    ]
}

VERTEX_SRC = """
#version 330 core
const vec2 v[4] = vec2[4](vec2(-1,-1),vec2(1,-1),vec2(-1,1),vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(v[gl_VertexID],0,1); uv = v[gl_VertexID]*0.5+0.5; }
"""

ECHO_FRAGMENT = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;        // current frame
uniform sampler2D u_depth_tex;
uniform sampler2D u_echo0;
uniform sampler2D u_echo1;
uniform sampler2D u_echo2;
uniform sampler2D u_echo3;
uniform int has_depth;
uniform float ghost_opacity;
uniform float color_decay;
uniform float blend_mode;
uniform float near_delay;
uniform float far_delay;
uniform float edge_bleed;

vec3 desaturate(vec3 c, float a) { return mix(c, vec3(dot(c, vec3(0.299,0.587,0.114))), a); }
vec3 blend_add(vec3 b, vec3 e) { return min(b+e, vec3(1.0)); }
vec3 blend_screen(vec3 b, vec3 e) { return 1.0-(1.0-b)*(1.0-e); }
vec3 blend_diff(vec3 b, vec3 e) { return abs(b-e); }

void main() {
    vec3 current = texture(tex0, uv).rgb;

    if (has_depth == 0) { fragColor = vec4(current, 1.0); return; }

    float depth = texture(u_depth_tex, uv).r;
    if (depth < 0.01) { fragColor = vec4(current, 1.0); return; }

    float time_index = clamp(mix(near_delay, far_delay, depth), 0.0, 1.0);

    // Sample 4 echo slots
    vec3 e0 = texture(u_echo0, uv).rgb;
    vec3 e1 = texture(u_echo1, uv).rgb;
    vec3 e2 = texture(u_echo2, uv).rgb;
    vec3 e3 = texture(u_echo3, uv).rgb;

    float seg = 0.25;
    float soft = edge_bleed * seg * 2.0 + 0.001;
    vec3 echo;
    if (time_index < seg) {
        echo = mix(current, e0, smoothstep(0.0, soft, time_index));
    } else if (time_index < seg*2.0) {
        echo = mix(e0, e1, smoothstep(0.0, 1.0, (time_index-seg)/seg));
    } else if (time_index < seg*3.0) {
        echo = mix(e1, e2, smoothstep(0.0, 1.0, (time_index-seg*2.0)/seg));
    } else {
        echo = mix(e2, e3, smoothstep(0.0, 1.0, (time_index-seg*3.0)/seg));
    }

    echo = desaturate(echo, color_decay * time_index);
    echo *= mix(vec3(1.0), vec3(0.7, 0.85, 1.0), time_index * 0.4);

    vec3 result;
    if (blend_mode < 0.25)   result = mix(current, echo, ghost_opacity);
    else if (blend_mode<0.5) result = mix(current, blend_add(current, echo*ghost_opacity), ghost_opacity);
    else if (blend_mode<0.75)result = mix(current, blend_screen(current, echo*ghost_opacity), ghost_opacity);
    else                     result = mix(current, blend_diff(current, echo), ghost_opacity);

    fragColor = vec4(result, 1.0);
}
"""

def _compile(vs, fs):
    v = gl.glCreateShader(gl.GL_VERTEX_SHADER)
    gl.glShaderSource(v, vs); gl.glCompileShader(v)
    if not gl.glGetShaderiv(v, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(v))
    f = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
    gl.glShaderSource(f, fs); gl.glCompileShader(f)
    if not gl.glGetShaderiv(f, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(f))
    p = gl.glCreateProgram()
    gl.glAttachShader(p, v); gl.glAttachShader(p, f); gl.glLinkProgram(p)
    if not gl.glGetProgramiv(p, gl.GL_LINK_STATUS): raise RuntimeError(gl.glGetProgramInfoLog(p))
    gl.glDeleteShader(v); gl.glDeleteShader(f)
    return p

def _make_fbo(w, h):
    fbo = gl.glGenFramebuffers(1); tex = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
    gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
    gl.glClearColor(0,0,0,0); gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
    return fbo, tex


class DepthTemporalEchoPlugin(object):
    """Depth Temporal Echo — 4-FBO ring buffer showing past frames by depth zone."""

    HISTORY_SLOTS = 4

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = 0
        self.empty_vao = 0
        # 4 history FBOs (ring buffer)
        self.history_fbos = [0] * self.HISTORY_SLOTS
        self.history_texs = [0] * self.HISTORY_SLOTS
        self.fbo_out = self.tex_out = 0
        self._ring_head = 0
        self._frame_count = 0
        self._capture_interval = 2  # update a history slot every N frames
        self._w = self._h = 0
        self._initialized = False

    def get_metadata(self): return METADATA

    def initialize(self, context) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = _compile(VERTEX_SRC, ECHO_FRAGMENT)
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"depth_temporal_echo init failed: {e}")
            self._mock_mode = True; return False

    def _free(self):
        try:
            fbos = [f for f in self.history_fbos + [self.fbo_out] if f]
            texs = [t for t in self.history_texs + [self.tex_out] if t]
            if fbos: gl.glDeleteFramebuffers(len(fbos), fbos)
            if texs: gl.glDeleteTextures(len(texs), texs)
        except Exception: pass
        self.history_fbos = [0]*self.HISTORY_SLOTS
        self.history_texs = [0]*self.HISTORY_SLOTS
        self.fbo_out = self.tex_out = 0

    def _alloc(self, w, h):
        self._free(); self._w, self._h = w, h
        for i in range(self.HISTORY_SLOTS):
            self.history_fbos[i], self.history_texs[i] = _make_fbo(w, h)
        self.fbo_out, self.tex_out = _make_fbo(w, h)

    def _u(self, name): return gl.glGetUniformLocation(self.prog, name)

    def _draw(self):
        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)

    def _blit_to_history(self, input_tex, w, h):
        """Copy input_tex into the current ring slot using the fragment shader as passthrough."""
        slot = self._ring_head % self.HISTORY_SLOTS
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.history_fbos[slot])
        gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_tex)
        gl.glUniform1i(self._u("tex0"), 0)
        # Set has_depth=0 so we get passthrough
        gl.glUniform1i(self._u("has_depth"), 0)
        self._draw()
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        self._ring_head = (self._ring_head + 1) % self.HISTORY_SLOTS

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0: return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"): context.outputs["video_out"] = input_texture
            return input_texture
        if not self._initialized: self.initialize(context)
        w = getattr(context, 'width', 1920); h = getattr(context, 'height', 1080)
        if w != self._w or h != self._h: self._alloc(w, h)

        self._frame_count += 1
        if self._frame_count % self._capture_interval == 0:
            self._blit_to_history(input_texture, w, h)

        inputs   = getattr(context, "inputs", {})
        depth_in = inputs.get("depth_in", 0)
        has_d    = 1 if depth_in > 0 else 0

        ghost_op = float(params.get("ghost_opacity", 0.7))
        c_decay  = float(params.get("color_decay",   0.3))
        blend    = float(params.get("blend_mode",    0.0))
        n_delay  = float(params.get("near_delay",    0.0))
        f_delay  = float(params.get("far_delay",     0.8))
        e_bleed  = float(params.get("edge_bleed",    0.4))

        gl.glViewport(0, 0, w, h)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_out)
        gl.glUseProgram(self.prog)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u("tex0"), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in if has_d else 0)
        gl.glUniform1i(self._u("u_depth_tex"), 1)

        for i in range(self.HISTORY_SLOTS):
            slot = (self._ring_head - 1 - i) % self.HISTORY_SLOTS
            gl.glActiveTexture(gl.GL_TEXTURE2 + i)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.history_texs[slot])
            gl.glUniform1i(self._u(f"u_echo{i}"), 2 + i)

        gl.glUniform1i(self._u("has_depth"),    has_d)
        gl.glUniform1f(self._u("ghost_opacity"), ghost_op)
        gl.glUniform1f(self._u("color_decay"),   c_decay)
        gl.glUniform1f(self._u("blend_mode"),    blend)
        gl.glUniform1f(self._u("near_delay"),    n_delay)
        gl.glUniform1f(self._u("far_delay"),     f_delay)
        gl.glUniform1f(self._u("edge_bleed"),    e_bleed)

        self._draw()
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        if hasattr(context, "outputs"): context.outputs["video_out"] = self.tex_out
        return self.tex_out

    def cleanup(self) -> None:
        try:
            self._free()
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup error depth_temporal_echo: {e}")
        finally:
            self.prog = self.empty_vao = 0
