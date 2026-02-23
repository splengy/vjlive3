"""
P3-EXT040: Depth Acid Fractal Datamosh — neon fractal mayhem at 3AM.
Ported from vjlive/plugins/vdepth/depth_acid_fractal.py

Julia-set fractals use the depth map as the complex parameter — the scene
*becomes* a fractal at depth boundaries. Layered on top:
  - Prismatic RGB splitting (crystal prism dispersion)
  - Sabattier solarization (darkroom partial inversion — alien neon edges)
  - Cross-processing (wrong film chemistry per depth band)
  - Film burn / neon light leaks (depth-contour overexposure)
  - Zoom blur (radial, depth-modulated)
  - Posterization (depth-banded, comic-book neon)
  - Temporal feedback (depth-progressive)

Dreamer analysis: [DREAMER_GENIUS] — the depth-modulated Julia c parameter
is a genuinely original technique. Port faithfully.
"""
from __future__ import annotations

import logging
from typing import Any

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from .api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  METADATA
# ─────────────────────────────────────────────────────────────────────────────

METADATA: dict = {
    "name": "Depth Acid Fractal Datamosh",
    "description": (
        "Julia-set fractals driven by the depth map. Near/far boundaries erupt "
        "into neon fractal outlines. Layered with prismatic RGB splitting, "
        "Sabattier solarization, depth-banded cross-processing, film-burn light "
        "leaks, radial zoom blur, and temporal feedback. The scene becomes a "
        "fractal — bass, depth, and Julia chaos in one."
    ),
    "version": "3.0.0",
    "api_version": "3.0",
    "origin": "vjlive:plugins/vdepth/depth_acid_fractal.py",
    "dreamer_flag": True,
    "logic_purity": "genius",
    "role_assignment": "worker",
    "kitten_status": True,
    "plugin_type": "depth_effect",
    "category": "visual",
    "tags": ["depth", "fractal", "julia", "acid", "datamosh", "neon", "prism", "solarize"],
    "performance_impact": "high",
    "parameters": {
        "fractal_intensity": {"type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        "fractal_zoom":      {"type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        "fractal_iterations":{"type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        "fractal_morph":     {"type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        "prism_split":       {"type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        "prism_rotate":      {"type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        "prism_faces":       {"type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        "solarize":          {"type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        "cross_process":     {"type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        "film_burn":         {"type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        "posterize":         {"type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        "zoom_blur":         {"type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        "bass_throb":        {"type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        "neon_boost":        {"type": "float", "default": 6.0, "min": 0.0, "max": 10.0},
        "feedback":          {"type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        "mix":               {"type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
    },
}

PRESETS = {
    "microdose": {
        "fractal_intensity": 3.0, "fractal_zoom": 4.0, "fractal_iterations": 3.0,
        "fractal_morph": 2.0, "prism_split": 2.0, "prism_rotate": 1.0,
        "prism_faces": 1.0, "solarize": 2.0, "cross_process": 3.0,
        "film_burn": 1.0, "posterize": 1.0, "zoom_blur": 1.0,
        "bass_throb": 3.0, "neon_boost": 3.0, "feedback": 2.0,
    },
    "peak_acid": {
        "fractal_intensity": 7.0, "fractal_zoom": 6.0, "fractal_iterations": 7.0,
        "fractal_morph": 6.0, "prism_split": 6.0, "prism_rotate": 5.0,
        "prism_faces": 5.0, "solarize": 5.0, "cross_process": 6.0,
        "film_burn": 5.0, "posterize": 4.0, "zoom_blur": 4.0,
        "bass_throb": 6.0, "neon_boost": 7.0, "feedback": 5.0,
    },
    "film_alchemy": {
        "fractal_intensity": 4.0, "fractal_zoom": 5.0, "fractal_iterations": 4.0,
        "fractal_morph": 3.0, "prism_split": 3.0, "prism_rotate": 2.0,
        "prism_faces": 2.0, "solarize": 8.0, "cross_process": 8.0,
        "film_burn": 7.0, "posterize": 6.0, "zoom_blur": 2.0,
        "bass_throb": 4.0, "neon_boost": 5.0, "feedback": 3.0,
    },
    "dimensional_rift": {
        "fractal_intensity": 10.0, "fractal_zoom": 8.0, "fractal_iterations": 9.0,
        "fractal_morph": 8.0, "prism_split": 9.0, "prism_rotate": 7.0,
        "prism_faces": 7.0, "solarize": 6.0, "cross_process": 7.0,
        "film_burn": 6.0, "posterize": 5.0, "zoom_blur": 7.0,
        "bass_throb": 8.0, "neon_boost": 10.0, "feedback": 7.0,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
#  GLSL — vertex (full-screen quad)
# ─────────────────────────────────────────────────────────────────────────────

VERTEX_SHADER = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1),vec2(1,-1),vec2(-1,1),vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(verts[gl_VertexID],0,1); uv=verts[gl_VertexID]*.5+.5; }
"""

# ─────────────────────────────────────────────────────────────────────────────
#  GLSL — fragment (ported from legacy verbatim, uniforms renormalised)
# ─────────────────────────────────────────────────────────────────────────────

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv; out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform float time;
uniform vec2  resolution;
uniform float u_mix;

uniform float fractal_intensity;
uniform float fractal_zoom;
uniform float fractal_iterations;
uniform float fractal_morph;
uniform float prism_split;
uniform float prism_rotate;
uniform float prism_faces;
uniform float solarize;
uniform float cross_process;
uniform float film_burn;
uniform float posterize;
uniform float zoom_blur;
uniform float bass_throb;
uniform float neon_boost;
uniform float feedback;

float hash(vec2 p) {
    p = fract(p * vec2(443.897, 441.423));
    p += dot(p, p.yx + 19.19);
    return fract((p.x + p.y) * p.x);
}

vec3 hsv2rgb(vec3 c) {
    vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0/3.0, 1.0/3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

float depth_edge(vec2 p) {
    float t = 2.0 / resolution.x;
    float tl=texture(depth_tex,p+vec2(-t,-t)).r; float tc=texture(depth_tex,p+vec2(0,-t)).r;
    float tr=texture(depth_tex,p+vec2(t,-t)).r;  float ml=texture(depth_tex,p+vec2(-t,0)).r;
    float mr=texture(depth_tex,p+vec2(t,0)).r;   float bl=texture(depth_tex,p+vec2(-t,t)).r;
    float bc=texture(depth_tex,p+vec2(0,t)).r;   float br=texture(depth_tex,p+vec2(t,t)).r;
    float gx=-tl-2.0*ml-bl+tr+2.0*mr+br;
    float gy=-tl-2.0*tc-tr+bl+2.0*bc+br;
    return sqrt(gx*gx+gy*gy);
}

vec3 julia_fractal(vec2 p, float depth_val) {
    vec2 z = (p - 0.5) * 3.0 / max(0.1, fractal_zoom);
    float angle = time * fractal_morph * 0.3 + depth_val * 6.283;
    float radius = 0.7885 + depth_val * 0.1;
    vec2 c = vec2(cos(angle), sin(angle)) * radius;
    int max_iter = int(fractal_iterations * 20.0) + 4;
    float iter = 0.0;
    for (int i = 0; i < 64; i++) {
        if (i >= max_iter) break;
        if (dot(z,z) > 4.0) break;
        z = vec2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
        iter += 1.0;
    }
    float t = iter / float(max_iter);
    vec3 col;
    col.r = 0.5 + 0.5*sin(t*6.283*3.0 + time*0.5);
    col.g = 0.5 + 0.5*sin(t*6.283*3.0 + 2.094 + time*0.7);
    col.b = 0.5 + 0.5*sin(t*6.283*3.0 + 4.189 + time*0.3);
    col = pow(col, vec3(0.6));
    if (dot(z,z) <= 4.0) col = vec3(0.05, 0.0, 0.15);
    return col;
}

void main() {
    float depth = texture(depth_tex, uv).r;
    vec2 coord = uv;
    float bass = pow(abs(sin(time * 2.5)), 4.0);

    // Stage 1: bass throb
    if (bass_throb > 0.0) {
        vec2 center = coord - 0.5;
        float zoom = 1.0 - bass_throb * 0.04 * bass;
        coord = center * zoom + 0.5;
    }

    // Stage 2: prism splitting
    vec4 result;
    if (prism_split > 0.0) {
        float angle = prism_rotate * 6.283 + time * 0.3;
        float spread = prism_split * 0.03;
        vec2 r_off = vec2(cos(angle),           sin(angle))           * spread;
        vec2 g_off = vec2(cos(angle + 2.094),   sin(angle + 2.094))   * spread * 0.6;
        vec2 b_off = vec2(cos(angle + 4.189),   sin(angle + 4.189))   * spread;
        float dm = 1.0 + (1.0 - depth) * 1.5;
        r_off *= dm; g_off *= dm; b_off *= dm;
        result.r = texture(tex0, coord + r_off).r;
        result.g = texture(tex0, coord + g_off).g;
        result.b = texture(tex0, coord + b_off).b;
        if (prism_faces > 0.0) {
            int faces = int(prism_faces * 4.0) + 1;
            for (int i = 1; i < 5; i++) {
                if (i >= faces) break;
                float fa = float(i) * 6.283 / float(faces) + time * 0.1;
                vec4 gh = texture(tex0, coord + vec2(cos(fa),sin(fa))*spread*2.0*dm);
                result.rgb += gh.rgb * 0.15;
            }
        }
        result.a = 1.0;
    } else { result = texture(tex0, coord); }

    // Stage 3: zoom blur
    if (zoom_blur > 0.0) {
        float ba = zoom_blur * depth * 0.015;
        vec2 cen = coord - 0.5;
        vec4 blurred = result;
        for (int i = 1; i < 8; i++) {
            float t = float(i) / 8.0;
            blurred += texture(tex0, coord - cen * ba * t);
        }
        blurred /= 8.0;
        result = mix(result, blurred, depth * zoom_blur);
    }

    // Stage 4: fractal overlay
    if (fractal_intensity > 0.0) {
        vec3 frac = julia_fractal(coord, depth);
        float edge = depth_edge(coord) * 4.0;
        float fmask = mix(0.2, 1.0, smoothstep(0.1, 0.5, edge));
        vec3 screened = 1.0 - (1.0 - result.rgb) * (1.0 - frac * fmask);
        result.rgb = mix(result.rgb, screened, fractal_intensity * 0.7);
        result.rgb += frac * edge * fractal_intensity * 0.3;
    }

    // Stage 5: solarization
    if (solarize > 0.0) {
        vec3 solar = result.rgb;
        for (int ch = 0; ch < 3; ch++) {
            solar[ch] = abs(sin(result.rgb[ch] * 3.14159 * solarize * 2.0));
        }
        float db = 0.5 + 0.5*sin(depth * 6.283 * 2.0 + time * 0.5);
        result.rgb = mix(result.rgb, solar, db * solarize * 0.6);
    }

    // Stage 6: cross-processing
    if (cross_process > 0.0) {
        vec3 xpro = result.rgb;
        float band = fract(depth * 3.0 + time * 0.1);
        if (band < 0.33) {
            xpro = vec3(pow(xpro.r,0.8), pow(xpro.g,0.6)*1.2, pow(xpro.b,1.5)*0.7);
        } else if (band < 0.66) {
            xpro = vec3(pow(xpro.r,1.3)*0.9, pow(xpro.g,0.7)*1.1, pow(xpro.b,0.6)*1.3);
        } else {
            float ir = dot(xpro, vec3(0.1, 0.9, 0.0));
            xpro = vec3(xpro.r*0.5+ir*0.5, ir*0.3, xpro.b*1.4);
        }
        result.rgb = mix(result.rgb, clamp(xpro,0.0,1.0), cross_process);
    }

    // Stage 7: film burn
    if (film_burn > 0.0) {
        float edge = depth_edge(coord);
        float bn = hash(floor(coord * 8.0) + vec2(floor(time * 0.5)));
        float bs = smoothstep(0.6, 0.9, bn) * film_burn;
        bs += edge * 4.0 * film_burn * 0.3;
        bs *= 0.7 + 0.3 * bass;
        float bh = fract(time * 0.15 + depth * 0.5);
        vec3 bc_col = hsv2rgb(vec3(bh, 0.8, 1.0));
        result.rgb += bc_col * bs * 0.8;
        float streak = exp(-abs(coord.y - 0.5 - sin(time*0.3)*0.2) * 20.0) * bs * 0.3;
        result.rgb += bc_col * streak;
    }

    // Stage 8: posterization
    if (posterize > 0.0) {
        float bands = max(2.0, mix(16.0, 3.0, depth) / (1.0 + posterize));
        result.rgb = mix(result.rgb, floor(result.rgb * bands + 0.5) / bands, posterize * 0.7);
    }

    // Stage 9: neon boost
    if (neon_boost > 0.0) {
        float luma = dot(result.rgb, vec3(0.299, 0.587, 0.114));
        vec3 chroma = result.rgb - luma;
        result.rgb = luma + chroma * (1.0 + neon_boost * 4.0);
        result.r *= 1.0 + neon_boost * 0.1;
        result.rgb = clamp(result.rgb, 0.0, 1.5);
    }

    // Stage 10: feedback
    if (feedback > 0.0) {
        vec4 prev = texture(texPrev, coord);
        float fb = feedback * (0.3 + depth * 0.5);
        result = mix(result, prev, clamp(fb, 0.0, 0.9));
    }

    fragColor = mix(texture(tex0, uv), result, u_mix);
}
"""


class DepthAcidFractalDatamoshPlugin(EffectPlugin):
    """Depth Acid Fractal Datamosh — Julia fractals × depth × neon film alchemy."""

    def get_metadata(self) -> dict: return METADATA

    def __init__(self) -> None:
        super().__init__()
        self._prog = self._vao = 0
        self._prev_tex = self._prev_fbo = 0
        self._initialized = False
        self._mock = not HAS_GL

    # ── GL helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _compile(vs: str, fs: str) -> int:
        def _sh(src, kind):
            s = gl.glCreateShader(kind)
            gl.glShaderSource(s, src)
            gl.glCompileShader(s)
            if not gl.glGetShaderiv(s, gl.GL_COMPILE_STATUS):
                raise RuntimeError(gl.glGetShaderInfoLog(s))
            return s
        v, f = _sh(vs, gl.GL_VERTEX_SHADER), _sh(fs, gl.GL_FRAGMENT_SHADER)
        p = gl.glCreateProgram()
        gl.glAttachShader(p, v); gl.glAttachShader(p, f); gl.glLinkProgram(p)
        if not gl.glGetProgramiv(p, gl.GL_LINK_STATUS):
            raise RuntimeError(gl.glGetProgramInfoLog(p))
        gl.glDeleteShader(v); gl.glDeleteShader(f)
        return p

    def _u(self, n: str) -> int:
        return gl.glGetUniformLocation(self._prog, n)

    def _alloc_prev(self, w: int, h: int) -> None:
        """Allocate or resize the temporal feedback FBO."""
        if self._prev_tex:
            gl.glDeleteTextures(1, [self._prev_tex])
            gl.glDeleteFramebuffers(1, [self._prev_fbo])
        self._prev_tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._prev_tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0,
                        gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        self._prev_fbo = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._prev_fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0,
                                  gl.GL_TEXTURE_2D, self._prev_tex, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        self._prev_w, self._prev_h = w, h

    def initialize(self, context: PluginContext) -> bool:
        if self._mock or not hasattr(gl, 'glCreateProgram'):
            self._initialized = True
            return True
        try:
            self._prog = self._compile(VERTEX_SHADER, FRAGMENT_SHADER)
            self._vao  = gl.glGenVertexArrays(1)
            w = getattr(context, 'width', 1920)
            h = getattr(context, 'height', 1080)
            self._alloc_prev(w, h)
            self._initialized = True
            return True
        except Exception as exc:
            logger.error("DepthAcidFractalDatamoshPlugin init: %s", exc)
            self._mock = True
            return False

    def process_frame(self, input_texture: int, params: dict[str, Any], context: PluginContext) -> int:
        if not input_texture:
            return 0
        if not self._initialized:
            self.initialize(context)

        def _p(k, d): return float(params.get(k, d)) / 10.0

        if self._mock or not hasattr(gl, 'glCreateProgram'):
            if hasattr(context, 'outputs'):
                context.outputs['video_out'] = input_texture
            return input_texture

        w = getattr(context, 'width', 1920)
        h = getattr(context, 'height', 1080)

        depth_in = context.inputs.get('depth_in', 0) if hasattr(context, 'inputs') else 0
        depth_tex = depth_in if depth_in else input_texture  # fallback

        gl.glUseProgram(self._prog)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u('tex0'), 0)

        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._prev_tex)
        gl.glUniform1i(self._u('texPrev'), 1)

        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_tex)
        gl.glUniform1i(self._u('depth_tex'), 2)

        gl.glUniform1f(self._u('time'),               context.time if hasattr(context, 'time') else 0.0)
        gl.glUniform2f(self._u('resolution'),          float(w), float(h))
        gl.glUniform1f(self._u('u_mix'),               _p('mix', 8.0))
        gl.glUniform1f(self._u('fractal_intensity'),   _p('fractal_intensity', 5.0))
        gl.glUniform1f(self._u('fractal_zoom'),        0.5 + _p('fractal_zoom', 5.0) * 3.5)
        gl.glUniform1f(self._u('fractal_iterations'),  _p('fractal_iterations', 5.0))
        gl.glUniform1f(self._u('fractal_morph'),       _p('fractal_morph', 4.0))
        gl.glUniform1f(self._u('prism_split'),         _p('prism_split', 5.0))
        gl.glUniform1f(self._u('prism_rotate'),        _p('prism_rotate', 3.0))
        gl.glUniform1f(self._u('prism_faces'),         _p('prism_faces', 3.0))
        gl.glUniform1f(self._u('solarize'),            _p('solarize', 4.0))
        gl.glUniform1f(self._u('cross_process'),       _p('cross_process', 5.0))
        gl.glUniform1f(self._u('film_burn'),           _p('film_burn', 4.0))
        gl.glUniform1f(self._u('posterize'),           _p('posterize', 3.0))
        gl.glUniform1f(self._u('zoom_blur'),           _p('zoom_blur', 3.0))
        gl.glUniform1f(self._u('bass_throb'),          _p('bass_throb', 5.0))
        gl.glUniform1f(self._u('neon_boost'),          _p('neon_boost', 6.0))
        gl.glUniform1f(self._u('feedback'),            _p('feedback', 4.0))

        gl.glBindVertexArray(self._vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)

        # Copy output to prev texture for next frame
        if self._prev_fbo:
            gl.glBindFramebuffer(gl.GL_READ_FRAMEBUFFER, 0)
            gl.glBindFramebuffer(gl.GL_DRAW_FRAMEBUFFER, self._prev_fbo)
            gl.glBlitFramebuffer(0, 0, w, h, 0, 0, w, h,
                                 gl.GL_COLOR_BUFFER_BIT, gl.GL_NEAREST)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        gl.glUseProgram(0)
        if hasattr(context, 'outputs'):
            context.outputs['video_out'] = input_texture
        return input_texture

    def cleanup(self) -> None:
        try:
            if HAS_GL and hasattr(gl, 'glDeleteProgram'):
                if self._prog: gl.glDeleteProgram(self._prog)
            if HAS_GL and hasattr(gl, 'glDeleteVertexArrays'):
                if self._vao: gl.glDeleteVertexArrays(1, [self._vao])
            if HAS_GL and hasattr(gl, 'glDeleteTextures'):
                if self._prev_tex: gl.glDeleteTextures(1, [self._prev_tex])
            if HAS_GL and hasattr(gl, 'glDeleteFramebuffers'):
                if self._prev_fbo: gl.glDeleteFramebuffers(1, [self._prev_fbo])
        except Exception as exc:
            logger.error("DepthAcidFractalDatamoshPlugin cleanup: %s", exc)
        finally:
            self._prog = self._vao = self._prev_tex = self._prev_fbo = 0


# Legacy compat alias
DepthAcidFractalDatamoshEffect = DepthAcidFractalDatamoshPlugin
