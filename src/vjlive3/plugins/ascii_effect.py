"""
P3-EXT001: ASCII Effect — Transform video into living typography.

The screen becomes a terminal from an alternate dimension. Every pixel cluster
maps to a character whose shape echoes the luminance and structure beneath.
Multiple character sets, color modes, and a CRT phosphor simulation turn modern
video into the visual language of machines.

Ported from VJLive-2: plugins/core/ascii_effect/__init__.py
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
    "name": "ASCII Effect",
    "description": "Transform video into living typography with CRT simulation.",
    "version": "1.0.0",
    "plugin_type": "effect",
    "category": "stylize",
    "tags": ["ascii", "text", "matrix", "retro", "code", "glitch", "crt"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        # Grid
        {"name": "cell_size",       "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "aspect_correct",  "type": "float", "default": 6.0, "min": 0.0, "max": 10.0},
        # Character mapping
        {"name": "charset",         "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "threshold_curve", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "edge_detect",     "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "detail_boost",    "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        # Color
        {"name": "color_mode",      "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "fg_brightness",   "type": "float", "default": 6.0, "min": 0.0, "max": 10.0},
        {"name": "bg_brightness",   "type": "float", "default": 1.0, "min": 0.0, "max": 10.0},
        {"name": "saturation",      "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "hue_offset",      "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        # CRT simulation
        {"name": "scanlines",       "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "phosphor_glow",   "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "flicker",         "type": "float", "default": 1.0, "min": 0.0, "max": 10.0},
        {"name": "curvature",       "type": "float", "default": 2.0, "min": 0.0, "max": 10.0},
        {"name": "noise_amount",    "type": "float", "default": 1.0, "min": 0.0, "max": 10.0},
        # Animation
        {"name": "scroll_speed",    "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "rain_density",    "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "char_jitter",     "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "wave_amount",     "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "wave_freq",       "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        # Output
        {"name": "mix",             "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
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
uniform float cell_size;
uniform float aspect_correct;
uniform float charset;
uniform float threshold_curve;
uniform float edge_detect;
uniform float detail_boost;
uniform float color_mode;
uniform float fg_brightness;
uniform float bg_brightness;
uniform float saturation;
uniform float hue_offset;
uniform float scanlines;
uniform float phosphor_glow;
uniform float flicker;
uniform float curvature;
uniform float noise_amount;
uniform float scroll_speed;
uniform float rain_density;
uniform float char_jitter;
uniform float wave_amount;
uniform float wave_freq;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float hash3(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + 1e-10)), d / (q.x + 1e-10), q.x);
}
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

float render_char(vec2 local_uv, float char_index, int charset_id) {
    float ci = floor(char_index * 10.0);
    vec2 p = local_uv;
    if (charset_id == 0) {
        float density = ci / 10.0;
        if (density < 0.1) return 0.0;
        if (density < 0.3) { float d = length(p - 0.5); return step(0.5 - density * 0.8, 1.0 - d); }
        if (density < 0.6) { float cross = step(abs(p.x-0.5), density*0.3) + step(abs(p.y-0.5), density*0.2); return min(cross, 1.0); }
        float fill = density;
        return step(fract(p.x*3.0), fill) * step(fract(p.y*3.0), fill) * density;
    } else if (charset_id == 1) {
        float density = char_index;
        float block = step(1.0 - density, p.y) + step(1.0 - density, p.x) * 0.5;
        return clamp(block * density, 0.0, 1.0);
    } else if (charset_id == 2) {
        float density = char_index;
        vec2 grid_pos = floor(p * vec2(2.0, 4.0));
        float dot_idx = grid_pos.x + grid_pos.y * 2.0;
        vec2 dot_center = (grid_pos + 0.5) / vec2(2.0, 4.0);
        float d = length(p - dot_center);
        return step(dot_idx / 8.0, density) * smoothstep(0.15, 0.1, d);
    } else if (charset_id == 3) {
        float h = hash(vec2(ci, floor(time * 3.0)));
        float bar_h = step(abs(p.x - h), 0.15);
        float bar_v = step(abs(p.y - fract(h * 7.0)), 0.15);
        float corner = step(length(p - vec2(h, fract(h * 3.0))), 0.2);
        return clamp(bar_h + bar_v + corner, 0.0, 1.0) * char_index;
    } else if (charset_id == 4) {
        float bit = step(0.5, char_index);
        if (bit < 0.5) {
            float ring = abs(length(p - 0.5) - 0.25);
            return smoothstep(0.08, 0.03, ring);
        } else {
            float bar = step(abs(p.x - 0.5), 0.08);
            float hat = step(abs(p.x - 0.35), 0.08) * step(0.3, p.y) * step(p.y, 0.5);
            float base = step(abs(p.y - 0.15), 0.04) * step(0.3, p.x) * step(p.x, 0.7);
            return clamp(bar + hat + base, 0.0, 1.0);
        }
    }
    return step(1.0 - char_index, hash(p * 10.0 + ci));
}

void main() {
    float csize = mix(4.0, 32.0, cell_size / 10.0);
    float aspect = mix(0.4, 1.0, aspect_correct / 10.0);
    int charset_id = int(charset / 10.0 * 4.0 + 0.5);
    float t_curve = mix(0.3, 3.0, threshold_curve / 10.0);
    float edge_mix = edge_detect / 10.0;
    float detail  = detail_boost / 10.0 * 3.0;
    int   cmode   = int(color_mode / 10.0 * 5.0 + 0.5);
    float fg_b    = mix(0.3, 3.0, fg_brightness / 10.0);
    float bg_b    = bg_brightness / 10.0 * 0.5;
    float sat     = saturation / 10.0 * 2.0;
    float hue_off = hue_offset / 10.0;
    float scan    = scanlines / 10.0;
    float glow    = phosphor_glow / 10.0 * 2.0;
    float flick   = flicker / 10.0 * 0.1;
    float curve   = curvature / 10.0 * 0.3;
    float noise_amt = noise_amount / 10.0 * 0.15;
    float scroll  = (scroll_speed / 10.0 - 0.5) * 10.0;
    float rain    = rain_density / 10.0;
    float jitter  = char_jitter / 10.0;
    float wave_a  = wave_amount / 10.0 * 0.5;
    float wave_f  = mix(1.0, 20.0, wave_freq / 10.0);

    vec2 cuv = uv;
    if (curve > 0.0) {
        vec2 cc = uv * 2.0 - 1.0;
        cc *= 1.0 + dot(cc, cc) * curve;
        cuv = cc * 0.5 + 0.5;
        if (cuv.x < 0.0 || cuv.x > 1.0 || cuv.y < 0.0 || cuv.y > 1.0) { fragColor = vec4(0.0); return; }
    }
    if (wave_a > 0.0) {
        cuv.x += sin(cuv.y * wave_f + time * 2.0) * wave_a;
        cuv.y += cos(cuv.x * wave_f * 0.7 + time * 1.5) * wave_a * 0.3;
    }

    vec2 cell_px = vec2(csize, csize / aspect);
    vec2 grid_pos = floor(cuv * resolution / cell_px);
    vec2 cell_uv  = fract(cuv * resolution / cell_px);
    vec2 cell_center = (grid_pos + 0.5) * cell_px / resolution;

    vec4 src = texture(tex0, cell_center);
    float luma = dot(src.rgb, vec3(0.299, 0.587, 0.114));

    if (edge_mix > 0.0) {
        vec2 tx = cell_px / resolution;
        float l = dot(texture(tex0, cell_center - vec2(tx.x, 0.0)).rgb, vec3(0.299,0.587,0.114));
        float r = dot(texture(tex0, cell_center + vec2(tx.x, 0.0)).rgb, vec3(0.299,0.587,0.114));
        float dv = dot(texture(tex0, cell_center - vec2(0.0, tx.y)).rgb, vec3(0.299,0.587,0.114));
        float u2 = dot(texture(tex0, cell_center + vec2(0.0, tx.y)).rgb, vec3(0.299,0.587,0.114));
        luma = mix(luma, (abs(l-r) + abs(dv-u2)) * 3.0, edge_mix);
    }
    luma = clamp(pow(luma, t_curve) * (1.0 + detail), 0.0, 1.0);

    float char_idx = luma;
    if (jitter > 0.0) {
        float j = hash3(vec3(grid_pos, floor(time * 10.0)));
        if (j < jitter * 0.3) char_idx = hash(grid_pos + floor(time * 5.0));
    }

    float rain_alpha = 0.0;
    if (rain > 0.0) {
        float column_hash = hash(vec2(grid_pos.x, 0.0));
        if (column_hash < rain) {
            float drop_pos = fract(time * scroll * 0.1 + column_hash * 10.0);
            float cell_y   = grid_pos.y / (resolution.y / cell_px.y);
            float trail = smoothstep(drop_pos, drop_pos - 0.3, cell_y) * step(cell_y, drop_pos);
            rain_alpha = trail;
            char_idx = max(char_idx, hash3(vec3(grid_pos, floor(time * 8.0))) * trail);
        }
    }

    float char_pixel = render_char(cell_uv, char_idx, charset_id);

    vec3 fg_color; vec3 bg_color = vec3(bg_b);
    if (cmode == 0) {
        fg_color = vec3(0.1, 1.0, 0.3) * fg_b; bg_color = vec3(0.0, bg_b*0.3, 0.0);
    } else if (cmode == 1) {
        fg_color = vec3(1.0, 0.7, 0.1) * fg_b; bg_color = vec3(bg_b*0.3, bg_b*0.2, 0.0);
    } else if (cmode == 2) {
        vec3 hsv = rgb2hsv(src.rgb); hsv.y *= sat; hsv.z = fg_b; fg_color = hsv2rgb(hsv);
    } else if (cmode == 3) {
        vec3 hsv = rgb2hsv(src.rgb); hsv.x = fract(hsv.x + hue_off); hsv.y = min(hsv.y*sat, 1.0); hsv.z = fg_b; fg_color = hsv2rgb(hsv);
    } else if (cmode == 4) {
        float rh = fract(hue_off + grid_pos.x/40.0 + grid_pos.y/60.0 + time*0.05);
        fg_color = hsv2rgb(vec3(rh, 0.9, fg_b));
    } else {
        float temp = luma;
        fg_color = vec3(smoothstep(0.3,0.7,temp)*2.0, smoothstep(0.5,0.8,temp),
                       smoothstep(0.0,0.3,temp)*(1.0-smoothstep(0.5,0.9,temp))) * fg_b;
    }
    if (rain_alpha > 0.0) fg_color = mix(fg_color, vec3(0.0,1.0,0.3)*fg_b, rain_alpha);

    vec3 color = mix(bg_color, fg_color, char_pixel);

    if (glow > 0.0) {
        vec2 tx = 1.0 / resolution;
        float glow_sum = 0.0;
        for (float dx = -1.0; dx <= 1.0; dx += 1.0)
            for (float dy = -1.0; dy <= 1.0; dy += 1.0) {
                if (dx == 0.0 && dy == 0.0) continue;
                vec2 nc = cell_center + vec2(dx,dy) * cell_px / resolution;
                float n_luma = dot(texture(tex0, nc).rgb, vec3(0.299,0.587,0.114));
                glow_sum += pow(n_luma, t_curve) * 0.1;
            }
        color += fg_color * glow_sum * glow;
    }
    if (scan > 0.0) { float sl = sin(cuv.y * resolution.y * 3.14159) * 0.5 + 0.5; color *= 1.0 - scan*(1.0-sl)*0.5; }
    color *= 1.0 - flick * sin(time * 60.0);
    if (noise_amt > 0.0) color += (hash(cuv*resolution + time*100.0) - 0.5) * noise_amt;

    fragColor = mix(texture(tex0, uv), vec4(clamp(color,0.,1.), 1.0), u_mix);
}
"""

