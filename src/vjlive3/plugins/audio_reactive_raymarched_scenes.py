"""
P3-EXT009: AudioReactiveRaymarchedScenes — SDF ray-marched 3D scenes with audio modulation.

Three scene types: spheres array, infinite tunnel, Mandelbulb fractal.
Audio-reactive: bass→sphere/tunnel size, treble→color hue, beat→background flash.
Ultra boost params for runtime performance tuning.

Ported from VJLive-2: plugins/core/vshadertoy_extra/raymarched_scenes.py (298 lines)
"""
import logging
from typing import List
try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
# # from .api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

METADATA = {
    "name": "Audio Reactive Raymarched Scenes",
    "description": "Ray-marched 3D scenes: spheres, tunnel, Mandelbulb fractal — audio reactive with HSV color and ultra-boost controls.",
    "version": "2.0.0",
    "plugin_type": "effect",
    "category": "3d",
    "tags": ["raymarching", "3d", "sdf", "fractal", "audio-reactive"],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "scene_type",         "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "base_radius",        "type": "float", "default": 1.5, "min": 0.0, "max": 10.0},
        {"name": "color_hue",          "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "color_saturation",   "type": "float", "default": 8.0, "min": 0.0, "max": 10.0},
        {"name": "color_value",        "type": "float", "default": 10.0,"min": 0.0, "max": 10.0},
        {"name": "audio_volume_mix",   "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "audio_bass_mix",     "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "audio_mid_mix",      "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "audio_treble_mix",   "type": "float", "default": 7.0, "min": 0.0, "max": 10.0},
        {"name": "audio_beat_mix",     "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "ultra_max_iterations","type":"float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "ultra_fractal_power","type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "ultra_step_size",    "type": "float", "default": 0.0, "min": 0.0, "max": 10.0},
        {"name": "mix",               "type": "float", "default": 8.0,  "min": 0.0, "max": 10.0},
    ],
}

VERTEX_SHADER = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1),vec2(1,-1),vec2(-1,1),vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(verts[gl_VertexID],0.0,1.0); uv=verts[gl_VertexID]*0.5+0.5; }
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv; out vec4 fragColor;
uniform sampler2D tex0;
uniform float iTime;
uniform vec2 iResolution;
uniform float u_mix;
uniform int   iSceneType;
uniform float iBaseRadius;
uniform float iColorHue;
uniform float iColorSat;
uniform float iColorVal;
uniform float iAudioBass;
uniform float iAudioMid;
uniform float iAudioTreble;
uniform float iAudioBeat;
uniform float iAudioVolume;
uniform int   iMaxIter;
uniform float iFractalPower;
uniform float iStepEps;

// --- SDF helpers ---
float sdSphere(vec3 p, float r) { return length(p) - r; }

float sdTorus(vec3 p, vec2 t) {
    vec2 q = vec2(length(p.xz)-t.x, p.y);
    return length(q)-t.y;
}

float mandelbulbDE(vec3 pos) {
    vec3 z = pos; float dr = 1.0; float r = 0.0;
    float pw = max(2.0, iFractalPower);
    for (int i = 0; i < 5; i++) {
        r = length(z);
        if (r > 2.0) break;
        float theta = acos(z.z/r); float phi = atan(z.y, z.x);
        dr = pow(r, pw-1.0)*pw*dr + 1.0;
        float zr = pow(r, pw);
        theta *= pw; phi *= pw;
        z = zr * vec3(sin(theta)*cos(phi), sin(phi)*sin(theta), cos(theta));
        z += pos;
    }
    return 0.5 * log(r) * r / dr;
}

// --- Scene maps ---
float mapSpheres(vec3 p) {
    float r = iBaseRadius * 0.3 + iAudioBass * 0.15;
    float d = 1e9;
    for (int x = -2; x <= 2; x++)
    for (int y = -2; y <= 2; y++) {
        d = min(d, sdSphere(p - vec3(float(x)*2.0, float(y)*2.0, 0.0), r));
    }
    return d;
}

float mapTunnel(vec3 p) {
    float r = iBaseRadius * 0.3 + iAudioBass * 0.2;
    return r - length(p.xy);
}

float mapFractal(vec3 p) { return mandelbulbDE(p) * 0.5; }

float map(vec3 p) {
    if (iSceneType == 1) return mapTunnel(p);
    if (iSceneType == 2) return mapFractal(p);
    return mapSpheres(p);
}

// --- Normal ---
vec3 calcNormal(vec3 p) {
    const float e = 0.001;
    return normalize(vec3(map(p+vec3(e,0,0))-map(p-vec3(e,0,0)),
                          map(p+vec3(0,e,0))-map(p-vec3(0,e,0)),
                          map(p+vec3(0,0,e))-map(p-vec3(0,0,e))));
}

// --- HSV ---
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0,2.0/3.0,1.0/3.0,3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p-K.xxx, 0.0, 1.0), c.y);
}

