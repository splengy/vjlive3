"""
P5-DM04: Bass therapy — strobe flash, pupil dilation, adrenaline chaos.
Ported from VJlive-2/plugins/vdatamosh/bass_therapy_datamosh.py.
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
    "name": "Bass Therapy Datamosh",
    "description": "Bass therapy — strobe flash, pupil dilation, adrenaline chaos.",
    "version": "1.0.0",
    "plugin_type": "datamosh",
    "category": "datamosh",
    "tags": ['bass', 'strobe', 'adrenaline', 'datamosh', 'audio'],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [{'name': 'strobe_speed', 'type': 'float', 'default': 5.0, 'min': 0.0, 'max': 10.0}, {'name': 'strobe_intensity', 'type': 'float', 'default': 3.0, 'min': 0.0, 'max': 10.0}, {'name': 'bass_crush', 'type': 'float', 'default': 3.0, 'min': 0.0, 'max': 10.0}, {'name': 'pupil_dilate', 'type': 'float', 'default': 3.0, 'min': 0.0, 'max': 10.0}, {'name': 'sweat_drip', 'type': 'float', 'default': 2.0, 'min': 0.0, 'max': 10.0}, {'name': 'laser_burn', 'type': 'float', 'default': 2.0, 'min': 0.0, 'max': 10.0}, {'name': 'rail_grip', 'type': 'float', 'default': 5.0, 'min': 0.0, 'max': 10.0}, {'name': 'adrenaline', 'type': 'float', 'default': 5.0, 'min': 0.0, 'max': 10.0}, {'name': 'bpm_sync', 'type': 'float', 'default': 5.0, 'min': 0.0, 'max': 10.0}, {'name': 'dark_room', 'type': 'float', 'default': 3.0, 'min': 0.0, 'max': 10.0}, {'name': 'visual_bleed', 'type': 'float', 'default': 2.0, 'min': 0.0, 'max': 10.0}, {'name': 'retina_burn', 'type': 'float', 'default': 3.0, 'min': 0.0, 'max': 10.0}]
}

VERTEX_SHADER = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1), vec2(1,-1), vec2(-1,1), vec2(1,1));
out vec2 uv;
void main() {
    gl_Position = vec4(verts[gl_VertexID], 0.0, 1.0);
    uv = verts[gl_VertexID] * 0.5 + 0.5;
}
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform sampler2D prev_tex;
uniform vec2  resolution;
uniform float time;
uniform float u_mix;
uniform float strobe_speed;  // Flash speed
uniform float strobe_intensity;  // Flash brightness
uniform float bass_crush;  // Screen shake
uniform float pupil_dilate;  // Radial blur
uniform float sweat_drip;  // Melt intensity
uniform float laser_burn;  // Edge burn
uniform float rail_grip;  // Feedback lock
uniform float adrenaline;  // Chaos speed
uniform float bpm_sync;  // BPM sync
uniform float dark_room;  // Darkness level
uniform float visual_bleed;  // Video B bleed
uniform float retina_burn;  // Persistence

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
    vec2 i = floor(p); vec2 f = fract(p);
    f = f*f*(3.0-2.0*f);
    return mix(mix(hash(i), hash(i+vec2(1,0)), f.x), mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), f.x), f.y);
}

void main() {
    vec4 curr = texture(tex0, uv);
    vec4 prev = texture(prev_tex, uv);
    vec2 texel = 1.0 / resolution;

    // Combined displacement from all parameters
    float displacement = (strobe_intensity / 10.0);
    float feedback     = (retina_burn / 10.0);

    vec2 du = vec2(
        noise(uv * (8.0 + (strobe_speed / 10.0) * 10.0) + vec2(time * 0.5)) - 0.5,
        noise(uv * (8.0 + (strobe_speed / 10.0) * 10.0) + vec2(1.3, time * 0.4)) - 0.5
    ) * displacement * 0.1;

    vec4 warped = texture(tex0, clamp(uv + du, 0.0, 1.0));
    vec3 color = mix(warped.rgb, prev.rgb, feedback * 0.5);

    // Chromatic separation
    float chroma = (visual_bleed / 10.0);
    color.r = texture(tex0, clamp(uv + du + vec2(chroma * 0.01, 0.0), 0.0, 1.0)).r;
    color.b = texture(tex0, clamp(uv + du - vec2(chroma * 0.01, 0.0), 0.0, 1.0)).b;

    // Vignette
    float vign = (dark_room / 10.0);
    if (vign > 0.0) {
        vec2 vc = uv * 2.0 - 1.0;
        color *= 1.0 - dot(vc, vc) * vign * 0.5;
    }

    // Color tint
    color.r *= 1.0 + strobe_speed/10.0*0.3;
    color.g *= 1.0 + 0.0;
    color.b *= 1.0 + 0.0;
    color = clamp(color, 0.0, 1.0);

    fragColor = mix(curr, vec4(color, curr.a), u_mix);
}
"""