_PARAM_NAMES = [
    "cell_size", "aspect_correct", "charset", "threshold_curve", "edge_detect",
    "detail_boost", "color_mode", "fg_brightness", "bg_brightness", "saturation",
    "hue_offset", "scanlines", "phosphor_glow", "flicker", "curvature",
    "noise_amount", "scroll_speed", "rain_density", "char_jitter", "wave_amount",
    "wave_freq",
]
_PARAM_DEFAULTS = {
    "cell_size": 4.0, "aspect_correct": 6.0, "charset": 0.0, "threshold_curve": 5.0,
    "edge_detect": 0.0, "detail_boost": 3.0, "color_mode": 0.0, "fg_brightness": 6.0,
    "bg_brightness": 1.0, "saturation": 5.0, "hue_offset": 0.0, "scanlines": 3.0,
    "phosphor_glow": 2.0, "flicker": 1.0, "curvature": 2.0, "noise_amount": 1.0,
    "scroll_speed": 5.0, "rain_density": 0.0, "char_jitter": 0.0, "wave_amount": 0.0,
    "wave_freq": 3.0,
}

PRESETS = {
    "matrix_rain":       {"cell_size": 3.0, "charset": 3.0, "color_mode": 0.0, "fg_brightness": 8.0, "bg_brightness": 0.5, "scanlines": 2.0, "phosphor_glow": 3.0, "rain_density": 5.0, "scroll_speed": 3.0},
    "classic_terminal":  {"cell_size": 4.0, "charset": 0.0, "color_mode": 0.0, "fg_brightness": 7.0, "bg_brightness": 1.0, "scanlines": 4.0, "phosphor_glow": 2.0, "flicker": 2.0, "curvature": 3.0},
    "color_ascii":       {"cell_size": 3.0, "charset": 0.0, "color_mode": 5.0, "fg_brightness": 7.0, "bg_brightness": 0.0, "saturation": 7.0, "edge_detect": 3.0, "detail_boost": 5.0},
    "blocky_pixels":     {"cell_size": 6.0, "charset": 5.0, "color_mode": 5.0, "fg_brightness": 6.0, "bg_brightness": 0.0, "scanlines": 0.0, "noise_amount": 0.0},
    "glitch_text":       {"cell_size": 4.0, "charset": 3.0, "color_mode": 0.0, "fg_brightness": 9.0, "char_jitter": 5.0, "wave_amount": 3.0, "flicker": 4.0, "noise_amount": 3.0},
}


