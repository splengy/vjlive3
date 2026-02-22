"""
P1-R2: ShaderProgram
Compiled GLSL vertex + fragment shader with cached uniform setters.
Synthesized from VJlive-2 core.shaders.program.
"""
import moderngl
from typing import Dict, Any, Tuple
import numpy as np

# Built-in GLSL Shaders (Embedded Strings)
BASE_VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 position;
layout(location = 1) in vec2 texCoord;

uniform vec2 u_ViewOffset;     // Offset in pixels (e.g., [1920.0, 0.0])
uniform vec2 u_ViewResolution; // Resolution of this node (e.g., [1920.0, 1080.0])
uniform vec2 u_TotalResolution; // Global canvas resolution (e.g., [3840.0, 1080.0])

out vec2 uv;
out vec2 v_uv; // Local UV (0.0 to 1.0) for screen-space effects

void main() {
    gl_Position = vec4(position, 0.0, 1.0);
    
    // Pass local UVs
    v_uv = texCoord;
    
    // Calculate Global UVs logic:
    vec2 local_pixel = texCoord * u_ViewResolution;
    vec2 global_pixel = local_pixel + u_ViewOffset;
    
    // Normalize to 0.0 - 1.0 range
    vec2 total_res = u_TotalResolution;
    if (total_res.x < 1.0) total_res = u_ViewResolution;
    
    uv = global_pixel / total_res;
}
"""

PASSTHROUGH_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;
uniform sampler2D tex0;

void main() {
    fragColor = vec4(texture(tex0, v_uv).rgb, 1.0);
}
"""

OVERLAY_FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;
uniform sampler2D texOverlay;

void main() {
    fragColor = texture(texOverlay, v_uv);
}
"""

WARP_VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 position;
layout(location = 1) in vec2 texCoord;

uniform vec2 u_view_offset;  // Offset for spatial stitching
uniform vec2 u_view_scale;   // Scale for spatial stitching
uniform vec2 corners[4];     // 4 corner points for bilinear warp
uniform vec2 bezier_mesh[25]; // 5x5 Bezier control points (u,v pairs)
uniform int warp_mode;       // 0: none, 1: corner pin, 2: bezier mesh

out vec2 uv;

void main() {
    gl_Position = vec4(position, 0.0, 1.0);
    vec2 base_uv = texCoord * u_view_scale + u_view_offset;

    if (warp_mode == 0) {
        // No warping
        uv = base_uv;
    } else if (warp_mode == 1) {
        // 4-point corner pin bilinear interpolation
        float u = base_uv.x;
        float v = base_uv.y;

        vec2 top = mix(corners[0], corners[1], u);
        vec2 bottom = mix(corners[3], corners[2], u);
        uv = mix(top, bottom, v);
    } else if (warp_mode == 2) {
        // 5x5 Bezier mesh warp
        float u = base_uv.x;
        float v = base_uv.y;

        int iu = int(u * 4.0);
        int iv = int(v * 4.0);
        iu = clamp(iu, 0, 3);
        iv = clamp(iv, 0, 3);

        float lu = fract(u * 4.0);
        float lv = fract(v * 4.0);

        int idx00 = iv * 5 + iu;
        int idx10 = iv * 5 + iu + 1;
        int idx01 = (iv + 1) * 5 + iu;
        int idx11 = (iv + 1) * 5 + iu + 1;

        vec2 p00 = bezier_mesh[idx00];
        vec2 p10 = bezier_mesh[idx10];
        vec2 p01 = bezier_mesh[idx01];
        vec2 p11 = bezier_mesh[idx11];

        vec2 top = mix(p00, p10, lu);
        vec2 bottom = mix(p01, p11, lu);
        uv = mix(top, bottom, lv);
    }
}
"""

WARP_BLEND_FRAGMENT = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D screenTexture;
uniform float edgeFeather; // 0.0 to 1.0 (blend width as fraction of screen)
uniform int nodeSide;      // 0: Left, 1: Middle, 2: Right
uniform bool calibrationMode;

