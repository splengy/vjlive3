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
    "name": "Depth Portal Composite",
    "description": "Isolates performer using depth and composites onto a new background.",
    "version": "1.0.0",
    "parameters": [
        {"name": "slice_near", "type": "float", "min": 0.0, "max": 10.0, "default": 1.5, "description": "Near depth threshold in meters"},
        {"name": "slice_far", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0, "description": "Far depth threshold in meters"},
        {"name": "edge_softness", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "spill_suppress", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "bg_opacity", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0},
        {"name": "fg_scale", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
        {"name": "fg_offset_x", "type": "float", "min": -1.0, "max": 1.0, "default": 0.0},
        {"name": "fg_offset_y", "type": "float", "min": -1.0, "max": 1.0, "default": 0.0}
    ],
    "inputs": ["video_in", "background_in", "depth_in"],
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
out vec4 fragColor_main;

uniform sampler2D tex0;            // background video (second camera/feed)
uniform sampler2D u_depth_tex;     // depth matte (R channel)
uniform sampler2D u_fg_tex;        // foreground (video_in)

uniform float u_slice_near;        // near threshold
uniform float u_slice_far;         // far threshold
uniform float u_edge_softness;     // matte feathering
uniform float u_spill;             // edge spill suppression
uniform float u_bg_opacity;        // background visibility
uniform float u_fg_scale;          // foreground scale
uniform vec2  u_fg_offset;         // foreground position offset
uniform vec2  resolution;

uniform int has_background;
uniform int has_depth;

// Smoothstep-based matte from depth
float computeMatte(float depth) {
    if (depth < 0.001) return 0.0;  // invalid depth = transparent

    // Feathered depth slice
    float softness = max(u_edge_softness * 0.1, 0.001);
    float near_fade = smoothstep(u_slice_near - softness, u_slice_near + softness, depth);
    float far_fade = smoothstep(u_slice_far + softness, u_slice_far - softness, depth);

    return near_fade * far_fade;
}

// Edge spill suppression
float suppressSpill(float matte, vec2 uv_coord, float strength) {
    if (strength < 0.01) return matte;

    vec2 pixel = 1.0 / resolution;
    float sum = 0.0;
    float count = 0.0;
    for (float dx = -2.0; dx <= 2.0; dx += 1.0) {
        for (float dy = -2.0; dy <= 2.0; dy += 1.0) {
            float d = texture(u_depth_tex, uv_coord + vec2(dx, dy) * pixel * 2.0).r;
            sum += computeMatte(d);
            count += 1.0;
        }
    }
    float blurred_matte = sum / count;

    // Erode edges slightly
    float edge = abs(matte - blurred_matte);
    return matte * (1.0 - edge * strength * 5.0);
}

void main() {
    vec3 fg_color = vec3(0.0);
    vec3 bg_color = vec3(0.0);
    float matte = 1.0;

    // Sample foreground (performer) with scale/offset
    vec2 fg_uv = (uv - 0.5) / u_fg_scale + 0.5 + u_fg_offset;
    if (fg_uv.x >= 0.0 && fg_uv.x <= 1.0 && fg_uv.y >= 0.0 && fg_uv.y <= 1.0) {
        fg_color = texture(u_fg_tex, fg_uv).rgb;
    }

    if (has_depth == 1) {
        float depth = texture(u_depth_tex, uv).r;
        matte = computeMatte(depth);
        matte = suppressSpill(matte, uv, u_spill);
        matte = clamp(matte, 0.0, 1.0);
    }

    if (has_background == 1) {
        bg_color = texture(tex0, uv).rgb * u_bg_opacity;
    }

    vec3 result = mix(bg_color, fg_color, matte);

    if (has_depth == 1) {
        float edge_detect = abs(dFdx(matte)) + abs(dFdy(matte));
        vec3 edge_color = vec3(0.3, 0.6, 1.0) * edge_detect * 4.0;
        result += edge_color * 0.3;
    }

    fragColor_main = vec4(result, 1.0);
}
"""

class DepthPortalCompositePlugin(object):
    """Depth Portal Composite Plugin."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.fbo = None
        self.out_tex = None
        self.vao = None
        self.vbo = None

    def get_metadata(self) -> Dict[str, Any]:
        return METADATA

    def initialize(self, context) -> None:
        if self._mock_mode:
            logger.warning("Initializing DepthPortalComposite in Mock Mode (No OpenGL)")
            return

        try:
            self._compile_shader()
            self._setup_quad()
            self._setup_fbo(1920, 1080)
        except Exception as e:
            logger.error(f"Failed to initialize OpenGL in DepthPortalComposite: {e}")
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

    def _setup_fbo(self, w: int, h: int):
        self.fbo = gl.glGenFramebuffers(1)
        self.out_tex = gl.glGenTextures(1)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.out_tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.out_tex, 0)
        gl.glDrawBuffers(1, [gl.GL_COLOR_ATTACHMENT0])
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def process_frame(self, input_texture: int, params: Dict[str, Any], context) -> int:
        if not input_texture or input_texture <= 0:
             return 0
             
        if self._mock_mode:
            if hasattr(context, "outputs"):
                context.outputs["video_out"] = input_texture
            return input_texture
             
        inputs = getattr(context, "inputs", {})
        bg_tex = inputs.get("background_in", 0)
        depth_tex = inputs.get("depth_in", 0)
        
        w, h = getattr(context, 'width', 1920), getattr(context, 'height', 1080)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, w, h)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        
        gl.glUseProgram(self.prog)
        
        # Unit 0: Background
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, bg_tex)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
        
        # Unit 1: Foreground (input_texture / video_in)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "u_fg_tex"), 1)
        
        # Unit 2: Depth Matte
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_tex)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "u_depth_tex"), 2)
        
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_background"), 1 if bg_tex > 0 else 0)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), 1 if depth_tex > 0 else 0)
        
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        
        # Handle Parameters
        # Spec says parameters are 0-10 based, we'll map them inside the python side if needed
        # Or just pass them if they are already mapped or expect 0-10.
        # Wait, the spec specifies the ranges: slice_near (0-10), slice_far (0-10).
        # We need to normalize them or let the shader use them as-is.
        # But wait, depth in the legacy shader: `float depth = texture(u_depth_tex, uv).r;` is 0-1 normalized!
        # So slice_near from 0-10 needs to be normalized to 0-1 inside the shader or converted here.
        # The VJLive-2 code did: self._map_param('sliceNear', 0.0, 1.0) which mapped a 0-10 value to 0.0-1.0.
        # Yes, standard VJLive-2 params were always 0-10. Our METADATA spec marks min/max.
        # We should map 'slice_near' (0-10) -> (0-1) for the depth comparison.
        
        def map_p(val, in_min, in_max, out_min, out_max):
            return out_min + ((val - in_min) / (in_max - in_min)) * (out_max - out_min)
        
        sn = float(params.get("slice_near", 1.5))
        sf = float(params.get("slice_far", 4.0))
        
        # Map 0-10 to 0-1 for depth
        norm_sn = map_p(sn, 0.0, 10.0, 0.0, 1.0)
        norm_sf = map_p(sf, 0.0, 10.0, 0.0, 1.0)
        
        if norm_sn > norm_sf:
            norm_sn, norm_sf = norm_sf, norm_sn
            
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_slice_near"), norm_sn)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_slice_far"), norm_sf)
        
        # Edge Softness 0-10 -> 0-1
        es = float(params.get("edge_softness", 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_edge_softness"), map_p(es, 0.0, 10.0, 0.0, 1.0))
        
        # Spill Suppress 0-10 -> 0-1
        spill = float(params.get("spill_suppress", 3.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_spill"), map_p(spill, 0.0, 10.0, 0.0, 1.0))
        
        # Bg Opacity 0-1 -> 0-1 (wait, spec says max is 1.0 in VJLive3)
        # The Spec: {"name": "bg_opacity", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
        bg_op = float(params.get("bg_opacity", 1.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_bg_opacity"), bg_op)
        
        # FG Scale 0.0-10.0. Spec maps it to 0.3-2.0 historically? Legacy code: _map_param('fgScale', 0.3, 2.0)
        # Let's map 0-10 to 0.3-2.0
        fgs = float(params.get("fg_scale", 1.0))
        # Wait, the spec min=0, max=10, default=1.0. Let's just pass the factor so 1.0 = scale 1.0
        # If it's VJLive3, the parameter may be actual scale factor. Let's assume the parameter is literally the scale.
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_fg_scale"), max(fgs, 0.01))
        
        # FG Offsets -1.0 to 1.0, pass as is
        fgx = float(params.get("fg_offset_x", 0.0))
        fgy = float(params.get("fg_offset_y", 0.0))
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "u_fg_offset"), fgx, fgy)
        
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.out_tex
            
        return self.out_tex

    def cleanup(self) -> None:
        if self._mock_mode:
            return
            
        try:
            if self.out_tex:
                gl.glDeleteTextures(1, [self.out_tex])
                self.out_tex = None
            if self.fbo:
                gl.glDeleteFramebuffers(1, [self.fbo])
                self.fbo = None
            if self.vbo:
                gl.glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.vao:
                gl.glDeleteVertexArrays(1, [self.vao])
                self.vao = None
            if self.prog:
                gl.glDeleteProgram(self.prog)
                self.prog = None
        except Exception as e:
            logger.error(f"Cleanup Error in DepthPortalComposite: {e}")
