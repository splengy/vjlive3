"""
P3-EXT004: Agent Avatar Effect — Reactive geometric avatar visualizing agent state.

Renders a floating geometric entity (central hexagon + orbiting triangles + glow)
that responds to agent emotional states. Optionally integrates with IR camera
for shadow mode and eye tracking.

Ported from VJLive-2: core/effects/agent_avatar.py
"""
from typing import Dict, Any
import logging
try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
from .api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

METADATA = {
    "name": "Agent Avatar",
    "description": "Reactive geometric avatar visualizing agent emotional state (thinking/confident/overwhelmed).",
    "version": "1.0.0",
    "plugin_type": "effect",
    "category": "agents",
    "tags": ["agent", "avatar", "geometric", "sdf", "state", "visualization"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        # Avatar geometry
        {"name": "avatar_scale",           "type": "float", "default": 2.0,  "min": 0.0, "max": 10.0},
        {"name": "avatar_x",               "type": "float", "default": 9.0,  "min": 0.0, "max": 10.0},
        {"name": "avatar_y",               "type": "float", "default": 1.0,  "min": 0.0, "max": 10.0},
        {"name": "avatar_alpha",           "type": "float", "default": 7.0,  "min": 0.0, "max": 10.0},
        # Agent state
        {"name": "spin_speed",             "type": "float", "default": 2.0,  "min": 0.0, "max": 10.0},
        {"name": "glow_intensity",         "type": "float", "default": 5.0,  "min": 0.0, "max": 10.0},
        {"name": "confidence",             "type": "float", "default": 8.0,  "min": 0.0, "max": 10.0},
        {"name": "fragmentation",          "type": "float", "default": 0.0,  "min": 0.0, "max": 10.0},
        # Glow color
        {"name": "glow_color_r",           "type": "float", "default": 1.0,  "min": 0.0, "max": 10.0},
        {"name": "glow_color_g",           "type": "float", "default": 1.0,  "min": 0.0, "max": 10.0},
        {"name": "glow_color_b",           "type": "float", "default": 1.0,  "min": 0.0, "max": 10.0},
        # Shadow mode
        {"name": "shadow_mode_enabled",    "type": "float", "default": 0.0,  "min": 0.0, "max": 10.0},
        {"name": "shadow_threshold",       "type": "float", "default": 3.0,  "min": 0.0, "max": 10.0},
        {"name": "shadow_smooth",          "type": "float", "default": 1.0,  "min": 0.0, "max": 10.0},
        # Eye tracking
        {"name": "eye_tracking_enabled",   "type": "float", "default": 0.0,  "min": 0.0, "max": 10.0},
        {"name": "gaze_smooth",            "type": "float", "default": 0.5,  "min": 0.0, "max": 10.0},
        {"name": "face_timeout",           "type": "float", "default": 2.0,  "min": 0.0, "max": 10.0},
        {"name": "gaze_x",                 "type": "float", "default": 5.0,  "min": 0.0, "max": 10.0},
        {"name": "gaze_y",                 "type": "float", "default": 5.0,  "min": 0.0, "max": 10.0},
        # Mix
        {"name": "mix",                    "type": "float", "default": 8.0,  "min": 0.0, "max": 10.0},
    ],
}

VERTEX_SHADER = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1), vec2(1,-1), vec2(-1,1), vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(verts[gl_VertexID], 0.0, 1.0); uv = verts[gl_VertexID]*0.5+0.5; }
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;
uniform float avatar_scale;
uniform vec2  avatar_position;
uniform float avatar_alpha;
uniform float spin_speed;
uniform float glow_intensity;
uniform float confidence;
uniform float fragmentation;
uniform vec3  glow_color;
uniform float shadow_mode_enabled;
uniform float eye_tracking_enabled;
uniform vec2  gaze_direction;

#define PI 3.14159265359

