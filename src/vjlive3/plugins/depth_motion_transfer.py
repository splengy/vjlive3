"""
P3-VD59: Depth Motion Transfer Plugin for VJLive3.
Ported from legacy VJlive-2 DepthMotionTransferEffect.

Architecture change: Legacy used CPU+cv2 Sobel for motion field computation.
In VJLive3 we replace this with a GPU-only dual-pass approach:
  Pass 1: GPGPU depth-delta → motion RG texture (written to fbo_motion)
  Pass 2: displacement shader using motion texture + feedback → video output
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
    "name": "Depth Motion Transfer",
    "description": "Performer depth movement drives video displacement with persistent decay.",
    "version": "1.0.0",
    "plugin_type": "depth_effect",
    "category": "motion",
    "tags": ["depth", "motion", "displacement", "transfer", "velocity"],
    "priority": 1,
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "motion_scale",    "type": "float", "min": 0.0, "max": 1.0,  "default": 0.6},
        {"name": "decay_rate",      "type": "float", "min": 0.8, "max": 0.99, "default": 0.9},
        {"name": "force_direction", "type": "float", "min": 0.0, "max": 1.0,  "default": 0.0},
        {"name": "color_smear",     "type": "float", "min": 0.0, "max": 1.0,  "default": 0.3},
        {"name": "threshold",       "type": "float", "min": 0.0, "max": 0.1,  "default": 0.02},
        {"name": "feedback",        "type": "float", "min": 0.0, "max": 1.0,  "default": 0.3},
        {"name": "accumulate",      "type": "float", "min": 0.0, "max": 1.0,  "default": 0.7},
    ]
}

VERTEX_SRC = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1),vec2(1,-1),vec2(-1,1),vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(verts[gl_VertexID],0,1); uv = verts[gl_VertexID]*0.5+0.5; }
"""

# Pass 1: compute motion field from current depth vs previous depth
MOTION_PASS_FRAG = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D depth_curr;
uniform sampler2D depth_prev;
uniform sampler2D motion_prev;   // accumulated motion from last frame
uniform vec2 resolution;
uniform float threshold;
uniform float decay_rate;
uniform float accumulate;

void main() {
    vec2 px = 1.0 / resolution;

    float curr = texture(depth_curr, uv).r;
    float prev_d = texture(depth_prev, uv).r;

    float delta = prev_d - curr;  // positive = approaching camera

    // Threshold noise gate
    if (abs(delta) < threshold) delta = 0.0;

    // Spatial gradient via finite differences (replaces CPU Sobel)
    float gx = (texture(depth_curr, uv + vec2(px.x, 0)).r -
                texture(depth_curr, uv - vec2(px.x, 0)).r) * 0.5;
    float gy = (texture(depth_curr, uv + vec2(0, px.y)).r -
                texture(depth_curr, uv - vec2(0, px.y)).r) * 0.5;

    float mx = delta * gx * 0.5 + delta * 0.1;
    float my = delta * gy * 0.5 + delta * 0.05;

    // Accumulate with decay
    vec2 prev_m = (texture(motion_prev, uv).rg - 0.5) * 2.0;
    vec2 new_m = prev_m * decay_rate * accumulate + vec2(mx, my) * (1.0 - accumulate * 0.5);
    new_m = clamp(new_m, -1.0, 1.0);

    // Encode to 0-1 (0.5 = no motion)
    fragColor = vec4(new_m * 0.5 + 0.5, 0.0, 1.0);
}
"""

# Pass 2: displace video using motion field + feedback
DISPLACE_FRAG = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D u_motion_tex;
uniform sampler2D u_displaced_prev;
uniform int has_depth;
uniform float motion_scale;
uniform float force_direction;
uniform float color_smear;
uniform float feedback;

void main() {
    if (has_depth == 0) {
        fragColor = texture(tex0, uv);
        return;
    }

    vec2 motion = (texture(u_motion_tex, uv).rg - 0.5) * 2.0;

    vec2 displacement;
    if (force_direction < 0.33) {
        displacement = motion * motion_scale * 0.1;
    } else if (force_direction < 0.66) {
        float mag = length(motion);
        vec2 dir = normalize(motion + 0.0001);
        displacement = dir * mag * motion_scale * 0.15;
    } else {
        float mag = length(motion);
        displacement = vec2(-motion.y, motion.x) * motion_scale * 0.1;
        displacement += motion * mag * 0.02;
    }

    vec2 displaced_uv = clamp(uv - displacement, 0.0, 1.0);

    vec3 color;
    if (color_smear > 0.01) {
        vec2 smear = displacement * color_smear * 0.5;
        color.r = texture(tex0, clamp(displaced_uv + smear, 0.0, 1.0)).r;
        color.g = texture(tex0, displaced_uv).g;
        color.b = texture(tex0, clamp(displaced_uv - smear, 0.0, 1.0)).b;
    } else {
        color = texture(tex0, displaced_uv).rgb;
    }

    if (feedback > 0.01) {
        vec3 prev = texture(u_displaced_prev, displaced_uv).rgb;
        color = mix(color, prev, feedback * 0.7);
    }

    float edge = smoothstep(0.0, 0.02, displaced_uv.x)
               * smoothstep(1.0, 0.98, displaced_uv.x)
               * smoothstep(0.0, 0.02, displaced_uv.y)
               * smoothstep(1.0, 0.98, displaced_uv.y);
    color *= edge;

    float motion_vis = length(motion) * 0.3;
    vec3 motion_color = vec3(motion.x*0.5+0.5, motion.y*0.5+0.5, motion_vis);
    color = mix(color, color + motion_color * 0.05, motion_vis);

    fragColor = vec4(color, 1.0);
}
"""


