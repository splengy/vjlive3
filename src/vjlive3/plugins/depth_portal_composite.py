import os
import logging
from typing import Dict, Any, Optional
import numpy as np

from vjlive3.plugins.api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

try:
    if os.environ.get("PYTEST_MOCK_GL"):
        raise ImportError("Forced MOCK GL for pytest")
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
    gl = None

PORTAL_COMPOSITE_FRAGMENT = """
#version 330 core

in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;            // background video (second camera/feed)
uniform sampler2D tex1;            // depth matte (R channel, 0-1 normalized)
uniform sampler2D tex2;            // foreground (from depth camera's color or colorized depth)
uniform float u_mix;

uniform float u_slice_near;        // near threshold (0-1 normalized)
uniform float u_slice_far;         // far threshold (0-1 normalized)
uniform float u_edge_softness;     // matte feathering
uniform float u_spill;             // edge spill suppression
uniform float u_bg_opacity;        // background visibility
uniform float u_fg_scale;          // foreground scale
uniform vec2  u_fg_offset;         // foreground position offset
uniform vec2  resolution;

// Smoothstep-based matte from depth
float computeMatte(float depth) {
    if (depth < 0.001) return 0.0;  // invalid depth = transparent

    // Feathered depth slice
    float softness = max(u_edge_softness * 0.1, 0.001);
    float near_fade = smoothstep(u_slice_near - softness, u_slice_near + softness, depth);
    float far_fade = smoothstep(u_slice_far + softness, u_slice_far - softness, depth);

    return near_fade * far_fade;
}

// Edge spill suppression: blur the matte slightly and use the difference
// to suppress color bleeding at transition edges
float suppressSpill(float matte, vec2 uv_coord, float strength) {
    if (strength < 0.01) return matte;

    vec2 pixel = 1.0 / resolution;
    float sum = 0.0;
    float count = 0.0;
    for (float dx = -2.0; dx <= 2.0; dx += 1.0) {
        for (float dy = -2.0; dy <= 2.0; dy += 1.0) {
            float d = texture(tex1, uv_coord + vec2(dx, dy) * pixel * 2.0).r;
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
    float depth = texture(tex1, v_uv).r;
    float matte = computeMatte(depth);

    // Apply spill suppression
    matte = suppressSpill(matte, v_uv, u_spill);
    matte = clamp(matte, 0.0, 1.0);

    // Sample foreground (performer from depth camera) with scale/offset
    vec2 fg_uv = (v_uv - 0.5) / u_fg_scale + 0.5 + u_fg_offset;
    
    // Bounds check to avoid mirrored edge wrapping 
    vec4 fg_sample = texture(tex2, fg_uv);
    if (fg_uv.x < 0.0 || fg_uv.x > 1.0 || fg_uv.y < 0.0 || fg_uv.y > 1.0) {
         fg_sample.a = 0.0;
         matte = 0.0; 
    }
    vec3 fg_color = fg_sample.rgb;

    // Sample background (second video feed)
    vec3 bg_color = texture(tex0, v_uv).rgb * u_bg_opacity;

    // Composite: performer over background using depth matte
    vec3 result = mix(bg_color, fg_color, matte * u_mix);

    // Optional: add subtle edge glow at matte boundary for AR feel
    float edge_detect = abs(dFdx(matte)) + abs(dFdy(matte));
    vec3 edge_color = vec3(0.3, 0.6, 1.0) * edge_detect * 4.0;
    result += edge_color * 0.3;

    fragColor = vec4(result, 1.0);
}
"""