float tri_sdf(vec2 p, vec2 a, vec2 b, vec2 c) {
    vec2 e0=b-a, e1=c-b, e2=a-c;
    vec2 v0=p-a, v1=p-b, v2=p-c;
    vec2 pq0=v0-e0*clamp(dot(v0,e0)/dot(e0,e0),0.,1.);
    vec2 pq1=v1-e1*clamp(dot(v1,e1)/dot(e1,e1),0.,1.);
    vec2 pq2=v2-e2*clamp(dot(v2,e2)/dot(e2,e2),0.,1.);
    float s=sign(e0.x*e2.y-e0.y*e2.x);
    vec2 d=min(min(vec2(dot(pq0,pq0),s*(v0.x*e0.y-v0.y*e0.x)),
                   vec2(dot(pq1,pq1),s*(v1.x*e1.y-v1.y*e1.x))),
                   vec2(dot(pq2,pq2),s*(v2.x*e2.y-v2.y*e2.x)));
    return -sqrt(d.x)*sign(d.y);
}

float agent_core(vec2 p, float t) {
    p = (p - avatar_position) / avatar_scale;
    float angle = t * spin_speed;
    float ca=cos(angle), sa=sin(angle);
    p = vec2(p.x*ca - p.y*sa, p.x*sa + p.y*ca);
    float frag = fragmentation;

    float d = 1.0;
    // Central hexagon ring
    float hex_r = length(p);
    d = min(d, abs(hex_r - 0.3) - 0.05);

    // 6 orbiting triangles
    for (int i = 0; i < 6; i++) {
        float a = float(i) * PI / 3.0 + t * spin_speed * 0.5;
        vec2 c = vec2(cos(a), sin(a)) * 0.6;
        c += normalize(c) * frag * sin(t * 3.0 + float(i)) * 0.1;
        vec2 v1 = c + vec2(0.1, 0.0);
        vec2 v2 = c + vec2(-0.05, 0.08);
        vec2 v3 = c + vec2(-0.05, -0.08);
        d = min(d, tri_sdf(p, v1, v2, v3) - 0.02);
    }

    // 3 inner dots
    for (int i = 0; i < 3; i++) {
        float a = float(i) * 2.0 * PI / 3.0 + t * spin_speed * 2.0;
        vec2 pos = vec2(cos(a), sin(a)) * 0.15;
        pos += normalize(pos) * frag * 0.05;
        d = min(d, length(p - pos) - 0.03);
    }
    return d;
}

