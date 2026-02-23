"""
P4-AU08: ByteBeat Generator Plugin for VJLive3.
Based on VJlive-2 vcv_video_generators (ByteBeatGen class).

ByteBeat is an algorithmic audio+video synthesis technique:
  f(t) = expression involving t (integer), producing a visually and sonically rich
  output from pure integer math.

In VJLive3 we generate a visual pattern from the bytebeat formula where:
  - The XY pixel coordinates substitute for time/space
  - The result is mapped to a colour
  - Audio bass/treble scale the formula parameters

Multiple preset formulas are provided (selected by 0-10 param).
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
    "name": "ByteBeat Generator",
    "description": "Algorithmic visuals from integer bytebeat formulae, audio-reactive scale.",
    "version": "1.0.0",
    "plugin_type": "audio_effect",
    "category": "generator",
    "tags": ["bytebeat", "algorithmic", "generative", "audio", "glitch", "integer"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "formula",          "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "speed",            "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "color_palette",    "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "mix",              "type": "float", "default": 7.0, "min": 0.0, "max": 10.0},
    ]
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
uniform float time;
uniform float speed;
uniform int   formula;
uniform float bass_level;
uniform float treble_level;
uniform int   color_palette;
uniform float u_mix;

// Integer bytebeat formulae simulated in float
// t = pixel-space coordinate (integer-like)
float bytebeat(float tx, float ty) {
    float t = floor(time * speed * 256.0);
    float x = floor(tx * 256.0);
    float y = floor(ty * 256.0);

    float bass_s   = 1.0 + bass_level * 4.0;
    float treble_s = 1.0 + treble_level * 2.0;

    float v = 0.0;
    if (formula == 0) {
        // Classic: t*(t>>5|t>>8)
        float ts = t * bass_s;
        v = mod(ts * (mod(ts, 32.0) + mod(ts, 64.0)) + x + y, 256.0);
    } else if (formula == 1) {
        // XOR: (t^x^y) 
        float ts = t * bass_s;
        v = mod(mod(ts, 256.0) + x + y * treble_s, 256.0);
    } else if (formula == 2) {
        // Tunnel-ish: t/(x^y) pattern
        float denom = max(abs(x - 128.0) + abs(y - 128.0), 1.0);
        v = mod(t * bass_s / denom, 256.0);
    } else {
        // Sine bytebeat  
        float ts = t * bass_s;
        v = mod(ts * sin(x * 0.05 + ts * 0.01) + y * treble_s, 256.0);
    }
    return v / 255.0;
}

vec3 palette(float v, int mode) {
    if (mode == 0) {
        // Greyscale
        return vec3(v);
    } else if (mode == 1) {
        // HSV cycle
        float h = v * 6.0;
        float s = 1.0;
        float r = clamp(abs(mod(h, 6.0) - 3.0) - 1.0, 0.0, 1.0);
        float g = clamp(2.0 - abs(mod(h, 6.0) - 2.0), 0.0, 1.0);
        float b = clamp(2.0 - abs(mod(h, 6.0) - 4.0), 0.0, 1.0);
        return vec3(r, g, b);
    } else {
        // Fire palette
        return vec3(v * 2.0, v * v, v * 0.3);
    }
}

void main() {
    float v = bytebeat(uv.x, uv.y);
    vec3 color = palette(v, color_palette);
    fragColor = mix(texture(tex0, uv), vec4(color, 1.0), u_mix);
}
"""


def _map(val: float, out_min: float, out_max: float) -> float:
    t = max(0.0, min(10.0, float(val))) / 10.0
    return out_min + t * (out_max - out_min)


class ByteBeatGeneratorPlugin(EffectPlugin):
    """ByteBeat visual generator — algorithmic pixel patterns from integer math."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = 0
        self.vao  = 0
        self._initialized = False

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def _compile(self, vs: str, fs: str) -> int:
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

    def initialize(self, context: PluginContext) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True
            return True
        try:
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao  = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"ByteBeatGenerator init failed: {e}")
            self._mock_mode = True
            return False

    def _u(self, name: str) -> int:
        return gl.glGetUniformLocation(self.prog, name)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
            return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
        if not self._initialized:
            self.initialize(context)

        formula = int(_map(params.get("formula",       0.0), 0, 3) + 0.5)
        spd     = _map(params.get("speed",             5.0), 0.1, 4.0)
        palette = int(_map(params.get("color_palette", 0.0), 0, 2) + 0.5)
        mix_v   = _map(params.get("mix",               7.0), 0.0, 1.0)

        inputs = getattr(context, "inputs", {})
        audio  = inputs.get("audio_data", {})
        if not isinstance(audio, dict):
            audio = {}
        bass   = float(audio.get("bass",   0.0))
        treble = float(audio.get("treble", 0.0))
        time_v = float(getattr(context, "time", 0.0))
        w = getattr(context, "width",  1920)
        h = getattr(context, "height", 1080)

        gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u("tex0"), 0)

        gl.glUniform1f(self._u("time"),          time_v)
        gl.glUniform1f(self._u("speed"),         spd)
        gl.glUniform1i(self._u("formula"),       formula)
        gl.glUniform1f(self._u("bass_level"),    bass)
        gl.glUniform1f(self._u("treble_level"),  treble)
        gl.glUniform1i(self._u("color_palette"), palette)
        gl.glUniform1f(self._u("u_mix"),         mix_v)

        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glUseProgram(0)

        if hasattr(context, "outputs"):
            context.outputs["video_out"] = input_texture
        return input_texture

    def cleanup(self) -> None:
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog:
                gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao:
                gl.glDeleteVertexArrays(1, [self.vao])
        except Exception as e:
            logger.error(f"ByteBeatGenerator cleanup: {e}")
        finally:
            self.prog = self.vao = 0
