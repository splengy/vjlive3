"""
P3-VD58: Depth Mosh Nexus Plugin for VJLive3.
Ported from legacy VJlive-2 DepthMoshNexus.

ARCHITECTURAL PIVOT: Legacy had speculative dead code (6 feedback textures never
backed by FBOs, neural_model=None, Python fract() crash, unbound tex2). Per
no-stub policy, those dead paths are purged. The genuine visual core is preserved:
  - Dual-depth displacement datamosh (depth difference drives UV offset)
  - texPrev Ping-Pong temporal bleed
  - Loop in/out window modular control
  - Synesthetic HSV color overlay + hash chaos
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
    "name": "Depth Mosh Nexus",
    "description": "Dual-depth displacement datamosh with loop control and synesthetic color overlay.",
    "version": "1.0.0",
    "plugin_type": "depth_effect",
    "category": "glitch",
    "tags": ["depth", "datamosh", "nexus", "loop", "synesthetic", "double-depth"],
    "priority": 1,
    "inputs": ["video_in", "depth_in", "depth_in_b"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "master_intensity",      "type": "float", "min": 0.0, "max": 1.0,  "default": 1.0},
        {"name": "displacement_strength", "type": "float", "min": 0.0, "max": 1.0,  "default": 0.9},
        {"name": "mosh_chaos",            "type": "float", "min": 0.0, "max": 1.0,  "default": 0.7},
        {"name": "loop_in",               "type": "float", "min": 0.0, "max": 1.0,  "default": 0.0},
        {"name": "loop_out",              "type": "float", "min": 0.0, "max": 1.0,  "default": 1.0},
        {"name": "depth_blend",           "type": "float", "min": 0.0, "max": 1.0,  "default": 0.8},
        {"name": "bass_pulse",            "type": "float", "min": 0.0, "max": 1.0,  "default": 0.8},
        {"name": "treble_glow",           "type": "float", "min": 0.0, "max": 1.0,  "default": 0.7},
        {"name": "mosh_speed",            "type": "float", "min": 0.0, "max": 3.0,  "default": 1.0},
        {"name": "feedback_amount",       "type": "float", "min": 0.0, "max": 1.0,  "default": 0.5},
    ]
}

VERTEX_SHADER_SOURCE = """
#version 330 core
const vec2 quadVertices[4] = vec2[4](
    vec2(-1.0, -1.0),
    vec2( 1.0, -1.0),
    vec2(-1.0,  1.0),
    vec2( 1.0,  1.0)
);
out vec2 uv;
void main() {
    gl_Position = vec4(quadVertices[gl_VertexID], 0.0, 1.0);
    uv = quadVertices[gl_VertexID] * 0.5 + 0.5;
}
"""

FRAGMENT_SHADER_SOURCE = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;        // video_in
uniform sampler2D texPrev;     // Ping-Pong feedback
uniform sampler2D depth_tex0;  // depth_in (optional)
uniform sampler2D depth_tex1;  // depth_in_b (optional secondary)
uniform float time;
uniform vec2 resolution;
uniform int has_depth0;
uniform int has_depth1;

uniform float master_intensity;
uniform float displacement_strength;
uniform float mosh_chaos;
uniform float loop_in;
uniform float loop_out;
uniform float depth_blend;
uniform float bass_pulse;
uniform float treble_glow;
uniform float mosh_speed;
uniform float feedback_amount;

// Pseudo-random hash
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

// HSV to RGB for synesthetic overlay
vec3 hsv_to_rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    float depth0 = (has_depth0 == 1) ? texture(depth_tex0, uv).r : 0.5;
    float depth1 = (has_depth1 == 1) ? texture(depth_tex1, uv).r : 0.5;

    // --- Mosh loop position ---
    float loop_length = max(loop_out - loop_in, 0.001);
    float mosh_pos = fract((time * mosh_speed * 0.1 - loop_in) / loop_length);

    // --- Displacement from depth difference ---
    float depth_diff = abs(depth0 - depth1);
    float displacement = depth_diff * displacement_strength * 0.15;

    // Chaos noise injection
    displacement += hash(uv + vec2(time * 0.07)) * mosh_chaos * 0.04;

    // Loop modulation (sinusoidal warp within the loop window)
    float loop_mod = sin(mosh_pos * 3.14159) * 0.05;
    vec2 displaced_uv = uv + vec2(displacement + loop_mod, displacement * 0.5);
    displaced_uv = clamp(displaced_uv, 0.0, 1.0);

    // --- Sample displaced previous frame (core datamosh) ---
    vec4 moshed = texture(texPrev, displaced_uv);

    // --- Depth blending with original ---
    float avg_depth = (depth0 + depth1) * 0.5;
    vec4 source = texture(tex0, uv);
    vec4 depth_col = mix(source, moshed, avg_depth);

    // Blend moshed with source based on depth_blend
    vec4 result = mix(source, depth_col, depth_blend);

    // Feedback bleed from previous frame
    float total_mosh = clamp(displacement_strength * 0.8 + feedback_amount, 0.0, 0.95);
    result = mix(source, result, total_mosh);

    // --- Bass pulse brightness ---
    if (bass_pulse > 0.01) {
        float pulse = sin(time * 10.0 + (depth0 + depth1) * 3.0) * 0.5 + 0.5;
        result.rgb *= mix(1.0, 1.3, pulse * bass_pulse);
    }

    // --- Treble synesthetic HSV overlay ---
    if (treble_glow > 0.01) {
        float glow_val = fract(time * 5.0 + (depth0 + depth1) * 2.0);
        float hue = fract(glow_val * 3.0 + time * 0.05);
        vec3 syn_col = hsv_to_rgb(vec3(hue, 0.85, 0.75));
        result.rgb = mix(result.rgb, result.rgb + syn_col * 0.25, treble_glow);
    }

    // --- Master intensity and output ---
    fragColor = vec4(clamp(result.rgb * master_intensity, 0.0, 1.5), 1.0);
}
"""