void main() {
    vec4 src = texture(tex0, uv);
    vec2 suv = uv;

    // Eye tracking gaze offset
    if (eye_tracking_enabled > 0.5) {
        suv += gaze_direction * 0.1;
    }

    float d = agent_core(suv, time);

    float glow = pow(1.0 - smoothstep(0.0, 0.1, d), 2.0) * glow_intensity;
    float core = 1.0 - smoothstep(0.0, 0.02, d);
    float alpha = (core + glow) * avatar_alpha;

    float conf = confidence;
    vec3 col = glow_color * conf + vec3(1.0) * (1.0 - conf);
    col *= 0.5 + 0.5 * glow;

    // Composite over source
    vec4 avatar = vec4(col, clamp(alpha, 0.0, 1.0));
    fragColor = mix(src, src + avatar * (1.0 - src.a), u_mix);
}
"""

_PARAM_NAMES = [
    "avatar_scale", "avatar_x", "avatar_y", "avatar_alpha",
    "spin_speed", "glow_intensity", "confidence", "fragmentation",
    "glow_color_r", "glow_color_g", "glow_color_b",
    "shadow_mode_enabled", "shadow_threshold", "shadow_smooth",
    "eye_tracking_enabled", "gaze_smooth", "face_timeout", "gaze_x", "gaze_y",
]
_PARAM_DEFAULTS = {p["name"]: p["default"] for p in METADATA["parameters"]}

PRESETS = {
    "default_indicator":  {"spin_speed": 2.0, "glow_intensity": 5.0, "confidence": 8.0, "fragmentation": 0.0},
    "thinking_state":     {"spin_speed": 8.0, "glow_intensity": 4.0, "confidence": 3.0, "fragmentation": 0.0, "glow_color_r": 0.5, "glow_color_g": 0.7, "glow_color_b": 10.0},
    "confident_state":    {"spin_speed": 1.0, "glow_intensity": 9.0, "confidence": 9.0, "fragmentation": 0.0},
    "overwhelmed_state":  {"spin_speed": 5.0, "glow_intensity": 3.0, "confidence": 2.0, "fragmentation": 8.0, "glow_color_r": 10.0, "glow_color_g": 3.0, "glow_color_b": 3.0},
    "shadow_mode_active": {"shadow_mode_enabled": 10.0, "avatar_scale": 2.5, "avatar_x": 5.0, "avatar_y": 5.0, "glow_intensity": 7.0},
    "eye_tracking_active":{"eye_tracking_enabled": 10.0, "avatar_scale": 1.5, "spin_speed": 2.0, "glow_intensity": 6.0, "confidence": 7.0},
}


def _map(val, lo, hi): return lo + (max(0., min(10., float(val))) / 10.) * (hi - lo)


class AgentAvatarPlugin(EffectPlugin):
    """Agent avatar — 2D SDF geometric entity with agent-state visualization."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = self.vao = 0
        self._initialized = False

    def get_metadata(self): return METADATA

    def _compile(self, vs, fs):
        v = gl.glCreateShader(gl.GL_VERTEX_SHADER); gl.glShaderSource(v, vs); gl.glCompileShader(v)
        if not gl.glGetShaderiv(v, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(v))
        f = gl.glCreateShader(gl.GL_FRAGMENT_SHADER); gl.glShaderSource(f, fs); gl.glCompileShader(f)
        if not gl.glGetShaderiv(f, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(f))
        p = gl.glCreateProgram(); gl.glAttachShader(p, v); gl.glAttachShader(p, f); gl.glLinkProgram(p)
        if not gl.glGetProgramiv(p, gl.GL_LINK_STATUS): raise RuntimeError(gl.glGetProgramInfoLog(p))
        gl.glDeleteShader(v); gl.glDeleteShader(f); return p

    def initialize(self, context):
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"AgentAvatarPlugin init: {e}"); self._mock_mode = True; return False

    def _u(self, n): return gl.glGetUniformLocation(self.prog, n)

    def process_frame(self, input_texture, params, context):
        if not input_texture or input_texture <= 0: return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
            return input_texture
        if not self._initialized: self.initialize(context)
        w = getattr(context, 'width', 1920); h = getattr(context, 'height', 1080)
        ax = _map(params.get('avatar_x', 9.0), 0., 1.)
        ay = _map(params.get('avatar_y', 1.0), 0., 1.)
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u('tex0'), 0)
        gl.glUniform2f(self._u('resolution'), float(w), float(h))
        gl.glUniform1f(self._u('time'), float(getattr(context, 'time', 0.)))
        gl.glUniform1f(self._u('u_mix'), _map(params.get('mix', 8.), 0., 1.))
        gl.glUniform1f(self._u('avatar_scale'), _map(params.get('avatar_scale', 2.), 0., 0.5))
        gl.glUniform2f(self._u('avatar_position'), ax, ay)
        gl.glUniform1f(self._u('avatar_alpha'), _map(params.get('avatar_alpha', 7.), 0., 1.))
        gl.glUniform1f(self._u('spin_speed'), params.get('spin_speed', 2.0) / 10.0 * 5.0)
        gl.glUniform1f(self._u('glow_intensity'), params.get('glow_intensity', 5.0) / 10.0 * 3.0)
        gl.glUniform1f(self._u('confidence'), _map(params.get('confidence', 8.), 0., 1.))
        gl.glUniform1f(self._u('fragmentation'), _map(params.get('fragmentation', 0.), 0., 1.))
        gl.glUniform3f(self._u('glow_color'),
                       _map(params.get('glow_color_r', 1.), 0., 1.),
                       _map(params.get('glow_color_g', 1.), 0., 1.),
                       _map(params.get('glow_color_b', 1.), 0., 1.))
        gl.glUniform1f(self._u('shadow_mode_enabled'), float(params.get('shadow_mode_enabled', 0.) > 5.))
        gl.glUniform1f(self._u('eye_tracking_enabled'), float(params.get('eye_tracking_enabled', 0.) > 5.))
        gx = (params.get('gaze_x', 5.) - 5.) / 5.
        gy = (params.get('gaze_y', 5.) - 5.) / 5.
        gl.glUniform2f(self._u('gaze_direction'), gx, gy)
        gl.glBindVertexArray(self.vao); gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0); gl.glUseProgram(0)
        if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
        return input_texture

    def cleanup(self):
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
        except Exception as e: logger.error(f"AgentAvatarPlugin cleanup: {e}")
        finally: self.prog = self.vao = 0
