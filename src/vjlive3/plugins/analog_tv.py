"""
P3-EXT006: Analog TV Effect — Complete analog video degradation simulator.

Recreates CRT, VHS, and RF artifacts: barrel distortion, scanlines, phosphor mask,
VHS tracking errors, dropouts, RF interference, color bleeding, macro glitches.

Ported from VJLive-2: core/effects/analog_tv.py (374 lines)
"""
from typing import Dict
import logging
try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
# # from .api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

# ── Parameter table ────────────────────────────────────────────────────────────
# (name, default, lo, hi)
_PARAMS: tuple = (
    # VHS Physical
    ("vhs_tracking",    0.0, 0.0,  1.0),
    ("vhs_jitter",      1.0, 0.0,  0.02),
    ("tape_noise",      2.0, 0.0,  1.0),
    ("tape_wrinkle",    0.0, 0.0,  1.0),
    ("head_switch",     1.0, 0.0,  1.0),
    ("dropout_rate",    0.5, 0.0,  0.3),
    ("dropout_length",  2.0, 0.01, 0.5),
    ("tape_speed",      5.0, 0.5,  3.0),
    # CRT Display
    ("crt_curvature",   2.0, 0.0,  0.5),
    ("crt_scanlines",   3.0, 0.0,  1.0),
    ("scanline_freq",   7.0, 200.0,1080.0),
    ("phosphor_mask",   2.0, 0.0,  1.0),
    ("phosphor_glow",   2.0, 0.0,  2.0),
    ("convergence",     1.0, 0.0,  0.005),
    ("corner_shadow",   3.0, 0.0,  1.0),
    ("brightness",      5.5, 0.5,  2.0),
    # RF/Signal
    ("rf_noise",        1.0, 0.0,  0.3),
    ("rf_pattern",      0.0, 0.0,  1.0),
    ("color_bleed",     2.0, 0.0,  0.01),
    ("chroma_delay",    1.0, 0.0,  0.005),
    ("chroma_noise",    1.0, 0.0,  0.1),
    ("luma_sharpen",    3.0, 0.0,  2.0),
    # Glitch/Extreme
    ("glitch_intensity",0.0, 0.0,  1.0),
    ("rolling",         0.0, 0.0,  1.0),
    ("rolling_speed",   3.0, 0.1,  5.0),
    ("interlace",       0.0, 0.0,  1.0),
    ("snow",            0.0, 0.0,  1.0),
    ("color_kill",      0.0, 0.0,  1.0),
)

