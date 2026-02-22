"""
P1-R2: EffectChain
Ping-pong framebuffer effect pipeline.
Synthesized safely from VJlive-2 chain.py.
"""
import time
import logging
import threading
import ctypes
import numpy as np
import moderngl
from typing import List, Optional, Any, Tuple
import cv2

from .framebuffer import Framebuffer
from .program import ShaderProgram, PASSTHROUGH_FRAGMENT, BASE_VERTEX_SHADER, WARP_VERTEX_SHADER, WARP_BLEND_FRAGMENT
from .effect import Effect

logger = logging.getLogger("vjlive3.render.chain")

class EffectChain:
    """Ping-pong framebuffer effect pipeline."""

    # Required by PRIME_DIRECTIVE Rule 2
    METADATA = {
        "author": "Antigravity (Manager)",
        "phase": "P1-R2",
        "description": "Multi-pass ping-pong rendering pipeline via ModernGL"
    }

    def __init__(self, width: int = 1920, height: int = 1080) -> None:
        self.width = width
        self.height = height
        
        ctx = moderngl.get_context()
        if not ctx:
            raise RuntimeError("ModernGL context missing. Initialize OpenGLContext first.")

        # Thread safety lock for effect list modification
        self._lock = threading.RLock()
        self.effects: List[Effect] = []
        
        # Spatial stitching data
        self.view_offset = [0.0, 0.0]
        self.view_scale = [1.0, 1.0]
        
        # Ping-pong and feedback FBOs
        self.fbo_a = Framebuffer(width, height)
        self.fbo_b = Framebuffer(width, height)
        self.fbo_prev = Framebuffer(width, height)
        
        # Internal cache tracking
        self._last_output_texture: Optional[int] = None
        self._texture_map = {} # Maps glo (int) -> moderngl.Texture
        
        # Fullscreen quad for drawing effect overlays (2D pos + 2D UV)
        # 4 vertices using Triangle Strip (0,1,2,3)
        quad_data = np.array([
            -1.0, -1.0, 0.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0, -1.0, 1.0, 0.0,
             1.0,  1.0, 1.0, 1.0
        ], dtype='f4')
        self.vbo = ctx.buffer(quad_data)
        
        self.passthrough = ShaderProgram(BASE_VERTEX_SHADER, PASSTHROUGH_FRAGMENT, "passthrough")
        # Ensure VAO maps strictly to Program attribute layout: layout 0 is position, layout 1 is texCoord
        # Since moderngl parses GLSL, we pair the buffer by explicit declaration
        self.vao = ctx.vertex_array(
             self.passthrough._mgl_program,
             [(self.vbo, '2f 2f', 'position', 'texCoord')]
        )
        
        self.post_processing_shader: Optional[ShaderProgram] = None
        self.calibration_mode = False
        
        # PBO Async Readback State Tracking
        self._pbo_size = width * height * 3 # RGB by default
        # ModernGL handles async reading directly via `buffer.read()`. We'll retain two buffers to ping-pong
        self._pbos = [ctx.buffer(reserve=self._pbo_size), ctx.buffer(reserve=self._pbo_size)]
        self._pbo_index = 0
        self._readback_buffer = np.empty((height, width, 3), dtype=np.uint8)
        self._first_frame_read = False

    def add_effect(self, effect: Effect) -> None:
        with self._lock:
            self.effects.append(effect)

    def remove_effect(self, name: str) -> None:
        with self._lock:
            self.effects = [e for e in self.effects if e.name != name]

    def get_available_effects(self) -> List[str]:
        return [e.name for e in self.effects]

    def set_spatial_view(self, offset: List[float], scale: List[float]) -> None:
        """Set view_offset/view_scale uniforms for multi-node stitching."""
        self.view_offset = offset
        self.view_scale = scale

    def upload_texture(self, image: np.ndarray) -> int:
        """Upload HxWx3 uint8 BGR array. Returns GL texture ID."""
        ctx = moderngl.get_context()
        # image is assumed (H, W, 3). Moderngl takes (width, height) + components (3)
        # Flip vertically before uploading to match OpenGL coordinates natively if needed, but the original did it post-read.
        h, w = image.shape[0], image.shape[1]
        tex = ctx.texture((w, h), 3, image.tobytes())
        tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._texture_map[tex.glo] = tex
        return tex.glo

    def update_texture(self, texture: int, image: np.ndarray) -> None:
        """Update existing texture. Resizes image if dimensions changed."""
        tex_obj = self._texture_map.get(texture)
        if not tex_obj:
            return
            
        th, tw = tex_obj.height, tex_obj.width
        h, w = image.shape[0], image.shape[1]
        if w != tw or h != th:
            try:
                if cv2:
                    image = cv2.resize(image, (tw, th))
            except Exception:
                logger.warning(f"Could not resize texture upload {w}x{h} -> {tw}x{th}")
                return
                
        tex_obj.write(image.tobytes())

    def upload_float_texture(self, image: np.ndarray) -> int:
        ctx = moderngl.get_context()
        h, w = image.shape[0], image.shape[1]
        c = image.shape[2] if len(image.shape) > 2 else 1
        dtype = 'f4'
        tex = ctx.texture((w, h), c, image.astype(np.float32).tobytes(), dtype=dtype)
        self._texture_map[tex.glo] = tex
        return tex.glo
        
    def update_float_texture(self, texture: int, image: np.ndarray) -> None:
        self.update_texture(texture, image.astype(np.float32))

    def render(
        self,
        input_texture: int,
        extra_textures: Optional[List[int]] = None,
        audio_reactor: Any = None,
        semantic_layer: Any = None,
    ) -> int:
        """Run enabled effects in order via ping-pong FBOs."""
        t_start = time.time()
        ctx = moderngl.get_context()
        
        with self._lock:
            active_effects = [e for e in self.effects if e.enabled and e.mix > 0]
            
        if not active_effects:
            return input_texture
            
        read_fbo = None
        write_fbo = self.fbo_a
        use_input = True
        
        # We process manually; reconstruct texture object wrappers
        if input_texture:
            in_tex_obj = self._texture_map.get(input_texture)
            if not in_tex_obj:
                # Wrap it blindly if tracking fails (e.g external plugins) - advanced feature. Assuming valid tracking for now.
                pass
                
        for effect in active_effects:
            te_start = time.time()
            write_fbo.bind()
            ctx.clear(0, 0, 0, 1)
            
            # Identify current read texture ID
            current_in_glo = input_texture if use_input else read_fbo.texture
            
            # Optional UI/ML bypass handling
            try:
                pre_tex = effect.pre_process(self, current_in_glo)
                if pre_tex:
                    current_in_glo = pre_tex
            except Exception as e:
                logger.debug(f"Pre-process failed: {e}")
                pass
                
            effect.shader.set_uniform('u_ViewOffset', tuple(self.view_offset))
            effect.shader.set_uniform('u_ViewResolution', (self.width, self.height))
            effect.shader.set_uniform('u_TotalResolution', (self.width, self.height))
            
            try:
                effect.apply_uniforms(te_start, (self.width, self.height), audio_reactor, semantic_layer)
            except Exception as e:
                logger.error(f"Effect {effect.name} render failure: {e}")
                continue # Skip effect but don't crash chain
            
            # Texture Binding Logic relying strictly on moderngl bindings mapping to GLSL names
            tex_obj_0 = self._texture_map.get(current_in_glo, getattr(read_fbo, '_mgl_texture', None) if not use_input else None)
            
            if tex_obj_0:
                tex_obj_0.use(location=0)
                effect.shader.set_uniform('tex0', 0)
            
            # Extra textures
            if extra_textures:
                for j, ex_tex in enumerate(extra_textures):
                    unit = j + 2
                    ex_obj = self._texture_map.get(ex_tex)
                    if ex_obj:
                        ex_obj.use(location=unit)
                        name = f"tex{j+1}"
                        effect.shader.set_uniform(name, unit)
                            
            # Feedback previous texture
            prev_tex_obj = self.fbo_prev._mgl_texture
            if prev_tex_obj:
                prev_tex_obj.use(location=1)
                effect.shader.set_uniform('texPrev', 1)
            
            # Draw call
            vao = ctx.vertex_array(effect.shader._mgl_program, [(self.vbo, '2f 2f', 'position', 'texCoord')])
            vao.render(moderngl.TRIANGLE_STRIP)
            vao.release()
            
            # Ping-Pong Swap
            read_fbo = write_fbo
            write_fbo = self.fbo_b if write_fbo is self.fbo_a else self.fbo_a
            use_input = False
            
            te_end = time.time()
            if (te_end - te_start) > 0.005:
                logger.debug(f"Slow effect {effect.name}: {(te_end-te_start)*1000:.2f}ms")
                
        # Final copy to fbo_prev for feedback
        # ModernGL FBO to FBO copy (Blit mapping)
        dest_mgl = self.fbo_prev._mgl_fbo
        src_mgl = read_fbo._mgl_fbo
        # Blit color attachment 0
        ctx.copy_framebuffer(dest_mgl, src_mgl)
        
        self._last_output_texture = read_fbo.texture
        
        total_time = time.time() - t_start
        if total_time > 0.016:
            logger.debug(f"Slow render chain: {total_time*1000:.2f}ms")
            
        return self._last_output_texture

    def readback_texture(self, texture_id: int) -> Optional[np.ndarray]:
        """Synchronous glReadPixels alternative using moderngl mapping."""
        if not texture_id: return None
        ctx = moderngl.get_context()
        
        # Check standard buffers
        tex_obj = self._texture_map.get(texture_id)
        # Check if it was one of the render targets
        if not tex_obj:
            for target in [self.fbo_a, self.fbo_b, self.fbo_prev]:
                if target.texture == texture_id:
                    tex_obj = target._mgl_texture
                    
        if not tex_obj: return None
        
        try:
            # Requires FBO wrapper to download data directly in GL 3.3 core
            fbo = ctx.framebuffer(color_attachments=[tex_obj])
            data = fbo.read(components=3, alignment=1)
            arr = np.frombuffer(data, dtype=np.uint8).reshape((tex_obj.height, tex_obj.width, 3))
            arr = np.flip(arr, axis=0) # GL is bottom-up
            fbo.release()
            return arr
        except Exception as e:
            logger.warning(f"Sync readback failed: {e}")
            return None

    def readback_texture_async(
        self, texture_id: int, fmt: str = "rgb"
    ) -> Optional[np.ndarray]:
        """PBO ping-pong async readback. 1-frame latency, non-blocking."""
        if not texture_id: return None
        ctx = moderngl.get_context()
        
        tex_obj = self._texture_map.get(texture_id)
        if not tex_obj:
            for target in [self.fbo_a, self.fbo_b, self.fbo_prev]:
                if target.texture == texture_id:
                    tex_obj = target._mgl_texture
                    
        if not tex_obj: return None
        
        comp = 4 if fmt == 'rgba' else 3
        expected_size = tex_obj.width * tex_obj.height * comp
        
        if expected_size != self._pbo_size:
            self._pbos[0].release()
            self._pbos[1].release()
            self._pbo_size = expected_size
            self._pbos = [ctx.buffer(reserve=self._pbo_size), ctx.buffer(reserve=self._pbo_size)]
            self._readback_buffer = np.empty((tex_obj.height, tex_obj.width, comp), dtype=np.uint8)
            self._first_frame_read = False
            
        next_idx = (self._pbo_index + 1) % 2
        write_pbo = self._pbos[next_idx]
        read_pbo = self._pbos[self._pbo_index]
        
        arr_return = None
        
        # Dispatch Async Read (Pack mapping)
        fbo = ctx.framebuffer(color_attachments=[tex_obj])
        # ModernGL handles async glReadPixel to PBO directly
        fbo.read_into(write_pbo, components=comp, alignment=1)
        
        if self._first_frame_read:
            # Map the read PBO
            data_ptr = read_pbo.read() # This forces sync on the N-1 buffer, effectively async relative to draw
            ctypes.memmove(self._readback_buffer.ctypes.data, data_ptr, self._pbo_size)
            arr_return = np.flip(self._readback_buffer, axis=0)
            
        self._first_frame_read = True
        self._pbo_index = next_idx
        fbo.release()
        
        return arr_return

    def readback_last_output(self) -> Optional[np.ndarray]:
        return self.readback_texture(self._last_output_texture)

    def create_downsampled_fbo(self, width: int, height: int) -> Optional[Framebuffer]:
        try:
            return Framebuffer(width, height)
        except:
            return None

    def render_to_downsampled_fbo(self, input_texture: int, fbo: Framebuffer) -> None:
        if not fbo or not input_texture: return
        ctx = moderngl.get_context()
        tex_obj = self._texture_map.get(input_texture)
        if not tex_obj: return
        
        fbo.bind()
        ctx.clear(0, 0, 0, 1)
        self.passthrough.use()
        tex_obj.use(location=0)
        self.passthrough.set_uniform('tex0', 0)
        self.passthrough.set_uniform('u_ViewOffset', tuple(self.view_offset))
        self.passthrough.set_uniform('u_ViewResolution', (self.width, self.height))
        self.passthrough.set_uniform('u_TotalResolution', (self.width, self.height))
        
        self.vao.render(moderngl.TRIANGLE_STRIP)
        fbo.unbind()

    def set_projection_mapping(
        self,
        warp_mode: int = 0,
        corners: Optional[List[float]] = None,
        bezier_mesh: Optional[List[float]] = None,
        edge_feather: float = 0.0,
        node_side: int = 1,
        calibration_mode: bool = False,
    ) -> None:
        if not self.post_processing_shader:
            self.post_processing_shader = ShaderProgram(WARP_VERTEX_SHADER, WARP_BLEND_FRAGMENT, "warp_blend")
            
        self.post_processing_shader.set_uniform('warp_mode', warp_mode)
        self.post_processing_shader.set_uniform('edgeFeather', edge_feather)
        self.post_processing_shader.set_uniform('nodeSide', node_side)
        self.post_processing_shader.set_uniform('calibrationMode', int(calibration_mode))
        
        if corners and len(corners) == 8:
            self.post_processing_shader.set_uniform('corners', np.array(corners, dtype='f4'))
            
        if bezier_mesh and len(bezier_mesh) == 50:
            self.post_processing_shader.set_uniform('bezier_mesh', np.array(bezier_mesh, dtype='f4'))
            
        self.calibration_mode = calibration_mode

    def render_to_screen(
        self, texture: int, viewport: Tuple[int, int, int, int]
    ) -> None:
        if not texture: return
        ctx = moderngl.get_context()
        
        tex_obj = self._texture_map.get(texture)
        if not tex_obj:
            for target in [self.fbo_a, self.fbo_b, self.fbo_prev]:
                if target.texture == texture:
                    tex_obj = target._mgl_texture
                    
        if not tex_obj: return
        
        if ctx.screen:
            ctx.screen.use()
            ctx.screen.viewport = viewport
        
        shader = self.post_processing_shader if self.post_processing_shader else self.passthrough
        
        tex_obj.use(location=0)
        # Handle string map to 0
        sn = "screenTexture" if self.post_processing_shader else "tex0"
        shader.set_uniform(sn, 0)
            
        shader.set_uniform('u_view_offset', tuple(self.view_offset))
        shader.set_uniform('u_view_scale', tuple(self.view_scale))
        
        vao = ctx.vertex_array(shader._mgl_program, [(self.vbo, '2f 2f', 'position', 'texCoord')])
        vao.render(moderngl.TRIANGLE_STRIP)
        vao.release()

    def delete(self) -> None:
        if hasattr(self, 'fbo_a') and self.fbo_a: self.fbo_a.delete()
        if hasattr(self, 'fbo_b') and self.fbo_b: self.fbo_b.delete()
        if hasattr(self, 'fbo_prev') and self.fbo_prev: self.fbo_prev.delete()
        
        if hasattr(self, '_texture_map'):
            for t in self._texture_map.values():
                t.release()
            self._texture_map.clear()
        
        if hasattr(self, 'vbo') and self.vbo: self.vbo.release(); self.vbo = None
        if hasattr(self, 'vao') and self.vao: self.vao.release(); self.vao = None
        if hasattr(self, '_pbos') and self._pbos:
            for p in self._pbos: p.release()
            self._pbos = []
            
        if hasattr(self, 'passthrough') and self.passthrough: self.passthrough.delete()
        if hasattr(self, 'post_processing_shader') and self.post_processing_shader: self.post_processing_shader.delete()

    def __enter__(self) -> "EffectChain":
        return self

    def __exit__(self, *_) -> None:
        self.delete()

    def __del__(self) -> None:
        self.delete()
