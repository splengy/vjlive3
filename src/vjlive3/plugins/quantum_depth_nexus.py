"""
P3-VD75: Quantum Depth Nexus Plugin for VJLive3.
Ported from legacy VJlive-2 QuantumDepthNexus.

ARCHITECTURAL PIVOT (No-Stub Policy applied):
Legacy had dead code: 6 unbacked feedback channels, neural_model=None,
multi-depth-source fusion with 0 sources, AudioReactor coupling.
These are all dead-end stubs that would crash or produce no output.

Clean implementation: 8 visually-meaningful params preserving the actual
working logic:
  - Quantum tunneling: depth-driven UV phase warping
  - Procedural glitch: hash-based datamosh artifacts
  - Fractal noise: multi-octave depth noise overlay
  - Channel mixing via single feedback FBO
  - Motion prediction via temporal accumulation
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
    "name": "Quantum Depth Nexus",
    "description": "Depth-driven quantum tunneling, procedural glitch, and fractal noise datamosh.",
    "version": "1.0.0",
    "plugin_type": "depth_effect",
    "category": "glitch",
    "tags": ["depth", "quantum", "glitch", "fractal", "datamosh", "noise"],
    "priority": 1,
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "quantum_intensity",   "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "procedural_glitch",   "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "fractal_noise",       "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "feedback_intensity",  "type": "float", "min": 0.0, "max": 0.9, "default": 0.5},
        {"name": "temporal_coherence",  "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "quantum_tunneling",   "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "pattern_synthesis",   "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "master_fader",        "type": "float", "min": 0.0, "max": 1.0, "default": 1.0},
    ]
}

VERTEX_SRC = """
#version 330 core
const vec2 v[4] = vec2[4](vec2(-1,-1),vec2(1,-1),vec2(-1,1),vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(v[gl_VertexID],0,1); uv = v[gl_VertexID]*0.5+0.5; }
"""

NEXUS_FRAG = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D u_depth_tex;
uniform int has_depth;
uniform float time;
uniform vec2 resolution;

uniform float quantum_intensity;
uniform float procedural_glitch;
uniform float fractal_noise;
uniform float feedback_intensity;
uniform float temporal_coherence;
uniform float quantum_tunneling;
uniform float pattern_synthesis;
uniform float master_fader;

float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
float luminance(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

float fractalOctave(vec2 p, int octaves) {
    float val = 0.0; float amp = 0.5; float freq = 1.0;
    for (int i = 0; i < octaves; i++) {
        val += hash(p * freq + time * 0.1) * amp;
        amp *= 0.5; freq *= 2.0;
    }
    return val;
}

void main() {
    float depth = has_depth == 1 ? texture(u_depth_tex, uv).r : 0.5;
    vec4 current  = texture(tex0,  uv);
    vec4 previous = texture(texPrev, uv);

    vec2 warp_uv = uv;

    // Quantum tunneling: depth phase warp
    if (quantum_tunneling > 0.01) {
        float tunnel = fract(depth * 10.0 + time * 0.1);
        warp_uv += vec2(sin(tunnel*3.14159), cos(tunnel*3.14159)) * quantum_tunneling * 0.05;
        warp_uv = clamp(warp_uv, 0.0, 1.0);
    }

    vec4 warped = texture(tex0, warp_uv);

    // Fractal noise displacement
    if (fractal_noise > 0.01) {
        float noise = fractalOctave(uv + depth * 0.5, 4);
        vec2 noise_uv = clamp(warp_uv + (noise - 0.5) * fractal_noise * 0.05, 0.0, 1.0);
        warped = mix(warped, texture(tex0, noise_uv), fractal_noise * 0.5);
    }

    // Procedural glitch: depth-phase chromatic datamosh
    if (procedural_glitch > 0.01) {
        float glitch = fract(depth * 12.0 + time * 0.3);
        if (glitch > 1.0 - procedural_glitch * 0.4) {
            float pattern = fract(uv.y * resolution.y / 4.0 + time * 2.0);
            if (pattern > 0.9) {
                warped.r = texture(texPrev, uv + vec2(0.01, 0)).r;
                warped.b = texture(texPrev, uv - vec2(0.01, 0)).b;
            }
        }
        float noise_g = fract(sin(dot(uv * time * 0.05, vec2(12.9898, 78.233))) * 43758.5453);
        warped.rgb += (noise_g - 0.5) * fractal_noise * 0.08;
    }

    // Pattern synthesis: quantum pattern modulation
    if (pattern_synthesis > 0.01) {
        float p = fract(depth * 8.0 + time * 0.2);
        warped.rgb *= mix(0.85, 1.15, p) * pattern_synthesis + (1.0 - pattern_synthesis);
    }

    // Feedback accumulation
    vec4 result = mix(warped, previous, feedback_intensity * temporal_coherence);

    // Quantum intensity: depth-modulated blend
    float quantum_mod = quantum_intensity * (0.5 + depth * 0.5);
    result = mix(current, result, quantum_mod);

    fragColor = vec4(result.rgb * master_fader, 1.0);
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


class QuantumDepthNexusPlugin(object):
    """Quantum Depth Nexus — depth-driven quantum tunneling + glitch + fractal feedback."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = 0; self.empty_vao = 0
        self.fbo_a = self.tex_a = 0
        self.fbo_b = self.tex_b = 0
        self._w = self._h = 0
        self._initialized = False

    def get_metadata(self): return METADATA

    def initialize(self, context) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            self._initialized = True; return True
        try:
            self.prog = _compile(VERTEX_SRC, NEXUS_FRAG)
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True; return True
        except Exception as e:
            logger.error(f"quantum_depth_nexus init failed: {e}")
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

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
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
        gl.glUniform1i(self._u("u_depth_tex"), 2)

        gl.glUniform1i(self._u("has_depth"),        has_d)
        gl.glUniform1f(self._u("time"),             float(time_val))
        gl.glUniform2f(self._u("resolution"),       float(w), float(h))
        gl.glUniform1f(self._u("quantum_intensity"),float(params.get("quantum_intensity",  0.5)))
        gl.glUniform1f(self._u("procedural_glitch"),float(params.get("procedural_glitch", 0.6)))
        gl.glUniform1f(self._u("fractal_noise"),    float(params.get("fractal_noise",      0.5)))
        gl.glUniform1f(self._u("feedback_intensity"),float(params.get("feedback_intensity",0.5)))
        gl.glUniform1f(self._u("temporal_coherence"),float(params.get("temporal_coherence",0.8)))
        gl.glUniform1f(self._u("quantum_tunneling"),float(params.get("quantum_tunneling",  0.6)))
        gl.glUniform1f(self._u("pattern_synthesis"),float(params.get("pattern_synthesis",  0.6)))
        gl.glUniform1f(self._u("master_fader"),     float(params.get("master_fader",       1.0)))

        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
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
            logger.error(f"Cleanup error quantum_depth_nexus: {e}")
        finally:
            self.prog = self.empty_vao = 0