void main() {
    vec2 fragCoord = uv * iResolution;
    vec2 st = (2.0*fragCoord - iResolution) / iResolution.y;

    vec3 ro = vec3(0.0, 0.0, -3.0);
    vec3 rd = normalize(vec3(st, 1.5));

    // Tunnel cam moves forward
    if (iSceneType == 1) ro.z += iTime * 2.0;

    int maxSteps = (iMaxIter > 0) ? iMaxIter : 64;
    float eps = (iStepEps > 0.0) ? iStepEps : 0.001;

    float t = 0.0; bool hit = false;
    for (int i = 0; i < 128; i++) {
        if (i >= maxSteps) break;
        float d = map(ro + rd*t);
        if (d < eps) { hit = true; break; }
        t += d;
        if (t > 20.0) break;
    }

    vec3 col;
    if (hit) {
        vec3 p = ro + rd*t;
        vec3 n = calcNormal(p);
        vec3 ld = normalize(vec3(1.0,1.0,-1.0));
        float diff = max(0.0, dot(n, ld));
        float hue = iColorHue/10. + iAudioTreble * 0.2;
        float sat = iColorSat/10.;
        float val = iColorVal/10. * (0.5 + diff*0.5);
        col = hsv2rgb(vec3(hue, sat, val));
    } else {
        float bg_hue = iColorHue/10. + 0.5;
        float bg_flash = iAudioBeat * 0.2;
        col = hsv2rgb(vec3(bg_hue, 0.4, 0.1 + bg_flash));
    }

    vec4 src = texture(tex0, uv);
    fragColor = mix(src, vec4(col, 1.0), u_mix);
}
"""

PRESETS = {
    "spheres_default":    {"scene_type": 0.0, "base_radius": 1.5, "color_hue": 5.0},
    "tunnel_flow":        {"scene_type": 3.5, "base_radius": 2.0, "audio_bass_mix": 7.0},
    "fractal_zoom":       {"scene_type": 7.0, "base_radius": 1.0, "audio_treble_mix": 8.0},
    "audio_reactive":     {"scene_type": 0.0, "audio_bass_mix": 5.0, "audio_beat_mix": 5.0},
    "ultra_performance":  {"ultra_max_iterations": 3.2, "ultra_step_size": 1.0, "scene_type": 3.5},
}


def _c(v, lo=0., hi=10.): return max(lo, min(hi, float(v)))


class AudioReactiveRaymarchedScenesPlugin(object):
    """Ray-marched 3D scene renderer with audio reactivity (spheres/tunnel/fractal)."""

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
            logger.error(f"AudioReactiveRaymarchedScenesPlugin init: {e}"); self._mock_mode = True; return False

    def process_frame(self, input_texture, params, context):
        if not input_texture or input_texture <= 0: return 0
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
            return input_texture
        if not self._initialized: self.initialize(context)
        t = float(getattr(context, 'time', 0.))
        w = float(getattr(context, 'width', 1920)); h = float(getattr(context, 'height', 1080))
        scene = int(_c(params.get('scene_type', 0.0)) / 10. * 2.)
        base_r    = _c(params.get('base_radius', 1.5))
        hue       = _c(params.get('color_hue', 5.0))
        sat       = _c(params.get('color_saturation', 8.0))
        val       = _c(params.get('color_value', 10.0))
        a_bass    = _c(params.get('audio_bass_mix', 5.0)) / 10.
        a_treble  = _c(params.get('audio_treble_mix', 7.0)) / 10.
        a_beat    = _c(params.get('audio_beat_mix', 5.0)) / 10.
        a_vol     = _c(params.get('audio_volume_mix', 5.0)) / 10.
        a_mid     = _c(params.get('audio_mid_mix', 3.0)) / 10.
        ultra_i   = int(_c(params.get('ultra_max_iterations', 0.)) / 10. * 200.)
        ultra_f   = _c(params.get('ultra_fractal_power', 0.)) / 10. * 10.
        ultra_s   = _c(params.get('ultra_step_size', 0.)) * 0.01
        u_mix     = _c(params.get('mix', 8.0)) / 10.
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(self._u('tex0'), 0)
        gl.glUniform1f(self._u('iTime'), t)
        gl.glUniform2f(self._u('iResolution'), w, h)
        gl.glUniform1f(self._u('u_mix'), u_mix)
        gl.glUniform1i(self._u('iSceneType'), scene)
        gl.glUniform1f(self._u('iBaseRadius'), base_r)
        gl.glUniform1f(self._u('iColorHue'), hue)
        gl.glUniform1f(self._u('iColorSat'), sat)
        gl.glUniform1f(self._u('iColorVal'), val)
        gl.glUniform1f(self._u('iAudioBass'), a_bass)
        gl.glUniform1f(self._u('iAudioMid'), a_mid)
        gl.glUniform1f(self._u('iAudioTreble'), a_treble)
        gl.glUniform1f(self._u('iAudioBeat'), a_beat)
        gl.glUniform1f(self._u('iAudioVolume'), a_vol)
        gl.glUniform1i(self._u('iMaxIter'), ultra_i)
        gl.glUniform1f(self._u('iFractalPower'), ultra_f if ultra_f > 0 else 8.0)
        gl.glUniform1f(self._u('iStepEps'), ultra_s if ultra_s > 0 else 0.001)
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0); gl.glUseProgram(0)
        if hasattr(context, 'outputs'): context.outputs['video_out'] = input_texture
        return input_texture

    def cleanup(self):
        try:
            if hasattr(gl, 'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
        except Exception as e: logger.error(f"AudioReactiveRaymarchedScenesPlugin cleanup: {e}")
        finally: self.prog = self.vao = 0