METADATA = {
    "name": "Analog TV",
    "description": "Complete analog video degradation simulator: CRT, VHS, RF artifacts, and glitches.",
    "version": "2.0.0",
    "plugin_type": "effect",
    "category": "stylize",
    "tags": ["analog", "vhs", "crt", "glitch", "retro", "stylize"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [{"name": n, "type": "float", "default": d, "min": 0.0, "max": 10.0}
                   for n, d, *_ in _PARAMS] + [
        {"name": "mix", "type": "float", "default": 8.0, "min": 0.0, "max": 10.0}
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
in vec2 uv; out vec4 fragColor;
uniform sampler2D tex0;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// VHS
uniform float vhs_tracking; uniform float vhs_jitter; uniform float tape_noise;
uniform float tape_wrinkle;  uniform float head_switch;  uniform float dropout_rate;
uniform float dropout_length; uniform float tape_speed;
// CRT
uniform float crt_curvature; uniform float crt_scanlines; uniform float scanline_freq;
uniform float phosphor_mask; uniform float phosphor_glow; uniform float convergence;
uniform float corner_shadow; uniform float brightness;
// RF
uniform float rf_noise; uniform float rf_pattern; uniform float color_bleed;
uniform float chroma_delay; uniform float chroma_noise; uniform float luma_sharpen;
// Glitch
uniform float glitch_intensity; uniform float rolling; uniform float rolling_speed;
uniform float interlace; uniform float snow; uniform float color_kill;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float hash1(float p) { return fract(sin(p * 127.1) * 43758.5453); }

vec3 rgb2yiq(vec3 c) {
    return vec3(dot(c, vec3(0.299, 0.587, 0.114)),
                dot(c, vec3(0.596,-0.274,-0.322)),
                dot(c, vec3(0.212,-0.523, 0.311)));
}
vec3 yiq2rgb(vec3 c) {
    return vec3(c.x + 0.956*c.y + 0.621*c.z,
                c.x - 0.272*c.y - 0.647*c.z,
                c.x - 1.106*c.y + 1.703*c.z);
}

void main() {
    // Vertical rolling
    vec2 vuv = uv;
    if (rolling > 0.0) {
        float roll_offset = fract(time * rolling_speed * 0.1) * rolling;
        vuv.y = fract(vuv.y + roll_offset);
    }

    // CRT barrel distortion
    vec2 cuv = vuv;
    if (crt_curvature > 0.0) {
        vec2 cc = vuv * 2.0 - 1.0;
        cc *= 1.0 + dot(cc, cc) * crt_curvature * 0.3;
        cuv = cc * 0.5 + 0.5;
        if (cuv.x < 0.0 || cuv.x > 1.0 || cuv.y < 0.0 || cuv.y > 1.0) {
            fragColor = vec4(0.0); return;
        }
    }

    // VHS tracking error
    vec2 tvuv = cuv;
    if (vhs_tracking > 0.0) {
        float bar1 = smoothstep(0.05, 0.0, abs(cuv.y - fract(time*tape_speed*0.1 + 0.3)));
        float bar2 = smoothstep(0.04, 0.0, abs(cuv.y - fract(time*tape_speed*0.07 + 0.7)));
        tvuv.x += (bar1 * 0.4 + bar2 * 0.2) * vhs_tracking * sin(time * 40.0 + cuv.y * 30.0);
    }

    // Line jitter
    if (vhs_jitter > 0.0) {
        float sl = floor(cuv.y * resolution.y);
        tvuv.x += (hash1(sl + floor(time * 30.0)) - 0.5) * 2.0 * vhs_jitter;
    }

    // Tape wrinkle
    if (tape_wrinkle > 0.0) {
        tvuv.y += tape_wrinkle * 0.005 * sin(tvuv.x * 40.0 + time * 3.0);
    }

    // Head switching noise  (bottom strip)
    if (head_switch > 0.0) {
        if (cuv.y < 0.04) {
            tvuv.x += (hash(vec2(cuv.y * 100.0, time)) - 0.5) * head_switch * 0.6;
        }
    }

    // Glitch macro
    if (glitch_intensity > 0.0) {
        float gtime = floor(time * 20.0);
        float gseed = hash(vec2(gtime, 0.0));
        if (gseed < glitch_intensity * 0.15) {
            float gbar = hash(vec2(gtime, 1.0));
            float gstrip = smoothstep(0.05, 0.02, abs(cuv.y - gbar));
            tvuv.x += gstrip * (hash(vec2(gtime, 2.0)) - 0.5) * 0.4;
        }
    }

    tvuv = clamp(tvuv, 0.0, 1.0);

    // Sample with convergence error (RGB offset)
    vec2 off = vec2(convergence, 0.0);
    float r = texture(tex0, tvuv + off).r;
    float gv = texture(tex0, tvuv).g;
    float b = texture(tex0, tvuv - off).b;
    vec3 col = vec3(r, gv, b);

    // Color bleeding
    if (color_bleed > 0.0) {
        col.r = mix(col.r, texture(tex0, tvuv + vec2(color_bleed * 2.0, 0.0)).r, 0.5);
        col.b = mix(col.b, texture(tex0, tvuv - vec2(color_bleed, 0.0)).b, 0.3);
    }

    // YIQ processing
    vec3 yiq = rgb2yiq(col);

    // Luma sharpening
    if (luma_sharpen > 0.0) {
        float px = 1.0 / resolution.x;
        float lu = texture(tex0, tvuv + vec2(px, 0.0)).r * 0.299 + texture(tex0, tvuv + vec2(px, 0.0)).g * 0.587 + texture(tex0, tvuv + vec2(px, 0.0)).b * 0.114;
        float ll = texture(tex0, tvuv - vec2(px, 0.0)).r * 0.299 + texture(tex0, tvuv - vec2(px, 0.0)).g * 0.587 + texture(tex0, tvuv - vec2(px, 0.0)).b * 0.114;
        yiq.x = clamp(yiq.x + (yiq.x - (lu + ll) * 0.5) * luma_sharpen, 0.0, 1.0);
    }

    // Chroma delay
    if (chroma_delay > 0.0) {
        vec3 yiq2 = rgb2yiq(texture(tex0, tvuv + vec2(chroma_delay, 0.0)).rgb);
        yiq.y = yiq2.y; yiq.z = yiq2.z;
    }

    // Chroma noise
    if (chroma_noise > 0.0) {
        yiq.y += (hash(tvuv * resolution + time * 50.0) - 0.5) * chroma_noise * 2.0;
        yiq.z += (hash(tvuv * resolution + time * 70.0 + 100.0) - 0.5) * chroma_noise * 2.0;
    }

    col = clamp(yiq2rgb(yiq), 0.0, 1.0);

    // RF noise
    if (rf_noise > 0.0) {
        float rn = hash(tvuv * resolution + time * 100.0) - 0.5;
        col += rn * rf_noise;
    }

    // RF pattern
    if (rf_pattern > 0.0) {
        float rp = sin(tvuv.y * 800.0 + time * 50.0) * 0.5 + 0.5;
        col += rp * rf_pattern * 0.15;
    }

    // Tape noise streaks
    if (tape_noise > 0.0) {
        float tn = hash(vec2(floor(tvuv.y * resolution.y), time * 20.0));
        if (tn > 1.0 - tape_noise * 0.3) {
            float noise_v = hash(vec2(tvuv.x * resolution.x, tn)) - 0.5;
            col += noise_v * 0.5;
        }
    }

    // Dropouts
    if (dropout_rate > 0.0) {
        float dsl = floor(tvuv.y * resolution.y);
        float dseed = hash(vec2(dsl, floor(time * 24.0)));
        if (dseed < dropout_rate) {
            float start = hash(vec2(dsl, 1.0));
            float len_v = 0.01 + hash(vec2(dsl, 2.0)) * dropout_length;
            if (tvuv.x >= start && tvuv.x <= start + len_v) {
                col = mix(col, vec3(hash(vec2(dsl, 3.0))), 0.8);
            }
        }
    }

    // Scanlines
    if (crt_scanlines > 0.0) {
        float sl = sin(tvuv.y * scanline_freq * 3.14159) * 0.5 + 0.5;
        col *= 1.0 - crt_scanlines * (1.0 - sl) * 0.6;
    }

    // Interlace
    if (interlace > 0.0) {
        if (mod(floor(tvuv.y * resolution.y), 2.0) < 0.5) {
            col = mix(col, texture(tex0, tvuv + vec2(0.0, 1.0/resolution.y)).rgb, interlace * 0.5);
        }
    }

    // Phosphor mask (RGB subpixels)
    if (phosphor_mask > 0.0) {
        float px_w = tvuv.x * resolution.x;
        float sub = mod(px_w, 3.0);
        vec3 mask = vec3(step(sub, 1.0), step(1.0, sub) * step(sub, 2.0), step(2.0, sub));
        col = mix(col, col * (0.6 + 0.4 * mask), phosphor_mask);
    }

    // Phosphor glow
    if (phosphor_glow > 0.0) {
        float luma = dot(col, vec3(0.299, 0.587, 0.114));
        col += luma * phosphor_glow * 0.3;
    }

    // Corner shadow (vignette)
    if (corner_shadow > 0.0) {
        vec2 cv = tvuv * 2.0 - 1.0;
        float vign = 1.0 - dot(cv, cv) * corner_shadow * 0.5;
        col *= clamp(vign, 0.0, 1.0);
    }

    // Brightness
    col *= brightness;

    // Snow (no-signal)
    if (snow > 0.0) {
        float sn = hash(tvuv * resolution + time * 200.0);
        col = mix(col, vec3(sn), snow);
    }

    // Color kill (B&W)
    if (color_kill > 0.0) {
        float luma = dot(col, vec3(0.299, 0.587, 0.114));
        col = mix(col, vec3(luma), color_kill);
    }

    col = clamp(col, 0.0, 1.0);
    fragColor = mix(texture(tex0, uv), vec4(col, 1.0), u_mix);
}
"""

# Param defaults (raw 0-10 space)
_DEFAULTS: Dict[str, float] = {n: d for n, d, *_ in _PARAMS}
# Param ranges for remapping
_RANGES: Dict[str, tuple] = {n: (lo, hi) for n, d, lo, hi in _PARAMS}

PRESETS = {
    "clean_crt":       {"vhs_tracking": 0.0, "vhs_jitter": 0.0, "tape_noise": 0.0,
                        "crt_curvature": 2.0, "crt_scanlines": 3.0, "scanline_freq": 7.0,
                        "phosphor_mask": 2.0, "phosphor_glow": 2.0, "corner_shadow": 3.0},
    "vhs_degradation": {"vhs_tracking": 5.0, "vhs_jitter": 4.0, "tape_noise": 5.0,
                        "dropout_rate": 3.0, "dropout_length": 3.0, "head_switch": 4.0,
                        "crt_scanlines": 3.0},
    "rf_interference": {"rf_noise": 6.0, "rf_pattern": 5.0, "color_bleed": 7.0,
                        "chroma_delay": 5.0, "chroma_noise": 6.0, "luma_sharpen": 4.0},
    "extreme_glitch":  {"glitch_intensity": 8.0, "rolling": 7.0, "snow": 5.0,
                        "vhs_tracking": 7.0, "tape_noise": 8.0, "rf_noise": 5.0},
    "retro_bw":        {"color_kill": 10.0, "crt_scanlines": 6.0, "phosphor_mask": 5.0,
                        "corner_shadow": 5.0, "brightness": 5.5, "crt_curvature": 2.0},
}


def _remap(name: str, val_0_10: float) -> float:
    lo, hi = _RANGES.get(name, (0., 1.))
    return lo + (hi - lo) * (max(0., min(10., val_0_10)) / 10.)


class AnalogTVPlugin(object):
    """Analog TV degradation effect — CRT, VHS, RF and glitch artifacts."""

    def __init__(self):
        super().__init__()
        self._mock_mode   = not HAS_GL
        self.prog = self.vao = 0
        self._initialized = False

    def get_metadata(self): return METADATA

    def _compile(self, vs, fs):
        v = gl.glCreateShader(gl.GL_VERTEX_SHADER);  gl.glShaderSource(v, vs); gl.glCompileShader(v)
        if not gl.glGetShaderiv(v, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(v))
        f = gl.glCreateShader(gl.GL_FRAGMENT_SHADER); gl.glShaderSource(f, fs); gl.glCompileShader(f)
        if not gl.glGetShaderiv(f, gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(f))
        p = gl.glCreateProgram(); gl.glAttachShader(p, v); gl.glAttachShader(p, f); gl.glLinkProgram(p)
        if not gl.glGetProgramiv(p, gl.GL_LINK_STATUS): raise RuntimeError(gl.glGetProgramInfoLog(p))
        gl.glDeleteShader(v); gl.glDeleteShader(f); return p

    def _u(self, n): return gl.glGetUniformLocation(self.prog, n)

    def initialize(self, context):
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao  = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"AnalogTVPlugin init: {e}"); self._mock_mode = True; return False

    def process_frame(self, input_texture, params, context):
        if not input_texture or input_texture <= 0: return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
            return input_texture
        if not self._initialized: self.initialize(context)
        w = getattr(context, 'width', 1920); h = getattr(context, 'height', 1080)
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u('tex0'), 0)
        gl.glUniform2f(self._u('resolution'), float(w), float(h))
        gl.glUniform1f(self._u('time'), float(getattr(context, 'time', 0.)))
        gl.glUniform1f(self._u('u_mix'), max(0., min(10., float(params.get('mix', 8.)))) / 10.)
        for n, d, *_ in _PARAMS:
            val = float(params.get(n, d))
            gl.glUniform1f(self._u(n), _remap(n, val))
        gl.glBindVertexArray(self.vao); gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0); gl.glUseProgram(0)
        if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
        return input_texture

    def cleanup(self):
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
        except Exception as e: logger.error(f"AnalogTVPlugin cleanup: {e}")
        finally: self.prog = self.vao = 0