def _map(val, lo, hi): return lo + (max(0., min(10., float(val))) / 10.) * (hi - lo)


class ASCIIPlugin(object):
    """ASCII art effect — character-mapped video with CRT simulation."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = self.vao = 0
        self.trail_fbo = self.trail_tex = 0
        self._w = self._h = 0
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

    def _make_fbo(self, w, h):
        fbo = gl.glGenFramebuffers(1); tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        for k, v2 in [(gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR), (gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR),
                      (gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE), (gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)]:
            gl.glTexParameteri(gl.GL_TEXTURE_2D, k, v2)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
        gl.glClearColor(0, 0, 0, 0); gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0); return fbo, tex

    def initialize(self, context):
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self.vao = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"ASCIIPlugin init: {e}"); self._mock_mode = True; return False

    def _u(self, n): return gl.glGetUniformLocation(self.prog, n)

    def process_frame(self, input_texture, params, context):
        if not input_texture or input_texture <= 0: return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
            return input_texture
        if not self._initialized: self.initialize(context)
        w = getattr(context, 'width', 1920); h = getattr(context, 'height', 1080)
        if w != self._w or h != self._h:
            if self.trail_fbo:
                try: gl.glDeleteFramebuffers(1, [self.trail_fbo]); gl.glDeleteTextures(1, [self.trail_tex])
                except Exception: pass
            self.trail_fbo, self.trail_tex = self._make_fbo(w, h); self._w, self._h = w, h
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.trail_fbo); gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u('tex0'), 0)
        gl.glUniform2f(self._u('resolution'), float(w), float(h))
        gl.glUniform1f(self._u('time'), float(getattr(context, 'time', 0.)))
        gl.glUniform1f(self._u('u_mix'), _map(params.get('mix', 8.), 0., 1.))
        for p in _PARAM_NAMES:
            gl.glUniform1f(self._u(p), float(params.get(p, _PARAM_DEFAULTS.get(p, 5.))))
        gl.glBindVertexArray(self.vao); gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0); gl.glUseProgram(0); gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        if hasattr(context, 'outputs'): context.outputs['video_out'] = self.trail_tex
        return self.trail_tex

    def cleanup(self):
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
            if hasattr(gl, 'glDeleteTextures') and self.trail_tex: gl.glDeleteTextures(1, [self.trail_tex])
            if hasattr(gl, 'glDeleteFramebuffers') and self.trail_fbo: gl.glDeleteFramebuffers(1, [self.trail_fbo])
        except Exception as e: logger.error(f"ASCIIPlugin cleanup: {e}")
        finally: self.prog = self.vao = self.trail_fbo = self.trail_tex = 0
