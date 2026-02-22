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

DEPTH_CONTOUR_DATAMOSH_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D tex1;        // Video B — pixel source (what gets datamoshed)
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Contour parameters
uniform float contour_interval;    // Depth spacing between contours
uniform float contour_width;       // Thickness of contour detection
uniform int num_contours;          // Number of distinct contour levels
uniform float contour_smoothness;  // Smoothness of contour detection

// Datamosh along contours
uniform float flow_strength;       // How strongly artifacts flow along contours
uniform float cross_contamination; // Artifacts bleeding across contours
uniform float layer_separation;    // Independent glitch per depth layer
uniform float temporal_coherence;  // Temporal consistency of contour artifacts

// Visual
uniform float contour_glow;        // Neon glow on contour lines
uniform float chromatic_contour;   // RGB separation along contours
uniform vec3 contour_color;        // Color of contour lines
uniform float topographic_steps;   // Posterize depth into discrete layers

// Feedback
uniform float feedback_strength;
uniform float accumulation;

// Contour detection
float detect_contour(float depth, float interval, float width) {
    float safe_interval = max(interval, 0.001);
    float quantized = floor(depth / safe_interval) * safe_interval;
    float dist_to_contour = abs(depth - quantized);
    return 1.0 - smoothstep(0.0, width * safe_interval, dist_to_contour);
}

// Tangent to contour (perpendicular to depth gradient)
vec2 contour_tangent(sampler2D dtex, vec2 p) {
    float t = 1.0 / max(resolution.x, 1.0);
    float dx = texture(dtex, p + vec2(t, 0.0)).r - 
               texture(dtex, p - vec2(t, 0.0)).r;
    float dy = texture(dtex, p + vec2(0.0, t)).r - 
               texture(dtex, p - vec2(0.0, t)).r;
    
    vec2 gradient = vec2(dx, dy);
    float grad_mag = length(gradient);
    
    if (grad_mag < 0.001) return vec2(1.0, 0.0);
    
    // Tangent is perpendicular to gradient
    vec2 normal = normalize(gradient);
    return vec2(-normal.y, normal.x);  // Rotate 90 degrees
}

