import os
import logging
from typing import Dict, Any, Optional
import numpy as np

from vjlive3.plugins.api import EffectPlugin, PluginContext

logger = logging.getLogger(__name__)

# Mock GL for headless pytests via environment flag injection
try:
    if os.environ.get("PYTEST_MOCK_GL"):
        raise ImportError("Forced MOCK GL for pytest")
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
    gl = None

DEPTH_DUAL_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;           // Primary video
uniform sampler2D texPrev;        // Feedback loop
uniform sampler2D depth_a;        // Depth camera A
uniform sampler2D depth_b;        // Depth camera B
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Core
uniform float interaction_mode;    // Which dual-depth interaction (0-10 maps to 6 modes)
uniform float interaction_amount;  // Intensity of the interaction
uniform float depth_align;         // Alignment offset between two depth maps
uniform float depth_scale_b;       // Scale compensation for depth B (different ranges)

// Collision
uniform float collision_glow;      // Glow at collision surfaces
uniform float collision_width;     // Width of collision detection zone
uniform float collision_hue;       // Color of collision visualization

// Interference
uniform float interference_freq;   // Interference pattern frequency
uniform float interference_phase;  // Phase offset between depth waves

// Volume
uniform float volume_density;      // Volumetric rendering density
uniform float volume_absorption;   // Light absorption in volume

// Visual
uniform float edge_enhance;        // Enhanced edges from dual-depth
uniform float color_depth_a;       // Color tint from depth A
uniform float color_depth_b;       // Color tint from depth B
uniform float feedback;            // Temporal feedback

