"""
P3-VD57: Depth Mosaic Plugin for VJLive3.
Ported from legacy VJlive-2 DepthMosaicEffect.
Single-Pass FSQ filter deriving block mappings and edge mask limits 
dynamically from normalized variables over the standard video feed.
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
    "name": "Depth Mosaic",
    "description": "Depth-controlled video tessellation and quantization.",
    "version": "1.0.0",
    "plugin_type": "depth_effect",
    "category": "generator",
    "tags": ["depth", "mosaic", "tessellation", "quantization", "voronoi"],
    "priority": 1,
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"],
    "parameters": [
        {"name": "cell_size_min", "type": "float", "min": 1.0, "max": 20.0, "default": 2.0},
        {"name": "cell_size_max", "type": "float", "min": 10.0, "max": 120.0, "default": 64.0},
        {"name": "tile_style", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "depth_invert", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "gap_width", "type": "float", "min": 0.0, "max": 5.0, "default": 2.0},
        {"name": "gap_color", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "color_quantize", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "rotate_by_depth", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0}
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
uniform sampler2D u_depth_tex;    
uniform float time;
uniform vec2 resolution;
uniform int has_depth;

uniform float u_cell_min;         
uniform float u_cell_max;         
uniform float u_tile_style;       
uniform float u_invert;           
uniform float u_gap;              
uniform float u_gap_color;        
uniform float u_quantize;         
uniform float u_rotate;           

#define PI 3.14159265

vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
    return fract(sin(p) * 43758.5453);
}

void main() {
    float depth = 0.0;
    if (has_depth == 1) depth = texture(u_depth_tex, uv).r;
    
    if (depth < 0.01) {
        fragColor = vec4(texture(tex0, uv).rgb, 1.0);
        return;
    }

    float d = mix(depth, 1.0 - depth, u_invert);

    float cell_size = mix(u_cell_max, u_cell_min, d);
    cell_size = max(cell_size, 1.0);  
    vec2 cell_pixels = vec2(cell_size) / resolution;

    vec2 mosaic_uv;
    float edge_mask = 1.0;

    if (u_tile_style < 0.25) {
        mosaic_uv = floor(uv / cell_pixels + 0.5) * cell_pixels;
        vec2 cell_pos = fract(uv / cell_pixels);
        float gap_norm = u_gap / cell_size;
        edge_mask = step(gap_norm, cell_pos.x) * step(gap_norm, cell_pos.y)
                  * step(cell_pos.x, 1.0 - gap_norm) * step(cell_pos.y, 1.0 - gap_norm);

    } else if (u_tile_style < 0.5) {
        // HEXAGONAL TILES
        vec2 hex_size = cell_pixels * vec2(1.732, 1.0);  
        vec2 scaled = uv / hex_size;

        float row = floor(scaled.y);
        float offset = mod(row, 2.0) * 0.5;
        scaled.x += offset;

        mosaic_uv = (floor(scaled) + 0.5 - vec2(offset, 0.0)) * hex_size;

        vec2 hex_frac = fract(scaled) - 0.5;
        float hex_dist = max(abs(hex_frac.x), abs(hex_frac.y) * 0.866 + abs(hex_frac.x) * 0.5);
        float gap_norm = u_gap / cell_size * 0.5;
        edge_mask = smoothstep(0.5 - gap_norm, 0.5 - gap_norm - 0.01, hex_dist);

    } else if (u_tile_style < 0.75) {
        // CIRCULAR TILES
        mosaic_uv = floor(uv / cell_pixels + 0.5) * cell_pixels;

        vec2 cell_center = mosaic_uv;
        float dist = length((uv - cell_center) / cell_pixels);
        float gap_norm = u_gap / cell_size;
        edge_mask = smoothstep(0.5, 0.5 - gap_norm - 0.02, dist);

    } else {
        // VORONOI TILES
        vec2 cell_id = floor(uv / cell_pixels);
        float min_dist = 10.0;
        vec2 nearest_center = vec2(0.0);

        for (float dy = -1.0; dy <= 1.0; dy += 1.0) {
            for (float dx = -1.0; dx <= 1.0; dx += 1.0) {
                vec2 neighbor = cell_id + vec2(dx, dy);
                vec2 point = (neighbor + hash2(neighbor) * 0.8) * cell_pixels;
                float dist = length(uv - point);
                if (dist < min_dist) {
                    min_dist = dist;
                    nearest_center = point;
                }
            }
        }
        mosaic_uv = nearest_center;

        float gap_norm = u_gap * 0.002;
        float second_dist = 10.0;
        for (float dy = -1.0; dy <= 1.0; dy += 1.0) {
            for (float dx = -1.0; dx <= 1.0; dx += 1.0) {
                vec2 neighbor = cell_id + vec2(dx, dy);
                vec2 point = (neighbor + hash2(neighbor) * 0.8) * cell_pixels;
                float dist = length(uv - point);
                if (dist > min_dist + 0.0001 && dist < second_dist) {
                    second_dist = dist;
                }
            }
        }
        float edge_dist = (second_dist - min_dist);
        edge_mask = smoothstep(gap_norm, gap_norm + 0.001, edge_dist);
    }

    if (u_rotate > 0.01) {
        float angle = d * u_rotate * PI * 2.0;
        vec2 center = mosaic_uv;
        vec2 delta = uv - center;
        float c = cos(angle);
        float s = sin(angle);
        mosaic_uv = center + vec2(delta.x * c - delta.y * s,
                                   delta.x * s + delta.y * c);
    }

    vec3 color = texture(tex0, mosaic_uv).rgb;

    if (u_quantize > 0.01) {
        float levels = mix(256.0, 4.0, u_quantize);
        color = floor(color * levels + 0.5) / levels;
    }

    vec3 gap_col = vec3(u_gap_color);
    color = mix(gap_col, color, edge_mask);

    fragColor = vec4(color, 1.0);
}
"""

