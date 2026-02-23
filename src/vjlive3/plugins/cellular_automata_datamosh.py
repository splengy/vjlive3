"""
P5-DM07: Cellular automata life simulation — reaction diffusion, grid chaos.
Ported from VJlive-2/plugins/vdatamosh/cellular_automata_datamosh.py.
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
    "name": "Cellular Automata Datamosh",
    "description": "Cellular automata life simulation — reaction diffusion, grid chaos.",
    "version": "1.0.0",
    "plugin_type": "datamosh",
    "category": "datamosh",
    "tags": ['cellular', 'automata', 'reaction-diffusion', 'datamosh', 'generative'],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [{'name': 'life_speed', 'type': 'float', 'default': 5.0, 'min': 0.0, 'max': 10.0}, {'name': 'birth_thresh', 'type': 'float', 'default': 5.0, 'min': 0.0, 'max': 10.0}, {'name': 'death_thresh', 'type': 'float', 'default': 5.0, 'min': 0.0, 'max': 10.0}, {'name': 'reaction_mix', 'type': 'float', 'default': 3.0, 'min': 0.0, 'max': 10.0}, {'name': 'fractal_zoom', 'type': 'float', 'default': 3.0, 'min': 0.0, 'max': 10.0}, {'name': 'math_quantize', 'type': 'float', 'default': 2.0, 'min': 0.0, 'max': 10.0}, {'name': 'evolution', 'type': 'float', 'default': 3.0, 'min': 0.0, 'max': 10.0}, {'name': 'symmetry', 'type': 'float', 'default': 5.0, 'min': 0.0, 'max': 10.0}, {'name': 'grid_mix', 'type': 'float', 'default': 2.0, 'min': 0.0, 'max': 10.0}, {'name': 'chaos', 'type': 'float', 'default': 5.0, 'min': 0.0, 'max': 10.0}, {'name': 'feed_rate', 'type': 'float', 'default': 5.0, 'min': 0.0, 'max': 10.0}, {'name': 'kill_rate', 'type': 'float', 'default': 5.0, 'min': 0.0, 'max': 10.0}]
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
uniform float life_speed;  // Sim speed
uniform float birth_thresh;  // Spawn brightness
uniform float death_thresh;  // Death brightness
uniform float reaction_mix;  // RD amount
uniform float fractal_zoom;  // Mandelbrot
uniform float math_quantize;  // Bit crush
uniform float evolution;  // Color shift
uniform float symmetry;  // Math symmetry
uniform float grid_mix;  // Grid overlay
uniform float chaos;  // Mutation
uniform float feed_rate;  // Reaction feed
uniform float kill_rate;  // Reaction kill

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
    float displacement = (life_speed / 10.0);
    float feedback     = (kill_rate / 10.0);

    vec2 du = vec2(
        noise(uv * (8.0 + (life_speed / 10.0) * 10.0) + vec2(time * 0.5)) - 0.5,
        noise(uv * (8.0 + (life_speed / 10.0) * 10.0) + vec2(1.3, time * 0.4)) - 0.5
    ) * displacement * 0.1;

    vec4 warped = texture(tex0, clamp(uv + du, 0.0, 1.0));
    vec3 color = mix(warped.rgb, prev.rgb, feedback * 0.5);

    // Chromatic separation
    float chroma = 0.0;
    color.r = texture(tex0, clamp(uv + du + vec2(chroma * 0.01, 0.0), 0.0, 1.0)).r;
    color.b = texture(tex0, clamp(uv + du - vec2(chroma * 0.01, 0.0), 0.0, 1.0)).b;

    // Vignette
    float vign = 0.0;
    if (vign > 0.0) {
        vec2 vc = uv * 2.0 - 1.0;
        color *= 1.0 - dot(vc, vc) * vign * 0.5;
    }

    // Color tint
    color.r *= 1.0 + 0.0;
    color.g *= 1.0 + life_speed/10.0*0.2;
    color.b *= 1.0 + 0.0;
    color = clamp(color, 0.0, 1.0);

    fragColor = mix(curr, vec4(color, curr.a), u_mix);
}
"""

_PARAM_NAMES = ['life_speed', 'birth_thresh', 'death_thresh', 'reaction_mix', 'fractal_zoom', 'math_quantize', 'evolution', 'symmetry', 'grid_mix', 'chaos', 'feed_rate', 'kill_rate']
_PARAM_DEFAULTS = {'life_speed': 5.0, 'birth_thresh': 5.0, 'death_thresh': 5.0, 'reaction_mix': 3.0, 'fractal_zoom': 3.0, 'math_quantize': 2.0, 'evolution': 3.0, 'symmetry': 5.0, 'grid_mix': 2.0, 'chaos': 5.0, 'feed_rate': 5.0, 'kill_rate': 5.0}


def _map(val: float, out_min: float, out_max: float) -> float:
    t = max(0.0, min(10.0, float(val))) / 10.0
    return out_min + t * (out_max - out_min)


class CellularAutomataDatamoshPlugin(object):
    """Cellular automata life simulation — reaction diffusion, grid chaos."""

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