class DepthMoshNexusPlugin(EffectPlugin):
    """
    Depth Mosh Nexus — dual-depth displacement datamosh with loop control
    and synesthetic color overlay. 2-FBO Ping-Pong architecture.
    """

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL

        self.prog = 0
        self.empty_vao = 0

        # Ping-Pong FBOs
        self.fbo_a = 0
        self.tex_a = 0
        self.fbo_b = 0
        self.tex_b = 0

        self._width = 0
        self._height = 0
        self._initialized = False

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def _compile_shader(self, vs_src: str, fs_src: str) -> int:
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, vs_src)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(gl.glGetShaderInfoLog(vs))

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, fs_src)
        gl.glCompileShader(fs)
        if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(gl.glGetShaderInfoLog(fs))

        prog = gl.glCreateProgram()
        gl.glAttachShader(prog, vs)
        gl.glAttachShader(prog, fs)
        gl.glLinkProgram(prog)
        if not gl.glGetProgramiv(prog, gl.GL_LINK_STATUS):
            raise RuntimeError(gl.glGetProgramInfoLog(prog))

        gl.glDeleteShader(vs)
        gl.glDeleteShader(fs)
        return prog

    def initialize(self, context: PluginContext) -> bool:
        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            logger.warning("Mock mode engaged. Skipping GL initialization.")
            self._initialized = True
            return True
        try:
            self.prog = self._compile_shader(VERTEX_SHADER_SOURCE, FRAGMENT_SHADER_SOURCE)
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize depth_mosh_nexus: {e}")
            self._mock_mode = True
            return False

    def _make_fbo(self, w: int, h: int):
        fbo = gl.glGenFramebuffers(1)
        tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        return fbo, tex

    def _free_fbos(self):
        try:
            textures = [t for t in [self.tex_a, self.tex_b] if t != 0]
            fbos    = [f for f in [self.fbo_a, self.fbo_b] if f != 0]
            if textures: gl.glDeleteTextures(len(textures), textures)
            if fbos:     gl.glDeleteFramebuffers(len(fbos), fbos)
        except Exception:
            pass
        self.tex_a = self.tex_b = 0
        self.fbo_a = self.fbo_b = 0

    def _allocate_buffers(self, w: int, h: int):
        self._free_fbos()
        self._width, self._height = w, h
        self.fbo_a, self.tex_a = self._make_fbo(w, h)
        self.fbo_b, self.tex_b = self._make_fbo(w, h)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
            return 0

        if self._mock_mode or not hasattr(gl, 'glCreateShader'):
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture

        if not self._initialized:
            self.initialize(context)

        w = getattr(context, 'width', 1920)
        h = getattr(context, 'height', 1080)

        if w != self._width or h != self._height:
            self._allocate_buffers(w, h)

        inputs    = getattr(context, "inputs", {})
        depth_in  = inputs.get("depth_in",   0)
        depth_in_b = inputs.get("depth_in_b", 0)
        time_val  = getattr(context, 'time', 0.0)

        # Render into fbo_a, using tex_b as texPrev
        gl.glViewport(0, 0, w, h)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo_a)
        gl.glUseProgram(self.prog)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)

        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_b)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrev"), 1)

        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in if depth_in > 0 else 0)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex0"), 2)

        gl.glActiveTexture(gl.GL_TEXTURE3)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in_b if depth_in_b > 0 else 0)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex1"), 3)

        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth0"), 1 if depth_in > 0 else 0)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth1"), 1 if depth_in_b > 0 else 0)
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), float(time_val))

        # Direct parameter passthrough (native ranges)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "master_intensity"),      float(params.get("master_intensity",      1.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "displacement_strength"), float(params.get("displacement_strength", 0.9)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "mosh_chaos"),            float(params.get("mosh_chaos",            0.7)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "loop_in"),               float(params.get("loop_in",               0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "loop_out"),              float(params.get("loop_out",              1.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_blend"),           float(params.get("depth_blend",           0.8)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "bass_pulse"),            float(params.get("bass_pulse",            0.8)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "treble_glow"),           float(params.get("treble_glow",           0.7)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "mosh_speed"),            float(params.get("mosh_speed",            1.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "feedback_amount"),       float(params.get("feedback_amount",       0.5)))

        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        # Swap Ping-Pong
        self.fbo_a, self.fbo_b = self.fbo_b, self.fbo_a
        self.tex_a, self.tex_b = self.tex_b, self.tex_a

        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.tex_b

        return self.tex_b

    def cleanup(self) -> None:
        try:
            self._free_fbos()
            if hasattr(gl, 'glDeleteProgram') and self.prog != 0:
                gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao != 0:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup Error in DepthMoshNexus: {e}")
        finally:
            self.prog = 0
            self.empty_vao = 0