class DepthMosaicPlugin(EffectPlugin):
    """
    Depth Mosaic single-pass full-screen quad filter evaluating
    dynamic geometric tessellation boundaries mapped cleanly to distance offsets.
    """

    def __init__(self):
        super().__init__()
        self._mock_mode = not HAS_GL
        
        self.prog = 0
        self.empty_vao = 0
        
        self.fbo = 0
        self.tex = 0

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
            logger.error(f"Failed to config OpenGL in depth_mosaic: {e}")
            self._mock_mode = True
            return False

    def _free_fbo(self):
        try:
            if self.tex != 0:
                gl.glDeleteTextures(1, [self.tex])
            if self.fbo != 0:
                gl.glDeleteFramebuffers(1, [self.fbo])
        except Exception:
            pass
            
        self.tex = 0
        self.fbo = 0

    def _allocate_fbo(self, w: int, h: int):
        self._free_fbo()
        self._width = w
        self._height = h
        
        self.fbo = gl.glGenFramebuffers(1)
        self.tex = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.tex, 0)
        
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        

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
            self._allocate_fbo(w, h)
            
        inputs = getattr(context, "inputs", {})
        depth_in = inputs.get("depth_in", 0)
        time_val = getattr(context, 'time', 0.0)
        
        has_depth_val = 1 if depth_in > 0 else 0
        
        gl.glViewport(0, 0, w, h)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glUseProgram(self.prog)
        
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, input_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "tex0"), 0)

        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, depth_in)
        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "u_depth_tex"), 1)

        gl.glUniform1i(gl.glGetUniformLocation(self.prog, "has_depth"), has_depth_val)
        gl.glUniform2f(gl.glGetUniformLocation(self.prog, "resolution"), float(w), float(h))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "time"), float(time_val))

        # Parameters are passed directly at their native ranges (no 0-10 normalization)
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_cell_min"), float(params.get("cell_size_min", 2.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_cell_max"), float(params.get("cell_size_max", 64.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_tile_style"), float(params.get("tile_style", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_invert"), float(params.get("depth_invert", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_gap"), float(params.get("gap_width", 2.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_gap_color"), float(params.get("gap_color", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_quantize"), float(params.get("color_quantize", 0.0)))
        gl.glUniform1f(gl.glGetUniformLocation(self.prog, "u_rotate"), float(params.get("rotate_by_depth", 0.0)))

        gl.glBindVertexArray(self.empty_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        
        gl.glBindVertexArray(0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if hasattr(context, "outputs"):
            context.outputs["video_out"] = self.tex 
            
        return self.tex

    def cleanup(self) -> None:
        try:
            self._free_fbo()
            if hasattr(gl, 'glDeleteProgram') and self.prog != 0:
                gl.glDeleteProgram(self.prog)
            if hasattr(gl, 'glDeleteVertexArrays') and self.empty_vao != 0:
                gl.glDeleteVertexArrays(1, [self.empty_vao])
        except Exception as e:
            logger.error(f"Cleanup Error in DepthMosaic: {e}")
        finally:
            self.prog = 0
            self.empty_vao = 0