void main() {
    vec4 color = texture(screenTexture, uv);
    float alpha = 1.0;

    // Edge Blending Logic
    if (nodeSide == 0 && uv.x > (1.0 - edgeFeather)) {
        alpha = (1.0 - uv.x) / edgeFeather;
    } else if (nodeSide == 2 && uv.x < edgeFeather) {
        alpha = uv.x / edgeFeather;
    }

    if (calibrationMode) {
        vec2 grid_uv = uv * 20.0; // 20x20 grid
        vec2 grid_pos = fract(grid_uv);
        float grid_line = step(0.95, grid_pos.x) + step(0.95, grid_pos.y);

        float center_dist = length(uv - 0.5);
        float cross = step(0.48, uv.x) * step(uv.x, 0.52) + step(0.48, uv.y) * step(uv.y, 0.52);

        vec3 cal_color = mix(vec3(0.0), vec3(0.0, 1.0, 0.0), grid_line + cross);
        float coord_bright = (floor(grid_uv.x) + floor(grid_uv.y)) / 40.0;
        cal_color += vec3(coord_bright);

        color = vec4(cal_color, 1.0);
    }

    fragColor = vec4(color.rgb * alpha, 1.0);
}
"""

class ShaderProgram:
    """Compiled GLSL vertex + fragment shader with cached uniform setters."""

    METADATA = {
        "author": "Antigravity (Manager)",
        "phase": "P1-R2",
        "description": "ModernGL Shader Program manager"
    }

    def __init__(self, vertex_source: str, fragment_source: str, name: str = "unnamed") -> None:
        """Compile and link shader. Caches all active uniform locations."""
        ctx = moderngl.get_context()
        if not ctx:
            raise RuntimeError("No active ModernGL context found.")

        self.name = name
        
        try:
            self._mgl_program = ctx.program(
                vertex_shader=vertex_source,
                fragment_shader=fragment_source,
            )
        except moderngl.Error as e:
            raise RuntimeError(f"Shader compilation failed for '{name}': {e}")
            
        # Cache uniforms safely. We only cache the keys exposed by the moderngl Program.
        # Note: moderngl gives access to uniforms via program[key].
        self.uniforms: Dict[str, bool] = {}
        for key in self._mgl_program:
            # ModernGL objects expose uniform introspection
            self.uniforms[key] = True

    def use(self) -> None:
        """glUseProgram is handled automatically by ModernGL when rendering.
        This function is kept purely for semantic compatibility with older code."""
        pass

    def set_uniform(self, name: str, value: object) -> None:
        """Set a uniform by Python type dispatch.
        
        ModernGL `program['uniform_name'].value = X` handles the dispatch safely.
        """
        if name not in self.uniforms:
            return

        uniform_obj = self._mgl_program.get(name, None)
        if uniform_obj is None:
            return

        # Handle specific ModernGL type conversions
        if isinstance(value, bool):
            uniform_obj.value = int(value)
        elif isinstance(value, (int, float)):
            uniform_obj.value = value
        elif isinstance(value, (tuple, list)):
            if len(value) in (2, 3, 4):
                uniform_obj.value = tuple(float(v) for v in value)
            else:
                 # If list of vectors, ModernGL handles numpy arrays trivially or flattened lists.
                 # Safest is to cast to bytes if treating as bulk uniform array depending on moderngl version.
                 try:
                      uniform_obj.write(np.array(value, dtype='f4').tobytes())
                 except Exception:
                      pass
        elif isinstance(value, np.ndarray):
            # Write raw bytes for ndarrays (e.g., matrices or arrays of vecs)
            try:
                uniform_obj.write(value.astype('f4').tobytes())
            except Exception:
                pass

    @property
    def program(self) -> int:
        """Underlying OpenGL Program ID for low-level interop."""
        return self._mgl_program.glo

    def delete(self) -> None:
        """glDeleteProgram equivalent."""
        if hasattr(self, '_mgl_program') and self._mgl_program:
            self._mgl_program.release()
            self._mgl_program = None

    def __del__(self) -> None:
        self.delete()
