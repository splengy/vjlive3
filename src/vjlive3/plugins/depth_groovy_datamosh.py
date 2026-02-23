"""
P3-VD51: Depth Groovy Datamosh Plugin for VJLive3.
Ported from legacy VJlive-2 DepthGroovyDatamoshEffect.
Monolithic maximalist psychedelic shader mapping 16 parameters dynamically against
a Ping-Pong temporal UV-displacement structure.
"""

from typing import Dict, Any, Optional
import numpy as np
import logging

try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

from .api import EffectPlugin, PluginContext
logger = logging.getLogger(__name__)

METADATA = {
    "name": "DepthGroovyDatamosh",
    "version": "3.0.0",
    "description": "Maximalist psychedelic depth datamosh featuring recursive zooms, kaleidoscopes, and spiral feedbacks.",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "psychedelic",
    "tags": ["depth", "datamosh", "kaleidoscope", "spiral", "feedback", "rainbow"],
    "priority": 1,
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "rainbowIntensity", "type": "float", "default": 6.0, "min": 0.0, "max": 10.0},
        {"name": "rainbowSpeed", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "kaleidoscope", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "spiralFeedback", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "spiralSpeed", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "breathing", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "breathingSpeed", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "depthZoom", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "pixelSort", "type": "float", "default": 3.0, "min": 0.0, "max": 10.0},
        {"name": "melt", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "moshAmount", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "blockChaos", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "colorBleed", "type": "float", "default": 4.0, "min": 0.0, "max": 10.0},
        {"name": "saturationBoost", "type": "float", "default": 6.0, "min": 0.0, "max": 10.0},
        {"name": "glowTrails", "type": "float", "default": 5.0, "min": 0.0, "max": 10.0},
        {"name": "strobeFlash", "type": "float", "default": 0.0, "min": 0.0, "max": 10.0}
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

uniform sampler2D tex0;          
uniform sampler2D texPrev;       
uniform sampler2D depth_tex;     
uniform float time;
uniform vec2 resolution;
uniform int has_depth;

uniform float rainbow_intensity; 
uniform float rainbow_speed;     
uniform float kaleidoscope;      
uniform float spiral_feedback;   
uniform float spiral_speed;      
uniform float breathing;         
uniform float breathing_speed;   
uniform float depth_zoom;        
uniform float pixel_sort;        
uniform float melt;              
uniform float mosh_amount;       
uniform float block_chaos;       
uniform float color_bleed;       
uniform float saturation_boost;  
uniform float glow_trails;       
uniform float strobe_flash;      

float hash(vec2 p) {
    p = fract(p * vec2(443.897, 441.423));
    p += dot(p, p.yx + 19.19);
    return fract((p.x + p.y) * p.x);
}

