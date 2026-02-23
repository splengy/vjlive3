"""
P3-VD69: Depth Vector Field Datamosh Plugin for VJLive3.
Ported from legacy VJlive-2 DepthVectorFieldDatamoshEffect.

THE MISSING LINK — depth temporal deltas drive classic datamosh P-frame vectors.
Architecture: 3-FBO Ping-Pong: depth current, depth previous, video feedback.
All 10 params ported faithfully. Audio reactor stripped (VJLive3 standard).
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
    "name": "Depth Vector Field Datamosh",
    "description": "Depth frame-to-frame deltas become datamosh motion vectors.",
    "version": "1.0.0",
    "plugin_type": "depth_effect",
    "category": "glitch",
    "tags": ["depth", "datamosh", "vector-field", "motion", "displacement", "chromatic"],
    "priority": 1,
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "vector_scale",       "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "temporal_blend",     "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "propagation_decay",  "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "depth_threshold",    "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "block_size",         "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "block_chaos",        "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "chromatic_drift",    "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "color_bleed",        "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "feedback_strength",  "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "accumulation",       "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
    ]
}

VERTEX_SRC = """
#version 330 core
const vec2 v[4] = vec2[4](vec2(-1,-1),vec2(1,-1),vec2(-1,1),vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(v[gl_VertexID],0,1); uv = v[gl_VertexID]*0.5+0.5; }
"""

# Shader ported directly from legacy (no CPU side) 
VECTOR_FIELD_FRAG = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform sampler2D depth_prev_tex;
uniform int has_depth;
uniform float time;
uniform vec2 resolution;

uniform float vector_scale;
uniform float temporal_blend;
uniform float propagation_decay;
uniform float depth_threshold;
uniform float block_size;
uniform float block_chaos;
uniform float chromatic_drift;
uniform float color_bleed;
uniform float feedback_strength;
uniform float accumulation;

float hash(vec2 p) {
    p = fract(p * vec2(443.897, 441.423));
    p += dot(p, p.yx + 19.19);
    return fract((p.x + p.y) * p.x);
}

vec2 depth_gradient(vec2 p) {
    float t = 1.0 / resolution.x;
    float tl = texture(depth_tex, p+vec2(-t,-t)).r, tc = texture(depth_tex, p+vec2(0,-t)).r, tr = texture(depth_tex, p+vec2(t,-t)).r;
    float ml = texture(depth_tex, p+vec2(-t, 0)).r,                                             mr = texture(depth_tex, p+vec2(t, 0)).r;
    float bl = texture(depth_tex, p+vec2(-t, t)).r, bc = texture(depth_tex, p+vec2(0, t)).r,   br = texture(depth_tex, p+vec2(t, t)).r;
    return vec2(-tl-2.0*ml-bl+tr+2.0*mr+br, -tl-2.0*tc-tr+bl+2.0*bc+br);
}

void main() {
    vec4 current  = texture(tex0, uv);
    vec4 previous = texture(texPrev, uv);

    if (has_depth == 0) { fragColor = current; return; }

    float depth      = texture(depth_tex, uv).r;
    float depth_prev = texture(depth_prev_tex, uv).r;
    float depth_delta    = depth - depth_prev;
    float depth_velocity = abs(depth_delta);

    vec2 grad     = depth_gradient(uv);
    float grad_mag = length(grad);
    vec2 motion_vector = vec2(0.0);

    if (depth_velocity > depth_threshold * 0.01) {
        vec2 grad_dir = grad_mag > 0.001 ? normalize(grad) : vec2(1.0, 0.0);
        float mv_mag  = depth_delta * vector_scale * 0.05;
        motion_vector = grad_dir * mv_mag;
        vec2 prev_motion = (previous.rg - 0.5) * 0.1;
        motion_vector = mix(motion_vector, prev_motion, temporal_blend * 0.5);
    }

    float block = max(4.0, block_size * 40.0 + 4.0);
    vec2 block_uv = floor(uv * resolution / block) * block / resolution;
    vec2 block_motion = motion_vector;
    if (block_chaos > 0.0) {
        vec2 chaos_off = (vec2(hash(block_uv+1.1), hash(block_uv+2.2)) - 0.5) * block_chaos * 0.02;
        block_motion += chaos_off * depth_velocity;
    }

    vec2 displaced_uv = clamp(uv + block_motion, 0.001, 0.999);
    vec4 displaced = texture(texPrev, displaced_uv);

    float mosh_factor = smoothstep(depth_threshold*0.005, depth_threshold*0.02, depth_velocity);
    mosh_factor *= (1.0 - propagation_decay * 0.05);
    vec4 result = mix(current, displaced, mosh_factor);

    if (chromatic_drift > 0.0 && mosh_factor > 0.1) {
        float chroma = chromatic_drift * 0.005 * mosh_factor;
        result.r = texture(texPrev, clamp(displaced_uv + block_motion*chroma, 0.001, 0.999)).r;
        result.b = texture(texPrev, clamp(displaced_uv - block_motion*chroma, 0.001, 0.999)).b;
    }

    if (color_bleed > 0.0 && mosh_factor > 0.1) {
        vec2 bleed_dir = length(block_motion) > 0.001 ? normalize(block_motion) : vec2(0.0);
        float bleed_step = color_bleed * 0.01;
        vec4 bleed_sample = vec4(0.0);
        for (int i = 1; i <= 4; i++) {
            vec2 b_uv = clamp(uv + bleed_dir * bleed_step * float(i), 0.001, 0.999);
            bleed_sample += texture(texPrev, b_uv) / 4.0;
        }
        result = mix(result, bleed_sample, mosh_factor * color_bleed * 0.3);
    }

    if (feedback_strength > 0.0)
        result = mix(result, previous, feedback_strength * 0.3 * mosh_factor);
    if (accumulation > 0.0) {
        float accum = accumulation * 0.2 * smoothstep(0.0, 0.3, depth_velocity);
        result = max(result, texture(texPrev, uv) * accum);
    }

    fragColor = mix(current, result, 1.0);
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


class DepthVectorFieldDatamoshPlugin(object):
    """Depth Vector Field Datamosh — depth deltas AS motion vectors."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = 0
        self.empty_vao = 0
        # Ping-Pong: video (a/b) + depth history (c/d)
        self.fbo_a = self.tex_a = 0
        self.fbo_b = self.tex_b = 0
        self.fbo_dc = self.tex_dc = 0
        self.fbo_dp = self.tex_dp = 0
        self._w = self._h = 0
        self._initialized = False

    def get_metadata(self): return METADATA

    def initialize(self, context) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = _compile(VERTEX_SRC, VECTOR_FIELD_FRAG)
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"depth_vector_field_datamosh init failed: {e}")
            self._mock_mode = True; return False

    def _free(self):
        try:
            fbos = [f for f in [self.fbo_a, self.fbo_b, self.fbo_dc, self.fbo_dp] if f]
            texs = [t for t in [self.tex_a, self.tex_b, self.tex_dc, self.tex_dp] if t]
            if fbos: gl.glDeleteFramebuffers(len(fbos), fbos)
            if texs: gl.glDeleteTextures(len(texs), texs)
        except Exception: pass
        self.fbo_a = self.tex_a = self.fbo_b = self.tex_b = 0
        self.fbo_dc = self.tex_dc = self.fbo_dp = self.tex_dp = 0

    def _alloc(self, w, h):
        self._free(); self._w, self._h = w, h
        self.fbo_a,  self.tex_a  = _make_fbo(w, h)
        self.fbo_b,  self.tex_b  = _make_fbo(w, h)
        self.fbo_dc, self.tex_dc = _make_fbo(w, h)
        self.fbo_dp, self.tex_dp = _make_fbo(w, h)

    def _u(self, name): return gl.glGetUniformLocation(self.prog, name)

    def _draw(self):
        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)

    def _blit_depth(self, depth_tex, target_fbo, w, h):
        """Copy depth texture into history FBO."""
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, target_fbo)
        gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_tex)
        gl.glUniform1i(self._u("tex0"), 0)
        gl.glUniform1i(self._u("has_depth"), 0)
        self._draw()
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0: return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"): context.outputs["video_out"] = input_texture
            return input_texture
        if not self._initialized: self.initialize(context)
        w = getattr(context, 'width', 1920); h = getattr(context, 'height', 1080)
        if w != self._w or h != self._h: self._alloc(w, h)

        inputs   = getattr(context, "inputs", {})
        depth_in = inputs.get("depth_in", 0)
        time_val = getattr(context, 'time', 0.0)
        has_d    = 1 if depth_in > 0 else 0

        if has_d:
            self._blit_depth(depth_in, self.fbo_dc, w, h)

        gl.glViewport(0, 0, w, h)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_a)
        gl.glUseProgram(self.prog)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u("tex0"), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_b)
        gl.glUniform1i(self._u("texPrev"), 1)
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_dc if has_d else 0)
        gl.glUniform1i(self._u("depth_tex"), 2)
        gl.glActiveTexture(gl.GL_TEXTURE3)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_dp if has_d else 0)
        gl.glUniform1i(self._u("depth_prev_tex"), 3)

        gl.glUniform1i(self._u("has_depth"),         has_d)
        gl.glUniform2f(self._u("resolution"),        float(w), float(h))
        gl.glUniform1f(self._u("time"),              float(time_val))
        gl.glUniform1f(self._u("vector_scale"),      float(params.get("vector_scale",      0.5)))
        gl.glUniform1f(self._u("temporal_blend"),    float(params.get("temporal_blend",    0.4)))
        gl.glUniform1f(self._u("propagation_decay"), float(params.get("propagation_decay", 0.3)))
        gl.glUniform1f(self._u("depth_threshold"),   float(params.get("depth_threshold",   0.4)))
        gl.glUniform1f(self._u("block_size"),        float(params.get("block_size",        0.4)))
        gl.glUniform1f(self._u("block_chaos"),       float(params.get("block_chaos",       0.3)))
        gl.glUniform1f(self._u("chromatic_drift"),   float(params.get("chromatic_drift",   0.3)))
        gl.glUniform1f(self._u("color_bleed"),       float(params.get("color_bleed",       0.3)))
        gl.glUniform1f(self._u("feedback_strength"), float(params.get("feedback_strength", 0.3)))
        gl.glUniform1f(self._u("accumulation"),      float(params.get("accumulation",      0.2)))

        self._draw()
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        # Swap rings
        self.fbo_a, self.fbo_b   = self.fbo_b, self.fbo_a
        self.tex_a, self.tex_b   = self.tex_b, self.tex_a
        self.fbo_dc, self.fbo_dp = self.fbo_dp, self.fbo_dc
        self.tex_dc, self.tex_dp = self.tex_dp, self.tex_dc

        if hasattr(context, "outputs"): context.outputs["video_out"] = self.tex_b
        return self.tex_b

    def cleanup(self) -> None:
        try:
            self._free()
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup error depth_vector_field_datamosh: {e}")
        finally:
            self.prog = self.empty_vao = 0