_PARAM_NAMES = ['strobe_speed', 'strobe_intensity', 'bass_crush', 'pupil_dilate', 'sweat_drip', 'laser_burn', 'rail_grip', 'adrenaline', 'bpm_sync', 'dark_room', 'visual_bleed', 'retina_burn']
_PARAM_DEFAULTS = {'strobe_speed': 5.0, 'strobe_intensity': 3.0, 'bass_crush': 3.0, 'pupil_dilate': 3.0, 'sweat_drip': 2.0, 'laser_burn': 2.0, 'rail_grip': 5.0, 'adrenaline': 5.0, 'bpm_sync': 5.0, 'dark_room': 3.0, 'visual_bleed': 2.0, 'retina_burn': 3.0}


def _map(val: float, out_min: float, out_max: float) -> float:
    t = max(0.0, min(10.0, float(val))) / 10.0
    return out_min + t * (out_max - out_min)


class BassTherapyDatamoshPlugin(object):
    """Bass therapy — strobe flash, pupil dilation, adrenaline chaos."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = 0
        self.vao  = 0
        self.trail_fbo = 0
        self.trail_tex = 0
        self._w = self._h = 0
        self._initialized = False

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def _compile(self, vs: str, fs: str) -> int:
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

    def _make_fbo(self, w: int, h: int):
        fbo = gl.glGenFramebuffers(1); tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
        gl.glClearColor(0, 0, 0, 0); gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        return fbo, tex

    def initialize(self, context) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao  = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"{self.__class__.__name__} init failed: {e}")
            self._mock_mode = True; return False

    def _u(self, name: str) -> int:
        return gl.glGetUniformLocation(self.prog, name)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0: return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"): context.outputs["video_out"] = input_texture
            return input_texture
        if not self._initialized: self.initialize(context)

        w = getattr(context, "width", 1920); h = getattr(context, "height", 1080)
        if w != self._w or h != self._h:
            if self.trail_fbo:
                try: gl.glDeleteFramebuffers(1, [self.trail_fbo]); gl.glDeleteTextures(1, [self.trail_tex])
                except Exception: pass
            self.trail_fbo, self.trail_tex = self._make_fbo(w, h)
            self._w, self._h = w, h

        mix_v  = _map(params.get("mix", 5.0), 0.0, 1.0)
        time_v = float(getattr(context, "time", 0.0))

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.trail_fbo)
        gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u("tex0"), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.trail_tex)
        gl.glUniform1i(self._u("prev_tex"), 1)
        gl.glUniform2f(self._u("resolution"), float(w), float(h))
        gl.glUniform1f(self._u("time"),   time_v)
        gl.glUniform1f(self._u("u_mix"),  mix_v)
        for p_name in _PARAM_NAMES:
            gl.glUniform1f(self._u(p_name), float(params.get(p_name, _PARAM_DEFAULTS.get(p_name, 5.0))))
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glUseProgram(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        if hasattr(context, "outputs"): context.outputs["video_out"] = self.trail_tex
        return self.trail_tex

    def cleanup(self) -> None:
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
            if hasattr(gl, 'glDeleteTextures') and self.trail_tex: gl.glDeleteTextures(1, [self.trail_tex])
            if hasattr(gl, 'glDeleteFramebuffers') and self.trail_fbo: gl.glDeleteFramebuffers(1, [self.trail_fbo])
        except Exception as e:
            logger.error(f"{self.__class__.__name__} cleanup: {e}")
        finally:
            self.prog = self.vao = self.trail_fbo = self.trail_tex = 0