def _compile(vs, fs):
    v = gl.glCreateShader(gl.GL_VERTEX_SHADER)
    gl.glShaderSource(v, vs)
    gl.glCompileShader(v)
    if not gl.glGetShaderiv(v, gl.GL_COMPILE_STATUS):
        raise RuntimeError(gl.glGetShaderInfoLog(v))
    f = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
    gl.glShaderSource(f, fs)
    gl.glCompileShader(f)
    if not gl.glGetShaderiv(f, gl.GL_COMPILE_STATUS):
        raise RuntimeError(gl.glGetShaderInfoLog(f))
    p = gl.glCreateProgram()
    gl.glAttachShader(p, v)
    gl.glAttachShader(p, f)
    gl.glLinkProgram(p)
    if not gl.glGetProgramiv(p, gl.GL_LINK_STATUS):
        raise RuntimeError(gl.glGetProgramInfoLog(p))
    gl.glDeleteShader(v)
    gl.glDeleteShader(f)
    return p


def _make_fbo(w, h, internal=None):
    internal = internal or gl.GL_RGBA
    fbo = gl.glGenFramebuffers(1)
    tex = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, internal, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
    gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
    gl.glClearColor(0.5, 0.5, 0, 1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
    return fbo, tex


class DepthMotionTransferPlugin(object):
    """Depth Motion Transfer — GPGPU depth-delta displacement with feedback."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog_motion = 0
        self.prog_displace = 0
        self.empty_vao = 0
        # Motion field ping-pong
        self.fbo_motion_a = self.tex_motion_a = 0
        self.fbo_motion_b = self.tex_motion_b = 0
        # Depth history ping-pong (current/prev)
        self.fbo_depth_a = self.tex_depth_a = 0
        self.fbo_depth_b = self.tex_depth_b = 0
        # Output + feedback
        self.fbo_out_a = self.tex_out_a = 0
        self.fbo_out_b = self.tex_out_b = 0
        self._w = self._h = 0
        self._initialized = False

    def get_metadata(self):
        return METADATA

    def initialize(self, context) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True
            return True
        try:
            self.prog_motion = _compile(VERTEX_SRC, MOTION_PASS_FRAG)
            self.prog_displace = _compile(VERTEX_SRC, DISPLACE_FRAG)
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"depth_motion_transfer init failed: {e}")
            self._mock_mode = True
            return False

    def _free(self):
        try:
            fbos = [f for f in [self.fbo_motion_a, self.fbo_motion_b,
                                 self.fbo_depth_a, self.fbo_depth_b,
                                 self.fbo_out_a, self.fbo_out_b] if f]
            texs = [t for t in [self.tex_motion_a, self.tex_motion_b,
                                 self.tex_depth_a, self.tex_depth_b,
                                 self.tex_out_a, self.tex_out_b] if t]
            if fbos: gl.glDeleteFramebuffers(len(fbos), fbos)
            if texs: gl.glDeleteTextures(len(texs), texs)
        except Exception:
            pass
        (self.fbo_motion_a, self.tex_motion_a,
         self.fbo_motion_b, self.tex_motion_b,
         self.fbo_depth_a, self.tex_depth_a,
         self.fbo_depth_b, self.tex_depth_b,
         self.fbo_out_a, self.tex_out_a,
         self.fbo_out_b, self.tex_out_b) = (0,) * 12

    def _alloc(self, w, h):
        self._free()
        self._w, self._h = w, h
        self.fbo_motion_a, self.tex_motion_a = _make_fbo(w, h)
        self.fbo_motion_b, self.tex_motion_b = _make_fbo(w, h)
        self.fbo_depth_a, self.tex_depth_a   = _make_fbo(w, h)
        self.fbo_depth_b, self.tex_depth_b   = _make_fbo(w, h)
        self.fbo_out_a, self.tex_out_a       = _make_fbo(w, h)
        self.fbo_out_b, self.tex_out_b       = _make_fbo(w, h)

    def _u(self, prog, name):
        return gl.glGetUniformLocation(prog, name)

    def _draw(self):
        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)

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
        if w != self._w or h != self._h:
            self._alloc(w, h)

        inputs   = getattr(context, "inputs", {})
        depth_in = inputs.get("depth_in", 0)
        has_d    = 1 if depth_in > 0 else 0

        threshold  = float(params.get("threshold",       0.02))
        decay_rate = float(params.get("decay_rate",      0.90))
        accumulate = float(params.get("accumulate",      0.70))
        m_scale    = float(params.get("motion_scale",    0.60))
        force_dir  = float(params.get("force_direction", 0.0))
        c_smear    = float(params.get("color_smear",     0.3))
        feedback   = float(params.get("feedback",        0.3))

        gl.glViewport(0, 0, w, h)

        # ── Pass 1: Compute motion field ──────────────────────────────────
        if has_d:
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_motion_a)
            gl.glUseProgram(self.prog_motion)
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
            gl.glUniform1i(self._u(self.prog_motion, "depth_curr"), 0)
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_depth_b)
            gl.glUniform1i(self._u(self.prog_motion, "depth_prev"), 1)
            gl.glActiveTexture(gl.GL_TEXTURE2)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_motion_b)
            gl.glUniform1i(self._u(self.prog_motion, "motion_prev"), 2)
            gl.glUniform2f(self._u(self.prog_motion, "resolution"), float(w), float(h))
            gl.glUniform1f(self._u(self.prog_motion, "threshold"),   threshold)
            gl.glUniform1f(self._u(self.prog_motion, "decay_rate"),  decay_rate)
            gl.glUniform1f(self._u(self.prog_motion, "accumulate"),  accumulate)
            self._draw()
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            # Save current depth as previous for next frame
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_depth_a)
            gl.glUseProgram(self.prog_displace)  # reuse VS; just need passthrough
            # simpler: blit depth via texture copy render
            gl.glUseProgram(self.prog_motion)
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
            gl.glUniform1i(self._u(self.prog_motion, "depth_curr"), 0)
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
            gl.glUniform1i(self._u(self.prog_motion, "depth_prev"), 1)
            gl.glActiveTexture(gl.GL_TEXTURE2)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_motion_b)
            gl.glUniform1i(self._u(self.prog_motion, "motion_prev"), 2)
            gl.glUniform1f(self._u(self.prog_motion, "threshold"),  0.0)
            gl.glUniform1f(self._u(self.prog_motion, "decay_rate"), 0.0)
            gl.glUniform1f(self._u(self.prog_motion, "accumulate"), 0.0)
            self._draw()
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        # ── Pass 2: Displacement ──────────────────────────────────────────
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_out_a)
        gl.glUseProgram(self.prog_displace)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u(self.prog_displace, "tex0"), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_motion_a if has_d else 0)
        gl.glUniform1i(self._u(self.prog_displace, "u_motion_tex"), 1)
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_out_b)
        gl.glUniform1i(self._u(self.prog_displace, "u_displaced_prev"), 2)
        gl.glUniform1i(self._u(self.prog_displace, "has_depth"),      has_d)
        gl.glUniform1f(self._u(self.prog_displace, "motion_scale"),   m_scale)
        gl.glUniform1f(self._u(self.prog_displace, "force_direction"),force_dir)
        gl.glUniform1f(self._u(self.prog_displace, "color_smear"),    c_smear)
        gl.glUniform1f(self._u(self.prog_displace, "feedback"),       feedback)
        self._draw()
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        # Ping-Pong swaps
        self.fbo_motion_a, self.fbo_motion_b = self.fbo_motion_b, self.fbo_motion_a
        self.tex_motion_a, self.tex_motion_b = self.tex_motion_b, self.tex_motion_a
        self.fbo_depth_a, self.fbo_depth_b   = self.fbo_depth_b, self.fbo_depth_a
        self.tex_depth_a, self.tex_depth_b   = self.tex_depth_b, self.tex_depth_a
        self.fbo_out_a, self.fbo_out_b       = self.fbo_out_b, self.fbo_out_a
        self.tex_out_a, self.tex_out_b       = self.tex_out_b, self.tex_out_a

        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.tex_out_b
        return self.tex_out_b

    def cleanup(self) -> None:
        try:
            self._free()
            if hasattr(gl, 'glDeleteProgram'):
                if self.prog_motion:   gl.glDeleteProgram(self.prog_motion)
                if self.prog_displace: gl.glDeleteProgram(self.prog_displace)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup error depth_motion_transfer: {e}")
        finally:
            self.prog_motion = self.prog_displace = self.empty_vao = 0
