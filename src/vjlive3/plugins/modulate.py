"""
P5-MO03: Modulate Effect Plugin for VJLive3.
Ported from VJlive-2/core/effects/blend.py::ModulateEffect.

UV displacement driven by a self-feedback texture (prev frame via trail FBO).
8 parameters control displacement strength, direction modes (XY/radial/twist/zoom/barrel),
oscillation frequency, displacement source channel, and iterative application.
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
    "name": "Modulate",
    "description": "UV displacement using self-feedback as a displacement map.",
    "version": "1.0.0",
    "plugin_type": "effect",
    "category": "blend",
    "tags": ["modulate", "displacement", "warp", "spatial", "feedback", "reactive"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "amount",       "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "direction",    "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "frequency",    "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "source_blur",  "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "quantize",     "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "iterations",   "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "channel_src",  "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "feedback_mix", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
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
uniform sampler2D prev_tex;
uniform vec2  resolution;
uniform float time;
uniform float u_mix;

uniform float amount;
uniform float direction;
uniform float frequency;
uniform float source_blur;
uniform float quantize;
uniform float iterations;
uniform float channel_src;
uniform float feedback_mix;

void main() {
    vec4 input_color = texture(tex0, uv);
    float a   = amount / 10.0 * 0.5;
    float dir = direction / 10.0 * 4.0;
    float freq = frequency / 10.0 * 5.0;
    float sb  = source_blur / 10.0 * 3.0;
    float quant = quantize / 10.0 * 16.0;
    float iters = 1.0 + iterations / 10.0 * 4.0;
    float cs  = channel_src / 10.0 * 4.0;
    float fb  = feedback_mix / 10.0;

    // Sample displacement source
    vec4 mod_source;
    if (sb > 0.1) {
        vec2 px = 1.0 / resolution;
        mod_source = vec4(0.0);
        float total = 0.0;
        for (float dx = -1.0; dx <= 1.0; dx++) {
            for (float dy = -1.0; dy <= 1.0; dy++) {
                float w = exp(-(dx*dx + dy*dy) / (sb + 0.01));
                mod_source += texture(prev_tex, uv + vec2(dx, dy) * px * sb) * w;
                total += w;
            }
        }
        mod_source /= total;
    } else {
        mod_source = texture(prev_tex, uv);
    }

    if (fb > 0.01) mod_source = mix(mod_source, input_color, fb);

    // Extract displacement vector
    vec2 raw_disp;
    if (cs < 1.0) {
        raw_disp = mod_source.rg - 0.5;
    } else if (cs < 2.0) {
        float luma = dot(mod_source.rgb, vec3(0.299, 0.587, 0.114));
        raw_disp = vec2(luma - 0.5);
    } else if (cs < 3.0) {
        float maxc = max(max(mod_source.r, mod_source.g), mod_source.b);
        float minc = min(min(mod_source.r, mod_source.g), mod_source.b);
        raw_disp = vec2(maxc - minc - 0.3, mod_source.r - mod_source.b);
    } else if (cs < 4.0) {
        raw_disp = vec2(mod_source.r - 0.5, 0.0);
    } else {
        vec2 px = 1.0 / resolution;
        float gx = texture(prev_tex, uv + vec2(px.x, 0.0)).r - texture(prev_tex, uv - vec2(px.x, 0.0)).r;
        float gy = texture(prev_tex, uv + vec2(0.0, px.y)).r - texture(prev_tex, uv - vec2(0.0, px.y)).r;
        raw_disp = vec2(gx, gy) * 5.0;
    }

    // Quantize
    if (quant > 1.5) raw_disp = floor(raw_disp * quant) / quant;

    // Oscillation
    if (freq > 0.01) raw_disp *= sin(time * freq * 3.14159) * 0.5 + 0.5;

    // Iterative displacement (max 5)
    vec2 displaced_uv = uv;
    int iter_count = int(iters);
    for (int i = 0; i < 5; i++) {
        if (i >= iter_count) break;
        vec2 offset;
        if (dir < 1.0) {
            offset = raw_disp * 2.0 * a;
        } else if (dir < 2.0) {
            vec2 to_c = displaced_uv - 0.5;
            float dist = length(to_c);
            offset = normalize(to_c + vec2(0.0001)) * raw_disp.x * a * dist * 3.0;
        } else if (dir < 3.0) {
            vec2 to_c = displaced_uv - 0.5;
            vec2 tang = vec2(-to_c.y, to_c.x);
            offset = tang * raw_disp.x * a * 3.0;
        } else if (dir < 4.0) {
            offset = (displaced_uv - 0.5) * raw_disp.x * a * 2.0;
        } else {
            float r2 = dot(displaced_uv - 0.5, displaced_uv - 0.5);
            offset = (displaced_uv - 0.5) * r2 * raw_disp.x * a * 8.0;
        }
        displaced_uv += offset / float(iter_count);
    }

    vec4 modulated = texture(tex0, clamp(displaced_uv, 0.0, 1.0));
    fragColor = mix(input_color, modulated, u_mix);
}
"""


