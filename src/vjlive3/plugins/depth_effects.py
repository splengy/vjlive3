import numpy as np
import logging

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from typing import Dict, Any
from vjlive3.plugins.api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

METADATA = {
    "name": "DepthEffects",
    "version": "3.0.0",
    "description": "Chain multiple depth effects together",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "utility",
    "tags": ["depth", "effects", "chain", "pipeline"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "effect_chain", "type": "list", "default": []},
        {"name": "effect_order", "type": "list", "default": []},
        {"name": "effect_params", "type": "dict", "default": {}},
        {"name": "blend_mode", "type": "str", "default": "sequential", "options": ["sequential", "parallel", "weighted"]},
        {"name": "blend_weights", "type": "list", "default": []},
        {"name": "enable_depth_normalization", "type": "bool", "default": True},
        {"name": "preserve_original", "type": "bool", "default": False}
    ]
}

VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 position;
layout(location = 1) in vec2 texcoord;
out vec2 uv;
void main() {
    uv = texcoord;
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

FRAGMENT_HEADER = """
#version 330 core
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform vec2 resolution;
uniform float blend_weight;

float get_depth() {
    float d = texture(depth_tex, uv).r;
    return clamp(d, 0.0, 1.0);
}
"""

SHADERS = {
    "blur": FRAGMENT_HEADER + """
        uniform float radius;
        void main() {
            float d = get_depth();
            float r = clamp(radius * d, 0.0, 15.0);
            if (r < 0.5) {
                fragColor = texture(tex0, uv) * blend_weight;
                return;
            }
            vec4 sum = vec4(0.0);
            float t_x = 1.0 / resolution.x;
            float t_y = 1.0 / resolution.y;
            float count = 0.0;
            for(float x = -r; x <= r; x += 1.0) {
                for(float y = -r; y <= r; y += 1.0) {
                    sum += texture(tex0, uv + vec2(x*t_x, y*t_y));
                    count += 1.0;
                }
            }
            fragColor = (sum / max(count, 1.0)) * blend_weight;
        }
    """,
    "color_grade": FRAGMENT_HEADER + """
        uniform vec3 color_shift;
        void main() {
            vec4 src = texture(tex0, uv);
            vec3 final_rgb = src.rgb * mix(vec3(1.0), color_shift, get_depth());
            fragColor = vec4(final_rgb, src.a) * blend_weight;
        }
    """,
    "distortion": FRAGMENT_HEADER + """
        uniform float dist_amount;
        void main() {
            float d = get_depth();
            vec2 offset = vec2(sin(uv.y * 20.0), cos(uv.x * 20.0)) * dist_amount * d * 0.05;
            fragColor = texture(tex0, uv + offset) * blend_weight;
        }
    """,
    "glow": FRAGMENT_HEADER + """
        uniform float glow_intensity;
        uniform vec3 glow_color;
        void main() {
            float t_x = 1.0 / resolution.x;
            float t_y = 1.0 / resolution.y;
            float dC = texture(depth_tex, uv).r;
            float dR = texture(depth_tex, uv + vec2(t_x, 0.0)).r;
            float dD = texture(depth_tex, uv + vec2(0.0, t_y)).r;
            float sobel = length(vec2(dR - dC, dD - dC));
            float edge = smoothstep(0.01, 0.05, sobel);
            vec4 src = texture(tex0, uv);
            vec3 res = src.rgb + (glow_color * edge * glow_intensity);
            fragColor = vec4(clamp(res, 0.0, 1.0), src.a) * blend_weight;
        }
    """,
    "fog": FRAGMENT_HEADER + """
        uniform float fog_density;
        uniform vec3 fog_color;
        void main() {
            float fog = smoothstep(0.0, fog_density, get_depth());
            vec4 src = texture(tex0, uv);
            vec3 res = mix(src.rgb, fog_color, fog);
            fragColor = vec4(res, src.a) * blend_weight;
        }
    """,
    "sharpen": FRAGMENT_HEADER + """
        uniform float sharpen_amount;
        void main() {
            float d = get_depth();
            float t_x = 1.0 / resolution.x;
            float t_y = 1.0 / resolution.y;
            vec4 src = texture(tex0, uv);
            vec4 blur = (
                texture(tex0, uv + vec2(-t_x, 0.0)) +
                texture(tex0, uv + vec2(t_x, 0.0)) +
                texture(tex0, uv + vec2(0.0, -t_y)) +
                texture(tex0, uv + vec2(0.0, t_y))
            ) * 0.25;
            vec4 res = mix(src, src + (src - blur) * sharpen_amount, d);
            fragColor = clamp(res, 0.0, 1.0) * blend_weight;
        }
    """,
    "copy": FRAGMENT_HEADER + """
        void main() {
            fragColor = texture(tex0, uv) * blend_weight;
        }
    """
}

class DepthEffectsPlugin(EffectPlugin):
    """
    DepthEffects pipeline chaining manager for VJLive3.
    Evaluates up to 6 micro-kernels dynamically utilizing Double-FBO Ping-Pong iterations preventing plugin bloat.
    """
    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.programs: Dict[str, int] = {}
        
        self.fboA = None
        self.texA = None
        self.fboB = None
        self.texB = None
        self.fboOut = None
        self.texOut = None
        
        self.vao = None
        self.vbo = None

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context: PluginContext) -> None:
        if self._mock_mode:
            return

        try:
            self._compile_all_shaders()
            self._setup_quad()
            w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
            self.fboA, self.texA = self._create_fbo(w, h)
            self.fboB, self.texB = self._create_fbo(w, h)
            self.fboOut, self.texOut = self._create_fbo(w, h)
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthEffects: {e}")
            self._mock_mode = True

    def _compile_all_shaders(self):
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)

        for name, fs_source in SHADERS.items():
            fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fs, fs_source)
            gl.glCompileShader(fs)
            
            if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
                gl.glDeleteShader(fs)
                raise RuntimeError(f"FS Error ({name}): {gl.glGetShaderInfoLog(fs)}")

            prog = gl.glCreateProgram()
            gl.glAttachShader(prog, vs)
            gl.glAttachShader(prog, fs)
            gl.glLinkProgram(prog)
            gl.glDeleteShader(fs)
            
            self.programs[name] = prog
            
        gl.glDeleteShader(vs)

    def _create_fbo(self, w: int, h: int) -> tuple[int, int]:
        fbo = gl.glGenFramebuffers(1)
        tex = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, tex, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        return fbo, tex

    def _setup_quad(self):
        vertices = np.array([
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 1.0,
             1.0,  1.0,  1.0, 1.0,
        ], dtype=np.float32)
        
        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        
        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
        
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(8))
        gl.glBindVertexArray(0)

    def _apply_uniforms_for_effect(self, prog: int, effect_name: str, params: Dict[str, Any]):
        if effect_name == "blur":
            gl.glUniform1f(gl.glGetUniformLocation(prog, "radius"), float(params.get("radius", 5.0)))
        elif effect_name == "color_grade":
            c = params.get("color_shift", [1.0, 1.0, 1.0])
            if not isinstance(c, (list, tuple)) or len(c) < 3: c = [1.0, 1.0, 1.0]
            gl.glUniform3f(gl.glGetUniformLocation(prog, "color_shift"), float(c[0]), float(c[1]), float(c[2]))
        elif effect_name == "distortion":
            gl.glUniform1f(gl.glGetUniformLocation(prog, "dist_amount"), float(params.get("dist_amount", 1.0)))
        elif effect_name == "glow":
            gl.glUniform1f(gl.glGetUniformLocation(prog, "glow_intensity"), float(params.get("glow_intensity", 1.0)))
            c = params.get("glow_color", [1.0, 1.0, 1.0])
            if not isinstance(c, (list, tuple)) or len(c) < 3: c = [1.0, 1.0, 1.0]
            gl.glUniform3f(gl.glGetUniformLocation(prog, "glow_color"), float(c[0]), float(c[1]), float(c[2]))
        elif effect_name == "fog":
            gl.glUniform1f(gl.glGetUniformLocation(prog, "fog_density"), float(params.get("fog_density", 0.5)))
            c = params.get("fog_color", [1.0, 1.0, 1.0])
            if not isinstance(c, (list, tuple)) or len(c) < 3: c = [1.0, 1.0, 1.0]
            gl.glUniform3f(gl.glGetUniformLocation(prog, "fog_color"), float(c[0]), float(c[1]), float(c[2]))
        elif effect_name == "sharpen":
            gl.glUniform1f(gl.glGetUniformLocation(prog, "sharpen_amount"), float(params.get("sharpen_amount", 1.0)))

    def _draw_pass(self, prog: int, src_tex: int, depth_tex: int, fbo_target: int, w: int, h: int, weight: float = 1.0):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo_target)
        gl.glUseProgram(prog)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, src_tex)
        gl.glUniform1i(gl.glGetUniformLocation(prog, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_tex)
        gl.glUniform1i(gl.glGetUniformLocation(prog, "depth_tex"), 1)
        
        gl.glUniform2f(gl.glGetUniformLocation(prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(prog, "blend_weight"), float(weight))
        
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        depth_texture = getattr(context, "inputs", {}).get("depth_in", input_texture)
        
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        gl.glViewport(0, 0, w, h)
        gl.glBindVertexArray(self.vao)
        
        effect_order = params.get("effect_order", [])
        if not isinstance(effect_order, list): effect_order = []
        
        # Filter strictly
        chain = [e for e in effect_order if e in self.programs]
        
        if not chain:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        effect_params = params.get("effect_params", {})
        if not isinstance(effect_params, dict): effect_params = {}
        
        blend_mode = params.get("blend_mode", "sequential")
        # Ensure we stay safe
        if blend_mode not in ["sequential", "parallel", "weighted"]:
            blend_mode = "sequential"

        current_src = input_texture
        target_fbo = self.fboA
        target_tex = self.texA

        if blend_mode == "sequential":
            gl.glDisable(gl.GL_BLEND)
            for effect in chain:
                prog = self.programs[effect]
                self._apply_uniforms_for_effect(prog, effect, effect_params.get(effect, {}))
                self._draw_pass(prog, current_src, depth_texture, target_fbo, w, h, 1.0)
                
                # Ping pong
                current_src = target_tex
                if target_fbo == self.fboA:
                    target_fbo = self.fboB
                    target_tex = self.texB
                else:
                    target_fbo = self.fboA
                    target_tex = self.texA
                    
        else:
            # Parallel or Weighted modes use Additive Blending targeting fboOut explicitly
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fboOut)
            gl.glClearColor(0.0, 0.0, 0.0, 0.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
            
            weights = params.get("blend_weights", [])
            if not isinstance(weights, list): weights = []
            
            for i, effect in enumerate(chain):
                prog = self.programs[effect]
                self._apply_uniforms_for_effect(prog, effect, effect_params.get(effect, {}))
                w_val = 1.0 / len(chain)
                if blend_mode == "weighted" and i < len(weights):
                    try: w_val = float(weights[i])
                    except: pass
                    
                self._draw_pass(prog, input_texture, depth_texture, self.fboOut, w, h, w_val)
            
            gl.glDisable(gl.GL_BLEND)
            current_src = self.texOut

        # Output resolution mapping
        if params.get("preserve_original", False):
            # Accumulate original with resulting blend using a final copy pass to fboOut
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fboB) # safely use B as temporary target
            gl.glClearColor(0.0, 0.0, 0.0, 0.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
            
            prog = self.programs["copy"]
            self._draw_pass(prog, input_texture, depth_texture, self.fboB, w, h, 0.5)
            self._draw_pass(prog, current_src, depth_texture, self.fboB, w, h, 0.5)
            
            gl.glDisable(gl.GL_BLEND)
            current_src = self.texB

        gl.glBindVertexArray(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = current_src
            
        return current_src

    def cleanup(self) -> None:
        if self._mock_mode:
            return
            
        try:
            if self.texA: gl.glDeleteTextures(1, [self.texA])
            if self.fboA: gl.glDeleteFramebuffers(1, [self.fboA])
            
            if self.texB: gl.glDeleteTextures(1, [self.texB])
            if self.fboB: gl.glDeleteFramebuffers(1, [self.fboB])
            
            if self.texOut: gl.glDeleteTextures(1, [self.texOut])
            if self.fboOut: gl.glDeleteFramebuffers(1, [self.fboOut])
            
            self.texA, self.fboA, self.texB, self.fboB, self.texOut, self.fboOut = None, None, None, None, None, None

            if self.vbo: gl.glDeleteBuffers(1, [self.vbo])
            if self.vao: gl.glDeleteVertexArrays(1, [self.vao])
            self.vbo, self.vao = None, None
            
            for prog in self.programs.values():
                gl.glDeleteProgram(prog)
            self.programs.clear()
            
        except Exception as e:
            logger.error(f"Cleanup Error in DepthEffects: {e}")
