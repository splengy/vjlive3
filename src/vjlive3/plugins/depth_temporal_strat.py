"""
P3-VD68: Depth Temporal Stratification Datamosh Plugin for VJLive3.
Ported from legacy VJlive-2 DepthTemporalStratEffect.

The shader is clean and directly portable. Architecture is a Ping-Pong
2-FBO pattern (current frame + texPrev feedback). Depth input is optional.
13 parameters. Audio reactivity stripped (no AudioReactor in VJLive3).
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
    "name": "Depth Temporal Strat",
    "description": "Depth strata each run at different temporal offsets. Near=live, far=past.",
    "version": "1.0.0",
    "plugin_type": "depth_effect",
    "category": "temporal",
    "tags": ["depth", "strata", "temporal", "datamosh", "ghost", "strobe"],
    "priority": 1,
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "num_strata",       "type": "int",   "min": 2,   "max": 12,  "default": 4},
        {"name": "strata_separation","type": "float", "min": 0.0, "max": 1.0, "default": 0.7},
        {"name": "strata_offset",    "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "temporal_depth",   "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "temporal_gradient","type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "freeze_amount",    "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "seam_datamosh",    "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "seam_width",       "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "block_displace",   "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "motion_warp",      "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "ghost_opacity",    "type": "float", "min": 0.0, "max": 1.0, "default": 0.7},
        {"name": "color_shift",      "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "strobe_rate",      "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
    ]
}

VERTEX_SRC = """
#version 330 core
const vec2 v[4] = vec2[4](vec2(-1,-1),vec2(1,-1),vec2(-1,1),vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(v[gl_VertexID],0,1); uv = v[gl_VertexID]*0.5+0.5; }
"""

# Shader ported directly from legacy (clean, no CPU-side dependencies)
STRAT_FRAG = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform int has_depth;
uniform float time;
uniform vec2 resolution;

uniform int   num_strata;
uniform float strata_separation;
uniform float strata_offset;
uniform float temporal_depth;
uniform float temporal_gradient;
uniform float freeze_amount;
uniform float seam_datamosh;
uniform float seam_width;
uniform float block_displace;
uniform float motion_warp;
uniform float ghost_opacity;
uniform float color_shift;
uniform float strobe_rate;

float hash(vec2 p) {
    p = fract(p * vec2(443.897, 441.423));
    p += dot(p, p.yx + 19.19);
    return fract((p.x + p.y) * p.x);
}

float get_stratum(float depth, int n) {
    float d = clamp(depth, 0.0, 1.0);
    float quantized = floor(d * float(n)) / float(n);
    return mix(d, quantized, strata_separation);
}

float stratum_edge(vec2 p, int n) {
    float texel = 1.0 / resolution.x;
    float d0 = get_stratum(texture(depth_tex, p).r, n);
    float d1 = get_stratum(texture(depth_tex, p+vec2(texel*2,0)).r, n);
    float d2 = get_stratum(texture(depth_tex, p+vec2(-texel*2,0)).r, n);
    float d3 = get_stratum(texture(depth_tex, p+vec2(0,texel*2)).r, n);
    float d4 = get_stratum(texture(depth_tex, p+vec2(0,-texel*2)).r, n);
    float dx = abs(d1-d2); float dy = abs(d3-d4);
    return clamp(sqrt(dx*dx+dy*dy)*float(n), 0.0, 1.0);
}

vec3 hue_rotate(vec3 c, float a) {
    float s=sin(a), co=cos(a);
    float r = 0.577350;
    mat3 rot = mat3(
        co+(1.0-co)/3.0,     (1.0-co)/3.0-s*r, (1.0-co)/3.0+s*r,
        (1.0-co)/3.0+s*r, co+(1.0-co)/3.0,     (1.0-co)/3.0-s*r,
        (1.0-co)/3.0-s*r, (1.0-co)/3.0+s*r, co+(1.0-co)/3.0
    );
    return clamp(rot*c, 0.0, 1.0);
}

void main() {
    vec4 current  = texture(tex0, uv);
    vec4 previous = texture(texPrev, uv);

    if (has_depth == 0) { fragColor = current; return; }

    float depth = texture(depth_tex, uv).r;
    float animated_depth = clamp(depth + sin(time*0.5+depth*3.0)*strata_offset*0.05, 0.0, 1.0);
    float stratum = get_stratum(animated_depth, num_strata);

    float delay_factor = pow(stratum, 1.0 + temporal_gradient * 2.0);
    float temporal_blend = clamp(delay_factor * temporal_depth, 0.0, 1.0);
    temporal_blend = max(temporal_blend, delay_factor * freeze_amount);

    if (strobe_rate > 0.0) {
        float layer_index = floor(animated_depth * float(num_strata));
        float strobe = sin(time * strobe_rate * 6.283 + layer_index * 1.571);
        temporal_blend *= 0.5 + 0.5 * strobe;
    }

    float edge = stratum_edge(uv, num_strata);
    float seam_factor = smoothstep(1.0 - seam_width, 1.0, edge);
    vec2 displaced_uv = uv;

    if (seam_factor > 0.0 && seam_datamosh > 0.0) {
        float block = max(2.0, block_displace * 32.0);
        vec2 blockUV = floor(uv*resolution/block)*block/resolution;
        vec3 motion = texture(tex0, blockUV).rgb - texture(texPrev, blockUV).rgb;
        float motion_mag = length(motion);
        if (motion_mag > 0.02) displaced_uv = uv + motion.rg * motion_warp * 0.05 * seam_factor * seam_datamosh;
        float jitter = hash(blockUV+time)*2.0-1.0;
        displaced_uv += vec2(jitter*0.003)*seam_factor*seam_datamosh;
    }

    vec4 delayed = texture(texPrev, displaced_uv);
    vec4 temporal_result = mix(current, delayed, temporal_blend);
    if (seam_factor > 0.0) temporal_result = mix(temporal_result, texture(texPrev, displaced_uv), seam_factor*seam_datamosh);

    if (color_shift > 0.0) {
        float layer_index = floor(animated_depth * float(num_strata));
        temporal_result.rgb = hue_rotate(temporal_result.rgb, layer_index * color_shift * 0.628);
    }

    float ghost = 1.0 - delay_factor * (1.0 - ghost_opacity);
    temporal_result.rgb *= ghost;
    temporal_result.rgb += vec3(seam_factor * 0.08 * seam_datamosh);

    fragColor = mix(current, temporal_result, 1.0);
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


class DepthTemporalStratPlugin(EffectPlugin):
    """Depth Temporal Strat — per-stratum temporal delay + datamosh at seams."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = 0
        self.empty_vao = 0
        self.fbo_a = self.tex_a = 0
        self.fbo_b = self.tex_b = 0
        self._w = self._h = 0
        self._initialized = False

    def get_metadata(self): return METADATA

    def initialize(self, context: PluginContext) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = _compile(VERTEX_SRC, STRAT_FRAG)
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"depth_temporal_strat init failed: {e}")
            self._mock_mode = True; return False

    def _free(self):
        try:
            fbos = [f for f in [self.fbo_a, self.fbo_b] if f]
            texs = [t for t in [self.tex_a, self.tex_b] if t]
            if fbos: gl.glDeleteFramebuffers(len(fbos), fbos)
            if texs: gl.glDeleteTextures(len(texs), texs)
        except Exception: pass
        self.fbo_a = self.tex_a = self.fbo_b = self.tex_b = 0

    def _alloc(self, w, h):
        self._free(); self._w, self._h = w, h
        self.fbo_a, self.tex_a = _make_fbo(w, h)
        self.fbo_b, self.tex_b = _make_fbo(w, h)

    def _u(self, name): return gl.glGetUniformLocation(self.prog, name)

    def _draw(self):
        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
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
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in if has_d else 0)
        gl.glUniform1i(self._u("depth_tex"), 2)

        gl.glUniform1i(self._u("has_depth"), has_d)
        gl.glUniform2f(self._u("resolution"), float(w), float(h))
        gl.glUniform1f(self._u("time"), float(time_val))
        gl.glUniform1i(self._u("num_strata"),         int(params.get("num_strata", 4)))
        gl.glUniform1f(self._u("strata_separation"),  float(params.get("strata_separation", 0.7)))
        gl.glUniform1f(self._u("strata_offset"),      float(params.get("strata_offset", 0.2)))
        gl.glUniform1f(self._u("temporal_depth"),     float(params.get("temporal_depth", 0.6)))
        gl.glUniform1f(self._u("temporal_gradient"),  float(params.get("temporal_gradient", 0.5)))
        gl.glUniform1f(self._u("freeze_amount"),      float(params.get("freeze_amount", 0.3)))
        gl.glUniform1f(self._u("seam_datamosh"),      float(params.get("seam_datamosh", 0.5)))
        gl.glUniform1f(self._u("seam_width"),         float(params.get("seam_width", 0.4)))
        gl.glUniform1f(self._u("block_displace"),     float(params.get("block_displace", 0.5)))
        gl.glUniform1f(self._u("motion_warp"),        float(params.get("motion_warp", 0.5)))
        gl.glUniform1f(self._u("ghost_opacity"),      float(params.get("ghost_opacity", 0.7)))
        gl.glUniform1f(self._u("color_shift"),        float(params.get("color_shift", 0.2)))
        gl.glUniform1f(self._u("strobe_rate"),        float(params.get("strobe_rate", 0.0)))

        self._draw()
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        self.fbo_a, self.fbo_b = self.fbo_b, self.fbo_a
        self.tex_a, self.tex_b = self.tex_b, self.tex_a

        if hasattr(context, "outputs"): context.outputs["video_out"] = self.tex_b
        return self.tex_b

    def cleanup(self) -> None:
        try:
            self._free()
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup error depth_temporal_strat: {e}")
        finally:
            self.prog = self.empty_vao = 0