void main() {

    // Detect if Video B is connected (not all black)
    vec4 testB = texture(tex1, vec2(0.5));
    bool hasDualInput = (testB.r + testB.g + testB.b) > 0.01;

    vec4 current = texture(tex0, v_uv);
    vec4 previous = texture(texPrev, v_uv);
    float depth = texture(depth_tex, v_uv).r;
    
    // ====== STAGE 1: CONTOUR DETECTION ======
    float interval = contour_interval * 0.5 + 0.1;  // 0.1 to 0.6 meters
    float width = contour_width * 0.1 + 0.01;
    
    float contour_strength = detect_contour(depth, interval, width);
    
    // Which contour layer are we in?
    int layer_index = int(depth / max(interval, 0.001));
    float layer_phase = float(layer_index) / float(max(num_contours, 1));
    
    // ====== STAGE 2: TOPOGRAPHIC POSTERIZATION ======
    float depth_stepped = depth;
    if (topographic_steps > 0.0) {
        int steps = int(topographic_steps * 20.0) + 2;
        depth_stepped = floor(depth * float(steps)) / float(steps);
    }
    
    // ====== STAGE 3: CONTOUR-FOLLOWING DATAMOSH ======
    vec2 tangent = contour_tangent(depth_tex, v_uv);
    
    // Flow displacement along contour
    vec2 flow_displacement = tangent * flow_strength * 0.02;
    flow_displacement *= contour_strength;  // Stronger flow at contour
    
    // Add per-layer variation
    float layer_chaos = sin(layer_phase * 6.28318 + time * 0.5) * 0.5 + 0.5;
    flow_displacement *= (0.5 + layer_chaos * layer_separation);
    
    // Add temporal coherence (less jitter)
    float temporal_phase = floor(time * (1.0 - temporal_coherence) * 10.0) / 10.0;
    flow_displacement *= (1.0 + sin(temporal_phase + layer_phase * 3.14159) * 0.3);
    
    // ====== STAGE 4: CROSS-LAYER CONTAMINATION ======
    vec2 cross_displacement = vec2(0.0);
    if (cross_contamination > 0.0 && contour_strength > 0.3) {
        // Sample from adjacent depth layer
        vec2 grad = vec2(
            texture(depth_tex, v_uv + vec2(1.0/max(resolution.x, 1.0), 0.0)).r - 
            texture(depth_tex, v_uv - vec2(1.0/max(resolution.x, 1.0), 0.0)).r,
            texture(depth_tex, v_uv + vec2(0.0, 1.0/max(resolution.y, 1.0))).r - 
            texture(depth_tex, v_uv - vec2(0.0, 1.0/max(resolution.y, 1.0))).r
        );
        
        if (length(grad) > 0.001) {
            vec2 grad_dir = normalize(grad);
            cross_displacement = grad_dir * cross_contamination * 0.015;
        }
    }
    
    // ====== STAGE 5: SAMPLE & COMPOSITE ======
    vec2 total_displacement = flow_displacement + cross_displacement;
    vec2 displaced_uv = v_uv + total_displacement;
    displaced_uv = clamp(displaced_uv, 0.001, 0.999);
    
    vec4 displaced = texture(texPrev, displaced_uv);
    
    // Mix based on contour strength and layer separation
    float mosh_factor = contour_strength * (0.3 + layer_separation * 0.7);
    vec4 result = mix(current, displaced, mosh_factor);
    
    // ====== STAGE 6: CHROMATIC CONTOUR ======
    if (chromatic_contour > 0.0 && contour_strength > 0.2) {
        float chroma_scale = chromatic_contour * 0.01;
        vec2 r_uv = v_uv + total_displacement + tangent * chroma_scale;
        vec2 b_uv = v_uv + total_displacement - tangent * chroma_scale;
        r_uv = clamp(r_uv, 0.001, 0.999);
        b_uv = clamp(b_uv, 0.001, 0.999);
        
        result.r = mix(result.r, texture(texPrev, r_uv).r, 0.5);
        result.b = mix(result.b, texture(texPrev, b_uv).b, 0.5);
    }
    
    // ====== STAGE 7: CONTOUR LINE RENDERING ======
    if (contour_glow > 0.0 && contour_strength > 0.4) {
        vec3 glow_col = contour_color * contour_glow;
        float glow_intensity = contour_strength * contour_glow * 0.5;
        result.rgb = mix(result.rgb, glow_col, glow_intensity);
    }
    
    // ====== STAGE 8: FEEDBACK ======
    if (feedback_strength > 0.0) {
        result = mix(result, previous, feedback_strength * 0.3 * contour_strength);
    }
    
    if (accumulation > 0.0) {
        vec4 prev_direct = texture(texPrev, v_uv);
        result = max(result, prev_direct * accumulation * 0.5 * contour_strength);
    }
    
    fragColor = mix(current, result, u_mix);
}
"""

METADATA = {
    "name": "Depth Contour Datamosh",
    "description": "Topographic depth slice datamoshing.",
    "version": "1.0.0",
    "author": "Antigravity",
    "category": "Visual Depth",
    "tags": ["datamosh", "contour", "feedback", "topography"],
    "status": "active",
    "parameters": [
        {"name": "contourInterval", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "contourWidth", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "numContours", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "contourSmoothness", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "flowStrength", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "crossContamination", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "layerSeparation", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "temporalCoherence", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "contourGlow", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "chromaticContour", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "contourColorR", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "contourColorG", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "contourColorB", "type": "float", "min": 0.0, "max": 10.0, "default": 10.0},
        {"name": "topographicSteps", "type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
        {"name": "feedbackStrength", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "accumulation", "type": "float", "min": 0.0, "max": 10.0, "default": 2.0},
        {"name": "u_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
    ],
    "inputs": ["video_in", "video_b_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthContourDatamoshPlugin(EffectPlugin):
    """P3-VD31: Depth Contour Datamosh effect port mapping VJlive-2 parameters."""
    
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
            gl.glShaderSource(fragment, DEPTH_CONTOUR_DATAMOSH_FRAGMENT)
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
            logger.warning(f"Failed to initialize GL FBOs inside DepthContourDatamosh: {e}")
            self._mock_mode = True

    def process_frame(self, input_texture: int, params: Dict[str, Any], context: PluginContext) -> int:
        if input_texture is None or input_texture == 0:
            return 0
            
        self.time += 0.016 # simulate advancing time if not passed
            
        if self._mock_mode:
            context.outputs["video_out"] = input_texture
            return input_texture

        try:
            depth_in = context.inputs.get("depth_in", input_texture)
            video_b_in = context.inputs.get("video_b_in", input_texture)

            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            h = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_HEIGHT)
            
            current_fbo = self.fbos[f"feedback_{1 - self.ping_pong}"]
            current_tex = self.textures[f"feedback_{1 - self.ping_pong}"]
            prev_tex = self.textures[f"feedback_{self.ping_pong}"]
            
            gl.glBindTexture(gl.GL_TEXTURE_2D, current_tex)
            tex_w = gl.glGetTexLevelParameteriv(gl.GL_TEXTURE_2D, 0, gl.GL_TEXTURE_WIDTH)
            if tex_w != w:
                # Re-allocate textures cleanly on resolution jump
                for t in self.textures.values():
                    gl.glBindTexture(gl.GL_TEXTURE_2D, t)
                    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
                
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, current_fbo)
                gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, current_tex, 0)
                
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, current_fbo)
            gl.glViewport(0, 0, w, h)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            
            gl.glUseProgram(self.prog)
            self._bind_uniforms(params, w, h)
            
            # Bind textures
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)

            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, video_b_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex1"), 1)
            
            gl.glActiveTexture(gl.GL_TEXTURE2)
            gl.glBindTexture(gl.GL_TEXTURE_2D, prev_tex)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "texPrev"), 2)

            gl.glActiveTexture(gl.GL_TEXTURE3)
            gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
            gl.glUniform1i(gl.glGetUniformLocation(self.prog, "depth_tex"), 3)
            
            # Draw
            gl.glBindVertexArray(self.vao)
            gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
            gl.glBindVertexArray(0)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            
            self.ping_pong = 1 - self.ping_pong
            context.outputs["video_out"] = current_tex
            return current_tex
            
        except Exception as e:
            logger.error(f"Render failed: {e}")
            return input_texture

    def _map_param(self, params, name, out_min, out_max, default_val):
        val = params.get(name, default_val)
        return out_min + (val / 10.0) * (out_max - out_min)

    def _bind_uniforms(self, params, w, h):
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), float(self.time))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_mix"), float(params.get("u_mix", 1.0)))

        # Mapping parameters into target shader uniforms
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "contour_interval"), self._map_param(params, 'contourInterval', 0.0, 1.0, 4.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "contour_width"), self._map_param(params, 'contourWidth', 0.0, 1.0, 3.0))
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "num_contours"), int(self._map_param(params, 'numContours', 2, 20, 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "contour_smoothness"), self._map_param(params, 'contourSmoothness', 0.0, 1.0, 5.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "flow_strength"), self._map_param(params, 'flowStrength', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "cross_contamination"), self._map_param(params, 'crossContamination', 0.0, 1.0, 3.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "layer_separation"), self._map_param(params, 'layerSeparation', 0.0, 1.0, 5.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "temporal_coherence"), self._map_param(params, 'temporalCoherence', 0.0, 1.0, 5.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "contour_glow"), self._map_param(params, 'contourGlow', 0.0, 1.0, 3.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "chromatic_contour"), self._map_param(params, 'chromaticContour', 0.0, 1.0, 3.0))
        gl.glUniform3f(gl.glGetUniformLocation(self.prog, "contour_color"), 
            self._map_param(params, 'contourColorR', 0.0, 1.0, 0.0),
            self._map_param(params, 'contourColorG', 0.0, 1.0, 5.0),
            self._map_param(params, 'contourColorB', 0.0, 1.0, 10.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "topographic_steps"), self._map_param(params, 'topographicSteps', 0.0, 1.0, 0.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "feedback_strength"), self._map_param(params, 'feedbackStrength', 0.0, 1.0, 3.0))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "accumulation"), self._map_param(params, 'accumulation', 0.0, 1.0, 2.0))

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
                logger.error(f"Error cleaning up FBOs/Textures during DepthContourDatamosh unload: {e}")
                
        for k in self.textures:
            self.textures[k] = None
            self.fbos[k] = None