vec3 hsv2rgb(vec3 c) {
    vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0/3.0, 1.0/3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

// Sobel edge on a depth texture
float depth_edge(sampler2D dtex, vec2 p) {
    float t = 1.5 / max(resolution.x, 1.0);
    float ml = texture(dtex, p + vec2(-t, 0)).r;
    float mr = texture(dtex, p + vec2( t, 0)).r;
    float mu = texture(dtex, p + vec2(0, -t)).r;
    float md = texture(dtex, p + vec2(0,  t)).r;
    return length(vec2(mr - ml, md - mu));
}

void main() {
    vec4 source = texture(tex0, v_uv);
    vec4 previous = texture(texPrev, v_uv);

    // Read both depth maps
    float dA = texture(depth_a, v_uv).r;
    float dB = texture(depth_b, v_uv + vec2(depth_align * 0.1, 0.0)).r;

    // Scale compensation
    dB *= depth_scale_b;

    // Depth difference and relationship
    float diff = abs(dA - dB);
    float avg = (dA + dB) * 0.5;
    float min_d = min(dA, dB);
    float max_d = max(dA, dB);

    float edgeA = depth_edge(depth_a, v_uv);
    float edgeB = depth_edge(depth_b, v_uv + vec2(depth_align * 0.1, 0.0));
    float dual_edge = max(edgeA, edgeB);

    float bass = pow(abs(sin(time * 2.5)), 4.0);
    float mode = interaction_mode;
    vec3 result = source.rgb;

    // ====== MODE 0: COLLISION ======
    if (mode < 1.7) {
        float collision_zone = smoothstep(collision_width * 0.1, 0.0, diff);
        vec3 coll_color = hsv2rgb(vec3(
            collision_hue + time * 0.1,
            0.8,
            collision_zone * collision_glow * 2.0
        ));
        result = mix(source.rgb, source.rgb + coll_color, collision_zone * interaction_amount);
        
        float coll_edge = smoothstep(0.02, 0.0, abs(diff - collision_width * 0.05));
        result += coll_color * coll_edge * 0.5;
    }
    // ====== MODE 1: INTERFERENCE ======
    else if (mode < 3.3) {
        float wave_a = sin(dA * interference_freq * 30.0 + time * 2.0);
        float wave_b = sin(dB * interference_freq * 30.0 + time * 2.0 + interference_phase * 6.283);
        
        float constructive = (wave_a + wave_b) * 0.5;
        float destructive = abs(wave_a - wave_b) * 0.5;
        
        vec3 int_color = hsv2rgb(vec3(
            constructive * 0.3 + time * 0.05,
            0.7 + destructive * 0.3,
            0.5 + constructive * 0.5
        ));
        
        float pattern = constructive * constructive;
        result = mix(source.rgb, int_color, pattern * interaction_amount * 0.7);
        
        float standing = smoothstep(0.1, 0.0, abs(constructive)) * smoothstep(0.1, 0.0, abs(destructive));
        result += vec3(standing * 0.3) * interaction_amount;
    }
    // ====== MODE 2: DIFFERENCE ======
    else if (mode < 5.0) {
        float disagree = smoothstep(0.01, 0.15, diff);
        vec3 diff_color = (dA < dB) ? 
            hsv2rgb(vec3(color_depth_a, 0.9, 0.8 + disagree * 0.2)) : 
            hsv2rgb(vec3(color_depth_b, 0.9, 0.8 + disagree * 0.2));
            
        result = mix(source.rgb, diff_color, disagree * interaction_amount * 0.6);
        float strong_disagree = smoothstep(0.1, 0.3, diff);
        result += diff_color * strong_disagree * 0.3 * bass;
    }
    // ====== MODE 3: VOLUMETRIC ======
    else if (mode < 6.7) {
        float solidity = 1.0 - smoothstep(0.0, 0.1 * volume_density, diff);
        float thickness = max_d - min_d;
        float absorption = exp(-thickness * volume_absorption * 10.0);
        
        vec3 vol_color = source.rgb * absorption;
        vol_color *= 1.0 + solidity * 0.5;
        
        float vol_edge = smoothstep(0.02, 0.08, diff) * smoothstep(0.15, 0.08, diff);
        vec3 edge_glow = hsv2rgb(vec3(avg + time * 0.1, 0.7, 1.0));
        vol_color += edge_glow * vol_edge * interaction_amount;
        
        result = mix(source.rgb, vol_color, interaction_amount);
    }
    // ====== MODE 4: XOR ======
    else if (mode < 8.3) {
        float occ_a = smoothstep(0.02, 0.1, dB - dA);
        float occ_b = smoothstep(0.02, 0.1, dA - dB);
        float xor_mask = abs(occ_a - occ_b);
        
        vec3 xor_color = source.rgb;
        xor_color = mix(xor_color, xor_color * hsv2rgb(vec3(color_depth_a, 0.6, 1.2)), occ_a * interaction_amount);
        xor_color = mix(xor_color, xor_color * hsv2rgb(vec3(color_depth_b, 0.6, 1.2)), occ_b * interaction_amount);
        
        float xor_edge = smoothstep(0.08, 0.05, abs(occ_a - occ_b));
        xor_color += vec3(xor_edge * 0.3) * interaction_amount;
        result = xor_color;
    }
    // ====== MODE 5: PARALLAX ======
    else {
        float disparity = (dA - dB);
        float shift_amount = disparity * interaction_amount * 0.05;
        vec2 shifted_uv = clamp(v_uv + vec2(shift_amount, 0.0), 0.001, 0.999);
        
        vec4 shifted = texture(tex0, shifted_uv);
        result.r = source.r;
        result.g = shifted.g;
        result.b = shifted.b;
        
        vec3 parallax_tint = hsv2rgb(vec3(avg * 0.5 + time * 0.05, 0.3, 1.0));
        result = mix(result, result * parallax_tint, abs(disparity) * 2.0);
    }

    if (edge_enhance > 0.0) {
        float combined_edge = edgeA + edgeB;
        float exclusive_edge = abs(edgeA - edgeB);
        vec3 edge_color = hsv2rgb(vec3(time * 0.1 + avg, 0.8, 1.0));
        result += edge_color * combined_edge * edge_enhance * 3.0;
        result += vec3(1.0, 0.5, 0.0) * exclusive_edge * edge_enhance * 2.0;
    }

    if (feedback > 0.0) {
        float fb = feedback * (0.3 + avg * 0.4);
        result = mix(result, previous.rgb, clamp(fb, 0.0, 0.9));
    }

    fragColor = mix(source, vec4(clamp(result, 0.0, 1.5), 1.0), u_mix);
}
"""

METADATA = {
    "name": "Depth Dual",
    "description": "Six interaction modes for mapping stereo depth fields: Collision, Interference, Difference, Volumetric, XOR, Parallax.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["dual", "depth", "stereo", "parallax"],
    "status": "active",
    "parameters": [
        {"name": "interactionMode", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "interactionAmount", "type": "float", "min": 0.0, "max": 10.0, "default": 6.0},
        {"name": "depthAlign", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "depthScaleB", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "collisionGlow", "type": "float", "min": 0.0, "max": 10.0, "default": 6.0},
        {"name": "collisionWidth", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "collisionHue", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "interferenceFreq", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "interferencePhase", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "volumeDensity", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "volumeAbsorption", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "edgeEnhance", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "colorDepthA", "type": "float", "min": 0.0, "max": 10.0, "default": 2.0},
        {"name": "colorDepthB", "type": "float", "min": 0.0, "max": 10.0, "default": 6.0},
        {"name": "feedback", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in_a", "depth_in_b"],
    "outputs": ["video_out"]
}


class DepthDualPlugin(EffectPlugin):
    """P3-VD34: Depth Dual effect port mapping VJlive-2 dual depth patterns to VJLive3."""
    
    def __init__(self) -> None:
        super().__init__()
        self._mock_mode = not HAS_GL
        self.prog = None
        self.ping_pong = 0
        self.time = 0.0
        
        self.textures: Dict[str, Optional[int]] = {"feedback_0": None, "feedback_1": None}
        self.fbos: Dict[str, Optional[int]] = {"feedback_0": None, "feedback_1": None}

    def _compile_shader(self):
        if not HAS_GL: return None
        try:
            vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
            gl.glShaderSource(vertex, "#version 330 core\\nlayout(location=0) in vec2 pos; layout(location=1) in vec2 uv; out vec2 v_uv; void main() { gl_Position = vec4(pos, 0.0, 1.0); v_uv = uv; }")
            gl.glCompileShader(vertex)
            
            fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fragment, DEPTH_DUAL_FRAGMENT)
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
        if self._mock_mode:
            return
            
        try:
            self.prog = self._compile_shader()
            if not self.prog:
                self._mock_mode = True
                return

            tex_ids = gl.glGenTextures(2)
            fbo_ids = gl.glGenFramebuffers(2)
            if isinstance(tex_ids, int): tex_ids = [tex_ids, tex_ids+1]
            if isinstance(fbo_ids, int): fbo_ids = [fbo_ids, fbo_ids+1]
                
            for i, key in enumerate(self.textures.keys()):
                self.textures[key] = tex_ids[i]
                self.fbos[key] = fbo_ids[i]
                
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
            logger.warning(f"Failed to initialize GL FBOs inside DepthDualPlugin: {e}")
            self._mock_mode = True

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if input_texture is None or input_texture == 0:
            return 0
            
        self.time += 0.016
            
        if self._mock_mode:
            context.outputs["video_out"] = input_texture
            return input_texture

        try:
            depth_in_a = context.inputs.get("depth_in_a", input_texture)
            depth_in_b = context.inputs.get("depth_in_b", input_texture)

            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            h = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_HEIGHT)
            
            # Ping-pong for temporal feedback
            current_fbo = self.fbos[f"feedback_{1 - self.ping_pong}"]
            current_tex = self.textures[f"feedback_{1 - self.ping_pong}"]
            prev_tex = self.textures[f"feedback_{self.ping_pong}"]
            
            gl.glBindTexture(gl.GL_TEXTURE_2D, current_tex)
            tex_w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            if tex_w != w:
                for k in ["feedback_0", "feedback_1"]:
                    gl.glBindTexture(gl.GL_TEXTURE_2D, self.textures[k])
                    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbos[k])
                    gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.textures[k], 0)
                
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, current_fbo)
            gl.glViewport(0, 0, w, h)
            
            gl.glUseProgram(self.prog)
            self._bind_uniforms(params, w, h)
            
            # Textures
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)
            
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, prev_tex)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrev"), 1)
            
            gl.glActiveTexture(gl.GL_TEXTURE2)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in_a)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_a"), 2)
            
            gl.glActiveTexture(gl.GL_TEXTURE3)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in_b)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_b"), 3)
            
            gl.glBindVertexArray(self.vao)
            gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
            gl.glBindVertexArray(0)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            
            self.ping_pong = 1 - self.ping_pong
            context.outputs["video_out"] = current_tex
            return current_tex
            
        except Exception as e:
            logger.error(f"Render failed in Depth Dual: {e}")
            return input_texture

    def _map_param(self, params, name, out_min, out_max, default_val):
        val = params.get(name, default_val)
        return out_min + (val / 10.0) * (out_max - out_min)

    def _bind_uniforms(self, params, w, h):
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), float(self.time))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), params.get("u_mix", 1.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "interaction_mode"), self._map_param(params, 'interactionMode', 0.0, 10.0, 0.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "interaction_amount"), self._map_param(params, 'interactionAmount', 0.0, 1.0, 6.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_align"), self._map_param(params, 'depthAlign', -0.5, 0.5, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "depth_scale_b"), self._map_param(params, 'depthScaleB', 0.5, 2.0, 5.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "collision_glow"), self._map_param(params, 'collisionGlow', 0.0, 1.0, 6.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "collision_width"), self._map_param(params, 'collisionWidth', 0.0, 1.0, 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "collision_hue"), self._map_param(params, 'collisionHue', 0.0, 1.0, 5.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "interference_freq"), self._map_param(params, 'interferenceFreq', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "interference_phase"), self._map_param(params, 'interferencePhase', 0.0, 1.0, 0.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "volume_density"), self._map_param(params, 'volumeDensity', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "volume_absorption"), self._map_param(params, 'volumeAbsorption', 0.0, 1.0, 4.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "edge_enhance"), self._map_param(params, 'edgeEnhance', 0.0, 1.0, 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "color_depth_a"), self._map_param(params, 'colorDepthA', 0.0, 1.0, 2.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "color_depth_b"), self._map_param(params, 'colorDepthB', 0.0, 1.0, 6.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "feedback"), self._map_param(params, 'feedback', 0.0, 1.0, 3.0))

    def cleanup(self) -> None:
        if not self._mock_mode:
            try:
                textures_to_delete = [t for t in self.textures.values() if t is not None]
                if textures_to_delete:
                    gl.glDeleteTextures(len(textures_to_delete), textures_to_delete)
                fbos_to_delete = [f for f in self.fbos.values() if f is not None]
                if fbos_to_delete:
                    gl.glDeleteFramebuffers(len(fbos_to_delete), fbos_to_delete)
                if self.prog:
                    gl.glDeleteProgram(self.prog)
                if hasattr(self, 'vao') and self.vao:
                    gl.glDeleteVertexArrays(1, [self.vao])
                if hasattr(self, 'vbo') and self.vbo:
                    gl.glDeleteBuffers(1, [self.vbo])
            except Exception as e:
                logger.error(f"Error cleaning up FBOs/Textures during DepthDual unload: {e}")
                
        for k in self.textures:
            self.textures[k] = None
            self.fbos[k] = None