def _map(val: float, out_min: float, out_max: float) -> float:
    t = max(0.0, min(10.0, float(val))) / 10.0
    return out_min + t * (out_max - out_min)


class ModulatePlugin(object):
    """UV displacement using self-feedback. Trail FBO provides prev-frame source."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = 0
        self.vao = 0
        self.trail_fbo = 0
        self.trail_tex = 0
        self._w = self._h = 0
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

    def _make_fbo(self, w: int, h: int):
        fbo = gl.glGenFramebuffers(1)
        tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0,
                        gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0,
                                   gl.GL_TEXTURE_2D, tex, 0)
        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        return fbo, tex

    def initialize(self, context) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True
            return True
        try:
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao  = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Modulate init failed: {e}")
            self._mock_mode = True
            return False

    def _u(self, name: str) -> int:
        return gl.glGetUniformLocation(self.prog, name)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0:
            return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
        if not self._initialized:
            self.initialize(context)

        w = getattr(context, "width",  1920)
        h = getattr(context, "height", 1080)
        if w != self._w or h != self._h:
            if self.trail_fbo:
                try:
                    gl.glDeleteFramebuffers(1, [self.trail_fbo])
                    gl.glDeleteTextures(1, [self.trail_tex])
                except Exception:
                    pass
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
        gl.glUniform1f(self._u("time"),        time_v)
        gl.glUniform1f(self._u("u_mix"),       mix_v)
        gl.glUniform1f(self._u("amount"),      float(params.get("amount",       2.0)))
        gl.glUniform1f(self._u("direction"),   float(params.get("direction",    0.0)))
        gl.glUniform1f(self._u("frequency"),   float(params.get("frequency",    0.0)))
        gl.glUniform1f(self._u("source_blur"), float(params.get("source_blur",  0.0)))
        gl.glUniform1f(self._u("quantize"),    float(params.get("quantize",     0.0)))
        gl.glUniform1f(self._u("iterations"),  float(params.get("iterations",   0.0)))
        gl.glUniform1f(self._u("channel_src"), float(params.get("channel_src",  0.0)))
        gl.glUniform1f(self._u("feedback_mix"),float(params.get("feedback_mix", 0.0)))

        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glUseProgram(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.trail_tex
        return self.trail_tex

    def cleanup(self) -> None:
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog:
                gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao:
                gl.glDeleteVertexArrays(1, [self.vao])
            if hasattr(gl, 'glDeleteTextures') and self.trail_tex:
                gl.glDeleteTextures(1, [self.trail_tex])
            if hasattr(gl, 'glDeleteFramebuffers') and self.trail_fbo:
                gl.glDeleteFramebuffers(1, [self.trail_fbo])
        except Exception as e:
            logger.error(f"Modulate cleanup: {e}")
        finally:
            self.prog = self.vao = self.trail_fbo = self.trail_tex = 0
