import numpy as np
import logging
import time

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from typing import Dict, Any

logger = logging.getLogger(__name__)

METADATA = {
    "name": "Depth Acid Fractal",
    "description": "Neon fractal mayhem modulated by depth boundaries.",
    "version": "1.0.0",
    "parameters": [
        {"name": "fractal_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "prism_split", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "solarize_level", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "neon_burn", "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "zoom_blur", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "depth_threshold", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
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

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depthTex;

uniform float time;
uniform int has_depth;

uniform float fractal_intensity;
uniform float prism_split;
uniform float solarize_level;
uniform float neon_burn;
uniform float zoom_blur;
uniform float depth_threshold;

float hash(vec2 p) {
    p = fract(p * vec2(443.897, 441.423));
    p += dot(p, p.yx + 19.19);
    return fract((p.x + p.y) * p.x);
}

vec3 hsv2rgb(vec3 c) {
    vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0/3.0, 1.0/3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

vec3 julia_fractal(vec2 p, float depth_val) {
    vec2 z = (p - 0.5) * 3.0;
    
    // Morph parameter based on depth to create reacting topology
    float angle = time * 0.3 + depth_val * 6.283;
    float radius = 0.7885 + depth_val * 0.1;
    vec2 c = vec2(cos(angle), sin(angle)) * radius;

    // Hardcap at 16 loops ensuring strict 60FPS safety limits prevent shader timeouts internally natively
    float iter = 0.0;
    for (int i = 0; i < 16; i++) {
        if (dot(z, z) > 4.0) break;
        z = vec2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y) + c;
        iter += 1.0;
    }

    float t = iter / 16.0;
    vec3 col;
    col.r = 0.5 + 0.5 * sin(t * 6.283 * 3.0 + time * 0.5);
    col.g = 0.5 + 0.5 * sin(t * 6.283 * 3.0 + 2.094 + time * 0.7);
    col.b = 0.5 + 0.5 * sin(t * 6.283 * 3.0 + 4.189 + time * 0.3);

    // Deep mapping black center
    if (dot(z, z) <= 4.0) {
        col = vec3(0.05, 0.0, 0.15);
    }
    return pow(col, vec3(0.6));
}

vec2 safe_uv(vec2 coords) {
    return vec2(1.0) - abs(vec2(1.0) - mod(coords, 2.0));
}

void main() {
    float depth = 0.0;
    if (has_depth == 1) {
        depth = texture(depthTex, uv).r;
    }
    
    // Discard processing mappings safely resolving input omissions flawlessly
    if (has_depth == 0 || depth < depth_threshold) {
         fragColor = texture(tex0, uv);
         return;
    }

    // Prism scale mapped
    vec4 base_color;
    if (prism_split > 0.0) {
        float angle = time * 0.3;
        float spl = prism_split * 0.03 * depth;
        vec2 r_off = vec2(cos(angle), sin(angle)) * spl;
        vec2 g_off = vec2(cos(angle + 2.094), sin(angle + 2.094)) * spl * 0.6;
        vec2 b_off = vec2(cos(angle + 4.189), sin(angle + 4.189)) * spl;
        
        base_color.r = texture(tex0, safe_uv(uv + r_off)).r;
        base_color.g = texture(tex0, safe_uv(uv + g_off)).g;
        base_color.b = texture(tex0, safe_uv(uv + b_off)).b;
        base_color.a = 1.0;
    } else {
        base_color = texture(tex0, uv);
    }
    
    // Zoom Blur scale natively pushing vectors outward mapping depth coordinates precisely 
    if (zoom_blur > 0.0) {
        float amt = zoom_blur * depth * 0.015;
        vec2 center = uv - 0.5;
        vec4 blurred = base_color;
        // Bounded loops natively limiting sample checks structurally preventing timeout execution natively
        for (int i = 1; i < 4; i++) {
            float mt = float(i) / 4.0;
            blurred += texture(tex0, safe_uv(uv - center * amt * mt));
        }
        base_color = mix(base_color, blurred / 4.0, depth * zoom_blur);
    }

    // Fractal topology mapping 
    if (fractal_intensity > 0.0) {
        vec3 fractal = julia_fractal(uv, depth);
        vec3 screened = 1.0 - (1.0 - base_color.rgb) * (1.0 - fractal);
        base_color.rgb = mix(base_color.rgb, screened, fractal_intensity * depth);
    }
    
    // Solarize mapped against explicit bounds mapping curve vectors reliably organically
    if (solarize_level > 0.0) {
        vec3 solar = base_color.rgb;
        for (int ch = 0; ch < 3; ch++) {
            solar[ch] = abs(sin(base_color.rgb[ch] * 3.14159 * 2.0 * solarize_level));
        }
        base_color.rgb = mix(base_color.rgb, solar, solarize_level * 0.6 * depth);
    }
    
    // Neon Film burn mapping
    if (neon_burn > 0.0) {
        float burn_noise = hash(floor(uv * 8.0) + vec2(floor(time * 0.5)));
        float spot = smoothstep(0.6, 0.9, burn_noise) * neon_burn * depth;
        float h = fract(time * 0.15 + depth * 0.5);
        vec3 bc = hsv2rgb(vec3(h, 0.8, 1.0));
        base_color.rgb += bc * spot * 0.8;
    }
    
    // Temporal buffer pingpong mix
    vec4 previous = texture(texPrev, uv);
    base_color = mix(base_color, previous, 0.3 * depth_threshold); // fixed feedback map

    fragColor = clamp(base_color, 0.0, 1.0);
}
"""

class DepthAcidFractalPlugin(object):
    """Depth-reactive psychedelic fractal shader mapping PingPong execution."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        
        # Ping Pong Textures
        self.fbo = [None, None]
        self.tex = [None, None]
        self.ping_pong = 0
        
        self.vao = None
        self.vbo = None
        self._width = 0
        self._height = 0
        self.start_time = time.time()

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthAcidFractal in Mock Mode (No OpenGL)")
            return

        try:
            self._compile_shader()
            self._setup_quad()
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthAcidFractal: {e}")
            self._mock_mode = True

    def _compile_shader(self):
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, VERTEX_SHADER)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"Vertex Shader Error: {gl.glGetShaderInfoLog(vs)}")

        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, FRAGMENT_SHADER)
        gl.glCompileShader(fs)
        if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"Fragment Shader Error: {gl.glGetShaderInfoLog(fs)}")

        self.prog = gl.glCreateProgram()
        gl.glAttachShader(self.prog, vs)
        gl.glAttachShader(self.prog, fs)
        gl.glLinkProgram(self.prog)
        if not gl.glGetProgramiv(self.prog, gl.GL_LINK_STATUS):
            raise RuntimeError(f"Program Link Error: {gl.glGetProgramInfoLog(self.prog)}")
            
        gl.glDeleteShader(vs)
        gl.glDeleteShader(fs)

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

    def _allocate_buffers(self, w: int, h: int):
        self._free_fbo()
        self._width = w
        self._height = h
        
        fbos = gl.glGenFramebuffers(2)
        texs = gl.glGenTextures(2)
        
        if not isinstance(fbos, (list, tuple, np.ndarray)):
             fbos = [fbos] * 2
        if not isinstance(texs, (list, tuple, np.ndarray)):
             texs = [texs] * 2
             
        for i in range(2):
            self.fbo[i] = fbos[i]
            self.tex[i] = texs[i]
            
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo[i])
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex[i])
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
            
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            
            gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.tex[i], 0)

            # Pre-clear the buffers directly avoiding garbage artifacts dynamically reading natively during bounds
            gl.glClearColor(0.0, 0.0, 0.0, 1.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _free_fbo(self):
        try:
            valid_texs = [t for t in self.tex if t is not None]
            if valid_texs:
                gl.glDeleteTextures(len(valid_texs), valid_texs)
                
            valid_fbos = [f for f in self.fbo if f is not None]
            if valid_fbos:
                gl.glDeleteFramebuffers(len(valid_fbos), valid_fbos)
                
            self.tex = [None, None]
            self.fbo = [None, None]
        except Exception as e:
            logger.debug(f"Safely catching cleanup exception on FBO: {e}")

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
            
        inputs = getattr(context, "inputs", {})
        depth_in = inputs.get("depth_in", 0)
        
        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        if w != self._width or h != self._height:
            self._allocate_buffers(w, h)
            
        current_fbo = self.fbo[self.ping_pong]
        previous_tex = self.tex[1 - self.ping_pong]
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, current_fbo)
        gl.glViewport(0, 0, w, h)
        
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glUseProgram(self.prog)
        
        # Primary Video Source
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        # Feedback Source
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, previous_tex)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrev"), 1)
        
        # Depth Map Source
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depthTex"), 2)
        
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), 1 if depth_in > 0 else 0)
        
        current_time = time.time() - self.start_time
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), current_time)
        
        # Acid Scale parameters natively mapped against structural limits accurately mapped
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "fractal_intensity"), float(params.get("fractal_intensity", 0.5)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "prism_split"), float(params.get("prism_split", 0.3)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "solarize_level"), float(params.get("solarize_level", 0.4)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "neon_burn"), float(params.get("neon_burn", 0.6)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "zoom_blur"), float(params.get("zoom_blur", 0.2)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_threshold"), float(params.get("depth_threshold", 0.5)))
        
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        out_target = self.tex[self.ping_pong]
        
        # Ping the Pong
        self.ping_pong = 1 - self.ping_pong
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = out_target
            
        return out_target

    def cleanup(self) -> None:
        if self._mock_mode:
            return
            
        try:
            self._free_fbo()
            if self.vbo is not None:
                gl.glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.vao is not None:
                gl.glDeleteVertexArrays(1, [self.vao])
                self.vao = None
            if self.prog is not None:
                gl.glDeleteProgram(self.prog)
                self.prog = None
        except Exception as e:
            logger.error(f"Cleanup Error in DepthAcidFractal: {e}")