METADATA = {
    "name": "Depth Portal Composite",
    "description": "Isolates performer using depth and composites onto a new background.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["composite", "chromakey", "depth"],
    "status": "active",
    "parameters": [
        {"name": "slice_near", "type": "float", "min": 0.0, "max": 1.0, "default": 0.15, "description": "Near threshold"},
        {"name": "slice_far", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4, "description": "Far threshold"},
        {"name": "edge_softness", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "spill_suppress", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "bg_opacity", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0},
        {"name": "fg_scale", "type": "float", "min": 0.1, "max": 3.0, "default": 1.0},
        {"name": "fg_offset_x", "type": "float", "min": -1.0, "max": 1.0, "default": 0.0},
        {"name": "fg_offset_y", "type": "float", "min": -1.0, "max": 1.0, "default": 0.0},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in", "color_in"],
    "outputs": ["video_out"]
}

class DepthPortalCompositePlugin(EffectPlugin):
    """Depth-based chroma-key compositing effect."""
    
    def __init__(self) -> None:
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.fbo = None
        self.out_tex = None

    def _compile_shader(self):
        if not HAS_GL: return None
        try:
            vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
            gl.glShaderSource(vertex, "#version 330 core\\nlayout(location=0) in vec2 pos; layout(location=1) in vec2 uv; out vec2 v_uv; void main() { gl_Position = vec4(pos, 0.0, 1.0); v_uv = uv; }")
            gl.glCompileShader(vertex)
            
            fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fragment, PORTAL_COMPOSITE_FRAGMENT)
            gl.glCompileShader(fragment)
            
            if gl.glGetShaderiv(fragment, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
                logger.error(f"Fragment compile failed: {gl.glGetShaderInfoLog(fragment)}")
                return None
                
            prog = gl.glCreateProgram()
            gl.glAttachShader(prog, vertex)
            gl.glAttachShader(prog, fragment)
            gl.glLinkProgram(prog)
            return prog
        except Exception as e:
            logger.error(f"Failed to compile shader locally: {e}")
            return None

    def initialize(self, context: PluginContext) -> None:
        super().initialize(context)
        if self._mock_mode: return
            
        try:
            self.prog = self._compile_shader()
            if not self.prog:
                self._mock_mode = True
                return

            self.fbo = gl.glGenFramebuffers(1)
            self.out_tex = gl.glGenTextures(1)
                
            self.vao = gl.glGenVertexArrays(1)
            self.vbo = gl.glGenBuffers(1)
            gl.glBindVertexArray(self.vao)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
            quad_data = np.array([
                -1.0, -1.0,  0.0, 0.0,
                 1.0, -1.0,  1.0, 0.0,
                -1.0,  1.0,  0.0, 1.0,
                 1.0,  1.0,  1.0, 1.0
            ], dtype=np.float32)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, quad_data.nbytes, quad_data, gl.GL_STATIC_DRAW)
            gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(0))
            gl.glEnableVertexAttribArray(0)
            gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(8))
            gl.glEnableVertexAttribArray(1)
            gl.glBindVertexArray(0)
            
        except Exception as e:
            logger.warning(f"Failed to initialize GL FBOs inside PortalComposite: {e}")
            self._mock_mode = True

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        video_in = input_texture
        depth_in = context.inputs.get("depth_in")
        color_in = context.inputs.get("color_in")
        
        if video_in is None or video_in == 0:
            return 0
            
        if depth_in is None or color_in is None:
            context.outputs["video_out"] = video_in
            return video_in

        near = params.get("slice_near", 0.15)
        far = params.get("slice_far", 0.4)

        if near > far:
            near, far = far, near
            
        params["_clamped_near"] = near
        params["_clamped_far"] = far
        
        if self._mock_mode:
            # Fallback to background mock test 
            bg_opacity = params.get("bg_opacity", 1.0)
            if bg_opacity > 0.0:
                context.outputs["video_out"] = color_in # Fg takes priority if full opacity
                return color_in
            return video_in

        try:
            gl.glBindTexture(gl.GL_TEXTURE_2D, video_in)
            w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            h = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_HEIGHT)
            
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.out_tex)
            tex_w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            
            if tex_w != w:
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
                gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.out_tex, 0)
                
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
            gl.glViewport(0, 0, w, h)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            
            gl.glUseProgram(self.prog)
            
            gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), params.get("u_mix", 1.0))
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_slice_near"), near)
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_slice_far"), far)
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_edge_softness"), params.get("edge_softness", 0.4))
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_spill"), params.get("spill_suppress", 0.3))
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_bg_opacity"), params.get("bg_opacity", 1.0))
            gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_fg_scale"), params.get("fg_scale", 1.0))
            gl.glUniform2f(gl.glGetUniformLocation(self.prog, "u_fg_offset"), params.get("fg_offset_x", 0.0), params.get("fg_offset_y", 0.0))
            
            gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D, video_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
            
            gl.glActiveTexture(gl.GL_TEXTURE1); gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex1"), 1)
            
            gl.glActiveTexture(gl.GL_TEXTURE2); gl.glBindTexture(gl.GL_TEXTURE_2D, color_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex2"), 2)
            
            gl.glBindVertexArray(self.vao)
            gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
            gl.glBindVertexArray(0)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            
            context.outputs["video_out"] = self.out_tex
            return self.out_tex
            
        except Exception as e:
            logger.error(f"Render failed: {e}")
            return video_in

    def cleanup(self) -> None:
        if not self._mock_mode:
            try:
                if self.out_tex: gl.glDeleteTextures(1, [self.out_tex])
                if self.fbo: gl.glDeleteFramebuffers(1, [self.fbo])
                if self.prog: gl.glDeleteProgram(self.prog)
                if hasattr(self, 'vao') and self.vao: gl.glDeleteVertexArrays(1, [self.vao])
                if hasattr(self, 'vbo') and self.vbo: gl.glDeleteBuffers(1, [self.vbo])
            except Exception as e:
                logger.error(f"Error cleaning up FBOs/Textures during PortalComposite unload: {e}")
                
        self.out_tex = None
        self.fbo = None