vec3 hsv2rgb(vec3 c) {
    vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0/3.0, 1.0/3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec2 depth_gradient(vec2 p) {
    float texel = 1.0 / resolution.x;
    float dL = texture(depth_tex, p + vec2(-texel, 0.0)).r;
    float dR = texture(depth_tex, p + vec2( texel, 0.0)).r;
    float dU = texture(depth_tex, p + vec2(0.0,  texel)).r;
    float dD = texture(depth_tex, p + vec2(0.0, -texel)).r;
    return vec2(dR - dL, dU - dD);
}

void main() {
    float depth = 0.0;
    if (has_depth == 1) {
        depth = texture(depth_tex, uv).r;
    }
    vec2 coord = uv;

    // === STAGE 1: UV TRANSFORMATIONS ===
    if (kaleidoscope > 0.1) {
        int folds = int(kaleidoscope * 6.0) + 2; 
        vec2 centered = coord - 0.5;
        float angle = atan(centered.y, centered.x);
        float radius = length(centered);

        float fold_angle = 6.283 / float(folds);
        angle = mod(angle, fold_angle);
        if (angle > fold_angle * 0.5) angle = fold_angle - angle; 
        angle += depth * 1.0 + time * 0.2;
        coord = vec2(cos(angle), sin(angle)) * radius + 0.5;
    }

    if (spiral_feedback > 0.0) {
        vec2 centered = coord - 0.5;
        float radius = length(centered);
        float angle = atan(centered.y, centered.x);

        float spiral_amount = spiral_feedback * (1.0 - depth * 0.5);
        angle += spiral_amount * 0.3 * sin(time * spiral_speed + radius * 8.0);

        float zoom = 1.0 - spiral_feedback * 0.02 * (1.0 + depth * depth_zoom);
        radius *= zoom;
        coord = vec2(cos(angle), sin(angle)) * radius + 0.5;
    }

    if (breathing > 0.0) {
        vec2 centered = coord - 0.5;
        float pulse = sin(time * breathing_speed * 2.0 + depth * 6.283 * 2.0);
        float scale = 1.0 + pulse * breathing * 0.05 * (1.0 + depth);
        coord = centered * scale + 0.5;
    }

    if (melt > 0.0) {
        vec2 grad = vec2(0.0);
        if (has_depth == 1) grad = depth_gradient(coord);
        
        float wave_x = sin(coord.y * 20.0 + time * 2.0 + depth * 8.0) * melt * 0.02;
        float wave_y = cos(coord.x * 20.0 + time * 1.7 + depth * 6.0) * melt * 0.02;
        coord += vec2(wave_x, wave_y) + grad * melt * 0.1;
    }

    if (depth_zoom > 0.0) {
        vec2 centered = coord - 0.5;
        float zoom_factor = 1.0 - depth * depth_zoom * 0.1;
        coord = centered * zoom_factor + 0.5;
    }

    if (pixel_sort > 0.0 && has_depth == 1) {
        vec2 grad = depth_gradient(coord);
        float grad_mag = length(grad);
        if (grad_mag > 0.001) {
            vec2 sort_dir = normalize(grad);
            float sort_amount = pixel_sort * 0.03 * grad_mag * 20.0;
            float strip = floor(dot(coord, sort_dir) * resolution.x / 4.0);
            float strip_hash = hash(vec2(strip, floor(time * 2.0)));
            coord += sort_dir * sort_amount * strip_hash;
        }
    }

    coord = clamp(coord, 0.001, 0.999);

    // === STAGE 2: SAMPLING ===
    vec4 current = texture(tex0, coord);
    vec4 previous = texture(texPrev, coord);
    vec4 result = current;

    // === STAGE 3: DATAMOSH ===
    if (mosh_amount > 0.0) {
        float block = max(4.0, block_chaos * 40.0 + 4.0);
        vec2 blockUV = floor(coord * resolution / block) * block / resolution;
        float block_hash = hash(blockUV + vec2(floor(time * 3.0)));

        float depth_mosh = 0.5 + 0.5 * sin(depth * 6.283 + time);
        float mosh_factor = mosh_amount * depth_mosh;

        if (block_hash > 0.5) {
            vec2 displace = (vec2(hash(blockUV), hash(blockUV + 99.0)) - 0.5) * 0.04 * mosh_factor;
            vec4 moshed = texture(texPrev, clamp(coord + displace, 0.001, 0.999));
            result = mix(result, moshed, mosh_factor * 0.5);
        }

        if (color_bleed > 0.0) {
            float cb = color_bleed * 0.01 * mosh_factor;
            vec2 grad = vec2(0.0);
            if (has_depth == 1) grad = depth_gradient(coord);
            result.r = mix(result.r, texture(texPrev, clamp(coord + grad * cb, 0.001, 0.999)).r, mosh_factor * 0.3);
            result.b = mix(result.b, texture(texPrev, clamp(coord - grad * cb, 0.001, 0.999)).b, mosh_factor * 0.3);
        }
    }

    float fb_blend = spiral_feedback * 0.3 + glow_trails * 0.4;
    fb_blend = clamp(fb_blend, 0.0, 0.9);
    result = mix(result, previous, fb_blend);

    // === STAGE 4: COLOR PSYCHEDELIA ===
    if (rainbow_intensity > 0.0) {
        float hue = fract(depth * 2.0 + time * rainbow_speed * 0.1);
        vec3 rainbow = hsv2rgb(vec3(hue, 1.0, 1.0));

        vec3 overlay;
        for (int i = 0; i < 3; i++) {
            float base = result.rgb[i];
            float blend = rainbow[i];
            overlay[i] = base < 0.5 ? 2.0 * base * blend : 1.0 - 2.0 * (1.0 - base) * (1.0 - blend);
        }
        result.rgb = mix(result.rgb, overlay, rainbow_intensity * 0.6);
        
        if (has_depth == 1) {
            float edge = length(depth_gradient(coord)) * 8.0;
            result.rgb += rainbow * edge * rainbow_intensity * 0.5;
        }
    }

    if (saturation_boost > 0.0) {
        vec3 hsv = rgb2hsv(clamp(result.rgb, 0.0, 1.0));
        hsv.y = clamp(hsv.y * (1.0 + saturation_boost * 2.0), 0.0, 1.0);
        hsv.z = clamp(hsv.z * (1.0 + saturation_boost * 0.3), 0.0, 1.0);
        result.rgb = hsv2rgb(hsv);
    }

    if (glow_trails > 0.0) {
        vec3 glow = max(result.rgb, previous.rgb * glow_trails * 0.8);
        result.rgb = mix(result.rgb, glow, glow_trails * 0.5);
    }

    if (strobe_flash > 0.0) {
        float flash = pow(max(0.0, sin(time * strobe_flash * 8.0)), 8.0);
        flash *= pow(max(0.0, sin(time * strobe_flash * 8.0 + depth * 3.14)), 4.0);
        result.rgb += vec3(flash * 0.5);
    }

    fragColor = vec4(clamp(result.rgb, 0.0, 3.0), 1.0);
}
"""

class DepthGroovyDatamoshPlugin(EffectPlugin):
    """Depth Groovy Datamosh mapping psychedelic parameters onto a ping-pong buffer."""

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        self.program = 0
        self.empty_vao = 0
        
        self.fbo1 = 0
        self.tex1 = 0
        self.fbo2 = 0
        self.tex2 = 0
        
        self.is_fbo1_active = True
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
            self.program = self._compile_shader(VERTEX_SHADER_SOURCE, FRAGMENT_SHADER_SOURCE)
            self.empty_vao = gl.glGenVertexArrays(1)
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to config OpenGL in depth_groovy_datamosh: {e}")
            self._mock_mode = True
            return False

    def _free_fbo(self):
        try:
            if self.tex1 != 0: gl.glDeleteTextures(1, [self.tex1])
            if self.tex2 != 0: gl.glDeleteTextures(1, [self.tex2])
            if self.fbo1 != 0: gl.glDeleteFramebuffers(1, [self.fbo1])
            if self.fbo2 != 0: gl.glDeleteFramebuffers(1, [self.fbo2])
        except Exception:
            pass
        self.fbo1 = self.fbo2 = 0
        self.tex1 = self.tex2 = 0

    def _create_fbo_tex(self, w: int, h: int):
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

    def _allocate_buffers(self, w: int, h: int):
        self._free_fbo()
        self._width = w
        self._height = h
        self.fbo1, self.tex1 = self._create_fbo_tex(w, h)
        self.fbo2, self.tex2 = self._create_fbo_tex(w, h)

    def _map_norm(self, val: float, max_v: float = 1.0) -> float:
        return (max(0.0, min(10.0, float(val))) / 10.0) * max_v

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
            
        inputs = getattr(context, "inputs", {})
        depth_in = inputs.get("depth_in", 0)
        time_val = getattr(context, 'time', 0.0)
        
        read_fbo = self.tex1 if self.is_fbo1_active else self.tex2
        write_fbo = self.fbo2 if self.is_fbo1_active else self.fbo1
        write_texture = self.tex2 if self.is_fbo1_active else self.tex1
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, write_fbo)
        gl.glViewport(0, 0, w, h)
        gl.glUseProgram(self.program)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "tex0"), 0)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, read_fbo)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "texPrev"), 1)
        
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.program, "depth_tex"), 2)

        gl.glUniform1i(gl.glGetUniformLocation(self.program, "has_depth"), 1 if depth_in > 0 else 0)
        gl.glUniform2f(gl.glGetUniformLocation(self.program, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "time"), float(time_val))

        gl.glUniform1f(gl.glGetUniformLocation(self.program, "rainbow_intensity"), self._map_norm(params.get("rainbowIntensity", 6.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "rainbow_speed"), self._map_norm(params.get("rainbowSpeed", 4.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "kaleidoscope"), self._map_norm(params.get("kaleidoscope", 3.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "spiral_feedback"), self._map_norm(params.get("spiralFeedback", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "spiral_speed"), self._map_norm(params.get("spiralSpeed", 4.0), 3.0))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "breathing"), self._map_norm(params.get("breathing", 4.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "breathing_speed"), self._map_norm(params.get("breathingSpeed", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "depth_zoom"), self._map_norm(params.get("depthZoom", 3.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "pixel_sort"), self._map_norm(params.get("pixelSort", 3.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "melt"), self._map_norm(params.get("melt", 4.0)))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "mosh_amount"), self._map_norm(params.get("moshAmount", 4.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "block_chaos"), self._map_norm(params.get("blockChaos", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "color_bleed"), self._map_norm(params.get("colorBleed", 4.0)))
        
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "saturation_boost"), self._map_norm(params.get("saturationBoost", 6.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "glow_trails"), self._map_norm(params.get("glowTrails", 5.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.program, "strobe_flash"), self._map_norm(params.get("strobeFlash", 0.0)))

        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        self.is_fbo1_active = not self.is_fbo1_active

        if hasattr(context, "outputs"):
            context.outputs["video_out"] = write_texture
            
        return write_texture

    def cleanup(self) -> None:
        try:
            self._free_fbo()
            if hasattr(gl, 'glDeleteProgram') and self.program != 0:
                gl.glDeleteProgram(self.program)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao != 0:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup Error in DepthGroovyDatamosh: {e}")
        finally:
            self.program = 0
            self.empty_vao = 0

